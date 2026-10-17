from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, EngineeringElement, Project
from app.api.dependencies import require_project_access
from app.schemas.schemas import (
    EngineeringElementCreate,
    EngineeringElementResponse,
    EngineeringElementRevise,
    EngineeringElementVerify
)
from app.services.engineering_elements import (
    create_element_record,
    verify_or_revise_element_record,
    build_element_response
)

router = APIRouter()

@router.post("", response_model=EngineeringElementResponse)
def create_engineering_element(
    project_id: str,
    element_in: EngineeringElementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access)
):
    element = create_element_record(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
        element_type=element_in.element_type.value,
        element_name=element_in.element_name,
        source_fact_id=element_in.source_fact_id,
        metadata_json=element_in.metadata_json
    )
    db.commit()
    db.refresh(element)
    return build_element_response(db, element)

@router.get("", response_model=List[EngineeringElementResponse])
def list_engineering_elements(
    project_id: str,
    element_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access)
):
    query = db.query(EngineeringElement).filter(EngineeringElement.project_id == project_id)
    if element_type:
        query = query.filter(EngineeringElement.element_type == element_type)
    
    elements = query.order_by(EngineeringElement.created_at.asc()).all()
    return [build_element_response(db, el) for el in elements]

@router.get("/{element_id}", response_model=EngineeringElementResponse)
def get_engineering_element(
    project_id: str,
    element_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access)
):
    element = db.query(EngineeringElement).filter(
        EngineeringElement.id == element_id,
        EngineeringElement.project_id == project_id
    ).first()
    if not element:
        raise HTTPException(status_code=404, detail="EngineeringElement not found in this project")
    
    return build_element_response(db, element)

@router.post("/{element_id}/revisions", response_model=EngineeringElementResponse)
def revise_engineering_element(
    project_id: str,
    element_id: str,
    revision_in: EngineeringElementRevise,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access)
):
    element = verify_or_revise_element_record(
        db=db,
        project_id=project_id,
        element_id=element_id,
        user=current_user,
        verification_status=revision_in.verification_status.value if revision_in.verification_status else None,
        revision_note=revision_in.revision_note,
        new_name=revision_in.element_name,
        new_type=revision_in.element_type.value if revision_in.element_type else None,
        new_source_fact_id=revision_in.source_fact_id,
        metadata_json=revision_in.metadata_json
    )
    db.commit()
    db.refresh(element)
    return build_element_response(db, element)

@router.post("/{element_id}/verify", response_model=EngineeringElementResponse)
def verify_engineering_element(
    project_id: str,
    element_id: str,
    verify_in: EngineeringElementVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access)
):
    element = verify_or_revise_element_record(
        db=db,
        project_id=project_id,
        element_id=element_id,
        user=current_user,
        verification_status=verify_in.verification_status.value,
        revision_note=verify_in.verification_note,
        new_name=verify_in.corrected_name,
        new_type=verify_in.corrected_type.value if verify_in.corrected_type else None,
        metadata_json=verify_in.metadata_json
    )
    db.commit()
    db.refresh(element)
    return build_element_response(db, element)
