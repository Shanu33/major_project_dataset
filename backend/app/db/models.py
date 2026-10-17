from sqlalchemy import Column, Integer, Float, Numeric, String, Boolean, ForeignKey, DateTime, JSON, Index, Text, text, CheckConstraint, UniqueConstraint, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)

class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    created_by = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    active_baseline_id = Column(String, ForeignKey("project_baselines.id", use_alter=True, name="fk_active_baseline"), nullable=True)
    baselines = relationship("ProjectBaseline", back_populates="project", foreign_keys="ProjectBaseline.project_id")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    engineering_elements = relationship("EngineeringElement", back_populates="project", cascade="all, delete-orphan")
    activities = relationship("ConstructionActivity", back_populates="project", cascade="all, delete-orphan")
    schedules = relationship("ConstructionSchedule", back_populates="project", cascade="all, delete-orphan")
    monitoring_baselines = relationship("MonitoringBaseline", back_populates="project", cascade="all, delete-orphan")
    daily_progress_reports = relationship("DailyProgressReport", back_populates="project", cascade="all, delete-orphan")
    boq_items = relationship("BoqItem", back_populates="project", cascade="all, delete-orphan")
    boq_mappings = relationship("BoqCalculationMapping", back_populates="project", cascade="all, delete-orphan")
    boq_reconciliations = relationship("BoqReconciliation", back_populates="project", cascade="all, delete-orphan")
    cost_rates = relationship("CostRate", back_populates="project", cascade="all, delete-orphan")
    cost_calculations = relationship("CostCalculation", back_populates="project", cascade="all, delete-orphan")
    activity_rate_mappings = relationship("ActivityRateMapping", back_populates="project", cascade="all, delete-orphan")
    daily_progress_valuations = relationship("DailyProgressValuation", back_populates="project", cascade="all, delete-orphan")
    period_progress_certificates = relationship("PeriodProgressCertificate", back_populates="project", cascade="all, delete-orphan")
    contract_execution_items = relationship("ContractExecutionItem", back_populates="project", cascade="all, delete-orphan")
    activity_contract_mappings = relationship("ActivityContractMapping", back_populates="project", cascade="all, delete-orphan")
    contract_variation_orders = relationship("ContractVariationOrder", back_populates="project", cascade="all, delete-orphan")
    boq_reconciliation_snapshots = relationship("BoqReconciliationSnapshot", back_populates="project", cascade="all, delete-orphan")
    material_items = relationship("MaterialItem", back_populates="project", cascade="all, delete-orphan")
    material_mix_designs = relationship("MaterialMixDesign", back_populates="project", cascade="all, delete-orphan")
    material_plans = relationship("MaterialPlan", back_populates="project", cascade="all, delete-orphan")
    material_consumption_entries = relationship("MaterialConsumptionEntry", back_populates="project", cascade="all, delete-orphan")
    theoretical_consumption_items = relationship("TheoreticalConsumptionItem", back_populates="project", cascade="all, delete-orphan")
    material_reconciliation_reports = relationship("MaterialReconciliationReport", back_populates="project", cascade="all, delete-orphan")

class ProjectMember(Base):
    __tablename__ = "project_members"
    project_id = Column(String, ForeignKey("projects.id"), primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    project = relationship("Project", back_populates="members")

class ProjectBaseline(Base):
    __tablename__ = "project_baselines"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    revision_number = Column(Integer, default=0)
    frozen_by = Column(String, ForeignKey("users.id"))
    frozen_at = Column(DateTime(timezone=True), server_default=func.now())
    reason_for_revision = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    project = relationship("Project", back_populates="baselines", foreign_keys=[project_id])

    __table_args__ = (
        Index('uq_active_baseline', 'project_id', unique=True, postgresql_where=text("is_active = true")),
    )

class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    storage_key = Column(String, nullable=False)
    document_type = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    sha256_hash = Column(String, nullable=False)
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processing_status = Column(String, nullable=False, default="UPLOADED")

    # Phase 1B Classification Fields (system results, leaving original document_type unchanged)
    classified_document_type = Column(String, nullable=True)
    classification_score = Column(Float, nullable=True) # Explicit heuristic rule score, NOT a statistical probability or ML confidence
    classification_method = Column(String, nullable=True)
    classified_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="documents")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan", order_by="DocumentPage.page_number")
    processing_history = relationship("DocumentProcessingHistory", back_populates="document", cascade="all, delete-orphan", order_by="DocumentProcessingHistory.started_at")
    evidence_records = relationship("Evidence", back_populates="document", cascade="all, delete-orphan")
    boq_items = relationship("BoqItem", back_populates="document")
    
    __table_args__ = (
        Index('uq_project_file_hash', 'project_id', 'sha256_hash', unique=True),
    )

class DocumentPage(Base):
    __tablename__ = "document_pages"
    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    page_count = Column(Integer, nullable=False)
    page_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="pages")
    evidence_records = relationship("Evidence", back_populates="page")

    __table_args__ = (
        Index('uq_document_page_number', 'document_id', 'page_number', unique=True),
    )

class DocumentProcessingHistory(Base):
    __tablename__ = "document_processing_history"
    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    processing_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_code = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    processor_version = Column(String, nullable=False, default="phase-1b-v1")
    metadata_json = Column(JSON, nullable=True)

    document = relationship("Document", back_populates="processing_history")

# ==============================================================================
# PHASE 1C: EVIDENCE & PROVENANCE FOUNDATION
# ==============================================================================

class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_id = Column(String, ForeignKey("document_pages.id", ondelete="SET NULL"), nullable=True)
    evidence_type = Column(String, nullable=False) # TEXT, TABLE, DRAWING_REGION, DIMENSION, BOQ_ITEM, MANUAL_ENTRY
    source_reference = Column(String, nullable=False) # e.g. "BOQ Item 3.2", "Drawing S-102"
    locator = Column(JSON, nullable=True) # Structured JSON locator (e.g. {"type": "bbox", "x0": 120, ...})
    raw_content = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    verification_status = Column(String, nullable=False, default="UNVERIFIED")

    document = relationship("Document", back_populates="evidence_records")
    page = relationship("DocumentPage", back_populates="evidence_records")
    facts = relationship("ExtractedFact", back_populates="evidence", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_evidence_doc_page', 'document_id', 'page_id'),
    )

class ExtractedFact(Base):
    __tablename__ = "extracted_facts"
    id = Column(String, primary_key=True, default=generate_uuid)
    evidence_id = Column(String, ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False)
    fact_type = Column(String, nullable=False) # DIMENSION, QUANTITY, SPECIFICATION, PROPERTY
    field_name = Column(String, nullable=False) # length, width, depth, grade, count
    raw_value = Column(String, nullable=False) # e.g. "600 mm", "12.7 m" - preserved as source representation
    normalized_value = Column(Numeric(18, 6), nullable=True) # Exact engineering decimal representation
    normalized_unit = Column(String, nullable=True) # e.g. "m", "mm"
    extraction_method = Column(String, nullable=False, default="MANUAL") # MANUAL, RULE_BASED
    extraction_version = Column(String, nullable=False, default="phase-1c-v1")
    extraction_status = Column(String, nullable=False, default="EXTRACTED") # CANDIDATE, EXTRACTED, REJECTED, VERIFIED
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    verification_status = Column(String, nullable=False, default="UNVERIFIED")
    metadata_json = Column(JSON, nullable=True)

    evidence = relationship("Evidence", back_populates="facts")
    verifications = relationship("FactVerification", back_populates="fact", cascade="all, delete-orphan", order_by="FactVerification.verified_at.desc()")

class FactVerification(Base):
    __tablename__ = "fact_verifications"
    id = Column(String, primary_key=True, default=generate_uuid)
    fact_id = Column(String, ForeignKey("extracted_facts.id", ondelete="CASCADE"), nullable=False)
    verified_by = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, nullable=False) # VERIFIED, REJECTED
    verification_note = Column(String, nullable=True)
    corrected_value = Column(Numeric(18, 6), nullable=True) # Explicit correction preserving original fact immutably
    corrected_unit = Column(String, nullable=True)
    verified_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_json = Column(JSON, nullable=True)

    fact = relationship("ExtractedFact", back_populates="verifications")

# ==============================================================================
# PHASE 1D: ENGINEERING ELEMENT FOUNDATION
# ==============================================================================

