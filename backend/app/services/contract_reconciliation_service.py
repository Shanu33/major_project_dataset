"""Phase 1M: BOQ Quantity-to-Execution Reconciliation & Contract Variation Foundation Service."""
import hashlib
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
import uuid

from fastapi import HTTPException, status
from sqlalchemy import text, func, and_, or_
from sqlalchemy.orm import Session

from app.db.models import (
    ContractExecutionItem,
    ActivityContractMapping,
    ContractVariationOrder,
    BoqReconciliationSnapshot,
    BoqItem,
    ConstructionActivity,
    PeriodProgressCertificate,
    PeriodCertificateItem,
    DailyProgressValuation,
    Project,
)
from app.schemas.contract_reconciliation import (
    ContractExecutionItemCreateOriginal,
    ContractExecutionItemSupersedeRequest,
    ActivityContractMappingCreate,
    ContractVariationOrderCreate,
)
from app.services.audit import log_action
from app.services.unit_normalization import UNIT_SYNONYMS


def _normalize_unit(u: str) -> str:
    cleaned = u.strip().lower()
    return UNIT_SYNONYMS.get(cleaned, cleaned)


def _check_unit_compatibility(u1: str, u2: str) -> Tuple[bool, Decimal]:
    norm1 = _normalize_unit(u1)
    norm2 = _normalize_unit(u2)
    if norm1 == norm2:
        return True, Decimal("1.0")

    # Linear length conversions
    if norm1 == "m" and norm2 == "mm":
        return True, Decimal("1000.0")
    if norm1 == "mm" and norm2 == "m":
        return True, Decimal("0.001")
    if norm1 == "m" and norm2 == "cm":
        return True, Decimal("100.0")
    if norm1 == "cm" and norm2 == "m":
        return True, Decimal("0.01")

    # Mass conversions
    if norm1 == "tonne" and norm2 == "kg":
        return True, Decimal("1000.0")
    if norm1 == "kg" and norm2 == "tonne":
        return True, Decimal("0.001")

    return False, Decimal("0.0")


# ==============================================================================
# 1. Contract Execution Item Services
# ==============================================================================

def create_original_contract_item(
    db: Session,
    project_id: str,
    data: ContractExecutionItemCreateOriginal,
    current_user_id: str,
) -> ContractExecutionItem:
    boq_item = db.query(BoqItem).filter(BoqItem.id == data.boq_item_id).first()
    if not boq_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BOQ item not found.")
    if boq_item.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="BOQ item belongs to another project.")
    if boq_item.status != "CONFIRMED":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot create ContractExecutionItem from BOQ item with status '{boq_item.status}'. Must be CONFIRMED.",
        )

    existing = db.query(ContractExecutionItem).filter(
        ContractExecutionItem.boq_item_id == boq_item.id,
        ContractExecutionItem.item_origin == "ORIGINAL_BOQ",
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A ContractExecutionItem already exists for this BOQ item.",
        )

    item_code = data.item_code or boq_item.item_code
    description = data.description or boq_item.description
    uom = data.unit_of_measure or boq_item.unit
    stated_qty = Decimal(str(boq_item.stated_quantity))
    rate = Decimal(str(data.original_contract_rate))

    item = ContractExecutionItem(
        project_id=project_id,
        boq_item_id=boq_item.id,
        originating_cvo_id=None,
        item_origin="ORIGINAL_BOQ",
        item_code=item_code,
        description=description,
        unit_of_measure=uom,
        original_contract_quantity=stated_qty,
        effective_contract_quantity=stated_qty,
        original_contract_rate=rate,
        current_contract_rate=rate,
        currency=data.currency,
        effective_date=data.effective_date,
        status="ACTIVE",
    )
    db.add(item)
    db.flush()

    log_action(db, current_user_id, "CREATE_CONTRACT_EXECUTION_ITEM", "contract_execution_items", item.id, "Created ORIGINAL_BOQ item")
    db.commit()
    db.refresh(item)
    return item


