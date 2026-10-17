from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.db.models import (
    EngineeringCalculation,
    EngineeringElement,
    ExtractedFact,
    Evidence,
    Document,
    Project,
    User
)
from app.services.audit import log_action
from app.schemas.schemas import (
    CalculationTypeEnum,
    CalculationStatusEnum,
    CalculationResponse,
    CalculationProvenanceItem
)

# ==============================================================================
# CALCULATION STRATEGY / REGISTRY PATTERN
# ==============================================================================

class CalculationDefinition(ABC):
    calculation_type: str
    calculation_version: str
    formula_identifier: str
    formula_expression: str
    result_unit: str
    supported_element_types: List[str]
    required_inputs: List[str]

    @abstractmethod
    def calculate(self, inputs: Dict[str, Decimal]) -> Decimal:
        pass

class ConcreteVolumeRectangularDefinition(CalculationDefinition):
    calculation_type = "CONCRETE_VOLUME_RECTANGULAR"
    calculation_version = "1.0"
    formula_identifier = "RECTANGULAR_VOLUME"
    formula_expression = "V = L * W * D"
    result_unit = "m3"
    supported_element_types = ["FOOTING", "PILE_CAP", "COLUMN", "BEAM", "SLAB", "FOUNDATION"]
    required_inputs = ["length_m", "width_m", "depth_m"]

    def calculate(self, inputs: Dict[str, Decimal]) -> Decimal:
        length = inputs["length_m"]
        width = inputs["width_m"]
        depth = inputs["depth_m"]
        # V = L * W * D
        volume = length * width * depth
        return volume.quantize(Decimal("0.000001"))

CALCULATION_REGISTRY: Dict[str, CalculationDefinition] = {
    CalculationTypeEnum.CONCRETE_VOLUME_RECTANGULAR.value: ConcreteVolumeRectangularDefinition(),
}

def get_calculation_definition(calc_type: str) -> CalculationDefinition:
    defn = CALCULATION_REGISTRY.get(calc_type)
    if not defn:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported calculation_type '{calc_type}'. Supported: {list(CALCULATION_REGISTRY.keys())}"
        )
    return defn

# ==============================================================================
# CALCULATION EXECUTION & AUDITING
# ==============================================================================

