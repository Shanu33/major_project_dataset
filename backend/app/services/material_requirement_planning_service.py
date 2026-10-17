import hashlib
import json
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.models import (
    User,
    Project,
    MonitoringBaseline,
    ConstructionSchedule,
    ConstructionActivity,
    ActivityScheduleResult,
    MaterialItem,
    MaterialPlan,
    MaterialRequirementPlan,
    MaterialRequirementItem,
    ProcurementRequirement,
)
from app.schemas.material_requirement_planning import (
    MaterialRequirementPlanCreate,
    MaterialRequirementGenerateRequest,
    ProcurementRequirementsGenerateRequest,
)

# Explicit deterministic unit conversion table
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


def _compute_mrp_hash(
    plan_id: str,
    project_id: str,
    baseline_id: str,
    plan_version: str,
    items: List[MaterialRequirementItem],
) -> str:
    serialized_items = []
    for item in items:
        serialized_items.append({
            "activity_id": str(item.activity_id),
            "conversion_factor": f"{Decimal(str(item.conversion_factor)):.6f}",
            "material_item_id": str(item.material_item_id),
            "material_plan_id": str(item.material_plan_id),
            "requirement_quantity": f"{Decimal(str(item.requirement_quantity)):.4f}",
            "requirement_unit": str(item.requirement_unit),
            "source_quantity": f"{Decimal(str(item.source_quantity)):.4f}",
            "source_unit": str(item.source_unit),
        })
    serialized_items.sort(key=lambda x: (x["material_plan_id"], x["material_item_id"]))
    payload = {
        "algorithm_version": "MRP_1.0",
        "baseline_id": str(baseline_id),
        "items": serialized_items,
        "plan_id": str(plan_id),
        "plan_version": str(plan_version),
        "project_id": str(project_id),
    }
    payload_bytes = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload_bytes).hexdigest()


def _check_project_membership(db: Session, project_id: str, current_user: User) -> None:
    if current_user.role.lower() not in ["admin", "supervisor", "site_supervisor", "contractor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{current_user.role}' is not authorized for Phase 1O operations.",
        )
    if current_user.role.lower() == "admin":
        return
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    is_member = any(m.user_id == current_user.id for m in proj.members)
    if not is_member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Not a project member.")


def _enforce_role(current_user: User, allowed_roles: List[str], action_name: str) -> None:
    role = current_user.role.lower()
    if role not in [r.lower() for r in allowed_roles]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{current_user.role}' is not authorized to {action_name}.",
        )