def supersede_contract_item(
    db: Session,
    project_id: str,
    item_id: str,
    data: ContractExecutionItemSupersedeRequest,
    current_user_id: str,
) -> ContractExecutionItem:
    old_item = (
        db.query(ContractExecutionItem)
        .filter(ContractExecutionItem.id == item_id, ContractExecutionItem.project_id == project_id)
        .with_for_update()
        .first()
    )
    if not old_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract execution item not found.")

    if old_item.item_origin == "EXTRA_ITEM":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="EXTRA_ITEM_CANNOT_BE_SUPERSEDED: Extra items cannot undergo generic supersession. Use contract variation orders for scope or rate evolution.",
        )

    if old_item.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot supersede item with status '{old_item.status}'. Only ACTIVE items can be superseded.",
        )

    now_utc = datetime.now(timezone.utc)
    super_date = now_utc.date()

    # Set explicit supersession authorization context
    db.execute(text("SET LOCAL app.auth_cei_supersession = 'TRUE'"))

    new_item = ContractExecutionItem(
        project_id=old_item.project_id,
        boq_item_id=old_item.boq_item_id,
        originating_cvo_id=None,
        item_origin=old_item.item_origin,
        item_code=data.item_code,
        description=data.description,
        unit_of_measure=old_item.unit_of_measure,
        original_contract_quantity=old_item.original_contract_quantity,
        effective_contract_quantity=old_item.effective_contract_quantity,
        original_contract_rate=old_item.original_contract_rate,
        current_contract_rate=old_item.current_contract_rate,
        currency=old_item.currency,
        effective_date=super_date,
        status="ACTIVE",
    )
    db.add(new_item)
    db.flush()

    old_item.status = "SUPERSEDED"
    old_item.superseded_at = now_utc
    old_item.superseding_item_id = new_item.id

    log_action(
        db,
        current_user_id,
        "SUPERSEDE_CONTRACT_EXECUTION_ITEM",
        "contract_execution_items",
        old_item.id,
        f"Superseded by {new_item.id}",
    )
    db.commit()
    db.refresh(new_item)
    return new_item


def list_contract_items(
    db: Session,
    project_id: str,
    status_filter: Optional[str] = None,
) -> List[ContractExecutionItem]:
    q = db.query(ContractExecutionItem).filter(ContractExecutionItem.project_id == project_id)
    if status_filter:
        q = q.filter(ContractExecutionItem.status == status_filter.upper())
    return q.order_by(ContractExecutionItem.created_at.asc()).all()


def get_contract_item(db: Session, project_id: str, item_id: str) -> ContractExecutionItem:
    item = (
        db.query(ContractExecutionItem)
        .filter(ContractExecutionItem.id == item_id, ContractExecutionItem.project_id == project_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract execution item not found.")
    return item


# ==============================================================================
# 2. Activity Contract Mapping Services
# ==============================================================================

def create_activity_contract_mapping(
    db: Session,
    project_id: str,
    data: ActivityContractMappingCreate,
    current_user_id: str,
) -> ActivityContractMapping:
    # 1. Lock activity row to avoid concurrency anomalies
    activity = (
        db.query(ConstructionActivity)
        .filter(ConstructionActivity.id == data.activity_id)
        .with_for_update()
        .first()
    )
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Construction activity not found.")
    if activity.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Construction activity belongs to another project.")

    cei = (
        db.query(ContractExecutionItem)
        .filter(ContractExecutionItem.id == data.contract_execution_item_id)
        .first()
    )
    if not cei:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract execution item not found.")
    if cei.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contract execution item belongs to another project.")

    if cei.status == "CLOSED":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot map to a CLOSED contract item.")

    if data.effective_from < cei.effective_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"CONTRACT_ITEM_NOT_EFFECTIVE_FOR_MAPPING: mapping effective_from ({data.effective_from}) cannot precede contract item effective_date ({cei.effective_date}).",
        )

    if cei.status == "SUPERSEDED":
        super_date = cei.superseded_at.astimezone(timezone.utc).date()
        if data.effective_from >= super_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"CONTRACT_ITEM_SUPERSEDED_FOR_MAPPING: mapping effective_from cannot be on or after supersession date ({super_date}).",
            )
        if data.effective_to and data.effective_to >= super_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"CONTRACT_ITEM_SUPERSEDED_FOR_MAPPING: mapping effective_to exceeds supersession date ({super_date}).",
            )

    mapping = ActivityContractMapping(
        project_id=project_id,
        activity_id=data.activity_id,
        contract_execution_item_id=data.contract_execution_item_id,
        allocation_percentage=data.allocation_percentage,
        effective_from=data.effective_from,
        effective_to=data.effective_to,
    )
    db.add(mapping)
    db.flush()

    log_action(
        db,
        current_user_id,
        "CREATE_ACTIVITY_CONTRACT_MAPPING",
        "activity_contract_mappings",
        mapping.id,
        f"Mapped activity {data.activity_id} to CEI {data.contract_execution_item_id}",
    )
    db.commit()
    db.refresh(mapping)
    return mapping