def execute_element_calculation(
    db: Session,
    project_id: str,
    element_id: str,
    user_id: str,
    calculation_type: str,
    inputs_raw: Dict[str, Any],
    assumptions_raw: Optional[Dict[str, Any]] = None
) -> EngineeringCalculation:
    # 0. Reject assumptions: Do not introduce assumptions in Phase 1E
    if assumptions_raw and len(assumptions_raw) > 0:
        raise HTTPException(
            status_code=400,
            detail="Assumptions are not permitted in Phase 1E. All dimensions must derive from VERIFIED_FACT."
        )

    # 1. Fetch EngineeringElement and verify project boundary
    element = db.query(EngineeringElement).filter(
        EngineeringElement.id == element_id,
        EngineeringElement.project_id == project_id
    ).first()
    if not element:
        raise HTTPException(status_code=404, detail="EngineeringElement not found in this project")

    # 2. Lookup Calculation Strategy
    strategy = get_calculation_definition(calculation_type)

    # 3. Element Type Compatibility Check
    if element.element_type not in strategy.supported_element_types:
        raise HTTPException(
            status_code=400,
            detail=f"Element type '{element.element_type}' is unsupported for calculation '{calculation_type}'. "
                   f"Supported element types: {strategy.supported_element_types}"
        )

    # 4. Input Validation & Resolution
    cleaned_numeric_inputs: Dict[str, Decimal] = {}
    persisted_inputs_json: Dict[str, Any] = {}

    for req_input in strategy.required_inputs:
        if req_input not in inputs_raw or inputs_raw[req_input] is None:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required dimension '{req_input}' (status: REQUIRES_INPUT). Missing dimensions cannot be inferred."
            )

        raw_item = inputs_raw[req_input]

        if not isinstance(raw_item, dict):
            raise HTTPException(
                status_code=400,
                detail=f"Dimension '{req_input}' must be a dictionary specifying source provenance. Direct numeric geometry values are not permitted."
            )

        # source_fact_id validation
        source_fact_id = raw_item.get("source_fact_id")
        if not source_fact_id or not str(source_fact_id).strip():
            raise HTTPException(
                status_code=400,
                detail=f"Dimension '{req_input}' is missing required 'source_fact_id'. Every engineering input must be traceable to a verified fact."
            )

        # source_type validation
        source_type = raw_item.get("source_type")
        if not source_type or not str(source_type).strip():
            raise HTTPException(
                status_code=400,
                detail=f"Dimension '{req_input}' is missing required 'source_type'."
            )
        if source_type != "VERIFIED_FACT":
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported source_type '{source_type}' for dimension '{req_input}'. Only 'VERIFIED_FACT' is permitted."
            )

        # Lookup ExtractedFact
        fact = db.query(ExtractedFact).join(Evidence).join(Document).filter(
            ExtractedFact.id == source_fact_id
        ).first()
        if not fact:
            raise HTTPException(
                status_code=400,
                detail=f"Source fact '{source_fact_id}' for dimension '{req_input}' does not exist"
            )

        # Fact verification check
        if fact.verification_status != "VERIFIED":
            raise HTTPException(
                status_code=400,
                detail=f"Source fact '{source_fact_id}' for dimension '{req_input}' must be VERIFIED. Current status: '{fact.verification_status}'"
            )

        # Project isolation check
        fact_doc = fact.evidence.document
        if fact_doc.project_id != project_id:
            raise HTTPException(
                status_code=400,
                detail=f"Cross-project fact rejected: fact '{source_fact_id}' belongs to project '{fact_doc.project_id}'"
            )

        # Cross-element fact check: verify fact is not associated with another element
        other_element = db.query(EngineeringElement).filter(
            EngineeringElement.project_id == project_id,
            EngineeringElement.source_fact_id == source_fact_id,
            EngineeringElement.id != element_id
        ).first()
        if other_element:
            raise HTTPException(
                status_code=400,
                detail=f"Cross-element fact rejected: fact '{source_fact_id}' is associated with element '{other_element.id}' ('{other_element.element_name}')"
            )

        # Fact normalized value check
        if fact.normalized_value is None:
            raise HTTPException(
                status_code=400,
                detail=f"Source fact '{source_fact_id}' for dimension '{req_input}' has no normalized value"
            )

        # Unit check on fact
        if fact.normalized_unit != "m":
            raise HTTPException(
                status_code=400,
                detail=f"Source fact '{source_fact_id}' for dimension '{req_input}' has incompatible unit '{fact.normalized_unit}'. Expected 'm'."
            )

        # Unit check on raw input if provided
        input_unit = raw_item.get("unit")
        if input_unit is not None and input_unit != "m":
            raise HTTPException(
                status_code=400,
                detail=f"Input unit for '{req_input}' must be normalized to 'm'. Provided: '{input_unit}'"
            )

        # Value resolution & positivity check
        val_decimal = fact.normalized_value

        if "value" in raw_item and raw_item["value"] is not None:
            try:
                provided_val = Decimal(str(raw_item["value"]))
            except Exception:
                raise HTTPException(status_code=400, detail=f"Invalid numeric value for '{req_input}'")
            if provided_val <= Decimal("0"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Dimension '{req_input}' must be strictly positive (> 0). Provided: {provided_val}"
                )
            val_decimal = fact.normalized_value

        if val_decimal <= Decimal("0"):
            raise HTTPException(
                status_code=400,
                detail=f"Dimension '{req_input}' must be strictly positive (> 0). Provided: {val_decimal} (status: INVALID_INPUT)"
            )

        cleaned_numeric_inputs[req_input] = val_decimal
        persisted_inputs_json[req_input] = {
            "value": str(val_decimal),
            "unit": "m",
            "source_fact_id": source_fact_id,
            "source_type": "VERIFIED_FACT"
        }

    # 5. Deterministic Calculation
    result_val = strategy.calculate(cleaned_numeric_inputs)

    # 6. Supersede previous completed calculations for this element & type
    existing_calcs = db.query(EngineeringCalculation).filter(
        EngineeringCalculation.engineering_element_id == element_id,
        EngineeringCalculation.calculation_type == calculation_type,
        EngineeringCalculation.status == CalculationStatusEnum.CALCULATED.value
    ).all()
    for prev_calc in existing_calcs:
        prev_calc.status = CalculationStatusEnum.SUPERSEDED.value

    # 7. Create Calculation Record
    calc_record = EngineeringCalculation(
        project_id=project_id,
        engineering_element_id=element_id,
        calculation_type=calculation_type,
        calculation_version=strategy.calculation_version,
        status=CalculationStatusEnum.CALCULATED.value,
        result_value=result_val,
        result_unit=strategy.result_unit,
        formula_identifier=strategy.formula_identifier,
        formula_expression=strategy.formula_expression,
        inputs_json=persisted_inputs_json,
        assumptions_json=assumptions_raw or {},
        created_by=user_id
    )
    db.add(calc_record)
    db.flush()

    # 8. Transactional Audit Log
    log_action(
        db,
        user_id,
        "CALCULATION_PERFORMED",
        "EngineeringCalculation",
        calc_record.id,
        f"{calculation_type} on {element.element_name}: {result_val} {strategy.result_unit}"
    )

    return calc_record

