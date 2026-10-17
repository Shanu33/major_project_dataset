"""Phase 1K: Deterministic Cost Estimation & Rate-Based Valuation Foundation.

Provides service functions for:
- Declaring and versioning cost rates (global and project-specific)
- Confirming cost rates with atomic supersession
- Deleting draft cost rates
- Deterministic calculation execution (total_cost = quantity * rate) across:
  - BOQ_STATED
  - ENGINEERING_CALCULATED
  - VERIFIED_RECONCILED (with explicit decision model)
- Project cost aggregation and comparative valuation
- Transactional audit logging
"""
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.models import (
    Project,
    CostRate,
    CostCalculation,
    BoqItem,
    BoqCalculationMapping,
    BoqReconciliation,
    EngineeringCalculation,
    Document,
    Evidence,
)
from app.schemas.schemas import (
    CostRateCreate,
    CostCalculationCreate,
    CostRateStatusEnum,
    CostCalculationStatusEnum,
    QuantityBasisEnum,
    ReconciliationDecisionEnum,
)
from app.services.audit import log_action
from app.services.unit_normalization import are_units_compatible


def declare_cost_rate(
    db: Session,
    project_id: Optional[str],
    payload: CostRateCreate,
    current_user_id: str,
) -> CostRate:
    """
    Creates a new cost rate in DRAFT status.
    Can be global (project_id=None) or project-specific.
    """
    # 1. Project validation if project-specific
    if project_id:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found.",
            )
    else:
        # Global rate cannot reference project documents
        if payload.source_document_id or payload.source_evidence_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Global cost rates cannot reference project documents or evidence.",
            )

    # 2. Document & evidence validation if supplied
    if payload.source_document_id:
        doc = db.query(Document).filter(Document.id == payload.source_document_id).first()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source document {payload.source_document_id} not found.",
            )
        if doc.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source document does not belong to specified project.",
            )

        if payload.source_evidence_id:
            ev = db.query(Evidence).filter(Evidence.id == payload.source_evidence_id).first()
            if not ev:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Source evidence {payload.source_evidence_id} not found.",
                )
            if ev.document_id != payload.source_document_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Source evidence does not belong to the source document.",
                )

    # 3. Rate value validation
    if payload.rate_value < Decimal("0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rate value cannot be negative.",
        )

    # 4. Rate code validation
    rate_code_clean = payload.rate_code.strip()
    if not rate_code_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="rate_code cannot be empty.",
        )

    # 4b. Unit validation
    unit_clean = payload.unit.strip()
    if not unit_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="unit cannot be empty.",
        )

    # 4c. Description validation
    desc_clean = payload.description.strip()
    if not desc_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="description cannot be empty.",
        )

    # 4d. Source reference validation
    ref_clean = payload.source_reference.strip()
    if not ref_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="source_reference cannot be empty.",
        )

    # 5. Replaced rate validation if provided
    if payload.replaces_rate_id:
        replaced_rate = db.query(CostRate).filter(CostRate.id == payload.replaces_rate_id).first()
        if not replaced_rate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Replaced rate {payload.replaces_rate_id} not found.",
            )
        if replaced_rate.rate_code != rate_code_clean:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New rate version must maintain the same rate_code.",
            )
        if (replaced_rate.project_id is None and project_id is not None) or \
           (replaced_rate.project_id is not None and project_id is None) or \
           (replaced_rate.project_id != project_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New rate version cannot change project scope.",
            )
        if replaced_rate.status != CostRateStatusEnum.CONFIRMED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only CONFIRMED rates can be replaced by a new version.",
            )

    # 6. Check for duplicate active confirmed rate if not replacing
    existing_confirmed = db.query(CostRate).filter(
        CostRate.rate_code == rate_code_clean,
        CostRate.status == CostRateStatusEnum.CONFIRMED.value,
        CostRate.project_id == project_id,
    ).first()

    if existing_confirmed and not payload.replaces_rate_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Active confirmed rate with code '{rate_code_clean}' already exists. Provide replaces_rate_id to create a new version.",
        )

    # 7. Create DRAFT rate
    rate = CostRate(
        project_id=project_id,
        rate_code=rate_code_clean,
        description=payload.description.strip(),
        unit=payload.unit.strip(),
        rate_value=payload.rate_value.quantize(Decimal("0.000001")),
        currency=payload.currency.strip().upper(),
        source_type=payload.source_type.value,
        source_reference=payload.source_reference.strip(),
        source_document_id=payload.source_document_id,
        source_evidence_id=payload.source_evidence_id,
        version=payload.version.strip() if payload.version else "1.0",
        status=CostRateStatusEnum.DRAFT.value,
        replaces_rate_id=payload.replaces_rate_id,
        created_by=current_user_id,
        metadata_json=payload.metadata_json,
    )
    db.add(rate)
    db.flush()

    log_action(
        db=db,
        user_id=current_user_id,
        action="DECLARE_COST_RATE",
        entity_type="CostRate",
        entity_id=rate.id,
        reason=f"Declared cost rate {rate.rate_code} v{rate.version} in DRAFT status",
    )
    db.commit()
    db.refresh(rate)
    return rate