def list_activity_contract_mappings(
    db: Session,
    project_id: str,
    activity_id: Optional[str] = None,
    cei_id: Optional[str] = None,
) -> List[ActivityContractMapping]:
    q = db.query(ActivityContractMapping).filter(ActivityContractMapping.project_id == project_id)
    if activity_id:
        q = q.filter(ActivityContractMapping.activity_id == activity_id)
    if cei_id:
        q = q.filter(ActivityContractMapping.contract_execution_item_id == cei_id)
    return q.order_by(ActivityContractMapping.effective_from.asc()).all()


# ==============================================================================
# 3. Contract Variation Order Services
# ==============================================================================

def create_variation_order(
    db: Session,
    project_id: str,
    data: ContractVariationOrderCreate,
    current_user_id: str,
) -> ContractVariationOrder:
    v_type = data.variation_type.upper()
    if v_type not in ["QUANTITY_VARIATION", "RATE_REVISION", "EXTRA_ITEM_ADDITION", "SCOPE_OMISSION"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid variation_type '{data.variation_type}'.")

    if v_type == "EXTRA_ITEM_ADDITION":
        if data.contract_execution_item_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="EXTRA_ITEM_ADDITION cannot specify contract_execution_item_id in DRAFT.",
            )
        if data.rate_previous != data.rate_revised:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="EXTRA_ITEM_ADDITION must have rate_previous == rate_revised.",
            )
        if data.quantity_delta <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="EXTRA_ITEM_ADDITION quantity_delta must be positive.",
            )
        cei_id = None
    else:
        if not data.contract_execution_item_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{v_type} requires a contract_execution_item_id.",
            )
        cei = (
            db.query(ContractExecutionItem)
            .filter(
                ContractExecutionItem.id == data.contract_execution_item_id,
                ContractExecutionItem.project_id == project_id,
            )
            .first()
        )
        if not cei:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target contract execution item not found.")
        if cei.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot create variation for non-ACTIVE item (status={cei.status}).",
            )
        if data.unit_of_measure != cei.unit_of_measure:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CVO unit_of_measure ({data.unit_of_measure}) must match CEI unit_of_measure ({cei.unit_of_measure}).",
            )
        if data.rate_previous != cei.current_contract_rate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"RATE_REVISION_STALE_AT_CREATION: CVO rate_previous ({data.rate_previous}) must match live CEI rate ({cei.current_contract_rate}).",
            )
        if v_type in ["QUANTITY_VARIATION", "SCOPE_OMISSION"]:
            if data.rate_previous != data.rate_revised:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{v_type} cannot modify rate.")
            if v_type == "SCOPE_OMISSION" and data.quantity_delta >= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SCOPE_OMISSION quantity_delta must be negative.")
            if v_type == "QUANTITY_VARIATION" and data.quantity_delta == 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="QUANTITY_VARIATION quantity_delta cannot be zero.")
        elif v_type == "RATE_REVISION":
            if data.quantity_delta != 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="RATE_REVISION quantity_delta must be zero.")
            if data.rate_previous == data.rate_revised:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="RATE_REVISION rate_revised must differ from rate_previous.")
        cei_id = cei.id

    cvo = ContractVariationOrder(
        project_id=project_id,
        contract_execution_item_id=cei_id,
        variation_number=data.variation_number,
        variation_type=v_type,
        unit_of_measure=data.unit_of_measure,
        quantity_delta=data.quantity_delta,
        rate_previous=data.rate_previous,
        rate_revised=data.rate_revised,
        net_variation_amount=None,
        effective_date=data.effective_date,
        approved_at=None,
        approved_by_user_id=None,
        status="DRAFT",
        description=data.description,
    )
    db.add(cvo)
    db.flush()

    log_action(db, current_user_id, "CREATE_VARIATION_ORDER", "contract_variation_orders", cvo.id, f"Created {v_type} CVO")
    db.commit()
    db.refresh(cvo)
    return cvo


