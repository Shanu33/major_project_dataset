"""Phase 1I: Daily Site Progress Monitoring & Activity Progress Tracking Endpoints.

Provides REST API routes for:
- Freezing monitoring baselines (supervisor / admin)
- Listing and viewing monitoring baselines
- Daily progress reports (DRAFT -> SUBMITTED -> FINALIZED)
- Adding activity progress under daily reports
- Supervisor verification/correction of activity progress (append-only)
- Deterministic plan-vs-actual variance calculation
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import (
    User,
    MonitoringBaseline,
    DailyProgressReport,
    DailyActivityProgress,
    DailyActivityProgressVerification,
)
from app.api.dependencies import require_project_access
from app.schemas.schemas import (
    MonitoringBaselineCreate,
    MonitoringBaselineResponse,
    DailyProgressReportCreate,
    DailyProgressReportResponse,
    DailyActivityProgressCreate,
    DailyActivityProgressResponse,
    DailyActivityProgressVerificationCreate,
    DailyActivityProgressVerificationResponse,
    ProgressVarianceResponse,
)
from app.services.monitoring import (
    freeze_monitoring_baseline,
    create_daily_progress_report,
    submit_daily_progress_report,
    finalize_daily_progress_report,
    add_daily_activity_progress,
    verify_daily_activity_progress,
    build_daily_activity_progress_response,
    calculate_progress_variance,
)

router = APIRouter()


def _ensure_role(user: User, allowed_roles: List[str]):
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation not permitted for role '{user.role}'. Required: {allowed_roles}",
        )


def _build_daily_report_response(report: DailyProgressReport) -> DailyProgressReportResponse:
    activities_dto = [
        build_daily_activity_progress_response(act)
        for act in (report.activity_progress_items or [])
    ]
    return DailyProgressReportResponse(
        id=report.id,
        project_id=report.project_id,
        report_date=report.report_date,
        submitted_by=report.submitted_by,
        submission_status=report.submission_status,
        created_at=report.created_at,
        metadata_json=report.metadata_json,
        activities=activities_dto,
    )


# ==============================================================================
# 1. MONITORING BASELINES
# ==============================================================================

@router.post(
    "/monitoring-baselines",
    response_model=MonitoringBaselineResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_monitoring_baseline_endpoint(
    project_id: str,
    baseline_in: MonitoringBaselineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["supervisor", "admin"])
    baseline = freeze_monitoring_baseline(
        db=db,
        project_id=project_id,
        schedule_id=baseline_in.schedule_id,
        current_user_id=current_user.id,
        baseline_start_date=baseline_in.baseline_start_date,
        metadata_json=baseline_in.metadata_json,
    )
    return baseline


@router.get(
    "/monitoring-baselines",
    response_model=List[MonitoringBaselineResponse],
    status_code=status.HTTP_200_OK,
)
def list_monitoring_baselines_endpoint(
    project_id: str,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    query = db.query(MonitoringBaseline).filter(MonitoringBaseline.project_id == project_id)
    if status_filter:
        query = query.filter(MonitoringBaseline.status == status_filter)
    return query.order_by(MonitoringBaseline.frozen_at.desc()).all()


@router.get(
    "/monitoring-baselines/{baseline_id}",
    response_model=MonitoringBaselineResponse,
    status_code=status.HTTP_200_OK,
)
def get_monitoring_baseline_endpoint(
    project_id: str,
    baseline_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    baseline = db.query(MonitoringBaseline).filter(
        MonitoringBaseline.id == baseline_id,
        MonitoringBaseline.project_id == project_id,
    ).first()
    if not baseline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitoring baseline not found in this project.",
        )
    return baseline


# ==============================================================================
# 2. DAILY PROGRESS REPORTS
# ==============================================================================

@router.post(
    "/daily-progress-reports",
    response_model=DailyProgressReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_daily_progress_report_endpoint(
    project_id: str,
    report_in: DailyProgressReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["contractor", "supervisor", "admin"])
    report = create_daily_progress_report(
        db=db,
        project_id=project_id,
        report_in=report_in,
        current_user_id=current_user.id,
    )
    return _build_daily_report_response(report)


@router.get(
    "/daily-progress-reports",
    response_model=List[DailyProgressReportResponse],
    status_code=status.HTTP_200_OK,
)
def list_daily_progress_reports_endpoint(
    project_id: str,
    report_date: Optional[date] = Query(None),
    submission_status: Optional[str] = Query(None),
    submitted_by: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    query = db.query(DailyProgressReport).filter(DailyProgressReport.project_id == project_id)
    if report_date:
        query = query.filter(DailyProgressReport.report_date == report_date)
    if submission_status:
        query = query.filter(DailyProgressReport.submission_status == submission_status)
    if submitted_by:
        query = query.filter(DailyProgressReport.submitted_by == submitted_by)
    reports = query.order_by(DailyProgressReport.report_date.desc(), DailyProgressReport.created_at.desc()).all()
    return [_build_daily_report_response(r) for r in reports]


@router.get(
    "/daily-progress-reports/{report_id}",
    response_model=DailyProgressReportResponse,
    status_code=status.HTTP_200_OK,
)
def get_daily_progress_report_endpoint(
    project_id: str,
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    report = db.query(DailyProgressReport).filter(
        DailyProgressReport.id == report_id,
        DailyProgressReport.project_id == project_id,
    ).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Daily progress report not found in this project.",
        )
    return _build_daily_report_response(report)


@router.post(
    "/daily-progress-reports/{report_id}/submit",
    response_model=DailyProgressReportResponse,
    status_code=status.HTTP_200_OK,
)
def submit_daily_progress_report_endpoint(
    project_id: str,
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["contractor", "supervisor", "admin"])
    report = submit_daily_progress_report(
        db=db,
        project_id=project_id,
        report_id=report_id,
        current_user_id=current_user.id,
    )
    return _build_daily_report_response(report)


@router.post(
    "/daily-progress-reports/{report_id}/finalize",
    response_model=DailyProgressReportResponse,
    status_code=status.HTTP_200_OK,
)
def finalize_daily_progress_report_endpoint(
    project_id: str,
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["supervisor", "admin"])
    report = finalize_daily_progress_report(
        db=db,
        project_id=project_id,
        report_id=report_id,
        current_user_id=current_user.id,
    )
    return _build_daily_report_response(report)


# ==============================================================================
# 3. DAILY ACTIVITY PROGRESS
# ==============================================================================

@router.post(
    "/daily-progress-reports/{report_id}/activities",
    response_model=DailyActivityProgressResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_daily_activity_progress_endpoint(
    project_id: str,
    report_id: str,
    progress_in: DailyActivityProgressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["contractor", "supervisor", "admin"])
    prog = add_daily_activity_progress(
        db=db,
        project_id=project_id,
        report_id=report_id,
        progress_in=progress_in,
        current_user_id=current_user.id,
    )
    return build_daily_activity_progress_response(prog)


@router.get(
    "/daily-progress-reports/{report_id}/activities",
    response_model=List[DailyActivityProgressResponse],
    status_code=status.HTTP_200_OK,
)
def list_daily_activity_progress_endpoint(
    project_id: str,
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    report = db.query(DailyProgressReport).filter(
        DailyProgressReport.id == report_id,
        DailyProgressReport.project_id == project_id,
    ).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Daily progress report not found in this project.",
        )
    return [
        build_daily_activity_progress_response(p)
        for p in (report.activity_progress_items or [])
    ]


# ==============================================================================
# 4. SUPERVISOR VERIFICATION
# ==============================================================================

@router.post(
    "/progress/{progress_id}/verify",
    response_model=DailyActivityProgressVerificationResponse,
    status_code=status.HTTP_201_CREATED,
)
def verify_daily_activity_progress_endpoint(
    project_id: str,
    progress_id: str,
    verification_in: DailyActivityProgressVerificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["supervisor", "admin"])
    ver = verify_daily_activity_progress(
        db=db,
        project_id=project_id,
        progress_id=progress_id,
        verification_in=verification_in,
        current_user_id=current_user.id,
    )
    return ver


@router.get(
    "/progress/{progress_id}/verifications",
    response_model=List[DailyActivityProgressVerificationResponse],
    status_code=status.HTTP_200_OK,
)
def list_daily_activity_progress_verifications_endpoint(
    project_id: str,
    progress_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    prog = db.query(DailyActivityProgress).filter(
        DailyActivityProgress.id == progress_id,
        DailyActivityProgress.project_id == project_id,
    ).first()
    if not prog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Daily activity progress not found in this project.",
        )
    verifications = db.query(DailyActivityProgressVerification).filter(
        DailyActivityProgressVerification.daily_activity_progress_id == progress_id,
        DailyActivityProgressVerification.project_id == project_id,
    ).order_by(DailyActivityProgressVerification.verified_at.asc()).all()
    return verifications


# ==============================================================================
# 5. DETERMINISTIC PROGRESS VARIANCE
# ==============================================================================

@router.get(
    "/progress/{progress_id}/variance",
    response_model=ProgressVarianceResponse,
    status_code=status.HTTP_200_OK,
)
def get_progress_variance_endpoint(
    project_id: str,
    progress_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    variance = calculate_progress_variance(
        db=db,
        project_id=project_id,
        progress_id=progress_id,
    )
    return variance