class EngineeringElement(Base):
    __tablename__ = "engineering_elements"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    element_type = Column(String, nullable=False) # FOOTING, PILE, PILE_CAP, COLUMN, BEAM, SLAB, WALL, PAVEMENT, KERB, FOUNDATION, OTHER
    element_name = Column(String, nullable=False) # e.g. "C1", "Footing F-101", "Beam B-24"
    source_document_id = Column(String, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    source_page_id = Column(String, ForeignKey("document_pages.id", ondelete="SET NULL"), nullable=True)
    source_fact_id = Column(String, ForeignKey("extracted_facts.id", ondelete="SET NULL"), nullable=True)
    status = Column(String, nullable=False, default="ACTIVE") # ACTIVE, DEPRECATED
    verification_status = Column(String, nullable=False, default="PENDING") # PENDING, VERIFIED, REJECTED, CORRECTED
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_json = Column(JSON, nullable=True)

    project = relationship("Project", back_populates="engineering_elements")
    source_document = relationship("Document", foreign_keys=[source_document_id])
    source_page = relationship("DocumentPage", foreign_keys=[source_page_id])
    source_fact = relationship("ExtractedFact", foreign_keys=[source_fact_id])
    creator = relationship("User", foreign_keys=[created_by])
    revisions = relationship("EngineeringElementRevision", back_populates="element", cascade="all, delete-orphan", order_by="EngineeringElementRevision.revision_number.asc()")
    calculations = relationship("EngineeringCalculation", back_populates="engineering_element", cascade="all, delete-orphan", order_by="EngineeringCalculation.created_at.desc()")
    estimations = relationship("RuleBasedEstimation", back_populates="engineering_element", cascade="all, delete-orphan", order_by="RuleBasedEstimation.created_at.desc()")
    resource_plans = relationship("ResourcePlan", back_populates="engineering_element", cascade="all, delete-orphan", order_by="ResourcePlan.created_at.desc()")
    activities = relationship("ConstructionActivity", back_populates="engineering_element")

    __table_args__ = (
        Index('ix_engineering_elements_project', 'project_id'),
        Index('ix_engineering_elements_type', 'project_id', 'element_type'),
    )

class EngineeringElementRevision(Base):
    __tablename__ = "engineering_element_revisions"
    id = Column(String, primary_key=True, default=generate_uuid)
    element_id = Column(String, ForeignKey("engineering_elements.id", ondelete="CASCADE"), nullable=False)
    revision_number = Column(Integer, nullable=False, default=0)
    element_type = Column(String, nullable=False)
    element_name = Column(String, nullable=False)
    source_document_id = Column(String, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    source_page_id = Column(String, ForeignKey("document_pages.id", ondelete="SET NULL"), nullable=True)
    source_fact_id = Column(String, ForeignKey("extracted_facts.id", ondelete="SET NULL"), nullable=True)
    verification_status = Column(String, nullable=False, default="PENDING") # PENDING, VERIFIED, REJECTED, CORRECTED
    revision_note = Column(String, nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_json = Column(JSON, nullable=True)

    element = relationship("EngineeringElement", back_populates="revisions")
    source_document = relationship("Document", foreign_keys=[source_document_id])
    source_page = relationship("DocumentPage", foreign_keys=[source_page_id])
    source_fact = relationship("ExtractedFact", foreign_keys=[source_fact_id])
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index('uq_element_revision_num', 'element_id', 'revision_number', unique=True),
        Index('ix_element_revisions_fact', 'source_fact_id'),
    )

# ==============================================================================
# PHASE 1E: DETERMINISTIC ENGINEERING CALCULATIONS
# ==============================================================================

class EngineeringCalculation(Base):
    __tablename__ = "engineering_calculations"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    engineering_element_id = Column(String, ForeignKey("engineering_elements.id", ondelete="CASCADE"), nullable=False)
    calculation_type = Column(String, nullable=False) # e.g. CONCRETE_VOLUME_RECTANGULAR
    calculation_version = Column(String, nullable=False, default="1.0")
    status = Column(String, nullable=False, default="CALCULATED") # CALCULATED, INVALID_INPUT, REQUIRES_INPUT, SUPERSEDED
    result_value = Column(Numeric(18, 6), nullable=True) # Exact numeric representation in result_unit
    result_unit = Column(String, nullable=True) # e.g. "m3"
    formula_identifier = Column(String, nullable=False) # e.g. RECTANGULAR_VOLUME
    formula_expression = Column(String, nullable=False) # e.g. V = L * W * D
    inputs_json = Column(JSON, nullable=False)
    assumptions_json = Column(JSON, nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project")
    engineering_element = relationship("EngineeringElement", back_populates="calculations")
    creator = relationship("User", foreign_keys=[created_by])
    estimations = relationship("RuleBasedEstimation", back_populates="calculation", cascade="all, delete-orphan", order_by="RuleBasedEstimation.created_at.desc()")
    resource_plans = relationship("ResourcePlan", back_populates="calculation", cascade="all, delete-orphan", order_by="ResourcePlan.created_at.desc()")
    boq_mappings = relationship("BoqCalculationMapping", back_populates="calculation")
    boq_reconciliations = relationship("BoqReconciliation", back_populates="calculation")

    __table_args__ = (
        Index('ix_calculations_element', 'engineering_element_id'),
        Index('ix_calculations_project', 'project_id'),
        Index('ix_calculations_type', 'project_id', 'calculation_type'),
    )

# ==============================================================================
# PHASE 1F: RULE-BASED ESTIMATIONS
# ==============================================================================

class Rule(Base):
    __tablename__ = "rules"
    id = Column(String, primary_key=True, default=generate_uuid)
    rule_code = Column(String, nullable=False) # e.g. LABOUR_HOURS_FROM_QUANTITY
    rule_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    rule_category = Column(String, nullable=False) # e.g. LABOUR_PRODUCTIVITY
    input_unit = Column(String, nullable=False) # e.g. m3
    output_unit = Column(String, nullable=False) # e.g. labour-hour
    formula_identifier = Column(String, nullable=False) # e.g. QUANTITY_DIVIDED_BY_PRODUCTIVITY
    formula_expression = Column(String, nullable=False) # e.g. labour_hours = quantity / productivity_rate
    parameters_json = Column(JSON, nullable=False) # parameter definitions/defaults
    source_reference = Column(String, nullable=True)
    version = Column(String, nullable=False, default="1.0")
    status = Column(String, nullable=False, default="ACTIVE") # ACTIVE, INACTIVE, DEPRECATED
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_json = Column(JSON, nullable=True)

    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index('uq_rule_code_version', 'rule_code', 'version', unique=True),
        Index('ix_rules_status', 'status'),
    )

class RuleBasedEstimation(Base):
    __tablename__ = "rule_based_estimations"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    engineering_element_id = Column(String, ForeignKey("engineering_elements.id", ondelete="CASCADE"), nullable=False)
    calculation_id = Column(String, ForeignKey("engineering_calculations.id", ondelete="CASCADE"), nullable=False)
    rule_id = Column(String, ForeignKey("rules.id"), nullable=False)
    rule_version = Column(String, nullable=False)
    estimation_type = Column(String, nullable=False) # e.g. LABOUR_HOURS
    status = Column(String, nullable=False, default="ESTIMATED") # ESTIMATED, INVALID_INPUT, REQUIRES_INPUT, SUPERSEDED
    input_value = Column(Numeric(18, 6), nullable=False)
    input_unit = Column(String, nullable=False)
    result_value = Column(Numeric(18, 6), nullable=False)
    result_unit = Column(String, nullable=False)
    parameters_json = Column(JSON, nullable=False)
    assumptions_json = Column(JSON, nullable=False)
    provenance_json = Column(JSON, nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_json = Column(JSON, nullable=True)

    project = relationship("Project")
    engineering_element = relationship("EngineeringElement", back_populates="estimations")
    calculation = relationship("EngineeringCalculation", back_populates="estimations")
    rule = relationship("Rule")
    creator = relationship("User", foreign_keys=[created_by])
    resource_plans = relationship("ResourcePlan", back_populates="estimation", cascade="all, delete-orphan", order_by="ResourcePlan.created_at.desc()")

    __table_args__ = (
        Index('ix_estimations_project', 'project_id'),
        Index('ix_estimations_element', 'engineering_element_id'),
        Index('ix_estimations_calc', 'calculation_id'),
        Index('ix_estimations_rule', 'rule_id'),
    )

# ==============================================================================
# PHASE 1G: RESOURCE PLANNING FOUNDATION
# ==============================================================================

class Resource(Base):
    __tablename__ = "resources"
    id = Column(String, primary_key=True, default=generate_uuid)
    resource_code = Column(String, nullable=False) # e.g. LABOUR-CONCRETE
    resource_name = Column(String, nullable=False)
    resource_category = Column(String, nullable=False) # LABOUR, MATERIAL, EQUIPMENT
    unit = Column(String, nullable=False) # e.g. labour-hour, m3
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="ACTIVE") # ACTIVE, INACTIVE, DEPRECATED
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_json = Column(JSON, nullable=True)

    creator = relationship("User", foreign_keys=[created_by])
    plans = relationship("ResourcePlan", back_populates="resource")

    __table_args__ = (
        Index('uq_resource_code', 'resource_code', unique=True),
        Index('ix_resources_category', 'resource_category'),
        Index('ix_resources_status', 'status'),
    )

class CalculationResourceMapping(Base):
    __tablename__ = "calculation_resource_mappings"
    id = Column(String, primary_key=True, default=generate_uuid)
    calculation_type = Column(String, nullable=False)
    calculation_version = Column(String, nullable=False)
    resource_id = Column(String, ForeignKey("resources.id"), nullable=False)
    source_unit = Column(String, nullable=False)
    resource_unit = Column(String, nullable=False)
    mapping_method = Column(String, nullable=False, default="DIRECT")
    status = Column(String, nullable=False, default="ACTIVE") # ACTIVE, INACTIVE, DEPRECATED
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_json = Column(JSON, nullable=True)

    resource = relationship("Resource")
    creator = relationship("User", foreign_keys=[created_by])
    plans = relationship("ResourcePlan", back_populates="mapping")

    __table_args__ = (
        Index('uq_calc_res_mapping', 'calculation_type', 'calculation_version', 'resource_id', 'source_unit', unique=True),
        Index('ix_calc_res_mappings_res', 'resource_id'),
        Index('ix_calc_res_mappings_status', 'status'),
    )

class ResourcePlan(Base):
    __tablename__ = "resource_plans"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    engineering_element_id = Column(String, ForeignKey("engineering_elements.id", ondelete="CASCADE"), nullable=False)
    resource_id = Column(String, ForeignKey("resources.id"), nullable=False)
    calculation_id = Column(String, ForeignKey("engineering_calculations.id", ondelete="CASCADE"), nullable=True)
    estimation_id = Column(String, ForeignKey("rule_based_estimations.id", ondelete="CASCADE"), nullable=True)
    mapping_id = Column(String, ForeignKey("calculation_resource_mappings.id"), nullable=True)
    planned_quantity = Column(Numeric(18, 6), nullable=True)
    planned_unit = Column(String, nullable=True)
    resource_demand = Column(Numeric(18, 6), nullable=False)
    resource_demand_unit = Column(String, nullable=False)
    planning_method = Column(String, nullable=False) # DETERMINISTIC, RULE_BASED, USER_PROVIDED
    classification = Column(String, nullable=False) # CALCULATED, DERIVED, ASSUMPTION_BASED, USER_PROVIDED
    assumptions_json = Column(JSON, nullable=True)
    provenance_json = Column(JSON, nullable=False)
    status = Column(String, nullable=False, default="PLANNED") # PLANNED, SUPERSEDED
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_json = Column(JSON, nullable=True)

    project = relationship("Project")
    engineering_element = relationship("EngineeringElement", back_populates="resource_plans")
    resource = relationship("Resource", back_populates="plans")
    calculation = relationship("EngineeringCalculation", back_populates="resource_plans")
    estimation = relationship("RuleBasedEstimation", back_populates="resource_plans")
    mapping = relationship("CalculationResourceMapping", back_populates="plans")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index('ix_resource_plans_project', 'project_id'),
        Index('ix_resource_plans_element', 'engineering_element_id'),
        Index('ix_resource_plans_resource', 'resource_id'),
        Index('ix_resource_plans_calc', 'calculation_id'),
        Index('ix_resource_plans_estimation', 'estimation_id'),
        Index('ix_resource_plans_mapping', 'mapping_id'),
        Index('ix_resource_plans_status', 'status'),
    )

# ==============================================================================
# PHASE 1H: DETERMINISTIC CONSTRUCTION SCHEDULING
# ==============================================================================

class ConstructionActivity(Base):
    __tablename__ = "construction_activities"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    engineering_element_id = Column(String, ForeignKey("engineering_elements.id", ondelete="SET NULL"), nullable=True)
    activity_code = Column(String, nullable=False)
    activity_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    activity_type = Column(String, nullable=False)
    duration_value = Column(Numeric(18, 6), nullable=True)
    duration_unit = Column(String, nullable=True)
    duration_method = Column(String, nullable=False, default="USER_PROVIDED")
    duration_classification = Column(String, nullable=False, default="USER_PROVIDED")
    status = Column(String, nullable=False, default="ACTIVE") # ACTIVE, INACTIVE, DEPRECATED
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_json = Column(JSON, nullable=True)

    project = relationship("Project", back_populates="activities")
    engineering_element = relationship("EngineeringElement", back_populates="activities")
    creator = relationship("User", foreign_keys=[created_by])
    predecessor_dependencies = relationship("ActivityDependency", foreign_keys="ActivityDependency.successor_activity_id", back_populates="successor", cascade="all, delete-orphan")
    successor_dependencies = relationship("ActivityDependency", foreign_keys="ActivityDependency.predecessor_activity_id", back_populates="predecessor", cascade="all, delete-orphan")
    schedule_results = relationship("ActivityScheduleResult", back_populates="activity", cascade="all, delete-orphan")
    revisions = relationship("ConstructionActivityRevision", back_populates="activity", cascade="all, delete-orphan", order_by="ConstructionActivityRevision.revision_number.asc()")
    daily_progress_records = relationship("DailyActivityProgress", back_populates="activity", cascade="all, delete-orphan")
    rate_mappings = relationship("ActivityRateMapping", back_populates="activity", cascade="all, delete-orphan")
    activity_contract_mappings = relationship("ActivityContractMapping", back_populates="activity", cascade="all, delete-orphan")

    __table_args__ = (
        Index('uq_activity_project_code', 'project_id', 'activity_code', unique=True),
        Index('ix_activities_project', 'project_id'),
        Index('ix_activities_element', 'engineering_element_id'),
        Index('ix_activities_status', 'status'),
    )

class ConstructionActivityRevision(Base):
    __tablename__ = "construction_activity_revisions"
    id = Column(String, primary_key=True, default=generate_uuid)
    activity_id = Column(String, ForeignKey("construction_activities.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    revision_number = Column(Integer, nullable=False)
    activity_code = Column(String, nullable=False)
    activity_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    activity_type = Column(String, nullable=False)
    engineering_element_id = Column(String, ForeignKey("engineering_elements.id", ondelete="SET NULL"), nullable=True)
    duration_value = Column(Numeric(18, 6), nullable=True)
    duration_unit = Column(String, nullable=True)
    duration_method = Column(String, nullable=False)
    duration_classification = Column(String, nullable=False)
    status = Column(String, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revision_note = Column(Text, nullable=True)

    activity = relationship("ConstructionActivity", back_populates="revisions")
    project = relationship("Project")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        UniqueConstraint('activity_id', 'revision_number', name='uq_activity_revision'),
        Index('ix_act_rev_activity', 'activity_id'),
        Index('ix_act_rev_project', 'project_id'),
    )

class ActivityDependency(Base):
    __tablename__ = "activity_dependencies"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    predecessor_activity_id = Column(String, ForeignKey("construction_activities.id", ondelete="CASCADE"), nullable=False)
    successor_activity_id = Column(String, ForeignKey("construction_activities.id", ondelete="CASCADE"), nullable=False)
    dependency_type = Column(String, nullable=False, default="FINISH_TO_START")
    lag_value = Column(Numeric(18, 6), nullable=False, default=0)
    lag_unit = Column(String, nullable=False, default="day")
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_json = Column(JSON, nullable=True)

    project = relationship("Project")
    predecessor = relationship("ConstructionActivity", foreign_keys=[predecessor_activity_id], back_populates="successor_dependencies")
    successor = relationship("ConstructionActivity", foreign_keys=[successor_activity_id], back_populates="predecessor_dependencies")
    creator = relationship("User", foreign_keys=[created_by])
    revisions = relationship("ActivityDependencyRevision", back_populates="dependency", cascade="all, delete-orphan", order_by="ActivityDependencyRevision.revision_number.asc()")

    __table_args__ = (
        Index('uq_activity_dependency', 'project_id', 'predecessor_activity_id', 'successor_activity_id', unique=True),
        Index('ix_dependencies_project', 'project_id'),
        Index('ix_dependencies_pred', 'predecessor_activity_id'),
        Index('ix_dependencies_succ', 'successor_activity_id'),
        CheckConstraint('predecessor_activity_id != successor_activity_id', name='ck_no_self_dependency'),
    )

class ActivityDependencyRevision(Base):
    __tablename__ = "activity_dependency_revisions"
    id = Column(String, primary_key=True, default=generate_uuid)
    dependency_id = Column(String, ForeignKey("activity_dependencies.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    revision_number = Column(Integer, nullable=False)
    predecessor_activity_id = Column(String, ForeignKey("construction_activities.id", ondelete="CASCADE"), nullable=False)
    successor_activity_id = Column(String, ForeignKey("construction_activities.id", ondelete="CASCADE"), nullable=False)
    dependency_type = Column(String, nullable=False)
    lag_value = Column(Numeric(18, 6), nullable=False)
    lag_unit = Column(String, nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revision_note = Column(Text, nullable=True)

    dependency = relationship("ActivityDependency", back_populates="revisions")
    project = relationship("Project")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        UniqueConstraint('dependency_id', 'revision_number', name='uq_dependency_revision'),
        Index('ix_dep_rev_dependency', 'dependency_id'),
        Index('ix_dep_rev_project', 'project_id'),
    )

class ConstructionSchedule(Base):
    __tablename__ = "construction_schedules"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    schedule_version = Column(String, nullable=False)
    calculation_status = Column(String, nullable=False, default="CALCULATED") # CALCULATED, INVALID_INPUT, CIRCULAR_DEPENDENCY, REQUIRES_INPUT, SUPERSEDED
    project_duration = Column(Numeric(18, 6), nullable=True)
    duration_unit = Column(String, nullable=False, default="day")
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    calculated_by = Column(String, ForeignKey("users.id"), nullable=False)
    algorithm_version = Column(String, nullable=False, default="CPM_1.0")
    input_snapshot_json = Column(JSON, nullable=False)
    result_summary_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="schedules")
    calculator = relationship("User", foreign_keys=[calculated_by])
    results = relationship("ActivityScheduleResult", back_populates="schedule", cascade="all, delete-orphan", order_by="ActivityScheduleResult.es.asc()")
    monitoring_baselines = relationship("MonitoringBaseline", back_populates="schedule", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('project_id', 'schedule_version', name='uq_schedule_project_version'),
        Index('ix_schedules_project', 'project_id'),
        Index('ix_schedules_status', 'calculation_status'),
    )

class ActivityScheduleResult(Base):
    __tablename__ = "activity_schedule_results"
    id = Column(String, primary_key=True, default=generate_uuid)
    schedule_id = Column(String, ForeignKey("construction_schedules.id", ondelete="CASCADE"), nullable=False)
    activity_id = Column(String, ForeignKey("construction_activities.id", ondelete="CASCADE"), nullable=False)
    es = Column(Numeric(18, 6), nullable=False)
    ef = Column(Numeric(18, 6), nullable=False)
    ls = Column(Numeric(18, 6), nullable=False)
    lf = Column(Numeric(18, 6), nullable=False)
    total_float = Column(Numeric(18, 6), nullable=False)
    is_critical = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    schedule = relationship("ConstructionSchedule", back_populates="results")
    activity = relationship("ConstructionActivity", back_populates="schedule_results")

    __table_args__ = (
        Index('uq_sched_result_activity', 'schedule_id', 'activity_id', unique=True),
        Index('ix_sched_results_schedule', 'schedule_id'),
        Index('ix_sched_results_activity', 'activity_id'),
    )

# ==============================================================================
# PHASE 0: MONITORING, BASELINES & AUDITING
# ==============================================================================

class DailyReport(Base):
    __tablename__ = "daily_reports"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"))
    baseline_id = Column(String, ForeignKey("project_baselines.id"))
    submitted_by = Column(String, ForeignKey("users.id"))
    contractor_declared_work = Column(JSON, nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    is_finalized = Column(Boolean, default=False)
    verification = relationship("ReportVerification", back_populates="report", uselist=False)

class ReportVerification(Base):
    __tablename__ = "report_verifications"
    id = Column(String, primary_key=True, default=generate_uuid)
    daily_report_id = Column(String, ForeignKey("daily_reports.id"))
    verified_by = Column(String, ForeignKey("users.id"))
    supervisor_verified_work = Column(JSON, nullable=False)
    status = Column(String, nullable=False)
    verified_at = Column(DateTime(timezone=True), server_default=func.now())
    report = relationship("DailyReport", back_populates="verification")

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    action = Column(String, nullable=False)
    entity_type = Column(String)
    entity_id = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    reason = Column(String)

# ==============================================================================
# PHASE 1I: DAILY SITE PROGRESS MONITORING & ACTIVITY PROGRESS TRACKING
# ==============================================================================

class MonitoringBaseline(Base):
    __tablename__ = "monitoring_baselines"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    schedule_id = Column(String, ForeignKey("construction_schedules.id", ondelete="CASCADE"), nullable=False)
    schedule_version = Column(String, nullable=False)
    schedule_algorithm_version = Column(String, nullable=False)
    baseline_start_date = Column(Date, nullable=True)
    frozen_by = Column(String, ForeignKey("users.id"), nullable=False)
    frozen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String, nullable=False, default="ACTIVE") # ACTIVE, SUPERSEDED, REJECTED
    metadata_json = Column(JSON, nullable=True)

    project = relationship("Project", back_populates="monitoring_baselines")
    schedule = relationship("ConstructionSchedule", back_populates="monitoring_baselines")
    freezer = relationship("User", foreign_keys=[frozen_by])

    __table_args__ = (
        Index('ix_monitoring_baselines_project', 'project_id'),
        Index('ix_monitoring_baselines_schedule', 'schedule_id'),
        Index('ix_monitoring_baselines_status', 'status'),
        Index('uq_monitoring_baseline_active_per_project', 'project_id', unique=True, postgresql_where=text("status = 'ACTIVE'")),
        CheckConstraint("status IN ('ACTIVE', 'SUPERSEDED', 'REJECTED')", name='ck_monitoring_baseline_status'),
    )

class DailyProgressReport(Base):
    __tablename__ = "daily_progress_reports"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    report_date = Column(Date, nullable=False)
    submitted_by = Column(String, ForeignKey("users.id"), nullable=False)
    submission_status = Column(String, nullable=False, default="DRAFT") # DRAFT, SUBMITTED, FINALIZED
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata_json = Column(JSON, nullable=True)

    project = relationship("Project", back_populates="daily_progress_reports")
    submitter = relationship("User", foreign_keys=[submitted_by])
    activity_progress_items = relationship("DailyActivityProgress", back_populates="daily_report", cascade="all, delete-orphan", order_by="DailyActivityProgress.created_at.asc()")

    __table_args__ = (
        Index('ix_daily_progress_reports_project', 'project_id'),
        Index('ix_daily_progress_reports_date', 'report_date'),
        Index('ix_daily_progress_reports_status', 'submission_status'),
        CheckConstraint("submission_status IN ('DRAFT', 'SUBMITTED', 'FINALIZED')", name='ck_daily_progress_report_status'),
    )

class DailyActivityProgress(Base):
    __tablename__ = "daily_activity_progress"
    id = Column(String, primary_key=True, default=generate_uuid)
    daily_report_id = Column(String, ForeignKey("daily_progress_reports.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    activity_id = Column(String, ForeignKey("construction_activities.id", ondelete="CASCADE"), nullable=False)
    scheduled_activity_reference = Column(String, nullable=True)
    contractor_progress_value = Column(Numeric(18, 6), nullable=True)
    contractor_progress_unit = Column(String, nullable=True)
    contractor_percent_complete = Column(Numeric(5, 2), nullable=True)
    contractor_actual_start = Column(Date, nullable=True)
    contractor_actual_finish = Column(Date, nullable=True)
    contractor_remaining_duration = Column(Numeric(18, 6), nullable=True)
    contractor_status = Column(String, nullable=False, default="NOT_STARTED") # NOT_STARTED, IN_PROGRESS, COMPLETED, ON_HOLD
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata_json = Column(JSON, nullable=True)

    daily_report = relationship("DailyProgressReport", back_populates="activity_progress_items")
    project = relationship("Project")
    activity = relationship("ConstructionActivity", back_populates="daily_progress_records")
    creator = relationship("User", foreign_keys=[created_by])
    verifications = relationship("DailyActivityProgressVerification", back_populates="daily_activity_progress", cascade="all, delete-orphan", order_by="DailyActivityProgressVerification.verified_at.asc()")

    __table_args__ = (
        Index('ix_daily_act_prog_report', 'daily_report_id'),
        Index('ix_daily_act_prog_activity', 'activity_id'),
        Index('ix_daily_act_prog_project', 'project_id'),
        CheckConstraint('contractor_progress_value IS NULL OR contractor_progress_value >= 0', name='ck_contractor_progress_nonneg'),
        CheckConstraint('contractor_percent_complete IS NULL OR (contractor_percent_complete >= 0 AND contractor_percent_complete <= 100)', name='ck_contractor_percent_range'),
        CheckConstraint('contractor_remaining_duration IS NULL OR contractor_remaining_duration >= 0', name='ck_contractor_remaining_dur_nonneg'),
        CheckConstraint("contractor_status IN ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'ON_HOLD')", name='ck_daily_act_prog_status'),
        CheckConstraint("contractor_progress_value IS NULL OR (contractor_progress_unit IS NOT NULL AND length(trim(contractor_progress_unit)) > 0)", name='ck_contractor_progress_unit_required'),
        CheckConstraint("contractor_actual_start IS NULL OR contractor_actual_finish IS NULL OR contractor_actual_finish >= contractor_actual_start", name='ck_contractor_actual_dates'),
    )

class DailyActivityProgressVerification(Base):
    __tablename__ = "daily_activity_progress_verifications"
    id = Column(String, primary_key=True, default=generate_uuid)
    daily_activity_progress_id = Column(String, ForeignKey("daily_activity_progress.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    verification_status = Column(String, nullable=False) # PENDING, VERIFIED, CORRECTED, REJECTED
    verified_quantity = Column(Numeric(18, 6), nullable=True)
    verified_quantity_unit = Column(String, nullable=True)
    verified_percent_complete = Column(Numeric(5, 2), nullable=True)
    verified_actual_start = Column(Date, nullable=True)
    verified_actual_finish = Column(Date, nullable=True)
    verified_remaining_duration = Column(Numeric(18, 6), nullable=True)
    verified_status = Column(String, nullable=True) # NOT_STARTED, IN_PROGRESS, COMPLETED, ON_HOLD
    verification_note = Column(Text, nullable=True)
    verified_by = Column(String, ForeignKey("users.id"), nullable=False)
    verified_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata_json = Column(JSON, nullable=True)

    daily_activity_progress = relationship("DailyActivityProgress", back_populates="verifications")
    project = relationship("Project")
    verifier = relationship("User", foreign_keys=[verified_by])
    valuation = relationship("DailyProgressValuation", back_populates="verification", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_verifications_progress', 'daily_activity_progress_id'),
        Index('ix_verifications_project', 'project_id'),
        Index('ix_verifications_status', 'verification_status'),
        CheckConstraint('verified_quantity IS NULL OR verified_quantity >= 0', name='ck_verified_quantity_nonneg'),
        CheckConstraint('verified_percent_complete IS NULL OR (verified_percent_complete >= 0 AND verified_percent_complete <= 100)', name='ck_verified_percent_range'),
        CheckConstraint('verified_remaining_duration IS NULL OR verified_remaining_duration >= 0', name='ck_verified_remaining_dur_nonneg'),
        CheckConstraint("verification_status IN ('PENDING', 'VERIFIED', 'CORRECTED', 'REJECTED')", name='ck_verification_status'),
        CheckConstraint("verified_quantity IS NULL OR (verified_quantity_unit IS NOT NULL AND length(trim(verified_quantity_unit)) > 0)", name='ck_verified_quantity_unit_required'),
        CheckConstraint("verified_actual_start IS NULL OR verified_actual_finish IS NULL OR verified_actual_finish >= verified_actual_start", name='ck_verified_actual_dates'),
    )


# ==============================================================================
# PHASE 1J: BOQ INGESTION, LINE ITEM REPRESENTATION & RECONCILIATION
# ==============================================================================

class BoqItem(Base):
    __tablename__ = "boq_items"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id", ondelete="RESTRICT"), nullable=False)
    evidence_id = Column(String, ForeignKey("evidence.id", ondelete="RESTRICT"), nullable=True)
    item_code = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    unit = Column(String(50), nullable=False)
    stated_quantity = Column(Numeric(18, 6), nullable=False)
    status = Column(String(20), nullable=False, default="DRAFT") # DRAFT, CONFIRMED, SUPERSEDED
    classification = Column(String(50), nullable=False, default="DOCUMENT_DERIVED")
    replaces_boq_item_id = Column(String, ForeignKey("boq_items.id", ondelete="RESTRICT"), nullable=True)
    provenance_json = Column(JSON, nullable=False)
    created_by = Column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    confirmed_by = Column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(JSON, nullable=True)

    project = relationship("Project", back_populates="boq_items")
    document = relationship("Document", back_populates="boq_items")
    evidence = relationship("Evidence")
    creator = relationship("User", foreign_keys=[created_by])
    confirmer = relationship("User", foreign_keys=[confirmed_by])
    replaces_item = relationship("BoqItem", remote_side=[id])
    mappings = relationship("BoqCalculationMapping", back_populates="boq_item")
    reconciliations = relationship("BoqReconciliation", back_populates="boq_item")
    contract_execution_item = relationship("ContractExecutionItem", back_populates="boq_item", uselist=False)

    __table_args__ = (
        Index('ix_boq_items_project', 'project_id'),
        Index('ix_boq_items_document', 'document_id'),
        Index('ix_boq_items_status', 'status'),
        Index('uq_boq_items_doc_item_code', 'document_id', 'item_code', unique=True, postgresql_where=text("status IN ('DRAFT', 'CONFIRMED')")),
        CheckConstraint('stated_quantity >= 0', name='ck_boq_items_stated_quantity_nonneg'),
        CheckConstraint("status IN ('DRAFT', 'CONFIRMED', 'SUPERSEDED')", name='ck_boq_items_status'),
        CheckConstraint("length(trim(item_code)) > 0", name='ck_boq_items_item_code_nonempty'),
        CheckConstraint("length(trim(unit)) > 0", name='ck_boq_items_unit_nonempty'),
        CheckConstraint("status != 'CONFIRMED' OR (confirmed_by IS NOT NULL AND confirmed_at IS NOT NULL)", name='ck_boq_items_confirmed_fields'),
    )


class BoqCalculationMapping(Base):
    __tablename__ = "boq_calculation_mappings"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    boq_item_id = Column(String, ForeignKey("boq_items.id", ondelete="RESTRICT"), nullable=False)
    calculation_id = Column(String, ForeignKey("engineering_calculations.id", ondelete="RESTRICT"), nullable=False)
    mapping_type = Column(String(20), nullable=False, default="DIRECT") # DIRECT
    status = Column(String(20), nullable=False, default="PROPOSED") # PROPOSED, VERIFIED, REJECTED, SUPERSEDED
    verified_by = Column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_by = Column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata_json = Column(JSON, nullable=True)

    project = relationship("Project", back_populates="boq_mappings")
    boq_item = relationship("BoqItem", back_populates="mappings")
    calculation = relationship("EngineeringCalculation", back_populates="boq_mappings")
    creator = relationship("User", foreign_keys=[created_by])
    verifier = relationship("User", foreign_keys=[verified_by])
    reconciliations = relationship("BoqReconciliation", back_populates="mapping")

    __table_args__ = (
        Index('ix_boq_mappings_project', 'project_id'),
        Index('ix_boq_mappings_boq_item', 'boq_item_id'),
        Index('ix_boq_mappings_calculation', 'calculation_id'),
        Index('ix_boq_mappings_status', 'status'),
        Index('uq_boq_mappings_active_boq', 'boq_item_id', unique=True, postgresql_where=text("status IN ('PROPOSED', 'VERIFIED')")),
        Index('uq_boq_mappings_active_calc', 'calculation_id', unique=True, postgresql_where=text("status IN ('PROPOSED', 'VERIFIED')")),
        CheckConstraint("mapping_type = 'DIRECT'", name='ck_boq_mappings_type_direct'),
        CheckConstraint("status IN ('PROPOSED', 'VERIFIED', 'REJECTED', 'SUPERSEDED')", name='ck_boq_mappings_status'),
        CheckConstraint("status != 'VERIFIED' OR (verified_by IS NOT NULL AND verified_at IS NOT NULL)", name='ck_boq_mappings_verified_fields'),
        CheckConstraint("status != 'REJECTED' OR (verified_by IS NOT NULL AND verified_at IS NOT NULL AND rejection_reason IS NOT NULL AND length(trim(rejection_reason)) > 0)", name='ck_boq_mappings_rejected_fields'),
    )


class BoqReconciliation(Base):
    __tablename__ = "boq_reconciliations"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    mapping_id = Column(String, ForeignKey("boq_calculation_mappings.id", ondelete="RESTRICT"), nullable=False)
    boq_item_id = Column(String, ForeignKey("boq_items.id", ondelete="RESTRICT"), nullable=False)
    calculation_id = Column(String, ForeignKey("engineering_calculations.id", ondelete="RESTRICT"), nullable=False)
    boq_quantity = Column(Numeric(18, 6), nullable=False)
    boq_unit = Column(String(50), nullable=False)
    calculated_quantity = Column(Numeric(18, 6), nullable=False)
    calculated_unit = Column(String(50), nullable=False)
    quantity_delta = Column(Numeric(18, 6), nullable=True)
    variance_percentage = Column(Numeric(18, 6), nullable=True)
    tolerance_threshold = Column(Numeric(18, 6), nullable=False, default=0.0)
    discrepancy_status = Column(String(30), nullable=False) # MATCH, OVER_CALCULATED, UNDER_CALCULATED, UNIT_MISMATCH
    status = Column(String(20), nullable=False, default="CALCULATED") # CALCULATED, SUPERSEDED
    algorithm_version = Column(String(50), nullable=False, default="1.0")
    provenance_json = Column(JSON, nullable=False)
    created_by = Column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata_json = Column(JSON, nullable=True)

    project = relationship("Project", back_populates="boq_reconciliations")
    mapping = relationship("BoqCalculationMapping", back_populates="reconciliations")
    boq_item = relationship("BoqItem", back_populates="reconciliations")
    calculation = relationship("EngineeringCalculation", back_populates="boq_reconciliations")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index('ix_boq_reconciliations_project', 'project_id'),
        Index('ix_boq_reconciliations_mapping', 'mapping_id'),
        Index('ix_boq_reconciliations_boq_item', 'boq_item_id'),
        Index('ix_boq_reconciliations_calculation', 'calculation_id'),
        Index('ix_boq_reconciliations_status', 'status'),
        Index('ix_boq_reconciliations_discrepancy', 'discrepancy_status'),
        Index('uq_boq_reconciliations_active_mapping', 'mapping_id', unique=True, postgresql_where=text("status = 'CALCULATED'")),
        CheckConstraint('boq_quantity >= 0', name='ck_boq_reconciliations_boq_qty_nonneg'),
        CheckConstraint('calculated_quantity >= 0', name='ck_boq_reconciliations_calc_qty_nonneg'),
        CheckConstraint('tolerance_threshold >= 0', name='ck_boq_reconciliations_tolerance_nonneg'),
        CheckConstraint("discrepancy_status IN ('MATCH', 'OVER_CALCULATED', 'UNDER_CALCULATED', 'UNIT_MISMATCH')", name='ck_boq_reconciliations_discrepancy_status'),
        CheckConstraint("status IN ('CALCULATED', 'SUPERSEDED')", name='ck_boq_reconciliations_status'),
    )


# ==============================================================================
# PHASE 1K: DETERMINISTIC COST ESTIMATION & RATE-BASED VALUATION FOUNDATION
# ==============================================================================

class CostRate(Base):
    __tablename__ = "cost_rates"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    rate_code = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    unit = Column(String(50), nullable=False)
    rate_value = Column(Numeric(18, 6), nullable=False)
    currency = Column(String(10), nullable=False, default="INR")
    source_type = Column(String(50), nullable=False) # OFFICIAL_SCHEDULE, PROJECT_SPECIFIC, USER_PROVIDED, ASSUMPTION_BASED
    source_reference = Column(String(255), nullable=False)
    source_document_id = Column(String, ForeignKey("documents.id", ondelete="RESTRICT"), nullable=True)
    source_evidence_id = Column(String, ForeignKey("evidence.id", ondelete="RESTRICT"), nullable=True)
    version = Column(String(50), nullable=False, default="1.0")
    status = Column(String(20), nullable=False, default="DRAFT") # DRAFT, CONFIRMED, SUPERSEDED
    replaces_rate_id = Column(String, ForeignKey("cost_rates.id", ondelete="RESTRICT"), nullable=True)
    created_by = Column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    confirmed_by = Column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(JSON, nullable=True)

    project = relationship("Project", back_populates="cost_rates")
    source_document = relationship("Document", foreign_keys=[source_document_id])
    source_evidence = relationship("Evidence", foreign_keys=[source_evidence_id])
    creator = relationship("User", foreign_keys=[created_by])
    confirmer = relationship("User", foreign_keys=[confirmed_by])
    replaces_rate = relationship("CostRate", remote_side=[id])
    calculations = relationship("CostCalculation", back_populates="cost_rate")

    __table_args__ = (
        Index('ix_cost_rates_project', 'project_id'),
        Index('ix_cost_rates_code', 'rate_code'),
        Index('ix_cost_rates_status', 'status'),
        Index('uq_cost_rates_global_active_code', 'rate_code', unique=True, postgresql_where=text("project_id IS NULL AND status = 'CONFIRMED'")),
        Index('uq_cost_rates_project_active_code', 'project_id', 'rate_code', unique=True, postgresql_where=text("project_id IS NOT NULL AND status = 'CONFIRMED'")),
        CheckConstraint('rate_value >= 0', name='ck_cost_rates_rate_val_nonneg'),
        CheckConstraint("status IN ('DRAFT', 'CONFIRMED', 'SUPERSEDED')", name='ck_cost_rates_status'),
        CheckConstraint("source_type IN ('OFFICIAL_SCHEDULE', 'PROJECT_SPECIFIC', 'USER_PROVIDED', 'ASSUMPTION_BASED')", name='ck_cost_rates_source_type'),
        CheckConstraint("length(trim(rate_code)) > 0", name='ck_cost_rates_code_nonempty'),
        CheckConstraint("length(trim(unit)) > 0", name='ck_cost_rates_unit_nonempty'),
        CheckConstraint("length(trim(currency)) > 0", name='ck_cost_rates_currency_nonempty'),
        CheckConstraint("status != 'CONFIRMED' OR (confirmed_by IS NOT NULL AND confirmed_at IS NOT NULL)", name='ck_cost_rates_confirmed_fields'),
        CheckConstraint("project_id IS NOT NULL OR (source_document_id IS NULL AND source_evidence_id IS NULL)", name='ck_cost_rates_global_no_doc'),
        CheckConstraint("source_evidence_id IS NULL OR source_document_id IS NOT NULL", name='ck_cost_rates_evidence_requires_doc'),
        CheckConstraint("replaces_rate_id IS NULL OR replaces_rate_id != id", name='ck_cost_rates_no_self_replace'),
    )


class CostCalculation(Base):
    __tablename__ = "cost_calculations"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    cost_rate_id = Column(String, ForeignKey("cost_rates.id", ondelete="RESTRICT"), nullable=False)
    quantity_basis = Column(String(30), nullable=False) # BOQ_STATED, ENGINEERING_CALCULATED, VERIFIED_RECONCILED
    boq_item_id = Column(String, ForeignKey("boq_items.id", ondelete="RESTRICT"), nullable=True)
    calculation_id = Column(String, ForeignKey("engineering_calculations.id", ondelete="RESTRICT"), nullable=True)
    reconciliation_id = Column(String, ForeignKey("boq_reconciliations.id", ondelete="RESTRICT"), nullable=True)
    reconciliation_decision = Column(String(30), nullable=True) # ACCEPT_MATCH, ACCEPT_CALCULATED, ACCEPT_BOQ
    decision_reason = Column(Text, nullable=True)
    decided_by = Column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    quantity_value = Column(Numeric(18, 6), nullable=False)
    quantity_unit = Column(String(50), nullable=False)
    rate_value = Column(Numeric(18, 6), nullable=False)
    rate_unit = Column(String(50), nullable=False)
    rate_version = Column(String(50), nullable=False)
    currency = Column(String(10), nullable=False)
    total_cost = Column(Numeric(18, 6), nullable=False)
    status = Column(String(20), nullable=False, default="CALCULATED") # CALCULATED, SUPERSEDED
    formula_identifier = Column(String(100), nullable=False, default="DIRECT_RATE_VALUATION")
    formula_expression = Column(String(255), nullable=False, default="total_cost = quantity * rate")
    algorithm_version = Column(String(50), nullable=False, default="1.0")
    provenance_json = Column(JSON, nullable=False)
    created_by = Column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata_json = Column(JSON, nullable=True)

    project = relationship("Project", back_populates="cost_calculations")
    cost_rate = relationship("CostRate", back_populates="calculations")
    boq_item = relationship("BoqItem")
    calculation = relationship("EngineeringCalculation")
    reconciliation = relationship("BoqReconciliation")
    decider = relationship("User", foreign_keys=[decided_by])
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index('ix_cost_calc_project', 'project_id'),
        Index('ix_cost_calc_rate', 'cost_rate_id'),
        Index('ix_cost_calc_status', 'status'),
        Index('ix_cost_calc_basis', 'quantity_basis'),
        Index('uq_cost_calc_active_boq', 'boq_item_id', unique=True, postgresql_where=text("status = 'CALCULATED' AND quantity_basis = 'BOQ_STATED'")),
        Index('uq_cost_calc_active_eng', 'calculation_id', unique=True, postgresql_where=text("status = 'CALCULATED' AND quantity_basis = 'ENGINEERING_CALCULATED'")),
        Index('uq_cost_calc_active_rec', 'reconciliation_id', unique=True, postgresql_where=text("status = 'CALCULATED' AND quantity_basis = 'VERIFIED_RECONCILED'")),
        CheckConstraint('quantity_value >= 0', name='ck_cost_calc_qty_val_nonneg'),
        CheckConstraint('rate_value >= 0', name='ck_cost_calc_rate_val_nonneg'),
        CheckConstraint('total_cost >= 0', name='ck_cost_calc_total_cost_nonneg'),
        CheckConstraint("quantity_basis IN ('BOQ_STATED', 'ENGINEERING_CALCULATED', 'VERIFIED_RECONCILED')", name='ck_cost_calc_qty_basis'),
        CheckConstraint("status IN ('CALCULATED', 'SUPERSEDED')", name='ck_cost_calc_status'),
        CheckConstraint(
            "(quantity_basis = 'BOQ_STATED' AND boq_item_id IS NOT NULL AND calculation_id IS NULL AND reconciliation_id IS NULL AND reconciliation_decision IS NULL AND decision_reason IS NULL AND decided_by IS NULL AND decided_at IS NULL) OR "
            "(quantity_basis = 'ENGINEERING_CALCULATED' AND calculation_id IS NOT NULL AND boq_item_id IS NULL AND reconciliation_id IS NULL AND reconciliation_decision IS NULL AND decision_reason IS NULL AND decided_by IS NULL AND decided_at IS NULL) OR "
            "(quantity_basis = 'VERIFIED_RECONCILED' AND reconciliation_id IS NOT NULL AND boq_item_id IS NULL AND calculation_id IS NULL AND reconciliation_decision IS NOT NULL AND reconciliation_decision IN ('ACCEPT_MATCH', 'ACCEPT_CALCULATED', 'ACCEPT_BOQ') AND decision_reason IS NOT NULL AND decided_by IS NOT NULL AND decided_at IS NOT NULL)",
            name='ck_cost_calc_basis_sources'
        ),
    )


# ==============================================================================
# PHASE 1L: SITE PROGRESS VALUATION & CERTIFIED PROGRESS FOUNDATION
# ==============================================================================

class ActivityRateMapping(Base):
    __tablename__ = "activity_rate_mappings"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    activity_id = Column(String, ForeignKey("construction_activities.id", ondelete="CASCADE"), nullable=False)
    cost_rate_id = Column(String, ForeignKey("cost_rates.id", ondelete="RESTRICT"), nullable=False)
    rate_value = Column(Numeric(18, 6), nullable=False)
    rate_unit = Column(String(50), nullable=False)
    rate_version = Column(String(50), nullable=False)
    currency = Column(String(10), nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE") # ACTIVE, SUPERSEDED
    effective_from = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="activity_rate_mappings")
    activity = relationship("ConstructionActivity", back_populates="rate_mappings")
    cost_rate = relationship("CostRate")
    creator = relationship("User", foreign_keys=[created_by])
    valuations = relationship("DailyProgressValuation", back_populates="activity_rate_mapping")

    __table_args__ = (
        Index('ix_act_rate_map_project', 'project_id'),
        Index('ix_act_rate_map_activity', 'activity_id'),
        Index('ix_act_rate_map_cost_rate', 'cost_rate_id'),
        Index('ix_act_rate_map_status', 'status'),
        Index('uq_act_rate_map_active', 'activity_id', unique=True, postgresql_where=text("status = 'ACTIVE'")),
        CheckConstraint('rate_value > 0', name='ck_act_rate_map_rate_val_positive'),
        CheckConstraint("status IN ('ACTIVE', 'SUPERSEDED')", name='ck_act_rate_map_status'),
    )


class DailyProgressValuation(Base):
    __tablename__ = "daily_progress_valuations"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    verification_id = Column(String, ForeignKey("daily_activity_progress_verifications.id", ondelete="RESTRICT"), unique=True, nullable=False)
    activity_rate_mapping_id = Column(String, ForeignKey("activity_rate_mappings.id", ondelete="RESTRICT"), nullable=False)
    contractor_claimed_quantity = Column(Numeric(18, 6), nullable=False)
    supervisor_certified_quantity = Column(Numeric(18, 6), nullable=False)
    quantity_unit = Column(String(50), nullable=False)
    unit_conversion_factor = Column(Numeric(18, 6), nullable=False, default=1.0)
    applied_rate_value = Column(Numeric(18, 6), nullable=False)
    applied_rate_unit = Column(String(50), nullable=False)
    currency = Column(String(10), nullable=False)
    contractor_claimed_value = Column(Numeric(18, 4), nullable=False)
    certified_progress_value = Column(Numeric(18, 4), nullable=False)
    discrepancy_quantity = Column(Numeric(18, 6), nullable=False) # Signed Qc - Qs
    disputed_valuation_exposure = Column(Numeric(18, 4), nullable=False) # max(0, Qc - Qs) * R
    certified_certificate_id = Column(String, ForeignKey("period_progress_certificates.id", ondelete="RESTRICT"), nullable=True)
    valuation_status = Column(String(20), nullable=False, default="ACTIVE") # ACTIVE, SUPERSEDED
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="daily_progress_valuations")
    verification = relationship("DailyActivityProgressVerification", back_populates="valuation")
    activity_rate_mapping = relationship("ActivityRateMapping", back_populates="valuations")
    certified_certificate = relationship("PeriodProgressCertificate", back_populates="bound_valuations", foreign_keys=[certified_certificate_id])
    certificate_items = relationship("PeriodCertificateItem", back_populates="valuation")

    __table_args__ = (
        Index('ix_dpv_project', 'project_id'),
        Index('ix_dpv_verification', 'verification_id'),
        Index('ix_dpv_mapping', 'activity_rate_mapping_id'),
        Index('ix_dpv_status', 'valuation_status'),
        Index('ix_dpv_cert_binding', 'certified_certificate_id'),
        CheckConstraint('contractor_claimed_quantity >= 0', name='ck_dpv_claimed_qty_nonneg'),
        CheckConstraint('supervisor_certified_quantity >= 0', name='ck_dpv_certified_qty_nonneg'),
        CheckConstraint('applied_rate_value > 0', name='ck_dpv_applied_rate_positive'),
        CheckConstraint('contractor_claimed_value >= 0', name='ck_dpv_claimed_val_nonneg'),
        CheckConstraint('certified_progress_value >= 0', name='ck_dpv_certified_val_nonneg'),
        CheckConstraint('disputed_valuation_exposure >= 0', name='ck_dpv_disputed_exposure_nonneg'),
        CheckConstraint("valuation_status IN ('ACTIVE', 'SUPERSEDED')", name='ck_dpv_status'),
    )


class PeriodProgressCertificate(Base):
    __tablename__ = "period_progress_certificates"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    certificate_number = Column(String(100), nullable=False)
    certificate_type = Column(String(30), nullable=False, default="PERIOD_SNAPSHOT")
    monitoring_baseline_id = Column(String, ForeignKey("monitoring_baselines.id", ondelete="RESTRICT"), nullable=False)
    baseline_schedule_id = Column(String, nullable=False)
    baseline_schedule_version = Column(String(50), nullable=False)
    baseline_schedule_algorithm_version = Column(String(50), nullable=False)
    baseline_start_date = Column(Date, nullable=False)
    period_start_date = Column(Date, nullable=False)
    period_cut_off_date = Column(Date, nullable=False)
    certificate_status = Column(String(20), nullable=False, default="DRAFT") # DRAFT, CERTIFIED, SUPERSEDED
    currency = Column(String(10), nullable=False)
    period_claimed_value = Column(Numeric(18, 4), nullable=False, default=0)
    period_certified_value = Column(Numeric(18, 4), nullable=False, default=0)
    period_disputed_exposure = Column(Numeric(18, 4), nullable=False, default=0)
    cumulative_claimed_value = Column(Numeric(18, 4), nullable=False, default=0)
    cumulative_certified_value = Column(Numeric(18, 4), nullable=False, default=0)
    cumulative_disputed_exposure = Column(Numeric(18, 4), nullable=False, default=0)
    item_count = Column(Integer, nullable=False, default=0)
    valuation_snapshot_hash = Column(String(64), nullable=False)
    algorithm_version = Column(String(20), nullable=False, default="1.0")
    certified_by = Column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    certified_at = Column(DateTime(timezone=True), nullable=True)
    superseded_by = Column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    superseded_at = Column(DateTime(timezone=True), nullable=True)
    supersession_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="period_progress_certificates")
    monitoring_baseline = relationship("MonitoringBaseline")
    certifier = relationship("User", foreign_keys=[certified_by])
    superseder = relationship("User", foreign_keys=[superseded_by])
    items = relationship("PeriodCertificateItem", back_populates="certificate", cascade="all, delete-orphan")
    bound_valuations = relationship("DailyProgressValuation", back_populates="certified_certificate", foreign_keys="DailyProgressValuation.certified_certificate_id")
    reconciliation_snapshots = relationship("BoqReconciliationSnapshot", back_populates="certificate", cascade="all, delete-orphan")
    material_consumption_entries = relationship("MaterialConsumptionEntry", back_populates="certificate", cascade="all, delete-orphan")
    theoretical_consumption_items = relationship("TheoreticalConsumptionItem", back_populates="certificate", cascade="all, delete-orphan")
    material_reconciliation_reports = relationship("MaterialReconciliationReport", back_populates="certificate", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('project_id', 'certificate_number', name='uq_project_certificate_number'),
        Index('ix_ppc_project', 'project_id'),
        Index('ix_ppc_status', 'certificate_status'),
        Index('ix_ppc_dates', 'project_id', 'period_start_date', 'period_cut_off_date'),
        CheckConstraint("period_start_date <= period_cut_off_date", name='ck_ppc_date_window'),
        CheckConstraint("certificate_status IN ('DRAFT', 'CERTIFIED', 'SUPERSEDED')", name='ck_ppc_status'),
        CheckConstraint("item_count >= 0", name='ck_ppc_item_count_nonneg'),
    )


class PeriodCertificateItem(Base):
    __tablename__ = "period_certificate_items"
    id = Column(String, primary_key=True, default=generate_uuid)
    certificate_id = Column(String, ForeignKey("period_progress_certificates.id", ondelete="CASCADE"), nullable=False)
    valuation_id = Column(String, ForeignKey("daily_progress_valuations.id", ondelete="RESTRICT"), nullable=False)
    activity_id = Column(String, ForeignKey("construction_activities.id", ondelete="RESTRICT"), nullable=False)
    claimed_quantity = Column(Numeric(18, 6), nullable=False)
    certified_quantity = Column(Numeric(18, 6), nullable=False)
    quantity_unit = Column(String(50), nullable=False)
    unit_conversion_factor = Column(Numeric(18, 6), nullable=False, default=1.0)
    applied_rate = Column(Numeric(18, 6), nullable=False)
    applied_rate_unit = Column(String(50), nullable=False)
    currency = Column(String(10), nullable=False)
    claimed_amount = Column(Numeric(18, 4), nullable=False)
    certified_amount = Column(Numeric(18, 4), nullable=False)
    discrepancy_quantity = Column(Numeric(18, 6), nullable=False)
    disputed_exposure = Column(Numeric(18, 4), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    certificate = relationship("PeriodProgressCertificate", back_populates="items")
    valuation = relationship("DailyProgressValuation", back_populates="certificate_items")
    activity = relationship("ConstructionActivity")

    __table_args__ = (
        UniqueConstraint('certificate_id', 'valuation_id', name='uq_cert_items_cert_val'),
        Index('ix_pci_certificate', 'certificate_id'),
        Index('ix_pci_valuation', 'valuation_id'),
        Index('ix_pci_activity', 'activity_id'),
        CheckConstraint("claimed_quantity >= 0", name='ck_pci_claimed_qty_nonneg'),
        CheckConstraint("certified_quantity >= 0", name='ck_pci_certified_qty_nonneg'),
        CheckConstraint("applied_rate > 0", name='ck_pci_applied_rate_positive'),
        CheckConstraint("claimed_amount >= 0", name='ck_pci_claimed_amt_nonneg'),
        CheckConstraint("certified_amount >= 0", name='ck_pci_certified_amt_nonneg'),
        CheckConstraint("disputed_exposure >= 0", name='ck_pci_disputed_exposure_nonneg'),
    )


# ==============================================================================
# Phase 1M Models: BOQ Quantity-to-Execution Reconciliation & Variations
# ==============================================================================

class ContractExecutionItem(Base):
    __tablename__ = "contract_execution_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    boq_item_id = Column(String(36), ForeignKey("boq_items.id", ondelete="RESTRICT"), nullable=True)
    originating_cvo_id = Column(String(36), ForeignKey("contract_variation_orders.id", ondelete="RESTRICT"), nullable=True)
    item_origin = Column(String(32), nullable=False)  # ORIGINAL_BOQ, EXTRA_ITEM
    item_code = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    unit_of_measure = Column(String(32), nullable=False)
    original_contract_quantity = Column(Numeric(16, 4), nullable=False)
    effective_contract_quantity = Column(Numeric(16, 4), nullable=False)
    original_contract_rate = Column(Numeric(16, 4), nullable=False)
    current_contract_rate = Column(Numeric(16, 4), nullable=False)
    currency = Column(String(8), nullable=False, default="INR")
    effective_date = Column(Date, nullable=False)
    superseded_at = Column(DateTime(timezone=True), nullable=True)
    superseding_item_id = Column(String(36), ForeignKey("contract_execution_items.id", ondelete="RESTRICT"), nullable=True)
    status = Column(String(32), nullable=False, default="ACTIVE")  # ACTIVE, SUPERSEDED, CLOSED
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("Project", back_populates="contract_execution_items")
    boq_item = relationship("BoqItem", back_populates="contract_execution_item")
    originating_cvo = relationship("ContractVariationOrder", foreign_keys=[originating_cvo_id], back_populates="originated_extra_item")
    superseding_item = relationship("ContractExecutionItem", remote_side=[id], foreign_keys=[superseding_item_id])
    activity_mappings = relationship("ActivityContractMapping", back_populates="contract_execution_item", cascade="all, delete-orphan")
    variation_orders = relationship("ContractVariationOrder", foreign_keys="ContractVariationOrder.contract_execution_item_id", back_populates="contract_execution_item")
    reconciliation_snapshots = relationship("BoqReconciliationSnapshot", back_populates="contract_execution_item", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_cei_project_lookup", "project_id", "effective_date"),
        Index("uq_cei_active_item_code", "project_id", "item_code", unique=True, postgresql_where=text("status = 'ACTIVE'")),
        Index("uq_cei_boq_item_id", "boq_item_id", unique=True, postgresql_where=text("item_origin = 'ORIGINAL_BOQ'")),
        Index("uq_cei_originating_cvo", "originating_cvo_id", unique=True, postgresql_where=text("item_origin = 'EXTRA_ITEM'")),
        CheckConstraint("item_origin IN ('ORIGINAL_BOQ', 'EXTRA_ITEM')", name="chk_cei_item_origin"),
        CheckConstraint("status IN ('ACTIVE', 'SUPERSEDED', 'CLOSED')", name="chk_cei_status"),
        CheckConstraint("original_contract_quantity >= 0 AND effective_contract_quantity >= 0", name="chk_cei_quantities"),
        CheckConstraint("original_contract_rate > 0 AND current_contract_rate > 0", name="chk_cei_rates"),
        CheckConstraint(
            "(item_origin = 'ORIGINAL_BOQ' AND boq_item_id IS NOT NULL AND originating_cvo_id IS NULL) OR "
            "(item_origin = 'EXTRA_ITEM' AND boq_item_id IS NULL AND originating_cvo_id IS NOT NULL)",
            name="chk_cei_origin_identity"
        ),
        CheckConstraint(
            "(status = 'SUPERSEDED' AND superseded_at IS NOT NULL AND superseding_item_id IS NOT NULL) OR "
            "(status != 'SUPERSEDED' AND superseded_at IS NULL AND superseding_item_id IS NULL)",
            name="chk_cei_supersession"
        ),
    )


class ActivityContractMapping(Base):
    __tablename__ = "activity_contract_mappings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    activity_id = Column(String(36), ForeignKey("construction_activities.id", ondelete="RESTRICT"), nullable=False)
    contract_execution_item_id = Column(String(36), ForeignKey("contract_execution_items.id", ondelete="RESTRICT"), nullable=False)
    allocation_percentage = Column(Numeric(6, 2), nullable=False, default=100.00)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("Project", back_populates="activity_contract_mappings")
    activity = relationship("ConstructionActivity", back_populates="activity_contract_mappings")
    contract_execution_item = relationship("ContractExecutionItem", back_populates="activity_mappings")

    __table_args__ = (
        Index("idx_acm_activity_temporal", "activity_id", "effective_from", "effective_to"),
        Index("idx_acm_cei_temporal", "contract_execution_item_id", "effective_from", "effective_to"),
        CheckConstraint("allocation_percentage > 0.00 AND allocation_percentage <= 100.00", name="chk_acm_percentage"),
        CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="chk_acm_date_range"),
    )


class ContractVariationOrder(Base):
    __tablename__ = "contract_variation_orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    contract_execution_item_id = Column(String(36), ForeignKey("contract_execution_items.id", ondelete="RESTRICT"), nullable=True)
    variation_number = Column(String(64), nullable=False)
    variation_type = Column(String(32), nullable=False)  # QUANTITY_VARIATION, RATE_REVISION, EXTRA_ITEM_ADDITION, SCOPE_OMISSION
    unit_of_measure = Column(String(32), nullable=False)
    quantity_delta = Column(Numeric(16, 4), nullable=False, default=0.0000)
    rate_previous = Column(Numeric(16, 4), nullable=False)
    rate_revised = Column(Numeric(16, 4), nullable=False)
    net_variation_amount = Column(Numeric(18, 4), nullable=True)
    effective_date = Column(Date, nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    status = Column(String(32), nullable=False, default="DRAFT")  # DRAFT, SUBMITTED, APPROVED, REJECTED
    description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("Project", back_populates="contract_variation_orders")
    contract_execution_item = relationship("ContractExecutionItem", foreign_keys=[contract_execution_item_id], back_populates="variation_orders")
    originated_extra_item = relationship("ContractExecutionItem", foreign_keys="ContractExecutionItem.originating_cvo_id", back_populates="originating_cvo", uselist=False)
    approved_by_user = relationship("User", foreign_keys=[approved_by_user_id])

    __table_args__ = (
        Index("idx_cvo_item_temporal", "contract_execution_item_id", "effective_date", "approved_at"),
        Index("uq_cvo_project_number", "project_id", "variation_number", unique=True),
        Index("uq_cvo_extra_item_cei", "contract_execution_item_id", unique=True, postgresql_where=text("variation_type = 'EXTRA_ITEM_ADDITION' AND status = 'APPROVED'")),
        CheckConstraint("variation_type IN ('QUANTITY_VARIATION', 'RATE_REVISION', 'EXTRA_ITEM_ADDITION', 'SCOPE_OMISSION')", name="chk_cvo_type"),
        CheckConstraint("status IN ('DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED')", name="chk_cvo_status"),
        CheckConstraint("rate_previous > 0 AND rate_revised > 0", name="chk_cvo_rates"),
        CheckConstraint(
            "(variation_type IN ('QUANTITY_VARIATION', 'SCOPE_OMISSION', 'EXTRA_ITEM_ADDITION') AND rate_previous = rate_revised) OR "
            "(variation_type = 'RATE_REVISION' AND rate_previous != rate_revised)",
            name="chk_cvo_rate_semantics"
        ),
        CheckConstraint(
            "(variation_type = 'EXTRA_ITEM_ADDITION' AND quantity_delta > 0) OR "
            "(variation_type = 'SCOPE_OMISSION' AND quantity_delta < 0) OR "
            "(variation_type = 'QUANTITY_VARIATION' AND quantity_delta != 0) OR "
            "(variation_type = 'RATE_REVISION' AND quantity_delta = 0)",
            name="chk_cvo_type_deltas"
        ),
        CheckConstraint(
            """(variation_type = 'EXTRA_ITEM_ADDITION' AND status IN ('DRAFT', 'SUBMITTED', 'REJECTED') 
                AND contract_execution_item_id IS NULL AND approved_at IS NULL AND approved_by_user_id IS NULL AND net_variation_amount IS NULL) OR
            (variation_type = 'EXTRA_ITEM_ADDITION' AND status = 'APPROVED' 
                AND contract_execution_item_id IS NOT NULL AND approved_at IS NOT NULL AND approved_by_user_id IS NOT NULL AND net_variation_amount IS NOT NULL) OR
            (variation_type != 'EXTRA_ITEM_ADDITION' AND status IN ('DRAFT', 'SUBMITTED', 'REJECTED') 
                AND contract_execution_item_id IS NOT NULL AND approved_at IS NULL AND approved_by_user_id IS NULL AND net_variation_amount IS NULL) OR
            (variation_type != 'EXTRA_ITEM_ADDITION' AND status = 'APPROVED' 
                AND contract_execution_item_id IS NOT NULL AND approved_at IS NOT NULL AND approved_by_user_id IS NOT NULL AND net_variation_amount IS NOT NULL)""",
            name="chk_cvo_lifecycle_rules"
        ),
    )


class BoqReconciliationSnapshot(Base):
    __tablename__ = "boq_reconciliation_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    certificate_id = Column(String(36), ForeignKey("period_progress_certificates.id", ondelete="RESTRICT"), nullable=False)
    contract_execution_item_id = Column(String(36), ForeignKey("contract_execution_items.id", ondelete="RESTRICT"), nullable=False)
    effective_contract_quantity = Column(Numeric(16, 4), nullable=False)
    cumulative_executed_quantity = Column(Numeric(16, 4), nullable=False)
    cumulative_executed_quantity_boq_unit = Column(Numeric(16, 4), nullable=False)
    gross_over_execution_quantity = Column(Numeric(16, 4), nullable=False)
    critical_deviation_quantity = Column(Numeric(16, 4), nullable=False)
    reconciliation_rate = Column(Numeric(16, 4), nullable=False)
    historical_period_valuation = Column(Numeric(18, 4), nullable=False)
    current_rate_valuation = Column(Numeric(18, 4), nullable=False)
    valuation_delta = Column(Numeric(18, 4), nullable=False)
    is_critical_deviation = Column(Boolean, nullable=False, default=False)
    snapshot_hash = Column(String(64), nullable=False)
    verified_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="boq_reconciliation_snapshots")
    certificate = relationship("PeriodProgressCertificate", back_populates="reconciliation_snapshots")
    contract_execution_item = relationship("ContractExecutionItem", back_populates="reconciliation_snapshots")

    __table_args__ = (
        Index("uq_brs_cert_item", "certificate_id", "contract_execution_item_id", unique=True),
        Index("idx_brs_project_cert", "project_id", "certificate_id"),
        CheckConstraint(
            "effective_contract_quantity >= 0 AND cumulative_executed_quantity >= 0 AND "
            "cumulative_executed_quantity_boq_unit >= 0 AND gross_over_execution_quantity >= 0 AND "
            "critical_deviation_quantity >= 0",
            name="chk_brs_quantities"
        ),
        CheckConstraint("historical_period_valuation >= 0 AND current_rate_valuation >= 0", name="chk_brs_valuation"),
    )


# ==============================================================================
# PHASE 1N: MATERIAL REQUIREMENTS PLANNING, MIX FORMULATION & RECONCILIATION
# ==============================================================================

class MaterialItem(Base):
    __tablename__ = "material_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=True)
    material_code = Column(String(50), nullable=False)
    material_name = Column(String(100), nullable=False)
    material_category = Column(String(50), nullable=False)
    standard_unit = Column(String(20), nullable=False)
    density_kg_per_unit = Column(Numeric(12, 4), nullable=True)
    standard_permissible_waste_pct = Column(Numeric(5, 2), nullable=False, default=0.00)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="material_items")

    __table_args__ = (
        Index("ix_mat_items_proj", "project_id"),
        Index("ix_mat_items_category", "material_category"),
        CheckConstraint(
            "material_category IN ('BINDER', 'AGGREGATE', 'REINFORCEMENT', 'MASONRY', 'CHEMICAL', 'WATER', 'TIMBER', 'STEEL_SECTION')",
            name="ck_mat_item_category"
        ),
        CheckConstraint(
            "standard_unit IN ('BAG', 'KG', 'MT', 'M3', 'LITRE', 'NOS', 'SQM')",
            name="ck_mat_item_unit"
        ),
        CheckConstraint(
            "standard_permissible_waste_pct >= 0.00 AND standard_permissible_waste_pct <= 100.00",
            name="ck_mat_item_waste"
        ),
        CheckConstraint(
            "density_kg_per_unit IS NULL OR density_kg_per_unit >= 0",
            name="ck_mat_item_density"
        ),
    )


class MaterialMixDesign(Base):
    __tablename__ = "material_mix_designs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    mix_code = Column(String(50), nullable=False)
    grade_designation = Column(String(50), nullable=False)
    mix_type = Column(String(30), nullable=False)
    rule_code = Column(String(50), nullable=True)
    source_document_id = Column(String(36), ForeignKey("documents.id", ondelete="RESTRICT"), nullable=True)
    evidence_id = Column(String(36), ForeignKey("evidence.id", ondelete="RESTRICT"), nullable=True)
    dry_volume_factor = Column(Numeric(6, 4), nullable=False, default=1.5400)
    water_cement_ratio = Column(Numeric(5, 3), nullable=True)
    classification = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default="DRAFT")
    approved_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="material_mix_designs")
    source_document = relationship("Document", foreign_keys=[source_document_id])
    evidence = relationship("Evidence", foreign_keys=[evidence_id])
    approver = relationship("User", foreign_keys=[approved_by])
    constituents = relationship("MaterialMixConstituent", back_populates="mix_design", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_mmd_project", "project_id"),
        Index("ix_mmd_status", "status"),
        Index("uq_mmd_proj_code", "project_id", "mix_code", unique=True),
        CheckConstraint("mix_type IN ('DESIGN_MIX', 'NOMINAL_MIX')", name="ck_mmd_type"),
        CheckConstraint("status IN ('DRAFT', 'APPROVED', 'SUPERSEDED')", name="ck_mmd_status"),
        CheckConstraint("classification IN ('CALCULATED', 'DERIVED', 'ASSUMPTION_BASED')", name="ck_mmd_classification"),
        CheckConstraint("dry_volume_factor > 0", name="ck_mmd_dry_vol_factor"),
        CheckConstraint("water_cement_ratio IS NULL OR water_cement_ratio > 0", name="ck_mmd_wc_ratio"),
        CheckConstraint("status != 'APPROVED' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)", name="ck_mmd_approval"),
        CheckConstraint("mix_type != 'DESIGN_MIX' OR (source_document_id IS NOT NULL AND evidence_id IS NOT NULL)", name="ck_mmd_design_mix_evidence"),
        CheckConstraint("mix_type != 'NOMINAL_MIX' OR (classification = 'ASSUMPTION_BASED' AND rule_code IS NOT NULL)", name="ck_mmd_nominal_mix_rule"),
    )


class MaterialMixConstituent(Base):
    __tablename__ = "material_mix_constituents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    mix_design_id = Column(String(36), ForeignKey("material_mix_designs.id", ondelete="CASCADE"), nullable=False)
    material_item_id = Column(String(36), ForeignKey("material_items.id", ondelete="RESTRICT"), nullable=False)
    quantity_per_m3 = Column(Numeric(14, 6), nullable=False)
    unit = Column(String(20), nullable=False)

    mix_design = relationship("MaterialMixDesign", back_populates="constituents")
    material_item = relationship("MaterialItem")

    __table_args__ = (
        Index("ix_mmc_mix", "mix_design_id"),
        Index("ix_mmc_mat", "material_item_id"),
        Index("uq_mmc_mix_material", "mix_design_id", "material_item_id", unique=True),
        CheckConstraint("quantity_per_m3 > 0", name="ck_mmc_qty_positive"),
    )


class MaterialPlan(Base):
    __tablename__ = "material_plans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    baseline_id = Column(String(36), ForeignKey("monitoring_baselines.id", ondelete="RESTRICT"), nullable=False)
    material_item_id = Column(String(36), ForeignKey("material_items.id", ondelete="RESTRICT"), nullable=False)
    activity_id = Column(String(36), ForeignKey("construction_activities.id", ondelete="RESTRICT"), nullable=False)
    mix_design_id = Column(String(36), ForeignKey("material_mix_designs.id", ondelete="RESTRICT"), nullable=False)
    planned_quantity = Column(Numeric(18, 4), nullable=False)
    unit = Column(String(20), nullable=False)
    estimation_method = Column(String(30), nullable=False)
    waste_allowance_pct = Column(Numeric(5, 2), nullable=False, default=0.00)
    gross_planned_quantity = Column(Numeric(18, 4), nullable=False)
    provenance_metadata = Column(JSON, nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="material_plans")
    baseline = relationship("MonitoringBaseline")
    material_item = relationship("MaterialItem")
    activity = relationship("ConstructionActivity")
    mix_design = relationship("MaterialMixDesign")

    __table_args__ = (
        Index("ix_mat_plans_project", "project_id"),
        Index("ix_mat_plans_baseline", "baseline_id"),
        Index("ix_mat_plans_activity", "activity_id"),
        Index("ix_mat_plans_material", "material_item_id"),
        CheckConstraint("estimation_method IN ('CALCULATED', 'DERIVED', 'ASSUMPTION_BASED', 'USER_PROVIDED')", name="ck_mat_plan_method"),
        CheckConstraint("status IN ('ACTIVE', 'SUPERSEDED')", name="ck_mat_plan_status"),
        CheckConstraint("planned_quantity >= 0 AND gross_planned_quantity >= planned_quantity", name="ck_mat_plan_quantities"),
    )


class MaterialConsumptionEntry(Base):
    __tablename__ = "material_consumption_entries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    certificate_id = Column(String(36), ForeignKey("period_progress_certificates.id", ondelete="RESTRICT"), nullable=False)
    material_item_id = Column(String(36), ForeignKey("material_items.id", ondelete="RESTRICT"), nullable=False)
    store_challan_reference = Column(String(100), nullable=False)
    consumption_date_start = Column(Date, nullable=False)
    consumption_date_end = Column(Date, nullable=False)
    contractor_declared_quantity = Column(Numeric(18, 4), nullable=False)
    supervisor_verified_quantity = Column(Numeric(18, 4), nullable=True)
    discrepancy_quantity = Column(Numeric(18, 4), nullable=False, default=0.0000)
    is_disputed = Column(Boolean, nullable=False, default=False)
    unit = Column(String(20), nullable=False)
    submission_status = Column(String(20), nullable=False, default="SUBMITTED")
    supporting_document_id = Column(String(36), ForeignKey("documents.id", ondelete="RESTRICT"), nullable=True)
    submitted_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    verified_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="material_consumption_entries")
    certificate = relationship("PeriodProgressCertificate", back_populates="material_consumption_entries")
    material_item = relationship("MaterialItem")
    supporting_document = relationship("Document", foreign_keys=[supporting_document_id])
    submitter = relationship("User", foreign_keys=[submitted_by])
    verifier = relationship("User", foreign_keys=[verified_by])

    __table_args__ = (
        Index("ix_mce_proj_cert", "project_id", "certificate_id"),
        Index("ix_mce_material", "material_item_id"),
        Index("ix_mce_status", "submission_status"),
        Index("uq_mce_challan", "project_id", "store_challan_reference", unique=True),
        CheckConstraint("consumption_date_start <= consumption_date_end", name="ck_mce_dates"),
        CheckConstraint("submission_status IN ('SUBMITTED', 'VERIFIED', 'REJECTED')", name="ck_mce_status"),
        CheckConstraint("contractor_declared_quantity >= 0 AND (supervisor_verified_quantity IS NULL OR supervisor_verified_quantity >= 0)", name="ck_mce_quantities"),
        CheckConstraint("submission_status != 'VERIFIED' OR (supervisor_verified_quantity IS NOT NULL AND verified_by IS NOT NULL AND verified_at IS NOT NULL)", name="ck_mce_verified_fields"),
    )