def confirm_cost_rate(
    db: Session,
    rate_id: str,
    current_user_id: str,
) -> CostRate:
    """
    Confirms a DRAFT cost rate. If it replaces a previous version,
    atomically supersedes the previous rate.
    """
    rate = db.query(CostRate).filter(CostRate.id == rate_id).first()
    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cost rate {rate_id} not found.",
        )

    if rate.status != CostRateStatusEnum.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only DRAFT rates can be confirmed. Current status: {rate.status}.",
        )

    # Check that no other CONFIRMED rate has this rate_code in this scope
    existing_query = db.query(CostRate).filter(
        CostRate.rate_code == rate.rate_code,
        CostRate.status == CostRateStatusEnum.CONFIRMED.value,
        CostRate.project_id == rate.project_id,
        CostRate.id != rate.id,
    )
    if rate.replaces_rate_id:
        existing_query = existing_query.filter(CostRate.id != rate.replaces_rate_id)
    existing_confirmed = existing_query.first()

    if existing_confirmed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An active confirmed rate for '{rate.rate_code}' already exists ({existing_confirmed.id}).",
        )

    try:
        # If it replaces a previous rate, supersede that previous rate
        if rate.replaces_rate_id:
            old_rate = db.query(CostRate).filter(CostRate.id == rate.replaces_rate_id).first()
            if old_rate:
                if old_rate.status != CostRateStatusEnum.SUPERSEDED.value:
                    old_rate.status = CostRateStatusEnum.SUPERSEDED.value
                    db.flush()
                    log_action(
                        db=db,
                        user_id=current_user_id,
                        action="SUPERSEDE_COST_RATE",
                        entity_type="CostRate",
                        entity_id=old_rate.id,
                        reason=f"Rate superseded by new version {rate.id}",
                    )

        now = datetime.now(timezone.utc)
        rate.status = CostRateStatusEnum.CONFIRMED.value
        rate.confirmed_by = current_user_id
        rate.confirmed_at = now

        log_action(
            db=db,
            user_id=current_user_id,
            action="CONFIRM_COST_RATE",
            entity_type="CostRate",
            entity_id=rate.id,
            reason=f"Confirmed cost rate {rate.rate_code} v{rate.version}",
        )
        db.commit()
        db.refresh(rate)
        return rate
    except Exception:
        db.rollback()
        raise


