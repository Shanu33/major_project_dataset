"""Phase 1L: Site Progress Valuation & Certified Progress Foundation Service.

Provides deterministic service functions for:
- Activity-Rate Mapping with atomic supersession
- Daily Progress Report valuation from supervisor verifications
- Running-Account Period Progress Certificates (PERIOD_SNAPSHOT)
- Immutability and canonical SHA-256 snapshot hashing
- PostgreSQL advisory locking for concurrent certificate generation
- Transactional audit logging
"""
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_

from app.db.models import (
    Project,
    ConstructionActivity,
    CostRate,
    MonitoringBaseline,
    DailyProgressReport,
    DailyActivityProgress,
    DailyActivityProgressVerification,
    ActivityRateMapping,
    DailyProgressValuation,
    PeriodProgressCertificate,
    PeriodCertificateItem,
    User,
)
from app.schemas.progress_valuation import (
    ActivityRateMappingCreate,
    PeriodCertificateCreate,
    PeriodCertificateSupersedeRequest,
)
from app.services.audit import log_action
from app.services.unit_normalization import are_units_compatible, normalize_unit


def acquire_project_cert_lock(db: Session, project_id: str) -> None:
    """Acquires a transaction-level PostgreSQL advisory lock on project_id for serialized certificate operations."""
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtext('project_cert_' || :pid))"),
        {"pid": str(project_id)}
    )


def compute_valuation_snapshot_hash(
    cert: PeriodProgressCertificate,
    items: List[PeriodCertificateItem]
) -> str:
    """
    Computes a canonical SHA-256 cryptographic hash covering the entire certificate snapshot.
    Fixed field order, fixed decimal representations (.4f / .6f), fixed ISO-8601 date strings.
    """
    header_parts = [
        str(cert.id),
        str(cert.certificate_type),
        str(cert.monitoring_baseline_id),
        str(cert.baseline_schedule_id),
        str(cert.baseline_schedule_version),
        str(cert.baseline_schedule_algorithm_version),
        cert.baseline_start_date.isoformat(),
        cert.period_start_date.isoformat(),
        cert.period_cut_off_date.isoformat(),
        str(cert.currency),
        str(cert.algorithm_version),
    ]
    header_str = "|".join(header_parts)

    sorted_items = sorted(items, key=lambda x: str(x.valuation_id))
    item_strs = []
    for item in sorted_items:
        parts = [
            str(item.valuation_id),
            str(item.activity_id),
            f"{Decimal(str(item.claimed_quantity)):.6f}",
            f"{Decimal(str(item.certified_quantity)):.6f}",
            str(item.quantity_unit),
            f"{Decimal(str(item.unit_conversion_factor)):.6f}",
            f"{Decimal(str(item.applied_rate)):.6f}",
            str(item.applied_rate_unit),
            f"{Decimal(str(item.claimed_amount)):.4f}",
            f"{Decimal(str(item.certified_amount)):.4f}",
            f"{Decimal(str(item.discrepancy_quantity)):.6f}",
            f"{Decimal(str(item.disputed_exposure)):.4f}",
        ]
        item_strs.append("|".join(parts))

    full_payload = header_str + "||" + ";".join(item_strs)
    return hashlib.sha256(full_payload.encode("utf-8")).hexdigest()


# ==============================================================================
# 1. Activity Rate Mapping Service
# ==============================================================================

