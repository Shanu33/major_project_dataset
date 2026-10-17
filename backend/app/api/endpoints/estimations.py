from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, RuleBasedEstimation, Project
from app.api.dependencies import require_project_access
from app.schemas.schemas import (
    EstimationCreate,
    EstimationResponse
)
from app.services.estimations import (
    execute_rule_based_estimation,
    build_estimation_response
)

router = APIRouter()

@router.post("", response_model=EstimationResponse)
def create_rule_based_estimation(
    project_id: str,
    est_in: EstimationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access)
):
    estimation = execute_rule_based_estimation(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
        calculation_id=est_in.calculation_id,
        rule_code=est_in.rule_code,
        rule_version=est_in.rule_version,
        parameters=est_in.parameters,
        metadata_json=est_in.metadata_json
    )
    db.commit()
    db.refresh(estimation)
    return build_estimation_response(db, estimation)

@router.get("", response_model=List[EstimationResponse])
def list_rule_based_estimations(
    project_id: str,
    status: Optional[str] = Query(None),
    engineering_element_id: Optional[str] = Query(None),
    calculation_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access)
):
    query = db.query(RuleBasedEstimation).filter(
        RuleBasedEstimation.project_id == project_id
    )
    if status:
        query = query.filter(RuleBasedEstimation.status == status)
    if engineering_element_id:
        query = query.filter(RuleBasedEstimation.engineering_element_id == engineering_element_id)
    if calculation_id:
        query = query.filter(RuleBasedEstimation.calculation_id == calculation_id)

    estimations = query.order_by(RuleBasedEstimation.created_at.desc()).all()
    return [build_estimation_response(db, e) for e in estimations]

@router.get("/{estimation_id}", response_model=EstimationResponse)
def get_rule_based_estimation(
    project_id: str,
    estimation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access)
):
    estimation = db.query(RuleBasedEstimation).filter(
        RuleBasedEstimation.id == estimation_id,
        RuleBasedEstimation.project_id == project_id
    ).first()
    if not estimation:
        raise HTTPException(status_code=404, detail="RuleBasedEstimation not found")

    return build_estimation_response(db, estimation)