class TheoreticalConsumptionItem(Base):
    __tablename__ = "theoretical_consumption_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    certificate_id = Column(String(36), ForeignKey("period_progress_certificates.id", ondelete="RESTRICT"), nullable=False)
    certificate_item_id = Column(String(36), ForeignKey("period_certificate_items.id", ondelete="RESTRICT"), nullable=False)
    activity_id = Column(String(36), ForeignKey("construction_activities.id", ondelete="RESTRICT"), nullable=False)
    material_item_id = Column(String(36), ForeignKey("material_items.id", ondelete="RESTRICT"), nullable=False)
    mix_design_id = Column(String(36), ForeignKey("material_mix_designs.id", ondelete="RESTRICT"), nullable=False)
    certified_activity_volume = Column(Numeric(18, 6), nullable=False)
    coefficient_per_unit = Column(Numeric(14, 6), nullable=False)
    dry_volume_factor = Column(Numeric(6, 4), nullable=False)
    theoretical_quantity = Column(Numeric(18, 4), nullable=False)
    unit = Column(String(20), nullable=False)
    mix_design_version = Column(String(50), nullable=False)
    calculation_algorithm_version = Column(String(20), nullable=False, default="1.0-DETERMINISTIC")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="theoretical_consumption_items")
    certificate = relationship("PeriodProgressCertificate", back_populates="theoretical_consumption_items")
    certificate_item = relationship("PeriodCertificateItem")
    activity = relationship("ConstructionActivity")
    material_item = relationship("MaterialItem")
    mix_design = relationship("MaterialMixDesign")

    __table_args__ = (
        Index("ix_tci_cert_material", "certificate_id", "material_item_id"),
        Index("ix_tci_activity", "activity_id"),
        Index("ix_tci_cert_item", "certificate_item_id"),
        CheckConstraint("certified_activity_volume >= 0 AND coefficient_per_unit > 0 AND theoretical_quantity >= 0", name="ck_tci_quantities"),
    )


