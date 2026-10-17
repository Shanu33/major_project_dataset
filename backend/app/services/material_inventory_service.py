import hashlib
import json
import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

from app.db.models import (
    User,
    Project,
    MaterialItem,
    MaterialRequirementPlan,
    MaterialRequirementItem,
    MaterialStockLedger,
    MaterialStockBalance,
    MaterialReservation,
    MaterialAvailabilityReconciliation,
)
from app.schemas.material_inventory import (
    MaterialStockLedgerCreate,
    MaterialStockVerificationRequest,
    MaterialReservationCreate,
    MaterialAvailabilityReconciliationCreate,
)

# Deterministic unit conversion table (same canon as Phase 1O)
SUPPORTED_CONVERSIONS: Dict[Tuple[str, str], Decimal] = {
    ("TONNE", "KG"): Decimal("1000.000000"),
    ("KG", "TONNE"): Decimal("0.001000"),
    ("MT", "KG"): Decimal("1000.000000"),
    ("KG", "MT"): Decimal("0.001000"),
    ("MT", "TONNE"): Decimal("1.000000"),
    ("TONNE", "MT"): Decimal("1.000000"),
    ("M", "CM"): Decimal("100.000000"),
    ("CM", "M"): Decimal("0.010000"),
    ("M", "MM"): Decimal("1000.000000"),
    ("MM", "M"): Decimal("0.001000"),
    ("CM", "MM"): Decimal("10.000000"),
    ("MM", "CM"): Decimal("0.100000"),
}


def convert_unit(quantity: Decimal, from_unit: str, to_unit: str) -> Tuple[Decimal, Decimal, bool]:
    u_from = from_unit.strip().upper()
    u_to = to_unit.strip().upper()
    if u_from == u_to:
        return quantity, Decimal("1.000000"), True
    key = (u_from, u_to)
    if key in SUPPORTED_CONVERSIONS:
        factor = SUPPORTED_CONVERSIONS[key]
        return quantity * factor, factor, True
    return quantity, Decimal("1.000000"), False


def _verify_project_exists(db: Session, project_id: str) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    return project


def _verify_material_item(db: Session, project_id: str, material_item_id: str) -> MaterialItem:
    mat = db.query(MaterialItem).filter(MaterialItem.id == material_item_id).first()
    if not mat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material item '{material_item_id}' not found.",
        )
    if mat.project_id is not None and mat.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Material item '{material_item_id}' belongs to a different project.",
        )
    return mat


def _enable_balance_mutation(db: Session) -> None:
    db.execute(text("SET LOCAL app.allow_stock_balance_mutation = 'true'"))


def _ensure_stock_balance_row(
    db: Session,
    project_id: str,
    material_item_id: str,
    default_unit: str,
) -> MaterialStockBalance:
    """
    Guarantees concurrency safety on the first transaction using PostgreSQL atomic insert ON CONFLICT DO NOTHING,
    followed by row locking (with_for_update()).
    """
    _enable_balance_mutation(db)
    stmt = postgresql.insert(MaterialStockBalance).values(
        id=str(uuid.uuid4()),
        project_id=project_id,
        material_item_id=material_item_id,
        total_received=Decimal("0.0000"),
        total_issued=Decimal("0.0000"),
        total_adjustment_in=Decimal("0.0000"),
        total_adjustment_out=Decimal("0.0000"),
        total_returned=Decimal("0.0000"),
        total_transfer_in=Decimal("0.0000"),
        total_transfer_out=Decimal("0.0000"),
        on_hand_quantity=Decimal("0.0000"),
        reserved_quantity=Decimal("0.0000"),
        available_quantity=Decimal("0.0000"),
        unit=default_unit.strip().upper(),
        calculation_algorithm_version="STK_1.0",
        provenance_metadata={},
    ).on_conflict_do_nothing(index_elements=["project_id", "material_item_id"])
    db.execute(stmt)

    balance = (
        db.query(MaterialStockBalance)
        .filter(
            MaterialStockBalance.project_id == project_id,
            MaterialStockBalance.material_item_id == material_item_id,
        )
        .with_for_update()
        .one()
    )
    return balance


