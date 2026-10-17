import hashlib
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import (
    ConstructionActivity,
    MaterialActualConsumptionEntry,
    MaterialConsumptionReconciliation,
    MaterialConsumptionVerification,
    MaterialIssueAllocation,
    MaterialItem,
    MaterialRequirementItem,
    MaterialRequirementPlan,
    MaterialStockLedger,
    Project,
    TheoreticalConsumptionItem,
    User,
)
from app.schemas.material_consumption_reconciliation import (
    MaterialConsumptionCreate,
    MaterialConsumptionReconciliationCreate,
    MaterialConsumptionVerifyRequest,
    MaterialIssueAllocationCreate,
)
from app.services.material_inventory_service import convert_unit


def _ensure_role(user: User, allowed_roles: List[str]) -> None:
    role = user.role.lower()
    if role not in [r.lower() for r in allowed_roles]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{user.role}' is not authorized for this operation.",
        )


def _verify_project_exists(db: Session, project_id: str) -> Project:
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    return proj


def _verify_material_item(db: Session, project_id: str, material_item_id: str) -> MaterialItem:
    mat = db.query(MaterialItem).filter(MaterialItem.id == material_item_id).first()
    if not mat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MaterialItem '{material_item_id}' not found.",
        )
    if mat.project_id is not None and mat.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Material '{mat.material_code}' belongs to a different project.",
        )
    return mat


def _verify_activity(db: Session, project_id: str, activity_id: str) -> ConstructionActivity:
    act = db.query(ConstructionActivity).filter(ConstructionActivity.id == activity_id).first()
    if not act:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ConstructionActivity '{activity_id}' not found.",
        )
    if act.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Activity '{act.activity_code}' belongs to a different project.",
        )
    return act


# ==============================================================================
# 1. MATERIAL ISSUE ALLOCATION
# ==============================================================================

def create_material_issue_allocation(
    db: Session,
    project_id: str,
    data: MaterialIssueAllocationCreate,
    current_user: User,
) -> MaterialIssueAllocation:
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor"])
    _verify_project_exists(db, project_id)
    mat = _verify_material_item(db, project_id, data.material_item_id)
    act = _verify_activity(db, project_id, data.activity_id)

    # Concurrency safe lock on the referenced stock ledger transaction
    ledger = (
        db.query(MaterialStockLedger)
        .filter(MaterialStockLedger.id == data.material_stock_ledger_id)
        .with_for_update()
        .first()
    )
    if not ledger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MaterialStockLedger transaction '{data.material_stock_ledger_id}' not found.",
        )
    if ledger.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock ledger transaction belongs to project '{ledger.project_id}', not '{project_id}'.",
        )
    if ledger.material_item_id != data.material_item_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock transaction material '{ledger.material_item_id}' does not match requested material '{data.material_item_id}'.",
        )
    if ledger.transaction_type.upper() != "ISSUE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock transaction must be an ISSUE transaction (found '{ledger.transaction_type}').",
        )
    if not ledger.is_authoritative:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot allocate unverified/non-authoritative stock ledger transaction.",
        )

    # Optional plan & item verification
    if data.material_requirement_plan_id:
        plan = db.query(MaterialRequirementPlan).filter(MaterialRequirementPlan.id == data.material_requirement_plan_id).first()
        if not plan or plan.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"MaterialRequirementPlan '{data.material_requirement_plan_id}' does not exist for project '{project_id}'.",
            )
    if data.material_requirement_item_id:
        item = db.query(MaterialRequirementItem).filter(MaterialRequirementItem.id == data.material_requirement_item_id).first()
        if not item or item.project_id != project_id or item.material_item_id != data.material_item_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"MaterialRequirementItem '{data.material_requirement_item_id}' does not match project or material.",
            )

    # Unit conversion from allocation unit to ledger unit
    requested_qty_ledger_unit, factor, ok = convert_unit(data.issued_quantity, data.issued_unit, ledger.unit)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unit mismatch: allocation unit '{data.issued_unit}' incompatible with stock ledger unit '{ledger.unit}'.",
        )

    # Over-allocation protection against the authoritative issue transaction
    existing_allocations = (
        db.query(MaterialIssueAllocation)
        .filter(
            MaterialIssueAllocation.material_stock_ledger_id == ledger.id,
            MaterialIssueAllocation.status == "ALLOCATED",
        )
        .all()
    )
    already_allocated_ledger_unit = Decimal("0.0000")
    for alloc in existing_allocations:
        conv_q, _, conv_ok = convert_unit(alloc.issued_quantity, alloc.issued_unit, ledger.unit)
        if conv_ok:
            already_allocated_ledger_unit += conv_q

    if already_allocated_ledger_unit + requested_qty_ledger_unit > ledger.transaction_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Allocation exceeds available issued quantity on stock ledger transaction: "
                f"already allocated {already_allocated_ledger_unit} {ledger.unit} + requested {requested_qty_ledger_unit} {ledger.unit} "
                f"> transaction quantity {ledger.transaction_quantity} {ledger.unit}."
            ),
        )

    allocation = MaterialIssueAllocation(
        id=str(uuid.uuid4()),
        project_id=project_id,
        material_item_id=data.material_item_id,
        material_stock_ledger_id=data.material_stock_ledger_id,
        activity_id=data.activity_id,
        material_requirement_plan_id=data.material_requirement_plan_id,
        material_requirement_item_id=data.material_requirement_item_id,
        issued_quantity=data.issued_quantity,
        issued_unit=data.issued_unit,
        issue_date=data.issue_date,
        source_type=data.source_type or "STORE_ISSUE",
        reference_type=data.reference_type,
        reference_id=data.reference_id,
        status="ALLOCATED",
        created_by=current_user.id,
        metadata_json=data.metadata_json or {},
    )
    db.add(allocation)
    db.commit()
    db.refresh(allocation)
    return allocation


