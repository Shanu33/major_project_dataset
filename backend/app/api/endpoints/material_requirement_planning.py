from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.api.dependencies import get_current_user
from app.schemas.material_requirement_planning import (
    MaterialRequirementPlanCreate,
    MaterialRequirementPlanResponse,
    MaterialRequirementGenerateRequest,
    MaterialRequirementItemResponse,
    ProcurementRequirementsGenerateRequest,
    ProcurementRequirementResponse,
)
from app.services.material_requirement_planning_service import (
    create_material_requirement_plan,
    list_material_requirement_plans,
    get_material_requirement_plan,
    generate_material_requirement_items,
    list_material_requirement_items,
    generate_procurement_requirements,
    list_procurement_requirements,
    activate_material_requirement_plan,
    supersede_material_requirement_plan,
)

router = APIRouter()


def _ensure_role(current_user: User, allowed_roles: List[str]) -> None:
    role = current_user.role.lower()
    if role not in [r.lower() for r in allowed_roles]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{current_user.role}' is not authorized for this operation.",
        )


@router.post(
    "/projects/{project_id}/material-requirement-plans",
    response_model=MaterialRequirementPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_plan_endpoint(
    project_id: str,
    data: MaterialRequirementPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor"])
    return create_material_requirement_plan(db, project_id, data, current_user)


@router.get(
    "/projects/{project_id}/material-requirement-plans",
    response_model=List[MaterialRequirementPlanResponse],
)
def list_plans_endpoint(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    return list_material_requirement_plans(db, project_id, current_user)


@router.get(
    "/projects/{project_id}/material-requirement-plans/{plan_id}",
    response_model=MaterialRequirementPlanResponse,
)
def get_plan_endpoint(
    project_id: str,
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    return get_material_requirement_plan(db, project_id, plan_id, current_user)


@router.post(
    "/projects/{project_id}/material-requirement-plans/{plan_id}/generate",
    response_model=List[MaterialRequirementItemResponse],
)
def generate_items_endpoint(
    project_id: str,
    plan_id: str,
    data: MaterialRequirementGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor"])
    return generate_material_requirement_items(db, project_id, plan_id, data, current_user)


@router.get(
    "/projects/{project_id}/material-requirement-plans/{plan_id}/items",
    response_model=List[MaterialRequirementItemResponse],
)
def list_items_endpoint(
    project_id: str,
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    return list_material_requirement_items(db, project_id, plan_id, current_user)


@router.post(
    "/projects/{project_id}/material-requirement-plans/{plan_id}/procurement-requirements",
    response_model=List[ProcurementRequirementResponse],
)
def generate_procurement_requirements_endpoint(
    project_id: str,
    plan_id: str,
    data: ProcurementRequirementsGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    return generate_procurement_requirements(db, project_id, plan_id, data, current_user)


@router.get(
    "/projects/{project_id}/material-requirement-plans/{plan_id}/procurement-requirements",
    response_model=List[ProcurementRequirementResponse],
)
def list_procurement_requirements_endpoint(
    project_id: str,
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    return list_procurement_requirements(db, project_id, plan_id, current_user)


@router.post(
    "/projects/{project_id}/material-requirement-plans/{plan_id}/activate",
    response_model=MaterialRequirementPlanResponse,
)
def activate_plan_endpoint(
    project_id: str,
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor"])
    return activate_material_requirement_plan(db, project_id, plan_id, current_user)


@router.post(
    "/projects/{project_id}/material-requirement-plans/{plan_id}/supersede",
    response_model=MaterialRequirementPlanResponse,
)
def supersede_plan_endpoint(
    project_id: str,
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor"])
    return supersede_material_requirement_plan(db, project_id, plan_id, current_user)