def submit_variation_order(
    db: Session,
    project_id: str,
    cvo_id: str,
    current_user_id: str,
) -> ContractVariationOrder:
    cvo = (
        db.query(ContractVariationOrder)
        .filter(ContractVariationOrder.id == cvo_id, ContractVariationOrder.project_id == project_id)
        .with_for_update()
        .first()
    )
    if not cvo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variation order not found.")
    if cvo.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot submit variation order with status '{cvo.status}'. Must be DRAFT.",
        )

    # Revalidate rate freshness at submission for RATE_REVISION
    if cvo.variation_type == "RATE_REVISION":
        cei = db.query(ContractExecutionItem).filter(ContractExecutionItem.id == cvo.contract_execution_item_id).first()
        if not cei or cvo.rate_previous != cei.current_contract_rate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"RATE_REVISION_STALE_AT_SUBMISSION: rate_previous ({cvo.rate_previous}) differs from live CEI rate ({cei.current_contract_rate if cei else 'none'}).",
            )

    cvo.status = "SUBMITTED"
    log_action(db, current_user_id, "SUBMIT_VARIATION_ORDER", "contract_variation_orders", cvo.id, "Submitted CVO")
    db.commit()
    db.refresh(cvo)
    return cvo


def reject_variation_order(
    db: Session,
    project_id: str,
    cvo_id: str,
    current_user_id: str,
) -> ContractVariationOrder:
    cvo = (
        db.query(ContractVariationOrder)
        .filter(ContractVariationOrder.id == cvo_id, ContractVariationOrder.project_id == project_id)
        .with_for_update()
        .first()
    )
    if not cvo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variation order not found.")
    if cvo.status not in ["DRAFT", "SUBMITTED"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot reject variation order with terminal status '{cvo.status}'.",
        )

    cvo.status = "REJECTED"
    log_action(db, current_user_id, "REJECT_VARIATION_ORDER", "contract_variation_orders", cvo.id, "Rejected CVO")
    db.commit()
    db.refresh(cvo)
    return cvo


def _compute_cum_exec_at_date(db: Session, cei_id: str, cutoff_date: date) -> Decimal:
    """Computes cumulative certified execution for a CEI across certified certificates with cut_off <= cutoff_date."""
    # Find all certificates up to cutoff_date
    certs = (
        db.query(PeriodProgressCertificate)
        .filter(
            PeriodProgressCertificate.certificate_status == "CERTIFIED",
            PeriodProgressCertificate.period_cut_off_date <= cutoff_date,
        )
        .all()
    )
    if not certs:
        return Decimal("0.0000")

    total_exec = Decimal("0.0000")
    for cert in certs:
        # Sum period certificate items mapped to this CEI
        items = (
            db.query(PeriodCertificateItem)
            .filter(PeriodCertificateItem.certificate_id == cert.id)
            .all()
        )
        for pci in items:
            # Check mappings for this activity at cert cutoff
            mappings = (
                db.query(ActivityContractMapping)
                .filter(
                    ActivityContractMapping.activity_id == pci.activity_id,
                    ActivityContractMapping.contract_execution_item_id == cei_id,
                    ActivityContractMapping.effective_from <= cert.period_cut_off_date,
                    or_(
                        ActivityContractMapping.effective_to.is_(None),
                        ActivityContractMapping.effective_to >= cert.period_cut_off_date,
                    ),
                )
                .all()
            )
            for m in mappings:
                alloc_ratio = Decimal(str(m.allocation_percentage)) / Decimal("100.00")
                total_exec += Decimal(str(pci.certified_quantity)) * alloc_ratio

    return total_exec