class MaterialReconciliationReport(Base):
    __tablename__ = "material_reconciliation_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    certificate_id = Column(String(36), ForeignKey("period_progress_certificates.id", ondelete="RESTRICT"), nullable=False)
    material_item_id = Column(String(36), ForeignKey("material_items.id", ondelete="RESTRICT"), nullable=False)
    revision_number = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="DRAFT")
    cumulative_theoretical_quantity = Column(Numeric(18, 4), nullable=False)
    cumulative_actual_quantity = Column(Numeric(18, 4), nullable=False)
    variance_quantity = Column(Numeric(18, 4), nullable=False)
    variance_percentage = Column(Numeric(8, 4), nullable=False)
    is_saving = Column(Boolean, nullable=False, default=False)
    permissible_waste_percentage = Column(Numeric(5, 2), nullable=False)
    permissible_waste_quantity = Column(Numeric(18, 4), nullable=False)
    unauthorized_wastage_quantity = Column(Numeric(18, 4), nullable=False)
    is_excess_flagged = Column(Boolean, nullable=False, default=False)
    reconciliation_hash = Column(String(64), nullable=False)
    finalized_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    finalized_at = Column(DateTime(timezone=True), nullable=True)
    supersedes_report_id = Column(String(36), ForeignKey("material_reconciliation_reports.id", ondelete="RESTRICT"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="material_reconciliation_reports")
    certificate = relationship("PeriodProgressCertificate", back_populates="material_reconciliation_reports")
    material_item = relationship("MaterialItem")
    finalizer = relationship("User", foreign_keys=[finalized_by])
    superseded_report = relationship("MaterialReconciliationReport", remote_side=[id])

    __table_args__ = (
        Index("ix_mrr_proj_cert", "project_id", "certificate_id"),
        Index("ix_mrr_material", "material_item_id"),
        Index("uq_mrr_cert_material_rev", "certificate_id", "material_item_id", "revision_number", unique=True),
        CheckConstraint("status IN ('DRAFT', 'FINALIZED', 'SUPERSEDED')", name="ck_mrr_status"),
        CheckConstraint(
            "cumulative_theoretical_quantity >= 0 AND cumulative_actual_quantity >= 0 AND permissible_waste_quantity >= 0 AND unauthorized_wastage_quantity >= 0",
            name="ck_mrr_quantities"
        ),
        CheckConstraint("status != 'FINALIZED' OR (finalized_by IS NOT NULL AND finalized_at IS NOT NULL)", name="ck_mrr_finalized_fields"),
    )
# ==============================================================================
# PHASE 1O: CONTRACTOR RESOURCE & PROCUREMENT PLANNING FOUNDATION
# ==============================================================================

class MaterialRequirementPlan(Base):
    __tablename__ = "material_requirement_plans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    baseline_id = Column(String(36), ForeignKey("monitoring_baselines.id", ondelete="RESTRICT"), nullable=False)
    plan_version = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="DRAFT")  # DRAFT, ACTIVE, SUPERSEDED
    planning_start_date = Column(Date, nullable=True)
    planning_end_date = Column(Date, nullable=True)
    algorithm_version = Column(String(50), nullable=False, default="MRP_1.0")
    input_snapshot_json = Column(JSON, nullable=False)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    superseded_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(JSON, nullable=True)

    project = relationship("Project")
    baseline = relationship("MonitoringBaseline")
    creator = relationship("User")
    items = relationship("MaterialRequirementItem", back_populates="material_requirement_plan", cascade="all, delete-orphan")
    procurement_requirements = relationship("ProcurementRequirement", back_populates="material_requirement_plan", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("project_id", "plan_version", name="uq_mrp_project_version"),
        Index("uq_mrp_active_per_project", "project_id", unique=True, postgresql_where=text("status = 'ACTIVE'")),
        Index("ix_mrp_project", "project_id"),
        Index("ix_mrp_baseline", "baseline_id"),
        Index("ix_mrp_status", "status"),
        CheckConstraint("status IN ('DRAFT', 'ACTIVE', 'SUPERSEDED')", name="ck_mrp_status"),
        CheckConstraint("planning_end_date IS NULL OR planning_start_date IS NULL OR planning_end_date >= planning_start_date", name="ck_mrp_dates"),
    )


