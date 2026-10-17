from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ResourcePerformanceCreateRequest(BaseModel):
    activity_id: str
    resource_category: str # LABOUR, MATERIAL, EQUIPMENT
    resource_id: Optional[str] = None
    material_item_id: Optional[str] = None
    resource_plan_id: Optional[str] = None
    material_performance_snapshot_id: Optional[str] = None
    cost_rate_id: Optional[str] = None
    rate_mapping_id: Optional[str] = None
    performance_period_start: Optional[date] = None
    performance_period_end: Optional[date] = None
    planned_quantity: Optional[Decimal] = None
    planned_unit: Optional[str] = None
    verified_actual_resource_quantity: Optional[Decimal] = None
    verified_actual_resource_unit: Optional[str] = None
    verified_output_quantity: Optional[Decimal] = None
    verified_output_unit: Optional[str] = None
    tolerance_percentage: Optional[Decimal] = None
    status: Optional[str] = "DRAFT"

    @field_validator("status")
    def validate_status(cls, v: Optional[str]) -> str:
        if v is not None and v != "DRAFT":
            raise ValueError("Snapshots must always be created in DRAFT status. Cannot specify status='FINALIZED'.")
        return "DRAFT"

    @field_validator("resource_category")
    def validate_category(cls, v: str) -> str:
        cat = v.strip().upper()
        if cat not in ["LABOUR", "MATERIAL", "EQUIPMENT"]:
            raise ValueError("resource_category must be one of: LABOUR, MATERIAL, EQUIPMENT")
        return cat

    @field_validator("planned_quantity")
    def validate_non_negative_planned(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < 0:
            raise ValueError("planned_quantity cannot be negative")
        return v

    @field_validator("verified_actual_resource_quantity")
    def validate_non_negative_actual(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < 0:
            raise ValueError("verified_actual_resource_quantity cannot be negative")
        return v

    @field_validator("verified_output_quantity")
    def validate_non_negative_output(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < 0:
            raise ValueError("verified_output_quantity cannot be negative")
        return v

    @field_validator("tolerance_percentage")
    def validate_tolerance(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < 0:
            raise ValueError("tolerance_percentage cannot be negative")
        return v


class ResourcePerformanceSupersedeRequest(BaseModel):
    supersession_reason: str
    replacement_snapshot_id: Optional[str] = None

    @field_validator("supersession_reason")
    def validate_reason(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("supersession_reason cannot be empty")
        return s


class ResourcePerformanceSnapshotResponse(BaseModel):
    id: str
    project_id: str
    activity_id: str
    resource_id: Optional[str] = None
    material_item_id: Optional[str] = None
    resource_category: str
    performance_period_start: Optional[date] = None
    performance_period_end: Optional[date] = None
    resource_plan_id: Optional[str] = None
    material_performance_snapshot_id: Optional[str] = None
    cost_rate_id: Optional[str] = None
    rate_mapping_id: Optional[str] = None
    cost_rate_version: Optional[str] = None
    applied_cost_rate_value: Optional[Decimal] = None
    applied_cost_rate_unit: Optional[str] = None
    planned_quantity: Optional[Decimal] = None
    planned_unit: Optional[str] = None
    actual_resource_quantity: Optional[Decimal] = None
    actual_resource_unit: Optional[str] = None
    verified_output_quantity: Optional[Decimal] = None
    verified_output_unit: Optional[str] = None
    currency: Optional[str] = None
    planned_cost: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    resource_variance: Optional[Decimal] = None
    resource_variance_percentage: Optional[Decimal] = None
    cost_variance: Optional[Decimal] = None
    productivity: Optional[Decimal] = None
    productivity_unit: Optional[str] = None
    resource_intensity: Optional[Decimal] = None
    resource_intensity_unit: Optional[str] = None
    cost_intensity: Optional[Decimal] = None
    cost_intensity_unit: Optional[str] = None
    tolerance_percentage: Optional[Decimal] = None
    performance_status: str
    algorithm_version: str
    input_snapshot_json: Dict[str, Any]
    provenance_metadata: Dict[str, Any]
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


class ResourcePerformanceSummaryResponse(BaseModel):
    project_id: str
    total_snapshots: int
    total_planned_quantities: Dict[str, Decimal]
    total_actual_quantities: Dict[str, Decimal]
    total_resource_variance: Dict[str, Decimal]
    total_variance_percentage: Dict[str, Decimal]
    total_planned_cost: Dict[str, Decimal]
    total_actual_cost: Dict[str, Decimal]
    total_cost_variance: Dict[str, Decimal]
    category_distribution: Dict[str, int]
    status_distribution: Dict[str, int]
    snapshots: List[ResourcePerformanceSnapshotResponse]

    model_config = ConfigDict(from_attributes=True)

