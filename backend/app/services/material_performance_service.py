import hashlib
import json
import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.db.models import (
    User,
    Project,
    ProjectMember,
    ConstructionActivity,
    MaterialItem,
    MaterialRequirementPlan,
    MaterialRequirementItem,
    TheoreticalConsumptionItem,
    MaterialIssueAllocation,
    MaterialActualConsumptionEntry,
    MaterialConsumptionVerification,
    MaterialConsumptionReconciliation,
    MaterialPerformanceSnapshot,
    DailyActivityProgress,
    DailyActivityProgressVerification,
    PeriodCertificateItem,
)
from app.schemas.material_performance import (
    MaterialPerformanceCreateRequest,
    MaterialPerformanceSummaryResponse,
    MaterialPerformanceSnapshotResponse,
)
from app.services.material_inventory_service import convert_unit


ALGORITHM_VERSION = "MAT_PERFORMANCE_1.0"


def _ensure_role(user: User, allowed_roles: List[str]) -> None:
    role = user.role.lower()
    if role not in [r.lower() for r in allowed_roles]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{user.role}' is not authorized for this operation.",
        )


def generate_canonical_hash(payload: Dict[str, Any]) -> str:
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def _verify_project_access(db: Session, project_id: str, user: User) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    if user.role.lower() == "admin":
        return project
    if project.created_by == user.id:
        return project
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user.id,
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not authorized for this project.",
        )
    return project


