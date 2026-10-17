import hashlib
import json
import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, text

from app.db.models import (
    Project,
    User,
    Document,
    Evidence,
    ConstructionActivity,
    MonitoringBaseline,
    PeriodProgressCertificate,
    PeriodCertificateItem,
    MaterialItem,
    MaterialMixDesign,
    MaterialMixConstituent,
    MaterialPlan,
    MaterialConsumptionEntry,
    TheoreticalConsumptionItem,
    MaterialReconciliationReport,
)
from app.schemas.material_reconciliation import (
    MaterialItemCreate,
    MixDesignCreate,
    ContractorConsumptionSubmit,
    SupervisorConsumptionVerify,
    CANONICAL_MATERIAL_CATEGORIES,
    CANONICAL_STANDARD_UNITS,
)
from app.services.audit import log_action


def _compute_reconciliation_hash(
    project_id: str,
    certificate_id: str,
    material_item_id: str,
    cutoff_date: date,
    cum_theo: Decimal,
    cum_actual: Decimal,
    perm_waste: Decimal,
    variance: Decimal,
    unauth_waste: Decimal,
) -> str:
    payload = {
        "algorithm_version": "1.0-DETERMINISTIC",
        "certificate_id": str(certificate_id),
        "cumulative_actual_quantity": f"{cum_actual:.4f}",
        "cumulative_theoretical_quantity": f"{cum_theo:.4f}",
        "cutoff_date": str(cutoff_date),
        "material_item_id": str(material_item_id),
        "permissible_waste_quantity": f"{perm_waste:.4f}",
        "project_id": str(project_id),
        "unauthorized_wastage_quantity": f"{unauth_waste:.4f}",
        "variance_quantity": f"{variance:.4f}",
    }
    canonical_json = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------------------
# 1. Material Catalog
# ------------------------------------------------------------------------------