def list_material_issue_allocations(
    db: Session,
    project_id: str,
    current_user: User,
    material_item_id: Optional[str] = None,
    activity_id: Optional[str] = None,
    material_stock_ledger_id: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> List[MaterialIssueAllocation]:
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    _verify_project_exists(db, project_id)

    q = db.query(MaterialIssueAllocation).filter(MaterialIssueAllocation.project_id == project_id)
    if material_item_id:
        q = q.filter(MaterialIssueAllocation.material_item_id == material_item_id)
    if activity_id:
        q = q.filter(MaterialIssueAllocation.activity_id == activity_id)
    if material_stock_ledger_id:
        q = q.filter(MaterialIssueAllocation.material_stock_ledger_id == material_stock_ledger_id)
    if status_filter:
        q = q.filter(MaterialIssueAllocation.status == status_filter.upper())
    return q.order_by(MaterialIssueAllocation.created_at.desc()).all()


def get_material_issue_allocation(
    db: Session,
    project_id: str,
    allocation_id: str,
    current_user: User,
) -> MaterialIssueAllocation:
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    _verify_project_exists(db, project_id)
    alloc = (
        db.query(MaterialIssueAllocation)
        .filter(MaterialIssueAllocation.id == allocation_id, MaterialIssueAllocation.project_id == project_id)
        .first()
    )
    if not alloc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MaterialIssueAllocation '{allocation_id}' not found.",
        )
    return alloc


# ==============================================================================
# 2. CONTRACTOR CONSUMPTION DECLARATION
# ==============================================================================

