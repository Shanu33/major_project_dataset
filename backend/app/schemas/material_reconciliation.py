from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal


CANONICAL_MATERIAL_CATEGORIES = {
    "BINDER",
    "AGGREGATE",
    "REINFORCEMENT",
    "MASONRY",
    "CHEMICAL",
    "WATER",
    "TIMBER",
    "STEEL_SECTION",
}

CANONICAL_STANDARD_UNITS = {
    "BAG",
    "KG",
    "MT",
    "M3",
    "LITRE",
    "NOS",
    "SQM",
}


# ------------------------------------------------------------------------------
# Material Item Schemas
# ------------------------------------------------------------------------------

class MaterialItemCreate(BaseModel):
    material_code: str = Field(..., max_length=50)
    material_name: str = Field(..., max_length=100)
    material_category: str = Field(..., max_length=50) # BINDER, AGGREGATE, REINFORCEMENT, MASONRY, CHEMICAL, WATER, TIMBER, STEEL_SECTION
    standard_unit: str = Field(..., max_length=20)     # BAG, KG, MT, M3, LITRE, NOS, SQM
    density_kg_per_unit: Optional[Decimal] = None
    standard_permissible_waste_pct: Decimal = Decimal("0.00")

    @field_validator("material_category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in CANONICAL_MATERIAL_CATEGORIES:
            raise ValueError(f"Invalid material category '{v}'. Allowed: {sorted(list(CANONICAL_MATERIAL_CATEGORIES))}")
        return v

    @field_validator("standard_unit")
    @classmethod
    def validate_unit(cls, v: str) -> str:
        if v not in CANONICAL_STANDARD_UNITS:
            raise ValueError(f"Invalid standard unit '{v}'. Allowed: {sorted(list(CANONICAL_STANDARD_UNITS))}")
        return v


class MaterialItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: Optional[str]
    material_code: str
    material_name: str
    material_category: str
    standard_unit: str
    density_kg_per_unit: Optional[Decimal]
    standard_permissible_waste_pct: Decimal
    is_active: bool
    created_at: datetime


# ------------------------------------------------------------------------------
# Mix Design & Constituent Schemas
# ------------------------------------------------------------------------------

class MixConstituentCreate(BaseModel):
    material_item_id: str
    quantity_per_m3: Decimal
    unit: str


class MixConstituentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    mix_design_id: str
    material_item_id: str
    quantity_per_m3: Decimal
    unit: str


class MixDesignCreate(BaseModel):
    mix_code: str = Field(..., max_length=50)
    grade_designation: str = Field(..., max_length=50)
    mix_type: str = Field(..., max_length=30) # DESIGN_MIX, NOMINAL_MIX
    rule_code: Optional[str] = None
    source_document_id: Optional[str] = None
    evidence_id: Optional[str] = None
    dry_volume_factor: Decimal = Decimal("1.5400")
    water_cement_ratio: Optional[Decimal] = None
    constituents: List[MixConstituentCreate] = Field(default_factory=list)


class MixDesignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    mix_code: str
    grade_designation: str
    mix_type: str
    rule_code: Optional[str]
    source_document_id: Optional[str]
    evidence_id: Optional[str]
    dry_volume_factor: Decimal
    water_cement_ratio: Optional[Decimal]
    classification: str
    status: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime
    constituents: List[MixConstituentResponse] = Field(default_factory=list)


# ------------------------------------------------------------------------------
# Material Plan Schemas
# ------------------------------------------------------------------------------

class MaterialPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    baseline_id: str
    material_item_id: str
    activity_id: str
    mix_design_id: str
    planned_quantity: Decimal
    unit: str
    estimation_method: str
    waste_allowance_pct: Decimal
    gross_planned_quantity: Decimal
    provenance_metadata: Dict[str, Any]
    status: str
    created_at: datetime


# ------------------------------------------------------------------------------
# Actual Consumption Schemas
# ------------------------------------------------------------------------------

class ContractorConsumptionSubmit(BaseModel):
    material_item_id: str
    store_challan_reference: str = Field(..., max_length=100)
    consumption_date_start: date
    consumption_date_end: date
    contractor_declared_quantity: Decimal
    unit: str = Field(..., max_length=20)
    supporting_document_id: Optional[str] = None


class SupervisorConsumptionVerify(BaseModel):
    supervisor_verified_quantity: Decimal
    is_rejected: bool = False


class MaterialConsumptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    certificate_id: str
    material_item_id: str
    store_challan_reference: str
    consumption_date_start: date
    consumption_date_end: date
    contractor_declared_quantity: Decimal
    supervisor_verified_quantity: Optional[Decimal]
    discrepancy_quantity: Decimal
    is_disputed: bool
    unit: str
    submission_status: str
    supporting_document_id: Optional[str]
    submitted_by: str
    verified_by: Optional[str]
    verified_at: Optional[datetime]
    created_at: datetime


# ------------------------------------------------------------------------------
# Theoretical Consumption Schemas
# ------------------------------------------------------------------------------

class TheoreticalConsumptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    certificate_id: str
    certificate_item_id: str
    activity_id: str
    material_item_id: str
    mix_design_id: str
    certified_activity_volume: Decimal
    coefficient_per_unit: Decimal
    dry_volume_factor: Decimal
    theoretical_quantity: Decimal
    unit: str
    mix_design_version: str
    calculation_algorithm_version: str
    created_at: datetime


# ------------------------------------------------------------------------------
# Material Reconciliation Report Schemas
# ------------------------------------------------------------------------------

class MaterialReconciliationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    certificate_id: str
    material_item_id: str
    revision_number: int
    status: str
    cumulative_theoretical_quantity: Decimal
    cumulative_actual_quantity: Decimal
    variance_quantity: Decimal
    variance_percentage: Decimal
    is_saving: bool
    permissible_waste_percentage: Decimal
    permissible_waste_quantity: Decimal
    unauthorized_wastage_quantity: Decimal
    is_excess_flagged: bool
    reconciliation_hash: str
    finalized_by: Optional[str]
    finalized_at: Optional[datetime]
    supersedes_report_id: Optional[str]
    created_at: datetime