def approve_variation_order(
    db: Session,
    project_id: str,
    cvo_id: str,
    current_user_id: str,
) -> ContractVariationOrder:
    cvo = (
        db.query(ContractVariationOrder)
        .filter(ContractVariationOrder.id == cvo_id, ContractVariationOrder.project_id == project_id)
        .with_for_update()
        .first()
    )
    if not cvo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variation order not found.")
    if cvo.status != "SUBMITTED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot approve variation order with status '{cvo.status}'. Must be SUBMITTED.",
        )

    now_utc = datetime.now(timezone.utc)
    now_date_utc = now_utc.date()
    d_applicable = max(cvo.effective_date, now_date_utc)

    if cvo.variation_type == "EXTRA_ITEM_ADDITION":
        # Authorization Contexts
        db.execute(text("SET LOCAL app.auth_extra_item_creation = 'TRUE'"))
        db.execute(text("SET LOCAL app.auth_cvo_approval = 'TRUE'"))

        new_cei_id = str(uuid.uuid4())
        new_cei = ContractExecutionItem(
            id=new_cei_id,
            project_id=project_id,
            boq_item_id=None,
            originating_cvo_id=cvo.id,
            item_origin="EXTRA_ITEM",
            item_code=f"EI-{cvo.variation_number}",
            description=cvo.description,
            unit_of_measure=cvo.unit_of_measure,
            original_contract_quantity=cvo.quantity_delta,
            effective_contract_quantity=cvo.quantity_delta,
            original_contract_rate=cvo.rate_revised,
            current_contract_rate=cvo.rate_revised,
            currency="INR",
            effective_date=cvo.effective_date,
            status="ACTIVE",
        )
        db.add(new_cei)
        db.flush()

        cvo.contract_execution_item_id = new_cei.id
        cvo.status = "APPROVED"
        cvo.approved_at = now_utc
        cvo.approved_by_user_id = current_user_id
        cvo.net_variation_amount = Decimal(str(cvo.quantity_delta)) * Decimal(str(cvo.rate_revised))

        log_action(db, current_user_id, "APPROVE_EXTRA_ITEM_VARIATION", "contract_variation_orders", cvo.id, f"Approved Extra Item CEI {new_cei_id}")
        db.commit()
        db.refresh(cvo)
        return cvo

    else:
        # Standard variation
        cei = (
            db.query(ContractExecutionItem)
            .filter(ContractExecutionItem.id == cvo.contract_execution_item_id)
            .with_for_update()
            .first()
        )
        if not cei:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target CEI not found.")

        # Revalidate rate freshness under FOR UPDATE lock
        if cvo.variation_type == "RATE_REVISION":
            if cvo.rate_previous != cei.current_contract_rate:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"RATE_REVISION_STALE_AT_APPROVAL: rate_previous ({cvo.rate_previous}) differs from live CEI rate ({cei.current_contract_rate}).",
                )

        # Set authorization contexts
        db.execute(text("SET LOCAL app.auth_cvo_approval = 'TRUE'"))
        db.execute(text("SET LOCAL app.auth_cei_state_mutation = 'TRUE'"))

        if cvo.variation_type == "RATE_REVISION":
            q_exec = _compute_cum_exec_at_date(db, cei.id, d_applicable)
            q_forward = max(Decimal("0.0000"), Decimal(str(cei.effective_contract_quantity)) - q_exec)
            cvo.net_variation_amount = q_forward * (Decimal(str(cvo.rate_revised)) - Decimal(str(cvo.rate_previous)))

        elif cvo.variation_type == "QUANTITY_VARIATION":
            cvo.net_variation_amount = Decimal(str(cvo.quantity_delta)) * Decimal(str(cei.current_contract_rate))

        elif cvo.variation_type == "SCOPE_OMISSION":
            q_exec = _compute_cum_exec_at_date(db, cei.id, d_applicable)
            new_eff_qty = Decimal(str(cei.effective_contract_quantity)) + Decimal(str(cvo.quantity_delta))
            if new_eff_qty < q_exec:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Scope omission cannot reduce quantity ({new_eff_qty}) below already executed volume ({q_exec}).",
                )
            cvo.net_variation_amount = Decimal(str(cvo.quantity_delta)) * Decimal(str(cei.current_contract_rate))

        cvo.status = "APPROVED"
        cvo.approved_at = now_utc
        cvo.approved_by_user_id = current_user_id

        # Flush CVO transition to APPROVED first so trigger validates rate_previous against live CEI rate
        db.flush()

        if cvo.variation_type == "RATE_REVISION":
            cei.current_contract_rate = cvo.rate_revised
        elif cvo.variation_type in ("QUANTITY_VARIATION", "SCOPE_OMISSION"):
            cei.effective_contract_quantity += cvo.quantity_delta

        db.flush()
        log_action(db, current_user_id, "APPROVE_VARIATION_ORDER", "contract_variation_orders", cvo.id, f"Approved {cvo.variation_type} CVO")
        db.commit()
        db.refresh(cvo)
        return cvo


