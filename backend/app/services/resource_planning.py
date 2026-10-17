from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.db.models import (
    Resource,
    CalculationResourceMapping,
    ResourcePlan,
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
from app.schemas.schemas import (
    ResourceCreate,
    ResourceResponse,
    CalculationResourceMappingCreate,
    CalculationResourceMappingResponse,
    ResourcePlanResponse,
    PlanningMethodEnum,
    PlanClassificationEnum,
    PlanStatusEnum,
    ResourceCategoryEnum,
    ResourceStatusEnum,
    MappingStatusEnum
)

# ==============================================================================
# RESOURCE SEEDING & MANAGEMENT
# ==============================================================================

DEFAULT_RESOURCES = [
    {
        "resource_code": "LABOUR-CONCRETE",
        "resource_name": "Concrete Labour",
        "resource_category": "LABOUR",
        "unit": "labour-hour",
        "description": "Concrete pouring, compaction, levelling and finishing labour.",
        "status": "ACTIVE",
        "metadata_json": {"system_seeded": True}
    },
    {
        "resource_code": "MATERIAL-CONCRETE",
        "resource_name": "Ready-Mix Concrete",
        "resource_category": "MATERIAL",
        "unit": "m3",
        "description": "Ready-mix concrete supply for structural elements.",
        "status": "ACTIVE",
        "metadata_json": {"system_seeded": True}
    },
    {
        "resource_code": "EQUIPMENT-PUMP",
        "resource_name": "Concrete Boom Pump",
        "resource_category": "EQUIPMENT",
        "unit": "equipment-hour",
        "description": "Mobile concrete pump truck for placing concrete.",
        "status": "ACTIVE",
        "metadata_json": {"system_seeded": True}
    }
]

def seed_default_resources(db: Session, created_by_user_id: Optional[str] = None) -> List[Resource]:
    seeded: List[Resource] = []
    for r_data in DEFAULT_RESOURCES:
        existing = db.query(Resource).filter(Resource.resource_code == r_data["resource_code"]).first()
        if not existing:
            new_r = Resource(
                resource_code=r_data["resource_code"],
                resource_name=r_data["resource_name"],
                resource_category=r_data["resource_category"],
                unit=r_data["unit"],
                description=r_data["description"],
                status=r_data["status"],
                created_by=created_by_user_id,
                metadata_json=r_data["metadata_json"]
            )
            db.add(new_r)
            db.flush()
            seeded.append(new_r)
        else:
            seeded.append(existing)
    return seeded


def seed_default_mappings(db: Session, created_by_user_id: Optional[str] = None) -> List[CalculationResourceMapping]:
    seed_default_resources(db, created_by_user_id)
    mat_res = db.query(Resource).filter(Resource.resource_code == "MATERIAL-CONCRETE").first()
    seeded: List[CalculationResourceMapping] = []
    if mat_res:
        existing = db.query(CalculationResourceMapping).filter(
            CalculationResourceMapping.calculation_type == "CONCRETE_VOLUME_RECTANGULAR",
            CalculationResourceMapping.calculation_version == "1.0",
            CalculationResourceMapping.resource_id == mat_res.id,
            CalculationResourceMapping.source_unit == "m3"
        ).first()
        if not existing:
            mapping = CalculationResourceMapping(
                calculation_type="CONCRETE_VOLUME_RECTANGULAR",
                calculation_version="1.0",
                resource_id=mat_res.id,
                source_unit="m3",
                resource_unit="m3",
                mapping_method="DIRECT",
                status="ACTIVE",
                created_by=created_by_user_id,
                metadata_json={"system_seeded": True}
            )
            db.add(mapping)
            db.flush()
            seeded.append(mapping)
        else:
            seeded.append(existing)
    return seeded


def create_resource(db: Session, resource_in: ResourceCreate, created_by_user_id: Optional[str] = None) -> Resource:
    existing = db.query(Resource).filter(Resource.resource_code == resource_in.resource_code).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Resource with code '{resource_in.resource_code}' already exists"
        )
    resource = Resource(
        resource_code=resource_in.resource_code,
        resource_name=resource_in.resource_name,
        resource_category=resource_in.resource_category.value,
        unit=resource_in.unit,
        description=resource_in.description,
        status=resource_in.status.value,
        created_by=created_by_user_id,
        metadata_json=resource_in.metadata_json or {}
    )
    db.add(resource)
    db.flush()
    return resource


