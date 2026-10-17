"""Phase 1J: BOQ Ingestion, Line Item Representation & Deterministic Quantity Reconciliation.

Provides service functions for:
- Declaring BOQ line items as DRAFT (from official BOQ document)
- Supervisor/Admin confirmation of BOQ items
- Proposing 1:1 DIRECT calculation-to-BOQ mappings
- Supervisor/Admin verification or rejection of mappings
- Deterministic exact Decimal quantity reconciliation calculation
- Querying BOQ items and reconciliations
"""
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import (
    BoqItem,
    BoqCalculationMapping,
    BoqReconciliation,
    Document,
    Evidence,
    EngineeringCalculation,
)
from app.schemas.schemas import (
    BoqItemCreate,
    BoqMappingCreate,
    BoqMappingVerifyRequest,
    BoqVerifyActionEnum,
    BoqReconciliationCreate,
)
from app.services.audit import log_action
from app.services.unit_normalization import are_units_compatible


def declare_boq_item(
    db: Session,
    project_id: str,
    document_id: str,
    payload: BoqItemCreate,
    current_user_id: str,
) -> BoqItem:
    """
    Creates a new BOQ line item in DRAFT status against a verified BOQ document.
    """
    # 1. Validate document exists and belongs to the project
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.project_id == project_id,
    ).first()
    if not doc:
        # Check if doc exists in another project for clean 400 vs 404
        other_doc = db.query(Document).filter(Document.id == document_id).first()
        if other_doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document does not belong to specified project.",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found.",
        )

    # 2. Validate document is BOQ
    is_boq = (doc.document_type == "BOQ") or (doc.classified_document_type == "BOQ")
    if not is_boq:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Referenced document {document_id} is not classified as a BOQ document.",
        )

    # 3. Validate evidence if supplied
    if payload.evidence_id:
        ev = db.query(Evidence).filter(Evidence.id == payload.evidence_id).first()
        if not ev:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evidence {payload.evidence_id} not found.",
            )
        if ev.document_id != document_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Evidence {payload.evidence_id} does not belong to document {document_id}.",
            )

    # 4. Item code must be non-empty and unique within document for active items
    item_code_clean = payload.item_code.strip()
    if not item_code_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="item_code must not be empty.",
        )

    existing_active = db.query(BoqItem).filter(
        BoqItem.document_id == document_id,
        BoqItem.item_code == item_code_clean,
        BoqItem.status.in_(["DRAFT", "CONFIRMED"]),
    ).first()
    if existing_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An active BOQ item with code '{item_code_clean}' already exists in document {document_id}.",
        )

    # 5. Validate replaced BOQ item if supplied
    if payload.replaces_boq_item_id:
        replaced_item = db.query(BoqItem).filter(
            BoqItem.id == payload.replaces_boq_item_id,
            BoqItem.project_id == project_id,
        ).first()
        if not replaced_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Replaced BOQ item {payload.replaces_boq_item_id} not found in project.",
            )

    # 6. Build provenance
    provenance_json: Dict[str, Any] = {
        "source": "USER_DECLARED",
        "document_id": document_id,
        "evidence_id": payload.evidence_id,
        "classification": "DOCUMENT_DERIVED",
        "declared_by": current_user_id,
        "declared_at": datetime.now(timezone.utc).isoformat(),
    }

    item = BoqItem(
        project_id=project_id,
        document_id=document_id,
        evidence_id=payload.evidence_id,
        item_code=item_code_clean,
        description=payload.description.strip(),
        unit=payload.unit.strip(),
        stated_quantity=payload.stated_quantity,
        status="DRAFT",
        classification="DOCUMENT_DERIVED",
        replaces_boq_item_id=payload.replaces_boq_item_id,
        provenance_json=provenance_json,
        created_by=current_user_id,
        metadata_json=payload.metadata_json,
    )
    db.add(item)
    db.flush()

    log_action(
        db=db,
        user_id=current_user_id,
        action="DECLARE_BOQ_ITEM",
        entity_type="boq_item",
        entity_id=item.id,
        reason=f"Declared BOQ item {item.item_code} as DRAFT",
    )
    db.commit()
    db.refresh(item)
    return item


