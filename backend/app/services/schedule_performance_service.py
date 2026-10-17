import hashlib
import json
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import (
    ActivityScheduleResult,
    ConstructionActivity,
    ConstructionSchedule,
    ContractVariationOrder,
    DailyActivityProgress,
    DailyActivityProgressVerification,
    DailyProgressReport,
    Document,
    MonitoringBaseline,
    Project,
    ProjectMember,
    SchedulePerformanceSnapshot,
    User,
)
from app.schemas.schedule_performance import (
    SchedulePerformanceCreateRequest,
    SchedulePerformanceSnapshotResponse,
    SchedulePerformanceSummaryResponse,
    VALID_DELAY_STATUSES,
    VALID_PERFORMANCE_STATUSES,
    VALID_SNAPSHOT_STATUSES,
)


ALGORITHM_VERSION = "SCHED_PERFORMANCE_1.0_LINEAR"


def _verify_project_access(db: Session, project_id: str, user: User) -> None:
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found")

    if (user.role or "").lower() == "admin":
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


def calculate_date_duration_days(start_date: Optional[date], finish_date: Optional[date]) -> Optional[int]:
    """
    Standard Construction Scheduling Date Convention:
    Duration in days is inclusive of both the start date and the finish date:
    Duration = (finish_date - start_date).days + 1
    Requires start_date <= finish_date. If either date is missing, returns None.
    """
    if start_date is None or finish_date is None:
        return None
    if start_date > finish_date:
        raise ValueError(f"start_date ({start_date}) cannot be after finish_date ({finish_date})")
    return (finish_date - start_date).days + 1


def calculate_actual_time_days(start_date: Optional[date], eval_or_finish_date: Optional[date]) -> Optional[Decimal]:
    """
    Elapsed Actual Time (AT) in days:
    Measured inclusively from actual start date through evaluation date or actual finish date:
    AT = (eval_or_finish_date - start_date).days + 1
    If either operand is None, returns None.
    """
    if start_date is None or eval_or_finish_date is None:
        return None
    if start_date > eval_or_finish_date:
        # Evaluation prior to actual start -> 0 days elapsed
        return Decimal("0.0000")
    days = (eval_or_finish_date - start_date).days + 1
    return Decimal(str(days)).quantize(Decimal("0.0001"))


def calculate_earned_schedule_days(
    planned_duration_days: Optional[int],
    actual_cumulative_progress_pct: Optional[Decimal],
) -> Optional[Decimal]:
    """
    Earned Schedule (ES) calculation using Linear CPM Approximation:
    In deterministic schedule performance analytics where CPM baseline does not provide
    a non-linear daily cumulative progress S-curve, Earned Schedule is approximated assuming
    linear planned rate of progress across the planned duration.
    Formula: ES = Planned Duration * (Actual Cumulative Progress % / 100)
    Label: LINEAR_CPM_APPROXIMATION
    If planned duration is None or progress percentage is None, returns None (never silently zero).
    """
    if planned_duration_days is None or actual_cumulative_progress_pct is None:
        return None
    pd_dec = Decimal(str(planned_duration_days))
    pct_fraction = actual_cumulative_progress_pct / Decimal("100.0000")
    es = pd_dec * pct_fraction
    return es.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def calculate_schedule_variance_days(
    earned_schedule: Optional[Decimal],
    actual_time: Optional[Decimal],
) -> Optional[Decimal]:
    """
    Schedule Variance in Time (SV_t):
    Formula: SV_t = ES - AT
    Positive => Ahead of schedule in days.
    Negative => Behind schedule (delay) in days.
    If either operand is missing, returns None.
    """
    if earned_schedule is None or actual_time is None:
        return None
    sv = earned_schedule - actual_time
    return sv.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def calculate_schedule_performance_index(
    earned_schedule: Optional[Decimal],
    actual_time: Optional[Decimal],
) -> Optional[Decimal]:
    """
    Schedule Performance Index in Time (SPI_t):
    Formula: SPI_t = ES / AT
    Edge cases:
    - If AT == 0 and ES == 0: activity hasn't started elapsed time yet, returns None (indeterminate/unstarted).
    - If AT == 0 and ES > 0: zero denominator guard, returns None.
    - If either operand is missing, returns None.
    """
    if earned_schedule is None or actual_time is None:
        return None
    if actual_time <= Decimal("0.0000"):
        return None
    spi = earned_schedule / actual_time
    return spi.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def calculate_residual_float_days(
    baseline_total_float_days: Optional[int],
    schedule_variance_days: Optional[Decimal],
) -> Optional[int]:
    """
    Residual Total Float calculation:
    Residual Float represents the remaining schedule buffer after absorbing schedule delay slip:
    Float consumed = max(0, -SV_t) (delay consumes float).
    Residual Float = Baseline Float - Float consumed
    Contract: Residual Float is stored as integer calendar days.
    Calculation uses pure Decimal arithmetic with ROUND_CEILING:
    slip_days = int((-schedule_variance_days).to_integral_value(rounding=ROUND_CEILING))
    If SV_t >= 0, float is preserved: Residual Float = Baseline Float.
    If baseline float is None or schedule variance is None, returns None.
    """
    if baseline_total_float_days is None or schedule_variance_days is None:
        return None
    if schedule_variance_days < Decimal("0.0000"):
        # Pure Decimal ceiling without floating-point conversion
        slip_days = int((-schedule_variance_days).to_integral_value(rounding=ROUND_CEILING))
        return baseline_total_float_days - slip_days
    return baseline_total_float_days