class MaterialRequirementItem(Base):
    __tablename__ = "material_requirement_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    material_requirement_plan_id = Column(String(36), ForeignKey("material_requirement_plans.id", ondelete="CASCADE"), nullable=False)
    material_item_id = Column(String(36), ForeignKey("material_items.id", ondelete="RESTRICT"), nullable=False)
    activity_id = Column(String(36), ForeignKey("construction_activities.id", ondelete="RESTRICT"), nullable=False)
    material_plan_id = Column(String(36), ForeignKey("material_plans.id", ondelete="RESTRICT"), nullable=False)
    requirement_quantity = Column(Numeric(18, 4), nullable=False)
    requirement_unit = Column(String(20), nullable=False)
    requirement_date_start = Column(Date, nullable=True)
    requirement_date_end = Column(Date, nullable=True)
    source_quantity = Column(Numeric(18, 4), nullable=False)
    source_unit = Column(String(20), nullable=False)
    conversion_factor = Column(Numeric(18, 6), nullable=False, default=1.000000)
    planning_method = Column(String(50), nullable=False, default="DIRECT_PHASE_1N_DERIVATION")
    classification = Column(String(30), nullable=False, default="CALCULATED")
    provenance_metadata = Column(JSON, nullable=False)
    status = Column(String(20), nullable=False, default="PLANNED")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project")
    material_requirement_plan = relationship("MaterialRequirementPlan", back_populates="items")
    material_item = relationship("MaterialItem")
    activity = relationship("ConstructionActivity")
    material_plan = relationship("MaterialPlan")

    __table_args__ = (
        Index("ix_mri_plan", "material_requirement_plan_id"),
        Index("ix_mri_project", "project_id"),
        Index("ix_mri_material", "material_item_id"),
        Index("ix_mri_activity", "activity_id"),
        Index("ix_mri_mat_plan", "material_plan_id"),
        UniqueConstraint("material_requirement_plan_id", "material_plan_id", name="uq_mri_plan_mat_plan"),
        CheckConstraint("classification IN ('CALCULATED', 'DERIVED', 'ASSUMPTION_BASED', 'USER_PROVIDED', 'REQUIRES_INPUT')", name="ck_mri_classification"),
        CheckConstraint("status IN ('PLANNED', 'REQUIRES_INPUT', 'SUPERSEDED')", name="ck_mri_status"),
        CheckConstraint("requirement_quantity >= 0", name="ck_mri_req_qty_positive"),
        CheckConstraint("source_quantity >= 0", name="ck_mri_src_qty_positive"),
        CheckConstraint("conversion_factor > 0", name="ck_mri_conv_factor_positive"),
        CheckConstraint("requirement_date_end IS NULL OR requirement_date_start IS NULL OR requirement_date_end >= requirement_date_start", name="ck_mri_dates"),
    )