def create_activity_rate_mapping(
    db: Session,
    project_id: str,
    payload: ActivityRateMappingCreate,
    current_user_id: str,
) -> ActivityRateMapping:
    """
    Links a ConstructionActivity to a confirmed CostRate.
    Atomically supersedes any existing ACTIVE mapping for this activity.
    """
    # 1. Verify Project
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found.")

    # 2. Verify Activity
    activity = db.query(ConstructionActivity).filter(
        ConstructionActivity.id == payload.activity_id,
        ConstructionActivity.project_id == project_id
    ).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity {payload.activity_id} not found in project {project_id}."
        )

    # 3. Verify CostRate
    cost_rate = db.query(CostRate).filter(CostRate.id == payload.cost_rate_id).first()
    if not cost_rate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"CostRate {payload.cost_rate_id} not found.")

    if cost_rate.status != "CONFIRMED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CostRate must be in CONFIRMED status. Current: {cost_rate.status}."
        )

    if cost_rate.project_id is not None and cost_rate.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project-specific cost rate belongs to project {cost_rate.project_id}, not {project_id}."
        )

    now = datetime.now(timezone.utc)

    # 4. Atomic supersession of existing ACTIVE mapping
    existing_active = db.query(ActivityRateMapping).filter(
        ActivityRateMapping.activity_id == payload.activity_id,
        ActivityRateMapping.status == "ACTIVE"
    ).first()

    if existing_active:
        existing_active.status = "SUPERSEDED"
        existing_active.effective_to = now
        log_action(
            db,
            user_id=current_user_id,
            action="ACTIVITY_RATE_SUPERSEDED",
            entity_type="ActivityRateMapping",
            entity_id=existing_active.id,
            reason=f"Superseded by new mapping to rate {cost_rate.id}"
        )

    # 5. Create new ACTIVE mapping
    new_mapping = ActivityRateMapping(
        project_id=project_id,
        activity_id=payload.activity_id,
        cost_rate_id=cost_rate.id,
        rate_value=cost_rate.rate_value,
        rate_unit=cost_rate.unit,
        rate_version=cost_rate.version,
        currency=cost_rate.currency,
        status="ACTIVE",
        effective_from=now,
        created_by=current_user_id,
    )
    db.add(new_mapping)
    db.flush()

    log_action(
        db,
        user_id=current_user_id,
        action="ACTIVITY_RATE_MAPPED",
        entity_type="ActivityRateMapping",
        entity_id=new_mapping.id,
        reason=f"Mapped activity {activity.id} to confirmed rate {cost_rate.id}"
    )

    db.commit()
    db.refresh(new_mapping)
    return new_mapping


def list_activity_rate_mappings(
    db: Session,
    project_id: str,
    status_filter: Optional[str] = None
) -> List[ActivityRateMapping]:
    """Lists activity rate mappings for a project."""
    query = db.query(ActivityRateMapping).filter(ActivityRateMapping.project_id == project_id)
    if status_filter:
        query = query.filter(ActivityRateMapping.status == status_filter.upper())
    return query.order_by(ActivityRateMapping.created_at.desc()).all()


# ==============================================================================
# 2. Daily Progress Valuation Service
# ==============================================================================

def evaluate_daily_progress_report(
    db: Session,
    project_id: str,
    report_id: str,
    current_user_id: str,
) -> Tuple[List[DailyProgressValuation], Decimal, Decimal, Decimal, str]:
    """
    Evaluates supervisor-verified progress items for a FINALIZED DailyProgressReport.
    Creates deterministic DailyProgressValuation records.
    """
    # 1. Verify Report
    report = db.query(DailyProgressReport).filter(
        DailyProgressReport.id == report_id,
        DailyProgressReport.project_id == project_id
    ).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DailyProgressReport {report_id} not found in project {project_id}."
        )

    if report.submission_status != "FINALIZED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"DailyProgressReport must be FINALIZED before valuation. Current status: {report.submission_status}."
        )

    # 2. Find activity progress records
    progress_items = db.query(DailyActivityProgress).filter(
        DailyActivityProgress.daily_report_id == report.id
    ).all()

    valuations_created: List[DailyProgressValuation] = []
    total_claimed = Decimal("0.0000")
    total_certified = Decimal("0.0000")
    total_disputed = Decimal("0.0000")
    report_currency = "INR"

    for prog in progress_items:
        # Get latest verification
        latest_ver = db.query(DailyActivityProgressVerification).filter(
            DailyActivityProgressVerification.daily_activity_progress_id == prog.id
        ).order_by(DailyActivityProgressVerification.verified_at.desc()).first()

        if not latest_ver:
            continue

        if latest_ver.verification_status == "PENDING":
            continue

        # Check if already valued
        existing_val = db.query(DailyProgressValuation).filter(
            DailyProgressValuation.verification_id == latest_ver.id
        ).first()
        if existing_val:
            continue

        # Find ACTIVE rate mapping
        mapping = db.query(ActivityRateMapping).filter(
            ActivityRateMapping.activity_id == prog.activity_id,
            ActivityRateMapping.status == "ACTIVE"
        ).first()
        if not mapping:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No ACTIVE rate mapping found for activity {prog.activity_id}."
            )

        report_currency = mapping.currency

        # Unit compatibility check
        qty_unit = latest_ver.verified_quantity_unit or prog.contractor_progress_unit
        if not qty_unit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing quantity unit for progress {prog.id}."
            )

        if not are_units_compatible(qty_unit, mapping.rate_unit):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"INCOMPATIBLE_UNITS_FOR_VALUATION: Progress unit '{qty_unit}' is incompatible with rate unit '{mapping.rate_unit}'."
            )

        # Quantities
        q_claimed = Decimal(str(prog.contractor_progress_value or 0))
        if latest_ver.verification_status in ("VERIFIED", "CORRECTED"):
            q_certified = Decimal(str(latest_ver.verified_quantity or 0))
        else: # REJECTED
            q_certified = Decimal("0.000000")

        conversion_factor = Decimal("1.000000")
        rate_val = Decimal(str(mapping.rate_value))

        # Financial formulas
        q_cert_norm = q_certified * conversion_factor
        cev = (q_cert_norm * rate_val).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        q_claim_norm = q_claimed * conversion_factor
        claimed_val = (q_claim_norm * rate_val).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        discrepancy_q = q_claimed - q_certified
        overclaim_q = max(Decimal("0"), q_claim_norm - q_cert_norm)
        disputed_exp = (overclaim_q * rate_val).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        valuation = DailyProgressValuation(
            project_id=project_id,
            verification_id=latest_ver.id,
            activity_rate_mapping_id=mapping.id,
            contractor_claimed_quantity=q_claimed,
            supervisor_certified_quantity=q_certified,
            quantity_unit=qty_unit,
            unit_conversion_factor=conversion_factor,
            applied_rate_value=rate_val,
            applied_rate_unit=mapping.rate_unit,
            currency=mapping.currency,
            contractor_claimed_value=claimed_val,
            certified_progress_value=cev,
            discrepancy_quantity=discrepancy_q,
            disputed_valuation_exposure=disputed_exp,
            valuation_status="ACTIVE",
        )
        db.add(valuation)
        db.flush()

        log_action(
            db,
            user_id=current_user_id,
            action="PROGRESS_REPORT_VALUED",
            entity_type="DailyProgressValuation",
            entity_id=valuation.id,
            reason=f"Valued verification {latest_ver.id} of activity {prog.activity_id}"
        )

        valuations_created.append(valuation)
        total_claimed += claimed_val
        total_certified += cev
        total_disputed += disputed_exp

    db.commit()
    for v in valuations_created:
        db.refresh(v)

    return valuations_created, total_claimed, total_certified, total_disputed, report_currency