def create_material_consumption_entry(
    db: Session,
    project_id: str,
    data: MaterialConsumptionCreate,
    current_user: User,
) -> MaterialActualConsumptionEntry:
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    _verify_project_exists(db, project_id)
    _verify_material_item(db, project_id, data.material_item_id)
    _verify_activity(db, project_id, data.activity_id)

    if data.issue_allocation_id:
        alloc = db.query(MaterialIssueAllocation).filter(MaterialIssueAllocation.id == data.issue_allocation_id).first()
        if not alloc or alloc.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Issue allocation '{data.issue_allocation_id}' does not belong to project '{project_id}'.",
            )
        if alloc.material_item_id != data.material_item_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Issue allocation material does not match declared material '{data.material_item_id}'.",
            )
        if alloc.activity_id != data.activity_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Issue allocation activity does not match declared activity '{data.activity_id}'.",
            )

    if data.material_requirement_plan_id:
        plan = db.query(MaterialRequirementPlan).filter(MaterialRequirementPlan.id == data.material_requirement_plan_id).first()
        if not plan or plan.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requirement plan '{data.material_requirement_plan_id}' does not belong to project '{project_id}'.",
            )

    entry = MaterialActualConsumptionEntry(
        id=str(uuid.uuid4()),
        project_id=project_id,
        material_item_id=data.material_item_id,
        activity_id=data.activity_id,
        material_requirement_plan_id=data.material_requirement_plan_id,
        material_requirement_item_id=data.material_requirement_item_id,
        issue_allocation_id=data.issue_allocation_id,
        contractor_consumed_quantity=data.contractor_consumed_quantity,
        contractor_consumed_unit=data.contractor_consumed_unit,
        consumption_date=data.consumption_date,
        declared_by=current_user.id,
        verification_status="PENDING_VERIFICATION",
        metadata_json=data.metadata_json or {},
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_material_consumption_entries(
    db: Session,
    project_id: str,
    current_user: User,
    material_item_id: Optional[str] = None,
    activity_id: Optional[str] = None,
    verification_status: Optional[str] = None,
) -> List[MaterialActualConsumptionEntry]:
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    _verify_project_exists(db, project_id)

    q = db.query(MaterialActualConsumptionEntry).filter(MaterialActualConsumptionEntry.project_id == project_id)
    if material_item_id:
        q = q.filter(MaterialActualConsumptionEntry.material_item_id == material_item_id)
    if activity_id:
        q = q.filter(MaterialActualConsumptionEntry.activity_id == activity_id)
    if verification_status:
        q = q.filter(MaterialActualConsumptionEntry.verification_status == verification_status.upper())
    return q.order_by(MaterialActualConsumptionEntry.declared_at.desc()).all()


def get_material_consumption_entry(
    db: Session,
    project_id: str,
    entry_id: str,
    current_user: User,
) -> MaterialActualConsumptionEntry:
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    _verify_project_exists(db, project_id)
    entry = (
        db.query(MaterialActualConsumptionEntry)
        .filter(MaterialActualConsumptionEntry.id == entry_id, MaterialActualConsumptionEntry.project_id == project_id)
        .first()
    )
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MaterialActualConsumptionEntry '{entry_id}' not found.",
        )
    return entry


# ==============================================================================
# 3. SUPERVISOR CONSUMPTION VERIFICATION
# ==============================================================================

def verify_material_consumption_entry(
    db: Session,
    project_id: str,
    entry_id: str,
    data: MaterialConsumptionVerifyRequest,
    current_user: User,
) -> MaterialConsumptionVerification:
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor"])
    _verify_project_exists(db, project_id)

    # Concurrency safe lock on consumption entry
    entry = (
        db.query(MaterialActualConsumptionEntry)
        .filter(MaterialActualConsumptionEntry.id == entry_id, MaterialActualConsumptionEntry.project_id == project_id)
        .with_for_update()
        .first()
    )
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MaterialActualConsumptionEntry '{entry_id}' not found in project '{project_id}'.",
        )

    # Contractor cannot verify own declaration
    if current_user.id == entry.declared_by and current_user.role.lower() not in ("admin",):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Contractor cannot verify their own consumption declaration.",
        )

    # Duplicate verification prevention
    if entry.verification_status != "PENDING_VERIFICATION":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Consumption entry is already verified with status '{entry.verification_status}'.",
        )

    action = data.verification_action.upper()
    if action == "VERIFIED":
        verified_qty = (
            data.verified_quantity
            if data.verified_quantity is not None
            else entry.contractor_consumed_quantity
        )
        verified_unit = data.verified_unit or entry.contractor_consumed_unit
    elif action == "CORRECTED":
        if data.verified_quantity is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="verified_quantity is required for CORRECTED verification action.",
            )
        verified_qty = data.verified_quantity
        verified_unit = data.verified_unit or entry.contractor_consumed_unit
    elif action == "REJECTED":
        verified_qty = Decimal("0.0000")
        verified_unit = entry.contractor_consumed_unit
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid verification action '{action}'.",
        )

    # Append verification record (preserves original contractor declaration untouched)
    verification = MaterialConsumptionVerification(
        id=str(uuid.uuid4()),
        consumption_entry_id=entry.id,
        verified_quantity=verified_qty,
        verified_unit=verified_unit,
        verification_status=action,
        correction_reason=data.correction_reason,
        verified_by=current_user.id,
        metadata_json=data.metadata_json or {},
    )
    db.add(verification)

    # Update entry verification status
    entry.verification_status = action
    db.commit()
    db.refresh(verification)
    return verification