class ProcurementRequirement(Base):
    __tablename__ = "procurement_requirements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    material_requirement_plan_id = Column(String(36), ForeignKey("material_requirement_plans.id", ondelete="CASCADE"), nullable=False)
    material_item_id = Column(String(36), ForeignKey("material_items.id", ondelete="RESTRICT"), nullable=False)
    requirement_period_start = Column(Date, nullable=True)
    requirement_period_end = Column(Date, nullable=True)
    required_quantity = Column(Numeric(18, 4), nullable=False)
    unit = Column(String(20), nullable=False)
    already_planned_quantity = Column(Numeric(18, 4), nullable=True)
    procurement_quantity = Column(Numeric(18, 4), nullable=True)
    planning_method = Column(String(50), nullable=False, default="PERIOD_AGGREGATED_NET_REQUIREMENT")
    status = Column(String(20), nullable=False, default="PLANNED")
    provenance_metadata = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project")
    material_requirement_plan = relationship("MaterialRequirementPlan", back_populates="procurement_requirements")
    material_item = relationship("MaterialItem")

    __table_args__ = (
        Index("ix_procreq_plan", "material_requirement_plan_id"),
        Index("ix_procreq_project", "project_id"),
        Index("ix_procreq_material", "material_item_id"),
        CheckConstraint("status IN ('PLANNED', 'REQUIRES_INPUT', 'SUPERSEDED')", name="ck_procreq_status"),
        CheckConstraint("required_quantity >= 0", name="ck_procreq_req_qty_positive"),
        CheckConstraint("already_planned_quantity IS NULL OR already_planned_quantity >= 0", name="ck_procreq_planned_qty_positive"),
        CheckConstraint("procurement_quantity IS NULL OR procurement_quantity >= 0", name="ck_procreq_proc_qty_positive"),
        CheckConstraint("requirement_period_end IS NULL OR requirement_period_start IS NULL OR requirement_period_end >= requirement_period_start", name="ck_procreq_dates"),
    )


# ==============================================================================
# PHASE 1P: INVENTORY & MATERIAL AVAILABILITY RECONCILIATION FOUNDATION
# ==============================================================================
from decimal import Decimal

class MaterialStockLedger(Base):
    __tablename__ = "material_stock_ledger"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    material_item_id = Column(String(36), ForeignKey("material_items.id", ondelete="RESTRICT"), nullable=False)
    transaction_type = Column(String(30), nullable=False)
    transaction_quantity = Column(Numeric(18, 4), nullable=False)
    unit = Column(String(20), nullable=False)
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(String(100), nullable=True)
    transaction_date = Column(Date, nullable=False)
    source_type = Column(String(50), nullable=False)
    source_reference = Column(String(100), nullable=True)
    is_authoritative = Column(Boolean, nullable=False, default=True)
    verification_status = Column(String(30), nullable=False, default="VERIFIED")
    created_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata_json = Column(JSON, nullable=False, default=dict)

    project = relationship("Project")
    material_item = relationship("MaterialItem")
    creator = relationship("User")

    __table_args__ = (
        Index("ix_stk_ledger_project", "project_id"),
        Index("ix_stk_ledger_material", "material_item_id"),
        Index("ix_stk_ledger_proj_mat", "project_id", "material_item_id"),
        Index("ix_stk_ledger_date", "transaction_date"),
        Index("ix_stk_ledger_type", "transaction_type"),
        Index("ix_stk_ledger_authoritative", "is_authoritative"),
        Index("ix_stk_ledger_verif_status", "verification_status"),
        CheckConstraint(
            "transaction_type IN ('RECEIPT', 'ISSUE', 'ADJUSTMENT_IN', 'ADJUSTMENT_OUT', 'RETURN', 'TRANSFER_IN', 'TRANSFER_OUT')",
            name="ck_stk_ledger_type",
        ),
        CheckConstraint(
            "source_type IN ('CONTRACTOR_DECLARED', 'SUPERVISOR_VERIFIED', 'SUPERVISOR_CORRECTED', 'SYSTEM_ADJUSTED')",
            name="ck_stk_ledger_source",
        ),
        CheckConstraint(
            "verification_status IN ('PENDING_VERIFICATION', 'VERIFIED', 'CORRECTED', 'REJECTED')",
            name="ck_stk_ledger_verif_status",
        ),
        CheckConstraint("transaction_quantity > 0", name="ck_stk_ledger_qty_pos"),
    )


class MaterialStockBalance(Base):
    __tablename__ = "material_stock_balances"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    material_item_id = Column(String(36), ForeignKey("material_items.id", ondelete="RESTRICT"), nullable=False)
    total_received = Column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    total_issued = Column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    total_adjustment_in = Column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    total_adjustment_out = Column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    total_returned = Column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    total_transfer_in = Column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    total_transfer_out = Column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    on_hand_quantity = Column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    reserved_quantity = Column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    available_quantity = Column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    unit = Column(String(20), nullable=False)
    calculation_algorithm_version = Column(String(50), nullable=False, default="STK_1.0")
    provenance_metadata = Column(JSON, nullable=False, default=dict)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("Project")
    material_item = relationship("MaterialItem")

    __table_args__ = (
        UniqueConstraint("project_id", "material_item_id", name="uq_stock_balance_proj_material"),
        Index("ix_stk_balance_project", "project_id"),
        Index("ix_stk_balance_material", "material_item_id"),
        CheckConstraint("on_hand_quantity >= 0", name="ck_stock_balance_on_hand_nonneg"),
        CheckConstraint("reserved_quantity >= 0", name="ck_stock_balance_reserved_nonneg"),
        CheckConstraint("available_quantity >= 0", name="ck_stock_balance_available_nonneg"),
        CheckConstraint("total_received >= 0", name="ck_stock_balance_received_nonneg"),
        CheckConstraint("total_issued >= 0", name="ck_stock_balance_issued_nonneg"),
        CheckConstraint("total_adjustment_in >= 0", name="ck_stock_balance_adj_in_nonneg"),
        CheckConstraint("total_adjustment_out >= 0", name="ck_stock_balance_adj_out_nonneg"),
        CheckConstraint("total_returned >= 0", name="ck_stock_balance_returned_nonneg"),
        CheckConstraint("total_transfer_in >= 0", name="ck_stock_balance_transfer_in_nonneg"),
        CheckConstraint("total_transfer_out >= 0", name="ck_stock_balance_transfer_out_nonneg"),
    )


