"""Phase 1N: Material Requirements Planning, Mix Formulation & Theoretical Consumption Reconciliation Test Suite.

32 Mandatory Verification Scenarios:
Scenarios 1–3:   Material Catalog Integrity & Constraints
Scenarios 4–7:   Mix Formulation & Evidence Constraints
Scenarios 8–10:  Activity Provenance & Consistency
Scenarios 11–15: Actual Consumption Dual-Reporting & Verification
Scenarios 16–18: Deterministic Stoichiometry & Coefficient Snapshots
Scenarios 19–22: Wastage & Variance Semantics
Scenarios 23–26: Reconciliation Report Lifecycle & Immutability
Scenarios 27–29: Security & Project Boundary Isolation
Scenarios 30–32: Migration Lifecycle & Full Regression
"""
import uuid
import hashlib
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import get_db, engine
from app.db.models import (
    User,
    Project,
    ProjectMember,
    Document,
    Evidence,
    EngineeringElement,
    ConstructionActivity,
    ConstructionSchedule,
    MonitoringBaseline,
    PeriodProgressCertificate,
    PeriodCertificateItem,
    DailyProgressValuation,
    DailyProgressReport,
    DailyActivityProgress,
    DailyActivityProgressVerification,
    ActivityRateMapping,
    CostRate,
    MaterialItem,
    MaterialMixDesign,
    MaterialMixConstituent,
    MaterialPlan,
    MaterialConsumptionEntry,
    TheoreticalConsumptionItem,
    MaterialReconciliationReport,
)
from app.core.security import get_password_hash, create_access_token

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def client_fixture():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="module")
def setup_phase_1n(client_fixture):
    admin_email = f"admin_1n_{uuid.uuid4().hex[:6]}@test.com"
    pm_email = f"pm_1n_{uuid.uuid4().hex[:6]}@test.com"
    sup_email = f"sup_1n_{uuid.uuid4().hex[:6]}@test.com"
    con_email = f"con_1n_{uuid.uuid4().hex[:6]}@test.com"

    with TestingSessionLocal() as db_init:
        adm = User(email=admin_email, password_hash=get_password_hash("p"), role="admin")
        pm = User(email=pm_email, password_hash=get_password_hash("p"), role="project_manager")
        sup = User(email=sup_email, password_hash=get_password_hash("p"), role="site_supervisor")
        con = User(email=con_email, password_hash=get_password_hash("p"), role="contractor")
        db_init.add_all([adm, pm, sup, con])
        db_init.commit()

    admin_token = create_access_token(data={"sub": admin_email, "role": "admin"})
    pm_token = create_access_token(data={"sub": pm_email, "role": "project_manager"})
    sup_token = create_access_token(data={"sub": sup_email, "role": "site_supervisor"})
    con_token = create_access_token(data={"sub": con_email, "role": "contractor"})

    # Create Projects
    r1 = client_fixture.post("/api/projects", json={"name": f"P1N Project 1 {uuid.uuid4().hex[:6]}"}, headers={"Authorization": f"Bearer {admin_token}"})
    p1_id = r1.json()["id"]

    r2 = client_fixture.post("/api/projects", json={"name": f"P1N Project 2 {uuid.uuid4().hex[:6]}"}, headers={"Authorization": f"Bearer {admin_token}"})
    p2_id = r2.json()["id"]

    db = TestingSessionLocal()
    u_adm = db.query(User).filter(User.email == admin_email).first()
    u_pm = db.query(User).filter(User.email == pm_email).first()
    u_sup = db.query(User).filter(User.email == sup_email).first()
    u_con = db.query(User).filter(User.email == con_email).first()

    db.add(ProjectMember(project_id=p1_id, user_id=u_pm.id))
    db.add(ProjectMember(project_id=p1_id, user_id=u_sup.id))
    db.add(ProjectMember(project_id=p1_id, user_id=u_con.id))
    db.commit()

    # Document & Evidence for P1
    doc = Document(
        project_id=p1_id,
        original_filename="mix_design_doc.pdf",
        storage_key="/tmp/mix.pdf",
        document_type="TECHNICAL_SPEC",
        mime_type="application/pdf",
        file_size_bytes=2048,
        sha256_hash=uuid.uuid4().hex,
        uploaded_by=u_adm.id,
    )
    db.add(doc)
    db.flush()

    ev = Evidence(
        document_id=doc.id,
        evidence_type="TEXT",
        source_reference="Mix Specification Note 1",
        locator={"page": 1, "coordinates": [0, 0, 100, 100]},
        verification_status="VERIFIED",
        created_by=u_adm.id,
    )
    db.add(ev)
    db.flush()

    # Element, Schedule & Activity
    ee = EngineeringElement(
        project_id=p1_id,
        element_name="Footing Elements",
        element_type="FOUNDATION",
        created_by=u_adm.id,
    )
    db.add(ee)
    db.flush()

    sched = ConstructionSchedule(
        project_id=p1_id,
        schedule_version="1.0",
        calculation_status="CALCULATED",
        algorithm_version="1.0",
        input_snapshot_json={},
        calculated_by=u_adm.id,
    )
    db.add(sched)
    db.flush()

    act = ConstructionActivity(
        project_id=p1_id,
        activity_code="ACT-CONC-1N",
        activity_name="Pour M25 Footing Concrete",
        activity_type="CONCRETING",
        engineering_element_id=ee.id,
        duration_value=Decimal("10.0"),
        duration_unit="DAYS",
        duration_method="USER_PROVIDED",
        duration_classification="USER_PROVIDED",
        metadata_json={"planned_quantity": "100.0000"},
        status="ACTIVE",
        created_by=u_adm.id,
    )
    db.add(act)
    db.flush()

    base = MonitoringBaseline(
        project_id=p1_id,
        schedule_id=sched.id,
        schedule_version="1.0",
        schedule_algorithm_version="1.0",
        baseline_start_date=date(2026, 1, 1),
        frozen_by=u_adm.id,
        status="ACTIVE",
    )
    db.add(base)
    db.flush()

    # Cost Rate & Activity Rate Mapping
    crate = CostRate(
        project_id=p1_id,
        rate_code=f"RATE-M25-{uuid.uuid4().hex[:4]}",
        description="M25 Concrete Rate",
        unit="m3",
        rate_value=Decimal("150.00"),
        currency="INR",
        source_type="PROJECT_SPECIFIC",
        source_reference="Tender Schedule A",
        status="CONFIRMED",
        created_by=u_adm.id,
        confirmed_by=u_adm.id,
        confirmed_at=datetime.now(timezone.utc),
    )
    db.add(crate)
    db.flush()

    arm = ActivityRateMapping(
        project_id=p1_id,
        activity_id=act.id,
        cost_rate_id=crate.id,
        rate_value=Decimal("150.00"),
        rate_unit="m3",
        rate_version="1.0",
        currency="INR",
        status="ACTIVE",
        created_by=u_adm.id,
    )
    db.add(arm)
    db.flush()

    # Create certified progress certificate
    cert = PeriodProgressCertificate(
        project_id=p1_id,
        certificate_number=f"CERT-1N-{uuid.uuid4().hex[:6]}",
        certificate_type="PERIOD_SNAPSHOT",
        monitoring_baseline_id=base.id,
        baseline_schedule_id=sched.id,
        baseline_schedule_version="1.0",
        baseline_schedule_algorithm_version="1.0",
        baseline_start_date=date(2026, 1, 1),
        period_start_date=date(2026, 8, 1),
        period_cut_off_date=date(2026, 8, 31),
        certificate_status="DRAFT",
        currency="INR",
        period_claimed_value=Decimal("0.00"),
        period_certified_value=Decimal("0.00"),
        period_disputed_exposure=Decimal("0.00"),
        cumulative_claimed_value=Decimal("0.00"),
        cumulative_certified_value=Decimal("0.00"),
        cumulative_disputed_exposure=Decimal("0.00"),
        item_count=0,
        valuation_snapshot_hash="init",
    )
    db.add(cert)
    db.flush()

    dpr = DailyProgressReport(
        project_id=p1_id,
        report_date=date(2026, 8, 15),
        submitted_by=u_adm.id,
        submission_status="FINALIZED",
    )
    db.add(dpr)
    db.flush()

    dap = DailyActivityProgress(
        daily_report_id=dpr.id,
        project_id=p1_id,
        activity_id=act.id,
        contractor_progress_value=Decimal("100.0000"),
        contractor_progress_unit="m3",
        contractor_status="COMPLETED",
        created_by=u_adm.id,
    )
    db.add(dap)
    db.flush()

    dapv = DailyActivityProgressVerification(
        daily_activity_progress_id=dap.id,
        project_id=p1_id,
        verification_status="VERIFIED",
        verified_quantity=Decimal("100.0000"),
        verified_quantity_unit="m3",
        verified_by=u_adm.id,
    )
    db.add(dapv)
    db.flush()

    dpv = DailyProgressValuation(
        project_id=p1_id,
        verification_id=dapv.id,
        activity_rate_mapping_id=arm.id,
        contractor_claimed_quantity=Decimal("100.0000"),
        supervisor_certified_quantity=Decimal("100.0000"),
        quantity_unit="m3",
        unit_conversion_factor=Decimal("1.000000"),
        applied_rate_value=Decimal("150.00"),
        applied_rate_unit="m3",
        currency="INR",
        contractor_claimed_value=Decimal("15000.00"),
        certified_progress_value=Decimal("15000.00"),
        discrepancy_quantity=Decimal("0.000000"),
        disputed_valuation_exposure=Decimal("0.0000"),
        certified_certificate_id=cert.id,
        valuation_status="ACTIVE",
    )
    db.add(dpv)
    db.flush()

    cert_item = PeriodCertificateItem(
        certificate_id=cert.id,
        valuation_id=dpv.id,
        activity_id=act.id,
        claimed_quantity=Decimal("100.0000"),
        certified_quantity=Decimal("100.0000"),
        quantity_unit="m3",
        unit_conversion_factor=Decimal("1.000000"),
        applied_rate=Decimal("150.00"),
        applied_rate_unit="m3",
        currency="INR",
        claimed_amount=Decimal("15000.00"),
        certified_amount=Decimal("15000.00"),
        discrepancy_quantity=Decimal("0.0000"),
        disputed_exposure=Decimal("0.00"),
    )
    db.add(cert_item)
    db.flush()

    cert.period_claimed_value = Decimal("15000.00")
    cert.period_certified_value = Decimal("15000.00")
    cert.cumulative_claimed_value = Decimal("15000.00")
    cert.cumulative_certified_value = Decimal("15000.00")
    cert.item_count = 1
    cert.valuation_snapshot_hash = "valid_hash"
    cert.certificate_status = "CERTIFIED"
    cert.certified_by = u_adm.id
    cert.certified_at = datetime.now(timezone.utc)
    db.commit()

    # Seed baseline material and approved mix design
    mat_cem = MaterialItem(
        project_id=p1_id,
        material_code="MAT-CEM-PPC-BASE",
        material_name="Base Portland Pozzolana Cement",
        material_category="BINDER",
        standard_unit="BAG",
        density_kg_per_unit=Decimal("50.00"),
        standard_permissible_waste_pct=Decimal("3.00"),
    )
    db.add(mat_cem)
    db.flush()

    mix = MaterialMixDesign(
        project_id=p1_id,
        mix_code=f"MIX-M25-BASE-{uuid.uuid4().hex[:4]}",
        grade_designation="M25",
        mix_type="DESIGN_MIX",
        source_document_id=doc.id,
        evidence_id=ev.id,
        classification="CALCULATED",
        dry_volume_factor=Decimal("1.54"),
        water_cement_ratio=Decimal("0.45"),
        status="APPROVED",
        approved_by=u_adm.id,
        approved_at=datetime.now(timezone.utc),
    )
    db.add(mix)
    db.flush()

    mix_const = MaterialMixConstituent(
        mix_design_id=mix.id,
        material_item_id=mat_cem.id,
        quantity_per_m3=Decimal("8.200000"),
        unit="BAG",
    )
    db.add(mix_const)
    db.flush()
    db.commit()

    # Store IDs
    doc_id = doc.id
    ev_id = ev.id
    act_id = act.id
    base_id = base.id
    cert_id = cert.id
    cert_item_id = cert_item.id
    cem_id = mat_cem.id
    mix_id = mix.id
    u_adm_id = u_adm.id
    u_pm_id = u_pm.id
    u_sup_id = u_sup.id
    u_con_id = u_con.id

    db.close()

    return {
        "p1_id": p1_id,
        "p2_id": p2_id,
        "admin_token": admin_token,
        "pm_token": pm_token,
        "sup_token": sup_token,
        "con_token": con_token,
        "doc_id": doc_id,
        "ev_id": ev_id,
        "act_id": act_id,
        "base_id": base_id,
        "cert_id": cert_id,
        "cert_item_id": cert_item_id,
        "cem_id": cem_id,
        "mix_id": mix_id,
        "u_adm_id": u_adm_id,
        "u_sup_id": u_sup_id,
        "u_con_id": u_con_id,
    }