def create_calculation_resource_mapping(
    db: Session,
    mapping_in: CalculationResourceMappingCreate,
    created_by_user_id: Optional[str] = None
) -> CalculationResourceMapping:
    # Verify resource exists
    res = db.query(Resource).filter(Resource.id == mapping_in.resource_id).first()
    if not res:
        raise HTTPException(status_code=404, detail=f"Resource '{mapping_in.resource_id}' not found")

    existing = db.query(CalculationResourceMapping).filter(
        CalculationResourceMapping.calculation_type == mapping_in.calculation_type,
        CalculationResourceMapping.calculation_version == mapping_in.calculation_version,
        CalculationResourceMapping.resource_id == mapping_in.resource_id,
        CalculationResourceMapping.source_unit == mapping_in.source_unit
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Calculation-to-resource mapping already exists for this calculation and resource"
        )

    mapping = CalculationResourceMapping(
        calculation_type=mapping_in.calculation_type,
        calculation_version=mapping_in.calculation_version,
        resource_id=mapping_in.resource_id,
        source_unit=mapping_in.source_unit,
        resource_unit=mapping_in.resource_unit,
        mapping_method=mapping_in.mapping_method,
        status=mapping_in.status.value,
        created_by=created_by_user_id,
        metadata_json=mapping_in.metadata_json or {}
    )
    db.add(mapping)
    db.flush()
    return mapping


# ==============================================================================
# RESOURCE PLAN EXECUTION & VALIDATION
# ==============================================================================