def delete_draft_cost_rate(
    db: Session,
    rate_id: str,
    current_user_id: str,
) -> None:
    """
    Deletes a DRAFT cost rate. Rejects deletion if CONFIRMED or SUPERSEDED.
    """
    rate = db.query(CostRate).filter(CostRate.id == rate_id).first()
    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cost rate {rate_id} not found.",
        )

    if rate.status != CostRateStatusEnum.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete non-draft cost rate. Confirmed and superseded rates are immutable.",
        )

    try:
        db.delete(rate)
        log_action(
            db=db,
            user_id=current_user_id,
            action="DELETE_COST_RATE_DRAFT",
            entity_type="CostRate",
            entity_id=rate_id,
            reason="Deleted draft cost rate",
        )
        db.commit()
    except Exception:
        db.rollback()
        raise


def list_cost_rates(
    db: Session,
    project_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    rate_code: Optional[str] = None,
    include_global: bool = True,
) -> List[CostRate]:
    """
    Lists cost rates with optional filters.
    """
    query = db.query(CostRate)

    if project_id:
        if include_global:
            query = query.filter(or_(CostRate.project_id == project_id, CostRate.project_id.is_(None)))
        else:
            query = query.filter(CostRate.project_id == project_id)
    else:
        # If no project_id specified, list global rates unless requested otherwise
        if not include_global:
            query = query.filter(CostRate.project_id.isnot(None))

    if status_filter:
        query = query.filter(CostRate.status == status_filter)

    if rate_code:
        query = query.filter(CostRate.rate_code == rate_code)

    return query.order_by(CostRate.created_at.desc()).all()