def list_variation_orders(
    db: Session,
    project_id: str,
    status_filter: Optional[str] = None,
    cei_id: Optional[str] = None,
) -> List[ContractVariationOrder]:
    q = db.query(ContractVariationOrder).filter(ContractVariationOrder.project_id == project_id)
    if status_filter:
        q = q.filter(ContractVariationOrder.status == status_filter.upper())
    if cei_id:
        q = q.filter(ContractVariationOrder.contract_execution_item_id == cei_id)
    return q.order_by(ContractVariationOrder.created_at.asc()).all()


def get_variation_order(db: Session, project_id: str, cvo_id: str) -> ContractVariationOrder:
    cvo = (
        db.query(ContractVariationOrder)
        .filter(ContractVariationOrder.id == cvo_id, ContractVariationOrder.project_id == project_id)
        .first()
    )
    if not cvo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variation order not found.")
    return cvo


# ==============================================================================
# 4. BOQ Reconciliation Execution Services
# ==============================================================================

def _get_applicable_rate_at_cutoff(db: Session, cei: ContractExecutionItem, cutoff_date: date) -> Decimal:
    """Returns the legally applicable rate for a CEI at cutoff_date."""
    # Find approved rate revisions with D_applicable <= cutoff_date
    revs = (
        db.query(ContractVariationOrder)
        .filter(
            ContractVariationOrder.contract_execution_item_id == cei.id,
            ContractVariationOrder.variation_type == "RATE_REVISION",
            ContractVariationOrder.status == "APPROVED",
        )
        .all()
    )
    applicable_revs = []
    for r in revs:
        app_date_utc = r.approved_at.astimezone(timezone.utc).date()
        d_app = max(r.effective_date, app_date_utc)
        if d_app <= cutoff_date:
            applicable_revs.append((d_app, r.approved_at, r.rate_revised))

    if applicable_revs:
        # Sort by d_app desc, approved_at desc
        applicable_revs.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return Decimal(str(applicable_revs[0][2]))

    return Decimal(str(cei.original_contract_rate))