class MaterialReservation(Base):
    __tablename__ = "material_reservations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    material_item_id = Column(String(36), ForeignKey("material_items.id", ondelete="RESTRICT"), nullable=False)
    material_requirement_plan_id = Column(String(36), ForeignKey("material_requirement_plans.id", ondelete="CASCADE"), nullable=False)
    material_requirement_item_id = Column(String(36), ForeignKey("material_requirement_items.id", ondelete="CASCADE"), nullable=False)
    reserved_quantity = Column(Numeric(18, 4), nullable=False)
    unit = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    reservation_date = Column(Date, nullable=False)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    released_at = Column(DateTime(timezone=True), nullable=True)
    released_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)

    project = relationship("Project")
    material_item = relationship("MaterialItem")
    material_requirement_plan = relationship("MaterialRequirementPlan")
    material_requirement_item = relationship("MaterialRequirementItem")
    creator = relationship("User", foreign_keys=[created_by])
    releaser = relationship("User", foreign_keys=[released_by])

    __table_args__ = (
        Index("ix_mat_res_project", "project_id"),
        Index("ix_mat_res_material", "material_item_id"),
        Index("ix_mat_res_mrp_plan", "material_requirement_plan_id"),
        Index("ix_mat_res_mrp_item", "material_requirement_item_id"),
        Index("ix_mat_res_status", "status"),
        CheckConstraint("status IN ('ACTIVE', 'RELEASED', 'SUPERSEDED')", name="ck_mat_res_status"),
        CheckConstraint("reserved_quantity > 0", name="ck_mat_res_qty_positive"),
    )


class MaterialAvailabilityReconciliation(Base):
    __tablename__ = "material_availability_reconciliations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    material_requirement_plan_id = Column(String(36), ForeignKey("material_requirement_plans.id", ondelete="CASCADE"), nullable=False)
    material_requirement_item_id = Column(String(36), ForeignKey("material_requirement_items.id", ondelete="CASCADE"), nullable=False)
    material_item_id = Column(String(36), ForeignKey("material_items.id", ondelete="RESTRICT"), nullable=False)
    required_quantity = Column(Numeric(18, 4), nullable=False)
    required_unit = Column(String(20), nullable=False)
    on_hand_quantity = Column(Numeric(18, 4), nullable=True)
    reserved_quantity = Column(Numeric(18, 4), nullable=True)
    available_quantity = Column(Numeric(18, 4), nullable=True)
    shortage_quantity = Column(Numeric(18, 4), nullable=True, default=None)
    availability_status = Column(String(30), nullable=False)
    calculation_algorithm_version = Column(String(50), nullable=False, default="AVAIL_1.0")
    provenance_metadata = Column(JSON, nullable=False, default=dict)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    project = relationship("Project")
    material_requirement_plan = relationship("MaterialRequirementPlan")
    material_requirement_item = relationship("MaterialRequirementItem")
    material_item = relationship("MaterialItem")
    creator = relationship("User")

    __table_args__ = (
        Index("ix_avail_recon_project", "project_id"),
        Index("ix_avail_recon_plan", "material_requirement_plan_id"),
        Index("ix_avail_recon_mrp_item", "material_requirement_item_id"),
        Index("ix_avail_recon_material", "material_item_id"),
        Index("ix_avail_recon_status", "availability_status"),
        CheckConstraint(
            "availability_status IN ('AVAILABLE', 'PARTIALLY_AVAILABLE', 'SHORTAGE', 'NO_STOCK_DATA', 'UNIT_MISMATCH', 'REQUIRES_INPUT')",
            name="ck_avail_status",
        ),
        CheckConstraint("shortage_quantity IS NULL OR shortage_quantity >= 0", name="ck_avail_shortage_nonneg"),
        CheckConstraint("required_quantity >= 0", name="ck_avail_req_qty_positive"),
    )


# ==============================================================================
# PHASE 1Q: MATERIAL ISSUE, ACTUAL CONSUMPTION & RECONCILIATION FOUNDATION
# ==============================================================================

class MaterialIssueAllocation(Base):
    __tablename__ = "material_issue_allocations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    material_item_id = Column(String(36), ForeignKey("material_items.id", ondelete="RESTRICT"), nullable=False)
    material_stock_ledger_id = Column(String(36), ForeignKey("material_stock_ledger.id", ondelete="RESTRICT"), nullable=False)
    activity_id = Column(String(36), ForeignKey("construction_activities.id", ondelete="RESTRICT"), nullable=False)
    material_requirement_plan_id = Column(String(36), ForeignKey("material_requirement_plans.id", ondelete="RESTRICT"), nullable=True)
    material_requirement_item_id = Column(String(36), ForeignKey("material_requirement_items.id", ondelete="RESTRICT"), nullable=True)
    issued_quantity = Column(Numeric(18, 4), nullable=False)
    issued_unit = Column(String(20), nullable=False)
    issue_date = Column(Date, nullable=False)
    source_type = Column(String(50), nullable=False, default="STORE_ISSUE")
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(String(100), nullable=True)
    status = Column(String(30), nullable=False, default="ALLOCATED")
    created_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata_json = Column(JSON, nullable=False, default=dict)

    project = relationship("Project")
    material_item = relationship("MaterialItem")
    stock_ledger_entry = relationship("MaterialStockLedger")
    activity = relationship("ConstructionActivity")
    material_requirement_plan = relationship("MaterialRequirementPlan")
    material_requirement_item = relationship("MaterialRequirementItem")
    creator = relationship("User")

    __table_args__ = (
        Index("ix_issue_alloc_project", "project_id"),
        Index("ix_issue_alloc_material", "material_item_id"),
        Index("ix_issue_alloc_ledger", "material_stock_ledger_id"),
        Index("ix_issue_alloc_activity", "activity_id"),
        Index("ix_issue_alloc_plan", "material_requirement_plan_id"),
        Index("ix_issue_alloc_status", "status"),
        CheckConstraint("issued_quantity > 0", name="ck_issue_alloc_qty_pos"),
        CheckConstraint("status IN ('ALLOCATED', 'CANCELLED', 'SUPERSEDED')", name="ck_issue_alloc_status"),
    )


class MaterialActualConsumptionEntry(Base):
    __tablename__ = "material_actual_consumption_entries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    material_item_id = Column(String(36), ForeignKey("material_items.id", ondelete="RESTRICT"), nullable=False)
    activity_id = Column(String(36), ForeignKey("construction_activities.id", ondelete="RESTRICT"), nullable=False)
    material_requirement_plan_id = Column(String(36), ForeignKey("material_requirement_plans.id", ondelete="RESTRICT"), nullable=True)
    material_requirement_item_id = Column(String(36), ForeignKey("material_requirement_items.id", ondelete="RESTRICT"), nullable=True)
    issue_allocation_id = Column(String(36), ForeignKey("material_issue_allocations.id", ondelete="RESTRICT"), nullable=True)
    contractor_consumed_quantity = Column(Numeric(18, 4), nullable=False)
    contractor_consumed_unit = Column(String(20), nullable=False)
    consumption_date = Column(Date, nullable=False)
    declared_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    declared_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    verification_status = Column(String(30), nullable=False, default="PENDING_VERIFICATION")
    metadata_json = Column(JSON, nullable=False, default=dict)

    project = relationship("Project")
    material_item = relationship("MaterialItem")
    activity = relationship("ConstructionActivity")
    material_requirement_plan = relationship("MaterialRequirementPlan")
    material_requirement_item = relationship("MaterialRequirementItem")
    issue_allocation = relationship("MaterialIssueAllocation")
    declarer = relationship("User")
    verifications = relationship("MaterialConsumptionVerification", back_populates="consumption_entry")

    __table_args__ = (
        Index("ix_mat_cons_project", "project_id"),
        Index("ix_mat_cons_material", "material_item_id"),
        Index("ix_mat_cons_activity", "activity_id"),
        Index("ix_mat_cons_plan", "material_requirement_plan_id"),
        Index("ix_mat_cons_status", "verification_status"),
        CheckConstraint("contractor_consumed_quantity >= 0", name="ck_mat_cons_qty_nonneg"),
        CheckConstraint(
            "verification_status IN ('PENDING_VERIFICATION', 'VERIFIED', 'CORRECTED', 'REJECTED')",
            name="ck_mat_cons_verif_status",
        ),
    )


MaterialActivityConsumptionEntry = MaterialActualConsumptionEntry


class MaterialConsumptionVerification(Base):
    __tablename__ = "material_consumption_verifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    consumption_entry_id = Column(String(36), ForeignKey("material_actual_consumption_entries.id", ondelete="RESTRICT"), nullable=False)
    verified_quantity = Column(Numeric(18, 4), nullable=False)
    verified_unit = Column(String(20), nullable=False)
    verification_status = Column(String(30), nullable=False)
    correction_reason = Column(Text, nullable=True)
    verified_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    verified_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata_json = Column(JSON, nullable=False, default=dict)

    consumption_entry = relationship("MaterialActualConsumptionEntry", back_populates="verifications")
    verifier = relationship("User")

    __table_args__ = (
        Index("ix_mat_verif_entry", "consumption_entry_id"),
        Index("ix_mat_verif_status", "verification_status"),
        CheckConstraint("verified_quantity >= 0", name="ck_mat_verif_qty_nonneg"),
        CheckConstraint("verification_status IN ('VERIFIED', 'CORRECTED', 'REJECTED')", name="ck_mat_verif_status"),
    )


class MaterialConsumptionReconciliation(Base):
    __tablename__ = "material_consumption_reconciliations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    material_requirement_plan_id = Column(String(36), ForeignKey("material_requirement_plans.id", ondelete="CASCADE"), nullable=False)
    material_requirement_item_id = Column(String(36), ForeignKey("material_requirement_items.id", ondelete="CASCADE"), nullable=True)
    activity_id = Column(String(36), ForeignKey("construction_activities.id", ondelete="RESTRICT"), nullable=True)
    material_item_id = Column(String(36), ForeignKey("material_items.id", ondelete="RESTRICT"), nullable=False)
    planned_quantity = Column(Numeric(18, 4), nullable=True)
    planned_unit = Column(String(20), nullable=True)
    theoretical_quantity = Column(Numeric(18, 4), nullable=True)
    theoretical_unit = Column(String(20), nullable=True)
    issued_quantity = Column(Numeric(18, 4), nullable=True)
    issued_unit = Column(String(20), nullable=True)
    actual_consumed_quantity = Column(Numeric(18, 4), nullable=True)
    actual_consumed_unit = Column(String(20), nullable=True)
    variance_quantity = Column(Numeric(18, 4), nullable=True)
    variance_percentage = Column(Numeric(18, 4), nullable=True)
    permissible_wastage_quantity = Column(Numeric(18, 4), nullable=True)
    unauthorized_wastage_quantity = Column(Numeric(18, 4), nullable=True)
    status = Column(String(30), nullable=False)
    algorithm_version = Column(String(50), nullable=False, default="MAT_CONSUMPTION_RECON_1.0")
    input_snapshot_json = Column(JSON, nullable=False, default=dict)
    provenance_metadata = Column(JSON, nullable=False, default=dict)
    canonical_hash = Column(String(64), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project")
    material_requirement_plan = relationship("MaterialRequirementPlan")
    material_requirement_item = relationship("MaterialRequirementItem")
    activity = relationship("ConstructionActivity")
    material_item = relationship("MaterialItem")
    creator = relationship("User")

    __table_args__ = (
        Index("ix_mat_recon_project", "project_id"),
        Index("ix_mat_recon_plan", "material_requirement_plan_id"),
        Index("ix_mat_recon_activity", "activity_id"),
        Index("ix_mat_recon_material", "material_item_id"),
        Index("ix_mat_recon_status", "status"),
        CheckConstraint(
            "status IN ('MATCH', 'WITHIN_PERMISSIBLE_WASTAGE', 'OVER_CONSUMPTION', 'UNDER_CONSUMPTION', 'REQUIRES_INPUT', 'UNIT_MISMATCH', 'NO_VERIFIED_ACTUAL', 'CALCULATED', 'SUPERSEDED')",
            name="ck_mat_recon_status",
        ),
    )


# ==============================================================================
# PHASE 1R: MATERIAL PRODUCTIVITY, CONSUMPTION EFFICIENCY & RESOURCE PERFORMANCE
# ==============================================================================

class MaterialPerformanceSnapshot(Base):
    __tablename__ = "material_performance_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    activity_id = Column(String(36), ForeignKey("construction_activities.id", ondelete="RESTRICT"), nullable=False)
    material_item_id = Column(String(36), ForeignKey("material_items.id", ondelete="RESTRICT"), nullable=False)
    reconciliation_id = Column(String(36), ForeignKey("material_consumption_reconciliations.id", ondelete="SET NULL"), nullable=True)
    requirement_plan_id = Column(String(36), ForeignKey("material_requirement_plans.id", ondelete="SET NULL"), nullable=True)
    requirement_item_id = Column(String(36), ForeignKey("material_requirement_items.id", ondelete="SET NULL"), nullable=True)
    performance_period_start = Column(Date, nullable=True)
    performance_period_end = Column(Date, nullable=True)
    planned_quantity = Column(Numeric(18, 4), nullable=True)
    planned_unit = Column(String(20), nullable=True)
    theoretical_quantity = Column(Numeric(18, 4), nullable=True)
    theoretical_unit = Column(String(20), nullable=True)
    issued_quantity = Column(Numeric(18, 4), nullable=True)
    issued_unit = Column(String(20), nullable=True)
    actual_consumption_quantity = Column(Numeric(18, 4), nullable=True)
    actual_consumption_unit = Column(String(20), nullable=True)
    verified_activity_execution_quantity = Column(Numeric(18, 4), nullable=True)
    verified_activity_execution_unit = Column(String(20), nullable=True)
    permissible_wastage_quantity = Column(Numeric(18, 4), nullable=True)
    unauthorized_wastage_quantity = Column(Numeric(18, 4), nullable=True)
    planned_variance_quantity = Column(Numeric(18, 4), nullable=True)
    theoretical_variance_quantity = Column(Numeric(18, 4), nullable=True)
    planned_variance_percentage = Column(Numeric(18, 4), nullable=True)
    theoretical_variance_percentage = Column(Numeric(18, 4), nullable=True)
    consumption_intensity = Column(Numeric(18, 6), nullable=True)
    productivity = Column(Numeric(18, 6), nullable=True)
    performance_status = Column(String(30), nullable=False)
    algorithm_version = Column(String(50), nullable=False, default="MAT_PERFORMANCE_1.0")
    input_snapshot_json = Column(JSON, nullable=False, default=dict)
    provenance_metadata = Column(JSON, nullable=False, default=dict)
    canonical_hash = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False, default="DRAFT")
    created_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finalized_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    finalized_at = Column(DateTime(timezone=True), nullable=True)
    superseded_by = Column(String(36), ForeignKey("material_performance_snapshots.id", ondelete="SET NULL"), nullable=True)
    superseded_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    superseded_at = Column(DateTime(timezone=True), nullable=True)
    supersession_reason = Column(Text, nullable=True)

    project = relationship("Project")
    activity = relationship("ConstructionActivity")
    material_item = relationship("MaterialItem")
    reconciliation = relationship("MaterialConsumptionReconciliation")
    requirement_plan = relationship("MaterialRequirementPlan")
    requirement_item = relationship("MaterialRequirementItem")
    creator = relationship("User", foreign_keys=[created_by])
    finalizer = relationship("User", foreign_keys=[finalized_by])
    superseding_user = relationship("User", foreign_keys=[superseded_by_user_id])
    replacement_snapshot = relationship("MaterialPerformanceSnapshot", foreign_keys=[superseded_by], remote_side=[id])

    __table_args__ = (
        Index("ix_mps_project", "project_id"),
        Index("ix_mps_activity", "activity_id"),
        Index("ix_mps_material", "material_item_id"),
        Index("ix_mps_status", "status"),
        Index("ix_mps_perf_status", "performance_status"),
        Index(
            "uq_mps_authoritative_identity",
            "project_id",
            "activity_id",
            "material_item_id",
            text("COALESCE(performance_period_start, '1970-01-01'::date)"),
            text("COALESCE(performance_period_end, '1970-01-01'::date)"),
            text("COALESCE(reconciliation_id, '00000000-0000-0000-0000-000000000000')"),
            unique=True,
            postgresql_where=text("status = 'FINALIZED'"),
        ),
        CheckConstraint("status IN ('DRAFT', 'FINALIZED', 'SUPERSEDED')", name="ck_mps_status"),
        CheckConstraint(
            "performance_status IN ('MATCH', 'WITHIN_PERMISSIBLE_VARIANCE', 'OVER_CONSUMPTION', 'UNDER_CONSUMPTION', 'UNAUTHORIZED_WASTAGE', 'REQUIRES_INPUT', 'NO_VERIFIED_ACTUAL', 'NO_THEORETICAL_DATA', 'UNIT_MISMATCH')",
            name="ck_mps_perf_status"
        ),
        CheckConstraint("planned_quantity IS NULL OR planned_quantity >= 0", name="ck_mps_planned_qty"),
        CheckConstraint("theoretical_quantity IS NULL OR theoretical_quantity >= 0", name="ck_mps_theo_qty"),
        CheckConstraint("issued_quantity IS NULL OR issued_quantity >= 0", name="ck_mps_issued_qty"),
        CheckConstraint("actual_consumption_quantity IS NULL OR actual_consumption_quantity >= 0", name="ck_mps_act_qty"),
        CheckConstraint("verified_activity_execution_quantity IS NULL OR verified_activity_execution_quantity >= 0", name="ck_mps_exec_qty"),
        CheckConstraint(
            "performance_period_start IS NULL OR performance_period_end IS NULL OR performance_period_start <= performance_period_end",
            name="ck_mps_period"
        ),
    )