def create_resource_plan(
    db: Session,
    project_id: str,
    user_id: str,
    resource_id: Optional[str] = None,
    resource_code: Optional[str] = None,
    calculation_id: Optional[str] = None,
    estimation_id: Optional[str] = None,
    engineering_element_id: Optional[str] = None,
    metadata_json: Optional[Dict[str, Any]] = None
) -> ResourcePlan:
    # 1. Require at least one authoritative source
    if not calculation_id and not estimation_id:
        raise HTTPException(
            status_code=400,
            detail="Missing authoritative source: either estimation_id or calculation_id must be provided"
        )

    # 2. Lookup Resource
    if not resource_id and not resource_code:
        raise HTTPException(
            status_code=400,
            detail="Missing resource identifier: provide resource_id or resource_code"
        )

    seed_default_resources(db, user_id)

    if resource_id:
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
    else:
        resource = db.query(Resource).filter(Resource.resource_code == resource_code).first()

    if not resource:
        raise HTTPException(
            status_code=404,
            detail=f"Resource '{resource_id or resource_code}' not found"
        )

    if resource.status != ResourceStatusEnum.ACTIVE.value:
        raise HTTPException(
            status_code=400,
            detail=f"Resource '{resource.resource_code}' is not ACTIVE (current status: '{resource.status}')"
        )

    # 3. Handle conflict if BOTH calculation_id AND estimation_id are provided
    if calculation_id and estimation_id:
        calc_check = db.query(EngineeringCalculation).filter(EngineeringCalculation.id == calculation_id).first()
        est_check = db.query(RuleBasedEstimation).filter(RuleBasedEstimation.id == estimation_id).first()

        if not calc_check:
            raise HTTPException(status_code=404, detail=f"EngineeringCalculation '{calculation_id}' not found")
        if not est_check:
            raise HTTPException(status_code=404, detail=f"RuleBasedEstimation '{estimation_id}' not found")

        if calc_check.project_id != project_id:
            raise HTTPException(status_code=400, detail=f"Cross-project calculation rejected: calculation belongs to project '{calc_check.project_id}'")
        if est_check.project_id != project_id:
            raise HTTPException(status_code=400, detail=f"Cross-project estimation rejected: estimation belongs to project '{est_check.project_id}'")

        if est_check.calculation_id != calc_check.id or est_check.engineering_element_id != calc_check.engineering_element_id:
            raise HTTPException(
                status_code=400,
                detail="Conflict: Provided calculation_id and estimation_id do not refer to the same calculation or engineering element."
            )

        # Semantic check: Verify both sources are semantically compatible with the selected resource
        if est_check.estimation_type == "LABOUR_HOURS" and resource.resource_category != ResourceCategoryEnum.LABOUR.value:
            raise HTTPException(
                status_code=400,
                detail=f"Conflicting sources: estimation of type '{est_check.estimation_type}' is incompatible with resource '{resource.resource_code}' of category '{resource.resource_category}'."
            )

    # 4. Resolve source and authoritative values
    calc_obj: Optional[EngineeringCalculation] = None
    est_obj: Optional[RuleBasedEstimation] = None
    mapping_obj: Optional[CalculationResourceMapping] = None
    target_element_id: str
    authoritative_demand: Decimal
    authoritative_demand_unit: str
    planned_qty: Optional[Decimal] = None
    planned_qty_unit: Optional[str] = None
    planning_method: str
    classification: str
    assumptions_dict: Dict[str, Any]
    provenance_summary: Dict[str, Any]

    if estimation_id:
        # Path A: Rule-Based Estimation Source
        est_obj = db.query(RuleBasedEstimation).filter(RuleBasedEstimation.id == estimation_id).first()
        if not est_obj:
            raise HTTPException(
                status_code=404,
                detail=f"RuleBasedEstimation '{estimation_id}' not found"
            )

        if est_obj.project_id != project_id:
            raise HTTPException(
                status_code=400,
                detail=f"Cross-project estimation rejected: estimation belongs to project '{est_obj.project_id}'"
            )

        if est_obj.status != "ESTIMATED":
            raise HTTPException(
                status_code=400,
                detail=f"Invalid estimation status '{est_obj.status}'. Only active ESTIMATED estimations can be planned."
            )

        # Semantic validation: RuleBasedEstimation to Resource compatibility
        if est_obj.estimation_type == "LABOUR_HOURS":
            if resource.resource_category != ResourceCategoryEnum.LABOUR.value:
                raise HTTPException(
                    status_code=400,
                    detail=f"Incompatible resource: estimation type '{est_obj.estimation_type}' requires a LABOUR resource, but resource '{resource.resource_code}' is of category '{resource.resource_category}'"
                )
            if resource.unit != est_obj.result_unit:
                raise HTTPException(
                    status_code=400,
                    detail=f"Incompatible unit: estimation unit '{est_obj.result_unit}' does not match resource unit '{resource.unit}'"
                )

        target_element_id = est_obj.engineering_element_id
        if engineering_element_id and engineering_element_id != target_element_id:
            raise HTTPException(
                status_code=400,
                detail=f"Cross-element mismatch: estimation belongs to element '{target_element_id}' but request specified '{engineering_element_id}'"
            )

        calc_obj = db.query(EngineeringCalculation).filter(
            EngineeringCalculation.id == est_obj.calculation_id
        ).first()
        if not calc_obj:
            raise HTTPException(
                status_code=404,
                detail="Referenced calculation for estimation not found"
            )

        if calc_obj.project_id != project_id:
            raise HTTPException(
                status_code=400,
                detail=f"Cross-project calculation rejected: calculation belongs to project '{calc_obj.project_id}'"
            )

        if calc_obj.status != "CALCULATED":
            raise HTTPException(
                status_code=400,
                detail=f"Referenced calculation status is '{calc_obj.status}', not CALCULATED"
            )

        rule_obj = db.query(Rule).filter(Rule.id == est_obj.rule_id).first()
        if not rule_obj:
            raise HTTPException(status_code=404, detail="Referenced rule not found")
        if rule_obj.status != "ACTIVE":
            raise HTTPException(status_code=400, detail=f"Referenced rule '{rule_obj.rule_code}' is not ACTIVE (status: '{rule_obj.status}')")

        authoritative_demand = est_obj.result_value
        authoritative_demand_unit = est_obj.result_unit
        planned_qty = calc_obj.result_value
        planned_qty_unit = calc_obj.result_unit
        planning_method = PlanningMethodEnum.RULE_BASED.value
        classification = PlanClassificationEnum.ASSUMPTION_BASED.value

        assumptions_dict = {
            "source_type": "RULE_BASED_ESTIMATION",
            "estimation_id": est_obj.id,
            "rule_code": rule_obj.rule_code,
            "rule_version": rule_obj.version,
            "estimation_assumptions": est_obj.assumptions_json,
            "epistemic_classification": PlanClassificationEnum.ASSUMPTION_BASED.value,
            "note": "Resource demand derived from rule-based productivity estimate"
        }

        provenance_summary = {
            "project_id": project_id,
            "engineering_element_id": target_element_id,
            "resource_id": resource.id,
            "resource_code": resource.resource_code,
            "resource_category": resource.resource_category,
            "source_type": "RULE_BASED_ESTIMATION",
            "estimation_id": est_obj.id,
            "calculation_id": calc_obj.id,
            "demand_value": str(authoritative_demand),
            "demand_unit": authoritative_demand_unit,
            "planned_quantity": str(planned_qty) if planned_qty is not None else None,
            "planned_unit": planned_qty_unit
        }

    else:
        # Path B: Engineering Calculation Source -> Requires Explicit CalculationResourceMapping
        calc_obj = db.query(EngineeringCalculation).filter(EngineeringCalculation.id == calculation_id).first()
        if not calc_obj:
            raise HTTPException(
                status_code=404,
                detail=f"EngineeringCalculation '{calculation_id}' not found"
            )

        if calc_obj.project_id != project_id:
            raise HTTPException(
                status_code=400,
                detail=f"Cross-project calculation rejected: calculation belongs to project '{calc_obj.project_id}'"
            )

        if calc_obj.status != "CALCULATED":
            raise HTTPException(
                status_code=400,
                detail=f"Invalid calculation status '{calc_obj.status}'. Only active CALCULATED calculations can be planned."
            )

        target_element_id = calc_obj.engineering_element_id
        if engineering_element_id and engineering_element_id != target_element_id:
            raise HTTPException(
                status_code=400,
                detail=f"Cross-element mismatch: calculation belongs to element '{target_element_id}' but request specified '{engineering_element_id}'"
            )

        # Explicit Mapping Lookup
        seed_default_mappings(db, user_id)
        mapping_obj = db.query(CalculationResourceMapping).filter(
            CalculationResourceMapping.calculation_type == calc_obj.calculation_type,
            CalculationResourceMapping.calculation_version == calc_obj.calculation_version,
            CalculationResourceMapping.resource_id == resource.id,
            CalculationResourceMapping.source_unit == calc_obj.result_unit
        ).first()

        if not mapping_obj:
            raise HTTPException(
                status_code=400,
                detail=f"No explicit calculation-to-resource mapping found for calculation '{calc_obj.calculation_type}' v'{calc_obj.calculation_version}' -> resource '{resource.resource_code}' with source unit '{calc_obj.result_unit}'"
            )

        if mapping_obj.status != MappingStatusEnum.ACTIVE.value:
            raise HTTPException(
                status_code=400,
                detail=f"Calculation-to-resource mapping is not ACTIVE (current status: '{mapping_obj.status}')"
            )

        if mapping_obj.resource_unit != resource.unit:
            raise HTTPException(
                status_code=400,
                detail=f"Mapping unit mismatch: mapping resource unit '{mapping_obj.resource_unit}' != resource unit '{resource.unit}'"
            )

        authoritative_demand = calc_obj.result_value
        authoritative_demand_unit = mapping_obj.resource_unit
        planned_qty = calc_obj.result_value
        planned_qty_unit = calc_obj.result_unit
        planning_method = PlanningMethodEnum.DETERMINISTIC.value
        classification = PlanClassificationEnum.CALCULATED.value

        assumptions_dict = {
            "source_type": "ENGINEERING_CALCULATION",
            "calculation_id": calc_obj.id,
            "calculation_type": calc_obj.calculation_type,
            "mapping_id": mapping_obj.id,
            "mapping_method": mapping_obj.mapping_method,
            "epistemic_classification": PlanClassificationEnum.CALCULATED.value,
            "note": "Resource demand directly derived from deterministic engineering calculation via explicit semantic mapping"
        }

        provenance_summary = {
            "project_id": project_id,
            "engineering_element_id": target_element_id,
            "resource_id": resource.id,
            "resource_code": resource.resource_code,
            "resource_category": resource.resource_category,
            "source_type": "ENGINEERING_CALCULATION",
            "calculation_id": calc_obj.id,
            "mapping_id": mapping_obj.id,
            "calculation_type": mapping_obj.calculation_type,
            "calculation_version": mapping_obj.calculation_version,
            "mapping_method": mapping_obj.mapping_method,
            "source_unit": mapping_obj.source_unit,
            "resource_unit": mapping_obj.resource_unit,
            "demand_value": str(authoritative_demand),
            "demand_unit": authoritative_demand_unit,
            "planned_quantity": str(planned_qty),
            "planned_unit": planned_qty_unit
        }

    # 5. Verify Engineering Element
    element = db.query(EngineeringElement).filter(
        EngineeringElement.id == target_element_id
    ).first()
    if not element:
        raise HTTPException(
            status_code=404,
            detail=f"EngineeringElement '{target_element_id}' not found"
        )
    if element.project_id != project_id:
        raise HTTPException(
            status_code=400,
            detail=f"Cross-project engineering element rejected: element belongs to project '{element.project_id}'"
        )

    # 6. Demand positivity validation
    if authoritative_demand is None or authoritative_demand <= Decimal("0"):
        raise HTTPException(
            status_code=400,
            detail=f"Resource demand must be strictly positive (> 0). Value: {authoritative_demand}"
        )

    # 7. Unit compatibility validation
    if resource.unit != authoritative_demand_unit:
        raise HTTPException(
            status_code=400,
            detail=f"Incompatible units: resource '{resource.resource_code}' unit is '{resource.unit}', but planned demand unit is '{authoritative_demand_unit}'"
        )

    # 8. Supersede prior active plans for the same element and resource
    prior_plans = db.query(ResourcePlan).filter(
        ResourcePlan.project_id == project_id,
        ResourcePlan.engineering_element_id == element.id,
        ResourcePlan.resource_id == resource.id,
        ResourcePlan.status == PlanStatusEnum.PLANNED.value
    ).all()
    for prior in prior_plans:
        prior.status = PlanStatusEnum.SUPERSEDED.value

    # 9. Persist ResourcePlan
    plan = ResourcePlan(
        project_id=project_id,
        engineering_element_id=element.id,
        resource_id=resource.id,
        calculation_id=calc_obj.id,
        estimation_id=est_obj.id if est_obj else None,
        mapping_id=mapping_obj.id if mapping_obj else None,
        planned_quantity=planned_qty,
        planned_unit=planned_qty_unit,
        resource_demand=authoritative_demand,
        resource_demand_unit=authoritative_demand_unit,
        planning_method=planning_method,
        classification=classification,
        assumptions_json=assumptions_dict,
        provenance_json=provenance_summary,
        status=PlanStatusEnum.PLANNED.value,
        created_by=user_id,
        metadata_json=metadata_json or {}
    )
    db.add(plan)
    db.flush()

    # 10. Transactional Audit Log
    log_action(
        db,
        user_id,
        "RESOURCE_PLAN_CREATED",
        "ResourcePlan",
        plan.id,
        f"Planned {resource.resource_code} ({resource.resource_category}): demand {authoritative_demand} {authoritative_demand_unit} for {element.element_name} [{planning_method}/{classification}]"
    )

    return plan