def list_daily_progress_valuations(
    db: Session,
    project_id: str,
    status_filter: Optional[str] = None
) -> List[DailyProgressValuation]:
    """Lists progress valuations for a project."""
    query = db.query(DailyProgressValuation).filter(DailyProgressValuation.project_id == project_id)
    if status_filter:
        query = query.filter(DailyProgressValuation.valuation_status == status_filter.upper())
    return query.order_by(DailyProgressValuation.created_at.desc()).all()


# ==============================================================================
# 3. Period Progress Certificate Service (PERIOD_SNAPSHOT)
# ==============================================================================

def create_draft_period_certificate(
    db: Session,
    project_id: str,
    payload: PeriodCertificateCreate,
    current_user_id: str,
) -> PeriodProgressCertificate:
    """
    Creates a new Running-Account progress certificate draft (PERIOD_SNAPSHOT).
    Captures uncertified daily valuations in the date window [period_start_date, period_cut_off_date].
    """
    acquire_project_cert_lock(db, project_id)

    # 1. Date window validation
    if payload.period_start_date > payload.period_cut_off_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="period_start_date cannot be greater than period_cut_off_date."
        )

    # 2. Unique certificate number validation
    existing_num = db.query(PeriodProgressCertificate).filter(
        PeriodProgressCertificate.project_id == project_id,
        PeriodProgressCertificate.certificate_number == payload.certificate_number
    ).first()
    if existing_num:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate number '{payload.certificate_number}' already exists in project {project_id}."
        )

    # 3. Active Monitoring Baseline lookup
    baseline = db.query(MonitoringBaseline).filter(
        MonitoringBaseline.project_id == project_id,
        MonitoringBaseline.status == "ACTIVE"
    ).first()
    if not baseline:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No ACTIVE MonitoringBaseline found for project."
        )

    # 4. Mandatory baseline_start_date check
    if baseline.baseline_start_date is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="BASELINE_START_DATE_REQUIRED: baseline_start_date cannot be null."
        )

    # 5. Query eligible valuations in date window
    query = (
        db.query(DailyProgressValuation)
        .join(DailyActivityProgressVerification, DailyActivityProgressVerification.id == DailyProgressValuation.verification_id)
        .join(DailyActivityProgress, DailyActivityProgress.id == DailyActivityProgressVerification.daily_activity_progress_id)
        .join(DailyProgressReport, DailyProgressReport.id == DailyActivityProgress.daily_report_id)
        .filter(
            DailyProgressValuation.project_id == project_id,
            DailyProgressValuation.valuation_status == "ACTIVE",
            DailyProgressValuation.certified_certificate_id.is_(None),
            DailyProgressReport.submission_status == "FINALIZED",
            DailyProgressReport.report_date >= payload.period_start_date,
            DailyProgressReport.report_date <= payload.period_cut_off_date,
        )
    )
    eligible_valuations = query.all()

    # Determine currency
    cert_currency = "INR"
    if eligible_valuations:
        cert_currency = eligible_valuations[0].currency

    # Period totals
    period_claimed = Decimal("0.0000")
    period_certified = Decimal("0.0000")
    period_disputed = Decimal("0.0000")

    for val in eligible_valuations:
        if val.currency != cert_currency:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Currency mismatch among valuations: '{val.currency}' vs '{cert_currency}'."
            )
        period_claimed += Decimal(str(val.contractor_claimed_value))
        period_certified += Decimal(str(val.certified_progress_value))
        period_disputed += Decimal(str(val.disputed_valuation_exposure))

    # Preceding certified certificate for cumulative totals
    prev_cert = db.query(PeriodProgressCertificate).filter(
        PeriodProgressCertificate.project_id == project_id,
        PeriodProgressCertificate.certificate_status == "CERTIFIED",
        PeriodProgressCertificate.period_cut_off_date < payload.period_start_date
    ).order_by(PeriodProgressCertificate.period_cut_off_date.desc(), PeriodProgressCertificate.created_at.desc()).first()

    if prev_cert:
        cum_claimed = Decimal(str(prev_cert.cumulative_claimed_value)) + period_claimed
        cum_certified = Decimal(str(prev_cert.cumulative_certified_value)) + period_certified
        cum_disputed = Decimal(str(prev_cert.cumulative_disputed_exposure)) + period_disputed
    else:
        cum_claimed = period_claimed
        cum_certified = period_certified
        cum_disputed = period_disputed

    cert = PeriodProgressCertificate(
        project_id=project_id,
        certificate_number=payload.certificate_number,
        certificate_type="PERIOD_SNAPSHOT",
        monitoring_baseline_id=baseline.id,
        baseline_schedule_id=str(baseline.schedule_id),
        baseline_schedule_version=str(baseline.schedule_version),
        baseline_schedule_algorithm_version=str(baseline.schedule_algorithm_version),
        baseline_start_date=baseline.baseline_start_date,
        period_start_date=payload.period_start_date,
        period_cut_off_date=payload.period_cut_off_date,
        certificate_status="DRAFT",
        currency=cert_currency,
        period_claimed_value=period_claimed,
        period_certified_value=period_certified,
        period_disputed_exposure=period_disputed,
        cumulative_claimed_value=cum_claimed,
        cumulative_certified_value=cum_certified,
        cumulative_disputed_exposure=cum_disputed,
        item_count=len(eligible_valuations),
        valuation_snapshot_hash="DRAFT_PENDING_CERTIFICATION",
        algorithm_version="1.0",
    )
    db.add(cert)
    db.flush()

    items: List[PeriodCertificateItem] = []
    for val in eligible_valuations:
        item = PeriodCertificateItem(
            certificate_id=cert.id,
            valuation_id=val.id,
            activity_id=val.activity_rate_mapping.activity_id,
            claimed_quantity=val.contractor_claimed_quantity,
            certified_quantity=val.supervisor_certified_quantity,
            quantity_unit=val.quantity_unit,
            unit_conversion_factor=val.unit_conversion_factor,
            applied_rate=val.applied_rate_value,
            applied_rate_unit=val.applied_rate_unit,
            currency=val.currency,
            claimed_amount=val.contractor_claimed_value,
            certified_amount=val.certified_progress_value,
            discrepancy_quantity=val.discrepancy_quantity,
            disputed_exposure=val.disputed_valuation_exposure,
        )
        db.add(item)
        items.append(item)
    db.flush()

    # Calculate draft snapshot hash
    cert.valuation_snapshot_hash = compute_valuation_snapshot_hash(cert, items)

    log_action(
        db,
        user_id=current_user_id,
        action="PERIOD_CERTIFICATE_DRAFTED",
        entity_type="PeriodProgressCertificate",
        entity_id=cert.id,
        reason=f"Drafted certificate {cert.certificate_number} with {len(items)} items"
    )

    db.commit()
    db.refresh(cert)
    return cert