def create_material_requirement_plan(
    db: Session,
    project_id: str,
    payload: MaterialRequirementPlanCreate,
    current_user: User,
) -> MaterialRequirementPlan:
    _enforce_role(current_user, ["admin", "supervisor", "site_supervisor"], "create material requirement plan")
    _check_project_membership(db, project_id, current_user)

    # 1. Verify baseline belongs to project and is ACTIVE
    baseline = (
        db.query(MonitoringBaseline)
        .filter(MonitoringBaseline.id == payload.baseline_id, MonitoringBaseline.project_id == project_id)
        .first()
    )
    if not baseline:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"MonitoringBaseline {payload.baseline_id} not found in project {project_id}.",
        )
    if baseline.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"MonitoringBaseline {payload.baseline_id} must have status 'ACTIVE', found '{baseline.status}'.",
        )

    # 2. Check plan version uniqueness
    existing_version = (
        db.query(MaterialRequirementPlan)
        .filter(
            MaterialRequirementPlan.project_id == project_id,
            MaterialRequirementPlan.plan_version == payload.plan_version.strip(),
        )
        .first()
    )
    if existing_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"MaterialRequirementPlan version '{payload.plan_version}' already exists for project {project_id}.",
        )

    plan = MaterialRequirementPlan(
        project_id=project_id,
        baseline_id=baseline.id,
        plan_version=payload.plan_version.strip(),
        status="DRAFT",
        algorithm_version="MRP_1.0",
        input_snapshot_json={
            "baseline_id": baseline.id,
            "schedule_id": baseline.schedule_id,
            "schedule_version": baseline.schedule_version,
            "baseline_start_date": str(baseline.baseline_start_date) if baseline.baseline_start_date else None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        created_by=current_user.id,
        metadata_json=payload.metadata_json or {},
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def list_material_requirement_plans(
    db: Session,
    project_id: str,
    current_user: User,
) -> List[MaterialRequirementPlan]:
    _check_project_membership(db, project_id, current_user)
    return (
        db.query(MaterialRequirementPlan)
        .filter(MaterialRequirementPlan.project_id == project_id)
        .order_by(MaterialRequirementPlan.created_at.desc())
        .all()
    )


def get_material_requirement_plan(
    db: Session,
    project_id: str,
    plan_id: str,
    current_user: User,
) -> MaterialRequirementPlan:
    _check_project_membership(db, project_id, current_user)
    plan = (
        db.query(MaterialRequirementPlan)
        .filter(MaterialRequirementPlan.id == plan_id, MaterialRequirementPlan.project_id == project_id)
        .first()
    )
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MaterialRequirementPlan {plan_id} not found in project {project_id}.",
        )
    return plan


def generate_material_requirement_items(
    db: Session,
    project_id: str,
    plan_id: str,
    payload: MaterialRequirementGenerateRequest,
    current_user: User,
) -> List[MaterialRequirementItem]:
    _enforce_role(current_user, ["admin", "supervisor", "site_supervisor"], "generate material requirement items")
    _check_project_membership(db, project_id, current_user)

    plan = (
        db.query(MaterialRequirementPlan)
        .filter(MaterialRequirementPlan.id == plan_id, MaterialRequirementPlan.project_id == project_id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"MaterialRequirementPlan {plan_id} not found.")
    if plan.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot generate items for plan in '{plan.status}' status. Only DRAFT plans can be modified.",
        )

    # Validate baseline
    baseline = (
        db.query(MonitoringBaseline)
        .filter(MonitoringBaseline.id == plan.baseline_id, MonitoringBaseline.project_id == project_id)
        .first()
    )
    if not baseline or baseline.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Referenced MonitoringBaseline must be ACTIVE to generate requirements.",
        )

    # Fetch active Phase 1N material plans
    mat_plans = (
        db.query(MaterialPlan)
        .filter(
            MaterialPlan.project_id == project_id,
            MaterialPlan.baseline_id == baseline.id,
            MaterialPlan.status == "ACTIVE",
        )
        .all()
    )
    if not mat_plans:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No active Phase 1N MaterialPlan records found for project {project_id} and baseline {baseline.id}.",
        )

    # Fetch schedule results for date derivation
    sched_results = (
        db.query(ActivityScheduleResult)
        .filter(ActivityScheduleResult.schedule_id == baseline.schedule_id)
        .all()
    )
    sched_map = {sr.activity_id: sr for sr in sched_results}

    # Clear existing draft items and procurement requirements
    db.query(ProcurementRequirement).filter(ProcurementRequirement.material_requirement_plan_id == plan.id).delete()
    db.query(MaterialRequirementItem).filter(MaterialRequirementItem.material_requirement_plan_id == plan.id).delete()

    created_items: List[MaterialRequirementItem] = []
    min_start: Optional[date] = None
    max_end: Optional[date] = None

    qty_source = payload.quantity_source.strip().upper()
    if qty_source not in ["GROSS", "NET"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="quantity_source must be 'GROSS' or 'NET'.",
        )

    for mp in mat_plans:
        # Cross-project validations
        if mp.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cross-project MaterialPlan reference detected: {mp.id}.",
            )
        act = db.query(ConstructionActivity).filter(ConstructionActivity.id == mp.activity_id).first()
        if not act or act.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Activity {mp.activity_id} does not belong to project {project_id}.",
            )
        mat = db.query(MaterialItem).filter(MaterialItem.id == mp.material_item_id).first()
        if not mat or (mat.project_id is not None and mat.project_id != project_id):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Material item {mp.material_item_id} does not belong to project {project_id}.",
            )

        # Quantity derivation
        if qty_source == "GROSS":
            src_qty = Decimal(str(mp.gross_planned_quantity))
        else:
            src_qty = Decimal(str(mp.planned_quantity))

        if src_qty < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Negative source quantity ({src_qty}) in MaterialPlan {mp.id}.",
            )

        # Unit conversion
        if payload.target_unit:
            conv_qty, conv_factor, is_supp = convert_unit(src_qty, mp.unit, payload.target_unit)
            if not is_supp:
                req_qty = src_qty
                req_unit = mp.unit
                conv_factor = Decimal("1.000000")
                unit_classification = "REQUIRES_INPUT"
                unit_status = "REQUIRES_INPUT"
            else:
                req_qty = conv_qty
                req_unit = payload.target_unit.strip().upper()
                unit_classification = "CALCULATED"
                unit_status = "PLANNED"
        else:
            req_qty = src_qty
            req_unit = mp.unit
            conv_factor = Decimal("1.000000")
            unit_classification = "CALCULATED"
            unit_status = "PLANNED"

        # Date derivation from frozen schedule
        res = sched_map.get(mp.activity_id)
        if res and baseline.baseline_start_date is not None:
            # Deterministic calculation: early start and early finish in days
            start_d = baseline.baseline_start_date + timedelta(days=int(res.es))
            end_d = baseline.baseline_start_date + timedelta(days=int(res.ef))
            date_classification = "CALCULATED"
            date_status = "PLANNED"
            if min_start is None or start_d < min_start:
                min_start = start_d
            if max_end is None or end_d > max_end:
                max_end = end_d
        else:
            # Missing planned date -> no invented date!
            start_d = None
            end_d = None
            date_classification = "REQUIRES_INPUT"
            date_status = "REQUIRES_INPUT"

        # Classification synthesis
        if unit_classification == "REQUIRES_INPUT" or date_classification == "REQUIRES_INPUT":
            final_classification = "REQUIRES_INPUT"
            final_status = "REQUIRES_INPUT"
        else:
            final_classification = "CALCULATED"
            final_status = "PLANNED"

        provenance_metadata = {
            "material_plan_id": mp.id,
            "activity_id": mp.activity_id,
            "activity_code": act.activity_code if act else None,
            "mix_design_id": mp.mix_design_id,
            "quantity_source": qty_source,
            "net_planned_quantity": str(mp.planned_quantity),
            "gross_planned_quantity": str(mp.gross_planned_quantity),
            "waste_allowance_pct": str(mp.waste_allowance_pct),
            "estimation_method": mp.estimation_method,
            "schedule_id": baseline.schedule_id,
            "schedule_es_days": str(res.es) if res else None,
            "schedule_ef_days": str(res.ef) if res else None,
            "unit_conversion_applied": payload.target_unit is not None and unit_classification != "REQUIRES_INPUT",
        }

        item = MaterialRequirementItem(
            project_id=project_id,
            material_requirement_plan_id=plan.id,
            material_item_id=mp.material_item_id,
            activity_id=mp.activity_id,
            material_plan_id=mp.id,
            requirement_quantity=req_qty,
            requirement_unit=req_unit,
            requirement_date_start=start_d,
            requirement_date_end=end_d,
            source_quantity=src_qty,
            source_unit=mp.unit,
            conversion_factor=conv_factor,
            planning_method="DIRECT_PHASE_1N_DERIVATION",
            classification=final_classification,
            provenance_metadata=provenance_metadata,
            status=final_status,
        )
        db.add(item)
        created_items.append(item)

    plan.planning_start_date = min_start
    plan.planning_end_date = max_end

    # Deterministic plan hash computation
    plan_hash = _compute_mrp_hash(plan.id, project_id, baseline.id, plan.plan_version, created_items)
    snapshot = dict(plan.input_snapshot_json or {})
    snapshot["plan_hash"] = plan_hash
    snapshot["items_generated_count"] = len(created_items)
    snapshot["quantity_source"] = qty_source
    plan.input_snapshot_json = snapshot

    db.commit()
    for it in created_items:
        db.refresh(it)
    return created_items


