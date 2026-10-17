from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.db.models import (
    RuleBasedEstimation,
    EngineeringCalculation,
    EngineeringElement,
    ExtractedFact,
    Evidence,
    DocumentPage,
    Document,
    Project,
    Rule,
    User
)
from app.services.audit import log_action
from app.services.rules import get_rule_strategy, seed_default_rules
from app.schemas.schemas import (
    EstimationResponse,
    EstimationTypeEnum,
    EstimationStatusEnum
)

def execute_rule_based_estimation(
    db: Session,
    project_id: str,
    user_id: str,
    calculation_id: str,
    rule_code: str,
    rule_version: str,
    parameters: Dict[str, Any],
    metadata_json: Optional[Dict[str, Any]] = None
) -> RuleBasedEstimation:
    # 1. Fetch EngineeringCalculation and verify project boundary
    calc = db.query(EngineeringCalculation).filter(
        EngineeringCalculation.id == calculation_id
    ).first()
    if not calc:
        raise HTTPException(
            status_code=404,
            detail=f"EngineeringCalculation '{calculation_id}' not found"
        )

    if calc.project_id != project_id:
        raise HTTPException(
            status_code=400,
            detail=f"Cross-project calculation rejected: calculation belongs to project '{calc.project_id}'"
        )

    if calc.status != "CALCULATED":
        raise HTTPException(
            status_code=400,
            detail=f"Invalid calculation status '{calc.status}'. Only active CALCULATED engineering calculations can be estimated."
        )

    if calc.result_value is None or calc.result_value <= Decimal("0"):
        raise HTTPException(
            status_code=400,
            detail=f"Calculation result quantity must be strictly positive (> 0). Value: {calc.result_value}"
        )

    # 2. Verify EngineeringElement exists and matches calculation
    element = db.query(EngineeringElement).filter(
        EngineeringElement.id == calc.engineering_element_id,
        EngineeringElement.project_id == project_id
    ).first()
    if not element:
        raise HTTPException(
            status_code=404,
            detail=f"EngineeringElement '{calc.engineering_element_id}' not found in this project"
        )

    # 3. Lookup Rule in database
    rule = db.query(Rule).filter(
        Rule.rule_code == rule_code,
        Rule.version == rule_version
    ).first()
    if not rule:
        seed_default_rules(db, user_id)
        rule = db.query(Rule).filter(
            Rule.rule_code == rule_code,
            Rule.version == rule_version
        ).first()

    if not rule:
        raise HTTPException(
            status_code=404,
            detail=f"Rule '{rule_code}' version '{rule_version}' not found"
        )

    if rule.status != "ACTIVE":
        raise HTTPException(
            status_code=400,
            detail=f"Rule '{rule_code}' version '{rule_version}' is not ACTIVE (current status: '{rule.status}')"
        )

    # 4. Lookup Rule Strategy in registry
    strategy = get_rule_strategy(rule_code, rule_version)

    # 4b. Registry-Database Agreement Check (Section 4 consistency requirement)
    if (rule.rule_code != strategy.rule_code or
        rule.version != strategy.rule_version or
        rule.formula_identifier != strategy.formula_identifier or
        rule.input_unit not in strategy.supported_input_units or
        rule.output_unit != strategy.output_unit):
        raise HTTPException(
            status_code=400,
            detail=f"Registry-Database mismatch for rule '{rule_code}' v'{rule_version}'. Persisted definition does not agree with executable strategy."
        )

    # 5. Validate input unit compatibility
    if calc.result_unit not in strategy.supported_input_units:
        raise HTTPException(
            status_code=400,
            detail=f"Incompatible calculation unit '{calc.result_unit}' for rule '{rule_code}'. Supported: {strategy.supported_input_units}"
        )

    # 6. Validate parameters
    cleaned_params = strategy.validate_parameters(parameters)

    # 7. Execute deterministic rule calculation
    result_value = strategy.execute(calc.result_value, cleaned_params)

    # 8. Supersede prior active estimations for this element & rule
    prior_estimations = db.query(RuleBasedEstimation).filter(
        RuleBasedEstimation.engineering_element_id == element.id,
        RuleBasedEstimation.rule_id == rule.id,
        RuleBasedEstimation.status == EstimationStatusEnum.ESTIMATED.value
    ).all()
    for prior in prior_estimations:
        prior.status = EstimationStatusEnum.SUPERSEDED.value

    # 9. Build Assumption and Provenance metadata
    assumptions_data = {
        "productivity_rate": str(cleaned_params["productivity_rate"]),
        "productivity_unit": str(parameters.get("productivity_unit")),
        "assumption_type": "ASSUMPTION_BASED",
        "confidence_classification": "ASSUMPTION_BASED",
        "source_reference": parameters.get("source_reference") or rule.source_reference or "Configured system assumption",
        "rule_version": rule.version,
        "note": "Productivity rate is a configured rule assumption and not an empirical site measurement."
    }

    provenance_summary = {
        "project_id": project_id,
        "element_id": element.id,
        "element_name": element.element_name,
        "element_type": element.element_type,
        "calculation_id": calc.id,
        "calculation_type": calc.calculation_type,
        "input_quantity": str(calc.result_value),
        "input_unit": calc.result_unit
    }

    # 10. Persist RuleBasedEstimation record
    estimation = RuleBasedEstimation(
        project_id=project_id,
        engineering_element_id=element.id,
        calculation_id=calc.id,
        rule_id=rule.id,
        rule_version=rule.version,
        estimation_type=EstimationTypeEnum.LABOUR_HOURS.value,
        status=EstimationStatusEnum.ESTIMATED.value,
        input_value=calc.result_value,
        input_unit=calc.result_unit,
        result_value=result_value,
        result_unit=rule.output_unit,
        parameters_json={
            "productivity_rate": str(cleaned_params["productivity_rate"]),
            "productivity_unit": str(parameters.get("productivity_unit")),
            "source_reference": parameters.get("source_reference")
        },
        assumptions_json=assumptions_data,
        provenance_json=provenance_summary,
        created_by=user_id,
        metadata_json=metadata_json or {}
    )
    db.add(estimation)
    db.flush()

    # 11. Transactional Audit Log
    log_action(
        db,
        user_id,
        "ESTIMATION_PERFORMED",
        "RuleBasedEstimation",
        estimation.id,
        f"{rule.rule_code} v{rule.version} on {element.element_name}: {result_value} {rule.output_unit} (Input: {calc.result_value} {calc.result_unit}, Rate: {cleaned_params['productivity_rate']})"
    )

    return estimation