def certify_period_certificate(
    db: Session,
    project_id: str,
    cert_id: str,
    current_user_id: str,
) -> PeriodProgressCertificate:
    """
    Certifies a DRAFT period certificate.
    Permanently locks snapshot fields, verifies cumulative totals, and binds constituent valuations.
    """
    acquire_project_cert_lock(db, project_id)

    cert = db.query(PeriodProgressCertificate).filter(
        PeriodProgressCertificate.id == cert_id,
        PeriodProgressCertificate.project_id == project_id
    ).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate {cert_id} not found in project {project_id}."
        )

    if cert.certificate_status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only DRAFT certificates can be certified. Current status: {cert.certificate_status}."
        )

    # Verify no date overlap with existing CERTIFIED certificates
    overlap = db.query(PeriodProgressCertificate).filter(
        PeriodProgressCertificate.project_id == project_id,
        PeriodProgressCertificate.certificate_status == "CERTIFIED",
        PeriodProgressCertificate.id != cert.id,
        PeriodProgressCertificate.period_start_date <= cert.period_cut_off_date,
        PeriodProgressCertificate.period_cut_off_date >= cert.period_start_date,
    ).first()
    if overlap:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certified period window [{cert.period_start_date}, {cert.period_cut_off_date}] overlaps with existing certified certificate {overlap.certificate_number}."
        )

    items = db.query(PeriodCertificateItem).filter(
        PeriodCertificateItem.certificate_id == cert.id
    ).all()

    # Re-verify period totals match sum of items
    sum_cert = sum(Decimal(str(i.certified_amount)) for i in items) if items else Decimal("0.0000")
    sum_claim = sum(Decimal(str(i.claimed_amount)) for i in items) if items else Decimal("0.0000")
    sum_disp = sum(Decimal(str(i.disputed_exposure)) for i in items) if items else Decimal("0.0000")

    cert.period_certified_value = sum_cert
    cert.period_claimed_value = sum_claim
    cert.period_disputed_exposure = sum_disp
    cert.item_count = len(items)

    # Re-verify cumulative totals
    prev_cert = db.query(PeriodProgressCertificate).filter(
        PeriodProgressCertificate.project_id == project_id,
        PeriodProgressCertificate.certificate_status == "CERTIFIED",
        PeriodProgressCertificate.period_cut_off_date < cert.period_start_date
    ).order_by(PeriodProgressCertificate.period_cut_off_date.desc(), PeriodProgressCertificate.created_at.desc()).first()

    if prev_cert:
        cert.cumulative_claimed_value = Decimal(str(prev_cert.cumulative_claimed_value)) + sum_claim
        cert.cumulative_certified_value = Decimal(str(prev_cert.cumulative_certified_value)) + sum_cert
        cert.cumulative_disputed_exposure = Decimal(str(prev_cert.cumulative_disputed_exposure)) + sum_disp
    else:
        cert.cumulative_claimed_value = sum_claim
        cert.cumulative_certified_value = sum_cert
        cert.cumulative_disputed_exposure = sum_disp

    now = datetime.now(timezone.utc)
    cert.certified_by = current_user_id
    cert.certified_at = now
    cert.certificate_status = "CERTIFIED"
    cert.valuation_snapshot_hash = compute_valuation_snapshot_hash(cert, items)

    # Bind valuations
    for item in items:
        val = db.query(DailyProgressValuation).filter(DailyProgressValuation.id == item.valuation_id).first()
        if not val:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Valuation {item.valuation_id} not found.")
        if val.certified_certificate_id is not None and val.certified_certificate_id != cert.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Valuation {val.id} is already bound to certified certificate {val.certified_certificate_id}."
            )
        val.certified_certificate_id = cert.id

    log_action(
        db,
        user_id=current_user_id,
        action="PERIOD_CERTIFICATE_CERTIFIED",
        entity_type="PeriodProgressCertificate",
        entity_id=cert.id,
        reason=f"Certified certificate {cert.certificate_number} with hash {cert.valuation_snapshot_hash}"
    )

    db.commit()
    db.refresh(cert)
    return cert