def determine_delay_and_performance_status(
    planned_start_date: Optional[date],
    actual_start_date: Optional[date],
    evaluation_date: date,
    schedule_variance_days: Optional[Decimal],
    residual_total_float_days: Optional[int],
    is_critical_path: bool,
) -> Tuple[str, str, Optional[int]]:
    """
    Deterministically determines:
    1. delay_status: ON_SCHEDULE, AHEAD_OF_SCHEDULE, MINOR_DELAY, CRITICAL_DELAY, FLOAT_ABSORBED, SCHEDULE_BREACH, REQUIRES_INPUT
    2. performance_status: ON_TRACK, SCHEDULE_VARIANCE_WITHIN_TOLERANCE, CRITICAL_DELAY, SCHEDULE_BREACH, REQUIRES_INPUT, DATA_MISMATCH
    3. critical_path_impact_days: integer delay days impacting critical completion

    Threshold boundary rules:
    - SV_t > +0.5000: AHEAD_OF_SCHEDULE
    - -0.5000 <= SV_t <= +0.5000: ON_SCHEDULE (within tolerance band)
    - SV_t < -0.5000: DELAY (consumed float or critical path)
      * If critical path: CRITICAL_DELAY
      * Else if residual float < 0: CRITICAL_DELAY (float exhausted)
      * Else if residual float == 0: FLOAT_ABSORBED
      * Else: MINOR_DELAY
    """
    if schedule_variance_days is None:
        # Missing essential metrics
        if actual_start_date is None and planned_start_date and planned_start_date > evaluation_date:
            d_status = "ON_SCHEDULE"  # Future activity not yet planned to start
        else:
            d_status = "REQUIRES_INPUT"
    elif schedule_variance_days > Decimal("0.5000"):
        d_status = "AHEAD_OF_SCHEDULE"
    elif schedule_variance_days >= Decimal("-0.5000"):
        d_status = "ON_SCHEDULE"
    else:
        # Negative variance strictly < -0.5000 => Delay
        if is_critical_path:
            d_status = "CRITICAL_DELAY"
        elif residual_total_float_days is not None and residual_total_float_days < 0:
            d_status = "CRITICAL_DELAY"  # Float exhausted, transitioned to critical
        elif residual_total_float_days is not None and residual_total_float_days == 0:
            d_status = "FLOAT_ABSORBED"
        else:
            d_status = "MINOR_DELAY"

    # Critical path impact days
    cp_impact: Optional[int] = None
    if is_critical_path and schedule_variance_days is not None and schedule_variance_days < Decimal("0.0000"):
        cp_impact = int((-schedule_variance_days).to_integral_value(rounding=ROUND_CEILING))
    elif residual_total_float_days is not None and residual_total_float_days < 0:
        cp_impact = int(-residual_total_float_days)

    # Derive performance_status
    if d_status == "REQUIRES_INPUT":
        p_status = "REQUIRES_INPUT"
    elif d_status in ("ON_SCHEDULE", "AHEAD_OF_SCHEDULE"):
        p_status = "ON_TRACK"
    elif d_status in ("MINOR_DELAY", "FLOAT_ABSORBED"):
        p_status = "SCHEDULE_VARIANCE_WITHIN_TOLERANCE"
    elif d_status == "CRITICAL_DELAY":
        p_status = "CRITICAL_DELAY"
    elif d_status == "SCHEDULE_BREACH":
        p_status = "SCHEDULE_BREACH"
    else:
        p_status = "ON_TRACK"

    return d_status, p_status, cp_impact


