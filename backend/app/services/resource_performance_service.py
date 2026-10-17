import hashlib
import json
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.models import (
    ActivityRateMapping,
    ConstructionActivity,
    CostRate,
    DailyActivityProgress,
    DailyActivityProgressVerification,
    DailyProgressReport,
    MaterialItem,
    MaterialPerformanceSnapshot,
    PeriodCertificateItem,
    PeriodProgressCertificate,
    Project,
    ProjectMember,
    Resource,
    ResourcePerformanceSnapshot,
    ResourcePlan,
    User,
)
from app.schemas.resource_performance import (
    ResourcePerformanceCreateRequest,
    ResourcePerformanceSnapshotResponse,
    ResourcePerformanceSummaryResponse,
)


SUPPORTED_CONVERSIONS: Dict[Tuple[str, str], Decimal] = {
    # Mass
    ("TONNE", "KG"): Decimal("1000.000000"),
    ("KG", "TONNE"): Decimal("0.001000"),
    ("MT", "KG"): Decimal("1000.000000"),
    ("KG", "MT"): Decimal("0.001000"),
    ("MT", "TONNE"): Decimal("1.000000"),
    ("TONNE", "MT"): Decimal("1.000000"),
    # Length
    ("M", "CM"): Decimal("100.000000"),
    ("CM", "M"): Decimal("0.010000"),
    ("M", "MM"): Decimal("1000.000000"),
    ("MM", "M"): Decimal("0.001000"),
    ("CM", "MM"): Decimal("10.000000"),
    ("MM", "CM"): Decimal("0.100000"),
    # Time / Effort (Labour Hours)
    ("LABOUR-HOUR", "HOUR"): Decimal("1.000000"),
    ("HOUR", "LABOUR-HOUR"): Decimal("1.000000"),
    ("LABOUR-HOURS", "HOURS"): Decimal("1.000000"),
    ("HOURS", "LABOUR-HOURS"): Decimal("1.000000"),
    ("LABOUR-HOUR", "LABOUR-HOURS"): Decimal("1.000000"),
    ("LABOUR-HOURS", "LABOUR-HOUR"): Decimal("1.000000"),
    ("LABOUR-HOUR", "HOURS"): Decimal("1.000000"),
    ("HOURS", "LABOUR-HOUR"): Decimal("1.000000"),
    ("LABOUR-HOURS", "HOUR"): Decimal("1.000000"),
    ("HOUR", "LABOUR-HOURS"): Decimal("1.000000"),
    ("HOUR", "HOURS"): Decimal("1.000000"),
    ("HOURS", "HOUR"): Decimal("1.000000"),
    ("HR", "HOUR"): Decimal("1.000000"),
    ("HOUR", "HR"): Decimal("1.000000"),
    ("HRS", "HOURS"): Decimal("1.000000"),
    ("HOURS", "HRS"): Decimal("1.000000"),
    # Time / Effort (Equipment Hours)
    ("EQUIPMENT-HOUR", "HOUR"): Decimal("1.000000"),
    ("HOUR", "EQUIPMENT-HOUR"): Decimal("1.000000"),
    ("EQUIPMENT-HOURS", "HOURS"): Decimal("1.000000"),
    ("HOURS", "EQUIPMENT-HOURS"): Decimal("1.000000"),
    ("EQUIPMENT-HOUR", "EQUIPMENT-HOURS"): Decimal("1.000000"),
    ("EQUIPMENT-HOURS", "EQUIPMENT-HOUR"): Decimal("1.000000"),
    ("EQUIPMENT-HOUR", "HOURS"): Decimal("1.000000"),
    ("HOURS", "EQUIPMENT-HOUR"): Decimal("1.000000"),
    ("EQUIPMENT-HOURS", "HOUR"): Decimal("1.000000"),
    ("HOUR", "EQUIPMENT-HOURS"): Decimal("1.000000"),
    # Volume
    ("M3", "CUM"): Decimal("1.000000"),
    ("CUM", "M3"): Decimal("1.000000"),
    # Area
    ("M2", "SQM"): Decimal("1.000000"),
    ("SQM", "M2"): Decimal("1.000000"),
    # Packaging
    ("BAG", "BAGS"): Decimal("1.000000"),
    ("BAGS", "BAG"): Decimal("1.000000"),
    # Count
    ("NOS", "NO"): Decimal("1.000000"),
    ("NO", "NOS"): Decimal("1.000000"),
    ("EACH", "EA"): Decimal("1.000000"),
    ("EA", "EACH"): Decimal("1.000000"),
    ("PCS", "PIECES"): Decimal("1.000000"),
    ("PIECES", "PCS"): Decimal("1.000000"),
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


def _verify_project_access(db: Session, project_id: str, user: User) -> None:
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found")

    if user.role == "admin":
        return

    membership = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not authorized for this project.",
        )


def _ensure_role(user: User, allowed_roles: List[str]) -> None:
    role = (user.role or "").lower()
    if role == "site_supervisor":
        role = "supervisor"
    normalized_allowed = [r.lower() for r in allowed_roles]
    if "supervisor" in normalized_allowed and "site_supervisor" not in normalized_allowed:
        normalized_allowed.append("site_supervisor")

    if role not in normalized_allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation not permitted for role '{user.role}'. Allowed roles: {allowed_roles}",
        )