def delete_draft_period_certificate(
    db: Session,
    project_id: str,
    cert_id: str,
    current_user_id: str,
) -> None:
    """Deletes a DRAFT certificate and its line items. Certified certificates cannot be deleted."""
    acquire_project_cert_lock(db, project_id)

    cert = db.query(PeriodProgressCertificate).filter(
        PeriodProgressCertificate.id == cert_id,
        PeriodProgressCertificate.project_id == project_id
    ).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate {cert_id} not found in project {project_id}."
        )

    if cert.certificate_status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete certificate with status {cert.certificate_status}."
        )

    log_action(
        db,
        user_id=current_user_id,
        action="PERIOD_CERTIFICATE_DELETED",
        entity_type="PeriodProgressCertificate",
        entity_id=cert.id,
        reason=f"Deleted draft certificate {cert.certificate_number}"
    )

    db.delete(cert)
    db.commit()


def supersede_period_certificate(
    db: Session,
    project_id: str,
    cert_id: str,
    payload: PeriodCertificateSupersedeRequest,
    current_user_id: str,
) -> PeriodProgressCertificate:
    """
    Administrative supersession of a CERTIFIED certificate.
    Financial fields and line items remain permanently immutable.
    Valuations remain permanently bound.
    """
    acquire_project_cert_lock(db, project_id)

    cert = db.query(PeriodProgressCertificate).filter(
        PeriodProgressCertificate.id == cert_id,
        PeriodProgressCertificate.project_id == project_id
    ).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate {cert_id} not found in project {project_id}."
        )

    if cert.certificate_status != "CERTIFIED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only CERTIFIED certificates can be superseded. Current status: {cert.certificate_status}."
        )

    now = datetime.now(timezone.utc)
    cert.certificate_status = "SUPERSEDED"
    cert.superseded_by = current_user_id
    cert.superseded_at = now
    cert.supersession_reason = payload.reason

    log_action(
        db,
        user_id=current_user_id,
        action="PERIOD_CERTIFICATE_SUPERSEDED",
        entity_type="PeriodProgressCertificate",
        entity_id=cert.id,
        reason=f"Superseded certificate {cert.certificate_number}: {payload.reason}"
    )

    db.commit()
    db.refresh(cert)
    return cert


