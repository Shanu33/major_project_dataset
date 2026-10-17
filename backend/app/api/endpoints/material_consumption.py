from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.db.models import User
from app.schemas.material_consumption_reconciliation import (
    MaterialConsumptionCreate,
    MaterialConsumptionReconciliationCreate,
    MaterialConsumptionReconciliationResponse,
    MaterialConsumptionResponse,
    MaterialConsumptionVerificationResponse,
    MaterialConsumptionVerifyRequest,
    MaterialIssueAllocationCreate,
    MaterialIssueAllocationResponse,
)
from app.services.material_consumption_service import (
    create_material_consumption_entry,
    create_material_consumption_reconciliation,
    create_material_issue_allocation,
    get_material_consumption_entry,
    get_material_consumption_reconciliation,
    get_material_issue_allocation,
    list_consumption_verifications,
    list_material_consumption_entries,
    list_material_consumption_reconciliations,
    list_material_issue_allocations,
    verify_material_consumption_entry,
)

router = APIRouter()


# ==============================================================================
# 1. MATERIAL ISSUE ALLOCATIONS
# ==============================================================================

@router.post(
    "/projects/{project_id}/material-issue-allocations",
    response_model=MaterialIssueAllocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Allocate authoritative stock issue to construction activity",
)
def create_issue_allocation_endpoint(
    project_id: str,
    data: MaterialIssueAllocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_material_issue_allocation(db, project_id, data, current_user)


@router.get(
    "/projects/{project_id}/material-issue-allocations",
    response_model=List[MaterialIssueAllocationResponse],
    summary="List material issue allocations for project",
)
def list_issue_allocations_endpoint(
    project_id: str,
    material_item_id: Optional[str] = Query(None),
    activity_id: Optional[str] = Query(None),
    material_stock_ledger_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_material_issue_allocations(
        db,
        project_id,
        current_user,
        material_item_id=material_item_id,
        activity_id=activity_id,
        material_stock_ledger_id=material_stock_ledger_id,
        status_filter=status_filter,
    )


@router.get(
    "/projects/{project_id}/material-issue-allocations/{allocation_id}",
    response_model=MaterialIssueAllocationResponse,
    summary="Get single material issue allocation",
)
def get_issue_allocation_endpoint(
    project_id: str,
    allocation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_material_issue_allocation(db, project_id, allocation_id, current_user)


# ==============================================================================
# 2. CONTRACTOR CONSUMPTION DECLARATIONS
# ==============================================================================

@router.post(
    "/projects/{project_id}/material-consumption",
    response_model=MaterialConsumptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Contractor declaration of actual consumption against activity",
)
def create_consumption_entry_endpoint(
    project_id: str,
    data: MaterialConsumptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_material_consumption_entry(db, project_id, data, current_user)


@router.get(
    "/projects/{project_id}/material-consumption",
    response_model=List[MaterialConsumptionResponse],
    summary="List material consumption declarations for project",
)
def list_consumption_entries_endpoint(
    project_id: str,
    material_item_id: Optional[str] = Query(None),
    activity_id: Optional[str] = Query(None),
    verification_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_material_consumption_entries(
        db,
        project_id,
        current_user,
        material_item_id=material_item_id,
        activity_id=activity_id,
        verification_status=verification_status,
    )


@router.get(
    "/projects/{project_id}/material-consumption/{entry_id}",
    response_model=MaterialConsumptionResponse,
    summary="Get single material consumption declaration",
)
def get_consumption_entry_endpoint(
    project_id: str,
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_material_consumption_entry(db, project_id, entry_id, current_user)


@router.post(
    "/projects/{project_id}/material-consumption/{entry_id}/verify",
    response_model=MaterialConsumptionVerificationResponse,
    summary="Supervisor verification or correction of contractor consumption declaration",
)
def verify_consumption_entry_endpoint(
    project_id: str,
    entry_id: str,
    data: MaterialConsumptionVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return verify_material_consumption_entry(db, project_id, entry_id, data, current_user)


@router.get(
    "/projects/{project_id}/material-consumption/{entry_id}/verifications",
    response_model=List[MaterialConsumptionVerificationResponse],
    summary="List verification audit trail for consumption declaration",
)
def list_consumption_verifications_endpoint(
    project_id: str,
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_consumption_verifications(db, project_id, entry_id, current_user)


# ==============================================================================
# 3. PLANNED VS ACTUAL MATERIAL RECONCILIATIONS
# ==============================================================================

@router.post(
    "/projects/{project_id}/material-consumption-reconciliations",
    response_model=List[MaterialConsumptionReconciliationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Execute planned vs actual material reconciliation snapshot",
)
def create_consumption_reconciliation_endpoint(
    project_id: str,
    data: MaterialConsumptionReconciliationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_material_consumption_reconciliation(db, project_id, data, current_user)


@router.get(
    "/projects/{project_id}/material-consumption-reconciliations",
    response_model=List[MaterialConsumptionReconciliationResponse],
    summary="List material consumption reconciliations for project",
)
def list_consumption_reconciliations_endpoint(
    project_id: str,
    material_requirement_plan_id: Optional[str] = Query(None),
    activity_id: Optional[str] = Query(None),
    material_item_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_material_consumption_reconciliations(
        db,
        project_id,
        current_user,
        material_requirement_plan_id=material_requirement_plan_id,
        activity_id=activity_id,
        material_item_id=material_item_id,
        status_filter=status_filter,
    )


@router.get(
    "/projects/{project_id}/material-consumption-reconciliations/{reconciliation_id}",
    response_model=MaterialConsumptionReconciliationResponse,
    summary="Get single material consumption reconciliation snapshot",
)
def get_consumption_reconciliation_endpoint(
    project_id: str,
    reconciliation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_material_consumption_reconciliation(db, project_id, reconciliation_id, current_user)
