from pydantic import BaseModel, EmailStr, Field, ConfigDict
from decimal import Decimal
from typing import Optional, Any, Dict, List, Union
from datetime import datetime, date
from enum import Enum

# ==============================================================================
# PHASE 0 & 1A: USERS, PROJECTS, BASELINES, REPORTS & DOCUMENTS
# ==============================================================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserCreateAdmin(BaseModel):
    email: EmailStr
    password: str
    role: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    role: str

class ProjectCreate(BaseModel):
    name: str

class BaselineFreeze(BaseModel):
    reason_for_revision: str = "Initial Baseline"

class DailyReportSubmit(BaseModel):
    contractor_declared_work: Dict[str, Any]

class VerificationSubmit(BaseModel):
    supervisor_verified_work: Dict[str, Any]
    status: str

class DocumentTypeEnum(str, Enum):
    ARCHITECTURAL_DRAWING = "ARCHITECTURAL_DRAWING"
    STRUCTURAL_DRAWING = "STRUCTURAL_DRAWING"
    BOQ = "BOQ"
    SPECIFICATION = "SPECIFICATION"
    GEOTECHNICAL = "GEOTECHNICAL"
    TENDER_PROJECT_INFO = "TENDER_PROJECT_INFO"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"

class ProcessingStatusEnum(str, Enum):
    UPLOADED = "UPLOADED"
    VALIDATED = "VALIDATED"
    CLASSIFIED = "CLASSIFIED"
    READY_FOR_EXTRACTION = "READY_FOR_EXTRACTION"
    PROCESSING_FAILED = "PROCESSING_FAILED"

class ClassificationMethodEnum(str, Enum):
    RULE_BASED = "RULE_BASED"
    MANUAL = "MANUAL"

class DocumentResponse(BaseModel):
    id: str
    project_id: str
    original_filename: str
    document_type: DocumentTypeEnum
    mime_type: str
    file_size_bytes: int
    sha256_hash: str
    uploaded_by: str
    uploaded_at: datetime
    processing_status: ProcessingStatusEnum
    classified_document_type: Optional[DocumentTypeEnum] = None
    classification_score: Optional[float] = Field(None, description="Explicit heuristic rule-match score (0.0 - 1.0). NOT a statistical ML confidence or probability.")
    classification_method: Optional[str] = None
    classified_at: Optional[datetime] = None

class DocumentPageResponse(BaseModel):
    id: str
    document_id: str
    page_number: int
    page_count: int
    page_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

class DocumentProcessingHistoryResponse(BaseModel):
    id: str
    document_id: str
    processing_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    processor_version: str
    metadata_json: Optional[Dict[str, Any]] = None

class DocumentStatusResponse(BaseModel):
    id: str
    project_id: str
    original_filename: str
    document_type: DocumentTypeEnum
    classified_document_type: Optional[DocumentTypeEnum] = None
    classification_score: Optional[float] = Field(None, description="Explicit heuristic rule-match score (0.0 - 1.0). NOT a statistical ML confidence or probability.")
    classification_method: Optional[str] = None
    classified_at: Optional[datetime] = None
    processing_status: ProcessingStatusEnum
    total_pages: Optional[int] = None

# ==============================================================================
# PHASE 1C: EVIDENCE & PROVENANCE SCHEMAS
# ==============================================================================

class EvidenceTypeEnum(str, Enum):
    TEXT = "TEXT"
    TABLE = "TABLE"
    DRAWING_REGION = "DRAWING_REGION"
    DIMENSION = "DIMENSION"
    BOQ_ITEM = "BOQ_ITEM"
    MANUAL_ENTRY = "MANUAL_ENTRY"

class ExtractionMethodEnum(str, Enum):
    MANUAL = "MANUAL"
    RULE_BASED = "RULE_BASED"

class ExtractionStatusEnum(str, Enum):
    CANDIDATE = "CANDIDATE"
    EXTRACTED = "EXTRACTED"
    REJECTED = "REJECTED"
    VERIFIED = "VERIFIED"