def create_material_item(
    db: Session,
    project_id: Optional[str],
    data: MaterialItemCreate,
    current_user_id: str,
) -> MaterialItem:
    if data.material_category not in CANONICAL_MATERIAL_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid material category '{data.material_category}'. Allowed: {sorted(list(CANONICAL_MATERIAL_CATEGORIES))}",
        )
    if data.standard_unit not in CANONICAL_STANDARD_UNITS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid standard unit '{data.standard_unit}'. Allowed: {sorted(list(CANONICAL_STANDARD_UNITS))}",
        )

    if project_id is not None:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

        # Check duplicate code in project
        existing = db.query(MaterialItem).filter(
            MaterialItem.project_id == project_id,
            MaterialItem.material_code == data.material_code,
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate material code in project.")
    else:
        existing = db.query(MaterialItem).filter(
            MaterialItem.project_id.is_(None),
            MaterialItem.material_code == data.material_code,
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate global material code.")

    item = MaterialItem(
        project_id=project_id,
        material_code=data.material_code,
        material_name=data.material_name,
        material_category=data.material_category,
        standard_unit=data.standard_unit,
        density_kg_per_unit=data.density_kg_per_unit,
        standard_permissible_waste_pct=data.standard_permissible_waste_pct,
        is_active=True,
    )
    db.add(item)
    db.flush()

    log_action(db, current_user_id, "MATERIAL_CREATED", "material_items", item.id, f"Created material {item.material_code}")
    db.commit()
    db.refresh(item)
    return item


def list_material_items(db: Session, project_id: str) -> List[MaterialItem]:
    return (
        db.query(MaterialItem)
        .filter(or_(MaterialItem.project_id == project_id, MaterialItem.project_id.is_(None)))
        .all()
    )


# ------------------------------------------------------------------------------
# 2. Mix Designs
# ------------------------------------------------------------------------------

def create_mix_design(
    db: Session,
    project_id: str,
    data: MixDesignCreate,
    current_user_id: str,
) -> MaterialMixDesign:
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    existing = db.query(MaterialMixDesign).filter(
        MaterialMixDesign.project_id == project_id,
        MaterialMixDesign.mix_code == data.mix_code,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate mix code in project.")

    # Validation rules
    if data.mix_type == "DESIGN_MIX":
        if not data.source_document_id or not data.evidence_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="DESIGN_MIX requires both source_document_id and evidence_id.",
            )
        doc = db.query(Document).filter(Document.id == data.source_document_id).first()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Source document {data.source_document_id} not found.",
            )
        if doc.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Source document belongs to project {doc.project_id}, not mix project {project_id}.",
            )
        ev = db.query(Evidence).filter(Evidence.id == data.evidence_id).first()
        if not ev:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Evidence {data.evidence_id} not found.",
            )
        if ev.document_id != doc.id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Evidence {ev.id} belongs to document {ev.document_id}, not referenced document {doc.id}.",
            )
        classification = "CALCULATED"
    elif data.mix_type == "NOMINAL_MIX":
        if not data.rule_code:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="NOMINAL_MIX requires rule_code.",
            )
        classification = "ASSUMPTION_BASED"
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid mix_type '{data.mix_type}'.")

    mix = MaterialMixDesign(
        project_id=project_id,
        mix_code=data.mix_code,
        grade_designation=data.grade_designation,
        mix_type=data.mix_type,
        rule_code=data.rule_code,
        source_document_id=data.source_document_id,
        evidence_id=data.evidence_id,
        dry_volume_factor=data.dry_volume_factor,
        water_cement_ratio=data.water_cement_ratio,
        classification=classification,
        status="DRAFT",
    )
    db.add(mix)
    db.flush()

    for c in data.constituents:
        mat = db.query(MaterialItem).filter(MaterialItem.id == c.material_item_id).first()
        if not mat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Material item {c.material_item_id} not found.")
        if mat.project_id is not None and mat.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Material item {c.material_item_id} belongs to project {mat.project_id}, not mix project {project_id}.",
            )
        const = MaterialMixConstituent(
            mix_design_id=mix.id,
            material_item_id=c.material_item_id,
            quantity_per_m3=c.quantity_per_m3,
            unit=c.unit,
        )
        db.add(const)

    log_action(db, current_user_id, "MIX_DESIGN_CREATED", "material_mix_designs", mix.id, f"Created mix {mix.mix_code}")
    db.commit()
    db.refresh(mix)
    return mix


def approve_mix_design(
    db: Session,
    project_id: str,
    mix_id: str,
    current_user: User,
) -> MaterialMixDesign:
    if current_user.role.lower() not in ["admin", "supervisor", "site_supervisor"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Admin or Supervisor can approve mix designs.")

    mix = (
        db.query(MaterialMixDesign)
        .filter(MaterialMixDesign.id == mix_id, MaterialMixDesign.project_id == project_id)
        .with_for_update()
        .first()
    )
    if not mix:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mix design not found.")

    if mix.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot approve mix design with status '{mix.status}'. Must be DRAFT.",
        )

    if mix.mix_type == "DESIGN_MIX":
        if not mix.source_document_id or not mix.evidence_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot approve DESIGN_MIX without verified source document and evidence.",
            )
        doc = db.query(Document).filter(Document.id == mix.source_document_id).first()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Source document {mix.source_document_id} not found.",
            )
        if doc.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Source document belongs to project {doc.project_id}, not mix project {project_id}.",
            )
        ev = db.query(Evidence).filter(Evidence.id == mix.evidence_id).first()
        if not ev:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Evidence {mix.evidence_id} not found.",
            )
        if ev.document_id != doc.id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Evidence {ev.id} belongs to document {ev.document_id}, not referenced document {doc.id}.",
            )
        if ev.verification_status != "VERIFIED":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Evidence {ev.id} has verification_status '{ev.verification_status}'. Must be VERIFIED.",
            )
    elif mix.mix_type == "NOMINAL_MIX":
        if not mix.rule_code or mix.classification != "ASSUMPTION_BASED":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="NOMINAL_MIX must be ASSUMPTION_BASED and specify rule_code.",
            )

    now_utc = datetime.now(timezone.utc)
    mix.status = "APPROVED"
    mix.approved_by = current_user.id
    mix.approved_at = now_utc

    log_action(db, current_user.id, "MIX_DESIGN_APPROVED", "material_mix_designs", mix.id, f"Approved mix {mix.mix_code}")
    db.commit()
    db.refresh(mix)
    return mix