def list_material_requirement_items(
    db: Session,
    project_id: str,
    plan_id: str,
    current_user: User,
) -> List[MaterialRequirementItem]:
    _check_project_membership(db, project_id, current_user)
    plan = (
        db.query(MaterialRequirementPlan)
        .filter(MaterialRequirementPlan.id == plan_id, MaterialRequirementPlan.project_id == project_id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"MaterialRequirementPlan {plan_id} not found.")

    return (
        db.query(MaterialRequirementItem)
        .filter(MaterialRequirementItem.material_requirement_plan_id == plan.id)
        .order_by(MaterialRequirementItem.created_at.asc())
        .all()
    )


def generate_procurement_requirements(
    db: Session,
    project_id: str,
    plan_id: str,
    payload: ProcurementRequirementsGenerateRequest,
    current_user: User,
) -> List[ProcurementRequirement]:
    _enforce_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"], "provide procurement planning inputs")
    _check_project_membership(db, project_id, current_user)

    plan = (
        db.query(MaterialRequirementPlan)
        .filter(MaterialRequirementPlan.id == plan_id, MaterialRequirementPlan.project_id == project_id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"MaterialRequirementPlan {plan_id} not found.")
    if plan.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot generate procurement requirements for plan in '{plan.status}' status. Only DRAFT plans can be modified.",
        )

    items = (
        db.query(MaterialRequirementItem)
        .filter(MaterialRequirementItem.material_requirement_plan_id == plan.id)
        .all()
    )
    if not items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="MaterialRequirementPlan has no items. Generate items first.",
        )

    # Input map
    inputs_map: Dict[str, Optional[Decimal]] = {}
    plan_mat_ids = {it.material_item_id for it in items}
    for inp in payload.inputs:
        if inp.already_planned_quantity is not None and inp.already_planned_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"already_planned_quantity cannot be negative ({inp.already_planned_quantity}).",
            )
        if inp.material_item_id not in plan_mat_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"material_item_id '{inp.material_item_id}' in procurement inputs is not part of requirement plan {plan.id}.",
            )
        inputs_map[inp.material_item_id] = inp.already_planned_quantity

    # Group items by (material_item_id, requirement_unit)
    grouped: Dict[Tuple[str, str], List[MaterialRequirementItem]] = {}
    for it in items:
        key = (it.material_item_id, it.requirement_unit)
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(it)

    # Clear existing draft procurement requirements
    db.query(ProcurementRequirement).filter(ProcurementRequirement.material_requirement_plan_id == plan.id).delete()

    created_proc_reqs: List[ProcurementRequirement] = []

    for (mat_id, unit), group_items in grouped.items():
        total_req_qty = sum(Decimal(str(gi.requirement_quantity)) for gi in group_items)
        dates_start = [gi.requirement_date_start for gi in group_items if gi.requirement_date_start is not None]
        dates_end = [gi.requirement_date_end for gi in group_items if gi.requirement_date_end is not None]

        period_start = min(dates_start) if dates_start else None
        period_end = max(dates_end) if dates_end else None

        # Check if already_planned_quantity was explicitly supplied
        if mat_id in inputs_map and inputs_map[mat_id] is not None:
            already_planned = Decimal(str(inputs_map[mat_id]))
            proc_qty = max(Decimal("0.0000"), total_req_qty - already_planned)
            proc_status = "PLANNED"
        else:
            # DO NOT ASSUME ZERO! Return REQUIRES_INPUT
            already_planned = None
            proc_qty = None
            proc_status = "REQUIRES_INPUT"

        pr = ProcurementRequirement(
            project_id=project_id,
            material_requirement_plan_id=plan.id,
            material_item_id=mat_id,
            requirement_period_start=period_start,
            requirement_period_end=period_end,
            required_quantity=total_req_qty,
            unit=unit,
            already_planned_quantity=already_planned,
            procurement_quantity=proc_qty,
            planning_method="PERIOD_AGGREGATED_NET_REQUIREMENT",
            status=proc_status,
            provenance_metadata={
                "items_count": len(group_items),
                "aggregated_material_item_id": mat_id,
                "input_source": "EXPLICIT_USER_SUPPLIED" if already_planned is not None else "MISSING_INPUT",
            },
        )
        db.add(pr)
        created_proc_reqs.append(pr)

    db.commit()
    for pr in created_proc_reqs:
        db.refresh(pr)
    return created_proc_reqs


