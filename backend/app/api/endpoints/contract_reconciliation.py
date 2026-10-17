"""Phase 1M: BOQ Quantity-to-Execution Reconciliation & Contract Variation Foundation Endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.api.dependencies import get_current_user, require_project_access
from app.schemas.contract_reconciliation import (
    ContractExecutionItemCreateOriginal,
    ContractExecutionItemSupersedeRequest,
    ContractExecutionItemResponse,
    ActivityContractMappingCreate,
    ActivityContractMappingResponse,
    ContractVariationOrderCreate,
    ContractVariationOrderResponse,
    BoqReconciliationSnapshotResponse,
    BoqReconciliationExecuteResponse,
)
from app.services.contract_reconciliation_service import (
    create_original_contract_item,
    supersede_contract_item,
    list_contract_items,
    get_contract_item,
    create_activity_contract_mapping,
    list_activity_contract_mappings,
    create_variation_order,
    submit_variation_order,
    approve_variation_order,
    reject_variation_order,
    list_variation_orders,
    get_variation_order,
    execute_boq_reconciliation,
    get_certificate_reconciliations,
)

router = APIRouter()


def _ensure_role(user: User, allowed_roles: List[str]):
    if user.role.lower() not in [r.lower() for r in allowed_roles]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation not permitted for role '{user.role}'. Required: {allowed_roles}",
        )


# ==============================================================================
# 1. Contract Execution Item Endpoints
# ==============================================================================

@router.post(
    "/projects/{project_id}/contract-items/original",
    response_model=ContractExecutionItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_original_item_endpoint(
    project_id: str,
    data: ContractExecutionItemCreateOriginal,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["admin", "project_manager"])
    return create_original_contract_item(db, project_id, data, current_user.id)


@router.get(
    "/projects/{project_id}/contract-items",
    response_model=List[ContractExecutionItemResponse],
)
def list_items_endpoint(
    project_id: str,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    return list_contract_items(db, project_id, status_filter)


@router.get(
    "/projects/{project_id}/contract-items/{item_id}",
    response_model=ContractExecutionItemResponse,
)
def get_item_endpoint(
    project_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    return get_contract_item(db, project_id, item_id)


@router.post(
    "/projects/{project_id}/contract-items/{item_id}/supersede",
    response_model=ContractExecutionItemResponse,
)
def supersede_item_endpoint(
    project_id: str,
    item_id: str,
    data: ContractExecutionItemSupersedeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["admin", "project_manager"])
    return supersede_contract_item(db, project_id, item_id, data, current_user.id)


# ==============================================================================
# 2. Activity Contract Mapping Endpoints
# ==============================================================================

@router.post(
    "/projects/{project_id}/activity-contract-mappings",
    response_model=ActivityContractMappingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_mapping_endpoint(
    project_id: str,
    data: ActivityContractMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["admin", "project_manager"])
    return create_activity_contract_mapping(db, project_id, data, current_user.id)


@router.get(
    "/projects/{project_id}/activity-contract-mappings",
    response_model=List[ActivityContractMappingResponse],
)
def list_mappings_endpoint(
    project_id: str,
    activity_id: Optional[str] = None,
    cei_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    return list_activity_contract_mappings(db, project_id, activity_id, cei_id)


# ==============================================================================
# 3. Contract Variation Order Endpoints
# ==============================================================================

@router.post(
    "/projects/{project_id}/variation-orders",
    response_model=ContractVariationOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_variation_endpoint(
    project_id: str,
    data: ContractVariationOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["admin", "project_manager"])
    return create_variation_order(db, project_id, data, current_user.id)


@router.get(
    "/projects/{project_id}/variation-orders",
    response_model=List[ContractVariationOrderResponse],
)
def list_variations_endpoint(
    project_id: str,
    status_filter: Optional[str] = Query(None, alias="status"),
    cei_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    return list_variation_orders(db, project_id, status_filter, cei_id)


@router.get(
    "/projects/{project_id}/variation-orders/{cvo_id}",
    response_model=ContractVariationOrderResponse,
)
def get_variation_endpoint(
    project_id: str,
    cvo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    return get_variation_order(db, project_id, cvo_id)


@router.post(
    "/projects/{project_id}/variation-orders/{cvo_id}/submit",
    response_model=ContractVariationOrderResponse,
)
def submit_variation_endpoint(
    project_id: str,
    cvo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["admin", "project_manager"])
    return submit_variation_order(db, project_id, cvo_id, current_user.id)


@router.post(
    "/projects/{project_id}/variation-orders/{cvo_id}/approve",
    response_model=ContractVariationOrderResponse,
)
def approve_variation_endpoint(
    project_id: str,
    cvo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["admin", "project_manager"])
    return approve_variation_order(db, project_id, cvo_id, current_user.id)


@router.post(
    "/projects/{project_id}/variation-orders/{cvo_id}/reject",
    response_model=ContractVariationOrderResponse,
)
def reject_variation_endpoint(
    project_id: str,
    cvo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["admin", "project_manager"])
    return reject_variation_order(db, project_id, cvo_id, current_user.id)


# ==============================================================================
# 4. BOQ Reconciliation Endpoints
# ==============================================================================

@router.post(
    "/projects/{project_id}/certificates/{certificate_id}/reconcile",
    response_model=BoqReconciliationExecuteResponse,
)
def reconcile_certificate_endpoint(
    project_id: str,
    certificate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    _ensure_role(current_user, ["admin", "project_manager", "site_supervisor"])
    snapshots = execute_boq_reconciliation(db, project_id, certificate_id, current_user.id)
    return BoqReconciliationExecuteResponse(
        certificate_id=certificate_id,
        snapshots_count=len(snapshots),
        snapshots=snapshots,
    )


@router.get(
    "/projects/{project_id}/certificates/{certificate_id}/reconciliations",
    response_model=List[BoqReconciliationSnapshotResponse],
)
def get_reconciliations_endpoint(
    project_id: str,
    certificate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    return get_certificate_reconciliations(db, project_id, certificate_id)