def confirm_boq_item(
    db: Session,
    project_id: str,
    boq_item_id: str,
    current_user_id: str,
) -> BoqItem:
    """
    Confirms a DRAFT BOQ item, freezing contractual attributes. Supervisor/Admin only.
    """
    item = db.query(BoqItem).filter(
        BoqItem.id == boq_item_id,
        BoqItem.project_id == project_id,
    ).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BOQ item {boq_item_id} not found in project.",
        )

    if item.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only DRAFT BOQ items can be confirmed. Current status: '{item.status}'.",
        )

    # If this item replaces a previous item, mark the previous item SUPERSEDED
    if item.replaces_boq_item_id:
        old_item = db.query(BoqItem).filter(
            BoqItem.id == item.replaces_boq_item_id,
            BoqItem.project_id == project_id,
        ).first()
        if old_item and old_item.status in ["DRAFT", "CONFIRMED"]:
            old_item.status = "SUPERSEDED"

    item.status = "CONFIRMED"
    item.confirmed_by = current_user_id
    item.confirmed_at = datetime.now(timezone.utc)
    db.flush()

    log_action(
        db=db,
        user_id=current_user_id,
        action="CONFIRM_BOQ_ITEM",
        entity_type="boq_item",
        entity_id=item.id,
        reason=f"Confirmed BOQ item {item.item_code}",
    )
    db.commit()
    db.refresh(item)
    return item


def list_boq_items(
    db: Session,
    project_id: str,
    document_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[BoqItem]:
    """
    Lists BOQ items for a project with optional filtering and pagination.
    """
    query = db.query(BoqItem).filter(BoqItem.project_id == project_id)
    if document_id:
        query = query.filter(BoqItem.document_id == document_id)
    if status:
        query = query.filter(BoqItem.status == status)
    return query.order_by(BoqItem.created_at.asc()).offset(skip).limit(limit).all()


def propose_boq_mapping(
    db: Session,
    project_id: str,
    payload: BoqMappingCreate,
    current_user_id: str,
) -> BoqCalculationMapping:
    """
    Proposes a 1:1 DIRECT mapping between a CONFIRMED BOQ item and a CALCULATED engineering calculation.
    """
    # 1. Validate BOQ item
    boq = db.query(BoqItem).filter(
        BoqItem.id == payload.boq_item_id,
        BoqItem.project_id == project_id,
    ).first()
    if not boq:
        # Check cross-project
        other_boq = db.query(BoqItem).filter(BoqItem.id == payload.boq_item_id).first()
        if other_boq:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="BOQ item does not belong to specified project.",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BOQ item {payload.boq_item_id} not found.",
        )

    if boq.status != "CONFIRMED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only CONFIRMED BOQ items can be mapped. Current status: '{boq.status}'.",
        )

    # 2. Validate calculation
    calc = db.query(EngineeringCalculation).filter(
        EngineeringCalculation.id == payload.calculation_id,
        EngineeringCalculation.project_id == project_id,
    ).first()
    if not calc:
        other_calc = db.query(EngineeringCalculation).filter(EngineeringCalculation.id == payload.calculation_id).first()
        if other_calc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Engineering calculation does not belong to specified project.",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Engineering calculation {payload.calculation_id} not found.",
        )

    if calc.status != "CALCULATED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Engineering calculation must have status CALCULATED to be mapped. Current status: '{calc.status}'.",
        )

    # 3. True 1:1 Active Mapping Uniqueness checks
    existing_boq_map = db.query(BoqCalculationMapping).filter(
        BoqCalculationMapping.boq_item_id == payload.boq_item_id,
        BoqCalculationMapping.status.in_(["PROPOSED", "VERIFIED"]),
    ).first()
    if existing_boq_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An active mapping already exists for BOQ item {payload.boq_item_id}.",
        )

    existing_calc_map = db.query(BoqCalculationMapping).filter(
        BoqCalculationMapping.calculation_id == payload.calculation_id,
        BoqCalculationMapping.status.in_(["PROPOSED", "VERIFIED"]),
    ).first()
    if existing_calc_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An active mapping already exists for calculation {payload.calculation_id}.",
        )

    mapping = BoqCalculationMapping(
        project_id=project_id,
        boq_item_id=payload.boq_item_id,
        calculation_id=payload.calculation_id,
        mapping_type="DIRECT",
        status="PROPOSED",
        created_by=current_user_id,
        metadata_json=payload.metadata_json,
    )
    db.add(mapping)
    db.flush()

    log_action(
        db=db,
        user_id=current_user_id,
        action="PROPOSE_BOQ_MAPPING",
        entity_type="boq_calculation_mapping",
        entity_id=mapping.id,
        reason="Proposed DIRECT mapping between BOQ item and Engineering Calculation",
    )
    db.commit()
    db.refresh(mapping)
    return mapping