def get_period_certificate(
    db: Session,
    project_id: str,
    cert_id: str
) -> PeriodProgressCertificate:
    """Retrieves a single period certificate by ID."""
    cert = db.query(PeriodProgressCertificate).filter(
        PeriodProgressCertificate.id == cert_id,
        PeriodProgressCertificate.project_id == project_id
    ).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate {cert_id} not found in project {project_id}."
        )
    return cert


def list_period_certificates(
    db: Session,
    project_id: str,
    status_filter: Optional[str] = None
) -> List[PeriodProgressCertificate]:
    """Lists period certificates for a project."""
    query = db.query(PeriodProgressCertificate).filter(PeriodProgressCertificate.project_id == project_id)
    if status_filter:
        query = query.filter(PeriodProgressCertificate.certificate_status == status_filter.upper())
    return query.order_by(PeriodProgressCertificate.period_cut_off_date.asc(), PeriodProgressCertificate.created_at.asc()).all()


# ==============================================================================
# 4. Project Financial Progress Summary Service
# ==============================================================================

def get_financial_progress_summary(
    db: Session,
    project_id: str
) -> Dict[str, Any]:
    """
    Computes real-time project financial progress summary over active valuations.
    Planned Value is strictly marked PLANNED_VALUATION_NOT_AVAILABLE.
    """
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found.")

    valuations = db.query(DailyProgressValuation).filter(
        DailyProgressValuation.project_id == project_id,
        DailyProgressValuation.valuation_status == "ACTIVE"
    ).all()

    currency = "INR"
    cev_total = Decimal("0.0000")
    claim_total = Decimal("0.0000")
    disp_total = Decimal("0.0000")

    for v in valuations:
        currency = v.currency
        cev_total += Decimal(str(v.certified_progress_value))
        claim_total += Decimal(str(v.contractor_claimed_value))
        disp_total += Decimal(str(v.disputed_valuation_exposure))

    return {
        "project_id": project_id,
        "currency": currency,
        "cumulative_earned_value": cev_total,
        "cumulative_claimed_value": claim_total,
        "cumulative_disputed_exposure": disp_total,
        "planned_valuation_status": "PLANNED_VALUATION_NOT_AVAILABLE",
        "cumulative_planned_value": None,
        "schedule_variance_cost": None,
    }