def list_consumption_verifications(
    db: Session,
    project_id: str,
    entry_id: str,
    current_user: User,
) -> List[MaterialConsumptionVerification]:
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    entry = get_material_consumption_entry(db, project_id, entry_id, current_user)
    return (
        db.query(MaterialConsumptionVerification)
        .filter(MaterialConsumptionVerification.consumption_entry_id == entry.id)
        .order_by(MaterialConsumptionVerification.verified_at.asc())
        .all()
    )


# ==============================================================================
# 4. PLANNED VS ACTUAL MATERIAL RECONCILIATION
# ==============================================================================

def _compute_canonical_hash(payload: Dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def create_material_consumption_reconciliation(
    db: Session,
    project_id: str,
    data: MaterialConsumptionReconciliationCreate,
    current_user: User,
) -> List[MaterialConsumptionReconciliation]:
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor"])
    _verify_project_exists(db, project_id)

    plan = (
        db.query(MaterialRequirementPlan)
        .filter(
            MaterialRequirementPlan.id == data.material_requirement_plan_id,
            MaterialRequirementPlan.project_id == project_id,
        )
        .first()
    )
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MaterialRequirementPlan '{data.material_requirement_plan_id}' not found for project '{project_id}'.",
        )

    # Query requirement items
    items_query = db.query(MaterialRequirementItem).filter(
        MaterialRequirementItem.material_requirement_plan_id == plan.id,
        MaterialRequirementItem.project_id == project_id,
    )
    if data.activity_id:
        items_query = items_query.filter(MaterialRequirementItem.activity_id == data.activity_id)
    if data.material_item_id:
        items_query = items_query.filter(MaterialRequirementItem.material_item_id == data.material_item_id)

    items = items_query.all()
    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No requirement items found matching the given criteria.",
        )

    created_reconciliations: List[MaterialConsumptionReconciliation] = []
    algorithm_version = "MAT_CONSUMPTION_RECON_1.0"

    for req_item in items:
        mat_id = req_item.material_item_id
        act_id = req_item.activity_id
        req_unit = req_item.requirement_unit
        planned_qty = req_item.requirement_quantity

        mat = db.query(MaterialItem).filter(MaterialItem.id == mat_id).first()

        # 1. Theoretical consumption calculation
        # Query theoretical items for this activity and material
        theo_items = (
            db.query(TheoreticalConsumptionItem)
            .filter(
                TheoreticalConsumptionItem.project_id == project_id,
                TheoreticalConsumptionItem.material_item_id == mat_id,
                TheoreticalConsumptionItem.activity_id == act_id,
            )
            .all()
        )
        theo_qty: Optional[Decimal] = None
        theo_unit: Optional[str] = None
        if theo_items:
            theo_qty = Decimal("0.0000")
            theo_unit = req_unit
            for t_item in theo_items:
                conv_t, _, conv_ok = convert_unit(t_item.theoretical_quantity, t_item.unit, req_unit)
                if conv_ok:
                    theo_qty += conv_t

        # 2. Issued quantity calculation
        allocations = (
            db.query(MaterialIssueAllocation)
            .filter(
                MaterialIssueAllocation.project_id == project_id,
                MaterialIssueAllocation.material_item_id == mat_id,
                MaterialIssueAllocation.activity_id == act_id,
                MaterialIssueAllocation.status == "ALLOCATED",
            )
            .all()
        )
        issued_qty: Optional[Decimal] = Decimal("0.0000") if allocations else None
        issued_unit: Optional[str] = req_unit if allocations else None
        if allocations:
            issued_qty = Decimal("0.0000")
            for alloc in allocations:
                conv_iss, _, conv_ok = convert_unit(alloc.issued_quantity, alloc.issued_unit, req_unit)
                if conv_ok:
                    issued_qty += conv_iss

        # 3. Actual verified consumption calculation
        # Retrieve all verified / corrected consumption verifications for this activity and material
        verified_entries = (
            db.query(MaterialConsumptionVerification)
            .join(MaterialActualConsumptionEntry, MaterialConsumptionVerification.consumption_entry_id == MaterialActualConsumptionEntry.id)
            .filter(
                MaterialActualConsumptionEntry.project_id == project_id,
                MaterialActualConsumptionEntry.material_item_id == mat_id,
                MaterialActualConsumptionEntry.activity_id == act_id,
                MaterialConsumptionVerification.verification_status.in_(["VERIFIED", "CORRECTED"]),
            )
            .all()
        )

        # 4. Reconciliation Math & Status Evaluation
        if not verified_entries:
            # Rule: NO_VERIFIED_ACTUAL never coerces to 0!
            actual_qty = None
            actual_unit = None
            variance_qty = None
            variance_pct = None
            perm_waste_qty = None
            unauth_waste_qty = None
            rec_status = "NO_VERIFIED_ACTUAL"
        else:
            actual_qty = Decimal("0.0000")
            actual_unit = req_unit
            unit_mismatch_found = False
            for v_entry in verified_entries:
                conv_act, _, conv_ok = convert_unit(v_entry.verified_quantity, v_entry.verified_unit, req_unit)
                if conv_ok:
                    actual_qty += conv_act
                else:
                    unit_mismatch_found = True

            if unit_mismatch_found:
                rec_status = "UNIT_MISMATCH"
                variance_qty = None
                variance_pct = None
                perm_waste_qty = None
                unauth_waste_qty = None
            elif theo_qty is None:
                # Missing theoretical quantity requires input, never coerces to 0
                rec_status = "REQUIRES_INPUT"
                variance_qty = None
                variance_pct = None
                perm_waste_qty = None
                unauth_waste_qty = None
            else:
                # Both actual and theoretical are available
                theoretical_variance = actual_qty - theo_qty
                variance_qty = theoretical_variance
                if theo_qty > 0:
                    variance_pct = ((actual_qty - theo_qty) / theo_qty) * Decimal("100.0000")
                else:
                    variance_pct = None

                # Determine permissible wastage percentage
                perm_waste_pct: Optional[Decimal] = None
                if data.permissible_waste_percentage_override is not None:
                    perm_waste_pct = data.permissible_waste_percentage_override
                elif mat and mat.standard_permissible_waste_pct is not None and mat.standard_permissible_waste_pct > 0:
                    perm_waste_pct = mat.standard_permissible_waste_pct

                if perm_waste_pct is None:
                    # Missing wastage configuration -> REQUIRES_INPUT
                    rec_status = "REQUIRES_INPUT"
                    perm_waste_qty = None
                    unauth_waste_qty = None
                else:
                    perm_waste_qty = (theo_qty * perm_waste_pct) / Decimal("100.0000")
                    excess = max(Decimal("0.0000"), actual_qty - theo_qty)
                    unauth_waste_qty = max(Decimal("0.0000"), excess - perm_waste_qty)

                    if actual_qty == theo_qty:
                        rec_status = "MATCH"
                    elif actual_qty > theo_qty:
                        if unauth_waste_qty == Decimal("0.0000"):
                            rec_status = "WITHIN_PERMISSIBLE_WASTAGE"
                        else:
                            rec_status = "OVER_CONSUMPTION"
                    else:
                        rec_status = "UNDER_CONSUMPTION"

        # Supersede existing active reconciliations for this plan item
        existing_recons = (
            db.query(MaterialConsumptionReconciliation)
            .filter(
                MaterialConsumptionReconciliation.project_id == project_id,
                MaterialConsumptionReconciliation.material_requirement_plan_id == plan.id,
                MaterialConsumptionReconciliation.material_requirement_item_id == req_item.id,
                MaterialConsumptionReconciliation.status != "SUPERSEDED",
            )
            .all()
        )
        for er in existing_recons:
            er.status = "SUPERSEDED"
            db.flush()

        # Build canonical hash payload
        hash_payload = {
            "algorithm_version": algorithm_version,
            "project_id": str(project_id),
            "material_requirement_plan_id": str(plan.id),
            "material_requirement_item_id": str(req_item.id),
            "activity_id": str(act_id),
            "material_item_id": str(mat_id),
            "planned_quantity": f"{planned_qty:.4f}" if planned_qty is not None else None,
            "planned_unit": req_unit,
            "theoretical_quantity": f"{theo_qty:.4f}" if theo_qty is not None else None,
            "theoretical_unit": theo_unit,
            "issued_quantity": f"{issued_qty:.4f}" if issued_qty is not None else None,
            "issued_unit": issued_unit,
            "actual_consumed_quantity": f"{actual_qty:.4f}" if actual_qty is not None else None,
            "actual_consumed_unit": actual_unit,
            "variance_quantity": f"{variance_qty:.4f}" if variance_qty is not None else None,
            "variance_percentage": f"{variance_pct:.4f}" if variance_pct is not None else None,
            "permissible_wastage_quantity": f"{perm_waste_qty:.4f}" if perm_waste_qty is not None else None,
            "unauthorized_wastage_quantity": f"{unauth_waste_qty:.4f}" if unauth_waste_qty is not None else None,
            "status": rec_status,
        }
        canonical_hash = _compute_canonical_hash(hash_payload)

        input_snapshot = {
            "requirement_plan_id": plan.id,
            "requirement_item_id": req_item.id,
            "material_code": mat.material_code if mat else None,
            "activity_id": act_id,
            "raw_hash_payload": hash_payload,
        }

        reconciliation = MaterialConsumptionReconciliation(
            id=str(uuid.uuid4()),
            project_id=project_id,
            material_requirement_plan_id=plan.id,
            material_requirement_item_id=req_item.id,
            activity_id=act_id,
            material_item_id=mat_id,
            planned_quantity=planned_qty,
            planned_unit=req_unit,
            theoretical_quantity=theo_qty,
            theoretical_unit=theo_unit,
            issued_quantity=issued_qty,
            issued_unit=issued_unit,
            actual_consumed_quantity=actual_qty,
            actual_consumed_unit=actual_unit,
            variance_quantity=variance_qty,
            variance_percentage=variance_pct,
            permissible_wastage_quantity=perm_waste_qty,
            unauthorized_wastage_quantity=unauth_waste_qty,
            status=rec_status,
            algorithm_version=algorithm_version,
            input_snapshot_json=input_snapshot,
            provenance_metadata=data.provenance_metadata or {},
            canonical_hash=canonical_hash,
            created_by=current_user.id,
        )
        db.add(reconciliation)
        created_reconciliations.append(reconciliation)

    db.commit()
    for r in created_reconciliations:
        db.refresh(r)
    return created_reconciliations


