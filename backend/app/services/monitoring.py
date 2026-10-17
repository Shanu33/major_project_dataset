"""Phase 1I: Daily Site Progress Monitoring & Activity Progress Tracking Service.

Implements:
- MonitoringBaseline freezing linked to Phase 1H ConstructionSchedule
- DailyProgressReport lifecycle (DRAFT -> SUBMITTED -> FINALIZED)
- Contractor DailyActivityProgress declaration
- Supervisor DailyActivityProgressVerification (append-only)
- Preservation of both contractor-declared and supervisor-verified values
- Deterministic plan-vs-actual variance calculation
- Transactional audit logging
"""
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import (
    Project,
    User,
    ConstructionActivity,
    ConstructionSchedule,
    ActivityScheduleResult,
    EngineeringCalculation,
    MonitoringBaseline,
    DailyProgressReport,
    DailyActivityProgress,
    DailyActivityProgressVerification,
    generate_uuid,
)
from app.schemas.schemas import (
    MonitoringBaselineCreate,
    DailyProgressReportCreate,
    DailyActivityProgressCreate,
    DailyActivityProgressVerificationCreate,
    MonitoringBaselineStatusEnum,
    ReportSubmissionStatusEnum,
    ActivityProgressStatusEnum,
    ProgressVerificationStatusEnum,
    ProgressSourceClassificationEnum,
    VarianceStatusEnum,
    ProgressVarianceResponse,
    DailyActivityProgressResponse,
    DailyActivityProgressVerificationResponse,
)
from app.services.audit import log_action


def freeze_monitoring_baseline(
    db: Session,
    project_id: str,
    schedule_id: str,
    baseline_start_date: date,
    current_user_id: str,
    metadata_json: Optional[Dict[str, Any]] = None,
) -> MonitoringBaseline:
    """Freeze a calculated schedule as the official monitoring baseline for progress comparison."""
    if not baseline_start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_INPUT: baseline_start_date is required to freeze a monitoring baseline."
        )

    # Lock project row to prevent race conditions
    project = db.query(Project).filter(Project.id == project_id).with_for_update().first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )

    schedule = db.query(ConstructionSchedule).filter(
        ConstructionSchedule.id == schedule_id,
        ConstructionSchedule.project_id == project_id,
    ).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found or does not belong to this project."
        )

    if schedule.calculation_status != "CALCULATED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"INVALID_INPUT: Only CALCULATED schedules can be frozen as monitoring baselines. Status is '{schedule.calculation_status}'."
        )

    if not schedule.algorithm_version or not str(schedule.algorithm_version).strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_INPUT: Schedule algorithm_version is missing. Cannot freeze monitoring baseline."
        )

    # Supersede previous active baselines
    db.query(MonitoringBaseline).filter(
        MonitoringBaseline.project_id == project_id,
        MonitoringBaseline.status == "ACTIVE",
    ).update({"status": "SUPERSEDED"}, synchronize_session=False)

    baseline_id = generate_uuid()
    baseline = MonitoringBaseline(
        id=baseline_id,
        project_id=project_id,
        schedule_id=schedule.id,
        schedule_version=schedule.schedule_version,
        schedule_algorithm_version=schedule.algorithm_version,
        baseline_start_date=baseline_start_date,
        frozen_by=current_user_id,
        status="ACTIVE",
        metadata_json=metadata_json,
    )
    db.add(baseline)

    log_action(
        db=db,
        user_id=current_user_id,
        action="FREEZE_MONITORING_BASELINE",
        entity_type="MonitoringBaseline",
        entity_id=baseline.id,
        reason=f"Frozen monitoring baseline for schedule version {schedule.schedule_version}",
    )

    try:
        db.commit()
        db.refresh(baseline)
        return baseline
    except Exception:
        db.rollback()
        raise