def verify_boq_mapping(
    db: Session,
    project_id: str,
    mapping_id: str,
    payload: BoqMappingVerifyRequest,
    current_user_id: str,
) -> BoqCalculationMapping:
    """
    Verifies or rejects a proposed mapping. Supervisor/Admin only.
    """
    mapping = db.query(BoqCalculationMapping).filter(
        BoqCalculationMapping.id == mapping_id,
        BoqCalculationMapping.project_id == project_id,
    ).first()
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BOQ mapping {mapping_id} not found in project.",
        )

    if mapping.status != "PROPOSED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only PROPOSED mappings can be verified or rejected. Current status: '{mapping.status}'.",
        )

    if payload.action == BoqVerifyActionEnum.REJECT:
        if not payload.rejection_reason or not payload.rejection_reason.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="rejection_reason is mandatory when rejecting a mapping.",
            )
        mapping.status = "REJECTED"
        mapping.verified_by = current_user_id
        mapping.verified_at = datetime.now(timezone.utc)
        mapping.rejection_reason = payload.rejection_reason.strip()
        db.flush()

        log_action(
            db=db,
            user_id=current_user_id,
            action="REJECT_BOQ_MAPPING",
            entity_type="boq_calculation_mapping",
            entity_id=mapping.id,
            reason=f"Rejected mapping: {mapping.rejection_reason}",
        )
    elif payload.action == BoqVerifyActionEnum.VERIFY:
        mapping.status = "VERIFIED"
        mapping.verified_by = current_user_id
        mapping.verified_at = datetime.now(timezone.utc)
        db.flush()

        log_action(
            db=db,
            user_id=current_user_id,
            action="VERIFY_BOQ_MAPPING",
            entity_type="boq_calculation_mapping",
            entity_id=mapping.id,
            reason="Verified DIRECT mapping",
        )

    db.commit()
    db.refresh(mapping)
    return mapping