def create_material_performance_snapshot(
    db: Session,
    project_id: str,
    data: MaterialPerformanceCreateRequest,
    current_user: User,
) -> MaterialPerformanceSnapshot:
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor"])
    _verify_project_access(db, project_id, current_user)
    current_user_id = current_user.id

    # Validate activity belongs to project
    activity = db.query(ConstructionActivity).filter(
        ConstructionActivity.id == data.activity_id,
        ConstructionActivity.project_id == project_id,
    ).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ConstructionActivity {data.activity_id} not found in project {project_id}",
        )

    # Validate material belongs to project or is global
    material = db.query(MaterialItem).filter(
        MaterialItem.id == data.material_item_id,
        (MaterialItem.project_id == project_id) | (MaterialItem.project_id.is_(None)),
    ).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MaterialItem {data.material_item_id} not found in project {project_id}",
        )

    # Validate requirement plan if provided
    plan = None
    if data.requirement_plan_id:
        plan = db.query(MaterialRequirementPlan).filter(
            MaterialRequirementPlan.id == data.requirement_plan_id,
            MaterialRequirementPlan.project_id == project_id,
        ).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MaterialRequirementPlan {data.requirement_plan_id} not found in project {project_id}",
            )

    # Validate requirement item if provided
    req_item = None
    if data.requirement_item_id:
        req_item = db.query(MaterialRequirementItem).filter(
            MaterialRequirementItem.id == data.requirement_item_id,
            MaterialRequirementItem.project_id == project_id,
        ).first()
        if not req_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MaterialRequirementItem {data.requirement_item_id} not found in project {project_id}",
            )

    # Validate reconciliation if provided
    recon = None
    if data.reconciliation_id:
        recon = db.query(MaterialConsumptionReconciliation).filter(
            MaterialConsumptionReconciliation.id == data.reconciliation_id,
            MaterialConsumptionReconciliation.project_id == project_id,
        ).first()
        if not recon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MaterialConsumptionReconciliation {data.reconciliation_id} not found in project {project_id}",
            )

    # Advisory lock for concurrency protection
    lock_key = f"mps_create:{project_id}:{data.activity_id}:{data.material_item_id}:{data.performance_period_start}:{data.performance_period_end}:{data.reconciliation_id}:{data.requirement_plan_id}"
    lock_hash = int(hashlib.sha256(lock_key.encode("utf-8")).hexdigest()[:15], 16)
    db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock_hash})

    # Determine Planned Quantity & Unit
    planned_qty: Optional[Decimal] = None
    planned_unit: Optional[str] = None
    if req_item:
        planned_qty = req_item.requirement_quantity
        planned_unit = req_item.requirement_unit
    elif plan:
        item = db.query(MaterialRequirementItem).filter(
            MaterialRequirementItem.material_requirement_plan_id == plan.id,
            MaterialRequirementItem.activity_id == data.activity_id,
            MaterialRequirementItem.material_item_id == data.material_item_id,
        ).first()
        if item:
            planned_qty = item.requirement_quantity
            planned_unit = item.requirement_unit
    elif recon and recon.planned_quantity is not None:
        planned_qty = recon.planned_quantity
        planned_unit = recon.planned_unit
    else:
        active_plan = db.query(MaterialRequirementPlan).filter(
            MaterialRequirementPlan.project_id == project_id,
            MaterialRequirementPlan.status == "ACTIVE",
        ).first()
        if active_plan:
            item = db.query(MaterialRequirementItem).filter(
                MaterialRequirementItem.material_requirement_plan_id == active_plan.id,
                MaterialRequirementItem.activity_id == data.activity_id,
                MaterialRequirementItem.material_item_id == data.material_item_id,
            ).first()
            if item:
                planned_qty = item.requirement_quantity
                planned_unit = item.requirement_unit

    target_unit = planned_unit or material.standard_unit
    unit_mismatch = False

    # Determine Theoretical Quantity & Unit
    theo_qty: Optional[Decimal] = None
    theo_unit: Optional[str] = None
    unconvertible_theoretical_units = []
    theo_items = db.query(TheoreticalConsumptionItem).filter(
        TheoreticalConsumptionItem.project_id == project_id,
        TheoreticalConsumptionItem.activity_id == data.activity_id,
        TheoreticalConsumptionItem.material_item_id == data.material_item_id,
    ).all()
    if theo_items:
        t_sum = Decimal("0.0000")
        has_theo_incompatible = False
        for t in theo_items:
            q_conv, _, ok = convert_unit(t.theoretical_quantity, t.unit, target_unit)
            if ok:
                t_sum += q_conv
            else:
                has_theo_incompatible = True
                unconvertible_theoretical_units.append({
                    "theoretical_item_id": t.id,
                    "quantity": str(t.theoretical_quantity),
                    "source_unit": t.unit,
                    "target_unit": target_unit,
                })
        if has_theo_incompatible:
            unit_mismatch = True
            theo_qty = None
            theo_unit = None
        else:
            theo_qty = t_sum
            theo_unit = target_unit
    elif recon and recon.theoretical_quantity is not None:
        if recon.theoretical_unit != target_unit:
            q_conv, _, ok = convert_unit(recon.theoretical_quantity, recon.theoretical_unit, target_unit)
            if ok:
                theo_qty = q_conv
                theo_unit = target_unit
            else:
                unit_mismatch = True
                theo_qty = None
                theo_unit = None
                unconvertible_theoretical_units.append({
                    "reconciliation_id": recon.id,
                    "quantity": str(recon.theoretical_quantity),
                    "source_unit": recon.theoretical_unit,
                    "target_unit": target_unit,
                })
        else:
            theo_qty = recon.theoretical_quantity
            theo_unit = recon.theoretical_unit

    # Determine Issued Quantity & Unit
    issued_qty: Optional[Decimal] = None
    issued_unit: Optional[str] = None
    unconvertible_issued_units = []
    issue_allocs = db.query(MaterialIssueAllocation).filter(
        MaterialIssueAllocation.project_id == project_id,
        MaterialIssueAllocation.activity_id == data.activity_id,
        MaterialIssueAllocation.material_item_id == data.material_item_id,
        MaterialIssueAllocation.status == "ALLOCATED",
    ).all()
    if issue_allocs:
        i_sum = Decimal("0.0000")
        has_issued_incompatible = False
        for alloc in issue_allocs:
            q_conv, _, ok = convert_unit(alloc.issued_quantity, alloc.issued_unit, target_unit)
            if ok:
                i_sum += q_conv
            else:
                has_issued_incompatible = True
                unconvertible_issued_units.append({
                    "allocation_id": alloc.id,
                    "quantity": str(alloc.issued_quantity),
                    "source_unit": alloc.issued_unit,
                    "target_unit": target_unit,
                })
        if has_issued_incompatible:
            unit_mismatch = True
            issued_qty = None
            issued_unit = None
        else:
            issued_qty = i_sum
            issued_unit = target_unit
    elif recon and recon.issued_quantity is not None:
        if recon.issued_unit != target_unit:
            q_conv, _, ok = convert_unit(recon.issued_quantity, recon.issued_unit, target_unit)
            if ok:
                issued_qty = q_conv
                issued_unit = target_unit
            else:
                unit_mismatch = True
                issued_qty = None
                issued_unit = None
                unconvertible_issued_units.append({
                    "reconciliation_id": recon.id,
                    "quantity": str(recon.issued_quantity),
                    "source_unit": recon.issued_unit,
                    "target_unit": target_unit,
                })
        else:
            issued_qty = recon.issued_quantity
            issued_unit = recon.issued_unit

    # Determine Verified Actual Consumption Quantity & Unit
    actual_qty: Optional[Decimal] = None
    actual_unit: Optional[str] = None
    unconvertible_actual_units = []

    verified_verifs = (
        db.query(MaterialConsumptionVerification)
        .join(MaterialActualConsumptionEntry, MaterialConsumptionVerification.consumption_entry_id == MaterialActualConsumptionEntry.id)
        .filter(
            MaterialActualConsumptionEntry.project_id == project_id,
            MaterialActualConsumptionEntry.activity_id == data.activity_id,
            MaterialActualConsumptionEntry.material_item_id == data.material_item_id,
            MaterialConsumptionVerification.verification_status.in_(["VERIFIED", "CORRECTED"]),
        )
        .all()
    )

    if verified_verifs:
        a_sum = Decimal("0.0000")
        has_actual_incompatible = False
        for v in verified_verifs:
            q_conv, _, ok = convert_unit(v.verified_quantity, v.verified_unit, target_unit)
            if ok:
                a_sum += q_conv
            else:
                has_actual_incompatible = True
                unconvertible_actual_units.append({
                    "verification_id": v.id,
                    "quantity": str(v.verified_quantity),
                    "source_unit": v.verified_unit,
                    "target_unit": target_unit,
                })
        if has_actual_incompatible:
            unit_mismatch = True
            actual_qty = None
            actual_unit = None
        else:
            actual_qty = a_sum
            actual_unit = target_unit
    elif recon and recon.actual_consumed_quantity is not None:
        if recon.actual_consumed_unit != target_unit:
            q_conv, _, ok = convert_unit(recon.actual_consumed_quantity, recon.actual_consumed_unit, target_unit)
            if ok:
                actual_qty = q_conv
                actual_unit = target_unit
            else:
                unit_mismatch = True
                actual_qty = None
                actual_unit = None
                unconvertible_actual_units.append({
                    "reconciliation_id": recon.id,
                    "quantity": str(recon.actual_consumed_quantity),
                    "source_unit": recon.actual_consumed_unit,
                    "target_unit": target_unit,
                })
        else:
            actual_qty = recon.actual_consumed_quantity
            actual_unit = recon.actual_consumed_unit

    # Cross-check unit compatibility between actual, theoretical, planned
    if actual_qty is not None and theo_qty is not None and actual_unit and theo_unit:
        if actual_unit != theo_unit:
            _, _, ok = convert_unit(Decimal("1.0"), actual_unit, theo_unit)
            if not ok:
                unit_mismatch = True

    if actual_qty is not None and planned_qty is not None and actual_unit and planned_unit:
        if actual_unit != planned_unit:
            _, _, ok = convert_unit(Decimal("1.0"), actual_unit, planned_unit)
            if not ok:
                unit_mismatch = True

    # Determine Wastage Quantities
    perm_waste_qty: Optional[Decimal] = None
    unauth_waste_qty: Optional[Decimal] = None
    if not unit_mismatch:
        if recon and recon.permissible_wastage_quantity is not None:
            perm_waste_qty = recon.permissible_wastage_quantity
            unauth_waste_qty = recon.unauthorized_wastage_quantity
        elif theo_qty is not None:
            waste_pct: Optional[Decimal] = None
            if data.tolerance_percentage is not None:
                waste_pct = data.tolerance_percentage
            elif material.standard_permissible_waste_pct is not None and material.standard_permissible_waste_pct > 0:
                waste_pct = material.standard_permissible_waste_pct

            if waste_pct is not None:
                perm_waste_qty = (theo_qty * waste_pct) / Decimal("100.0000")
                if actual_qty is not None:
                    excess = max(Decimal("0.0000"), actual_qty - theo_qty)
                    unauth_waste_qty = max(Decimal("0.0000"), excess - perm_waste_qty)

    # Determine Verified Activity Execution Output Quantity
    exec_qty: Optional[Decimal] = None
    exec_unit: Optional[str] = None
    if data.verified_activity_execution_quantity is not None:
        exec_qty = data.verified_activity_execution_quantity
        exec_unit = data.verified_activity_execution_unit or activity.duration_unit or "UNIT"
    else:
        prog_verif = (
            db.query(DailyActivityProgressVerification)
            .join(DailyActivityProgress, DailyActivityProgressVerification.daily_activity_progress_id == DailyActivityProgress.id)
            .filter(
                DailyActivityProgress.project_id == project_id,
                DailyActivityProgress.activity_id == data.activity_id,
                DailyActivityProgressVerification.verification_status.in_(["VERIFIED", "CORRECTED"]),
            )
            .order_by(DailyActivityProgressVerification.verified_at.desc())
            .first()
        )
        if prog_verif and prog_verif.verified_quantity is not None:
            exec_qty = Decimal(str(prog_verif.verified_quantity))
            exec_unit = prog_verif.verified_quantity_unit or "UNIT"
        else:
            cert_item = (
                db.query(PeriodCertificateItem)
                .filter(
                    PeriodCertificateItem.activity_id == data.activity_id,
                )
                .order_by(PeriodCertificateItem.id.desc())
                .first()
            )
            if cert_item and cert_item.certified_quantity is not None:
                exec_qty = Decimal(str(cert_item.certified_quantity))
                exec_unit = cert_item.quantity_unit

    # Compute Variances
    planned_var_qty: Optional[Decimal] = None
    planned_var_pct: Optional[Decimal] = None
    if not unit_mismatch and actual_qty is not None and planned_qty is not None:
        conv_actual = actual_qty
        if actual_unit and planned_unit and actual_unit != planned_unit:
            conv_actual, _, _ = convert_unit(actual_qty, actual_unit, planned_unit)
        planned_var_qty = conv_actual - planned_qty
        if planned_qty > 0:
            planned_var_pct = (planned_var_qty / planned_qty) * Decimal("100.0000")

    theo_var_qty: Optional[Decimal] = None
    theo_var_pct: Optional[Decimal] = None
    if not unit_mismatch and actual_qty is not None and theo_qty is not None:
        conv_actual = actual_qty
        if actual_unit and theo_unit and actual_unit != theo_unit:
            conv_actual, _, _ = convert_unit(actual_qty, actual_unit, theo_unit)
        theo_var_qty = conv_actual - theo_qty
        if theo_qty > 0:
            theo_var_pct = (theo_var_qty / theo_qty) * Decimal("100.0000")

    # Compute Consumption Intensity & Productivity
    consumption_intensity: Optional[Decimal] = None
    productivity: Optional[Decimal] = None
    if not unit_mismatch and exec_qty is not None and exec_qty > 0 and actual_qty is not None:
        consumption_intensity = actual_qty / exec_qty
        if actual_qty > 0:
            productivity = exec_qty / actual_qty

    # Determine Performance Status
    if unit_mismatch:
        perf_status = "UNIT_MISMATCH"
    elif actual_qty is None and theo_qty is None:
        perf_status = "REQUIRES_INPUT"
    elif actual_qty is None:
        perf_status = "NO_VERIFIED_ACTUAL"
    elif theo_qty is None:
        perf_status = "NO_THEORETICAL_DATA"
    else:
        cmp_actual = actual_qty
        if actual_unit and theo_unit and actual_unit != theo_unit:
            cmp_actual, _, _ = convert_unit(actual_qty, actual_unit, theo_unit)

        if cmp_actual == theo_qty:
            perf_status = "MATCH"
        elif cmp_actual < theo_qty:
            perf_status = "UNDER_CONSUMPTION"
        else:
            if unauth_waste_qty is not None and unauth_waste_qty > Decimal("0.0000"):
                perf_status = "UNAUTHORIZED_WASTAGE"
            elif perm_waste_qty is not None and (cmp_actual - theo_qty) <= perm_waste_qty:
                perf_status = "WITHIN_PERMISSIBLE_VARIANCE"
            else:
                perf_status = "OVER_CONSUMPTION"

    input_snapshot = {
        "project_id": project_id,
        "activity_id": data.activity_id,
        "material_item_id": data.material_item_id,
        "requirement_plan_id": data.requirement_plan_id,
        "requirement_item_id": data.requirement_item_id,
        "reconciliation_id": data.reconciliation_id,
        "upstream_reconciliation_id": data.reconciliation_id,
        "performance_period_start": data.performance_period_start.isoformat() if data.performance_period_start else None,
        "performance_period_end": data.performance_period_end.isoformat() if data.performance_period_end else None,
        "planned_quantity": str(planned_qty) if planned_qty is not None else None,
        "planned_unit": planned_unit,
        "theoretical_quantity": str(theo_qty) if theo_qty is not None else None,
        "theoretical_unit": theo_unit,
        "issued_quantity": str(issued_qty) if issued_qty is not None else None,
        "issued_unit": issued_unit,
        "actual_consumption_quantity": str(actual_qty) if actual_qty is not None else None,
        "actual_consumption_unit": actual_unit,
        "verified_activity_execution_quantity": str(exec_qty) if exec_qty is not None else None,
        "verified_activity_execution_unit": exec_unit,
        "permissible_wastage_quantity": str(perm_waste_qty) if perm_waste_qty is not None else None,
        "unauthorized_wastage_quantity": str(unauth_waste_qty) if unauth_waste_qty is not None else None,
        "tolerance_percentage": str(data.tolerance_percentage) if data.tolerance_percentage is not None else None,
    }

    provenance_metadata = {
        "activity_code": activity.activity_code,
        "activity_name": activity.activity_name,
        "material_code": material.material_code,
        "material_name": material.material_name,
        "upstream_reconciliation_id": data.reconciliation_id,
        "verified_entry_count": len(verified_verifs),
        "issue_allocation_count": len(issue_allocs),
        "theoretical_item_count": len(theo_items),
        "target_unit": target_unit,
    }
    if unconvertible_theoretical_units:
        provenance_metadata["unconvertible_theoretical_units"] = unconvertible_theoretical_units
    if unconvertible_issued_units:
        provenance_metadata["unconvertible_issued_units"] = unconvertible_issued_units
    if unconvertible_actual_units:
        provenance_metadata["unconvertible_actual_units"] = unconvertible_actual_units

    hash_payload = {
        "algorithm_version": ALGORITHM_VERSION,
        "project_id": project_id,
        "activity_id": data.activity_id,
        "material_item_id": data.material_item_id,
        "requirement_plan_id": data.requirement_plan_id,
        "performance_period_start": data.performance_period_start.isoformat() if data.performance_period_start else None,
        "performance_period_end": data.performance_period_end.isoformat() if data.performance_period_end else None,
        "planned_quantity": str(planned_qty) if planned_qty is not None else None,
        "planned_unit": planned_unit,
        "theoretical_quantity": str(theo_qty) if theo_qty is not None else None,
        "theoretical_unit": theo_unit,
        "issued_quantity": str(issued_qty) if issued_qty is not None else None,
        "issued_unit": issued_unit,
        "actual_consumption_quantity": str(actual_qty) if actual_qty is not None else None,
        "actual_consumption_unit": actual_unit,
        "verified_activity_execution_quantity": str(exec_qty) if exec_qty is not None else None,
        "verified_activity_execution_unit": exec_unit,
        "planned_variance_quantity": str(planned_var_qty) if planned_var_qty is not None else None,
        "planned_variance_percentage": str(planned_var_pct) if planned_var_pct is not None else None,
        "theoretical_variance_quantity": str(theo_var_qty) if theo_var_qty is not None else None,
        "theoretical_variance_percentage": str(theo_var_pct) if theo_var_pct is not None else None,
        "permissible_wastage_quantity": str(perm_waste_qty) if perm_waste_qty is not None else None,
        "unauthorized_wastage_quantity": str(unauth_waste_qty) if unauth_waste_qty is not None else None,
        "consumption_intensity": str(consumption_intensity) if consumption_intensity is not None else None,
        "productivity": str(productivity) if productivity is not None else None,
        "performance_status": perf_status,
    }

    canonical_hash = generate_canonical_hash(hash_payload)

    # Creation produces DRAFT strictly
    initial_status = "DRAFT"
    now_ts = datetime.now(timezone.utc)

    snapshot = MaterialPerformanceSnapshot(
        project_id=project_id,
        activity_id=data.activity_id,
        material_item_id=data.material_item_id,
        reconciliation_id=data.reconciliation_id,
        requirement_plan_id=data.requirement_plan_id,
        requirement_item_id=data.requirement_item_id,
        performance_period_start=data.performance_period_start,
        performance_period_end=data.performance_period_end,
        planned_quantity=planned_qty,
        planned_unit=planned_unit,
        theoretical_quantity=theo_qty,
        theoretical_unit=theo_unit,
        issued_quantity=issued_qty,
        issued_unit=issued_unit,
        actual_consumption_quantity=actual_qty,
        actual_consumption_unit=actual_unit,
        verified_activity_execution_quantity=exec_qty,
        verified_activity_execution_unit=exec_unit,
        permissible_wastage_quantity=perm_waste_qty,
        unauthorized_wastage_quantity=unauth_waste_qty,
        planned_variance_quantity=planned_var_qty,
        theoretical_variance_quantity=theo_var_qty,
        planned_variance_percentage=planned_var_pct,
        theoretical_variance_percentage=theo_var_pct,
        consumption_intensity=consumption_intensity,
        productivity=productivity,
        performance_status=perf_status,
        algorithm_version=ALGORITHM_VERSION,
        input_snapshot_json=input_snapshot,
        provenance_metadata=provenance_metadata,
        canonical_hash=canonical_hash,
        status=initial_status,
        created_by=current_user_id,
        created_at=now_ts,
        finalized_by=None,
        finalized_at=None,
    )

    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_material_performance_snapshot(
    db: Session,
    project_id: str,
    snapshot_id: str,
    user: User,
) -> MaterialPerformanceSnapshot:
    _ensure_role(user, ["admin", "supervisor", "site_supervisor", "contractor"])
    _verify_project_access(db, project_id, user)
    snapshot = db.query(MaterialPerformanceSnapshot).filter(
        MaterialPerformanceSnapshot.id == snapshot_id,
        MaterialPerformanceSnapshot.project_id == project_id,
    ).first()
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MaterialPerformanceSnapshot {snapshot_id} not found in project {project_id}",
        )
    return snapshot


