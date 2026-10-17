import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class MaterialRequirementPlanCreate(BaseModel):
    baseline_id: str
    plan_version: str
    metadata_json: Optional[Dict[str, Any]] = None

    @field_validator("plan_version")
    @classmethod
    def validate_plan_version(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("plan_version cannot be empty")
        return s

    @field_validator("baseline_id")
    @classmethod
    def validate_baseline_id(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("baseline_id cannot be empty")
        return s


class MaterialRequirementPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    baseline_id: str
    plan_version: str
    status: str
    planning_start_date: Optional[date] = None
    planning_end_date: Optional[date] = None
    algorithm_version: str
    input_snapshot_json: Dict[str, Any]
    created_by: str
    created_at: datetime
    superseded_at: Optional[datetime] = None
    metadata_json: Optional[Dict[str, Any]] = None
    items_count: Optional[int] = None
    procurement_requirements_count: Optional[int] = None


class MaterialRequirementGenerateRequest(BaseModel):
    quantity_source: str = Field(default="GROSS", description="'GROSS' (default, includes waste allowance) or 'NET'")
    target_unit: Optional[str] = None

    @field_validator("quantity_source")
    @classmethod
    def validate_quantity_source(cls, v: str) -> str:
        s = v.strip().upper()
        if s not in ["GROSS", "NET"]:
            raise ValueError("quantity_source must be 'GROSS' or 'NET'")
        return s


class MaterialRequirementItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    material_requirement_plan_id: str
    material_item_id: str
    activity_id: str
    material_plan_id: str
    requirement_quantity: Decimal
    requirement_unit: str
    requirement_date_start: Optional[date] = None
    requirement_date_end: Optional[date] = None
    source_quantity: Decimal
    source_unit: str
    conversion_factor: Decimal
    planning_method: str
    classification: str
    provenance_metadata: Dict[str, Any]
    status: str
    created_at: datetime


class ProcurementInputItem(BaseModel):
    material_item_id: str
    already_planned_quantity: Optional[Decimal] = None

    @field_validator("material_item_id")
    @classmethod
    def validate_material_item_id(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("material_item_id cannot be empty")
        return s

    @field_validator("already_planned_quantity")
    @classmethod
    def validate_already_planned_quantity(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < 0:
            raise ValueError("already_planned_quantity cannot be negative")
        return v


class ProcurementRequirementsGenerateRequest(BaseModel):
    inputs: List[ProcurementInputItem] = Field(default_factory=list)


class ProcurementRequirementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    material_requirement_plan_id: str
    material_item_id: str
    requirement_period_start: Optional[date] = None
    requirement_period_end: Optional[date] = None
    required_quantity: Decimal
    unit: str
    already_planned_quantity: Optional[Decimal] = None
    procurement_quantity: Optional[Decimal] = None
    planning_method: str
    status: str
    provenance_metadata: Dict[str, Any]
    created_at: datetime

