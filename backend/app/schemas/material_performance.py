from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class MaterialPerformanceCreateRequest(BaseModel):
    activity_id: str
    material_item_id: str
    requirement_plan_id: Optional[str] = None
    requirement_item_id: Optional[str] = None
    reconciliation_id: Optional[str] = None
    performance_period_start: Optional[date] = None
    performance_period_end: Optional[date] = None
    verified_activity_execution_quantity: Optional[Decimal] = None
    verified_activity_execution_unit: Optional[str] = None
    tolerance_percentage: Optional[Decimal] = None
    status: Optional[str] = "DRAFT"

    @field_validator("status")
    def validate_status(cls, v: Optional[str]) -> str:
        if v is not None and v != "DRAFT":
            raise ValueError("Snapshots must always be created in DRAFT status. Cannot specify status='FINALIZED'.")
        return "DRAFT"

    @field_validator("verified_activity_execution_quantity")
    def validate_non_negative_execution(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < 0:
            raise ValueError("verified_activity_execution_quantity cannot be negative")
        return v

    @field_validator("tolerance_percentage")
    def validate_tolerance(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < 0:
            raise ValueError("tolerance_percentage cannot be negative")
        return v


class MaterialPerformanceSupersedeRequest(BaseModel):
    supersession_reason: str
    replacement_snapshot_id: Optional[str] = None

    @field_validator("supersession_reason")
    def validate_reason(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("supersession_reason cannot be empty")
        return s


class MaterialPerformanceSnapshotResponse(BaseModel):
    id: str
    project_id: str
    activity_id: str
    material_item_id: str
    reconciliation_id: Optional[str] = None
    requirement_plan_id: Optional[str] = None
    requirement_item_id: Optional[str] = None
    performance_period_start: Optional[date] = None
    performance_period_end: Optional[date] = None
    planned_quantity: Optional[Decimal] = None
    planned_unit: Optional[str] = None
    theoretical_quantity: Optional[Decimal] = None
    theoretical_unit: Optional[str] = None
    issued_quantity: Optional[Decimal] = None
    issued_unit: Optional[str] = None
    actual_consumption_quantity: Optional[Decimal] = None
    actual_consumption_unit: Optional[str] = None
    verified_activity_execution_quantity: Optional[Decimal] = None
    verified_activity_execution_unit: Optional[str] = None
    permissible_wastage_quantity: Optional[Decimal] = None
    unauthorized_wastage_quantity: Optional[Decimal] = None
    planned_variance_quantity: Optional[Decimal] = None
    theoretical_variance_quantity: Optional[Decimal] = None
    planned_variance_percentage: Optional[Decimal] = None
    theoretical_variance_percentage: Optional[Decimal] = None
    consumption_intensity: Optional[Decimal] = None
    productivity: Optional[Decimal] = None
    performance_status: str
    algorithm_version: str
    input_snapshot_json: Dict[str, Any] = Field(default_factory=dict)
    provenance_metadata: Dict[str, Any] = Field(default_factory=dict)
    canonical_hash: str
    status: str
    created_by: str
    created_at: datetime
    finalized_by: Optional[str] = None
    finalized_at: Optional[datetime] = None
    superseded_by: Optional[str] = None
    superseded_by_user_id: Optional[str] = None
    superseded_at: Optional[datetime] = None
    supersession_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MaterialPerformanceSummaryResponse(BaseModel):
    project_id: str
    total_snapshots: int
    total_actual_consumption: Dict[str, Decimal] = Field(default_factory=dict)
    total_theoretical_consumption: Dict[str, Decimal] = Field(default_factory=dict)
    total_planned_consumption: Dict[str, Decimal] = Field(default_factory=dict)
    total_planned_variance: Dict[str, Decimal] = Field(default_factory=dict)
    total_theoretical_variance: Dict[str, Decimal] = Field(default_factory=dict)
    status_distribution: Dict[str, int] = Field(default_factory=dict)
    snapshots: List[MaterialPerformanceSnapshotResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