def _canonical_normalize(value: Any) -> Any:
    """
    Recursively normalize data structure for deterministic canonical JSON serialization.
    Strictly accepts only supported types:
    None, bool, int, Decimal, date, datetime, enum, str, list/tuple, and dict (string keys only).
    Rejects unsupported types and non-string dictionary keys with TypeError.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, Decimal):
        # Exact string representation of Decimal without binary float conversion
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, str):
        return value
    if hasattr(value, "value"):  # Enum support
        return str(value.value)
    if isinstance(value, dict):
        normalized_dict = {}
        for k, v in sorted(value.items()):
            if not isinstance(k, str):
                raise TypeError(f"Canonical payload dictionary keys must be strings, got {type(k).__name__}: {k!r}")
            normalized_dict[k] = _canonical_normalize(v)
        return normalized_dict
    if isinstance(value, (list, tuple)):
        return [_canonical_normalize(item) for item in value]

    raise TypeError(f"Unsupported type for canonical JSON serialization: {type(value).__name__} ({value!r})")


def generate_schedule_performance_canonical_hash(payload: Dict[str, Any]) -> str:
    """
    Canonical, deterministic SHA-256 serialization.
    Ensures sorted keys, standard string representation, and strict type normalization (no default=str fallback).
    Note: SHA-256 proves tamper detection relative to a digest, not real-world factual truth.
    """
    normalized = _canonical_normalize(payload)
    canonical_json = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def create_schedule_performance_snapshot(
    db: Session,
    project_id: str,
    data: SchedulePerformanceCreateRequest,
    current_user: User,
) -> SchedulePerformanceSnapshot:
    """
    Create a new draft schedule performance snapshot with auditable provenance and deterministic calculations.
    """
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor"])
    _verify_project_access(db, project_id, current_user)

    # 1. Validate activity belongs to project
    act = (
        db.query(ConstructionActivity)
        .filter(ConstructionActivity.id == data.activity_id, ConstructionActivity.project_id == project_id)
        .first()
    )
    if not act:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ConstructionActivity {data.activity_id} not found in project {project_id}",
        )

    # 2. Resolve schedule and monitoring baseline unambiguously
    schedule_id = data.schedule_id
    monitoring_baseline_id = data.monitoring_baseline_id
    sched = None
    baseline = None

    if monitoring_baseline_id:
        baseline = (
            db.query(MonitoringBaseline)
            .filter(MonitoringBaseline.id == monitoring_baseline_id, MonitoringBaseline.project_id == project_id)
            .first()
        )
        if not baseline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MonitoringBaseline {monitoring_baseline_id} not found in project {project_id}",
            )
        # If schedule_id was also explicitly supplied, it must strictly match baseline schedule_id
        if schedule_id and baseline.schedule_id != schedule_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Monitoring baseline schedule_id ({baseline.schedule_id}) does not match snapshot schedule_id ({schedule_id}).",
            )
        # Derive schedule_id from validated baseline if not explicitly supplied
        if not schedule_id:
            schedule_id = baseline.schedule_id

    if schedule_id:
        sched = (
            db.query(ConstructionSchedule)
            .filter(ConstructionSchedule.id == schedule_id, ConstructionSchedule.project_id == project_id)
            .first()
        )
        if not sched:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ConstructionSchedule {schedule_id} not found in project {project_id}",
            )
    else:
        # Ambiguous input: no schedule_id and no monitoring_baseline_id provided
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"schedule_id or an explicit monitoring_baseline_id must be provided to evaluate schedule performance for project {project_id}.",
        )

    # If baseline was not explicitly provided, check active baseline for project matching the schedule
    if not baseline:
        active_base = (
            db.query(MonitoringBaseline)
            .filter(MonitoringBaseline.project_id == project_id, MonitoringBaseline.status == "ACTIVE")
            .first()
        )
        if active_base and active_base.schedule_id == schedule_id:
            monitoring_baseline_id = active_base.id
            baseline = active_base

    # 3. Resolve activity CPM schedule result (if exists)
    sched_result = (
        db.query(ActivityScheduleResult)
        .filter(ActivityScheduleResult.schedule_id == schedule_id, ActivityScheduleResult.activity_id == data.activity_id)
        .first()
    )

    # Determine baseline planned dates and float
    planned_start = data.planned_start_date
    planned_finish = data.planned_finish_date
    baseline_float = data.baseline_total_float_days
    is_crit = data.is_critical_path or False

    if sched_result:
        if baseline_float is None:
            baseline_float = int(sched_result.total_float)
        is_crit = sched_result.is_critical or is_crit
        # If baseline start date is anchor
        if baseline and baseline.baseline_start_date and (planned_start is None or planned_finish is None):
            anchor = baseline.baseline_start_date
            if planned_start is None:
                # early start is offset in days from anchor
                es_offset = int(sched_result.es)
                from datetime import timedelta
                planned_start = anchor + timedelta(days=es_offset)
            if planned_finish is None:
                ef_offset = int(sched_result.ef)
                from datetime import timedelta
                # Inclusive finish date: ef is day count
                planned_finish = anchor + timedelta(days=ef_offset - 1)

    # 4. Query daily verification progress records with deterministic tie-breaking
    actual_start = data.actual_start_date
    actual_finish = data.actual_finish_date
    actual_pct = None
    progress_provenance = "NO_DATA"
    verified_record_count = 0
    upstream_verification_ids: List[str] = []

    # Look for supervisor verified progress up to evaluation date
    # Deterministic tie-breaking: report_date DESC, verified_at DESC, id DESC
    verifs = (
        db.query(DailyActivityProgressVerification)
        .join(DailyActivityProgress, DailyActivityProgressVerification.daily_activity_progress_id == DailyActivityProgress.id)
        .join(DailyProgressReport, DailyActivityProgress.daily_report_id == DailyProgressReport.id)
        .filter(
            DailyActivityProgressVerification.project_id == project_id,
            DailyActivityProgress.activity_id == data.activity_id,
            DailyActivityProgressVerification.verification_status.in_(["VERIFIED", "CORRECTED"]),
            DailyProgressReport.report_date <= data.evaluation_date,
        )
        .order_by(
            DailyProgressReport.report_date.desc(),
            DailyActivityProgressVerification.verified_at.desc(),
            DailyActivityProgressVerification.id.desc(),
        )
        .all()
    )
    if verifs:
        verified_record_count = len(verifs)
        upstream_verification_ids = [v.id for v in verifs[:5]]  # Capture latest IDs
        latest_v = verifs[0]
        if latest_v.verified_percent_complete is not None:
            actual_pct = Decimal(str(latest_v.verified_percent_complete)).quantize(Decimal("0.0001"))
            progress_provenance = "SUPERVISOR_VERIFIED"
        if actual_start is None:
            # find earliest verified start date
            for v in reversed(verifs):
                if v.verified_actual_start is not None:
                    actual_start = v.verified_actual_start
                    break
        if actual_finish is None and latest_v.verified_status == "COMPLETED":
            actual_finish = latest_v.verified_actual_finish

    # Check if request supplies an explicit actual_cumulative_progress_pct
    if data.actual_cumulative_progress_pct is not None:
        if verifs and actual_pct is not None and data.actual_cumulative_progress_pct != actual_pct:
            # Overriding existing verified progress requires explicit override_reason
            if not data.override_reason or not data.override_reason.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Overriding supervisor-verified actual progress requires an explicit override_reason.",
                )
            actual_pct = data.actual_cumulative_progress_pct
            progress_provenance = "MANUAL_OVERRIDE"
        elif not verifs:
            actual_pct = data.actual_cumulative_progress_pct
            progress_provenance = "DIRECT_ENTRY_UNVERIFIED"
        else:
            # Identical to verified progress
            actual_pct = data.actual_cumulative_progress_pct

    # 5. Validate evidence document and contract variation if provided
    if data.delay_evidence_document_id:
        doc = (
            db.query(Document)
            .filter(Document.id == data.delay_evidence_document_id, Document.project_id == project_id)
            .first()
        )
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {data.delay_evidence_document_id} not found in project {project_id}",
            )

    if data.contract_variation_id:
        cvo = (
            db.query(ContractVariationOrder)
            .filter(ContractVariationOrder.id == data.contract_variation_id, ContractVariationOrder.project_id == project_id)
            .first()
        )
        if not cvo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ContractVariationOrder {data.contract_variation_id} not found in project {project_id}",
            )

    # 6. Perform deterministic engineering calculations
    planned_dur = calculate_date_duration_days(planned_start, planned_finish)
    actual_dur = calculate_date_duration_days(actual_start, actual_finish)

    # Actual elapsed time AT
    at_eval_date = actual_finish if actual_finish else data.evaluation_date
    actual_time = calculate_actual_time_days(actual_start, at_eval_date)

    # Earned Schedule ES (Linear CPM approximation)
    earned_sched = calculate_earned_schedule_days(planned_dur, actual_pct)

    # Schedule Variance SV_t and SPI_t
    sv_days = calculate_schedule_variance_days(earned_sched, actual_time)
    spi_index = calculate_schedule_performance_index(earned_sched, actual_time)

    # Residual float
    residual_float = calculate_residual_float_days(baseline_float, sv_days)

    # Status determination (Strictly computed from metrics; never overridden by human assessment)
    computed_delay_st, perf_st, cp_impact = determine_delay_and_performance_status(
        planned_start_date=planned_start,
        actual_start_date=actual_start,
        evaluation_date=data.evaluation_date,
        schedule_variance_days=sv_days,
        residual_total_float_days=residual_float,
        is_critical_path=is_crit,
    )

    # 7. Provenance & Input Snapshot Metadata
    input_snapshot = {
        "project_id": project_id,
        "activity_id": data.activity_id,
        "schedule_id": schedule_id,
        "monitoring_baseline_id": monitoring_baseline_id,
        "performance_period_start": str(data.performance_period_start) if data.performance_period_start else None,
        "performance_period_end": str(data.performance_period_end) if data.performance_period_end else None,
        "evaluation_date": str(data.evaluation_date),
        "planned_start_date": str(planned_start) if planned_start else None,
        "planned_finish_date": str(planned_finish) if planned_finish else None,
        "actual_start_date": str(actual_start) if actual_start else None,
        "actual_finish_date": str(actual_finish) if actual_finish else None,
        "planned_cumulative_progress_pct": str(data.planned_cumulative_progress_pct) if data.planned_cumulative_progress_pct is not None else None,
        "actual_cumulative_progress_pct": str(actual_pct) if actual_pct is not None else None,
        "baseline_total_float_days": baseline_float,
        "is_critical_path": is_crit,
        "supervisor_assessed_delay_status": data.supervisor_assessed_delay_status,
        "override_reason": data.override_reason,
        "delay_classification": data.delay_classification,
        "delay_root_cause_category": data.delay_root_cause_category,
        "delay_justification": data.delay_justification,
        "delay_evidence_document_id": data.delay_evidence_document_id,
        "contract_variation_id": data.contract_variation_id,
    }

    provenance = {
        "algorithm_version": ALGORITHM_VERSION,
        "planned_progress_curve_type": "LINEAR_CPM_APPROXIMATION",
        "progress_provenance": progress_provenance,
        "override_reason": data.override_reason,
        "upstream_verification_ids": upstream_verification_ids,
        "evaluated_by_user_id": current_user.id,
        "evaluated_by_role": current_user.role,
        "supervisor_assessed_delay_status": data.supervisor_assessed_delay_status,
        "computed_delay_status": computed_delay_st,
        "schedule_source": "CONSTRUCTION_SCHEDULE_CPM" if sched_result else "EXPLICIT_OR_DEFAULT",
        "verified_site_progress_records_found": verified_record_count,
        "attribution_evidence_present": bool(data.delay_evidence_document_id or data.contract_variation_id),
        "tamper_digest_notice": "SHA-256 canonical hash provides cryptographic tamper detection relative to the stored digest, not external factual verification.",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    canonical_payload = {
        "project_id": project_id,
        "activity_id": data.activity_id,
        "schedule_id": schedule_id,
        "monitoring_baseline_id": monitoring_baseline_id,
        "performance_period_start": str(data.performance_period_start) if data.performance_period_start else None,
        "performance_period_end": str(data.performance_period_end) if data.performance_period_end else None,
        "evaluation_date": str(data.evaluation_date),
        "planned_start_date": str(planned_start) if planned_start else None,
        "planned_finish_date": str(planned_finish) if planned_finish else None,
        "planned_duration_days": planned_dur,
        "actual_start_date": str(actual_start) if actual_start else None,
        "actual_finish_date": str(actual_finish) if actual_finish else None,
        "actual_duration_days": actual_dur,
        "planned_cumulative_progress_pct": str(data.planned_cumulative_progress_pct) if data.planned_cumulative_progress_pct is not None else None,
        "actual_cumulative_progress_pct": str(actual_pct) if actual_pct is not None else None,
        "actual_time_days": str(actual_time) if actual_time is not None else None,
        "earned_schedule_days": str(earned_sched) if earned_sched is not None else None,
        "schedule_variance_days": str(sv_days) if sv_days is not None else None,
        "schedule_performance_index": str(spi_index) if spi_index is not None else None,
        "baseline_total_float_days": baseline_float,
        "residual_total_float_days": residual_float,
        "is_critical_path": is_crit,
        "critical_path_impact_days": cp_impact,
        "delay_status": computed_delay_st,
        "supervisor_assessed_delay_status": data.supervisor_assessed_delay_status,
        "performance_status": perf_st,
        "delay_classification": data.delay_classification,
        "delay_root_cause_category": data.delay_root_cause_category,
        "delay_justification": data.delay_justification,
        "delay_evidence_document_id": data.delay_evidence_document_id,
        "contract_variation_id": data.contract_variation_id,
        "progress_provenance": progress_provenance,
        "algorithm_version": ALGORITHM_VERSION,
    }
    canonical_hash = generate_schedule_performance_canonical_hash(canonical_payload)

    # 8. Create snapshot record in DRAFT status
    snapshot = SchedulePerformanceSnapshot(
        project_id=project_id,
        activity_id=data.activity_id,
        schedule_id=schedule_id,
        monitoring_baseline_id=monitoring_baseline_id,
        performance_period_start=data.performance_period_start,
        performance_period_end=data.performance_period_end,
        evaluation_date=data.evaluation_date,
        planned_start_date=planned_start,
        planned_finish_date=planned_finish,
        planned_duration_days=planned_dur,
        actual_start_date=actual_start,
        actual_finish_date=actual_finish,
        actual_duration_days=actual_dur,
        planned_cumulative_progress_pct=data.planned_cumulative_progress_pct,
        actual_cumulative_progress_pct=actual_pct,
        earned_schedule_days=earned_sched,
        actual_time_days=actual_time,
        schedule_variance_days=sv_days,
        schedule_performance_index=spi_index,
        baseline_total_float_days=baseline_float,
        residual_total_float_days=residual_float,
        is_critical_path=is_crit,
        critical_path_impact_days=cp_impact,
        delay_status=computed_delay_st,
        delay_classification=data.delay_classification,
        delay_root_cause_category=data.delay_root_cause_category,
        delay_justification=data.delay_justification,
        delay_evidence_document_id=data.delay_evidence_document_id,
        contract_variation_id=data.contract_variation_id,
        performance_status=perf_st,
        algorithm_version=ALGORITHM_VERSION,
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


def finalize_schedule_performance_snapshot(
    db: Session,
    project_id: str,
    snapshot_id: str,
    current_user: User,
) -> SchedulePerformanceSnapshot:
    """
    Transition a DRAFT schedule performance snapshot to FINALIZED status.
    Uses transaction-scoped advisory locks on the business identity (project_id, activity_id, period)
    to serialize concurrent finalization attempts and prevent duplicate authoritative records.
    """
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor"])
    _verify_project_access(db, project_id, current_user)

    snapshot = (
        db.query(SchedulePerformanceSnapshot)
        .filter(SchedulePerformanceSnapshot.id == snapshot_id, SchedulePerformanceSnapshot.project_id == project_id)
        .first()
    )
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SchedulePerformanceSnapshot {snapshot_id} not found in project {project_id}",
        )

    if snapshot.status == "FINALIZED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SchedulePerformanceSnapshot is already FINALIZED.",
        )
    if snapshot.status == "SUPERSEDED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot finalize a SUPERSEDED snapshot.",
        )

    # Advisory lock on stable business identity: project_id, activity_id, period
    period_start_str = str(snapshot.performance_period_start) if snapshot.performance_period_start else "NONE"
    period_end_str = str(snapshot.performance_period_end) if snapshot.performance_period_end else "NONE"
    business_lock_str = f"sps_finalize_{project_id}_{snapshot.activity_id}_{period_start_str}_{period_end_str}"
    lock_key = int(hashlib.sha256(business_lock_str.encode()).hexdigest()[:8], 16)
    db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock_key})

    # Check for existing authoritative finalized snapshot for this business identity
    if snapshot.performance_period_start is not None and snapshot.performance_period_end is not None:
        existing = (
            db.query(SchedulePerformanceSnapshot)
            .filter(
                SchedulePerformanceSnapshot.project_id == project_id,
                SchedulePerformanceSnapshot.activity_id == snapshot.activity_id,
                SchedulePerformanceSnapshot.performance_period_start == snapshot.performance_period_start,
                SchedulePerformanceSnapshot.performance_period_end == snapshot.performance_period_end,
                SchedulePerformanceSnapshot.status == "FINALIZED",
            )
            .first()
        )
    else:
        existing = (
            db.query(SchedulePerformanceSnapshot)
            .filter(
                SchedulePerformanceSnapshot.project_id == project_id,
                SchedulePerformanceSnapshot.activity_id == snapshot.activity_id,
                SchedulePerformanceSnapshot.performance_period_start.is_(None),
                SchedulePerformanceSnapshot.performance_period_end.is_(None),
                SchedulePerformanceSnapshot.status == "FINALIZED",
            )
            .first()
        )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Authoritative finalized snapshot already exists (id={existing.id}) for this activity and evaluation period.",
        )

    try:
        snapshot.status = "FINALIZED"
        snapshot.finalized_by = current_user.id
        snapshot.finalized_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(snapshot)
        return snapshot
    except IntegrityError as ie:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Finalization conflict: duplicate authoritative snapshot or database constraint violation.",
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected database error occurred during finalization.",
        )


def supersede_schedule_performance_snapshot(
    db: Session,
    project_id: str,
    snapshot_id: str,
    reason: str,
    replacement_snapshot_id: str,
    current_user: User,
) -> SchedulePerformanceSnapshot:
    """
    Supersede an authoritative FINALIZED snapshot with an existing replacement snapshot.
    Validates identity matching, prevents self-referencing, requires replacement to be DRAFT or FINALIZED,
    and preserves immutable audit lineage.
    """
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor"])
    _verify_project_access(db, project_id, current_user)

    clean_reason = reason.strip() if reason else ""
    if not clean_reason:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="supersession_reason cannot be empty.",
        )

    if replacement_snapshot_id == snapshot_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A snapshot cannot supersede itself.",
        )

    # Load target snapshot to supersede
    snapshot = (
        db.query(SchedulePerformanceSnapshot)
        .filter(SchedulePerformanceSnapshot.id == snapshot_id, SchedulePerformanceSnapshot.project_id == project_id)
        .first()
    )
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SchedulePerformanceSnapshot {snapshot_id} not found in project {project_id}",
        )

    if snapshot.status != "FINALIZED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only FINALIZED snapshots can be superseded. Current status: '{snapshot.status}'",
        )

    # Load replacement snapshot
    replacement = (
        db.query(SchedulePerformanceSnapshot)
        .filter(
            SchedulePerformanceSnapshot.id == replacement_snapshot_id,
            SchedulePerformanceSnapshot.project_id == project_id,
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

    # Prevent cycles: replacement cannot be superseded by snapshot
    if replacement.superseded_by == snapshot.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create cyclical supersession relationship.",
        )

    if replacement.activity_id != snapshot.activity_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Replacement snapshot activity ({replacement.activity_id}) does not match superseded snapshot activity ({snapshot.activity_id}).",
        )

    # Validate period equivalence
    if (replacement.performance_period_start != snapshot.performance_period_start or
            replacement.performance_period_end != snapshot.performance_period_end):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Replacement snapshot period ({replacement.performance_period_start} to {replacement.performance_period_end}) does not match superseded snapshot period ({snapshot.performance_period_start} to {snapshot.performance_period_end}).",
        )

    try:
        snapshot.status = "SUPERSEDED"
        snapshot.superseded_by = replacement.id
        snapshot.superseded_by_user_id = current_user.id
        snapshot.superseded_at = datetime.now(timezone.utc)
        snapshot.supersession_reason = clean_reason

        db.commit()
        db.refresh(snapshot)
        return snapshot
    except IntegrityError as ie:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Supersession conflict: database constraint violation or conflict.",
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected database error occurred during supersession.",
        )


def get_schedule_performance_summary(
    db: Session,
    project_id: str,
    evaluation_date: date,
    current_user: User,
) -> SchedulePerformanceSummaryResponse:
    """
    Calculate aggregated schedule health summary across authoritative snapshots in a project.
    """
    _verify_project_access(db, project_id, current_user)

    snapshots = (
        db.query(SchedulePerformanceSnapshot)
        .filter(
            SchedulePerformanceSnapshot.project_id == project_id,
            SchedulePerformanceSnapshot.status.in_(["FINALIZED", "DRAFT"]),
            SchedulePerformanceSnapshot.evaluation_date <= evaluation_date,
        )
        .all()
    )

    total_count = len(snapshots)
    spi_values = [s.schedule_performance_index for s in snapshots if s.schedule_performance_index is not None]
    sv_values = [s.schedule_variance_days for s in snapshots if s.schedule_variance_days is not None]

    mean_spi: Optional[Decimal] = None
    if spi_values:
        mean_spi = (sum(spi_values) / Decimal(str(len(spi_values)))).quantize(Decimal("0.000001"))

    total_sv: Optional[Decimal] = None
    if sv_values:
        total_sv = sum(sv_values).quantize(Decimal("0.0001"))

    delay_dist: Dict[str, int] = {}
    cause_dist: Dict[str, int] = {}
    perf_dist: Dict[str, int] = {}
    cp_delayed_count = 0

    for s in snapshots:
        delay_dist[s.delay_status] = delay_dist.get(s.delay_status, 0) + 1
        perf_dist[s.performance_status] = perf_dist.get(s.performance_status, 0) + 1
        if s.delay_root_cause_category:
            cause_dist[s.delay_root_cause_category] = cause_dist.get(s.delay_root_cause_category, 0) + 1
        if s.is_critical_path and s.delay_status in ("CRITICAL_DELAY", "SCHEDULE_BREACH", "MINOR_DELAY"):
            cp_delayed_count += 1

    return SchedulePerformanceSummaryResponse(
        project_id=project_id,
        evaluation_date=evaluation_date,
        total_snapshots=total_count,
        mean_schedule_performance_index=mean_spi,
        total_schedule_variance_days=total_sv,
        critical_path_delayed_activities_count=cp_delayed_count,
        delay_status_distribution=delay_dist,
        delay_root_cause_distribution=cause_dist,
        performance_status_distribution=perf_dist,
        snapshots=[SchedulePerformanceSnapshotResponse.model_validate(s) for s in snapshots],
    )


def get_schedule_performance_snapshot(
    db: Session,
    project_id: str,
    performance_id: str,
    current_user: User,
) -> SchedulePerformanceSnapshot:
    """
    Retrieve an individual schedule performance snapshot by ID.
    Enforces project membership and verifies that the snapshot belongs to the project.
    """
    _verify_project_access(db, project_id, current_user)

    snapshot = (
        db.query(SchedulePerformanceSnapshot)
        .filter(
            SchedulePerformanceSnapshot.id == performance_id,
            SchedulePerformanceSnapshot.project_id == project_id,
        )
        .first()
    )
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SchedulePerformanceSnapshot {performance_id} not found in project {project_id}",
        )
    return snapshot


def list_schedule_performance_snapshots(
    db: Session,
    project_id: str,
    current_user: User,
    activity_id: Optional[str] = None,
    schedule_id: Optional[str] = None,
    delay_status: Optional[str] = None,
    performance_status: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> List[SchedulePerformanceSnapshot]:
    """
    List schedule performance snapshots for a project with optional activity, status, and performance filters.
    Enforces project membership, validates activity belongs to project if specified,
    and returns snapshots in deterministic chronological ordering.
    """
    _verify_project_access(db, project_id, current_user)

    if activity_id:
        act = (
            db.query(ConstructionActivity)
            .filter(
                ConstructionActivity.id == activity_id,
                ConstructionActivity.project_id == project_id,
            )
            .first()
        )
        if not act:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ConstructionActivity {activity_id} not found in project {project_id}",
            )

    q = db.query(SchedulePerformanceSnapshot).filter(SchedulePerformanceSnapshot.project_id == project_id)

    if activity_id:
        q = q.filter(SchedulePerformanceSnapshot.activity_id == activity_id)
    if schedule_id:
        q = q.filter(SchedulePerformanceSnapshot.schedule_id == schedule_id)
    if delay_status:
        clean_delay = delay_status.strip().upper()
        if clean_delay not in VALID_DELAY_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid delay_status filter '{delay_status}'. Allowed values: {sorted(list(VALID_DELAY_STATUSES))}",
            )
        q = q.filter(SchedulePerformanceSnapshot.delay_status == clean_delay)
    if performance_status:
        clean_perf = performance_status.strip().upper()
        if clean_perf not in VALID_PERFORMANCE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid performance_status filter '{performance_status}'. Allowed values: {sorted(list(VALID_PERFORMANCE_STATUSES))}",
            )
        q = q.filter(SchedulePerformanceSnapshot.performance_status == clean_perf)
    if status_filter:
        clean_status = status_filter.strip().upper()
        if clean_status not in VALID_SNAPSHOT_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status filter '{status_filter}'. Allowed values: {sorted(list(VALID_SNAPSHOT_STATUSES))}",
            )
        q = q.filter(SchedulePerformanceSnapshot.status == clean_status)

    return q.order_by(
        SchedulePerformanceSnapshot.evaluation_date.desc(),
        SchedulePerformanceSnapshot.created_at.desc(),
        SchedulePerformanceSnapshot.id.desc(),
    ).all()