def build_calculation_response(db: Session, calc: EngineeringCalculation) -> CalculationResponse:
    element = calc.engineering_element
    prov_items: List[CalculationProvenanceItem] = []

    if isinstance(calc.inputs_json, dict):
        for dim_name, item_data in calc.inputs_json.items():
            if isinstance(item_data, dict):
                fact_id = item_data.get("source_fact_id")
                val = Decimal(str(item_data.get("value"))) if item_data.get("value") is not None else None
                unit = item_data.get("unit")
                raw_val = None
                ver_status = None
                ev_id = None
                ev_type = None
                src_ref = None
                loc = None
                p_id = None
                p_num = None
                d_id = None
                doc_name = None
                proj_id = None
                proj_name = None

                if fact_id:
                    fact = db.query(ExtractedFact).join(Evidence).join(Document).filter(
                        ExtractedFact.id == fact_id
                    ).first()
                    if fact:
                        raw_val = fact.raw_value
                        ver_status = fact.verification_status
                        ev = fact.evidence
                        if ev:
                            ev_id = ev.id
                            ev_type = ev.evidence_type
                            src_ref = ev.source_reference
                            loc = ev.locator
                            page = ev.page
                            if page:
                                p_id = page.id
                                p_num = page.page_number
                            doc = ev.document
                            if doc:
                                d_id = doc.id
                                doc_name = doc.original_filename
                                if doc.project:
                                    proj_id = doc.project.id
                                    proj_name = doc.project.name

                prov_items.append(CalculationProvenanceItem(
                    dimension_name=dim_name,
                    value=val,
                    unit=unit,
                    fact_id=fact_id,
                    raw_value=raw_val,
                    fact_verification_status=ver_status,
                    evidence_id=ev_id,
                    evidence_type=ev_type,
                    source_reference=src_ref,
                    locator=loc,
                    page_id=p_id,
                    page_number=p_num,
                    document_id=d_id,
                    original_filename=doc_name,
                    project_id=proj_id,
                    project_name=proj_name
                ))

    return CalculationResponse(
        id=calc.id,
        project_id=calc.project_id,
        engineering_element_id=calc.engineering_element_id,
        calculation_type=calc.calculation_type,
        calculation_version=calc.calculation_version,
        status=calc.status,
        result_value=calc.result_value,
        result_unit=calc.result_unit,
        formula_identifier=calc.formula_identifier,
        formula_expression=calc.formula_expression,
        inputs_json=calc.inputs_json,
        assumptions_json=calc.assumptions_json,
        created_by=calc.created_by,
        created_at=calc.created_at,
        element_name=element.element_name if element else None,
        element_type=element.element_type if element else None,
        provenance_details=prov_items
    )