def list_material_performance_snapshots(
    db: Session,
    project_id: str,
    user: User,
    activity_id: Optional[str] = None,
    material_item_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    performance_status: Optional[str] = None,
) -> List[MaterialPerformanceSnapshot]:
    _ensure_role(user, ["admin", "supervisor", "site_supervisor", "contractor"])
    _verify_project_access(db, project_id, user)
    q = db.query(MaterialPerformanceSnapshot).filter(MaterialPerformanceSnapshot.project_id == project_id)
    if activity_id:
        q = q.filter(MaterialPerformanceSnapshot.activity_id == activity_id)
    if material_item_id:
        q = q.filter(MaterialPerformanceSnapshot.material_item_id == material_item_id)
    if status_filter:
        q = q.filter(MaterialPerformanceSnapshot.status == status_filter)
    if performance_status:
        q = q.filter(MaterialPerformanceSnapshot.performance_status == performance_status)
    return q.order_by(MaterialPerformanceSnapshot.created_at.desc()).all()


def finalize_material_performance_snapshot(
    db: Session,
    project_id: str,
    snapshot_id: str,
    user: User,
) -> MaterialPerformanceSnapshot:
    _ensure_role(user, ["admin", "supervisor", "site_supervisor"])
    _verify_project_access(db, project_id, user)
    snapshot = (
        db.query(MaterialPerformanceSnapshot)
        .filter(
            MaterialPerformanceSnapshot.id == snapshot_id,
            MaterialPerformanceSnapshot.project_id == project_id,
        )
        .with_for_update()
        .first()
    )
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MaterialPerformanceSnapshot {snapshot_id} not found in project {project_id}",
        )
    if snapshot.status == "FINALIZED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Snapshot is already FINALIZED.",
        )
    if snapshot.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot finalize snapshot in status {snapshot.status}. Only DRAFT can be finalized.",
        )

    # Validate required inputs and provenance
    if not snapshot.canonical_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot finalize snapshot without valid canonical hash.",
        )
    if not snapshot.input_snapshot_json:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot finalize snapshot without valid input snapshot.",
        )

    # Advisory lock to protect concurrent finalization on the same logical identity
    lock_key = f"mps_fin:{project_id}:{snapshot.activity_id}:{snapshot.material_item_id}:{snapshot.performance_period_start}:{snapshot.performance_period_end}:{snapshot.reconciliation_id}"
    lock_hash = int(hashlib.sha256(lock_key.encode("utf-8")).hexdigest()[:15], 16)
    db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock_hash})

    # Check for duplicate authoritative finalized snapshot
    existing_finalized = (
        db.query(MaterialPerformanceSnapshot)
        .filter(
            MaterialPerformanceSnapshot.project_id == project_id,
            MaterialPerformanceSnapshot.activity_id == snapshot.activity_id,
            MaterialPerformanceSnapshot.material_item_id == snapshot.material_item_id,
            MaterialPerformanceSnapshot.performance_period_start == snapshot.performance_period_start,
            MaterialPerformanceSnapshot.performance_period_end == snapshot.performance_period_end,
            MaterialPerformanceSnapshot.reconciliation_id == snapshot.reconciliation_id,
            MaterialPerformanceSnapshot.status == "FINALIZED",
            MaterialPerformanceSnapshot.id != snapshot.id,
        )
        .first()
    )
    if existing_finalized:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An authoritative finalized performance snapshot already exists ({existing_finalized.id}). Supersede it before finalizing a new snapshot.",
        )

    snapshot.status = "FINALIZED"
    snapshot.finalized_by = user.id
    snapshot.finalized_at = datetime.now(timezone.utc)
    try:
        db.commit()
        db.refresh(snapshot)
        return snapshot
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An authoritative finalized performance snapshot already exists for this activity, material, and period.",
        )


