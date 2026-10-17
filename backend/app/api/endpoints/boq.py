"""Phase 1J: BOQ Ingestion, Line Item Representation & Deterministic Quantity Reconciliation Endpoints.

Provides REST API routes for:
- Declaring BOQ line items as DRAFT under BOQ documents (contractor, supervisor, admin)
- Confirming BOQ items (supervisor, admin only)
- Listing project BOQ items (contractor, supervisor, admin)
- Proposing 1:1 DIRECT calculation-to-BOQ mappings (contractor, supervisor, admin)
- Verifying or rejecting mappings (supervisor, admin only)
- Executing deterministic quantity reconciliation (supervisor, admin only)
- Listing reconciliations (contractor, supervisor, admin)
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.api.dependencies import require_project_access
from app.schemas.schemas import (
    BoqItemCreate,
    BoqItemResponse,
    BoqMappingCreate,
    BoqMappingVerifyRequest,
    BoqMappingResponse,
    BoqReconciliationCreate,
    BoqReconciliationResponse,
)
from app.services.boq_reconciliation import (
    declare_boq_item,
    confirm_boq_item,
    list_boq_items,
    propose_boq_mapping,
    verify_boq_mapping,
    execute_boq_reconciliation,
    list_boq_reconciliations,
)

router = APIRouter()


def _ensure_role(user: User, allowed_roles: List[str]):
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation not permitted for role '{user.role}'. Required: {allowed_roles}",
        )


@router.post(
    "/projects/{project_id}/documents/{document_id}/boq-items",
    response_model=BoqItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_boq_item_endpoint(
    project_id: str,
    document_id: str,
    payload: BoqItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """
    Declares a new structured BOQ line item in DRAFT status against a verified BOQ document.
    Allowed roles: contractor, supervisor, admin.
    """
    _ensure_role(current_user, ["contractor", "supervisor", "admin"])
    return declare_boq_item(
        db=db,
        project_id=project_id,
        document_id=document_id,
        payload=payload,
        current_user_id=current_user.id,
    )


@router.patch(
    "/projects/{project_id}/boq-items/{boq_item_id}/confirm",
    response_model=BoqItemResponse,
    status_code=status.HTTP_200_OK,
)
def confirm_boq_item_endpoint(
    project_id: str,
    boq_item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """
    Confirms a DRAFT BOQ line item, making its contractual attributes immutable.
    Allowed roles: supervisor, admin only.
    """
    _ensure_role(current_user, ["supervisor", "admin"])
    return confirm_boq_item(
        db=db,
        project_id=project_id,
        boq_item_id=boq_item_id,
        current_user_id=current_user.id,
    )


@router.get(
    "/projects/{project_id}/boq-items",
    response_model=List[BoqItemResponse],
    status_code=status.HTTP_200_OK,
)
def list_boq_items_endpoint(
    project_id: str,
    document_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """
    Lists project BOQ items with optional document and status filtering.
    Allowed roles: contractor, supervisor, admin.
    """
    _ensure_role(current_user, ["contractor", "supervisor", "admin"])
    return list_boq_items(
        db=db,
        project_id=project_id,
        document_id=document_id,
        status=status,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/projects/{project_id}/boq-mappings",
    response_model=BoqMappingResponse,
    status_code=status.HTTP_201_CREATED,
)
def propose_boq_mapping_endpoint(
    project_id: str,
    payload: BoqMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """
    Proposes a 1:1 DIRECT mapping between a CONFIRMED BOQ item and an active engineering calculation.
    Allowed roles: contractor, supervisor, admin.
    """
    _ensure_role(current_user, ["contractor", "supervisor", "admin"])
    return propose_boq_mapping(
        db=db,
        project_id=project_id,
        payload=payload,
        current_user_id=current_user.id,
    )


@router.patch(
    "/projects/{project_id}/boq-mappings/{mapping_id}/verify",
    response_model=BoqMappingResponse,
    status_code=status.HTTP_200_OK,
)
def verify_boq_mapping_endpoint(
    project_id: str,
    mapping_id: str,
    payload: BoqMappingVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """
    Verifies or rejects a proposed mapping.
    Allowed roles: supervisor, admin only.
    """
    _ensure_role(current_user, ["supervisor", "admin"])
    return verify_boq_mapping(
        db=db,
        project_id=project_id,
        mapping_id=mapping_id,
        payload=payload,
        current_user_id=current_user.id,
    )


@router.post(
    "/projects/{project_id}/boq-reconciliations",
    response_model=BoqReconciliationResponse,
    status_code=status.HTTP_201_CREATED,
)
def execute_boq_reconciliation_endpoint(
    project_id: str,
    payload: BoqReconciliationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """
    Executes deterministic quantity reconciliation against a VERIFIED mapping.
    Allowed roles: supervisor, admin only.
    """
    _ensure_role(current_user, ["supervisor", "admin"])
    return execute_boq_reconciliation(
        db=db,
        project_id=project_id,
        payload=payload,
        current_user_id=current_user.id,
    )


@router.get(
    "/projects/{project_id}/boq-reconciliations",
    response_model=List[BoqReconciliationResponse],
    status_code=status.HTTP_200_OK,
)
def list_boq_reconciliations_endpoint(
    project_id: str,
    boq_item_id: Optional[str] = Query(None),
    calculation_id: Optional[str] = Query(None),
    discrepancy_status: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    """
    Lists quantity reconciliations for a project with optional filters.
    Allowed roles: contractor, supervisor, admin.
    """
    _ensure_role(current_user, ["contractor", "supervisor", "admin"])
    return list_boq_reconciliations(
        db=db,
        project_id=project_id,
        boq_item_id=boq_item_id,
        calculation_id=calculation_id,
        discrepancy_status=discrepancy_status,
        status=status,
        skip=skip,
        limit=limit,
    )
