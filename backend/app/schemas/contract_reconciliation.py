"""Phase 1M: BOQ Quantity-to-Execution Reconciliation & Contract Variation Foundation Schemas."""
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


# ==============================================================================
# 1. Contract Execution Item Schemas
# ==============================================================================

class ContractExecutionItemCreateOriginal(BaseModel):
    boq_item_id: str
    original_contract_rate: Decimal = Field(..., gt=0)
    effective_date: date
    currency: str = "INR"
    item_code: Optional[str] = None
    description: Optional[str] = None
    unit_of_measure: Optional[str] = None


class ContractExecutionItemSupersedeRequest(BaseModel):
    item_code: str
    description: str


class ContractExecutionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    boq_item_id: Optional[str] = None
    originating_cvo_id: Optional[str] = None
    item_origin: str
    item_code: str
    description: str
    unit_of_measure: str
    original_contract_quantity: Decimal
    effective_contract_quantity: Decimal
    original_contract_rate: Decimal
    current_contract_rate: Decimal
    currency: str
    effective_date: date
    superseded_at: Optional[datetime] = None
    superseding_item_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


# ==============================================================================
# 2. Activity Contract Mapping Schemas
# ==============================================================================

class ActivityContractMappingCreate(BaseModel):
    activity_id: str
    contract_execution_item_id: str
    allocation_percentage: Decimal = Field(default=Decimal("100.00"), gt=0, le=100)
    effective_from: date
    effective_to: Optional[date] = None


class ActivityContractMappingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    activity_id: str
    contract_execution_item_id: str
    allocation_percentage: Decimal
    effective_from: date
    effective_to: Optional[date] = None
    created_at: datetime
    updated_at: datetime


# ==============================================================================
# 3. Contract Variation Order Schemas
# ==============================================================================

class ContractVariationOrderCreate(BaseModel):
    variation_number: str
    variation_type: str
    unit_of_measure: str
    contract_execution_item_id: Optional[str] = None
    quantity_delta: Decimal = Decimal("0.0000")
    rate_previous: Decimal = Field(..., gt=0)
    rate_revised: Decimal = Field(..., gt=0)
    effective_date: date
    description: str


class ContractVariationOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    contract_execution_item_id: Optional[str] = None
    variation_number: str
    variation_type: str
    unit_of_measure: str
    quantity_delta: Decimal
    rate_previous: Decimal
    rate_revised: Decimal
    net_variation_amount: Optional[Decimal] = None
    effective_date: date
    approved_at: Optional[datetime] = None
    approved_by_user_id: Optional[str] = None
    status: str
    description: str
    created_at: datetime
    updated_at: datetime


# ==============================================================================
# 4. BOQ Reconciliation Snapshot Schemas
# ==============================================================================

class BoqReconciliationSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    certificate_id: str
    contract_execution_item_id: str
    effective_contract_quantity: Decimal
    cumulative_executed_quantity: Decimal
    cumulative_executed_quantity_boq_unit: Decimal
    gross_over_execution_quantity: Decimal
    critical_deviation_quantity: Decimal
    reconciliation_rate: Decimal
    historical_period_valuation: Decimal
    current_rate_valuation: Decimal
    valuation_delta: Decimal
    is_critical_deviation: bool
    snapshot_hash: str
    verified_at: datetime
    created_at: datetime


class BoqReconciliationExecuteResponse(BaseModel):
    certificate_id: str
    snapshots_count: int
    snapshots: List[BoqReconciliationSnapshotResponse]
