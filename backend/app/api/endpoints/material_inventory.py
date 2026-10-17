from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.api.dependencies import get_current_user
from app.schemas.material_inventory import (
    MaterialStockLedgerCreate,
    MaterialStockLedgerResponse,
    MaterialStockVerificationRequest,
    MaterialStockBalanceResponse,
    MaterialReservationCreate,
    MaterialReservationResponse,
    MaterialAvailabilityReconciliationCreate,
    MaterialAvailabilityReconciliationResponse,
)
from app.services.material_inventory_service import (
    record_stock_transaction,
    verify_contractor_declaration,
    list_stock_transactions,
    list_stock_balances,
    get_stock_balance,
    reconstruct_stock_balances,
    create_material_reservation,
    release_material_reservation,
    list_material_reservations,
    create_availability_reconciliation,
    list_availability_reconciliations,
    get_availability_reconciliation,
)

router = APIRouter()


def _ensure_role(current_user: User, allowed_roles: List[str]) -> None:
    role = current_user.role.lower()
    if role not in [r.lower() for r in allowed_roles]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{current_user.role}' is not authorized for this operation.",
        )


# ------------------------------------------------------------------------------
# Stock Transactions (Ledger)
# ------------------------------------------------------------------------------

@router.post(
    "/projects/{project_id}/material-stock-transactions",
    response_model=MaterialStockLedgerResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_stock_transaction_endpoint(
    project_id: str,
    data: MaterialStockLedgerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    return record_stock_transaction(db, project_id, data, current_user)


@router.post(
    "/projects/{project_id}/material-stock-transactions/{transaction_id}/verify",
    response_model=MaterialStockLedgerResponse,
)
def verify_stock_transaction_endpoint(
    project_id: str,
    transaction_id: str,
    data: MaterialStockVerificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor"])
    return verify_contractor_declaration(db, project_id, transaction_id, data, current_user)


@router.get(
    "/projects/{project_id}/material-stock-transactions",
    response_model=List[MaterialStockLedgerResponse],
)
def list_stock_transactions_endpoint(
    project_id: str,
    material_item_id: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    return list_stock_transactions(db, project_id, material_item_id, transaction_type)


# ------------------------------------------------------------------------------
# Stock Balances
# ------------------------------------------------------------------------------

@router.get(
    "/projects/{project_id}/material-stock-balances",
    response_model=List[MaterialStockBalanceResponse],
)
def list_stock_balances_endpoint(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    return list_stock_balances(db, project_id)


@router.get(
    "/projects/{project_id}/material-stock-balances/{material_item_id}",
    response_model=MaterialStockBalanceResponse,
)
def get_stock_balance_endpoint(
    project_id: str,
    material_item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    return get_stock_balance(db, project_id, material_item_id)


@router.post(
    "/projects/{project_id}/material-stock-balances/reconstruct",
    response_model=List[MaterialStockBalanceResponse],
)
def reconstruct_stock_balances_endpoint(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor"])
    return reconstruct_stock_balances(db, project_id, current_user)


# ------------------------------------------------------------------------------
# Material Reservations
# ------------------------------------------------------------------------------

@router.post(
    "/projects/{project_id}/material-reservations",
    response_model=MaterialReservationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reservation_endpoint(
    project_id: str,
    data: MaterialReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor"])
    return create_material_reservation(db, project_id, data, current_user)


@router.post(
    "/projects/{project_id}/material-reservations/{reservation_id}/release",
    response_model=MaterialReservationResponse,
)
def release_reservation_endpoint(
    project_id: str,
    reservation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor"])
    return release_material_reservation(db, project_id, reservation_id, current_user)


@router.get(
    "/projects/{project_id}/material-reservations",
    response_model=List[MaterialReservationResponse],
)
def list_reservations_endpoint(
    project_id: str,
    plan_id: Optional[str] = Query(None),
    material_item_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    return list_material_reservations(db, project_id, plan_id, material_item_id, status)


# ------------------------------------------------------------------------------
# Material Availability Reconciliations
# ------------------------------------------------------------------------------

@router.post(
    "/projects/{project_id}/material-availability-reconciliations",
    response_model=List[MaterialAvailabilityReconciliationResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_availability_reconciliation_endpoint(
    project_id: str,
    data: MaterialAvailabilityReconciliationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor"])
    return create_availability_reconciliation(db, project_id, data, current_user)


@router.get(
    "/projects/{project_id}/material-availability-reconciliations",
    response_model=List[MaterialAvailabilityReconciliationResponse],
)
def list_availability_reconciliations_endpoint(
    project_id: str,
    plan_id: Optional[str] = Query(None),
    material_item_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    return list_availability_reconciliations(db, project_id, plan_id, material_item_id, status)


@router.get(
    "/projects/{project_id}/material-availability-reconciliations/{reconciliation_id}",
    response_model=MaterialAvailabilityReconciliationResponse,
)
def get_availability_reconciliation_endpoint(
    project_id: str,
    reconciliation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_role(current_user, ["admin", "supervisor", "site_supervisor", "contractor"])
    return get_availability_reconciliation(db, project_id, reconciliation_id)

