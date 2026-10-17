"""Phase 1N: Material Requirements Planning, Mix Formulation & Theoretical Consumption Reconciliation Endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.api.dependencies import require_project_access
from app.schemas.material_reconciliation import (
    MaterialItemCreate,
    MaterialItemResponse,
    MixDesignCreate,
    MixDesignResponse,
    MaterialPlanResponse,
    ContractorConsumptionSubmit,
    SupervisorConsumptionVerify,
    MaterialConsumptionResponse,
    TheoreticalConsumptionResponse,
    MaterialReconciliationResponse,
)
from app.services.material_reconciliation_service import (
    create_material_item,
    list_material_items,
    create_mix_design,
    approve_mix_design,
    list_mix_designs,
    generate_material_plans,
    list_material_plans,
    submit_material_consumption,
    verify_material_consumption,
    list_material_consumption,
    generate_theoretical_consumption,
    finalize_material_reconciliation,
    list_material_reconciliation,
)

router = APIRouter()


def _ensure_role(user: User, allowed_roles: List[str]):
    norm_allowed = set()
    for r in allowed_roles:
        r_low = r.lower()
        norm_allowed.add(r_low)
        if r_low == "supervisor":
            norm_allowed.add("site_supervisor")
        elif r_low == "site_supervisor":
            norm_allowed.add("supervisor")
    if user.role.lower() not in norm_allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation not permitted for role '{user.role}'. Required: {allowed_roles}",
        )


# ------------------------------------------------------------------------------
# 1. Material Catalog Endpoints
# ------------------------------------------------------------------------------

@router.get(
    "/projects/{project_id}/materials",
    response_model=List[MaterialItemResponse],
)
def list_materials_endpoint(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    return list_material_items(db, project_id)


@router.post(
    "/projects/{project_id}/materials",
    response_model=MaterialItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_material_endpoint(
    project_id: str,
    data: MaterialItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["admin", "supervisor"])
    return create_material_item(db, project_id, data, current_user.id)


# ------------------------------------------------------------------------------
# 2. Mix Design Endpoints
# ------------------------------------------------------------------------------

@router.post(
    "/projects/{project_id}/mix-designs",
    response_model=MixDesignResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_mix_design_endpoint(
    project_id: str,
    data: MixDesignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["admin", "supervisor"])
    return create_mix_design(db, project_id, data, current_user.id)


@router.patch(
    "/projects/{project_id}/mix-designs/{mix_id}/approve",
    response_model=MixDesignResponse,
)
def approve_mix_design_endpoint(
    project_id: str,
    mix_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["admin", "supervisor"])
    return approve_mix_design(db, project_id, mix_id, current_user)


@router.get(
    "/projects/{project_id}/mix-designs",
    response_model=List[MixDesignResponse],
)
def list_mix_designs_endpoint(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    return list_mix_designs(db, project_id)


# ------------------------------------------------------------------------------
# 3. Baseline Material Plans
# ------------------------------------------------------------------------------

@router.post(
    "/projects/{project_id}/baselines/{baseline_id}/material-plans/generate",
    response_model=List[MaterialPlanResponse],
    status_code=status.HTTP_201_CREATED,
)
def generate_material_plans_endpoint(
    project_id: str,
    baseline_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["admin", "supervisor"])
    return generate_material_plans(db, project_id, baseline_id, current_user)


@router.get(
    "/projects/{project_id}/baselines/{baseline_id}/material-plans",
    response_model=List[MaterialPlanResponse],
)
def list_material_plans_endpoint(
    project_id: str,
    baseline_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    return list_material_plans(db, project_id, baseline_id)


# ------------------------------------------------------------------------------
# 4. Actual Material Consumption
# ------------------------------------------------------------------------------

@router.post(
    "/projects/{project_id}/certificates/{certificate_id}/material-consumption/submit",
    response_model=MaterialConsumptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_material_consumption_endpoint(
    project_id: str,
    certificate_id: str,
    data: ContractorConsumptionSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["contractor", "admin"])
    return submit_material_consumption(db, project_id, certificate_id, data, current_user)


@router.patch(
    "/projects/{project_id}/material-consumption/{entry_id}/verify",
    response_model=MaterialConsumptionResponse,
)
def verify_material_consumption_endpoint(
    project_id: str,
    entry_id: str,
    data: SupervisorConsumptionVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["admin", "supervisor"])
    return verify_material_consumption(db, project_id, entry_id, data, current_user)


@router.get(
    "/projects/{project_id}/certificates/{certificate_id}/material-consumption",
    response_model=List[MaterialConsumptionResponse],
)
def list_material_consumption_endpoint(
    project_id: str,
    certificate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    return list_material_consumption(db, project_id, certificate_id)


# ------------------------------------------------------------------------------
# 5. Theoretical Consumption & Finalize Reconciliation
# ------------------------------------------------------------------------------

@router.post(
    "/projects/{project_id}/certificates/{certificate_id}/theoretical-consumption/generate",
    response_model=List[TheoreticalConsumptionResponse],
    status_code=status.HTTP_201_CREATED,
)
def generate_theoretical_consumption_endpoint(
    project_id: str,
    certificate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["admin", "supervisor"])
    return generate_theoretical_consumption(db, project_id, certificate_id, current_user)


@router.post(
    "/projects/{project_id}/certificates/{certificate_id}/material-reconciliation/finalize",
    response_model=List[MaterialReconciliationResponse],
)
def finalize_material_reconciliation_endpoint(
    project_id: str,
    certificate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["admin", "supervisor"])
    return finalize_material_reconciliation(db, project_id, certificate_id, current_user)


@router.get(
    "/projects/{project_id}/certificates/{certificate_id}/material-reconciliation",
    response_model=List[MaterialReconciliationResponse],
)
def list_material_reconciliation_endpoint(
    project_id: str,
    certificate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    return list_material_reconciliation(db, project_id, certificate_id)