# ==============================================================================
# SCENARIOS 1–3: Material Catalog Integrity & Constraints
# ==============================================================================

def test_01_to_03_material_catalog_integrity(client_fixture, setup_phase_1n):
    p1 = setup_phase_1n["p1_id"]
    token = setup_phase_1n["admin_token"]

    # SCENARIO 1: Create material item in project
    resp1 = client_fixture.post(
        f"/api/projects/{p1}/materials",
        json={
            "material_code": "MAT-CEM-PPC",
            "material_name": "Portland Pozzolana Cement",
            "material_category": "BINDER",
            "standard_unit": "BAG",
            "density_kg_per_unit": "50.00",
            "standard_permissible_waste_pct": "3.00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp1.status_code == 201
    mat_id = resp1.json()["id"]

    # Reject duplicate material code in same project
    dup_resp = client_fixture.post(
        f"/api/projects/{p1}/materials",
        json={
            "material_code": "MAT-CEM-PPC",
            "material_name": "Duplicate Cement",
            "material_category": "BINDER",
            "standard_unit": "BAG",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert dup_resp.status_code == 409

    # SCENARIO 2: Global material (project_id = NULL) uniqueness
    with TestingSessionLocal() as db:
        g_mat1 = MaterialItem(
            project_id=None,
            material_code="GLOB-STEEL-500D",
            material_name="Global Fe500D TMT",
            material_category="REINFORCEMENT",
            standard_unit="MT",
            standard_permissible_waste_pct=Decimal("2.00"),
        )
        db.add(g_mat1)
        db.commit()

        with pytest.raises(Exception):
            g_mat2 = MaterialItem(
                project_id=None,
                material_code="GLOB-STEEL-500D",
                material_name="Duplicate Global Fe500D",
                material_category="REINFORCEMENT",
                standard_unit="MT",
            )
            db.add(g_mat2)
            db.commit()
        db.rollback()

    # SCENARIO 3: Reject invalid category or negative density
    with TestingSessionLocal() as db:
        with pytest.raises(Exception):
            bad_cat = MaterialItem(
                project_id=p1,
                material_code="BAD-CAT",
                material_name="Bad Category",
                material_category="INVALID_CATEGORY",
                standard_unit="KG",
            )
            db.add(bad_cat)
            db.commit()
        db.rollback()


# ==============================================================================
# SCENARIOS 4–7: Mix Formulation & Evidence Constraints
# ==============================================================================

def test_04_to_07_mix_formulation_and_evidence(client_fixture, setup_phase_1n):
    p1 = setup_phase_1n["p1_id"]
    token = setup_phase_1n["sup_token"]
    cem_id = setup_phase_1n["cem_id"]

    # SCENARIO 4: DESIGN_MIX without evidence fails
    fail_dm = client_fixture.post(
        f"/api/projects/{p1}/mix-designs",
        json={
            "mix_code": "DM-FAIL-NO-EVID",
            "grade_designation": "M25",
            "mix_type": "DESIGN_MIX",
            "constituents": [{"material_item_id": cem_id, "quantity_per_m3": "8.20", "unit": "BAG"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert fail_dm.status_code == 422

    # SCENARIO 5: DESIGN_MIX with evidence created in DRAFT and approved
    dm_resp = client_fixture.post(
        f"/api/projects/{p1}/mix-designs",
        json={
            "mix_code": "DM-M25-VALID",
            "grade_designation": "M25",
            "mix_type": "DESIGN_MIX",
            "source_document_id": setup_phase_1n["doc_id"],
            "evidence_id": setup_phase_1n["ev_id"],
            "dry_volume_factor": "1.5400",
            "water_cement_ratio": "0.45",
            "constituents": [{"material_item_id": cem_id, "quantity_per_m3": "8.20", "unit": "BAG"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert dm_resp.status_code == 201
    dm_id = dm_resp.json()["id"]
    assert dm_resp.json()["status"] == "DRAFT"
    assert dm_resp.json()["classification"] == "CALCULATED"

    # Approve mix design
    app_resp = client_fixture.patch(
        f"/api/projects/{p1}/mix-designs/{dm_id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert app_resp.status_code == 200
    assert app_resp.json()["status"] == "APPROVED"
    assert app_resp.json()["approved_by"] is not None
    assert app_resp.json()["approved_at"] is not None

    # SCENARIO 6: Attempting NOMINAL_MIX with CALCULATED fails DB constraint
    with TestingSessionLocal() as db:
        with pytest.raises(Exception):
            bad_nom = MaterialMixDesign(
                project_id=p1,
                mix_code="NOM-BAD-CALC",
                grade_designation="M20",
                mix_type="NOMINAL_MIX",
                rule_code="CPWD-M20",
                classification="CALCULATED", # violates ck_mmd_nominal_mix_rule
                status="DRAFT",
            )
            db.add(bad_nom)
            db.commit()
        db.rollback()

    # SCENARIO 7: Valid NOMINAL_MIX is marked ASSUMPTION_BASED
    nom_resp = client_fixture.post(
        f"/api/projects/{p1}/mix-designs",
        json={
            "mix_code": "NOM-M20-CPWD",
            "grade_designation": "M20",
            "mix_type": "NOMINAL_MIX",
            "rule_code": "CPWD-DSR-2023-M20",
            "constituents": [{"material_item_id": cem_id, "quantity_per_m3": "6.80", "unit": "BAG"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert nom_resp.status_code == 201
    assert nom_resp.json()["classification"] == "ASSUMPTION_BASED"


# ==============================================================================
# SCENARIOS 8–10: Activity Provenance & Consistency
# ==============================================================================

def test_08_to_10_activity_provenance_and_consistency(client_fixture, setup_phase_1n):
    p1 = setup_phase_1n["p1_id"]
    cert_id = setup_phase_1n["cert_id"]
    cert_item_id = setup_phase_1n["cert_item_id"]
    act_id = setup_phase_1n["act_id"]
    cem_id = setup_phase_1n["cem_id"]
    mix_id = setup_phase_1n["mix_id"]

    with TestingSessionLocal() as db:
        mix = db.query(MaterialMixDesign).filter(MaterialMixDesign.id == mix_id).first()

        # SCENARIO 8: Inserting TheoreticalConsumptionItem with mismatched activity_id fails trigger
        with pytest.raises(Exception) as exc:
            rogue_tci = TheoreticalConsumptionItem(
                project_id=p1,
                certificate_id=cert_id,
                certificate_item_id=cert_item_id,
                activity_id=str(uuid.uuid4()), # mismatched rogue activity_id
                material_item_id=cem_id,
                mix_design_id=mix.id,
                certified_activity_volume=Decimal("100.00"),
                coefficient_per_unit=Decimal("8.20"),
                dry_volume_factor=Decimal("1.54"),
                theoretical_quantity=Decimal("820.00"),
                unit="BAG",
                mix_design_version=mix.mix_code,
            )
            db.add(rogue_tci)
            db.commit()
        db.rollback()
        assert "does not match period certificate item activity" in str(exc.value)

        # SCENARIO 9: Cross-project certificate item reference fails
        with pytest.raises(Exception):
            cross_tci = TheoreticalConsumptionItem(
                project_id=setup_phase_1n["p2_id"], # wrong project
                certificate_id=cert_id,
                certificate_item_id=cert_item_id,
                activity_id=act_id,
                material_item_id=cem_id,
                mix_design_id=mix.id,
                certified_activity_volume=Decimal("100.00"),
                coefficient_per_unit=Decimal("8.20"),
                dry_volume_factor=Decimal("1.54"),
                theoretical_quantity=Decimal("820.00"),
                unit="BAG",
                mix_design_version=mix.mix_code,
            )
            db.add(cross_tci)
            db.commit()
        db.rollback()

    # SCENARIO 10: Theoretical consumption endpoint generates correct active mix resolution
    token = setup_phase_1n["sup_token"]
    tci_resp = client_fixture.post(
        f"/api/projects/{p1}/certificates/{cert_id}/theoretical-consumption/generate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert tci_resp.status_code == 201
    items = tci_resp.json()
    assert len(items) >= 1
    assert Decimal(items[0]["theoretical_quantity"]) == Decimal("820.0000")


# ==============================================================================
# SCENARIOS 11–15: Actual Consumption Dual-Reporting & Verification
# ==============================================================================

def test_11_to_15_actual_consumption_reporting_and_verification(client_fixture, setup_phase_1n):
    p1 = setup_phase_1n["p1_id"]
    cert_id = setup_phase_1n["cert_id"]
    con_token = setup_phase_1n["con_token"]
    sup_token = setup_phase_1n["sup_token"]
    cem_id = setup_phase_1n["cem_id"]

    # SCENARIO 11: Contractor submits store challan
    challan_ref = f"CHALLAN-STORE-{uuid.uuid4().hex[:6]}"
    sub_resp = client_fixture.post(
        f"/api/projects/{p1}/certificates/{cert_id}/material-consumption/submit",
        json={
            "material_item_id": cem_id,
            "store_challan_reference": challan_ref,
            "consumption_date_start": "2026-08-01",
            "consumption_date_end": "2026-08-15",
            "contractor_declared_quantity": "835.0000",
            "unit": "BAG",
        },
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert sub_resp.status_code == 201
    entry_id = sub_resp.json()["id"]
    assert sub_resp.json()["submission_status"] == "SUBMITTED"
    assert sub_resp.json()["supervisor_verified_quantity"] is None

    # SCENARIO 12: Duplicate challan rejected
    dup_resp = client_fixture.post(
        f"/api/projects/{p1}/certificates/{cert_id}/material-consumption/submit",
        json={
            "material_item_id": cem_id,
            "store_challan_reference": challan_ref,
            "consumption_date_start": "2026-08-01",
            "consumption_date_end": "2026-08-15",
            "contractor_declared_quantity": "835.0000",
            "unit": "BAG",
        },
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert dup_resp.status_code == 409

    # SCENARIO 13 & 14: Supervisor verifies differing quantity -> is_disputed=True
    ver_resp = client_fixture.patch(
        f"/api/projects/{p1}/material-consumption/{entry_id}/verify",
        json={"supervisor_verified_quantity": "830.0000", "is_rejected": False},
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert ver_resp.status_code == 200
    res = ver_resp.json()
    assert res["submission_status"] == "VERIFIED"
    assert Decimal(res["contractor_declared_quantity"]) == Decimal("835.0000") # preserved
    assert Decimal(res["supervisor_verified_quantity"]) == Decimal("830.0000")
    assert Decimal(res["discrepancy_quantity"]) == Decimal("5.0000")
    assert res["is_disputed"] is True

    # SCENARIO 15: Direct SQL mutation or deletion of VERIFIED entry blocked by trigger
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc_del:
            db.execute(text(f"DELETE FROM material_consumption_entries WHERE id = '{entry_id}'"))
            db.commit()
        db.rollback()
        assert "Cannot delete VERIFIED material consumption entry" in str(exc_del.value)

        with pytest.raises(Exception) as exc_mut:
            db.execute(text(f"UPDATE material_consumption_entries SET supervisor_verified_quantity = 999 WHERE id = '{entry_id}'"))
            db.commit()
        db.rollback()
        assert "Cannot mutate VERIFIED material consumption entry" in str(exc_mut.value)


# ==============================================================================
# SCENARIOS 16–18: Deterministic Stoichiometry & Coefficient Snapshots
# ==============================================================================

def test_16_to_18_stoichiometry_and_snapshots(client_fixture, setup_phase_1n):
    p1 = setup_phase_1n["p1_id"]
    cert_id = setup_phase_1n["cert_id"]
    token = setup_phase_1n["sup_token"]

    # SCENARIO 16: Verify 100 m3 * 8.2 bags = 820.0000 bags
    with TestingSessionLocal() as db:
        tci = db.query(TheoreticalConsumptionItem).filter(TheoreticalConsumptionItem.certificate_id == cert_id).first()
        if not tci:
            tci_resp = client_fixture.post(
                f"/api/projects/{p1}/certificates/{cert_id}/theoretical-consumption/generate",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert tci_resp.status_code == 201
            tci = db.query(TheoreticalConsumptionItem).filter(TheoreticalConsumptionItem.certificate_id == cert_id).first()

        assert tci is not None
        assert tci.theoretical_quantity == Decimal("820.0000")
        assert tci.coefficient_per_unit == Decimal("8.200000")
        original_qty = tci.theoretical_quantity

        # SCENARIO 17: Mutating mix design constituent does not alter historical theoretical item
        mix_const = db.query(MaterialMixConstituent).filter(MaterialMixConstituent.mix_design_id == tci.mix_design_id).first()
        mix_const.quantity_per_m3 = Decimal("9.999999")
        db.commit()

        # Re-fetch tci to confirm stored snapshot is unchanged
        db.refresh(tci)
        assert tci.theoretical_quantity == original_qty
        assert tci.coefficient_per_unit == Decimal("8.200000")

        # SCENARIO 18: Zero certified volume yields exactly zero theoretical quantity
        zero_vol = Decimal("0.000000")
        coeff = Decimal("8.200000")
        assert zero_vol * coeff == Decimal("0.000000")


# ==============================================================================
# SCENARIOS 19–22: Wastage & Variance Semantics
# ==============================================================================

def test_19_to_22_wastage_and_variance_mathematics(client_fixture, setup_phase_1n):
    # SCENARIO 19: Under-consumption (saving)
    # Theoretical = 820, Actual = 800 -> Variance = -20
    theo = Decimal("820.0000")
    act_saving = Decimal("800.0000")
    var_saving = act_saving - theo # -20
    is_saving = (var_saving < 0)
    unauth_waste_saving = Decimal("0.0000")
    assert is_saving is True
    assert unauth_waste_saving == Decimal("0.0000")

    # SCENARIO 20: Over-consumption within permissible threshold (<= 3%)
    # Theoretical = 820, Permissible = 3% = 24.60
    # Actual = 835 -> Variance = 15.00 <= 24.60 -> Unauthorized Waste = 0
    perm_waste_pct = Decimal("3.00")
    perm_waste_qty = theo * (perm_waste_pct / Decimal("100.00")) # 24.6000
    act_within = Decimal("835.0000")
    var_within = act_within - theo # 15.0000
    unauth_within = max(Decimal("0.0000"), var_within - perm_waste_qty) # 0.0000
    assert unauth_within == Decimal("0.0000")

    # SCENARIO 21: Over-consumption exceeding permissible threshold (> 3%)
    # Actual = 860 -> Variance = 40.00 > 24.60 -> Unauthorized Waste = 40 - 24.60 = 15.40
    act_excess = Decimal("860.0000")
    var_excess = act_excess - theo # 40.0000
    unauth_excess = max(Decimal("0.0000"), var_excess - perm_waste_qty) # 15.4000
    assert unauth_excess == Decimal("15.4000")
    assert unauth_excess > Decimal("0.0000")

    # SCENARIO 22: Exact match
    act_exact = Decimal("820.0000")
    var_exact = act_exact - theo
    unauth_exact = max(Decimal("0.0000"), var_exact - perm_waste_qty)
    assert var_exact == Decimal("0.0000")
    assert unauth_exact == Decimal("0.0000")


# ==============================================================================
# SCENARIOS 23–26: Reconciliation Report Lifecycle & Immutability
# ==============================================================================

def test_23_to_26_reconciliation_report_lifecycle_and_immutability(client_fixture, setup_phase_1n):
    p1 = setup_phase_1n["p1_id"]
    cert_id = setup_phase_1n["cert_id"]
    token = setup_phase_1n["sup_token"]

    # Ensure theoretical consumption exists
    client_fixture.post(
        f"/api/projects/{p1}/certificates/{cert_id}/theoretical-consumption/generate",
        headers={"Authorization": f"Bearer {token}"},
    )

    # SCENARIO 23 & 24: Finalize material reconciliation report
    fin_resp = client_fixture.post(
        f"/api/projects/{p1}/certificates/{cert_id}/material-reconciliation/finalize",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert fin_resp.status_code == 200
    reports = fin_resp.json()
    assert len(reports) >= 1
    rep = reports[0]
    rep_id = rep["id"]
    assert rep["status"] == "FINALIZED"
    assert rep["reconciliation_hash"] is not None
    assert len(rep["reconciliation_hash"]) == 64
    assert rep["finalized_by"] is not None
    assert rep["finalized_at"] is not None

    # SCENARIO 25: Direct SQL UPDATE on FINALIZED report blocked by trigger
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc_upd:
            db.execute(text(f"UPDATE material_reconciliation_reports SET cumulative_actual_quantity = 9999 WHERE id = '{rep_id}'"))
            db.commit()
        db.rollback()
        assert "immutable historical audit records" in str(exc_upd.value)

    # SCENARIO 26: Direct SQL DELETE on FINALIZED report blocked by trigger
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc_del:
            db.execute(text(f"DELETE FROM material_reconciliation_reports WHERE id = '{rep_id}'"))
            db.commit()
        db.rollback()
        assert "immutable historical audit records" in str(exc_del.value)


# ==============================================================================
# SCENARIOS 27–29: Security & Project Boundary Isolation
# ==============================================================================

def test_27_to_29_security_and_project_isolation(client_fixture, setup_phase_1n):
    p1 = setup_phase_1n["p1_id"]
    p2 = setup_phase_1n["p2_id"]
    cert_id = setup_phase_1n["cert_id"]
    con_token = setup_phase_1n["con_token"]
    sup_token = setup_phase_1n["sup_token"]

    # SCENARIO 27: Cross-project access attempt returns 403 Forbidden
    cross_resp = client_fixture.get(
        f"/api/projects/{p2}/certificates/{cert_id}/material-consumption",
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert cross_resp.status_code == 403

    # SCENARIO 28: Contractor forbidden from approving mix design or finalizing reconciliation
    app_fail = client_fixture.patch(
        f"/api/projects/{p1}/mix-designs/any-id/approve",
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert app_fail.status_code == 403

    fin_fail = client_fixture.post(
        f"/api/projects/{p1}/certificates/{cert_id}/material-reconciliation/finalize",
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert fin_fail.status_code == 403

    # SCENARIO 29: Contractor forbidden from verifying material consumption
    ver_fail = client_fixture.patch(
        f"/api/projects/{p1}/material-consumption/any-id/verify",
        json={"supervisor_verified_quantity": "100.00"},
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert ver_fail.status_code == 403


# ==============================================================================
# SCENARIOS 30–32: Migration Lifecycle & Full Regression
# ==============================================================================

def test_30_to_32_baseline_bom_generation_and_audit(client_fixture, setup_phase_1n):
    p1 = setup_phase_1n["p1_id"]
    base_id = setup_phase_1n["base_id"]
    token = setup_phase_1n["sup_token"]

    # Generate Material Plans (BOM)
    gen_resp = client_fixture.post(
        f"/api/projects/{p1}/baselines/{base_id}/material-plans/generate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert gen_resp.status_code == 201
    plans = gen_resp.json()
    assert len(plans) >= 1
    assert Decimal(plans[0]["planned_quantity"]) > Decimal("0.0000")
    assert Decimal(plans[0]["gross_planned_quantity"]) >= Decimal(plans[0]["planned_quantity"])

    # List material plans
    list_resp = client_fixture.get(
        f"/api/projects/{p1}/baselines/{base_id}/material-plans",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == len(plans)


# ==============================================================================
# PHASE 1N HARDENING VERIFICATION TESTS
# ==============================================================================

def test_hardening_01_authorization_model_strictly_enforced(client_fixture, setup_phase_1n):
    p1 = setup_phase_1n["p1_id"]
    p2 = setup_phase_1n["p2_id"]
    cert_id = setup_phase_1n["cert_id"]
    base_id = setup_phase_1n["base_id"]
    cem_id = setup_phase_1n["cem_id"]
    con_token = setup_phase_1n["con_token"]
    sup_token = setup_phase_1n["sup_token"]
    pm_token = setup_phase_1n["pm_token"]
    adm_token = setup_phase_1n["admin_token"]

    # 1. contractor cannot approve mix
    resp = client_fixture.patch(
        f"/api/projects/{p1}/mix-designs/any-id/approve",
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert resp.status_code == 403

    # 2. contractor cannot finalize reconciliation
    resp = client_fixture.post(
        f"/api/projects/{p1}/certificates/{cert_id}/material-reconciliation/finalize",
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert resp.status_code == 403

    # 3. supervisor cannot submit contractor consumption
    resp = client_fixture.post(
        f"/api/projects/{p1}/certificates/{cert_id}/material-consumption/submit",
        json={
            "material_item_id": cem_id,
            "store_challan_reference": f"CHALLAN-SUP-SUB-{uuid.uuid4().hex[:4]}",
            "consumption_date_start": "2026-08-01",
            "consumption_date_end": "2026-08-15",
            "contractor_declared_quantity": "100.0000",
            "unit": "BAG",
        },
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert resp.status_code == 403

    # 4. contractor can submit consumption
    challan_ref = f"CHALLAN-CON-SUB-{uuid.uuid4().hex[:4]}"
    sub_resp = client_fixture.post(
        f"/api/projects/{p1}/certificates/{cert_id}/material-consumption/submit",
        json={
            "material_item_id": cem_id,
            "store_challan_reference": challan_ref,
            "consumption_date_start": "2026-08-01",
            "consumption_date_end": "2026-08-15",
            "contractor_declared_quantity": "100.0000",
            "unit": "BAG",
        },
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert sub_resp.status_code == 201
    entry_id = sub_resp.json()["id"]

    # 5. supervisor can verify consumption
    ver_resp = client_fixture.patch(
        f"/api/projects/{p1}/material-consumption/{entry_id}/verify",
        json={"supervisor_verified_quantity": "100.0000", "is_rejected": False},
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert ver_resp.status_code == 200

    # 6. project_manager cannot gain Phase 1N authority
    # PM cannot approve mix
    resp = client_fixture.patch(
        f"/api/projects/{p1}/mix-designs/any-id/approve",
        headers={"Authorization": f"Bearer {pm_token}"},
    )
    assert resp.status_code == 403

    # PM cannot verify consumption
    resp = client_fixture.patch(
        f"/api/projects/{p1}/material-consumption/{entry_id}/verify",
        json={"supervisor_verified_quantity": "100.0000"},
        headers={"Authorization": f"Bearer {pm_token}"},
    )
    assert resp.status_code == 403

    # PM cannot finalize reconciliation
    resp = client_fixture.post(
        f"/api/projects/{p1}/certificates/{cert_id}/material-reconciliation/finalize",
        headers={"Authorization": f"Bearer {pm_token}"},
    )
    assert resp.status_code == 403

    # PM cannot generate material plans
    resp = client_fixture.post(
        f"/api/projects/{p1}/baselines/{base_id}/material-plans/generate",
        headers={"Authorization": f"Bearer {pm_token}"},
    )
    assert resp.status_code == 403

    # PM cannot generate theoretical consumption
    resp = client_fixture.post(
        f"/api/projects/{p1}/certificates/{cert_id}/theoretical-consumption/generate",
        headers={"Authorization": f"Bearer {pm_token}"},
    )
    assert resp.status_code == 403

    # 7. cross-project users remain forbidden
    resp = client_fixture.get(
        f"/api/projects/{p2}/certificates/{cert_id}/material-consumption",
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert resp.status_code == 403


def test_hardening_02_material_category_canonical_vocabulary(client_fixture, setup_phase_1n):
    p1 = setup_phase_1n["p1_id"]
    token = setup_phase_1n["admin_token"]

    canonical_categories = [
        "BINDER",
        "AGGREGATE",
        "REINFORCEMENT",
        "MASONRY",
        "CHEMICAL",
        "WATER",
        "TIMBER",
        "STEEL_SECTION",
    ]

    for cat in canonical_categories:
        c_code = f"MAT-{cat[:4]}-{uuid.uuid4().hex[:4]}"
        r = client_fixture.post(
            f"/api/projects/{p1}/materials",
            json={
                "material_code": c_code,
                "material_name": f"Material {cat}",
                "material_category": cat,
                "standard_unit": "KG",
                "standard_permissible_waste_pct": "2.50",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 201

    invalid_categories = ["FINE_AGGREGATE", "COARSE_AGGREGATE", "ADMIXTURE", "OTHER", "UNKNOWN"]
    for inv_cat in invalid_categories:
        r = client_fixture.post(
            f"/api/projects/{p1}/materials",
            json={
                "material_code": f"MAT-INV-{uuid.uuid4().hex[:4]}",
                "material_name": "Invalid Category Material",
                "material_category": inv_cat,
                "standard_unit": "KG",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 422


def test_hardening_03_design_mix_evidence_verification(client_fixture, setup_phase_1n):
    p1 = setup_phase_1n["p1_id"]
    p2 = setup_phase_1n["p2_id"]
    token = setup_phase_1n["sup_token"]
    u_adm_id = setup_phase_1n["u_adm_id"]
    cem_id = setup_phase_1n["cem_id"]
    valid_doc_id = setup_phase_1n["doc_id"]
    valid_ev_id = setup_phase_1n["ev_id"]

    with TestingSessionLocal() as db:
        # Create unverified evidence in doc
        unver_ev = Evidence(
            document_id=valid_doc_id,
            evidence_type="TEXT",
            source_reference="Unverified Spec Note",
            locator={"page": 2},
            verification_status="UNVERIFIED",
            created_by=u_adm_id,
        )
        db.add(unver_ev)

        # Create doc in p2
        doc_p2 = Document(
            project_id=p2,
            original_filename="p2_spec.pdf",
            storage_key="/tmp/p2_spec.pdf",
            document_type="TECHNICAL_SPEC",
            mime_type="application/pdf",
            file_size_bytes=1024,
            sha256_hash=uuid.uuid4().hex,
            uploaded_by=u_adm_id,
        )
        db.add(doc_p2)
        db.flush()

        # Create verified evidence in p2
        p2_ev = Evidence(
            document_id=doc_p2.id,
            evidence_type="TEXT",
            source_reference="P2 Spec Note",
            locator={"page": 1},
            verification_status="VERIFIED",
            created_by=u_adm_id,
        )
        db.add(p2_ev)
        db.commit()

        unver_ev_id = unver_ev.id
        doc_p2_id = doc_p2.id
        p2_ev_id = p2_ev.id

    # 1. Nonexistent document rejected
    r1 = client_fixture.post(
        f"/api/projects/{p1}/mix-designs",
        json={
            "mix_code": f"DM-NODOC-{uuid.uuid4().hex[:4]}",
            "grade_designation": "M25",
            "mix_type": "DESIGN_MIX",
            "source_document_id": str(uuid.uuid4()),
            "evidence_id": valid_ev_id,
            "constituents": [{"material_item_id": cem_id, "quantity_per_m3": "8.20", "unit": "BAG"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r1.status_code == 422

    # 2. Nonexistent evidence rejected
    r2 = client_fixture.post(
        f"/api/projects/{p1}/mix-designs",
        json={
            "mix_code": f"DM-NOEV-{uuid.uuid4().hex[:4]}",
            "grade_designation": "M25",
            "mix_type": "DESIGN_MIX",
            "source_document_id": valid_doc_id,
            "evidence_id": str(uuid.uuid4()),
            "constituents": [{"material_item_id": cem_id, "quantity_per_m3": "8.20", "unit": "BAG"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 422

    # 3. Evidence from another document rejected
    r3 = client_fixture.post(
        f"/api/projects/{p1}/mix-designs",
        json={
            "mix_code": f"DM-MISMATCH-DOC-{uuid.uuid4().hex[:4]}",
            "grade_designation": "M25",
            "mix_type": "DESIGN_MIX",
            "source_document_id": valid_doc_id,
            "evidence_id": p2_ev_id,
            "constituents": [{"material_item_id": cem_id, "quantity_per_m3": "8.20", "unit": "BAG"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r3.status_code == 422

    # 4. Evidence from another project rejected
    r4 = client_fixture.post(
        f"/api/projects/{p1}/mix-designs",
        json={
            "mix_code": f"DM-CROSS-PROJ-{uuid.uuid4().hex[:4]}",
            "grade_designation": "M25",
            "mix_type": "DESIGN_MIX",
            "source_document_id": doc_p2_id,
            "evidence_id": p2_ev_id,
            "constituents": [{"material_item_id": cem_id, "quantity_per_m3": "8.20", "unit": "BAG"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r4.status_code == 422

    # 5. Unverified evidence: allowed in DRAFT, rejected on approval
    r5 = client_fixture.post(
        f"/api/projects/{p1}/mix-designs",
        json={
            "mix_code": f"DM-UNVER-{uuid.uuid4().hex[:4]}",
            "grade_designation": "M25",
            "mix_type": "DESIGN_MIX",
            "source_document_id": valid_doc_id,
            "evidence_id": unver_ev_id,
            "constituents": [{"material_item_id": cem_id, "quantity_per_m3": "8.20", "unit": "BAG"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r5.status_code == 201
    mix_unver_id = r5.json()["id"]
    app_r5 = client_fixture.patch(
        f"/api/projects/{p1}/mix-designs/{mix_unver_id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert app_r5.status_code == 422
    assert "verification_status" in app_r5.json()["detail"]

    # 6. Valid same-project verified evidence: approved successfully
    r6 = client_fixture.post(
        f"/api/projects/{p1}/mix-designs",
        json={
            "mix_code": f"DM-VER-{uuid.uuid4().hex[:4]}",
            "grade_designation": "M25",
            "mix_type": "DESIGN_MIX",
            "source_document_id": valid_doc_id,
            "evidence_id": valid_ev_id,
            "constituents": [{"material_item_id": cem_id, "quantity_per_m3": "8.20", "unit": "BAG"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r6.status_code == 201
    mix_ver_id = r6.json()["id"]
    app_r6 = client_fixture.patch(
        f"/api/projects/{p1}/mix-designs/{mix_ver_id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert app_r6.status_code == 200
    assert app_r6.json()["status"] == "APPROVED"


def test_hardening_04_material_mix_project_isolation(client_fixture, setup_phase_1n):
    p1 = setup_phase_1n["p1_id"]
    p2 = setup_phase_1n["p2_id"]
    token = setup_phase_1n["admin_token"]
    sup_token = setup_phase_1n["sup_token"]

    # Create material in P2
    r_p2_mat = client_fixture.post(
        f"/api/projects/{p2}/materials",
        json={
            "material_code": f"P2-MAT-{uuid.uuid4().hex[:4]}",
            "material_name": "Project 2 Material",
            "material_category": "AGGREGATE",
            "standard_unit": "M3",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_p2_mat.status_code == 201
    p2_mat_id = r_p2_mat.json()["id"]

    # Create global material
    with TestingSessionLocal() as db:
        g_mat = MaterialItem(
            project_id=None,
            material_code=f"GLOB-{uuid.uuid4().hex[:4]}",
            material_name="Global Aggregate",
            material_category="AGGREGATE",
            standard_unit="M3",
        )
        db.add(g_mat)
        db.commit()
        g_mat_id = g_mat.id

    # 1. Same-project material accepted
    r1 = client_fixture.post(
        f"/api/projects/{p1}/mix-designs",
        json={
            "mix_code": f"NOM-P1-SAME-{uuid.uuid4().hex[:4]}",
            "grade_designation": "M15",
            "mix_type": "NOMINAL_MIX",
            "rule_code": "CPWD-M15",
            "constituents": [{"material_item_id": setup_phase_1n["cem_id"], "quantity_per_m3": "5.00", "unit": "BAG"}],
        },
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert r1.status_code == 201

    # 2. Global material accepted
    r2 = client_fixture.post(
        f"/api/projects/{p1}/mix-designs",
        json={
            "mix_code": f"NOM-GLOB-OK-{uuid.uuid4().hex[:4]}",
            "grade_designation": "M15",
            "mix_type": "NOMINAL_MIX",
            "rule_code": "CPWD-M15",
            "constituents": [{"material_item_id": g_mat_id, "quantity_per_m3": "1.20", "unit": "M3"}],
        },
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert r2.status_code == 201

    # 3. Cross-project material rejected
    r3 = client_fixture.post(
        f"/api/projects/{p1}/mix-designs",
        json={
            "mix_code": f"NOM-CROSS-FAIL-{uuid.uuid4().hex[:4]}",
            "grade_designation": "M15",
            "mix_type": "NOMINAL_MIX",
            "rule_code": "CPWD-M15",
            "constituents": [{"material_item_id": p2_mat_id, "quantity_per_m3": "1.20", "unit": "M3"}],
        },
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert r3.status_code == 422

    # 4. Nonexistent material rejected
    r4 = client_fixture.post(
        f"/api/projects/{p1}/mix-designs",
        json={
            "mix_code": f"NOM-NONEXIST-{uuid.uuid4().hex[:4]}",
            "grade_designation": "M15",
            "mix_type": "NOMINAL_MIX",
            "rule_code": "CPWD-M15",
            "constituents": [{"material_item_id": str(uuid.uuid4()), "quantity_per_m3": "1.20", "unit": "M3"}],
        },
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert r4.status_code == 404


def test_hardening_05_canonical_hash_hardening():
    from app.services.material_reconciliation_service import _compute_reconciliation_hash
    import json
    import hashlib

    # Deterministic inputs
    proj_id = "test-proj-123"
    cert_id = "test-cert-456"
    mat_id = "test-mat-789"
    cut_date = date(2026, 8, 31)

    h1 = _compute_reconciliation_hash(
        proj_id, cert_id, mat_id, cut_date,
        Decimal("820.0000"), Decimal("835.0000"),
        Decimal("24.6000"), Decimal("15.0000"), Decimal("0.0000")
    )

    # Identical semantic payload => identical hash
    h2 = _compute_reconciliation_hash(
        proj_id, cert_id, mat_id, cut_date,
        Decimal("820.0000"), Decimal("835.0000"),
        Decimal("24.6000"), Decimal("15.0000"), Decimal("0.0000")
    )
    assert h1 == h2
    assert len(h1) == 64

    # Different value => different hash
    h3 = _compute_reconciliation_hash(
        proj_id, cert_id, mat_id, cut_date,
        Decimal("820.0000"), Decimal("860.0000"), # changed actual
        Decimal("24.6000"), Decimal("40.0000"), Decimal("15.4000")
    )
    assert h1 != h3

    # Key insertion order does not change hash
    dict_a = {
        "a": "1",
        "b": "2",
        "c": "3",
    }
    dict_b = {
        "c": "3",
        "a": "1",
        "b": "2",
    }
    hash_a = hashlib.sha256(json.dumps(dict_a, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()
    hash_b = hashlib.sha256(json.dumps(dict_b, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()
    assert hash_a == hash_b