def generate_canonical_hash(payload: Dict[str, Any]) -> str:
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def create_resource_performance_snapshot(
    db: Session,
    project_id: str,
    data: ResourcePerformanceCreateRequest,
    current_user: User,
) -> ResourcePerformanceSnapshot:
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor"])
    _verify_project_access(db, project_id, current_user)

    # Validate activity
    activity = (
        db.query(ConstructionActivity)
        .filter(ConstructionActivity.id == data.activity_id, ConstructionActivity.project_id == project_id)
        .first()
    )
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity {data.activity_id} not found in project {project_id}",
        )

    # Validate category and resource / material linkage
    category = data.resource_category.strip().upper()
    resource_obj: Optional[Resource] = None
    if data.resource_id:
        resource_obj = db.query(Resource).filter(Resource.id == data.resource_id).first()
        if not resource_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resource {data.resource_id} not found",
            )
        if resource_obj.resource_category.upper() != category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Resource {data.resource_id} category ({resource_obj.resource_category}) does not match snapshot category ({category})",
            )

    material_obj: Optional[MaterialItem] = None
    if data.material_item_id:
        material_obj = (
            db.query(MaterialItem)
            .filter(MaterialItem.id == data.material_item_id, MaterialItem.project_id == project_id)
            .first()
        )
        if not material_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Material item {data.material_item_id} not found in project {project_id}",
            )

    # Upstream source resolution
    source_mps: Optional[MaterialPerformanceSnapshot] = None
    if category == "MATERIAL":
        if data.material_performance_snapshot_id:
            source_mps = (
                db.query(MaterialPerformanceSnapshot)
                .filter(
                    MaterialPerformanceSnapshot.id == data.material_performance_snapshot_id,
                    MaterialPerformanceSnapshot.project_id == project_id,
                )
                .first()
            )
            if not source_mps:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"MaterialPerformanceSnapshot {data.material_performance_snapshot_id} not found in project",
                )
            if source_mps.activity_id != data.activity_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="MaterialPerformanceSnapshot activity does not match target activity",
                )
            if source_mps.status != "FINALIZED":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"MaterialPerformanceSnapshot must be FINALIZED to be used as authoritative source, got '{source_mps.status}'",
                )
        else:
            # Look for authoritative finalized snapshot for this activity & material
            q_mps = db.query(MaterialPerformanceSnapshot).filter(
                MaterialPerformanceSnapshot.project_id == project_id,
                MaterialPerformanceSnapshot.activity_id == data.activity_id,
                MaterialPerformanceSnapshot.status == "FINALIZED",
            )
            if data.material_item_id:
                q_mps = q_mps.filter(MaterialPerformanceSnapshot.material_item_id == data.material_item_id)
            source_mps = q_mps.order_by(MaterialPerformanceSnapshot.finalized_at.desc()).first()

    source_rp: Optional[ResourcePlan] = None
    if data.resource_plan_id:
        source_rp = (
            db.query(ResourcePlan)
            .filter(ResourcePlan.id == data.resource_plan_id, ResourcePlan.project_id == project_id)
            .first()
        )
        if not source_rp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ResourcePlan {data.resource_plan_id} not found in project",
            )
    elif activity.engineering_element_id and data.resource_id:
        # Match resource plan by element and resource
        source_rp = (
            db.query(ResourcePlan)
            .filter(
                ResourcePlan.project_id == project_id,
                ResourcePlan.engineering_element_id == activity.engineering_element_id,
                ResourcePlan.resource_id == data.resource_id,
                ResourcePlan.status == "PLANNED",
            )
            .first()
        )

    # Determine Planned Quantity & Unit
    planned_qty: Optional[Decimal] = None
    planned_unit: Optional[str] = None
    if data.planned_quantity is not None:
        planned_qty = data.planned_quantity
        planned_unit = data.planned_unit or (resource_obj.unit if resource_obj else None)
    elif source_mps and source_mps.planned_quantity is not None:
        planned_qty = source_mps.planned_quantity
        planned_unit = source_mps.planned_unit
    elif source_rp and source_rp.resource_demand is not None:
        planned_qty = source_rp.resource_demand
        planned_unit = source_rp.resource_demand_unit

    # Determine Actual Resource Quantity & Unit
    actual_qty: Optional[Decimal] = None
    actual_unit: Optional[str] = None
    if data.verified_actual_resource_quantity is not None:
        actual_qty = data.verified_actual_resource_quantity
        actual_unit = data.verified_actual_resource_unit or planned_unit or (resource_obj.unit if resource_obj else None)
    elif source_mps and source_mps.actual_consumption_quantity is not None:
        actual_qty = source_mps.actual_consumption_quantity
        actual_unit = source_mps.actual_consumption_unit

    # Determine Verified Output Quantity & Unit
    verified_output_qty: Optional[Decimal] = None
    verified_output_unit: Optional[str] = None
    output_source_info: Optional[Dict[str, Any]] = None
    if data.verified_output_quantity is not None:
        verified_output_qty = data.verified_output_quantity
        verified_output_unit = data.verified_output_unit
        output_source_info = {
            "source_type": "DIRECT_SUPERVISOR_ENTRY",
            "verification_state": "SUPERVISOR_ENTERED",
            "entered_by": current_user.id,
            "unit": verified_output_unit,
            "period_start": str(data.performance_period_start) if data.performance_period_start else None,
            "period_end": str(data.performance_period_end) if data.performance_period_end else None,
        }
    elif source_mps and source_mps.verified_activity_execution_quantity is not None:
        verified_output_qty = source_mps.verified_activity_execution_quantity
        verified_output_unit = source_mps.verified_activity_execution_unit
        output_source_info = {
            "source_type": "MATERIAL_PERFORMANCE_SNAPSHOT",
            "source_id": source_mps.id,
            "canonical_hash": source_mps.canonical_hash,
            "verification_state": "FINALIZED_MPS",
            "unit": verified_output_unit,
            "period_start": str(source_mps.performance_period_start) if source_mps.performance_period_start else None,
            "period_end": str(source_mps.performance_period_end) if source_mps.performance_period_end else None,
        }
    else:
        # Try finding verified output from DailyActivityProgressVerification
        q_verifs = (
            db.query(DailyActivityProgressVerification)
            .join(DailyActivityProgress, DailyActivityProgressVerification.daily_activity_progress_id == DailyActivityProgress.id)
            .join(DailyProgressReport, DailyActivityProgress.daily_report_id == DailyProgressReport.id)
            .filter(
                DailyActivityProgress.project_id == project_id,
                DailyActivityProgress.activity_id == data.activity_id,
                DailyActivityProgressVerification.verification_status == "VERIFIED",
                DailyActivityProgressVerification.verified_quantity.isnot(None),
            )
        )
        if data.performance_period_start:
            q_verifs = q_verifs.filter(DailyProgressReport.report_date >= data.performance_period_start)
        if data.performance_period_end:
            q_verifs = q_verifs.filter(DailyProgressReport.report_date <= data.performance_period_end)

        verifs = q_verifs.order_by(DailyActivityProgressVerification.verified_at.asc()).all()
        if verifs:
            first_unit = verifs[0].verified_quantity_unit
            sum_output = Decimal("0.0000")
            all_compat = True
            for v in verifs:
                conv_v, _, ok_v = convert_unit(v.verified_quantity, v.verified_quantity_unit, first_unit)
                if ok_v:
                    sum_output += conv_v
                else:
                    all_compat = False
                    break
            if all_compat:
                verified_output_qty = sum_output
                verified_output_unit = first_unit
                output_source_info = {
                    "source_type": "DAILY_ACTIVITY_PROGRESS_VERIFICATION",
                    "verification_state": "VERIFIED",
                    "verification_ids": [v.id for v in verifs],
                    "count": len(verifs),
                    "unit": first_unit,
                    "period_start": str(data.performance_period_start) if data.performance_period_start else None,
                    "period_end": str(data.performance_period_end) if data.performance_period_end else None,
                }
        else:
            # Try finding certified output from PeriodCertificateItem linked to authoritative CERTIFIED certificates
            q_certs = (
                db.query(PeriodCertificateItem, PeriodProgressCertificate)
                .join(PeriodProgressCertificate, PeriodCertificateItem.certificate_id == PeriodProgressCertificate.id)
                .join(ConstructionActivity, PeriodCertificateItem.activity_id == ConstructionActivity.id)
                .filter(
                    ConstructionActivity.project_id == project_id,
                    PeriodCertificateItem.activity_id == data.activity_id,
                    PeriodCertificateItem.certified_quantity.isnot(None),
                    PeriodProgressCertificate.certificate_status == "CERTIFIED",
                )
            )
            if data.performance_period_start:
                q_certs = q_certs.filter(PeriodProgressCertificate.period_cut_off_date >= data.performance_period_start)
            if data.performance_period_end:
                q_certs = q_certs.filter(PeriodProgressCertificate.period_start_date <= data.performance_period_end)

            cert_results = q_certs.order_by(PeriodCertificateItem.id.asc()).all()
            if cert_results:
                cert_items = [r[0] for r in cert_results]
                certs_map = {r[1].id: r[1] for r in cert_results}
                c_unit = cert_items[0].quantity_unit
                c_sum = Decimal("0.0000")
                all_c_compat = True
                for ci in cert_items:
                    conv_ci, _, ok_ci = convert_unit(ci.certified_quantity, ci.quantity_unit, c_unit)
                    if ok_ci:
                        c_sum += conv_ci
                    else:
                        all_c_compat = False
                        break
                if all_c_compat:
                    verified_output_qty = c_sum
                    verified_output_unit = c_unit
                    output_source_info = {
                        "source_type": "PERIOD_CERTIFICATE_ITEM",
                        "verification_state": "CERTIFIED",
                        "certificate_ids": list(certs_map.keys()),
                        "certificate_numbers": [c.certificate_number for c in certs_map.values()],
                        "item_ids": [ci.id for ci in cert_items],
                        "count": len(cert_items),
                        "unit": c_unit,
                        "period_start": str(data.performance_period_start) if data.performance_period_start else None,
                        "period_end": str(data.performance_period_end) if data.performance_period_end else None,
                    }

    unit_mismatch = False
    currency_mismatch = False
    rate_unavailable = False

    # Resource Variance
    resource_variance: Optional[Decimal] = None
    resource_variance_pct: Optional[Decimal] = None
    if planned_qty is not None and actual_qty is not None and planned_unit and actual_unit:
        conv_actual, _, ok_conv = convert_unit(actual_qty, actual_unit, planned_unit)
        if ok_conv:
            resource_variance = conv_actual - planned_qty
            if planned_qty > Decimal("0.0"):
                resource_variance_pct = (resource_variance / planned_qty) * Decimal("100.0")
            else:
                resource_variance_pct = None
        else:
            unit_mismatch = True
            resource_variance = None
            resource_variance_pct = None

    # Productivity
    productivity: Optional[Decimal] = None
    productivity_unit: Optional[str] = None
    if verified_output_qty is not None and actual_qty is not None and verified_output_unit and actual_unit:
        if actual_qty > Decimal("0.0"):
            productivity = verified_output_qty / actual_qty
            productivity_unit = f"{verified_output_unit}/{actual_unit}"

    # Resource Intensity
    resource_intensity: Optional[Decimal] = None
    resource_intensity_unit: Optional[str] = None
    if actual_qty is not None and verified_output_qty is not None and actual_unit and verified_output_unit:
        if verified_output_qty > Decimal("0.0"):
            resource_intensity = actual_qty / verified_output_qty
            resource_intensity_unit = f"{actual_unit}/{verified_output_unit}"

    # Cost Rate Resolution
    applied_rate_obj: Optional[CostRate] = None
    applied_arm_obj: Optional[ActivityRateMapping] = None
    if data.cost_rate_id:
        applied_rate_obj = db.query(CostRate).filter(CostRate.id == data.cost_rate_id).first()
        if not applied_rate_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"CostRate {data.cost_rate_id} not found")
        if applied_rate_obj.project_id is not None and applied_rate_obj.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CostRate belongs to another project")
        if applied_rate_obj.status != "CONFIRMED":
            rate_unavailable = True
    elif data.rate_mapping_id:
        applied_arm_obj = (
            db.query(ActivityRateMapping)
            .filter(ActivityRateMapping.id == data.rate_mapping_id, ActivityRateMapping.project_id == project_id)
            .first()
        )
        if not applied_arm_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ActivityRateMapping {data.rate_mapping_id} not found")
        if applied_arm_obj.activity_id != data.activity_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ActivityRateMapping activity mismatch")
        if applied_arm_obj.status != "ACTIVE":
            rate_unavailable = True
        else:
            applied_rate_obj = applied_arm_obj.cost_rate
    else:
        # Default lookup active ActivityRateMapping for activity
        arm = (
            db.query(ActivityRateMapping)
            .filter(
                ActivityRateMapping.project_id == project_id,
                ActivityRateMapping.activity_id == data.activity_id,
                ActivityRateMapping.status == "ACTIVE",
            )
            .first()
        )
        if arm and arm.cost_rate and arm.cost_rate.status == "CONFIRMED":
            applied_arm_obj = arm
            applied_rate_obj = arm.cost_rate

    # Cost Calculations
    cost_rate_id_val: Optional[str] = None
    rate_mapping_id_val: Optional[str] = None
    cost_rate_version_val: Optional[str] = None
    applied_rate_val: Optional[Decimal] = None
    applied_rate_unit_val: Optional[str] = None
    currency_val: Optional[str] = None
    planned_cost: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    cost_variance: Optional[Decimal] = None
    cost_intensity: Optional[Decimal] = None
    cost_intensity_unit: Optional[str] = None

    if applied_rate_obj and applied_rate_obj.status == "CONFIRMED":
        cost_rate_id_val = applied_rate_obj.id
        rate_mapping_id_val = applied_arm_obj.id if applied_arm_obj else None
        cost_rate_version_val = applied_arm_obj.rate_version if applied_arm_obj else applied_rate_obj.version
        applied_rate_val = applied_arm_obj.rate_value if applied_arm_obj else applied_rate_obj.rate_value
        applied_rate_unit_val = applied_arm_obj.rate_unit if applied_arm_obj else applied_rate_obj.unit
        currency_val = applied_arm_obj.currency if applied_arm_obj else applied_rate_obj.currency

        # Compute planned cost
        if planned_qty is not None and planned_unit and applied_rate_unit_val:
            p_conv, _, ok_p = convert_unit(planned_qty, planned_unit, applied_rate_unit_val)
            if ok_p:
                planned_cost = p_conv * applied_rate_val
            else:
                unit_mismatch = True

        # Compute actual cost
        if actual_qty is not None and actual_unit and applied_rate_unit_val:
            a_conv, _, ok_a = convert_unit(actual_qty, actual_unit, applied_rate_unit_val)
            if ok_a:
                actual_cost = a_conv * applied_rate_val
            else:
                unit_mismatch = True

        # Compute cost variance
        if planned_cost is not None and actual_cost is not None:
            cost_variance = actual_cost - planned_cost

        # Compute cost intensity
        if actual_cost is not None and verified_output_qty is not None and verified_output_unit and currency_val:
            if verified_output_qty > Decimal("0.0"):
                cost_intensity = actual_cost / verified_output_qty
                cost_intensity_unit = f"{currency_val}/{verified_output_unit}"

    # Performance Status Determination
    perf_status = "REQUIRES_INPUT"
    if unit_mismatch:
        perf_status = "UNIT_MISMATCH"
    elif currency_mismatch:
        perf_status = "CURRENCY_MISMATCH"
    elif rate_unavailable:
        perf_status = "RATE_UNAVAILABLE"
    elif planned_qty is None or actual_qty is None:
        perf_status = "REQUIRES_INPUT"
    elif verified_output_qty is None and productivity is None:
        perf_status = "NO_VERIFIED_OUTPUT"
    else:
        tol = data.tolerance_percentage if data.tolerance_percentage is not None else Decimal("0.0")
        diff = resource_variance if resource_variance is not None else Decimal("0.0")
        has_explicit_cost = (data.cost_rate_id is not None or data.rate_mapping_id is not None)

        if diff == Decimal("0.0"):
            perf_status = "MATCH"
        elif resource_variance_pct is not None and abs(resource_variance_pct) <= tol:
            perf_status = "WITHIN_PERMISSIBLE_VARIANCE"
        elif has_explicit_cost and cost_variance is not None and cost_variance > Decimal("0.0"):
            perf_status = "COST_OVER_RUN"
        elif has_explicit_cost and cost_variance is not None and cost_variance < Decimal("0.0"):
            perf_status = "COST_UNDER_RUN"
        elif diff > Decimal("0.0"):
            perf_status = "OVER_RESOURCE_CONSUMPTION"
        else: # diff < Decimal("0.0")
            perf_status = "UNDER_RESOURCE_CONSUMPTION"

    input_snapshot = {
        "activity_id": data.activity_id,
        "resource_category": category,
        "resource_id": data.resource_id,
        "material_item_id": data.material_item_id,
        "resource_plan_id": data.resource_plan_id,
        "material_performance_snapshot_id": data.material_performance_snapshot_id,
        "cost_rate_id": data.cost_rate_id,
        "rate_mapping_id": data.rate_mapping_id,
        "performance_period_start": str(data.performance_period_start) if data.performance_period_start else None,
        "performance_period_end": str(data.performance_period_end) if data.performance_period_end else None,
        "requested_planned_quantity": str(data.planned_quantity) if data.planned_quantity is not None else None,
        "requested_planned_unit": data.planned_unit,
        "requested_actual_resource_quantity": str(data.verified_actual_resource_quantity) if data.verified_actual_resource_quantity is not None else None,
        "requested_actual_resource_unit": data.verified_actual_resource_unit,
        "requested_verified_output_quantity": str(data.verified_output_quantity) if data.verified_output_quantity is not None else None,
        "requested_verified_output_unit": data.verified_output_unit,
        "tolerance_percentage": str(data.tolerance_percentage) if data.tolerance_percentage is not None else None,
    }

    provenance: Dict[str, Any] = {
        "resolved_at": datetime.now(timezone.utc).isoformat(),
        "resolved_by": current_user.id,
        "sources": {},
    }
    if source_mps:
        provenance["sources"]["material_performance_snapshot"] = {
            "id": source_mps.id,
            "canonical_hash": source_mps.canonical_hash,
            "status": source_mps.status,
            "planned_quantity": str(source_mps.planned_quantity) if source_mps.planned_quantity is not None else None,
            "actual_consumption_quantity": str(source_mps.actual_consumption_quantity) if source_mps.actual_consumption_quantity is not None else None,
        }
    if source_rp:
        provenance["sources"]["resource_plan"] = {
            "id": source_rp.id,
            "resource_demand": str(source_rp.resource_demand),
            "resource_demand_unit": source_rp.resource_demand_unit,
        }
    if applied_rate_obj:
        provenance["sources"]["cost_rate"] = {
            "id": applied_rate_obj.id,
            "rate_code": applied_rate_obj.rate_code,
            "version": applied_rate_obj.version,
            "rate_value": str(applied_rate_obj.rate_value),
            "unit": applied_rate_obj.unit,
            "currency": applied_rate_obj.currency,
        }
    if applied_arm_obj:
        provenance["sources"]["activity_rate_mapping"] = {
            "id": applied_arm_obj.id,
            "rate_version": applied_arm_obj.rate_version,
            "rate_value": str(applied_arm_obj.rate_value),
            "rate_unit": applied_arm_obj.rate_unit,
        }

    # Record planned resource origin
    if data.planned_quantity is not None:
        provenance["sources"]["planned_resource"] = {
            "source_type": "DIRECT_SUPERVISOR_ENTRY",
            "quantity": str(planned_qty) if planned_qty is not None else None,
            "unit": planned_unit,
            "entered_by": current_user.id,
        }
    elif source_mps and source_mps.planned_quantity is not None:
        provenance["sources"]["planned_resource"] = {
            "source_type": "MATERIAL_PERFORMANCE_SNAPSHOT",
            "source_id": source_mps.id,
            "quantity": str(planned_qty) if planned_qty is not None else None,
            "unit": planned_unit,
        }
    elif source_rp and source_rp.resource_demand is not None:
        provenance["sources"]["planned_resource"] = {
            "source_type": "RESOURCE_PLAN",
            "source_id": source_rp.id,
            "quantity": str(planned_qty) if planned_qty is not None else None,
            "unit": planned_unit,
        }

    # Record actual resource origin
    if data.verified_actual_resource_quantity is not None:
        provenance["sources"]["actual_resource"] = {
            "source_type": "DIRECT_SUPERVISOR_ENTRY",
            "verification_state": "SUPERVISOR_MEASURED",
            "quantity": str(actual_qty) if actual_qty is not None else None,
            "unit": actual_unit,
            "entered_by": current_user.id,
        }
    elif source_mps and source_mps.actual_consumption_quantity is not None:
        provenance["sources"]["actual_resource"] = {
            "source_type": "MATERIAL_PERFORMANCE_SNAPSHOT",
            "source_id": source_mps.id,
            "verification_state": "FINALIZED_MPS",
            "quantity": str(actual_qty) if actual_qty is not None else None,
            "unit": actual_unit,
        }

    if output_source_info:
        provenance["sources"]["verified_output"] = output_source_info

    hash_payload = {
        "project_id": project_id,
        "activity_id": data.activity_id,
        "resource_category": category,
        "resource_id": data.resource_id,
        "material_item_id": data.material_item_id,
        "performance_period_start": str(data.performance_period_start) if data.performance_period_start else None,
        "performance_period_end": str(data.performance_period_end) if data.performance_period_end else None,
        "planned_quantity": str(planned_qty) if planned_qty is not None else None,
        "planned_unit": planned_unit,
        "actual_resource_quantity": str(actual_qty) if actual_qty is not None else None,
        "actual_resource_unit": actual_unit,
        "verified_output_quantity": str(verified_output_qty) if verified_output_qty is not None else None,
        "verified_output_unit": verified_output_unit,
        "currency": currency_val,
        "cost_rate_id": cost_rate_id_val,
        "cost_rate_version": cost_rate_version_val,
        "applied_cost_rate_value": str(applied_rate_val) if applied_rate_val is not None else None,
        "applied_cost_rate_unit": applied_rate_unit_val,
        "planned_cost": str(planned_cost) if planned_cost is not None else None,
        "actual_cost": str(actual_cost) if actual_cost is not None else None,
        "resource_variance": str(resource_variance) if resource_variance is not None else None,
        "resource_variance_percentage": str(resource_variance_pct) if resource_variance_pct is not None else None,
        "cost_variance": str(cost_variance) if cost_variance is not None else None,
        "productivity": str(productivity) if productivity is not None else None,
        "productivity_unit": productivity_unit,
        "resource_intensity": str(resource_intensity) if resource_intensity is not None else None,
        "resource_intensity_unit": resource_intensity_unit,
        "cost_intensity": str(cost_intensity) if cost_intensity is not None else None,
        "cost_intensity_unit": cost_intensity_unit,
        "performance_status": perf_status,
        "algorithm_version": "RES_PERFORMANCE_1.0",
    }
    canonical_hash = generate_canonical_hash(hash_payload)

    snapshot = ResourcePerformanceSnapshot(
        project_id=project_id,
        activity_id=data.activity_id,
        resource_id=data.resource_id,
        material_item_id=data.material_item_id,
        resource_category=category,
        performance_period_start=data.performance_period_start,
        performance_period_end=data.performance_period_end,
        resource_plan_id=source_rp.id if source_rp else data.resource_plan_id,
        material_performance_snapshot_id=source_mps.id if source_mps else data.material_performance_snapshot_id,
        cost_rate_id=cost_rate_id_val,
        rate_mapping_id=rate_mapping_id_val,
        cost_rate_version=cost_rate_version_val,
        applied_cost_rate_value=applied_rate_val,
        applied_cost_rate_unit=applied_rate_unit_val,
        planned_quantity=planned_qty,
        planned_unit=planned_unit,
        actual_resource_quantity=actual_qty,
        actual_resource_unit=actual_unit,
        verified_output_quantity=verified_output_qty,
        verified_output_unit=verified_output_unit,
        currency=currency_val,
        planned_cost=planned_cost,
        actual_cost=actual_cost,
        resource_variance=resource_variance,
        resource_variance_percentage=resource_variance_pct,
        cost_variance=cost_variance,
        productivity=productivity,
        productivity_unit=productivity_unit,
        resource_intensity=resource_intensity,
        resource_intensity_unit=resource_intensity_unit,
        cost_intensity=cost_intensity,
        cost_intensity_unit=cost_intensity_unit,
        tolerance_percentage=data.tolerance_percentage,
        performance_status=perf_status,
        algorithm_version="RES_PERFORMANCE_1.0",
        input_snapshot_json=input_snapshot,
        provenance_metadata=provenance,
        canonical_hash=canonical_hash,
        status="DRAFT",
        created_by=current_user.id,
    )

    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_resource_performance_snapshot(
    db: Session,
    project_id: str,
    performance_id: str,
    current_user: User,
) -> ResourcePerformanceSnapshot:
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    _verify_project_access(db, project_id, current_user)

    snapshot = (
        db.query(ResourcePerformanceSnapshot)
        .filter(ResourcePerformanceSnapshot.id == performance_id, ResourcePerformanceSnapshot.project_id == project_id)
        .first()
    )
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ResourcePerformanceSnapshot {performance_id} not found in project {project_id}",
        )
    return snapshot