def execute_cost_calculation(
    db: Session,
    project_id: str,
    payload: CostCalculationCreate,
    current_user_id: str,
) -> CostCalculation:
    """
    Executes a deterministic cost calculation: total_cost = quantity * rate.
    Enforces exact Decimal arithmetic, unit compatibility, and project boundary isolation.
    Atomically supersedes any existing active calculation for the same source entity.
    """
    # 1. Project validation
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found.",
        )

    # 2. Rate validation
    rate = db.query(CostRate).filter(CostRate.id == payload.cost_rate_id).first()
    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cost rate {payload.cost_rate_id} not found.",
        )

    if rate.status != CostRateStatusEnum.CONFIRMED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cost rate must be in CONFIRMED status to be used in calculation. Current status: {rate.status}.",
        )

    if rate.project_id is not None and rate.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project-specific cost rate belongs to a different project.",
        )

    # 3. Source resolution by quantity basis
    quantity_value: Decimal
    quantity_unit: str
    boq_item_id: Optional[str] = None
    calculation_id: Optional[str] = None
    reconciliation_id: Optional[str] = None
    reconciliation_decision: Optional[str] = None
    decision_reason: Optional[str] = None
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None

    if payload.quantity_basis == QuantityBasisEnum.BOQ_STATED:
        if not payload.boq_item_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="boq_item_id is required for BOQ_STATED quantity basis.",
            )
        if payload.calculation_id or payload.reconciliation_id or payload.reconciliation_decision:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="calculation_id, reconciliation_id, and reconciliation_decision must be null for BOQ_STATED.",
            )

        boq_item = db.query(BoqItem).filter(BoqItem.id == payload.boq_item_id).first()
        if not boq_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"BOQ item {payload.boq_item_id} not found.",
            )
        if boq_item.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="BOQ item does not belong to specified project.",
            )
        if boq_item.status != "CONFIRMED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"BOQ item must be CONFIRMED. Current status: {boq_item.status}.",
            )

        quantity_value = Decimal(str(boq_item.stated_quantity))
        quantity_unit = boq_item.unit
        boq_item_id = boq_item.id

    elif payload.quantity_basis == QuantityBasisEnum.ENGINEERING_CALCULATED:
        if not payload.calculation_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="calculation_id is required for ENGINEERING_CALCULATED quantity basis.",
            )
        if payload.boq_item_id or payload.reconciliation_id or payload.reconciliation_decision:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="boq_item_id, reconciliation_id, and reconciliation_decision must be null for ENGINEERING_CALCULATED.",
            )

        calc = db.query(EngineeringCalculation).filter(EngineeringCalculation.id == payload.calculation_id).first()
        if not calc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Engineering calculation {payload.calculation_id} not found.",
            )
        if calc.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Engineering calculation does not belong to specified project.",
            )

        quantity_value = Decimal(str(calc.result_value))
        quantity_unit = calc.result_unit
        calculation_id = calc.id

    elif payload.quantity_basis == QuantityBasisEnum.VERIFIED_RECONCILED:
        if not payload.reconciliation_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="reconciliation_id is required for VERIFIED_RECONCILED quantity basis.",
            )
        if not payload.reconciliation_decision:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="reconciliation_decision is required for VERIFIED_RECONCILED quantity basis.",
            )
        if not payload.decision_reason or not payload.decision_reason.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="decision_reason is required for VERIFIED_RECONCILED quantity basis.",
            )

        rec = db.query(BoqReconciliation).filter(BoqReconciliation.id == payload.reconciliation_id).first()
        if not rec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reconciliation {payload.reconciliation_id} not found.",
            )
        if rec.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reconciliation does not belong to specified project.",
            )

        reconciliation_id = rec.id
        reconciliation_decision = payload.reconciliation_decision.value
        decision_reason = payload.decision_reason.strip()
        decided_by = current_user_id
        decided_at = datetime.now(timezone.utc)

        if payload.reconciliation_decision == ReconciliationDecisionEnum.ACCEPT_MATCH:
            if rec.discrepancy_status != "MATCH":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot choose ACCEPT_MATCH when discrepancy status is {rec.discrepancy_status}.",
                )
            quantity_value = Decimal(str(rec.calculated_quantity))
            quantity_unit = rec.calculated_unit
        elif payload.reconciliation_decision == ReconciliationDecisionEnum.ACCEPT_CALCULATED:
            quantity_value = Decimal(str(rec.calculated_quantity))
            quantity_unit = rec.calculated_unit
        elif payload.reconciliation_decision == ReconciliationDecisionEnum.ACCEPT_BOQ:
            quantity_value = Decimal(str(rec.boq_quantity))
            quantity_unit = rec.boq_unit
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown reconciliation decision {payload.reconciliation_decision}.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown quantity basis {payload.quantity_basis}.",
        )

    # 4. Unit compatibility check
    if not are_units_compatible(quantity_unit, rate.unit):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"UNIT_MISMATCH: Quantity unit '{quantity_unit}' is incompatible with rate unit '{rate.unit}'.",
        )

    # 5. Deterministic calculation: total_cost = quantity * rate
    calc_rate_value = Decimal(str(rate.rate_value))
    total_cost = (quantity_value * calc_rate_value).quantize(Decimal("0.000001"))

    try:
        # 6. Atomic supersession of existing active calculation for the same source
        existing_active: Optional[CostCalculation] = None
        if payload.quantity_basis == QuantityBasisEnum.BOQ_STATED:
            existing_active = db.query(CostCalculation).filter(
                CostCalculation.boq_item_id == boq_item_id,
                CostCalculation.status == CostCalculationStatusEnum.CALCULATED.value,
                CostCalculation.quantity_basis == QuantityBasisEnum.BOQ_STATED.value,
            ).first()
        elif payload.quantity_basis == QuantityBasisEnum.ENGINEERING_CALCULATED:
            existing_active = db.query(CostCalculation).filter(
                CostCalculation.calculation_id == calculation_id,
                CostCalculation.status == CostCalculationStatusEnum.CALCULATED.value,
                CostCalculation.quantity_basis == QuantityBasisEnum.ENGINEERING_CALCULATED.value,
            ).first()
        elif payload.quantity_basis == QuantityBasisEnum.VERIFIED_RECONCILED:
            existing_active = db.query(CostCalculation).filter(
                CostCalculation.reconciliation_id == reconciliation_id,
                CostCalculation.status == CostCalculationStatusEnum.CALCULATED.value,
                CostCalculation.quantity_basis == QuantityBasisEnum.VERIFIED_RECONCILED.value,
            ).first()

        if existing_active:
            existing_active.status = CostCalculationStatusEnum.SUPERSEDED.value
            db.flush()
            log_action(
                db=db,
                user_id=current_user_id,
                action="SUPERSEDE_COST_CALCULATION",
                entity_type="CostCalculation",
                entity_id=existing_active.id,
                reason="Superseded by recalculation",
            )

        # 7. Construct provenance snapshot
        provenance_json = {
            "quantity_basis": payload.quantity_basis.value,
            "quantity_value": str(quantity_value),
            "quantity_unit": quantity_unit,
            "rate_id": rate.id,
            "rate_code": rate.rate_code,
            "rate_value": str(calc_rate_value),
            "rate_unit": rate.unit,
            "rate_version": rate.version,
            "currency": rate.currency,
            "total_cost": str(total_cost),
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }
        if boq_item_id:
            provenance_json["boq_item_id"] = boq_item_id
        if calculation_id:
            provenance_json["calculation_id"] = calculation_id
        if reconciliation_id:
            provenance_json["reconciliation_id"] = reconciliation_id
            provenance_json["reconciliation_decision"] = reconciliation_decision
            provenance_json["decision_reason"] = decision_reason
            provenance_json["decided_by"] = decided_by
            provenance_json["decided_at"] = decided_at.isoformat() if decided_at else None

        # 8. Create calculation record
        cost_calc = CostCalculation(
            project_id=project_id,
            cost_rate_id=rate.id,
            quantity_basis=payload.quantity_basis.value,
            boq_item_id=boq_item_id,
            calculation_id=calculation_id,
            reconciliation_id=reconciliation_id,
            reconciliation_decision=reconciliation_decision,
            decision_reason=decision_reason,
            decided_by=decided_by,
            decided_at=decided_at,
            quantity_value=quantity_value.quantize(Decimal("0.000001")),
            quantity_unit=quantity_unit,
            rate_value=calc_rate_value.quantize(Decimal("0.000001")),
            rate_unit=rate.unit,
            rate_version=rate.version,
            currency=rate.currency,
            total_cost=total_cost,
            status=CostCalculationStatusEnum.CALCULATED.value,
            formula_identifier="DIRECT_RATE_VALUATION",
            formula_expression="total_cost = quantity * rate",
            algorithm_version="1.0",
            provenance_json=provenance_json,
            created_by=current_user_id,
            metadata_json=payload.metadata_json,
        )
        db.add(cost_calc)
        db.flush()

        log_action(
            db=db,
            user_id=current_user_id,
            action="EXECUTE_COST_CALCULATION",
            entity_type="CostCalculation",
            entity_id=cost_calc.id,
            reason=f"Executed cost calculation with basis {payload.quantity_basis.value}: total {total_cost} {rate.currency}",
        )
        db.commit()
        db.refresh(cost_calc)
        return cost_calc
    except Exception:
        db.rollback()
        raise