def _apply_transaction_to_balance(
    balance: MaterialStockBalance,
    transaction_type: str,
    converted_qty: Decimal,
) -> None:
    ttype = transaction_type.upper()
    if ttype == "RECEIPT":
        balance.total_received += converted_qty
        balance.on_hand_quantity += converted_qty
    elif ttype == "ISSUE":
        if balance.on_hand_quantity < converted_qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient on-hand stock: on-hand {balance.on_hand_quantity} {balance.unit} < issue quantity {converted_qty} {balance.unit}.",
            )
        balance.total_issued += converted_qty
        balance.on_hand_quantity -= converted_qty
    elif ttype == "ADJUSTMENT_IN":
        balance.total_adjustment_in += converted_qty
        balance.on_hand_quantity += converted_qty
    elif ttype == "ADJUSTMENT_OUT":
        if balance.on_hand_quantity < converted_qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient on-hand stock: on-hand {balance.on_hand_quantity} {balance.unit} < adjustment quantity {converted_qty} {balance.unit}.",
            )
        balance.total_adjustment_out += converted_qty
        balance.on_hand_quantity -= converted_qty
    elif ttype == "RETURN":
        balance.total_returned += converted_qty
        balance.on_hand_quantity += converted_qty
    elif ttype == "TRANSFER_IN":
        balance.total_transfer_in += converted_qty
        balance.on_hand_quantity += converted_qty
    elif ttype == "TRANSFER_OUT":
        if balance.on_hand_quantity < converted_qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient on-hand stock: on-hand {balance.on_hand_quantity} {balance.unit} < transfer quantity {converted_qty} {balance.unit}.",
            )
        balance.total_transfer_out += converted_qty
        balance.on_hand_quantity -= converted_qty
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported transaction type '{ttype}'.",
        )

    balance.available_quantity = max(Decimal("0.0000"), balance.on_hand_quantity - balance.reserved_quantity)
    balance.calculated_at = datetime.now(timezone.utc)