def execute_boq_reconciliation(
    db: Session,
    project_id: str,
    payload: BoqReconciliationCreate,
    current_user_id: str,
) -> BoqReconciliation:
    """
    Performs deterministic exact Decimal quantity reconciliation for a VERIFIED mapping.
    Handles tolerance, unit compatibility, zero BOQ quantities, and supersession of prior runs.
    """
    # 1. Fetch mapping
    mapping = db.query(BoqCalculationMapping).filter(
        BoqCalculationMapping.id == payload.mapping_id,
        BoqCalculationMapping.project_id == project_id,
    ).first()
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BOQ mapping {payload.mapping_id} not found in project.",
        )

    if mapping.status != "VERIFIED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only VERIFIED mappings can generate an official reconciliation. Current status: '{mapping.status}'.",
        )

    boq_item = mapping.boq_item
    calc = mapping.calculation

    if not boq_item or not calc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Associated BOQ item or engineering calculation not found.",
        )

    # 2. Extract quantities and units
    boq_qty = Decimal(str(boq_item.stated_quantity))
    boq_unit = boq_item.unit.strip()
    calc_qty = Decimal(str(calc.result_value))
    calc_unit = calc.result_unit.strip() if calc.result_unit else ""

    tol = (
        Decimal(str(payload.tolerance_threshold))
        if payload.tolerance_threshold is not None
        else Decimal("0.000000")
    )
    if tol < Decimal("0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tolerance threshold must be non-negative.",
        )

    # 3. Reconcile units and calculate delta
    delta: Optional[Decimal] = None
    var_pct: Optional[Decimal] = None

    if not are_units_compatible(boq_unit, calc_unit):
        discrepancy_status = "UNIT_MISMATCH"
        delta = None
        var_pct = None
    else:
        delta = (calc_qty - boq_qty).quantize(Decimal("0.000001"))
        abs_delta = abs(delta)

        if abs_delta <= tol:
            discrepancy_status = "MATCH"
        elif delta > tol:
            discrepancy_status = "OVER_CALCULATED"
        else:
            discrepancy_status = "UNDER_CALCULATED"

        if boq_qty == Decimal("0"):
            var_pct = None
        else:
            var_pct = ((delta / boq_qty) * Decimal("100")).quantize(Decimal("0.000001"))

    # 4. Handle supersession if an active CALCULATED reconciliation already exists
    existing_rec = db.query(BoqReconciliation).filter(
        BoqReconciliation.mapping_id == mapping.id,
        BoqReconciliation.status == "CALCULATED",
    ).first()
    if existing_rec:
        existing_rec.status = "SUPERSEDED"
        db.flush()
        log_action(
            db=db,
            user_id=current_user_id,
            action="SUPERSEDE_BOQ_RECONCILIATION",
            entity_type="boq_reconciliation",
            entity_id=existing_rec.id,
            reason="Superseded by new reconciliation snapshot",
        )

    # 5. Build snapshot provenance
    provenance_json: Dict[str, Any] = {
        "algorithm_version": "1.0",
        "reconciliation_type": "DIRECT_QUANTITY_RECONCILIATION",
        "mapping_id": mapping.id,
        "boq_item_id": boq_item.id,
        "boq_stated_quantity": str(boq_qty),
        "boq_unit": boq_unit,
        "calculation_id": calc.id,
        "calculation_result_value": str(calc_qty),
        "calculation_result_unit": calc_unit,
        "tolerance_threshold": str(tol),
        "executed_by": current_user_id,
        "executed_at": datetime.now(timezone.utc).isoformat(),
    }

    reconciliation = BoqReconciliation(
        project_id=project_id,
        mapping_id=mapping.id,
        boq_item_id=boq_item.id,
        calculation_id=calc.id,
        boq_quantity=boq_qty,
        boq_unit=boq_unit,
        calculated_quantity=calc_qty,
        calculated_unit=calc_unit,
        quantity_delta=delta,
        variance_percentage=var_pct,
        tolerance_threshold=tol,
        discrepancy_status=discrepancy_status,
        status="CALCULATED",
        algorithm_version="1.0",
        provenance_json=provenance_json,
        created_by=current_user_id,
        metadata_json=payload.metadata_json,
    )
    db.add(reconciliation)
    db.flush()

    log_action(
        db=db,
        user_id=current_user_id,
        action="EXECUTE_BOQ_RECONCILIATION",
        entity_type="boq_reconciliation",
        entity_id=reconciliation.id,
        reason=f"Executed quantity reconciliation with discrepancy status: {discrepancy_status}",
    )
    db.commit()
    db.refresh(reconciliation)
    return reconciliation


def list_boq_reconciliations(
    db: Session,
    project_id: str,
    boq_item_id: Optional[str] = None,
    calculation_id: Optional[str] = None,
    discrepancy_status: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[BoqReconciliation]:
    """
    Lists reconciliations for a project with optional filtering and pagination.
    """
    query = db.query(BoqReconciliation).filter(BoqReconciliation.project_id == project_id)
    if boq_item_id:
        query = query.filter(BoqReconciliation.boq_item_id == boq_item_id)
    if calculation_id:
        query = query.filter(BoqReconciliation.calculation_id == calculation_id)
    if discrepancy_status:
        query = query.filter(BoqReconciliation.discrepancy_status == discrepancy_status)
    if status:
        query = query.filter(BoqReconciliation.status == status)
    return query.order_by(BoqReconciliation.created_at.desc()).offset(skip).limit(limit).all()
