from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, ResourcePlan
from app.api.dependencies import require_project_access
from app.schemas.schemas import ResourcePlanCreate, ResourcePlanResponse
from app.services.resource_planning import (
    create_resource_plan,
    build_resource_plan_response
)

router = APIRouter()

@router.post("", response_model=ResourcePlanResponse)
def create_project_resource_plan(
    project_id: str,
    plan_in: ResourcePlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access)
):
    plan = create_resource_plan(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
        resource_id=plan_in.resource_id,
        resource_code=plan_in.resource_code,
        calculation_id=plan_in.calculation_id,
        estimation_id=plan_in.estimation_id,
        engineering_element_id=plan_in.engineering_element_id,
        metadata_json=plan_in.metadata_json
    )
    db.commit()
    db.refresh(plan)
    return build_resource_plan_response(db, plan)

@router.get("", response_model=List[ResourcePlanResponse])
def list_project_resource_plans(
    project_id: str,
    status: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    engineering_element_id: Optional[str] = Query(None),
    estimation_id: Optional[str] = Query(None),
    calculation_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access)
):
    query = db.query(ResourcePlan).filter(ResourcePlan.project_id == project_id)
    if status:
        query = query.filter(ResourcePlan.status == status)
    if resource_id:
        query = query.filter(ResourcePlan.resource_id == resource_id)
    if engineering_element_id:
        query = query.filter(ResourcePlan.engineering_element_id == engineering_element_id)
    if estimation_id:
        query = query.filter(ResourcePlan.estimation_id == estimation_id)
    if calculation_id:
        query = query.filter(ResourcePlan.calculation_id == calculation_id)

    plans = query.order_by(ResourcePlan.created_at.desc()).all()
    return [build_resource_plan_response(db, p) for p in plans]

@router.get("/{resource_plan_id}", response_model=ResourcePlanResponse)
def get_project_resource_plan(
    project_id: str,
    resource_plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access)
):
    plan = db.query(ResourcePlan).filter(
        ResourcePlan.id == resource_plan_id,
        ResourcePlan.project_id == project_id
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="ResourcePlan not found")
    return build_resource_plan_response(db, plan)