def list_material_consumption_reconciliations(
    db: Session,
    project_id: str,
    current_user: User,
    material_requirement_plan_id: Optional[str] = None,
    activity_id: Optional[str] = None,
    material_item_id: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> List[MaterialConsumptionReconciliation]:
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    _verify_project_exists(db, project_id)

    q = db.query(MaterialConsumptionReconciliation).filter(MaterialConsumptionReconciliation.project_id == project_id)
    if material_requirement_plan_id:
        q = q.filter(MaterialConsumptionReconciliation.material_requirement_plan_id == material_requirement_plan_id)
    if activity_id:
        q = q.filter(MaterialConsumptionReconciliation.activity_id == activity_id)
    if material_item_id:
        q = q.filter(MaterialConsumptionReconciliation.material_item_id == material_item_id)
    if status_filter:
        q = q.filter(MaterialConsumptionReconciliation.status == status_filter.upper())
    return q.order_by(MaterialConsumptionReconciliation.created_at.desc()).all()


def get_material_consumption_reconciliation(
    db: Session,
    project_id: str,
    reconciliation_id: str,
    current_user: User,
) -> MaterialConsumptionReconciliation:
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    _verify_project_exists(db, project_id)
    recon = (
        db.query(MaterialConsumptionReconciliation)
        .filter(MaterialConsumptionReconciliation.id == reconciliation_id, MaterialConsumptionReconciliation.project_id == project_id)
        .first()
    )
    if not recon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MaterialConsumptionReconciliation '{reconciliation_id}' not found.",
        )
    return recon