def list_procurement_requirements(
    db: Session,
    project_id: str,
    plan_id: str,
    current_user: User,
) -> List[ProcurementRequirement]:
    _check_project_membership(db, project_id, current_user)
    plan = (
        db.query(MaterialRequirementPlan)
        .filter(MaterialRequirementPlan.id == plan_id, MaterialRequirementPlan.project_id == project_id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"MaterialRequirementPlan {plan_id} not found.")

    return (
        db.query(ProcurementRequirement)
        .filter(ProcurementRequirement.material_requirement_plan_id == plan.id)
        .order_by(ProcurementRequirement.created_at.asc())
        .all()
    )


def activate_material_requirement_plan(
    db: Session,
    project_id: str,
    plan_id: str,
    current_user: User,
) -> MaterialRequirementPlan:
    _enforce_role(current_user, ["admin", "supervisor", "site_supervisor"], "activate material requirement plan")
    _check_project_membership(db, project_id, current_user)

    # Concurrency safe row-level locking
    target_plan = (
        db.query(MaterialRequirementPlan)
        .filter(MaterialRequirementPlan.id == plan_id, MaterialRequirementPlan.project_id == project_id)
        .with_for_update()
        .first()
    )
    if not target_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"MaterialRequirementPlan {plan_id} not found.")

    if target_plan.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot activate plan in '{target_plan.status}' status. Only DRAFT plans can be activated.",
        )

    # Must have generated items
    items_count = (
        db.query(MaterialRequirementItem)
        .filter(MaterialRequirementItem.material_requirement_plan_id == target_plan.id)
        .count()
    )
    if items_count == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot activate plan with zero items. Generate items first.",
        )

    # Lock and supersede any currently ACTIVE plan for this project
    current_active = (
        db.query(MaterialRequirementPlan)
        .filter(
            MaterialRequirementPlan.project_id == project_id,
            MaterialRequirementPlan.status == "ACTIVE",
        )
        .with_for_update()
        .first()
    )
    now = datetime.now(timezone.utc)
    if current_active:
        current_active.status = "SUPERSEDED"
        current_active.superseded_at = now
        db.flush()

    target_plan.status = "ACTIVE"
    db.commit()
    db.refresh(target_plan)
    return target_plan


def supersede_material_requirement_plan(
    db: Session,
    project_id: str,
    plan_id: str,
    current_user: User,
) -> MaterialRequirementPlan:
    _enforce_role(current_user, ["admin", "supervisor", "site_supervisor"], "supersede material requirement plan")
    _check_project_membership(db, project_id, current_user)

    target_plan = (
        db.query(MaterialRequirementPlan)
        .filter(MaterialRequirementPlan.id == plan_id, MaterialRequirementPlan.project_id == project_id)
        .with_for_update()
        .first()
    )
    if not target_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"MaterialRequirementPlan {plan_id} not found.")

    if target_plan.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot supersede plan in '{target_plan.status}' status. Only ACTIVE plans can be superseded.",
        )

    target_plan.status = "SUPERSEDED"
    target_plan.superseded_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(target_plan)
    return target_plan
