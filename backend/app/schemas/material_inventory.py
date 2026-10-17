import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


VALID_TRANSACTION_TYPES = {
    "RECEIPT",
    "ISSUE",
    "ADJUSTMENT_IN",
    "ADJUSTMENT_OUT",
    "RETURN",
    "TRANSFER_IN",
    "TRANSFER_OUT",
}

VALID_SOURCE_TYPES = {
    "CONTRACTOR_DECLARED",
    "SUPERVISOR_VERIFIED",
    "SUPERVISOR_CORRECTED",
    "SYSTEM_ADJUSTED",
}

VALID_AVAILABILITY_STATUSES = {
    "AVAILABLE",
    "PARTIALLY_AVAILABLE",
    "SHORTAGE",
    "NO_STOCK_DATA",
    "UNIT_MISMATCH",
    "REQUIRES_INPUT",
}


class MaterialStockLedgerCreate(BaseModel):
    material_item_id: str
    transaction_type: str
    transaction_quantity: Decimal = Field(gt=0)
    unit: str
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    transaction_date: date
    source_type: Optional[str] = None
    source_reference: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

    @field_validator("material_item_id")
    @classmethod
    def validate_material_item_id(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("material_item_id cannot be empty")
        return s

    @field_validator("transaction_type")
    @classmethod
    def validate_transaction_type(cls, v: str) -> str:
        s = v.strip().upper()
        if s not in VALID_TRANSACTION_TYPES:
            raise ValueError(f"transaction_type must be one of {sorted(VALID_TRANSACTION_TYPES)}")
        return s

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v: str) -> str:
        s = v.strip().upper()
        if not s:
            raise ValueError("unit cannot be empty")
        return s

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip().upper()
        if s not in VALID_SOURCE_TYPES:
            raise ValueError(f"source_type must be one of {sorted(VALID_SOURCE_TYPES)}")
        return s


class MaterialStockLedgerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    material_item_id: str
    transaction_type: str
    transaction_quantity: Decimal
    unit: str
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    transaction_date: date
    source_type: str
    source_reference: Optional[str] = None
    is_authoritative: bool
    verification_status: str
    created_by: str
    created_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None


class MaterialStockVerificationRequest(BaseModel):
    verification_action: str
    verified_quantity: Optional[Decimal] = None
    verification_notes: Optional[str] = None

    @field_validator("verification_action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        s = v.strip().upper()
        if s not in ["VERIFIED", "CORRECTED", "REJECTED"]:
            raise ValueError("verification_action must be 'VERIFIED', 'CORRECTED', or 'REJECTED'")
        return s


class MaterialStockBalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    material_item_id: str
    total_received: Decimal
    total_issued: Decimal
    total_adjustment_in: Decimal
    total_adjustment_out: Decimal
    total_returned: Decimal
    total_transfer_in: Decimal
    total_transfer_out: Decimal
    on_hand_quantity: Decimal
    reserved_quantity: Decimal
    available_quantity: Decimal
    unit: str
    calculation_algorithm_version: str
    provenance_metadata: Optional[Dict[str, Any]] = None
    calculated_at: datetime


class MaterialReservationCreate(BaseModel):
    material_item_id: str
    material_requirement_plan_id: str
    material_requirement_item_id: str
    reserved_quantity: Decimal = Field(gt=0)
    unit: str
    reservation_date: date
    metadata_json: Optional[Dict[str, Any]] = None

    @field_validator("material_item_id", "material_requirement_plan_id", "material_requirement_item_id")
    @classmethod
    def validate_non_empty_ids(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("ID fields cannot be empty")
        return s

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v: str) -> str:
        s = v.strip().upper()
        if not s:
            raise ValueError("unit cannot be empty")
        return s


class MaterialReservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    material_item_id: str
    material_requirement_plan_id: str
    material_requirement_item_id: str
    reserved_quantity: Decimal
    unit: str
    status: str
    reservation_date: date
    created_by: str
    created_at: datetime
    released_at: Optional[datetime] = None
    released_by: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class MaterialAvailabilityReconciliationCreate(BaseModel):
    material_requirement_plan_id: str
    metadata_json: Optional[Dict[str, Any]] = None

    @field_validator("material_requirement_plan_id")
    @classmethod
    def validate_plan_id(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("material_requirement_plan_id cannot be empty")
        return s


class MaterialAvailabilityReconciliationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    material_requirement_plan_id: str
    material_requirement_item_id: str
    material_item_id: str
    required_quantity: Decimal
    required_unit: str
    on_hand_quantity: Optional[Decimal] = None
    reserved_quantity: Optional[Decimal] = None
    available_quantity: Optional[Decimal] = None
    shortage_quantity: Optional[Decimal] = None
    availability_status: str
    calculation_algorithm_version: str
    provenance_metadata: Optional[Dict[str, Any]] = None
    calculated_at: datetime
    created_by: str