def record_stock_transaction(
    db: Session,
    project_id: str,
    data: MaterialStockLedgerCreate,
    current_user: User,
) -> MaterialStockLedger:
    _verify_project_exists(db, project_id)
    mat = _verify_material_item(db, project_id, data.material_item_id)

    user_role = current_user.role.lower()
    if user_role == "project_manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role 'project_manager' is not authorized for inventory operations.",
        )

    unit_canonical = data.unit.strip().upper()

    # Determine authoritative semantics
    if user_role == "contractor":
        # Contractor declaration: unverified, DOES NOT modify MaterialStockBalance
        source_type = "CONTRACTOR_DECLARED"
        is_authoritative = False
        verif_status = "PENDING_VERIFICATION"

        ledger_entry = MaterialStockLedger(
            id=str(uuid.uuid4()),
            project_id=project_id,
            material_item_id=data.material_item_id,
            transaction_type=data.transaction_type.upper(),
            transaction_quantity=data.transaction_quantity,
            unit=unit_canonical,
            reference_type=data.reference_type,
            reference_id=data.reference_id,
            transaction_date=data.transaction_date,
            source_type=source_type,
            source_reference=data.source_reference,
            is_authoritative=is_authoritative,
            verification_status=verif_status,
            created_by=current_user.id,
            metadata_json=data.metadata_json or {},
        )
        db.add(ledger_entry)
        db.commit()
        db.refresh(ledger_entry)
        return ledger_entry

    # Supervisor / Admin: Authoritative transaction that updates MaterialStockBalance
    source_type = data.source_type or "SUPERVISOR_VERIFIED"
    is_authoritative = True
    verif_status = "VERIFIED"

    # Concurrency safe balance fetch / creation using material item's canonical standard unit
    balance = _ensure_stock_balance_row(db, project_id, data.material_item_id, mat.standard_unit)

    converted_qty, factor, ok = convert_unit(data.transaction_quantity, unit_canonical, balance.unit)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unit mismatch: Transaction unit '{unit_canonical}' cannot be converted to balance unit '{balance.unit}'.",
        )

    _enable_balance_mutation(db)
    _apply_transaction_to_balance(balance, data.transaction_type, converted_qty)
    balance.provenance_metadata = {
        "last_transaction_type": data.transaction_type.upper(),
        "last_transaction_quantity": str(data.transaction_quantity),
        "last_transaction_unit": unit_canonical,
        "converted_quantity": str(converted_qty),
        "balance_unit": balance.unit,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    ledger_entry = MaterialStockLedger(
        id=str(uuid.uuid4()),
        project_id=project_id,
        material_item_id=data.material_item_id,
        transaction_type=data.transaction_type.upper(),
        transaction_quantity=data.transaction_quantity,
        unit=unit_canonical,
        reference_type=data.reference_type,
        reference_id=data.reference_id,
        transaction_date=data.transaction_date,
        source_type=source_type,
        source_reference=data.source_reference,
        is_authoritative=is_authoritative,
        verification_status=verif_status,
        created_by=current_user.id,
        metadata_json=data.metadata_json or {},
    )
    db.add(ledger_entry)
    db.commit()
    db.refresh(ledger_entry)
    return ledger_entry


def verify_contractor_declaration(
    db: Session,
    project_id: str,
    transaction_id: str,
    data: MaterialStockVerificationRequest,
    current_user: User,
) -> MaterialStockLedger:
    _verify_project_exists(db, project_id)

    user_role = current_user.role.lower()
    if user_role not in ["admin", "supervisor", "site_supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{current_user.role}' is not authorized to verify stock transactions.",
        )

    declaration = (
        db.query(MaterialStockLedger)
        .filter(
            MaterialStockLedger.id == transaction_id,
            MaterialStockLedger.project_id == project_id,
        )
        .first()
    )
    if not declaration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock declaration '{transaction_id}' not found in project '{project_id}'.",
        )

    if declaration.source_type != "CONTRACTOR_DECLARED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CONTRACTOR_DECLARED transactions can be verified.",
        )

    # Check if already resolved
    already_resolved = (
        db.query(MaterialStockLedger)
        .filter(
            MaterialStockLedger.project_id == project_id,
            MaterialStockLedger.source_reference == declaration.id,
        )
        .first()
    )
    if already_resolved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Declaration '{declaration.id}' has already been resolved with action '{already_resolved.verification_status}'.",
        )

    action = data.verification_action.upper()
    if action == "VERIFIED":
        final_qty = declaration.transaction_quantity
        source_type = "SUPERVISOR_VERIFIED"
        verif_status = "VERIFIED"
        is_auth = True
    elif action == "CORRECTED":
        if data.verified_quantity is None or data.verified_quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="verified_quantity must be positive when correcting a declaration.",
            )
        final_qty = data.verified_quantity
        source_type = "SUPERVISOR_CORRECTED"
        verif_status = "CORRECTED"
        is_auth = True
    elif action == "REJECTED":
        final_qty = declaration.transaction_quantity
        source_type = "SUPERVISOR_VERIFIED"
        verif_status = "REJECTED"
        is_auth = False
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid action '{action}'.")

    # If authoritative, update balance
    if is_auth:
        mat = _verify_material_item(db, project_id, declaration.material_item_id)
        balance = _ensure_stock_balance_row(db, project_id, declaration.material_item_id, mat.standard_unit)
        converted_qty, _, ok = convert_unit(final_qty, declaration.unit, balance.unit)
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unit mismatch: Verified unit '{declaration.unit}' cannot be converted to balance unit '{balance.unit}'.",
            )
        _enable_balance_mutation(db)
        _apply_transaction_to_balance(balance, declaration.transaction_type, converted_qty)

    # Append verification entry preserving original declaration immutably
    verification_entry = MaterialStockLedger(
        id=str(uuid.uuid4()),
        project_id=project_id,
        material_item_id=declaration.material_item_id,
        transaction_type=declaration.transaction_type,
        transaction_quantity=final_qty,
        unit=declaration.unit,
        reference_type="SUPERVISOR_VERIFICATION",
        reference_id=declaration.id,
        transaction_date=declaration.transaction_date,
        source_type=source_type,
        source_reference=declaration.id,
        is_authoritative=is_auth,
        verification_status=verif_status,
        created_by=current_user.id,
        metadata_json={
            "declaration_id": declaration.id,
            "declared_by": declaration.created_by,
            "declared_quantity": str(declaration.transaction_quantity),
            "verified_quantity": str(final_qty),
            "verification_action": action,
            "verification_notes": data.verification_notes,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    db.add(verification_entry)
    db.commit()
    db.refresh(verification_entry)
    return verification_entry


def list_stock_transactions(
    db: Session,
    project_id: str,
    material_item_id: Optional[str] = None,
    transaction_type: Optional[str] = None,
) -> List[MaterialStockLedger]:
    _verify_project_exists(db, project_id)
    q = db.query(MaterialStockLedger).filter(MaterialStockLedger.project_id == project_id)
    if material_item_id:
        q = q.filter(MaterialStockLedger.material_item_id == material_item_id)
    if transaction_type:
        q = q.filter(MaterialStockLedger.transaction_type == transaction_type.strip().upper())
    return q.order_by(MaterialStockLedger.transaction_date.desc(), MaterialStockLedger.created_at.desc()).all()


def list_stock_balances(
    db: Session,
    project_id: str,
) -> List[MaterialStockBalance]:
    _verify_project_exists(db, project_id)
    return db.query(MaterialStockBalance).filter(MaterialStockBalance.project_id == project_id).all()


def get_stock_balance(
    db: Session,
    project_id: str,
    material_item_id: str,
) -> MaterialStockBalance:
    _verify_project_exists(db, project_id)
    balance = (
        db.query(MaterialStockBalance)
        .filter(
            MaterialStockBalance.project_id == project_id,
            MaterialStockBalance.material_item_id == material_item_id,
        )
        .first()
    )
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock balance for material '{material_item_id}' not found in project '{project_id}'.",
        )
    return balance


def reconstruct_stock_balances(
    db: Session,
    project_id: str,
    current_user: User,
) -> List[MaterialStockBalance]:
    _verify_project_exists(db, project_id)

    # Enable service mutation of balance cache
    _enable_balance_mutation(db)

    # Find distinct materials from authoritative ledger entries
    materials = (
        db.query(MaterialStockLedger.material_item_id)
        .filter(
            MaterialStockLedger.project_id == project_id,
            MaterialStockLedger.is_authoritative == True,
        )
        .distinct()
        .all()
    )
    material_ids = [m[0] for m in materials]

    reconstructed: List[MaterialStockBalance] = []

    for mid in material_ids:
        entries = (
            db.query(MaterialStockLedger)
            .filter(
                MaterialStockLedger.project_id == project_id,
                MaterialStockLedger.material_item_id == mid,
                MaterialStockLedger.is_authoritative == True,
            )
            .order_by(MaterialStockLedger.transaction_date.asc(), MaterialStockLedger.created_at.asc())
            .all()
        )

        if not entries:
            continue

        mat = db.query(MaterialItem).filter(MaterialItem.id == mid).first()
        base_unit = mat.standard_unit if mat else entries[0].unit

        tot_rec = Decimal("0.0000")
        tot_iss = Decimal("0.0000")
        tot_adj_in = Decimal("0.0000")
        tot_adj_out = Decimal("0.0000")
        tot_ret = Decimal("0.0000")
        tot_tr_in = Decimal("0.0000")
        tot_tr_out = Decimal("0.0000")

        for ent in entries:
            conv_qty, _, ok = convert_unit(ent.transaction_quantity, ent.unit, base_unit)
            if not ok:
                conv_qty = ent.transaction_quantity

            tt = ent.transaction_type
            if tt == "RECEIPT":
                tot_rec += conv_qty
            elif tt == "ISSUE":
                tot_iss += conv_qty
            elif tt == "ADJUSTMENT_IN":
                tot_adj_in += conv_qty
            elif tt == "ADJUSTMENT_OUT":
                tot_adj_out += conv_qty
            elif tt == "RETURN":
                tot_ret += conv_qty
            elif tt == "TRANSFER_IN":
                tot_tr_in += conv_qty
            elif tt == "TRANSFER_OUT":
                tot_tr_out += conv_qty

        on_hand = (tot_rec + tot_adj_in + tot_ret + tot_tr_in) - (tot_iss + tot_adj_out + tot_tr_out)

        # Sum active reservations
        active_reservations = (
            db.query(MaterialReservation)
            .filter(
                MaterialReservation.project_id == project_id,
                MaterialReservation.material_item_id == mid,
                MaterialReservation.status == "ACTIVE",
            )
            .all()
        )
        res_sum = Decimal("0.0000")
        for r in active_reservations:
            r_conv, _, r_ok = convert_unit(r.reserved_quantity, r.unit, base_unit)
            if r_ok:
                res_sum += r_conv
            else:
                res_sum += r.reserved_quantity

        avail = max(Decimal("0.0000"), on_hand - res_sum)

        balance = _ensure_stock_balance_row(db, project_id, mid, base_unit)
        balance.total_received = tot_rec
        balance.total_issued = tot_iss
        balance.total_adjustment_in = tot_adj_in
        balance.total_adjustment_out = tot_adj_out
        balance.total_returned = tot_ret
        balance.total_transfer_in = tot_tr_in
        balance.total_transfer_out = tot_tr_out
        balance.on_hand_quantity = max(Decimal("0.0000"), on_hand)
        balance.reserved_quantity = res_sum
        balance.available_quantity = avail
        balance.calculated_at = datetime.now(timezone.utc)
        balance.provenance_metadata = {"reconstructed_at": datetime.now(timezone.utc).isoformat()}
        reconstructed.append(balance)

    db.commit()
    for b in reconstructed:
        db.refresh(b)
    return reconstructed


def create_material_reservation(
    db: Session,
    project_id: str,
    data: MaterialReservationCreate,
    current_user: User,
) -> MaterialReservation:
    _verify_project_exists(db, project_id)
    _verify_material_item(db, project_id, data.material_item_id)

    # Verify plan and requirement item
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
            detail=f"Material requirement plan '{data.material_requirement_plan_id}' not found in project '{project_id}'.",
        )

    req_item = (
        db.query(MaterialRequirementItem)
        .filter(
            MaterialRequirementItem.id == data.material_requirement_item_id,
            MaterialRequirementItem.material_requirement_plan_id == plan.id,
            MaterialRequirementItem.project_id == project_id,
        )
        .first()
    )
    if not req_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material requirement item '{data.material_requirement_item_id}' not found in plan '{plan.id}'.",
        )

    if req_item.material_item_id != data.material_item_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Material item does not match requirement item material.",
        )

    # Concurrency lock on balance
    balance = (
        db.query(MaterialStockBalance)
        .filter(
            MaterialStockBalance.project_id == project_id,
            MaterialStockBalance.material_item_id == data.material_item_id,
        )
        .with_for_update()
        .first()
    )

    if not balance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reserve: No stock balance exists for material '{data.material_item_id}'.",
        )

    req_unit = data.unit.strip().upper()
    converted_qty, factor, ok = convert_unit(data.reserved_quantity, req_unit, balance.unit)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot convert reservation unit '{req_unit}' to stock balance unit '{balance.unit}'.",
        )

    if balance.available_quantity < converted_qty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient available stock: available {balance.available_quantity} {balance.unit} < requested reservation {converted_qty} {balance.unit}.",
        )

    reservation = MaterialReservation(
        id=str(uuid.uuid4()),
        project_id=project_id,
        material_item_id=data.material_item_id,
        material_requirement_plan_id=data.material_requirement_plan_id,
        material_requirement_item_id=data.material_requirement_item_id,
        reserved_quantity=converted_qty,
        unit=balance.unit,
        status="ACTIVE",
        reservation_date=data.reservation_date,
        created_by=current_user.id,
        metadata_json=data.metadata_json or {},
    )
    db.add(reservation)

    _enable_balance_mutation(db)
    balance.reserved_quantity += converted_qty
    balance.available_quantity = max(Decimal("0.0000"), balance.on_hand_quantity - balance.reserved_quantity)
    balance.calculated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(reservation)
    return reservation