def list_cost_calculations(
    db: Session,
    project_id: str,
    quantity_basis: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> List[CostCalculation]:
    """
    Lists cost calculations for a project.
    """
    query = db.query(CostCalculation).filter(CostCalculation.project_id == project_id)

    if quantity_basis:
        query = query.filter(CostCalculation.quantity_basis == quantity_basis)

    if status_filter:
        query = query.filter(CostCalculation.status == status_filter)

    return query.order_by(CostCalculation.created_at.desc()).all()


def get_project_cost_summary(
    db: Session,
    project_id: str,
) -> Dict[str, Any]:
    """
    Aggregates project costs into totals by quantity basis and computes
    comparable valuation delta strictly over verified mapped items having both
    active BOQ and engineering calculations.
    """
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found.",
        )

    # Active calculations in project
    active_calcs = db.query(CostCalculation).filter(
        CostCalculation.project_id == project_id,
        CostCalculation.status == CostCalculationStatusEnum.CALCULATED.value,
    ).all()

    boq_stated_total = Decimal("0.000000")
    engineering_calculated_total = Decimal("0.000000")
    verified_reconciled_total = Decimal("0.000000")
    distinct_currencies = {c.currency for c in active_calcs}
    if len(distinct_currencies) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mixed currencies found in active calculations for project: {distinct_currencies}. Multi-currency aggregation without FX conversion is prohibited.",
        )
    currency = list(distinct_currencies)[0] if distinct_currencies else "INR"

    boq_calc_by_item: Dict[str, CostCalculation] = {}
    eng_calc_by_calc_id: Dict[str, CostCalculation] = {}

    for c in active_calcs:
        if c.quantity_basis == QuantityBasisEnum.BOQ_STATED.value:
            boq_stated_total += c.total_cost
            if c.boq_item_id:
                boq_calc_by_item[c.boq_item_id] = c
        elif c.quantity_basis == QuantityBasisEnum.ENGINEERING_CALCULATED.value:
            engineering_calculated_total += c.total_cost
            if c.calculation_id:
                eng_calc_by_calc_id[c.calculation_id] = c
        elif c.quantity_basis == QuantityBasisEnum.VERIFIED_RECONCILED.value:
            verified_reconciled_total += c.total_cost

    # Active rates count available to project
    active_rates_count = db.query(CostRate).filter(
        CostRate.status == CostRateStatusEnum.CONFIRMED.value,
        or_(CostRate.project_id == project_id, CostRate.project_id.is_(None)),
    ).count()

    active_calculations_count = len(active_calcs)

    # Verified mappings in project
    verified_mappings = db.query(BoqCalculationMapping).filter(
        BoqCalculationMapping.project_id == project_id,
        BoqCalculationMapping.status == "VERIFIED",
    ).all()

    mapped_boq_ids = set()
    mapped_eng_ids = set()
    comparable_items_count = 0
    comparable_boq_total = Decimal("0.000000")
    comparable_eng_total = Decimal("0.000000")

    for m in verified_mappings:
        mapped_boq_ids.add(m.boq_item_id)
        mapped_eng_ids.add(m.calculation_id)

        # Check if both BOQ and Engineering calculations exist for this verified mapping
        boq_c = boq_calc_by_item.get(m.boq_item_id)
        eng_c = eng_calc_by_calc_id.get(m.calculation_id)

        if boq_c is not None and eng_c is not None:
            comparable_items_count += 1
            comparable_boq_total += boq_c.total_cost
            comparable_eng_total += eng_c.total_cost

    comparable_valuation_delta = (comparable_boq_total - comparable_eng_total).quantize(Decimal("0.000001"))

    # Unmatched items
    total_confirmed_boq = db.query(BoqItem).filter(
        BoqItem.project_id == project_id,
        BoqItem.status == "CONFIRMED",
    ).count()

    total_eng_calcs = db.query(EngineeringCalculation).filter(
        EngineeringCalculation.project_id == project_id,
    ).count()

    unmatched_boq_items_count = max(0, total_confirmed_boq - len(mapped_boq_ids))
    unmatched_engineering_items_count = max(0, total_eng_calcs - len(mapped_eng_ids))

    return {
        "project_id": project_id,
        "boq_stated_total": boq_stated_total.quantize(Decimal("0.000001")),
        "engineering_calculated_total": engineering_calculated_total.quantize(Decimal("0.000001")),
        "verified_reconciled_total": verified_reconciled_total.quantize(Decimal("0.000001")),
        "currency": currency,
        "active_rates_count": active_rates_count,
        "active_calculations_count": active_calculations_count,
        "comparable_items_count": comparable_items_count,
        "unmatched_boq_items_count": unmatched_boq_items_count,
        "unmatched_engineering_items_count": unmatched_engineering_items_count,
        "comparable_valuation_delta": comparable_valuation_delta,
    }