def list_mix_designs(db: Session, project_id: str) -> List[MaterialMixDesign]:
    return db.query(MaterialMixDesign).filter(MaterialMixDesign.project_id == project_id).all()


# ------------------------------------------------------------------------------
# 3. Material Plans (BOM)
# ------------------------------------------------------------------------------

def generate_material_plans(
    db: Session,
    project_id: str,
    baseline_id: str,
    current_user: User,
) -> List[MaterialPlan]:
    if current_user.role.lower() not in ["admin", "supervisor", "site_supervisor"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Admin or Supervisor can generate material plans.")

    baseline = (
        db.query(MonitoringBaseline)
        .filter(MonitoringBaseline.id == baseline_id, MonitoringBaseline.project_id == project_id)
        .first()
    )
    if not baseline or baseline.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid ACTIVE MonitoringBaseline required to generate material plans.",
        )

    activities = (
        db.query(ConstructionActivity)
        .filter(ConstructionActivity.project_id == project_id)
        .all()
    )
    if not activities:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No construction activities found for project.")

    # Find approved mix designs
    mixes = (
        db.query(MaterialMixDesign)
        .filter(MaterialMixDesign.project_id == project_id, MaterialMixDesign.status == "APPROVED")
        .all()
    )
    if not mixes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No approved mix designs found for project.")

    default_mix = mixes[0]
    plans = []

    for act in activities:
        if act.metadata_json and "planned_quantity" in act.metadata_json:
            act_qty = Decimal(str(act.metadata_json["planned_quantity"]))
        else:
            act_qty = Decimal(str(act.duration_value or "100.0000"))
        if act_qty <= 0:
            continue

        for const in default_mix.constituents:
            planned_mat_qty = act_qty * Decimal(str(const.quantity_per_m3))
            waste_pct = const.material_item.standard_permissible_waste_pct or Decimal("0.00")
            gross_mat_qty = planned_mat_qty * (Decimal("1.00") + waste_pct / Decimal("100.00"))

            plan = MaterialPlan(
                project_id=project_id,
                baseline_id=baseline.id,
                material_item_id=const.material_item_id,
                activity_id=act.id,
                mix_design_id=default_mix.id,
                planned_quantity=planned_mat_qty,
                unit=const.unit,
                estimation_method=default_mix.classification,
                waste_allowance_pct=waste_pct,
                gross_planned_quantity=gross_mat_qty,
                provenance_metadata={
                    "activity_code": act.activity_code,
                    "mix_code": default_mix.mix_code,
                    "rate_per_unit": str(const.quantity_per_m3),
                },
                status="ACTIVE",
            )
            db.add(plan)
            plans.append(plan)

    log_action(db, current_user.id, "MATERIAL_PLAN_GENERATED", "material_plans", baseline.id, f"Generated {len(plans)} material plans")
    db.commit()
    for p in plans:
        db.refresh(p)
    return plans


def list_material_plans(db: Session, project_id: str, baseline_id: str) -> List[MaterialPlan]:
    return (
        db.query(MaterialPlan)
        .filter(MaterialPlan.project_id == project_id, MaterialPlan.baseline_id == baseline_id)
        .all()
    )


# ------------------------------------------------------------------------------
# 4. Actual Material Consumption Entries
# ------------------------------------------------------------------------------