def build_estimation_response(db: Session, est: RuleBasedEstimation) -> EstimationResponse:
    element = est.engineering_element
    calc = est.calculation

    # Build full provenance chain:
    # Estimation -> Calculation -> EngineeringElement -> Fact -> Evidence -> Page -> Document -> Project
    calc_inputs_prov = []
    if calc and isinstance(calc.inputs_json, dict):
        for dim_name, item_data in calc.inputs_json.items():
            if isinstance(item_data, dict):
                fact_id = item_data.get("source_fact_id")
                fact_info = {"dimension_name": dim_name, "source_fact_id": fact_id}
                if fact_id:
                    fact = db.query(ExtractedFact).join(Evidence).join(Document).filter(
                        ExtractedFact.id == fact_id
                    ).first()
                    if fact:
                        fact_info["raw_value"] = fact.raw_value
                        fact_info["normalized_value"] = str(fact.normalized_value) if fact.normalized_value is not None else None
                        fact_info["normalized_unit"] = fact.normalized_unit
                        fact_info["verification_status"] = fact.verification_status
                        ev = fact.evidence
                        if ev:
                            fact_info["evidence_id"] = ev.id
                            fact_info["evidence_type"] = ev.evidence_type
                            fact_info["source_reference"] = ev.source_reference
                            fact_info["locator"] = ev.locator
                            page = ev.page
                            if page:
                                fact_info["page_id"] = page.id
                                fact_info["page_number"] = page.page_number
                            doc = ev.document
                            if doc:
                                fact_info["document_id"] = doc.id
                                fact_info["document_name"] = doc.original_filename
                                if doc.project:
                                    fact_info["project_id"] = doc.project.id
                                    fact_info["project_name"] = doc.project.name
                calc_inputs_prov.append(fact_info)

    prov_chain = {
        "estimation_id": est.id,
        "calculation": {
            "id": calc.id if calc else est.calculation_id,
            "type": calc.calculation_type if calc else None,
            "formula": calc.formula_expression if calc else None,
            "result_value": str(calc.result_value) if calc else str(est.input_value),
            "result_unit": calc.result_unit if calc else est.input_unit,
            "inputs_provenance": calc_inputs_prov
        },
        "engineering_element": {
            "id": element.id if element else est.engineering_element_id,
            "name": element.element_name if element else None,
            "type": element.element_type if element else None
        },
        "project": {
            "id": est.project_id,
            "name": est.project.name if est.project else None
        }
    }

    return EstimationResponse(
        id=est.id,
        project_id=est.project_id,
        engineering_element_id=est.engineering_element_id,
        calculation_id=est.calculation_id,
        rule_id=est.rule_id,
        rule_code=est.rule.rule_code if est.rule else "LABOUR_HOURS_FROM_QUANTITY",
        rule_version=est.rule_version,
        estimation_type=est.estimation_type,
        status=est.status,
        input_value=est.input_value,
        input_unit=est.input_unit,
        result_value=est.result_value,
        result_unit=est.result_unit,
        parameters_json=est.parameters_json,
        assumptions_json=est.assumptions_json,
        provenance_json=est.provenance_json,
        estimation_method="RULE_BASED",
        confidence_classification="ASSUMPTION_BASED",
        created_by=est.created_by,
        created_at=est.created_at,
        element_name=element.element_name if element else None,
        element_type=element.element_type if element else None,
        provenance_chain=prov_chain
    )