def create_daily_progress_report(
    db: Session,
    project_id: str,
    report_in: DailyProgressReportCreate,
    current_user_id: str,
) -> DailyProgressReport:
    """Create a new daily progress report in DRAFT status."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )

    # Check duplicate finalized report for this project and date
    existing_final = db.query(DailyProgressReport).filter(
        DailyProgressReport.project_id == project_id,
        DailyProgressReport.report_date == report_in.report_date,
        DailyProgressReport.submission_status == "FINALIZED",
    ).first()
    if existing_final:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A finalized daily progress report already exists for project {project_id} on date {report_in.report_date}."
        )

    report_id = generate_uuid()
    report = DailyProgressReport(
        id=report_id,
        project_id=project_id,
        report_date=report_in.report_date,
        submitted_by=current_user_id,
        submission_status="DRAFT",
        metadata_json=report_in.metadata_json,
    )
    db.add(report)

    log_action(
        db=db,
        user_id=current_user_id,
        action="CREATE_DAILY_PROGRESS_REPORT",
        entity_type="DailyProgressReport",
        entity_id=report.id,
        reason=f"Created DRAFT report for date {report_in.report_date}",
    )

    try:
        db.commit()
        db.refresh(report)
        return report
    except Exception:
        db.rollback()
        raise


def submit_daily_progress_report(
    db: Session,
    project_id: str,
    report_id: str,
    current_user_id: str,
) -> DailyProgressReport:
    """Transition daily report from DRAFT to SUBMITTED."""
    report = db.query(DailyProgressReport).filter(
        DailyProgressReport.id == report_id,
        DailyProgressReport.project_id == project_id,
    ).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Daily progress report not found in this project."
        )

    if report.submission_status == "FINALIZED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report is already FINALIZED and cannot be modified."
        )

    if report.submission_status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report is not in DRAFT status. Current status: '{report.submission_status}'."
        )

    report.submission_status = "SUBMITTED"

    log_action(
        db=db,
        user_id=current_user_id,
        action="SUBMIT_DAILY_PROGRESS_REPORT",
        entity_type="DailyProgressReport",
        entity_id=report.id,
        reason="Submitted daily progress report",
    )

    try:
        db.commit()
        db.refresh(report)
        return report
    except Exception:
        db.rollback()
        raise


def finalize_daily_progress_report(
    db: Session,
    project_id: str,
    report_id: str,
    current_user_id: str,
) -> DailyProgressReport:
    """Finalize a submitted report, making it immutable at the database level."""
    report = db.query(DailyProgressReport).filter(
        DailyProgressReport.id == report_id,
        DailyProgressReport.project_id == project_id,
    ).with_for_update().first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Daily progress report not found in this project."
        )

    if report.submission_status == "FINALIZED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report is already FINALIZED."
        )

    if report.submission_status != "SUBMITTED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only SUBMITTED daily reports can be FINALIZED. Current status: '{report.submission_status}'."
        )

    # Check uniqueness of finalized report for this date
    existing_final = db.query(DailyProgressReport).filter(
        DailyProgressReport.project_id == project_id,
        DailyProgressReport.report_date == report.report_date,
        DailyProgressReport.submission_status == "FINALIZED",
        DailyProgressReport.id != report.id,
    ).first()
    if existing_final:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A finalized daily progress report already exists for date {report.report_date}."
        )

    report.submission_status = "FINALIZED"

    log_action(
        db=db,
        user_id=current_user_id,
        action="FINALIZE_DAILY_PROGRESS_REPORT",
        entity_type="DailyProgressReport",
        entity_id=report.id,
        reason="Finalized daily progress report",
    )

    try:
        db.commit()
        db.refresh(report)
        return report
    except Exception:
        db.rollback()
        raise


def add_daily_activity_progress(
    db: Session,
    project_id: str,
    report_id: str,
    progress_in: DailyActivityProgressCreate,
    current_user_id: str,
) -> DailyActivityProgress:
    """Record contractor-submitted activity progress under a daily report."""
    report = db.query(DailyProgressReport).filter(
        DailyProgressReport.id == report_id,
        DailyProgressReport.project_id == project_id,
    ).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Daily progress report not found in this project."
        )

    if report.submission_status == "FINALIZED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add activity progress to a FINALIZED daily report."
        )

    activity = db.query(ConstructionActivity).filter(
        ConstructionActivity.id == progress_in.activity_id,
        ConstructionActivity.project_id == project_id,
    ).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found or does not belong to this project."
        )

    if activity.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot report progress on inactive or deprecated activity '{activity.activity_code}'. Status: '{activity.status}'."
        )

    # Validations
    if progress_in.contractor_progress_value is not None:
        if progress_in.contractor_progress_value < Decimal("0"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: Progress quantity cannot be negative."
            )
        if not progress_in.contractor_progress_unit or not progress_in.contractor_progress_unit.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: Unit must be specified when progress quantity is provided."
            )

    if progress_in.contractor_percent_complete is not None:
        if progress_in.contractor_percent_complete < Decimal("0") or progress_in.contractor_percent_complete > Decimal("100"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: Percent complete must be between 0 and 100."
            )

    if progress_in.contractor_remaining_duration is not None:
        if progress_in.contractor_remaining_duration < Decimal("0"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: Remaining duration cannot be negative."
            )

    if progress_in.contractor_actual_start and progress_in.contractor_actual_finish:
        if progress_in.contractor_actual_finish < progress_in.contractor_actual_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: Actual finish date cannot precede actual start date."
            )

    prog_id = generate_uuid()
    prog = DailyActivityProgress(
        id=prog_id,
        daily_report_id=report_id,
        project_id=project_id,
        activity_id=activity.id,
        scheduled_activity_reference=activity.activity_code,
        contractor_progress_value=progress_in.contractor_progress_value,
        contractor_progress_unit=progress_in.contractor_progress_unit,
        contractor_percent_complete=progress_in.contractor_percent_complete,
        contractor_actual_start=progress_in.contractor_actual_start,
        contractor_actual_finish=progress_in.contractor_actual_finish,
        contractor_remaining_duration=progress_in.contractor_remaining_duration,
        contractor_status=progress_in.contractor_status.value if hasattr(progress_in.contractor_status, "value") else progress_in.contractor_status,
        created_by=current_user_id,
        metadata_json=progress_in.metadata_json,
    )
    db.add(prog)

    log_action(
        db=db,
        user_id=current_user_id,
        action="ADD_ACTIVITY_PROGRESS",
        entity_type="DailyActivityProgress",
        entity_id=prog.id,
        reason=f"Contractor progress recorded for activity {activity.activity_code}",
    )

    try:
        db.commit()
        db.refresh(prog)
        return prog
    except Exception:
        db.rollback()
        raise


def verify_daily_activity_progress(
    db: Session,
    project_id: str,
    progress_id: str,
    verification_in: DailyActivityProgressVerificationCreate,
    current_user_id: str,
) -> DailyActivityProgressVerification:
    """Record an append-only supervisor verification/correction without mutating contractor data."""
    prog = db.query(DailyActivityProgress).filter(
        DailyActivityProgress.id == progress_id,
        DailyActivityProgress.project_id == project_id,
    ).first()
    if not prog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Daily activity progress not found in this project."
        )

    # Validations
    if verification_in.verified_quantity is not None:
        if verification_in.verified_quantity < Decimal("0"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: Verified quantity cannot be negative."
            )
        if not verification_in.verified_quantity_unit or not verification_in.verified_quantity_unit.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: Unit must be specified when verified quantity is provided."
            )

    if verification_in.verified_percent_complete is not None:
        if verification_in.verified_percent_complete < Decimal("0") or verification_in.verified_percent_complete > Decimal("100"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: Verified percent complete must be between 0 and 100."
            )

    if verification_in.verified_remaining_duration is not None:
        if verification_in.verified_remaining_duration < Decimal("0"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: Verified remaining duration cannot be negative."
            )

    if verification_in.verified_actual_start and verification_in.verified_actual_finish:
        if verification_in.verified_actual_finish < verification_in.verified_actual_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: Verified actual finish date cannot precede actual start date."
            )

    ver_id = generate_uuid()
    ver = DailyActivityProgressVerification(
        id=ver_id,
        daily_activity_progress_id=progress_id,
        project_id=project_id,
        verification_status=verification_in.verification_status.value if hasattr(verification_in.verification_status, "value") else verification_in.verification_status,
        verified_quantity=verification_in.verified_quantity,
        verified_quantity_unit=verification_in.verified_quantity_unit,
        verified_percent_complete=verification_in.verified_percent_complete,
        verified_actual_start=verification_in.verified_actual_start,
        verified_actual_finish=verification_in.verified_actual_finish,
        verified_remaining_duration=verification_in.verified_remaining_duration,
        verified_status=verification_in.verified_status.value if hasattr(verification_in.verified_status, "value") and verification_in.verified_status else verification_in.verified_status,
        verification_note=verification_in.verification_note,
        verified_by=current_user_id,
        metadata_json=verification_in.metadata_json,
    )
    db.add(ver)

    log_action(
        db=db,
        user_id=current_user_id,
        action="VERIFY_ACTIVITY_PROGRESS",
        entity_type="DailyActivityProgressVerification",
        entity_id=ver.id,
        reason=f"Supervisor verification recorded with status {ver.verification_status}",
    )

    try:
        db.commit()
        db.refresh(ver)
        return ver
    except Exception:
        db.rollback()
        raise


def build_daily_activity_progress_response(
    prog: DailyActivityProgress,
) -> DailyActivityProgressResponse:
    """Build response DTO including latest verification and authoritative operational values."""
    verifications = prog.verifications or []
    sorted_vers = sorted(verifications, key=lambda v: (v.verified_at or datetime.min, v.id or ""), reverse=True) if verifications else []
    latest_ver = sorted_vers[0] if sorted_vers else None

    operational_value = prog.contractor_progress_value
    operational_percent = prog.contractor_percent_complete
    operational_status = prog.contractor_status
    verification_status = None

    if latest_ver:
        verification_status = latest_ver.verification_status
        if latest_ver.verification_status in {"VERIFIED", "CORRECTED"}:
            if latest_ver.verified_quantity is not None:
                operational_value = latest_ver.verified_quantity
            if latest_ver.verified_percent_complete is not None:
                operational_percent = latest_ver.verified_percent_complete
            if latest_ver.verified_status:
                operational_status = latest_ver.verified_status

    latest_ver_dto = None
    if latest_ver:
        latest_ver_dto = DailyActivityProgressVerificationResponse(
            id=latest_ver.id,
            daily_activity_progress_id=latest_ver.daily_activity_progress_id,
            project_id=latest_ver.project_id,
            verification_status=latest_ver.verification_status,
            verified_quantity=latest_ver.verified_quantity,
            verified_quantity_unit=latest_ver.verified_quantity_unit,
            verified_percent_complete=latest_ver.verified_percent_complete,
            verified_actual_start=latest_ver.verified_actual_start,
            verified_actual_finish=latest_ver.verified_actual_finish,
            verified_remaining_duration=latest_ver.verified_remaining_duration,
            verified_status=latest_ver.verified_status,
            verification_note=latest_ver.verification_note,
            verified_by=latest_ver.verified_by,
            verified_at=latest_ver.verified_at,
            metadata_json=latest_ver.metadata_json,
        )

    return DailyActivityProgressResponse(
        id=prog.id,
        daily_report_id=prog.daily_report_id,
        project_id=prog.project_id,
        activity_id=prog.activity_id,
        activity_code=prog.activity.activity_code if prog.activity else prog.scheduled_activity_reference,
        activity_name=prog.activity.activity_name if prog.activity else None,
        scheduled_activity_reference=prog.scheduled_activity_reference,
        contractor_progress_value=prog.contractor_progress_value,
        contractor_progress_unit=prog.contractor_progress_unit,
        contractor_percent_complete=prog.contractor_percent_complete,
        contractor_actual_start=prog.contractor_actual_start,
        contractor_actual_finish=prog.contractor_actual_finish,
        contractor_remaining_duration=prog.contractor_remaining_duration,
        contractor_status=prog.contractor_status,
        created_by=prog.created_by,
        created_at=prog.created_at,
        metadata_json=prog.metadata_json,
        latest_verification=latest_ver_dto,
        operational_value=operational_value,
        operational_percent=operational_percent,
        operational_status=operational_status,
        verification_status=verification_status,
    )


def calculate_progress_variance(
    db: Session,
    project_id: str,
    progress_id: str,
) -> ProgressVarianceResponse:
    """Calculate deterministic plan vs actual progress variance against the active monitoring baseline."""
    prog = db.query(DailyActivityProgress).filter(
        DailyActivityProgress.id == progress_id,
        DailyActivityProgress.project_id == project_id,
    ).first()
    if not prog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Daily activity progress not found in this project."
        )

    # Active monitoring baseline
    baseline = db.query(MonitoringBaseline).filter(
        MonitoringBaseline.project_id == project_id,
        MonitoringBaseline.status == "ACTIVE",
    ).first()

    planned_duration = None
    baseline_id = None
    schedule_id = None
    schedule_version = None
    schedule_algorithm_version = None
    baseline_start_date = None
    planned_start = None
    planned_finish = None

    if baseline:
        baseline_id = baseline.id
        schedule_id = baseline.schedule_id
        schedule_version = baseline.schedule_version
        schedule_algorithm_version = baseline.schedule_algorithm_version
        baseline_start_date = baseline.baseline_start_date
        sched_res = db.query(ActivityScheduleResult).filter(
            ActivityScheduleResult.schedule_id == baseline.schedule_id,
            ActivityScheduleResult.activity_id == prog.activity_id,
        ).first()
        if sched_res:
            planned_duration = sched_res.ef - sched_res.es

            # Authoritative calendar anchor strictly from baseline.baseline_start_date
            if baseline.baseline_start_date:
                planned_start = baseline.baseline_start_date + timedelta(days=int(sched_res.es))
                planned_finish = baseline.baseline_start_date + timedelta(days=int(sched_res.ef))

    # Look up latest verification deterministically (verified_at DESC, id DESC)
    latest_ver = db.query(DailyActivityProgressVerification).filter(
        DailyActivityProgressVerification.daily_activity_progress_id == prog.id
    ).order_by(
        DailyActivityProgressVerification.verified_at.desc(),
        DailyActivityProgressVerification.id.desc(),
    ).first()

    operational_quantity = prog.contractor_progress_value
    operational_percent = prog.contractor_percent_complete
    actual_start = prog.contractor_actual_start
    actual_finish = prog.contractor_actual_finish
    operational_source = ProgressSourceClassificationEnum.CONTRACTOR_DECLARED
    verification_status = None

    if latest_ver and latest_ver.verification_status in {"VERIFIED", "CORRECTED"}:
        operational_source = ProgressSourceClassificationEnum.SUPERVISOR_VERIFIED
        verification_status = latest_ver.verification_status
        if latest_ver.verified_quantity is not None:
            operational_quantity = latest_ver.verified_quantity
        if latest_ver.verified_percent_complete is not None:
            operational_percent = latest_ver.verified_percent_complete
        if latest_ver.verified_actual_start:
            actual_start = latest_ver.verified_actual_start
        if latest_ver.verified_actual_finish:
            actual_finish = latest_ver.verified_actual_finish
    elif latest_ver:
        verification_status = latest_ver.verification_status

    # Actual duration: inclusive convention (actual_finish - actual_start) + 1
    actual_duration = None
    duration_variance = None

    if actual_start and actual_finish:
        actual_duration = Decimal(str((actual_finish - actual_start).days + 1))
        if planned_duration is not None:
            duration_variance = actual_duration - planned_duration

    # Finish variance: only if both actual finish and planned finish are available
    finish_variance = None
    if actual_finish and planned_finish:
        finish_variance = Decimal(str((actual_finish - planned_finish).days))

    # Deterministic variance status classification based on finish variance
    variance_status = VarianceStatusEnum.NOT_AVAILABLE
    if finish_variance is not None:
        if finish_variance > Decimal("0"):
            variance_status = VarianceStatusEnum.DELAYED
        elif finish_variance == Decimal("0"):
            variance_status = VarianceStatusEnum.ON_SCHEDULE
        else:
            variance_status = VarianceStatusEnum.AHEAD

    # Planned quantity lookup (from verified engineering calculation on element if available)
    planned_quantity = None
    quantity_variance = None
    if prog.activity and prog.activity.engineering_element_id:
        calc = db.query(EngineeringCalculation).filter(
            EngineeringCalculation.engineering_element_id == prog.activity.engineering_element_id,
            EngineeringCalculation.status == "CALCULATED",
        ).order_by(EngineeringCalculation.created_at.desc()).first()
        if calc and calc.result_value is not None:
            planned_quantity = calc.result_value
            if operational_quantity is not None:
                # Check unit compatibility
                op_unit = (
                    latest_ver.verified_quantity_unit
                    if (latest_ver and latest_ver.verification_status in {"VERIFIED", "CORRECTED"} and latest_ver.verified_quantity is not None)
                    else prog.contractor_progress_unit
                )
                if calc.result_unit and op_unit:
                    if calc.result_unit.strip().lower() == op_unit.strip().lower():
                        quantity_variance = operational_quantity - planned_quantity
                    else:
                        quantity_variance = None
                else:
                    quantity_variance = operational_quantity - planned_quantity

    return ProgressVarianceResponse(
        project_id=prog.project_id,
        daily_activity_progress_id=prog.id,
        activity_id=prog.activity_id,
        activity_code=prog.activity.activity_code if prog.activity else prog.scheduled_activity_reference,
        activity_name=prog.activity.activity_name if prog.activity else None,
        baseline_id=baseline_id,
        monitoring_baseline_id=baseline_id,
        schedule_id=schedule_id,
        schedule_version=schedule_version,
        schedule_algorithm_version=schedule_algorithm_version,
        baseline_start_date=baseline_start_date,
        planned_start=planned_start,
        planned_finish=planned_finish,
        actual_start=actual_start,
        actual_finish=actual_finish,
        planned_duration=planned_duration,
        actual_duration=actual_duration,
        duration_variance=duration_variance,
        finish_variance=finish_variance,
        contractor_declared_quantity=prog.contractor_progress_value,
        supervisor_verified_quantity=latest_ver.verified_quantity if latest_ver else None,
        operational_quantity=operational_quantity,
        planned_quantity=planned_quantity,
        quantity_variance=quantity_variance,
        contractor_declared_percent=prog.contractor_percent_complete,
        supervisor_verified_percent=latest_ver.verified_percent_complete if latest_ver else None,
        operational_percent=operational_percent,
        operational_source=operational_source,
        verification_status=verification_status,
        status=variance_status,
        variance_status=variance_status,
    )
