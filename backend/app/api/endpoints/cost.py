"""Phase 1K: Deterministic Cost Estimation & Rate-Based Valuation Endpoints.

Provides REST API routes for:
- Declaring cost rates (project-specific and global catalog)
- Confirming cost rates with atomic supersession
- Deleting draft cost rates
- Listing cost rates
- Executing deterministic cost calculations (total_cost = quantity * rate)
- Listing cost calculations
- Project cost aggregation and comparative valuation summary
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, CostRate, ProjectMember, Project
from app.api.dependencies import get_current_user, require_project_access
from app.schemas.schemas import (
    CostRateCreate,
    CostRateResponse,
    CostCalculationCreate,
    CostCalculationResponse,
    ProjectCostSummaryResponse,
)
from app.services.cost_estimation import (
    declare_cost_rate,
    confirm_cost_rate,
    delete_draft_cost_rate,
    list_cost_rates,
    execute_cost_calculation,
    list_cost_calculations,
    get_project_cost_summary,
)

router = APIRouter()


def _ensure_role(user: User, allowed_roles: List[str]):
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation not permitted for role '{user.role}'. Required: {allowed_roles}",
        )


def _check_rate_access(db: Session, rate: CostRate, user: User):
    if user.role == "admin":
        return
    if rate.project_id is not None:
        proj = db.query(Project).filter(Project.id == rate.project_id).first()
        if not proj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
        if proj.created_by == user.id:
            return
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == rate.project_id,
            ProjectMember.user_id == user.id,
        ).first()
        if not member:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this project.")


# ==============================================================================
# COST RATES
# ==============================================================================

@router.post(
    "/projects/{project_id}/cost-rates",
    response_model=CostRateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project_cost_rate(
    project_id: str,
    payload: CostRateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """
    Declares a new project-specific cost rate in DRAFT status.
    Allowed roles: contractor, supervisor, admin.
    """
    _ensure_role(current_user, ["contractor", "supervisor", "admin"])
    return declare_cost_rate(
        db=db,
        project_id=project_id,
        payload=payload,
        current_user_id=current_user.id,
    )


@router.post(
    "/cost-rates",
    response_model=CostRateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_global_cost_rate(
    payload: CostRateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Declares a new global catalog cost rate in DRAFT status.
    Allowed roles: supervisor, admin.
    """
    _ensure_role(current_user, ["supervisor", "admin"])
    return declare_cost_rate(
        db=db,
        project_id=None,
        payload=payload,
        current_user_id=current_user.id,
    )


@router.patch(
    "/cost-rates/{rate_id}/confirm",
    response_model=CostRateResponse,
    status_code=status.HTTP_200_OK,
)
@router.post(
    "/cost-rates/{rate_id}/confirm",
    response_model=CostRateResponse,
    status_code=status.HTTP_200_OK,
)
def confirm_cost_rate_endpoint(
    rate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Confirms a DRAFT cost rate.
    Allowed roles: supervisor, admin.
    """
    _ensure_role(current_user, ["supervisor", "admin"])
    rate = db.query(CostRate).filter(CostRate.id == rate_id).first()
    if not rate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cost rate {rate_id} not found.")
    _check_rate_access(db, rate, current_user)
    return confirm_cost_rate(db=db, rate_id=rate_id, current_user_id=current_user.id)


@router.delete(
    "/cost-rates/{rate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_cost_rate_endpoint(
    rate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Deletes a DRAFT cost rate. Non-draft rates are rejected.
    Allowed roles: contractor, supervisor, admin.
    """
    _ensure_role(current_user, ["contractor", "supervisor", "admin"])
    rate = db.query(CostRate).filter(CostRate.id == rate_id).first()
    if not rate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cost rate {rate_id} not found.")
    _check_rate_access(db, rate, current_user)
    delete_draft_cost_rate(db=db, rate_id=rate_id, current_user_id=current_user.id)
    return None


@router.get(
    "/projects/{project_id}/cost-rates",
    response_model=List[CostRateResponse],
    status_code=status.HTTP_200_OK,
)
def list_project_cost_rates(
    project_id: str,
    status_filter: Optional[str] = Query(None, alias="status"),
    rate_code: Optional[str] = Query(None),
    include_global: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """
    Lists cost rates available to the project (including global by default).
    Allowed roles: contractor, supervisor, admin.
    """
    _ensure_role(current_user, ["contractor", "supervisor", "admin"])
    return list_cost_rates(
        db=db,
        project_id=project_id,
        status_filter=status_filter,
        rate_code=rate_code,
        include_global=include_global,
    )


@router.get(
    "/cost-rates",
    response_model=List[CostRateResponse],
    status_code=status.HTTP_200_OK,
)
def list_all_cost_rates(
    project_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    rate_code: Optional[str] = Query(None),
    include_global: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists cost rates across global catalog and optionally a project.
    Allowed roles: contractor, supervisor, admin.
    """
    _ensure_role(current_user, ["contractor", "supervisor", "admin"])
    return list_cost_rates(
        db=db,
        project_id=project_id,
        status_filter=status_filter,
        rate_code=rate_code,
        include_global=include_global,
    )


# ==============================================================================
# COST CALCULATIONS
# ==============================================================================

@router.post(
    "/projects/{project_id}/cost-calculations",
    response_model=CostCalculationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_cost_calculation(
    project_id: str,
    payload: CostCalculationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """
    Executes a deterministic cost calculation: total_cost = quantity * rate.
    Allowed roles: supervisor, admin.
    """
    _ensure_role(current_user, ["supervisor", "admin"])
    return execute_cost_calculation(
        db=db,
        project_id=project_id,
        payload=payload,
        current_user_id=current_user.id,
    )


@router.get(
    "/projects/{project_id}/cost-calculations",
    response_model=List[CostCalculationResponse],
    status_code=status.HTTP_200_OK,
)
def list_project_cost_calculations(
    project_id: str,
    quantity_basis: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """
    Lists cost calculations in a project.
    Allowed roles: contractor, supervisor, admin.
    """
    _ensure_role(current_user, ["contractor", "supervisor", "admin"])
    return list_cost_calculations(
        db=db,
        project_id=project_id,
        quantity_basis=quantity_basis,
        status_filter=status_filter,
    )


# ==============================================================================
# COST SUMMARY & COMPARATIVE VALUATION
# ==============================================================================

@router.get(
    "/projects/{project_id}/cost-summary",
    response_model=ProjectCostSummaryResponse,
    status_code=status.HTTP_200_OK,
)
def get_project_cost_summary_endpoint(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """
    Returns aggregated cost summaries and comparable valuation delta.
    Allowed roles: contractor, supervisor, admin.
    """
    _ensure_role(current_user, ["contractor", "supervisor", "admin"])
    return get_project_cost_summary(db=db, project_id=project_id)