def list_resource_performance_snapshots(
    db: Session,
    project_id: str,
    current_user: User,
    activity_id: Optional[str] = None,
    resource_category: Optional[str] = None,
    resource_id: Optional[str] = None,
    material_item_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    performance_status: Optional[str] = None,
) -> List[ResourcePerformanceSnapshot]:
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    _verify_project_access(db, project_id, current_user)

    q = db.query(ResourcePerformanceSnapshot).filter(ResourcePerformanceSnapshot.project_id == project_id)
    if activity_id:
        q = q.filter(ResourcePerformanceSnapshot.activity_id == activity_id)
    if resource_category:
        q = q.filter(ResourcePerformanceSnapshot.resource_category == resource_category.strip().upper())
    if resource_id:
        q = q.filter(ResourcePerformanceSnapshot.resource_id == resource_id)
    if material_item_id:
        q = q.filter(ResourcePerformanceSnapshot.material_item_id == material_item_id)
    if status_filter:
        q = q.filter(ResourcePerformanceSnapshot.status == status_filter.strip().upper())
    if performance_status:
        q = q.filter(ResourcePerformanceSnapshot.performance_status == performance_status.strip().upper())

    return q.order_by(ResourcePerformanceSnapshot.created_at.desc()).all()


def finalize_resource_performance_snapshot(
    db: Session,
    project_id: str,
    performance_id: str,
    current_user: User,
) -> ResourcePerformanceSnapshot:
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor"])
    _verify_project_access(db, project_id, current_user)

    # Advisory lock to serialize finalizations
    lock_key = int(hashlib.sha256(f"{project_id}_{performance_id}".encode()).hexdigest()[:8], 16)
    db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock_key})

    snapshot = (
        db.query(ResourcePerformanceSnapshot)
        .filter(ResourcePerformanceSnapshot.id == performance_id, ResourcePerformanceSnapshot.project_id == project_id)
        .first()
    )
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ResourcePerformanceSnapshot {performance_id} not found in project {project_id}",
        )

    if snapshot.status == "FINALIZED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ResourcePerformanceSnapshot is already FINALIZED.",
        )
    if snapshot.status == "SUPERSEDED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot finalize a SUPERSEDED snapshot.",
        )

    # Check duplicate authoritative identity
    p_start = snapshot.performance_period_start or date(1970, 1, 1)
    p_end = snapshot.performance_period_end or date(1970, 1, 1)
    res_id = snapshot.resource_id or "00000000-0000-0000-0000-000000000000"
    mat_id = snapshot.material_item_id or "00000000-0000-0000-0000-000000000000"

    existing_authoritative = (
        db.query(ResourcePerformanceSnapshot)
        .filter(
            ResourcePerformanceSnapshot.project_id == project_id,
            ResourcePerformanceSnapshot.activity_id == snapshot.activity_id,
            ResourcePerformanceSnapshot.resource_category == snapshot.resource_category,
            ResourcePerformanceSnapshot.status == "FINALIZED",
            text("COALESCE(resource_id, '00000000-0000-0000-0000-000000000000') = :res_id"),
            text("COALESCE(material_item_id, '00000000-0000-0000-0000-000000000000') = :mat_id"),
            text("COALESCE(performance_period_start, '1970-01-01'::date) = :p_start"),
            text("COALESCE(performance_period_end, '1970-01-01'::date) = :p_end"),
        )
        .params(res_id=res_id, mat_id=mat_id, p_start=p_start, p_end=p_end)
        .first()
    )
    if existing_authoritative:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Authoritative finalized snapshot already exists (id={existing_authoritative.id}) for this activity, resource, and period.",
        )

    snapshot.status = "FINALIZED"
    snapshot.finalized_by = current_user.id
    snapshot.finalized_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def supersede_resource_performance_snapshot(
    db: Session,
    project_id: str,
    performance_id: str,
    reason: str,
    current_user: User,
    replacement_snapshot_id: Optional[str] = None,
) -> ResourcePerformanceSnapshot:
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor"])
    _verify_project_access(db, project_id, current_user)

    clean_reason = reason.strip() if reason else ""
    if not clean_reason:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="supersession_reason cannot be empty.",
        )

    snapshot = (
        db.query(ResourcePerformanceSnapshot)
        .filter(ResourcePerformanceSnapshot.id == performance_id, ResourcePerformanceSnapshot.project_id == project_id)
        .first()
    )
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ResourcePerformanceSnapshot {performance_id} not found in project {project_id}",
        )

    if snapshot.status != "FINALIZED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only FINALIZED snapshots can be superseded. Current status: '{snapshot.status}'",
        )

    if replacement_snapshot_id:
        if replacement_snapshot_id == performance_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A snapshot cannot supersede itself.",
            )
        replacement = (
            db.query(ResourcePerformanceSnapshot)
            .filter(
                ResourcePerformanceSnapshot.id == replacement_snapshot_id,
                ResourcePerformanceSnapshot.project_id == project_id,
            )
            .first()
        )
        if not replacement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Replacement snapshot {replacement_snapshot_id} not found in project {project_id}",
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
        if replacement.resource_category != snapshot.resource_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Replacement snapshot resource_category ({replacement.resource_category}) does not match superseded snapshot resource_category ({snapshot.resource_category}).",
            )
        if replacement.resource_id != snapshot.resource_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Replacement snapshot resource_id ({replacement.resource_id}) does not match superseded snapshot resource_id ({snapshot.resource_id}).",
            )
        if replacement.material_item_id != snapshot.material_item_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Replacement snapshot material_item_id ({replacement.material_item_id}) does not match superseded snapshot material_item_id ({snapshot.material_item_id}).",
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

    snapshot.status = "SUPERSEDED"
    snapshot.superseded_by_user_id = current_user.id
    snapshot.superseded_at = datetime.now(timezone.utc)
    snapshot.supersession_reason = clean_reason
    snapshot.superseded_by = replacement_snapshot_id

    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_resource_performance_summary(
    db: Session,
    project_id: str,
    current_user: User,
    activity_id: Optional[str] = None,
    resource_category: Optional[str] = None,
    resource_id: Optional[str] = None,
) -> ResourcePerformanceSummaryResponse:
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    _verify_project_access(db, project_id, current_user)

    q = db.query(ResourcePerformanceSnapshot).filter(
        ResourcePerformanceSnapshot.project_id == project_id,
        ResourcePerformanceSnapshot.status.in_(["DRAFT", "FINALIZED"]),
    )
    if activity_id:
        q = q.filter(ResourcePerformanceSnapshot.activity_id == activity_id)
    if resource_category:
        q = q.filter(ResourcePerformanceSnapshot.resource_category == resource_category.strip().upper())
    if resource_id:
        q = q.filter(ResourcePerformanceSnapshot.resource_id == resource_id)

    snapshots = q.order_by(ResourcePerformanceSnapshot.created_at.desc()).all()

    total_planned_qty: Dict[str, Decimal] = {}
    total_actual_qty: Dict[str, Decimal] = {}
    total_res_var: Dict[str, Decimal] = {}
    total_var_pct: Dict[str, Decimal] = {}
    total_planned_cost: Dict[str, Decimal] = {}
    total_actual_cost: Dict[str, Decimal] = {}
    total_cost_var: Dict[str, Decimal] = {}
    cat_dist: Dict[str, int] = {}
    status_dist: Dict[str, int] = {}

    for s in snapshots:
        cat_dist[s.resource_category] = cat_dist.get(s.resource_category, 0) + 1
        status_dist[s.performance_status] = status_dist.get(s.performance_status, 0) + 1

        if s.planned_quantity is not None and s.planned_unit:
            u = s.planned_unit
            total_planned_qty[u] = total_planned_qty.get(u, Decimal("0.0000")) + s.planned_quantity

        if s.actual_resource_quantity is not None and s.actual_resource_unit:
            u = s.actual_resource_unit
            total_actual_qty[u] = total_actual_qty.get(u, Decimal("0.0000")) + s.actual_resource_quantity

        if s.planned_cost is not None and s.currency:
            c = s.currency
            total_planned_cost[c] = total_planned_cost.get(c, Decimal("0.0000")) + s.planned_cost

        if s.actual_cost is not None and s.currency:
            c = s.currency
            total_actual_cost[c] = total_actual_cost.get(c, Decimal("0.0000")) + s.actual_cost

    # Variance for quantities with compatible units present in both operands
    for u in total_actual_qty:
        if u in total_planned_qty:
            v = total_actual_qty[u] - total_planned_qty[u]
            total_res_var[u] = v
            if total_planned_qty[u] > Decimal("0.0"):
                total_var_pct[u] = (v / total_planned_qty[u]) * Decimal("100.0")

    # Variance for costs with currencies present in both operands
    for c in total_actual_cost:
        if c in total_planned_cost:
            total_cost_var[c] = total_actual_cost[c] - total_planned_cost[c]

    return ResourcePerformanceSummaryResponse(
        project_id=project_id,
        total_snapshots=len(snapshots),
        total_planned_quantities=total_planned_qty,
        total_actual_quantities=total_actual_qty,
        total_resource_variance=total_res_var,
        total_variance_percentage=total_var_pct,
        total_planned_cost=total_planned_cost,
        total_actual_cost=total_actual_cost,
        total_cost_variance=total_cost_var,
        category_distribution=cat_dist,
        status_distribution=status_dist,
        snapshots=[ResourcePerformanceSnapshotResponse.model_validate(s) for s in snapshots],
    )
