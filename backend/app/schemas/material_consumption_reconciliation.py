from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class MaterialIssueAllocationCreate(BaseModel):
    material_item_id: str
    material_stock_ledger_id: str
    activity_id: str
    material_requirement_plan_id: Optional[str] = None
    material_requirement_item_id: Optional[str] = None
    issued_quantity: Decimal
    issued_unit: str
    issue_date: date
    source_type: Optional[str] = "STORE_ISSUE"
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("issued_quantity")
    def validate_positive_quantity(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("issued_quantity must be strictly positive (> 0)")
        return v

    @field_validator("issued_unit")
    def validate_unit(cls, v: str) -> str:
        s = v.strip().upper()
        if not s:
            raise ValueError("issued_unit cannot be empty")
        return s


class MaterialIssueAllocationResponse(BaseModel):
    id: str
    project_id: str
    material_item_id: str
    material_stock_ledger_id: str
    activity_id: str
    material_requirement_plan_id: Optional[str] = None
    material_requirement_item_id: Optional[str] = None
    issued_quantity: Decimal
    issued_unit: str
    issue_date: date
    source_type: str
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    status: str
    created_by: str
    created_at: datetime
    metadata_json: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class MaterialConsumptionCreate(BaseModel):
    material_item_id: str
    activity_id: str
    contractor_consumed_quantity: Decimal
    contractor_consumed_unit: str
    consumption_date: date
    material_requirement_plan_id: Optional[str] = None
    material_requirement_item_id: Optional[str] = None
    issue_allocation_id: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("contractor_consumed_quantity")
    def validate_non_negative_quantity(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("contractor_consumed_quantity must be non-negative (>= 0)")
        return v

    @field_validator("contractor_consumed_unit")
    def validate_unit(cls, v: str) -> str:
        s = v.strip().upper()
        if not s:
            raise ValueError("contractor_consumed_unit cannot be empty")
        return s


class MaterialConsumptionResponse(BaseModel):
    id: str
    project_id: str
    material_item_id: str
    activity_id: str
    material_requirement_plan_id: Optional[str] = None
    material_requirement_item_id: Optional[str] = None
    issue_allocation_id: Optional[str] = None
    contractor_consumed_quantity: Decimal
    contractor_consumed_unit: str
    consumption_date: date
    declared_by: str
    declared_at: datetime
    verification_status: str
    metadata_json: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class MaterialConsumptionVerifyRequest(BaseModel):
    verification_action: str  # "VERIFIED", "CORRECTED", "REJECTED"
    verified_quantity: Optional[Decimal] = None
    verified_unit: Optional[str] = None
    correction_reason: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("verification_action")
    def validate_action(cls, v: str) -> str:
        s = v.strip().upper()
        if s not in ("VERIFIED", "CORRECTED", "REJECTED"):
            raise ValueError("verification_action must be one of: 'VERIFIED', 'CORRECTED', 'REJECTED'")
        return s

    @field_validator("verified_quantity")
    def validate_verified_quantity(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < 0:
            raise ValueError("verified_quantity must be non-negative (>= 0)")
        return v


class MaterialConsumptionVerificationResponse(BaseModel):
    id: str
    consumption_entry_id: str
    verified_quantity: Decimal
    verified_unit: str
    verification_status: str
    correction_reason: Optional[str] = None
    verified_by: str
    verified_at: datetime
    metadata_json: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class MaterialConsumptionReconciliationCreate(BaseModel):
    material_requirement_plan_id: str
    activity_id: Optional[str] = None
    material_item_id: Optional[str] = None
    permissible_waste_percentage_override: Optional[Decimal] = None
    provenance_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("permissible_waste_percentage_override")
    def validate_permissible_waste(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < 0:
            raise ValueError("permissible_waste_percentage_override cannot be negative")
        return v


class MaterialConsumptionReconciliationResponse(BaseModel):
    id: str
    project_id: str
    material_requirement_plan_id: str
    material_requirement_item_id: Optional[str] = None
    activity_id: Optional[str] = None
    material_item_id: str
    planned_quantity: Optional[Decimal] = None
    planned_unit: Optional[str] = None
    theoretical_quantity: Optional[Decimal] = None
    theoretical_unit: Optional[str] = None
    issued_quantity: Optional[Decimal] = None
    issued_unit: Optional[str] = None
    actual_consumed_quantity: Optional[Decimal] = None
    actual_consumed_unit: Optional[str] = None
    variance_quantity: Optional[Decimal] = None
    variance_percentage: Optional[Decimal] = None
    permissible_wastage_quantity: Optional[Decimal] = None
    unauthorized_wastage_quantity: Optional[Decimal] = None
    status: str
    algorithm_version: str
    input_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    provenance_metadata: Dict[str, Any] = Field(default_factory=dict)
    canonical_hash: str
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True