def supersede_material_performance_snapshot(
    db: Session,
    project_id: str,
    snapshot_id: str,
    reason: str,
    user: User,
    replacement_snapshot_id: Optional[str] = None,
) -> MaterialPerformanceSnapshot:
    _ensure_role(user, ["admin", "supervisor", "site_supervisor"])
    _verify_project_access(db, project_id, user)
    snapshot = (
        db.query(MaterialPerformanceSnapshot)
        .filter(
            MaterialPerformanceSnapshot.id == snapshot_id,
            MaterialPerformanceSnapshot.project_id == project_id,
        )
        .with_for_update()
        .first()
    )
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MaterialPerformanceSnapshot {snapshot_id} not found in project {project_id}",
        )
    if snapshot.status == "SUPERSEDED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Snapshot is already SUPERSEDED. Superseded snapshots cannot be modified or reopened.",
        )
    if snapshot.status != "FINALIZED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot supersede snapshot in status {snapshot.status}. Only FINALIZED snapshots can be superseded.",
        )

    if replacement_snapshot_id:
        if replacement_snapshot_id == snapshot_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A snapshot cannot supersede itself.",
            )
        replacement = db.query(MaterialPerformanceSnapshot).filter(
            MaterialPerformanceSnapshot.id == replacement_snapshot_id,
            MaterialPerformanceSnapshot.project_id == project_id,
        ).first()
        if not replacement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Replacement MaterialPerformanceSnapshot {replacement_snapshot_id} not found in project {project_id}",
            )
        if replacement.status == "SUPERSEDED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Replacement snapshot cannot already be SUPERSEDED.",
            )
        if replacement.activity_id != snapshot.activity_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Replacement snapshot activity ({replacement.activity_id}) does not match superseded snapshot activity ({snapshot.activity_id}).",
            )
        if replacement.material_item_id != snapshot.material_item_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Replacement snapshot material ({replacement.material_item_id}) does not match superseded snapshot material ({snapshot.material_item_id}).",
            )
        if replacement.performance_period_start != snapshot.performance_period_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Replacement snapshot performance_period_start ({replacement.performance_period_start}) does not match superseded snapshot performance_period_start ({snapshot.performance_period_start}).",
            )
        if replacement.performance_period_end != snapshot.performance_period_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Replacement snapshot performance_period_end ({replacement.performance_period_end}) does not match superseded snapshot performance_period_end ({snapshot.performance_period_end}).",
            )
        if replacement.reconciliation_id != snapshot.reconciliation_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Replacement snapshot reconciliation_id ({replacement.reconciliation_id}) does not match superseded snapshot reconciliation_id ({snapshot.reconciliation_id}).",
            )

    snapshot.status = "SUPERSEDED"
    snapshot.superseded_by = replacement_snapshot_id
    snapshot.superseded_by_user_id = user.id
    snapshot.superseded_at = datetime.now(timezone.utc)
    snapshot.supersession_reason = reason
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_material_performance_summary(
    db: Session,
    project_id: str,
    user: User,
    activity_id: Optional[str] = None,
    material_item_id: Optional[str] = None,
) -> MaterialPerformanceSummaryResponse:
    _ensure_role(user, ["admin", "supervisor", "site_supervisor", "contractor"])
    _verify_project_access(db, project_id, user)

    # Only include active non-superseded snapshots (DRAFT or FINALIZED)
    q = db.query(MaterialPerformanceSnapshot).filter(
        MaterialPerformanceSnapshot.project_id == project_id,
        MaterialPerformanceSnapshot.status.in_(["DRAFT", "FINALIZED"]),
    )
    if activity_id:
        q = q.filter(MaterialPerformanceSnapshot.activity_id == activity_id)
    if material_item_id:
        q = q.filter(MaterialPerformanceSnapshot.material_item_id == material_item_id)

    snapshots = q.order_by(MaterialPerformanceSnapshot.created_at.desc()).all()

    total_actual: Dict[str, Decimal] = {}
    total_theoretical: Dict[str, Decimal] = {}
    total_planned: Dict[str, Decimal] = {}
    total_planned_var: Dict[str, Decimal] = {}
    total_theo_var: Dict[str, Decimal] = {}
    status_dist: Dict[str, int] = {}

    for s in snapshots:
        status_dist[s.performance_status] = status_dist.get(s.performance_status, 0) + 1

        if s.actual_consumption_quantity is not None and s.actual_consumption_unit:
            u = s.actual_consumption_unit
            total_actual[u] = total_actual.get(u, Decimal("0.0000")) + s.actual_consumption_quantity

        if s.theoretical_quantity is not None and s.theoretical_unit:
            u = s.theoretical_unit
            total_theoretical[u] = total_theoretical.get(u, Decimal("0.0000")) + s.theoretical_quantity

        if s.planned_quantity is not None and s.planned_unit:
            u = s.planned_unit
            total_planned[u] = total_planned.get(u, Decimal("0.0000")) + s.planned_quantity

    # Only compute total variance for units present in BOTH operands (do not substitute 0 for missing quantities)
    for u in total_actual:
        if u in total_planned:
            total_planned_var[u] = total_actual[u] - total_planned[u]

    for u in total_actual:
        if u in total_theoretical:
            total_theo_var[u] = total_actual[u] - total_theoretical[u]

    return MaterialPerformanceSummaryResponse(
        project_id=project_id,
        total_snapshots=len(snapshots),
        total_actual_consumption=total_actual,
        total_theoretical_consumption=total_theoretical,
        total_planned_consumption=total_planned,
        total_planned_variance=total_planned_var,
        total_theoretical_variance=total_theo_var,
        status_distribution=status_dist,
        snapshots=[MaterialPerformanceSnapshotResponse.model_validate(s) for s in snapshots],
    )