def submit_material_consumption(
    db: Session,
    project_id: str,
    certificate_id: str,
    data: ContractorConsumptionSubmit,
    current_user: User,
) -> MaterialConsumptionEntry:
    if current_user.role.lower() not in ["contractor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Contractor or Admin can submit material consumption.",
        )

    cert = (
        db.query(PeriodProgressCertificate)
        .filter(PeriodProgressCertificate.id == certificate_id, PeriodProgressCertificate.project_id == project_id)
        .first()
    )
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target certificate not found.")

    mat = db.query(MaterialItem).filter(MaterialItem.id == data.material_item_id).first()
    if not mat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material item not found.")
    if mat.project_id is not None and mat.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Material item {data.material_item_id} belongs to project {mat.project_id}, not {project_id}.",
        )

    if data.supporting_document_id:
        sdoc = db.query(Document).filter(Document.id == data.supporting_document_id).first()
        if not sdoc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supporting document not found.")
        if sdoc.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Supporting document belongs to project {sdoc.project_id}, not {project_id}.",
            )

    # Check unique store challan
    existing = db.query(MaterialConsumptionEntry).filter(
        MaterialConsumptionEntry.project_id == project_id,
        MaterialConsumptionEntry.store_challan_reference == data.store_challan_reference,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Store challan reference already exists.")

    entry = MaterialConsumptionEntry(
        project_id=project_id,
        certificate_id=certificate_id,
        material_item_id=data.material_item_id,
        store_challan_reference=data.store_challan_reference,
        consumption_date_start=data.consumption_date_start,
        consumption_date_end=data.consumption_date_end,
        contractor_declared_quantity=data.contractor_declared_quantity,
        supervisor_verified_quantity=None,
        discrepancy_quantity=Decimal("0.0000"),
        is_disputed=False,
        unit=data.unit,
        submission_status="SUBMITTED",
        supporting_document_id=data.supporting_document_id,
        submitted_by=current_user.id,
    )
    db.add(entry)
    db.flush()

    log_action(db, current_user.id, "MATERIAL_CONSUMPTION_SUBMITTED", "material_consumption_entries", entry.id, f"Submitted challan {entry.store_challan_reference}")
    db.commit()
    db.refresh(entry)
    return entry


def verify_material_consumption(
    db: Session,
    project_id: str,
    entry_id: str,
    data: SupervisorConsumptionVerify,
    current_user: User,
) -> MaterialConsumptionEntry:
    if current_user.role.lower() not in ["admin", "supervisor", "site_supervisor"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Admin or Supervisor can verify consumption.")

    entry = (
        db.query(MaterialConsumptionEntry)
        .filter(MaterialConsumptionEntry.id == entry_id, MaterialConsumptionEntry.project_id == project_id)
        .with_for_update()
        .first()
    )
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consumption entry not found.")

    if entry.submission_status == "VERIFIED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Entry is already VERIFIED.")

    now_utc = datetime.now(timezone.utc)

    if data.is_rejected:
        entry.submission_status = "REJECTED"
        entry.verified_by = current_user.id
        entry.verified_at = now_utc
        log_action(db, current_user.id, "MATERIAL_CONSUMPTION_REJECTED", "material_consumption_entries", entry.id, "Rejected entry")
    else:
        entry.submission_status = "VERIFIED"
        entry.supervisor_verified_quantity = data.supervisor_verified_quantity
        entry.verified_by = current_user.id
        entry.verified_at = now_utc

        diff = abs(entry.contractor_declared_quantity - data.supervisor_verified_quantity)
        entry.discrepancy_quantity = diff
        entry.is_disputed = (diff > Decimal("0.0000"))

        log_action(db, current_user.id, "MATERIAL_CONSUMPTION_VERIFIED", "material_consumption_entries", entry.id, f"Verified quantity: {data.supervisor_verified_quantity}")

    db.commit()
    db.refresh(entry)
    return entry


def list_material_consumption(db: Session, project_id: str, certificate_id: str) -> List[MaterialConsumptionEntry]:
    return (
        db.query(MaterialConsumptionEntry)
        .filter(MaterialConsumptionEntry.project_id == project_id, MaterialConsumptionEntry.certificate_id == certificate_id)
        .all()
    )


# ------------------------------------------------------------------------------
# 5. Theoretical Material Consumption Generation
# ------------------------------------------------------------------------------

def generate_theoretical_consumption(
    db: Session,
    project_id: str,
    certificate_id: str,
    current_user: User,
) -> List[TheoreticalConsumptionItem]:
    if current_user.role.lower() not in ["admin", "supervisor", "site_supervisor"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Admin or Supervisor can generate theoretical consumption.")

    cert = (
        db.query(PeriodProgressCertificate)
        .filter(PeriodProgressCertificate.id == certificate_id, PeriodProgressCertificate.project_id == project_id)
        .first()
    )
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found.")

    cert_items = (
        db.query(PeriodCertificateItem)
        .filter(PeriodCertificateItem.certificate_id == certificate_id)
        .all()
    )
    if not cert_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No certificate items found.")

    # Get active approved mix designs
    mixes = (
        db.query(MaterialMixDesign)
        .filter(MaterialMixDesign.project_id == project_id, MaterialMixDesign.status == "APPROVED")
        .all()
    )
    if not mixes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No approved mix design available.")

    default_mix = mixes[0]
    theo_items = []

    for ci in cert_items:
        vol = Decimal(str(ci.certified_quantity))
        for const in default_mix.constituents:
            coeff = Decimal(str(const.quantity_per_m3))
            theo_qty = vol * coeff

            item = TheoreticalConsumptionItem(
                project_id=project_id,
                certificate_id=certificate_id,
                certificate_item_id=ci.id,
                activity_id=ci.activity_id,
                material_item_id=const.material_item_id,
                mix_design_id=default_mix.id,
                certified_activity_volume=vol,
                coefficient_per_unit=coeff,
                dry_volume_factor=default_mix.dry_volume_factor,
                theoretical_quantity=theo_qty,
                unit=const.unit,
                mix_design_version=default_mix.mix_code,
                calculation_algorithm_version="1.0-DETERMINISTIC",
            )
            db.add(item)
            theo_items.append(item)

    log_action(db, current_user.id, "THEORETICAL_CONSUMPTION_GENERATED", "theoretical_consumption_items", certificate_id, f"Generated {len(theo_items)} theoretical items")
    db.commit()
    for t in theo_items:
        db.refresh(t)
    return theo_items


# ------------------------------------------------------------------------------
# 6. Material Reconciliation Finalization
# ------------------------------------------------------------------------------

def finalize_material_reconciliation(
    db: Session,
    project_id: str,
    certificate_id: str,
    current_user: User,
) -> List[MaterialReconciliationReport]:
    if current_user.role.lower() not in ["admin", "supervisor", "site_supervisor"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Admin or Supervisor can finalize reconciliation.")

    cert = (
        db.query(PeriodProgressCertificate)
        .filter(PeriodProgressCertificate.id == certificate_id, PeriodProgressCertificate.project_id == project_id)
        .with_for_update()
        .first()
    )
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found.")

    cutoff_date = cert.period_cut_off_date

    # Find all prior and current certificates up to cutoff
    all_certs = (
        db.query(PeriodProgressCertificate)
        .filter(
            PeriodProgressCertificate.project_id == project_id,
            PeriodProgressCertificate.period_cut_off_date <= cutoff_date,
        )
        .all()
    )
    all_cert_ids = [c.id for c in all_certs]

    # Cumulative theoretical consumption per material
    theo_records = (
        db.query(
            TheoreticalConsumptionItem.material_item_id,
            func.sum(TheoreticalConsumptionItem.theoretical_quantity).label("total_theo"),
        )
        .filter(TheoreticalConsumptionItem.certificate_id.in_(all_cert_ids))
        .group_by(TheoreticalConsumptionItem.material_item_id)
        .all()
    )
    theo_map = {r[0]: Decimal(str(r[1])) for r in theo_records}

    # Cumulative actual verified consumption per material
    actual_records = (
        db.query(
            MaterialConsumptionEntry.material_item_id,
            func.sum(MaterialConsumptionEntry.supervisor_verified_quantity).label("total_actual"),
        )
        .filter(
            MaterialConsumptionEntry.project_id == project_id,
            MaterialConsumptionEntry.submission_status == "VERIFIED",
            MaterialConsumptionEntry.consumption_date_end <= cutoff_date,
        )
        .group_by(MaterialConsumptionEntry.material_item_id)
        .all()
    )
    actual_map = {r[0]: Decimal(str(r[1])) for r in actual_records}

    all_mat_ids = set(theo_map.keys()) | set(actual_map.keys())
    if not all_mat_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No theoretical or verified actual material records found.")

    reports = []
    now_utc = datetime.now(timezone.utc)

    for mat_id in sorted(list(all_mat_ids)):
        mat = db.query(MaterialItem).filter(MaterialItem.id == mat_id).first()
        if not mat:
            continue

        cum_theo = theo_map.get(mat_id, Decimal("0.0000"))
        cum_actual = actual_map.get(mat_id, Decimal("0.0000"))
        variance = cum_actual - cum_theo

        if cum_theo > 0:
            var_pct = (variance / cum_theo) * Decimal("100.00")
        else:
            var_pct = Decimal("0.0000")

        perm_waste_pct = mat.standard_permissible_waste_pct or Decimal("0.00")
        perm_waste_qty = cum_theo * (perm_waste_pct / Decimal("100.00"))

        if variance < 0:
            is_saving = True
            unauth_waste = Decimal("0.0000")
        else:
            is_saving = False
            unauth_waste = max(Decimal("0.0000"), variance - perm_waste_qty)

        is_excess = (unauth_waste > Decimal("0.0000"))

        r_hash = _compute_reconciliation_hash(
            project_id=project_id,
            certificate_id=certificate_id,
            material_item_id=mat_id,
            cutoff_date=cutoff_date,
            cum_theo=cum_theo,
            cum_actual=cum_actual,
            perm_waste=perm_waste_qty,
            variance=variance,
            unauth_waste=unauth_waste,
        )

        # Check existing draft report
        existing = db.query(MaterialReconciliationReport).filter(
            MaterialReconciliationReport.certificate_id == certificate_id,
            MaterialReconciliationReport.material_item_id == mat_id,
            MaterialReconciliationReport.status == "DRAFT",
        ).first()

        if existing:
            existing.cumulative_theoretical_quantity = cum_theo
            existing.cumulative_actual_quantity = cum_actual
            existing.variance_quantity = variance
            existing.variance_percentage = var_pct
            existing.is_saving = is_saving
            existing.permissible_waste_percentage = perm_waste_pct
            existing.permissible_waste_quantity = perm_waste_qty
            existing.unauthorized_wastage_quantity = unauth_waste
            existing.is_excess_flagged = is_excess
            existing.reconciliation_hash = r_hash
            existing.status = "FINALIZED"
            existing.finalized_by = current_user.id
            existing.finalized_at = now_utc
            reports.append(existing)
        else:
            report = MaterialReconciliationReport(
                project_id=project_id,
                certificate_id=certificate_id,
                material_item_id=mat_id,
                revision_number=1,
                status="FINALIZED",
                cumulative_theoretical_quantity=cum_theo,
                cumulative_actual_quantity=cum_actual,
                variance_quantity=variance,
                variance_percentage=var_pct,
                is_saving=is_saving,
                permissible_waste_percentage=perm_waste_pct,
                permissible_waste_quantity=perm_waste_qty,
                unauthorized_wastage_quantity=unauth_waste,
                is_excess_flagged=is_excess,
                reconciliation_hash=r_hash,
                finalized_by=current_user.id,
                finalized_at=now_utc,
            )
            db.add(report)
            reports.append(report)

    log_action(db, current_user.id, "MATERIAL_RECONCILIATION_FINALIZED", "material_reconciliation_reports", certificate_id, f"Finalized reconciliation for {len(reports)} materials")
    db.commit()
    for rep in reports:
        db.refresh(rep)
    return reports


def list_material_reconciliation(db: Session, project_id: str, certificate_id: str) -> List[MaterialReconciliationReport]:
    return (
        db.query(MaterialReconciliationReport)
        .filter(MaterialReconciliationReport.project_id == project_id, MaterialReconciliationReport.certificate_id == certificate_id)
        .all()
    )