def release_material_reservation(
    db: Session,
    project_id: str,
    reservation_id: str,
    current_user: User,
) -> MaterialReservation:
    _verify_project_exists(db, project_id)

    reservation = (
        db.query(MaterialReservation)
        .filter(
            MaterialReservation.id == reservation_id,
            MaterialReservation.project_id == project_id,
        )
        .first()
    )
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material reservation '{reservation_id}' not found in project '{project_id}'.",
        )

    if reservation.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Reservation '{reservation_id}' is not ACTIVE (current status: {reservation.status}).",
        )

    balance = (
        db.query(MaterialStockBalance)
        .filter(
            MaterialStockBalance.project_id == project_id,
            MaterialStockBalance.material_item_id == reservation.material_item_id,
        )
        .with_for_update()
        .first()
    )

    if balance is not None:
        _enable_balance_mutation(db)
        balance.reserved_quantity = max(Decimal("0.0000"), balance.reserved_quantity - reservation.reserved_quantity)
        balance.available_quantity = max(Decimal("0.0000"), balance.on_hand_quantity - balance.reserved_quantity)
        balance.calculated_at = datetime.now(timezone.utc)

    reservation.status = "RELEASED"
    reservation.released_at = datetime.now(timezone.utc)
    reservation.released_by = current_user.id

    db.commit()
    db.refresh(reservation)
    return reservation