def _compute_reconciliation_hash(
    certificate_id: str,
    cei_id: str,
    eff_qty: Decimal,
    cum_qty: Decimal,
    rec_rate: Decimal,
    hist_val: Decimal,
    curr_val: Decimal,
) -> str:
    raw = f"{certificate_id}|{cei_id}|{eff_qty:.4f}|{cum_qty:.4f}|{rec_rate:.4f}|{hist_val:.4f}|{curr_val:.4f}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def execute_boq_reconciliation(
    db: Session,
    project_id: str,
    certificate_id: str,
    current_user_id: str,
) -> List[BoqReconciliationSnapshot]:
    cert = (
        db.query(PeriodProgressCertificate)
        .filter(
            PeriodProgressCertificate.id == certificate_id,
            PeriodProgressCertificate.project_id == project_id,
        )
        .first()
    )
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Period progress certificate not found.")

    if cert.certificate_status != "CERTIFIED":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot execute reconciliation on certificate with status '{cert.certificate_status}'. Must be CERTIFIED.",
        )

    cutoff_date = cert.period_cut_off_date

    # Check if reconciliation already exists
    existing = (
        db.query(BoqReconciliationSnapshot)
        .filter(BoqReconciliationSnapshot.certificate_id == certificate_id)
        .all()
    )
    if existing:
        return existing

    # Get all certificate items for this certificate
    pci_items = (
        db.query(PeriodCertificateItem)
        .filter(PeriodCertificateItem.certificate_id == certificate_id)
        .all()
    )
    if not pci_items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Certificate has no progress items to reconcile.",
        )

    act_ids = list({item.activity_id for item in pci_items})

    # Lock all participating activities FOR SHARE
    db.query(ConstructionActivity).filter(ConstructionActivity.id.in_(act_ids)).with_for_update(read=True).all()

    # Revalidate 100.00% allocation completeness for every participating activity at cutoff_date
    for act_id in act_ids:
        mappings = (
            db.query(ActivityContractMapping)
            .filter(
                ActivityContractMapping.activity_id == act_id,
                ActivityContractMapping.effective_from <= cutoff_date,
                or_(
                    ActivityContractMapping.effective_to.is_(None),
                    ActivityContractMapping.effective_to >= cutoff_date,
                ),
            )
            .all()
        )
        total_alloc = sum(Decimal(str(m.allocation_percentage)) for m in mappings)
        if total_alloc < Decimal("100.00"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"ACTIVITY_CONTRACT_ALLOCATION_INCOMPLETE: Activity {act_id} has total allocation {total_alloc}% (< 100.00%).",
            )
        if total_alloc > Decimal("100.00"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"ACTIVITY_CONTRACT_ALLOCATION_OVERALLOCATED: Activity {act_id} has total allocation {total_alloc}% (> 100.00%).",
            )

    # Find all prior and current certified certificates up to cutoff_date
    all_certs = (
        db.query(PeriodProgressCertificate)
        .filter(
            PeriodProgressCertificate.project_id == project_id,
            PeriodProgressCertificate.certificate_status == "CERTIFIED",
            PeriodProgressCertificate.period_cut_off_date <= cutoff_date,
        )
        .order_by(PeriodProgressCertificate.period_cut_off_date.asc())
        .all()
    )

    # Collect all CEIs in project
    all_ceis = (
        db.query(ContractExecutionItem)
        .filter(ContractExecutionItem.project_id == project_id)
        .all()
    )

    snapshots = []
    now_utc = datetime.now(timezone.utc)

    for cei in all_ceis:
        # Determine contractual quantity at cutoff
        if cei.item_origin == "EXTRA_ITEM":
            orig_cvo = db.query(ContractVariationOrder).filter(ContractVariationOrder.id == cei.originating_cvo_id).first()
            if orig_cvo and orig_cvo.status == "APPROVED":
                orig_app_date_utc = orig_cvo.approved_at.astimezone(timezone.utc).date()
                d_app_orig = max(orig_cvo.effective_date, orig_app_date_utc)
                if cutoff_date < d_app_orig:
                    contractual_qty = Decimal("0.0000")
                else:
                    contractual_qty = Decimal(str(cei.original_contract_quantity))
            else:
                contractual_qty = Decimal("0.0000")
        else:
            if cutoff_date < cei.effective_date:
                contractual_qty = Decimal("0.0000")
            else:
                contractual_qty = Decimal(str(cei.original_contract_quantity))

        # Add scope / quantity variations approved on/before cutoff_date
        if contractual_qty > 0 or cei.item_origin == "ORIGINAL_BOQ":
            vars_on_cei = (
                db.query(ContractVariationOrder)
                .filter(
                    ContractVariationOrder.contract_execution_item_id == cei.id,
                    ContractVariationOrder.status == "APPROVED",
                    ContractVariationOrder.variation_type.in_(["QUANTITY_VARIATION", "SCOPE_OMISSION"]),
                )
                .all()
            )
            for v in vars_on_cei:
                v_app_date_utc = v.approved_at.astimezone(timezone.utc).date()
                d_app_v = max(v.effective_date, v_app_date_utc)
                if d_app_v <= cutoff_date:
                    contractual_qty += Decimal(str(v.quantity_delta))

        # Determine reconciliation_rate at cutoff_date
        rec_rate = _get_applicable_rate_at_cutoff(db, cei, cutoff_date)

        # Calculate cumulative executed quantity and historical period valuation
        cum_exec_qty = Decimal("0.0000")
        hist_val = Decimal("0.0000")

        for c_period in all_certs:
            p_cutoff = c_period.period_cut_off_date
            p_rate = _get_applicable_rate_at_cutoff(db, cei, p_cutoff)

            # Execution in this certificate period
            period_items = (
                db.query(PeriodCertificateItem)
                .filter(PeriodCertificateItem.certificate_id == c_period.id)
                .all()
            )
            period_qty_for_cei = Decimal("0.0000")

            for pi in period_items:
                maps = (
                    db.query(ActivityContractMapping)
                    .filter(
                        ActivityContractMapping.activity_id == pi.activity_id,
                        ActivityContractMapping.contract_execution_item_id == cei.id,
                        ActivityContractMapping.effective_from <= p_cutoff,
                        or_(
                            ActivityContractMapping.effective_to.is_(None),
                            ActivityContractMapping.effective_to >= p_cutoff,
                        ),
                    )
                    .all()
                )
                for m in maps:
                    # Unit compatibility check
                    compat, factor = _check_unit_compatibility(pi.quantity_unit, cei.unit_of_measure)
                    if not compat:
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"UNIT_INCOMPATIBILITY: Activity unit '{pi.quantity_unit}' is incompatible with CEI unit '{cei.unit_of_measure}'.",
                        )
                    ratio = Decimal(str(m.allocation_percentage)) / Decimal("100.00")
                    qty_allocated = Decimal(str(pi.certified_quantity)) * ratio * factor
                    period_qty_for_cei += qty_allocated

            cum_exec_qty += period_qty_for_cei
            hist_val += period_qty_for_cei * p_rate

        # Current live head rate valuation
        curr_rate = Decimal(str(cei.current_contract_rate))
        curr_val = cum_exec_qty * curr_rate
        val_delta = curr_val - hist_val

        gross_over = max(Decimal("0.0000"), cum_exec_qty - contractual_qty)
        crit_dev = gross_over
        is_crit = (cum_exec_qty > contractual_qty and contractual_qty > 0) or (cum_exec_qty > 0 and contractual_qty == 0)

        # Only create snapshot if item is mapped, active, or has execution
        has_mappings = (
            db.query(ActivityContractMapping)
            .filter(ActivityContractMapping.contract_execution_item_id == cei.id)
            .count()
            > 0
        )
        if contractual_qty > 0 or cum_exec_qty > 0 or has_mappings:
            s_hash = _compute_reconciliation_hash(
                certificate_id,
                cei.id,
                contractual_qty,
                cum_exec_qty,
                rec_rate,
                hist_val,
                curr_val,
            )
            snapshot = BoqReconciliationSnapshot(
                project_id=project_id,
                certificate_id=certificate_id,
                contract_execution_item_id=cei.id,
                effective_contract_quantity=contractual_qty,
                cumulative_executed_quantity=cum_exec_qty,
                cumulative_executed_quantity_boq_unit=cum_exec_qty,
                gross_over_execution_quantity=gross_over,
                critical_deviation_quantity=crit_dev,
                reconciliation_rate=rec_rate,
                historical_period_valuation=hist_val,
                current_rate_valuation=curr_val,
                valuation_delta=val_delta,
                is_critical_deviation=is_crit,
                snapshot_hash=s_hash,
                verified_at=now_utc,
            )
            db.add(snapshot)
            snapshots.append(snapshot)

    db.flush()
    log_action(
        db,
        current_user_id,
        "EXECUTE_BOQ_RECONCILIATION",
        "period_progress_certificates",
        certificate_id,
        f"Reconciled {len(snapshots)} contract items",
    )
    db.commit()
    return snapshots


def get_certificate_reconciliations(
    db: Session,
    project_id: str,
    certificate_id: str,
) -> List[BoqReconciliationSnapshot]:
    return (
        db.query(BoqReconciliationSnapshot)
        .filter(
            BoqReconciliationSnapshot.project_id == project_id,
            BoqReconciliationSnapshot.certificate_id == certificate_id,
        )
        .order_by(BoqReconciliationSnapshot.created_at.asc())
        .all()
    )
