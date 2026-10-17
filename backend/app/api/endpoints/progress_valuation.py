"""Phase 1L: Site Progress Valuation & Certified Progress Foundation Endpoints.

Provides REST API routes for:
- Creating / superseding ActivityRateMapping
- Listing ActivityRateMappings
- Evaluating DailyProgressReport to produce DailyProgressValuations
- Listing DailyProgressValuations
- Creating draft PeriodProgressCertificates (PERIOD_SNAPSHOT)
- Listing / retrieving PeriodProgressCertificates
- Certifying PeriodProgressCertificates
- Deleting draft PeriodProgressCertificates
- Superseding PeriodProgressCertificates (Admin only)
- Real-time financial progress summary
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.api.dependencies import get_current_user, require_project_access
from app.schemas.progress_valuation import (
    ActivityRateMappingCreate,
    ActivityRateMappingResponse,
    DailyReportValuationRequest,
    DailyReportValuationResponse,
    DailyProgressValuationResponse,
    PeriodCertificateCreate,
    PeriodCertificateResponse,
    PeriodCertificateSupersedeRequest,
    FinancialProgressSummaryResponse,
)
from app.services.progress_valuation_service import (
    create_activity_rate_mapping,
    list_activity_rate_mappings,
    evaluate_daily_progress_report,
    list_daily_progress_valuations,
    create_draft_period_certificate,
    certify_period_certificate,
    delete_draft_period_certificate,
    supersede_period_certificate,
    get_period_certificate,
    list_period_certificates,
    get_financial_progress_summary,
)

router = APIRouter()


def _ensure_role(user: User, allowed_roles: List[str]):
    if user.role.lower() not in [r.lower() for r in allowed_roles]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation not permitted for role '{user.role}'. Required: {allowed_roles}",
        )


# ==============================================================================
# 1. Activity Rate Mapping Routes
# ==============================================================================

@router.post(
    "/projects/{project_id}/activity-rate-mappings",
    response_model=ActivityRateMappingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_rate_mapping(
    project_id: str,
    payload: ActivityRateMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """Maps a construction activity to a confirmed cost rate. Requires ADMIN or SUPERVISOR."""
    _ensure_role(current_user, ["admin", "supervisor"])
    return create_activity_rate_mapping(
        db=db,
        project_id=project_id,
        payload=payload,
        current_user_id=current_user.id,
    )


@router.get(
    "/projects/{project_id}/activity-rate-mappings",
    response_model=List[ActivityRateMappingResponse],
)
def list_rate_mappings(
    project_id: str,
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, SUPERSEDED)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """Lists activity rate mappings for a project. Accessible by ADMIN, SUPERVISOR, CONTRACTOR."""
    _ensure_role(current_user, ["admin", "supervisor", "contractor"])
    return list_activity_rate_mappings(
        db=db,
        project_id=project_id,
        status_filter=status,
    )


# ==============================================================================
# 2. Daily Progress Valuation Routes
# ==============================================================================

@router.post(
    "/projects/{project_id}/progress-valuations/evaluate-report",
    response_model=DailyReportValuationResponse,
)
def evaluate_report_progress(
    project_id: str,
    payload: DailyReportValuationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """Evaluates verified physical progress in a FINALIZED daily report. Requires ADMIN or SUPERVISOR."""
    _ensure_role(current_user, ["admin", "supervisor"])
    valuations, claimed, certified, disputed, currency = evaluate_daily_progress_report(
        db=db,
        project_id=project_id,
        report_id=payload.daily_progress_report_id,
        current_user_id=current_user.id,
    )
    return DailyReportValuationResponse(
        daily_progress_report_id=payload.daily_progress_report_id,
        valuations_count=len(valuations),
        total_claimed_value=claimed,
        total_certified_value=certified,
        total_disputed_exposure=disputed,
        currency=currency,
        valuations=valuations,
    )


@router.get(
    "/projects/{project_id}/progress-valuations",
    response_model=List[DailyProgressValuationResponse],
)
def list_progress_valuations(
    project_id: str,
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, SUPERSEDED)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """Lists progress valuations for a project. Accessible by ADMIN, SUPERVISOR, CONTRACTOR."""
    _ensure_role(current_user, ["admin", "supervisor", "contractor"])
    return list_daily_progress_valuations(
        db=db,
        project_id=project_id,
        status_filter=status,
    )


# ==============================================================================
# 3. Period Progress Certificate Routes
# ==============================================================================

@router.post(
    "/projects/{project_id}/period-certificates",
    response_model=PeriodCertificateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_certificate(
    project_id: str,
    payload: PeriodCertificateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """Drafts a Running-Account period progress certificate (PERIOD_SNAPSHOT). Requires ADMIN or SUPERVISOR."""
    _ensure_role(current_user, ["admin", "supervisor"])
    return create_draft_period_certificate(
        db=db,
        project_id=project_id,
        payload=payload,
        current_user_id=current_user.id,
    )


@router.get(
    "/projects/{project_id}/period-certificates",
    response_model=List[PeriodCertificateResponse],
)
def list_certificates(
    project_id: str,
    status: Optional[str] = Query(None, description="Filter by status (DRAFT, CERTIFIED, SUPERSEDED)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """Lists period progress certificates for a project. Accessible by ADMIN, SUPERVISOR, CONTRACTOR."""
    _ensure_role(current_user, ["admin", "supervisor", "contractor"])
    return list_period_certificates(
        db=db,
        project_id=project_id,
        status_filter=status,
    )


@router.get(
    "/projects/{project_id}/period-certificates/{cert_id}",
    response_model=PeriodCertificateResponse,
)
def get_certificate(
    project_id: str,
    cert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """Retrieves a single period progress certificate with line items. Accessible by ADMIN, SUPERVISOR, CONTRACTOR."""
    _ensure_role(current_user, ["admin", "supervisor", "contractor"])
    return get_period_certificate(
        db=db,
        project_id=project_id,
        cert_id=cert_id,
    )


@router.post(
    "/projects/{project_id}/period-certificates/{cert_id}/certify",
    response_model=PeriodCertificateResponse,
)
def certify_certificate(
    project_id: str,
    cert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """Certifies and freezes a DRAFT period progress certificate. Requires ADMIN or SUPERVISOR."""
    _ensure_role(current_user, ["admin", "supervisor"])
    return certify_period_certificate(
        db=db,
        project_id=project_id,
        cert_id=cert_id,
        current_user_id=current_user.id,
    )


@router.delete(
    "/projects/{project_id}/period-certificates/{cert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_certificate(
    project_id: str,
    cert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """Deletes a DRAFT period progress certificate. Requires ADMIN or SUPERVISOR."""
    _ensure_role(current_user, ["admin", "supervisor"])
    delete_draft_period_certificate(
        db=db,
        project_id=project_id,
        cert_id=cert_id,
        current_user_id=current_user.id,
    )
    return None


@router.post(
    "/projects/{project_id}/period-certificates/{cert_id}/supersede",
    response_model=PeriodCertificateResponse,
)
def supersede_certificate(
    project_id: str,
    cert_id: str,
    payload: PeriodCertificateSupersedeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """Administratively supersedes a CERTIFIED certificate. Restricted to ADMIN ONLY."""
    _ensure_role(current_user, ["admin"])
    return supersede_period_certificate(
        db=db,
        project_id=project_id,
        cert_id=cert_id,
        payload=payload,
        current_user_id=current_user.id,
    )


# ==============================================================================
# 4. Project Financial Progress Summary Route
# ==============================================================================

@router.get(
    "/projects/{project_id}/financial-progress-summary",
    response_model=FinancialProgressSummaryResponse,
)
def get_summary(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """Retrieves real-time project financial progress summary. Accessible by ADMIN, SUPERVISOR, CONTRACTOR."""
    _ensure_role(current_user, ["admin", "supervisor", "contractor"])
    return get_financial_progress_summary(
        db=db,
        project_id=project_id,
    )