def list_material_reservations(
    db: Session,
    project_id: str,
    plan_id: Optional[str] = None,
    material_item_id: Optional[str] = None,
    res_status: Optional[str] = None,
) -> List[MaterialReservation]:
    _verify_project_exists(db, project_id)
    q = db.query(MaterialReservation).filter(MaterialReservation.project_id == project_id)
    if plan_id:
        q = q.filter(MaterialReservation.material_requirement_plan_id == plan_id)
    if material_item_id:
        q = q.filter(MaterialReservation.material_item_id == material_item_id)
    if res_status:
        q = q.filter(MaterialReservation.status == res_status.strip().upper())
    return q.order_by(MaterialReservation.reservation_date.desc(), MaterialReservation.created_at.desc()).all()


def create_availability_reconciliation(
    db: Session,
    project_id: str,
    data: MaterialAvailabilityReconciliationCreate,
    current_user: User,
) -> List[MaterialAvailabilityReconciliation]:
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
            detail=f"Material requirement plan '{data.material_requirement_plan_id}' not found in project '{project_id}'.",
        )

    requirement_items = (
        db.query(MaterialRequirementItem)
        .filter(
            MaterialRequirementItem.material_requirement_plan_id == plan.id,
            MaterialRequirementItem.project_id == project_id,
        )
        .all()
    )
    if not requirement_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Material requirement plan '{plan.id}' contains no requirement items to reconcile.",
        )

    results: List[MaterialAvailabilityReconciliation] = []

    for item in requirement_items:
        req_qty = getattr(item, "requirement_quantity", getattr(item, "required_quantity", Decimal("0.0000")))
        req_unit = getattr(item, "requirement_unit", getattr(item, "unit", "")).strip().upper()

        balance = (
            db.query(MaterialStockBalance)
            .filter(
                MaterialStockBalance.project_id == project_id,
                MaterialStockBalance.material_item_id == item.material_item_id,
            )
            .first()
        )

        if balance is None:
            avail_status = "NO_STOCK_DATA"
            on_hand = None
            reserved = None
            avail = None
            shortage = None
            factor = None
            conv_ok = True
        else:
            avail_conv, factor, ok = convert_unit(balance.available_quantity, balance.unit, req_unit)
            if not ok:
                avail_status = "UNIT_MISMATCH"
                on_hand = balance.on_hand_quantity
                reserved = balance.reserved_quantity
                avail = balance.available_quantity
                shortage = None
                factor = None
                conv_ok = False
            else:
                on_hand_conv, _, _ = convert_unit(balance.on_hand_quantity, balance.unit, req_unit)
                reserved_conv, _, _ = convert_unit(balance.reserved_quantity, balance.unit, req_unit)
                on_hand = on_hand_conv
                reserved = reserved_conv
                avail = avail_conv
                conv_ok = True
                if avail >= req_qty:
                    avail_status = "AVAILABLE"
                    shortage = Decimal("0.0000")
                elif avail > Decimal("0.0000"):
                    avail_status = "PARTIALLY_AVAILABLE"
                    shortage = req_qty - avail
                else:
                    avail_status = "SHORTAGE"
                    shortage = req_qty

        # Canonical SHA-256 hash computation
        hash_payload = {
            "algorithm_version": "AVAIL_1.0",
            "available_quantity": str(avail) if avail is not None else None,
            "availability_status": avail_status,
            "material_item_id": item.material_item_id,
            "material_requirement_item_id": item.id,
            "material_requirement_plan_id": plan.id,
            "project_id": project_id,
            "required_quantity": str(req_qty),
            "required_unit": req_unit,
            "shortage_quantity": str(shortage) if shortage is not None else None,
        }
        recon_hash = hashlib.sha256(
            json.dumps(
                hash_payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode("utf-8")
        ).hexdigest()

        provenance = {
            "reconciliation_hash": recon_hash,
            "stock_balance_unit": balance.unit if balance else None,
            "conversion_factor": str(factor) if factor is not None else None,
            "conversion_ok": conv_ok,
            "activity_id": item.activity_id,
            "custom_metadata": data.metadata_json or {},
        }

        recon = MaterialAvailabilityReconciliation(
            id=str(uuid.uuid4()),
            project_id=project_id,
            material_requirement_plan_id=plan.id,
            material_requirement_item_id=item.id,
            material_item_id=item.material_item_id,
            required_quantity=req_qty,
            required_unit=req_unit,
            on_hand_quantity=on_hand,
            reserved_quantity=reserved,
            available_quantity=avail,
            shortage_quantity=shortage,
            availability_status=avail_status,
            calculation_algorithm_version="AVAIL_1.0",
            provenance_metadata=provenance,
            created_by=current_user.id,
        )
        db.add(recon)
        results.append(recon)

    db.commit()
    for r in results:
        db.refresh(r)
    return results


def list_availability_reconciliations(
    db: Session,
    project_id: str,
    plan_id: Optional[str] = None,
    material_item_id: Optional[str] = None,
    avail_status: Optional[str] = None,
) -> List[MaterialAvailabilityReconciliation]:
    _verify_project_exists(db, project_id)
    q = db.query(MaterialAvailabilityReconciliation).filter(
        MaterialAvailabilityReconciliation.project_id == project_id
    )
    if plan_id:
        q = q.filter(MaterialAvailabilityReconciliation.material_requirement_plan_id == plan_id)
    if material_item_id:
        q = q.filter(MaterialAvailabilityReconciliation.material_item_id == material_item_id)
    if avail_status:
        q = q.filter(MaterialAvailabilityReconciliation.availability_status == avail_status.strip().upper())
    return q.order_by(MaterialAvailabilityReconciliation.calculated_at.desc()).all()


def get_availability_reconciliation(
    db: Session,
    project_id: str,
    reconciliation_id: str,
) -> MaterialAvailabilityReconciliation:
    _verify_project_exists(db, project_id)
    recon = (
        db.query(MaterialAvailabilityReconciliation)
        .filter(
            MaterialAvailabilityReconciliation.id == reconciliation_id,
            MaterialAvailabilityReconciliation.project_id == project_id,
        )
        .first()
    )
    if not recon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material availability reconciliation '{reconciliation_id}' not found in project '{project_id}'.",
        )
    return recon