def build_resource_plan_response(db: Session, plan: ResourcePlan) -> ResourcePlanResponse:
    resource = plan.resource
    element = plan.engineering_element
    calc = plan.calculation
    est = plan.estimation
    mapping = plan.mapping

    # Reconstruct provenance hierarchy
    calc_provenance_inputs = []
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
                            pg = ev.page
                            if pg:
                                fact_info["page_id"] = pg.id
                                fact_info["page_number"] = pg.page_number
                                doc = pg.document
                                if doc:
                                    fact_info["document_id"] = doc.id
                                    fact_info["original_filename"] = doc.original_filename
                                    proj = doc.project
                                    if proj:
                                        fact_info["project_id"] = proj.id
                                        fact_info["project_name"] = proj.name
                calc_provenance_inputs.append(fact_info)

    calc_hierarchy = None
    if calc:
        calc_hierarchy = {
            "id": calc.id,
            "calculation_type": calc.calculation_type,
            "calculation_version": calc.calculation_version,
            "status": calc.status,
            "result_value": str(calc.result_value) if calc.result_value is not None else None,
            "result_unit": calc.result_unit,
            "formula_identifier": calc.formula_identifier,
            "formula_expression": calc.formula_expression,
            "inputs_provenance": calc_provenance_inputs
        }

    est_hierarchy = None
    if est:
        est_hierarchy = {
            "id": est.id,
            "rule_id": est.rule_id,
            "rule_code": est.rule.rule_code if est.rule else None,
            "rule_version": est.rule_version,
            "estimation_type": est.estimation_type,
            "status": est.status,
            "input_value": str(est.input_value),
            "input_unit": est.input_unit,
            "result_value": str(est.result_value),
            "result_unit": est.result_unit,
            "parameters": est.parameters_json,
            "assumptions": est.assumptions_json
        }

    mapping_hierarchy = None
    if mapping:
        mapping_hierarchy = {
            "id": mapping.id,
            "calculation_type": mapping.calculation_type,
            "calculation_version": mapping.calculation_version,
            "mapping_method": mapping.mapping_method,
            "source_unit": mapping.source_unit,
            "resource_unit": mapping.resource_unit,
            "status": mapping.status
        }

    elem_hierarchy = None
    if element:
        elem_hierarchy = {
            "id": element.id,
            "element_name": element.element_name,
            "element_type": element.element_type,
            "verification_status": element.verification_status
        }

    proj = plan.project
    proj_hierarchy = {
        "id": proj.id if proj else plan.project_id,
        "name": proj.name if proj else None
    }

    full_hierarchy = {
        "resource_plan_id": plan.id,
        "planning_method": plan.planning_method,
        "classification": plan.classification,
        "status": plan.status,
        "resource": {
            "id": resource.id if resource else plan.resource_id,
            "resource_code": resource.resource_code if resource else None,
            "resource_name": resource.resource_name if resource else None,
            "resource_category": resource.resource_category if resource else None,
            "unit": resource.unit if resource else plan.resource_demand_unit
        },
        "demand": {
            "value": str(plan.resource_demand),
            "unit": plan.resource_demand_unit
        },
        "planned_quantity": {
            "value": str(plan.planned_quantity) if plan.planned_quantity is not None else None,
            "unit": plan.planned_unit
        },
        "mapping": mapping_hierarchy,
        "estimation": est_hierarchy,
        "calculation": calc_hierarchy,
        "engineering_element": elem_hierarchy,
        "project": proj_hierarchy
    }

    return ResourcePlanResponse(
        id=plan.id,
        project_id=plan.project_id,
        engineering_element_id=plan.engineering_element_id,
        resource_id=plan.resource_id,
        resource_code=resource.resource_code if resource else None,
        resource_name=resource.resource_name if resource else None,
        resource_category=resource.resource_category if resource else None,
        resource_unit=resource.unit if resource else None,
        source_type="RULE_BASED_ESTIMATION" if plan.estimation_id else "ENGINEERING_CALCULATION",
        calculation_id=plan.calculation_id,
        estimation_id=plan.estimation_id,
        mapping_id=plan.mapping_id,
        planned_quantity=plan.planned_quantity,
        planned_unit=plan.planned_unit,
        resource_demand=plan.resource_demand,
        resource_demand_unit=plan.resource_demand_unit,
        planning_method=plan.planning_method,
        classification=plan.classification,
        assumptions_json=plan.assumptions_json,
        provenance_json=plan.provenance_json,
        status=plan.status,
        created_by=plan.created_by,
        created_at=plan.created_at,
        metadata_json=plan.metadata_json,
        provenance_hierarchy=full_hierarchy
    )
