from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, EngineeringCalculation, EngineeringElement
from app.api.dependencies import require_project_access
from app.schemas.schemas import (
    CalculationCreate,
    CalculationResponse
)
from app.services.calculations import (
    execute_element_calculation,
    build_calculation_response
)

router = APIRouter()

@router.post("", response_model=CalculationResponse)
def create_calculation(
    project_id: str,
    element_id: str,
    calc_in: CalculationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access)
):
    calc = execute_element_calculation(
        db=db,
        project_id=project_id,
        element_id=element_id,
        user_id=current_user.id,
        calculation_type=calc_in.calculation_type.value,
        inputs_raw=calc_in.inputs,
        assumptions_raw=calc_in.assumptions
    )
    db.commit()
    db.refresh(calc)
    return build_calculation_response(db, calc)

@router.get("", response_model=List[CalculationResponse])
def list_calculations(
    project_id: str,
    element_id: str,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access)
):
    # Verify element exists in project
    element = db.query(EngineeringElement).filter(
        EngineeringElement.id == element_id,
        EngineeringElement.project_id == project_id
    ).first()
    if not element:
        raise HTTPException(status_code=404, detail="EngineeringElement not found in this project")

    query = db.query(EngineeringCalculation).filter(
        EngineeringCalculation.project_id == project_id,
        EngineeringCalculation.engineering_element_id == element_id
    )
    if status:
        query = query.filter(EngineeringCalculation.status == status)

    calcs = query.order_by(EngineeringCalculation.created_at.desc()).all()
    return [build_calculation_response(db, c) for c in calcs]

@router.get("/{calculation_id}", response_model=CalculationResponse)
def get_calculation(
    project_id: str,
    element_id: str,
    calculation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access)
):
    # Verify element exists in project
    element = db.query(EngineeringElement).filter(
        EngineeringElement.id == element_id,
        EngineeringElement.project_id == project_id
    ).first()
    if not element:
        raise HTTPException(status_code=404, detail="EngineeringElement not found in this project")

    calc = db.query(EngineeringCalculation).filter(
        EngineeringCalculation.id == calculation_id,
        EngineeringCalculation.project_id == project_id,
        EngineeringCalculation.engineering_element_id == element_id
    ).first()
    if not calc:
        raise HTTPException(status_code=404, detail="EngineeringCalculation not found")

    return build_calculation_response(db, calc)
