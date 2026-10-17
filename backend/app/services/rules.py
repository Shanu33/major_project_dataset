from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.db.models import Rule, User

# ==============================================================================
# RULE STRATEGY DEFINITIONS & REGISTRY
# ==============================================================================

class RuleDefinition(ABC):
    rule_code: str
    rule_version: str
    rule_name: str
    rule_category: str
    supported_input_units: List[str]
    supported_parameter_units: List[str]
    output_unit: str
    formula_identifier: str
    formula_expression: str
    source_reference: str

    @abstractmethod
    def validate_parameters(self, raw_params: Dict[str, Any]) -> Dict[str, Decimal]:
        pass

    @abstractmethod
    def execute(self, quantity: Decimal, parameters: Dict[str, Decimal]) -> Decimal:
        pass


class LabourHoursFromQuantityRule(RuleDefinition):
    rule_code = "LABOUR_HOURS_FROM_QUANTITY"
    rule_version = "1.0"
    rule_name = "Labour Hours from Quantity"
    rule_category = "LABOUR_PRODUCTIVITY"
    supported_input_units = ["m3"]
    supported_parameter_units = ["m3/hour", "m3/labour-hour"]
    output_unit = "labour-hour"
    formula_identifier = "QUANTITY_DIVIDED_BY_PRODUCTIVITY"
    formula_expression = "labour_hours = quantity / productivity_rate"
    source_reference = "IS 7272 / Standard Construction Output Norms"

    def validate_parameters(self, raw_params: Dict[str, Any]) -> Dict[str, Decimal]:
        if not isinstance(raw_params, dict):
            raise HTTPException(status_code=400, detail="Rule parameters must be provided as a dictionary")

        if "productivity_rate" not in raw_params or raw_params["productivity_rate"] is None:
            raise HTTPException(status_code=400, detail="Missing required rule parameter 'productivity_rate'")

        try:
            rate = Decimal(str(raw_params["productivity_rate"]))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid numeric format for 'productivity_rate'")

        if rate <= Decimal("0"):
            raise HTTPException(
                status_code=400,
                detail=f"Productivity rate must be strictly positive (> 0). Provided: {rate}"
            )

        prod_unit = raw_params.get("productivity_unit")
        if not prod_unit:
            raise HTTPException(status_code=400, detail="Missing required rule parameter 'productivity_unit'")

        if prod_unit not in self.supported_parameter_units:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported productivity_unit '{prod_unit}'. Supported: {self.supported_parameter_units}"
            )

        return {"productivity_rate": rate}

    def execute(self, quantity: Decimal, parameters: Dict[str, Decimal]) -> Decimal:
        if quantity <= Decimal("0"):
            raise HTTPException(
                status_code=400,
                detail=f"Input quantity must be strictly positive (> 0). Provided: {quantity}"
            )
        rate = parameters["productivity_rate"]
        hours = quantity / rate
        return hours.quantize(Decimal("0.000001"))


RULE_REGISTRY: Dict[Tuple[str, str], RuleDefinition] = {
    (LabourHoursFromQuantityRule.rule_code, LabourHoursFromQuantityRule.rule_version): LabourHoursFromQuantityRule(),
}

def get_rule_strategy(rule_code: str, version: str) -> RuleDefinition:
    strategy = RULE_REGISTRY.get((rule_code, version))
    if not strategy:
        raise HTTPException(
            status_code=400,
            detail=f"Rule '{rule_code}' version '{version}' is not supported in the estimation engine"
        )
    return strategy


def seed_default_rules(db: Session, created_by_user_id: str) -> List[Rule]:
    seeded: List[Rule] = []
    for (code, ver), defn in RULE_REGISTRY.items():
        existing = db.query(Rule).filter(
            Rule.rule_code == code,
            Rule.version == ver
        ).first()
        if not existing:
            new_rule = Rule(
                rule_code=code,
                rule_name=defn.rule_name,
                description=f"Standard rule for {defn.rule_name}",
                rule_category=defn.rule_category,
                input_unit=defn.supported_input_units[0],
                output_unit=defn.output_unit,
                formula_identifier=defn.formula_identifier,
                formula_expression=defn.formula_expression,
                parameters_json={
                    "required": ["productivity_rate", "productivity_unit"],
                    "supported_units": defn.supported_parameter_units,
                    "default_productivity_unit": "m3/hour"
                },
                source_reference=defn.source_reference,
                version=ver,
                status="ACTIVE",
                created_by=created_by_user_id,
                metadata_json={"system_seeded": True}
            )
            db.add(new_rule)
            db.flush()
            seeded.append(new_rule)
    return seeded