# ==============================================================================
# PHASE 1S: CONSTRUCTION RESOURCE PRODUCTIVITY & COST PERFORMANCE FOUNDATION
# ==============================================================================

class ResourcePerformanceSnapshot(Base):
    __tablename__ = "resource_performance_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    activity_id = Column(String(36), ForeignKey("construction_activities.id", ondelete="RESTRICT"), nullable=False)
    resource_id = Column(String(36), ForeignKey("resources.id", ondelete="RESTRICT"), nullable=True)
    material_item_id = Column(String(36), ForeignKey("material_items.id", ondelete="RESTRICT"), nullable=True)
    resource_category = Column(String(20), nullable=False) # LABOUR, MATERIAL, EQUIPMENT
    performance_period_start = Column(Date, nullable=True)
    performance_period_end = Column(Date, nullable=True)
    resource_plan_id = Column(String(36), ForeignKey("resource_plans.id", ondelete="SET NULL"), nullable=True)
    material_performance_snapshot_id = Column(String(36), ForeignKey("material_performance_snapshots.id", ondelete="SET NULL"), nullable=True)
    cost_rate_id = Column(String(36), ForeignKey("cost_rates.id", ondelete="RESTRICT"), nullable=True)
    rate_mapping_id = Column(String(36), ForeignKey("activity_rate_mappings.id", ondelete="SET NULL"), nullable=True)
    cost_rate_version = Column(String(50), nullable=True)
    applied_cost_rate_value = Column(Numeric(18, 6), nullable=True)
    applied_cost_rate_unit = Column(String(50), nullable=True)
    planned_quantity = Column(Numeric(18, 4), nullable=True)
    planned_unit = Column(String(50), nullable=True)
    actual_resource_quantity = Column(Numeric(18, 4), nullable=True)
    actual_resource_unit = Column(String(50), nullable=True)
    verified_output_quantity = Column(Numeric(18, 4), nullable=True)
    verified_output_unit = Column(String(50), nullable=True)
    currency = Column(String(10), nullable=True)
    planned_cost = Column(Numeric(18, 4), nullable=True)
    actual_cost = Column(Numeric(18, 4), nullable=True)
    resource_variance = Column(Numeric(18, 4), nullable=True)
    resource_variance_percentage = Column(Numeric(18, 4), nullable=True)
    cost_variance = Column(Numeric(18, 4), nullable=True)
    productivity = Column(Numeric(18, 6), nullable=True)
    productivity_unit = Column(String(50), nullable=True)
    resource_intensity = Column(Numeric(18, 6), nullable=True)
    resource_intensity_unit = Column(String(50), nullable=True)
    cost_intensity = Column(Numeric(18, 6), nullable=True)
    cost_intensity_unit = Column(String(50), nullable=True)
    tolerance_percentage = Column(Numeric(18, 4), nullable=True)
    performance_status = Column(String(40), nullable=False)
    algorithm_version = Column(String(50), nullable=False, default="RES_PERFORMANCE_1.0")
    input_snapshot_json = Column(JSON, nullable=False, default=dict)
    provenance_metadata = Column(JSON, nullable=False, default=dict)
    canonical_hash = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False, default="DRAFT") # DRAFT, FINALIZED, SUPERSEDED
    created_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finalized_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    finalized_at = Column(DateTime(timezone=True), nullable=True)
    superseded_by = Column(String(36), ForeignKey("resource_performance_snapshots.id", ondelete="SET NULL"), nullable=True)
    superseded_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    superseded_at = Column(DateTime(timezone=True), nullable=True)
    supersession_reason = Column(Text, nullable=True)

    project = relationship("Project")
    activity = relationship("ConstructionActivity")
    resource = relationship("Resource")
    material_item = relationship("MaterialItem")
    resource_plan = relationship("ResourcePlan")
    material_performance_snapshot = relationship("MaterialPerformanceSnapshot", foreign_keys=[material_performance_snapshot_id])
    cost_rate = relationship("CostRate", foreign_keys=[cost_rate_id])
    rate_mapping = relationship("ActivityRateMapping", foreign_keys=[rate_mapping_id])
    creator = relationship("User", foreign_keys=[created_by])
    finalizer = relationship("User", foreign_keys=[finalized_by])
    superseding_user = relationship("User", foreign_keys=[superseded_by_user_id])
    replacement_snapshot = relationship("ResourcePerformanceSnapshot", foreign_keys=[superseded_by], remote_side=[id])

    __table_args__ = (
        Index("ix_rps_project", "project_id"),
        Index("ix_rps_activity", "activity_id"),
        Index("ix_rps_resource", "resource_id"),
        Index("ix_rps_material", "material_item_id"),
        Index("ix_rps_category", "resource_category"),
        Index("ix_rps_status", "status"),
        Index("ix_rps_perf_status", "performance_status"),
        Index(
            "uq_rps_authoritative_identity",
            "project_id",
            "activity_id",
            "resource_category",
            text("COALESCE(resource_id, '00000000-0000-0000-0000-000000000000')"),
            text("COALESCE(material_item_id, '00000000-0000-0000-0000-000000000000')"),
            text("COALESCE(performance_period_start, '1970-01-01'::date)"),
            text("COALESCE(performance_period_end, '1970-01-01'::date)"),
            unique=True,
            postgresql_where=text("status = 'FINALIZED'"),
        ),
        CheckConstraint("resource_category IN ('LABOUR', 'MATERIAL', 'EQUIPMENT')", name="ck_rps_category"),
        CheckConstraint("status IN ('DRAFT', 'FINALIZED', 'SUPERSEDED')", name="ck_rps_status"),
        CheckConstraint(
            "performance_status IN ('MATCH', 'WITHIN_PERMISSIBLE_VARIANCE', 'OVER_RESOURCE_CONSUMPTION', 'UNDER_RESOURCE_CONSUMPTION', 'COST_OVER_RUN', 'COST_UNDER_RUN', 'REQUIRES_INPUT', 'NO_VERIFIED_OUTPUT', 'UNIT_MISMATCH', 'CURRENCY_MISMATCH', 'RATE_UNAVAILABLE')",
            name="ck_rps_perf_status"
        ),
        CheckConstraint("planned_quantity IS NULL OR planned_quantity >= 0", name="ck_rps_planned_qty"),
        CheckConstraint("actual_resource_quantity IS NULL OR actual_resource_quantity >= 0", name="ck_rps_act_qty"),
        CheckConstraint("verified_output_quantity IS NULL OR verified_output_quantity >= 0", name="ck_rps_exec_qty"),
        CheckConstraint("planned_cost IS NULL OR planned_cost >= 0", name="ck_rps_planned_cost"),
        CheckConstraint("actual_cost IS NULL OR actual_cost >= 0", name="ck_rps_act_cost"),
        CheckConstraint(
            "performance_period_start IS NULL OR performance_period_end IS NULL OR performance_period_start <= performance_period_end",
            name="ck_rps_period"
        ),
        CheckConstraint("tolerance_percentage IS NULL OR tolerance_percentage >= 0", name="ck_rps_tol"),
    )


# ==============================================================================
# PHASE 1T: CONSTRUCTION SCHEDULE PERFORMANCE & DELAY ATTRIBUTION FOUNDATION
# ==============================================================================

class SchedulePerformanceSnapshot(Base):
    __tablename__ = "schedule_performance_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    activity_id = Column(String(36), ForeignKey("construction_activities.id", ondelete="RESTRICT"), nullable=False)
    schedule_id = Column(String(36), ForeignKey("construction_schedules.id", ondelete="RESTRICT"), nullable=False)
    monitoring_baseline_id = Column(String(36), ForeignKey("monitoring_baselines.id", ondelete="RESTRICT"), nullable=True)
    performance_period_start = Column(Date, nullable=True)
    performance_period_end = Column(Date, nullable=True)
    evaluation_date = Column(Date, nullable=False)

    planned_start_date = Column(Date, nullable=True)
    planned_finish_date = Column(Date, nullable=True)
    planned_duration_days = Column(Integer, nullable=True)
    actual_start_date = Column(Date, nullable=True)
    actual_finish_date = Column(Date, nullable=True)
    actual_duration_days = Column(Integer, nullable=True)

    planned_cumulative_progress_pct = Column(Numeric(7, 4), nullable=True)
    actual_cumulative_progress_pct = Column(Numeric(7, 4), nullable=True)
    earned_schedule_days = Column(Numeric(10, 4), nullable=True)
    actual_time_days = Column(Numeric(10, 4), nullable=True)

    schedule_variance_days = Column(Numeric(10, 4), nullable=True)
    schedule_performance_index = Column(Numeric(10, 6), nullable=True)

    baseline_total_float_days = Column(Integer, nullable=True)
    residual_total_float_days = Column(Integer, nullable=True)
    is_critical_path = Column(Boolean, nullable=False, default=False)
    critical_path_impact_days = Column(Integer, nullable=True)

    delay_status = Column(String(40), nullable=False)
    delay_classification = Column(String(40), nullable=True)
    delay_root_cause_category = Column(String(50), nullable=True)
    delay_justification = Column(Text, nullable=True)
    delay_evidence_document_id = Column(String(36), ForeignKey("documents.id", ondelete="RESTRICT"), nullable=True)
    contract_variation_id = Column(String(36), ForeignKey("contract_variation_orders.id", ondelete="RESTRICT"), nullable=True)

    performance_status = Column(String(40), nullable=False)
    algorithm_version = Column(String(50), nullable=False, default="SCHED_PERFORMANCE_1.0")
    input_snapshot_json = Column(JSON, nullable=False, default=dict)
    provenance_metadata = Column(JSON, nullable=False, default=dict)
    canonical_hash = Column(String(64), nullable=False)

    status = Column(String(20), nullable=False, default="DRAFT") # DRAFT, FINALIZED, SUPERSEDED
    created_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finalized_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    finalized_at = Column(DateTime(timezone=True), nullable=True)
    superseded_by = Column(String(36), ForeignKey("schedule_performance_snapshots.id", ondelete="RESTRICT"), nullable=True)
    superseded_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    superseded_at = Column(DateTime(timezone=True), nullable=True)
    supersession_reason = Column(Text, nullable=True)

    project = relationship("Project")
    activity = relationship("ConstructionActivity")
    schedule = relationship("ConstructionSchedule")
    monitoring_baseline = relationship("MonitoringBaseline")
    delay_evidence_document = relationship("Document", foreign_keys=[delay_evidence_document_id])
    contract_variation = relationship("ContractVariationOrder", foreign_keys=[contract_variation_id])
    creator = relationship("User", foreign_keys=[created_by])
    finalizer = relationship("User", foreign_keys=[finalized_by])
    superseding_user = relationship("User", foreign_keys=[superseded_by_user_id])
    replacement_snapshot = relationship("SchedulePerformanceSnapshot", foreign_keys=[superseded_by], remote_side=[id])

    __table_args__ = (
        Index("ix_sps_project", "project_id"),
        Index("ix_sps_activity", "activity_id"),
        Index("ix_sps_schedule", "schedule_id"),
        Index("ix_sps_status", "status"),
        Index("ix_sps_delay_status", "delay_status"),
        Index("ix_sps_perf_status", "performance_status"),
        Index(
            "uq_sps_authoritative_identity",
            "project_id",
            "activity_id",
            "performance_period_start",
            "performance_period_end",
            unique=True,
            postgresql_where=text("status = 'FINALIZED' AND performance_period_start IS NOT NULL AND performance_period_end IS NOT NULL"),
        ),
        Index(
            "uq_sps_authoritative_identity_null_period",
            "project_id",
            "activity_id",
            unique=True,
            postgresql_where=text("status = 'FINALIZED' AND performance_period_start IS NULL AND performance_period_end IS NULL"),
        ),
        CheckConstraint("status IN ('DRAFT', 'FINALIZED', 'SUPERSEDED')", name="ck_sps_status"),
        CheckConstraint(
            "delay_status IN ('ON_SCHEDULE', 'AHEAD_OF_SCHEDULE', 'MINOR_DELAY', 'CRITICAL_DELAY', 'FLOAT_ABSORBED', 'SCHEDULE_BREACH', 'REQUIRES_INPUT')",
            name="ck_sps_delay_status"
        ),
        CheckConstraint(
            "delay_classification IS NULL OR delay_classification IN ('EXCUSABLE_COMPENSABLE', 'EXCUSABLE_NON_COMPENSABLE', 'NON_EXCUSABLE', 'CONCURRENT_DELAY', 'NO_DELAY')",
            name="ck_sps_delay_class"
        ),
        CheckConstraint(
            "performance_status IN ('ON_TRACK', 'SCHEDULE_VARIANCE_WITHIN_TOLERANCE', 'CRITICAL_DELAY', 'SCHEDULE_BREACH', 'REQUIRES_INPUT', 'DATA_MISMATCH')",
            name="ck_sps_perf_status"
        ),
        CheckConstraint(
            "performance_period_start IS NULL OR performance_period_end IS NULL OR performance_period_start <= performance_period_end",
            name="ck_sps_period"
        ),
        CheckConstraint(
            "planned_start_date IS NULL OR planned_finish_date IS NULL OR planned_start_date <= planned_finish_date",
            name="ck_sps_planned_dates"
        ),
        CheckConstraint(
            "actual_start_date IS NULL OR actual_finish_date IS NULL OR actual_start_date <= actual_finish_date",
            name="ck_sps_actual_dates"
        ),
        CheckConstraint("planned_duration_days IS NULL OR planned_duration_days >= 0", name="ck_sps_planned_duration"),
        CheckConstraint("actual_duration_days IS NULL OR actual_duration_days >= 0", name="ck_sps_actual_duration"),
        CheckConstraint(
            "planned_cumulative_progress_pct IS NULL OR (planned_cumulative_progress_pct >= 0 AND planned_cumulative_progress_pct <= 100)",
            name="ck_sps_planned_pct"
        ),
        CheckConstraint(
            "actual_cumulative_progress_pct IS NULL OR (actual_cumulative_progress_pct >= 0 AND actual_cumulative_progress_pct <= 100)",
            name="ck_sps_actual_pct"
        ),
        CheckConstraint(
            """(status = 'DRAFT' AND finalized_by IS NULL AND finalized_at IS NULL AND superseded_by IS NULL AND superseded_by_user_id IS NULL AND superseded_at IS NULL AND supersession_reason IS NULL) OR
               (status = 'FINALIZED' AND finalized_by IS NOT NULL AND finalized_at IS NOT NULL AND superseded_by IS NULL AND superseded_by_user_id IS NULL AND superseded_at IS NULL AND supersession_reason IS NULL) OR
               (status = 'SUPERSEDED' AND finalized_by IS NOT NULL AND finalized_at IS NOT NULL AND superseded_by IS NOT NULL AND superseded_by_user_id IS NOT NULL AND superseded_at IS NOT NULL AND supersession_reason IS NOT NULL)""",
            name="ck_sps_lifecycle_metadata"
        ),
    )