class VerificationStatusEnum(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

class EvidenceCreate(BaseModel):
    page_id: Optional[str] = None
    evidence_type: EvidenceTypeEnum
    source_reference: str
    locator: Optional[Any] = None
    raw_content: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    page_id: Optional[str] = None
    evidence_type: EvidenceTypeEnum
    source_reference: str
    locator: Optional[Any] = None
    raw_content: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    created_by: str
    verification_status: VerificationStatusEnum

class FactCreate(BaseModel):
    fact_type: str
    field_name: str
    raw_value: str
    normalized_value: Optional[Decimal] = None
    normalized_unit: Optional[str] = None
    extraction_method: ExtractionMethodEnum = ExtractionMethodEnum.MANUAL
    metadata_json: Optional[Dict[str, Any]] = None

class FactVerify(BaseModel):
    status: VerificationStatusEnum
    verification_note: Optional[str] = None
    corrected_value: Optional[Decimal] = None
    corrected_unit: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

class FactVerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    fact_id: str
    verified_by: str
    status: VerificationStatusEnum
    verification_note: Optional[str] = None
    corrected_value: Optional[Decimal] = None
    corrected_unit: Optional[str] = None
    verified_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None

class FactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    evidence_id: str
    fact_type: str
    field_name: str
    raw_value: str
    normalized_value: Optional[Decimal] = None
    normalized_unit: Optional[str] = None
    extraction_method: ExtractionMethodEnum
    extraction_version: str
    extraction_status: ExtractionStatusEnum
    created_at: datetime
    created_by: str
    verification_status: VerificationStatusEnum
    metadata_json: Optional[Dict[str, Any]] = None
    verifications: list[FactVerificationResponse] = []

class FactProvenanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fact_id: str
    fact_type: str
    field_name: str
    raw_value: str
    normalized_value: Optional[Decimal] = None
    normalized_unit: Optional[str] = None
    extraction_method: str
    extraction_version: str
    extraction_status: str
    verification_status: str
    evidence_id: str
    evidence_type: str
    source_reference: str
    locator: Optional[Any] = None
    raw_content: Optional[str] = None
    page_id: Optional[str] = None
    page_number: Optional[int] = None
    document_id: str
    original_filename: str
    project_id: str
    project_name: str
    verifications: list[FactVerificationResponse] = []

# ==============================================================================
# PHASE 1D: ENGINEERING ELEMENT FOUNDATION SCHEMAS
# ==============================================================================

class EngineeringElementTypeEnum(str, Enum):
    FOOTING = "FOOTING"
    PILE = "PILE"
    PILE_CAP = "PILE_CAP"
    COLUMN = "COLUMN"
    BEAM = "BEAM"
    SLAB = "SLAB"
    WALL = "WALL"
    PAVEMENT = "PAVEMENT"
    KERB = "KERB"
    FOUNDATION = "FOUNDATION"
    OTHER = "OTHER"

class ElementVerificationStatusEnum(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    CORRECTED = "CORRECTED"

class EngineeringElementCreate(BaseModel):
    element_type: EngineeringElementTypeEnum
    element_name: str
    source_fact_id: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

class EngineeringElementRevisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    element_id: str
    revision_number: int
    element_type: EngineeringElementTypeEnum
    element_name: str
    source_document_id: Optional[str] = None
    source_page_id: Optional[str] = None
    source_fact_id: Optional[str] = None
    verification_status: ElementVerificationStatusEnum
    revision_note: Optional[str] = None
    created_by: str
    created_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None

class ElementProvenanceChainResponse(BaseModel):
    provenance_type: str # "DOCUMENT_DERIVED" or "MANUALLY_SUPPLIED"
    fact_id: Optional[str] = None
    fact_type: Optional[str] = None
    field_name: Optional[str] = None
    raw_value: Optional[str] = None
    normalized_value: Optional[Decimal] = None
    normalized_unit: Optional[str] = None
    fact_verification_status: Optional[str] = None
    evidence_id: Optional[str] = None
    evidence_type: Optional[str] = None
    source_reference: Optional[str] = None
    locator: Optional[Any] = None
    page_id: Optional[str] = None
    page_number: Optional[int] = None
    document_id: Optional[str] = None
    original_filename: Optional[str] = None
    project_id: str
    project_name: str

class EngineeringElementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    element_type: EngineeringElementTypeEnum
    element_name: str
    source_document_id: Optional[str] = None
    source_page_id: Optional[str] = None
    source_fact_id: Optional[str] = None
    status: str
    verification_status: ElementVerificationStatusEnum
    created_by: str
    created_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None
    revisions: list[EngineeringElementRevisionResponse] = []
    provenance: Optional[ElementProvenanceChainResponse] = None

class EngineeringElementRevise(BaseModel):
    element_type: Optional[EngineeringElementTypeEnum] = None
    element_name: Optional[str] = None
    source_fact_id: Optional[str] = None
    verification_status: Optional[ElementVerificationStatusEnum] = None
    revision_note: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

class EngineeringElementVerify(BaseModel):
    verification_status: ElementVerificationStatusEnum
    verification_note: Optional[str] = None
    corrected_name: Optional[str] = None
    corrected_type: Optional[EngineeringElementTypeEnum] = None
    metadata_json: Optional[Dict[str, Any]] = None

# ==============================================================================
# PHASE 1E: DETERMINISTIC ENGINEERING CALCULATION SCHEMAS
# ==============================================================================

class CalculationTypeEnum(str, Enum):
    CONCRETE_VOLUME_RECTANGULAR = "CONCRETE_VOLUME_RECTANGULAR"

class CalculationStatusEnum(str, Enum):
    CALCULATED = "CALCULATED"
    INVALID_INPUT = "INVALID_INPUT"
    REQUIRES_INPUT = "REQUIRES_INPUT"
    SUPERSEDED = "SUPERSEDED"

class CalculationInputItem(BaseModel):
    value: Optional[Decimal] = None
    unit: Optional[str] = "m"
    source_fact_id: Optional[str] = None
    source_type: Optional[str] = "VERIFIED_FACT"

class CalculationCreate(BaseModel):
    calculation_type: CalculationTypeEnum
    inputs: Dict[str, Any]
    assumptions: Optional[Dict[str, Any]] = None

class CalculationProvenanceItem(BaseModel):
    dimension_name: str
    value: Optional[Decimal] = None
    unit: Optional[str] = None
    fact_id: Optional[str] = None
    raw_value: Optional[str] = None
    fact_verification_status: Optional[str] = None
    evidence_id: Optional[str] = None
    evidence_type: Optional[str] = None
    source_reference: Optional[str] = None
    locator: Optional[Any] = None
    page_id: Optional[str] = None
    page_number: Optional[int] = None
    document_id: Optional[str] = None
    original_filename: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None

class CalculationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    engineering_element_id: str
    calculation_type: CalculationTypeEnum
    calculation_version: str
    status: CalculationStatusEnum
    result_value: Optional[Decimal] = None
    result_unit: Optional[str] = None
    formula_identifier: str
    formula_expression: str
    inputs_json: Dict[str, Any]
    assumptions_json: Optional[Dict[str, Any]] = None
    created_by: str
    created_at: datetime
    element_name: Optional[str] = None
    element_type: Optional[str] = None
    provenance_details: Optional[List[CalculationProvenanceItem]] = None

# ==============================================================================
# PHASE 1F: RULE-BASED ESTIMATION FOUNDATION SCHEMAS
# ==============================================================================

class RuleStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEPRECATED = "DEPRECATED"

class EstimationTypeEnum(str, Enum):
    LABOUR_HOURS = "LABOUR_HOURS"

class EstimationStatusEnum(str, Enum):
    ESTIMATED = "ESTIMATED"
    INVALID_INPUT = "INVALID_INPUT"
    REQUIRES_INPUT = "REQUIRES_INPUT"
    SUPERSEDED = "SUPERSEDED"

class RuleCreate(BaseModel):
    rule_code: str
    rule_name: str
    description: Optional[str] = None
    rule_category: str
    input_unit: str
    output_unit: str
    formula_identifier: str
    formula_expression: str
    parameters_json: Dict[str, Any]
    source_reference: Optional[str] = None
    version: str = "1.0"
    status: RuleStatusEnum = RuleStatusEnum.ACTIVE
    metadata_json: Optional[Dict[str, Any]] = None

class RuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    rule_code: str
    rule_name: str
    description: Optional[str] = None
    rule_category: str
    input_unit: str
    output_unit: str
    formula_identifier: str
    formula_expression: str
    parameters_json: Dict[str, Any]
    source_reference: Optional[str] = None
    version: str
    status: RuleStatusEnum
    created_by: str
    created_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None

class EstimationCreate(BaseModel):
    calculation_id: str
    rule_code: str
    rule_version: str = "1.0"
    parameters: Dict[str, Any]
    metadata_json: Optional[Dict[str, Any]] = None

class EstimationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    engineering_element_id: str
    calculation_id: str
    rule_id: str
    rule_code: str
    rule_version: str
    estimation_type: str
    status: str
    input_value: Decimal
    input_unit: str
    result_value: Decimal
    result_unit: str
    parameters_json: Dict[str, Any]
    assumptions_json: Dict[str, Any]
    provenance_json: Dict[str, Any]
    estimation_method: str = "RULE_BASED"
    confidence_classification: str = "ASSUMPTION_BASED"
    created_by: str
    created_at: datetime
    element_name: Optional[str] = None
    element_type: Optional[str] = None
    provenance_chain: Optional[Dict[str, Any]] = None

# ==============================================================================
# PHASE 1G: RESOURCE PLANNING FOUNDATION SCHEMAS
# ==============================================================================

class ResourceCategoryEnum(str, Enum):
    LABOUR = "LABOUR"
    MATERIAL = "MATERIAL"
    EQUIPMENT = "EQUIPMENT"

class ResourceStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEPRECATED = "DEPRECATED"

class MappingStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEPRECATED = "DEPRECATED"

class PlanningMethodEnum(str, Enum):
    DETERMINISTIC = "DETERMINISTIC"
    RULE_BASED = "RULE_BASED"
    USER_PROVIDED = "USER_PROVIDED"

class PlanClassificationEnum(str, Enum):
    CALCULATED = "CALCULATED"
    DERIVED = "DERIVED"
    ASSUMPTION_BASED = "ASSUMPTION_BASED"
    USER_PROVIDED = "USER_PROVIDED"

class PlanStatusEnum(str, Enum):
    PLANNED = "PLANNED"
    SUPERSEDED = "SUPERSEDED"

class ResourceCreate(BaseModel):
    resource_code: str
    resource_name: str
    resource_category: ResourceCategoryEnum
    unit: str
    description: Optional[str] = None
    status: ResourceStatusEnum = ResourceStatusEnum.ACTIVE
    metadata_json: Optional[Dict[str, Any]] = None

class ResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resource_code: str
    resource_name: str
    resource_category: ResourceCategoryEnum
    unit: str
    description: Optional[str] = None
    status: ResourceStatusEnum
    created_by: Optional[str] = None
    created_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None

class CalculationResourceMappingCreate(BaseModel):
    calculation_type: str
    calculation_version: str = "1.0"
    resource_id: str
    source_unit: str
    resource_unit: str
    mapping_method: str = "DIRECT"
    status: MappingStatusEnum = MappingStatusEnum.ACTIVE
    metadata_json: Optional[Dict[str, Any]] = None

class CalculationResourceMappingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    calculation_type: str
    calculation_version: str
    resource_id: str
    resource_code: Optional[str] = None
    source_unit: str
    resource_unit: str
    mapping_method: str
    status: str
    created_by: Optional[str] = None
    created_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None

class ResourcePlanCreate(BaseModel):
    resource_id: Optional[str] = None
    resource_code: Optional[str] = None
    calculation_id: Optional[str] = None
    estimation_id: Optional[str] = None
    engineering_element_id: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

class ResourcePlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    engineering_element_id: str
    resource_id: str
    resource_code: Optional[str] = None
    resource_name: Optional[str] = None
    resource_category: Optional[str] = None
    resource_unit: Optional[str] = None
    source_type: Optional[str] = None
    calculation_id: Optional[str] = None
    estimation_id: Optional[str] = None
    mapping_id: Optional[str] = None
    planned_quantity: Optional[Decimal] = None
    planned_unit: Optional[str] = None
    resource_demand: Decimal
    resource_demand_unit: str
    planning_method: str
    classification: str
    assumptions_json: Optional[Dict[str, Any]] = None
    provenance_json: Dict[str, Any]
    status: str
    created_by: str
    created_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None
    provenance_hierarchy: Optional[Dict[str, Any]] = None

# ==============================================================================
# PHASE 1H: DETERMINISTIC CONSTRUCTION SCHEDULING SCHEMAS
# ==============================================================================

class ActivityTypeEnum(str, Enum):
    EXCAVATION = "EXCAVATION"
    FOUNDATION = "FOUNDATION"
    REINFORCEMENT = "REINFORCEMENT"
    FORMWORK = "FORMWORK"
    CONCRETING = "CONCRETING"
    CURING = "CURING"
    MASONRY = "MASONRY"
    PLASTERING = "PLASTERING"
    FLOORING = "FLOORING"
    PAINTING = "PAINTING"
    PAVEMENT = "PAVEMENT"
    KERB = "KERB"
    OTHER = "OTHER"

class DurationMethodEnum(str, Enum):
    USER_PROVIDED = "USER_PROVIDED"
    RULE_BASED = "RULE_BASED"
    DETERMINISTIC = "DETERMINISTIC"

class DurationClassificationEnum(str, Enum):
    USER_PROVIDED = "USER_PROVIDED"
    ASSUMPTION_BASED = "ASSUMPTION_BASED"
    CALCULATED = "CALCULATED"

class ActivityStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEPRECATED = "DEPRECATED"

class DependencyTypeEnum(str, Enum):
    FINISH_TO_START = "FINISH_TO_START"

class ScheduleStatusEnum(str, Enum):
    CALCULATED = "CALCULATED"
    INVALID_INPUT = "INVALID_INPUT"
    CIRCULAR_DEPENDENCY = "CIRCULAR_DEPENDENCY"
    REQUIRES_INPUT = "REQUIRES_INPUT"
    SUPERSEDED = "SUPERSEDED"

class ActivityCreate(BaseModel):
    activity_code: str
    activity_name: str
    activity_type: ActivityTypeEnum
    description: Optional[str] = None
    engineering_element_id: Optional[str] = None
    duration_value: Optional[Decimal] = None
    duration_unit: Optional[str] = "day"
    duration_method: DurationMethodEnum = DurationMethodEnum.USER_PROVIDED
    duration_classification: DurationClassificationEnum = DurationClassificationEnum.USER_PROVIDED
    metadata_json: Optional[Dict[str, Any]] = None

class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    engineering_element_id: Optional[str] = None
    activity_code: str
    activity_name: str
    description: Optional[str] = None
    activity_type: ActivityTypeEnum
    duration_value: Optional[Decimal] = None
    duration_unit: Optional[str] = None
    duration_method: DurationMethodEnum
    duration_classification: DurationClassificationEnum
    status: ActivityStatusEnum
    created_by: str
    created_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None

class ActivityRevisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    activity_id: str
    project_id: str
    revision_number: int
    activity_code: str
    activity_name: str
    description: Optional[str] = None
    activity_type: str
    engineering_element_id: Optional[str] = None
    duration_value: Optional[Decimal] = None
    duration_unit: Optional[str] = None
    duration_method: str
    duration_classification: str
    status: str
    metadata_json: Optional[Dict[str, Any]] = None
    created_by: str
    created_at: datetime
    revision_note: Optional[str] = None

class DependencyCreate(BaseModel):
    successor_activity_id: str
    dependency_type: DependencyTypeEnum = DependencyTypeEnum.FINISH_TO_START
    lag_value: Decimal = Decimal("0")
    lag_unit: str = "day"
    metadata_json: Optional[Dict[str, Any]] = None

class DependencyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    predecessor_activity_id: str
    successor_activity_id: str
    predecessor_code: Optional[str] = None
    successor_code: Optional[str] = None
    dependency_type: DependencyTypeEnum
    lag_value: Decimal
    lag_unit: str
    created_by: str
    created_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None

class DependencyRevisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    dependency_id: str
    project_id: str
    revision_number: int
    predecessor_activity_id: str
    successor_activity_id: str
    dependency_type: str
    lag_value: Decimal
    lag_unit: str
    created_by: str
    created_at: datetime
    revision_note: Optional[str] = None

class ActivityScheduleResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    schedule_id: str
    activity_id: str
    activity_code: Optional[str] = None
    activity_name: Optional[str] = None
    es: Decimal
    ef: Decimal
    ls: Decimal
    lf: Decimal
    total_float: Decimal
    is_critical: bool
    created_at: datetime

class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    schedule_version: str
    calculation_status: ScheduleStatusEnum
    project_duration: Optional[Decimal] = None
    duration_unit: str
    canonical_schedule_unit: str = "day"
    calculated_at: datetime
    calculated_by: str
    algorithm_version: str
    input_snapshot_json: Dict[str, Any]
    result_summary_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    critical_path: Optional[List[str]] = None
    results: Optional[List[ActivityScheduleResultResponse]] = None

# ==============================================================================
# PHASE 1I: DAILY SITE PROGRESS MONITORING & ACTIVITY TRACKING SCHEMAS
# ==============================================================================

class MonitoringBaselineStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    REJECTED = "REJECTED"

class ReportSubmissionStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    FINALIZED = "FINALIZED"

class ActivityProgressStatusEnum(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ON_HOLD = "ON_HOLD"

class ProgressVerificationStatusEnum(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    CORRECTED = "CORRECTED"
    REJECTED = "REJECTED"

class ProgressSourceClassificationEnum(str, Enum):
    CONTRACTOR_DECLARED = "CONTRACTOR_DECLARED"
    SUPERVISOR_VERIFIED = "SUPERVISOR_VERIFIED"
    SYSTEM_DERIVED = "SYSTEM_DERIVED"

class VarianceStatusEnum(str, Enum):
    CALCULATED = "CALCULATED"
    DELAYED = "DELAYED"
    ON_SCHEDULE = "ON_SCHEDULE"
    AHEAD = "AHEAD"
    NOT_AVAILABLE = "NOT_AVAILABLE"

class MonitoringBaselineCreate(BaseModel):
    schedule_id: str
    baseline_start_date: date
    metadata_json: Optional[Dict[str, Any]] = None

class MonitoringBaselineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    schedule_id: str
    schedule_version: str
    schedule_algorithm_version: str
    baseline_start_date: Optional[date] = None
    frozen_by: str
    frozen_at: datetime
    status: MonitoringBaselineStatusEnum
    metadata_json: Optional[Dict[str, Any]] = None

class DailyProgressReportCreate(BaseModel):
    report_date: date
    metadata_json: Optional[Dict[str, Any]] = None

class DailyActivityProgressVerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    daily_activity_progress_id: str
    project_id: str
    verification_status: ProgressVerificationStatusEnum
    verified_quantity: Optional[Decimal] = None
    verified_quantity_unit: Optional[str] = None
    verified_percent_complete: Optional[Decimal] = None
    verified_actual_start: Optional[date] = None
    verified_actual_finish: Optional[date] = None
    verified_remaining_duration: Optional[Decimal] = None
    verified_status: Optional[str] = None
    verification_note: Optional[str] = None
    verified_by: str
    verified_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None

class DailyActivityProgressCreate(BaseModel):
    activity_id: str
    contractor_progress_value: Optional[Decimal] = None
    contractor_progress_unit: Optional[str] = None
    contractor_percent_complete: Optional[Decimal] = None
    contractor_actual_start: Optional[date] = None
    contractor_actual_finish: Optional[date] = None
    contractor_remaining_duration: Optional[Decimal] = None
    contractor_status: ActivityProgressStatusEnum = ActivityProgressStatusEnum.NOT_STARTED
    metadata_json: Optional[Dict[str, Any]] = None

class DailyActivityProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    daily_report_id: str
    project_id: str
    activity_id: str
    activity_code: Optional[str] = None
    activity_name: Optional[str] = None
    scheduled_activity_reference: Optional[str] = None
    contractor_progress_value: Optional[Decimal] = None
    contractor_progress_unit: Optional[str] = None
    contractor_percent_complete: Optional[Decimal] = None
    contractor_actual_start: Optional[date] = None
    contractor_actual_finish: Optional[date] = None
    contractor_remaining_duration: Optional[Decimal] = None
    contractor_status: ActivityProgressStatusEnum
    created_by: str
    created_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None
    latest_verification: Optional[DailyActivityProgressVerificationResponse] = None
    operational_value: Optional[Decimal] = None
    operational_percent: Optional[Decimal] = None
    operational_status: Optional[str] = None
    verification_status: Optional[str] = None

class DailyProgressReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    report_date: date
    submitted_by: str
    submission_status: ReportSubmissionStatusEnum
    created_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None
    activities: Optional[List[DailyActivityProgressResponse]] = None

class DailyActivityProgressVerificationCreate(BaseModel):
    verification_status: ProgressVerificationStatusEnum
    verified_quantity: Optional[Decimal] = None
    verified_quantity_unit: Optional[str] = None
    verified_percent_complete: Optional[Decimal] = None
    verified_actual_start: Optional[date] = None
    verified_actual_finish: Optional[date] = None
    verified_remaining_duration: Optional[Decimal] = None
    verified_status: Optional[ActivityProgressStatusEnum] = None
    verification_note: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

class ProgressVarianceResponse(BaseModel):
    project_id: Optional[str] = None
    daily_activity_progress_id: str
    activity_id: str
    activity_code: Optional[str] = None
    activity_name: Optional[str] = None
    baseline_id: Optional[str] = None
    monitoring_baseline_id: Optional[str] = None
    schedule_id: Optional[str] = None
    schedule_version: Optional[str] = None
    schedule_algorithm_version: Optional[str] = None
    baseline_start_date: Optional[date] = None
    planned_start: Optional[date] = None
    planned_finish: Optional[date] = None
    actual_start: Optional[date] = None
    actual_finish: Optional[date] = None
    planned_duration: Optional[Decimal] = None
    actual_duration: Optional[Decimal] = None
    duration_variance: Optional[Decimal] = None
    finish_variance: Optional[Decimal] = None
    contractor_declared_quantity: Optional[Decimal] = None
    supervisor_verified_quantity: Optional[Decimal] = None
    operational_quantity: Optional[Decimal] = None
    planned_quantity: Optional[Decimal] = None
    quantity_variance: Optional[Decimal] = None
    contractor_declared_percent: Optional[Decimal] = None
    supervisor_verified_percent: Optional[Decimal] = None
    operational_percent: Optional[Decimal] = None
    operational_source: ProgressSourceClassificationEnum
    verification_status: Optional[str] = None
    status: VarianceStatusEnum
    variance_status: VarianceStatusEnum


# ==============================================================================
# PHASE 1J: BOQ INGESTION, LINE ITEM REPRESENTATION & RECONCILIATION
# ==============================================================================

class BoqItemStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    SUPERSEDED = "SUPERSEDED"

class BoqMappingStatusEnum(str, Enum):
    PROPOSED = "PROPOSED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"

class BoqMappingTypeEnum(str, Enum):
    DIRECT = "DIRECT"

class BoqDiscrepancyStatusEnum(str, Enum):
    MATCH = "MATCH"
    OVER_CALCULATED = "OVER_CALCULATED"
    UNDER_CALCULATED = "UNDER_CALCULATED"
    UNIT_MISMATCH = "UNIT_MISMATCH"

class BoqReconciliationStatusEnum(str, Enum):
    CALCULATED = "CALCULATED"
    SUPERSEDED = "SUPERSEDED"

class BoqVerifyActionEnum(str, Enum):
    VERIFY = "VERIFY"
    REJECT = "REJECT"

class BoqItemCreate(BaseModel):
    item_code: str
    description: str
    unit: str
    stated_quantity: Decimal = Field(..., ge=0)
    evidence_id: Optional[str] = None
    replaces_boq_item_id: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

class BoqItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    document_id: str
    evidence_id: Optional[str] = None
    item_code: str
    description: str
    unit: str
    stated_quantity: Decimal
    status: BoqItemStatusEnum
    classification: str
    replaces_boq_item_id: Optional[str] = None
    provenance_json: Dict[str, Any]
    created_by: str
    created_at: datetime
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    metadata_json: Optional[Dict[str, Any]] = None

class BoqMappingCreate(BaseModel):
    boq_item_id: str
    calculation_id: str
    mapping_type: BoqMappingTypeEnum = BoqMappingTypeEnum.DIRECT
    metadata_json: Optional[Dict[str, Any]] = None

class BoqMappingVerifyRequest(BaseModel):
    action: BoqVerifyActionEnum
    rejection_reason: Optional[str] = None

class BoqMappingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    boq_item_id: str
    calculation_id: str
    mapping_type: BoqMappingTypeEnum
    status: BoqMappingStatusEnum
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_by: str
    created_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None

class BoqReconciliationCreate(BaseModel):
    mapping_id: str
    tolerance_threshold: Optional[Decimal] = Field(default=Decimal("0.000000"), ge=0)
    metadata_json: Optional[Dict[str, Any]] = None

class BoqReconciliationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    mapping_id: str
    boq_item_id: str
    calculation_id: str
    boq_quantity: Decimal
    boq_unit: str
    calculated_quantity: Decimal
    calculated_unit: str
    quantity_delta: Optional[Decimal] = None
    variance_percentage: Optional[Decimal] = None
    tolerance_threshold: Decimal
    discrepancy_status: BoqDiscrepancyStatusEnum
    status: BoqReconciliationStatusEnum
    algorithm_version: str
    provenance_json: Dict[str, Any]
    created_by: str
    created_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None


# ==============================================================================
# PHASE 1K: DETERMINISTIC COST ESTIMATION & RATE-BASED VALUATION FOUNDATION
# ==============================================================================

class CostRateSourceTypeEnum(str, Enum):
    OFFICIAL_SCHEDULE = "OFFICIAL_SCHEDULE"
    PROJECT_SPECIFIC = "PROJECT_SPECIFIC"
    USER_PROVIDED = "USER_PROVIDED"
    ASSUMPTION_BASED = "ASSUMPTION_BASED"

class CostRateStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    SUPERSEDED = "SUPERSEDED"

class QuantityBasisEnum(str, Enum):
    BOQ_STATED = "BOQ_STATED"
    ENGINEERING_CALCULATED = "ENGINEERING_CALCULATED"
    VERIFIED_RECONCILED = "VERIFIED_RECONCILED"

class ReconciliationDecisionEnum(str, Enum):
    ACCEPT_MATCH = "ACCEPT_MATCH"
    ACCEPT_CALCULATED = "ACCEPT_CALCULATED"
    ACCEPT_BOQ = "ACCEPT_BOQ"

class CostCalculationStatusEnum(str, Enum):
    CALCULATED = "CALCULATED"
    SUPERSEDED = "SUPERSEDED"

class CostRateCreate(BaseModel):
    rate_code: str
    description: str
    unit: str
    rate_value: Decimal = Field(..., ge=0)
    currency: str = "INR"
    source_type: CostRateSourceTypeEnum
    source_reference: str
    source_document_id: Optional[str] = None
    source_evidence_id: Optional[str] = None
    version: Optional[str] = "1.0"
    replaces_rate_id: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

class CostRateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: Optional[str] = None
    rate_code: str
    description: str
    unit: str
    rate_value: Decimal
    currency: str
    source_type: CostRateSourceTypeEnum
    source_reference: str
    source_document_id: Optional[str] = None
    source_evidence_id: Optional[str] = None
    version: str
    status: CostRateStatusEnum
    replaces_rate_id: Optional[str] = None
    created_by: str
    created_at: datetime
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    metadata_json: Optional[Dict[str, Any]] = None

class CostCalculationCreate(BaseModel):
    cost_rate_id: str
    quantity_basis: QuantityBasisEnum
    boq_item_id: Optional[str] = None
    calculation_id: Optional[str] = None
    reconciliation_id: Optional[str] = None
    reconciliation_decision: Optional[ReconciliationDecisionEnum] = None
    decision_reason: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

class CostCalculationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    cost_rate_id: str
    quantity_basis: QuantityBasisEnum
    boq_item_id: Optional[str] = None
    calculation_id: Optional[str] = None
    reconciliation_id: Optional[str] = None
    reconciliation_decision: Optional[ReconciliationDecisionEnum] = None
    decision_reason: Optional[str] = None
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    quantity_value: Decimal
    quantity_unit: str
    rate_value: Decimal
    rate_unit: str
    rate_version: str
    currency: str
    total_cost: Decimal
    status: CostCalculationStatusEnum
    formula_identifier: str
    formula_expression: str
    algorithm_version: str
    provenance_json: Dict[str, Any]
    created_by: str
    created_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None

class ProjectCostSummaryResponse(BaseModel):
    project_id: str
    boq_stated_total: Decimal
    engineering_calculated_total: Decimal
    verified_reconciled_total: Decimal
    currency: str
    active_rates_count: int
    active_calculations_count: int
    comparable_items_count: int
    unmatched_boq_items_count: int
    unmatched_engineering_items_count: int
    comparable_valuation_delta: Decimal






