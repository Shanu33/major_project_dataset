from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, Resource, CalculationResourceMapping
from app.api.dependencies import get_current_user
from app.schemas.schemas import (
    ResourceCreate,
    ResourceResponse,
    ResourceCategoryEnum,
    ResourceStatusEnum,
    CalculationResourceMappingCreate,
    CalculationResourceMappingResponse
)
from app.services.resource_planning import (
    create_resource,
    seed_default_resources,
    seed_default_mappings,
    create_calculation_resource_mapping
)

router = APIRouter()

@router.post("", response_model=ResourceResponse)
def create_new_resource(
    res_in: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resource = create_resource(db, res_in, current_user.id)
    db.commit()
    db.refresh(resource)
    return resource

@router.get("", response_model=List[ResourceResponse])
def list_resources(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    seed_default_resources(db, current_user.id)
    query = db.query(Resource)
    if category:
        query = query.filter(Resource.resource_category == category)
    if status:
        query = query.filter(Resource.status == status)
    return query.order_by(Resource.resource_code.asc()).all()

@router.get("/mappings", response_model=List[CalculationResourceMappingResponse])
def list_mappings(
    calculation_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    seed_default_mappings(db, current_user.id)
    query = db.query(CalculationResourceMapping)
    if calculation_type:
        query = query.filter(CalculationResourceMapping.calculation_type == calculation_type)
    if status:
        query = query.filter(CalculationResourceMapping.status == status)
    mappings = query.order_by(CalculationResourceMapping.created_at.desc()).all()
    out = []
    for m in mappings:
        res = CalculationResourceMappingResponse(
            id=m.id,
            calculation_type=m.calculation_type,
            calculation_version=m.calculation_version,
            resource_id=m.resource_id,
            resource_code=m.resource.resource_code if m.resource else None,
            source_unit=m.source_unit,
            resource_unit=m.resource_unit,
            mapping_method=m.mapping_method,
            status=m.status,
            created_by=m.created_by,
            created_at=m.created_at,
            metadata_json=m.metadata_json
        )
        out.append(res)
    return out

@router.post("/mappings", response_model=CalculationResourceMappingResponse)
def create_new_mapping(
    mapping_in: CalculationResourceMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    mapping = create_calculation_resource_mapping(db, mapping_in, current_user.id)
    db.commit()
    db.refresh(mapping)
    return CalculationResourceMappingResponse(
        id=mapping.id,
        calculation_type=mapping.calculation_type,
        calculation_version=mapping.calculation_version,
        resource_id=mapping.resource_id,
        resource_code=mapping.resource.resource_code if mapping.resource else None,
        source_unit=mapping.source_unit,
        resource_unit=mapping.resource_unit,
        mapping_method=mapping.mapping_method,
        status=mapping.status,
        created_by=mapping.created_by,
        created_at=mapping.created_at,
        metadata_json=mapping.metadata_json
    )

@router.get("/{resource_id}", response_model=ResourceResponse)
def get_resource_by_id(
    resource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    seed_default_resources(db, current_user.id)
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource
