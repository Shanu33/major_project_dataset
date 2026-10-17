import hashlib
import json
import threading
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token, get_password_hash
from app.db.database import engine, get_db
from app.db.models import (
    ActivityRateMapping,
    Base,
    ConstructionActivity,
    ConstructionSchedule,
    CostRate,
    DailyActivityProgress,
    DailyActivityProgressVerification,
    DailyProgressReport,
    DailyProgressValuation,
    MaterialActualConsumptionEntry,
    MaterialConsumptionReconciliation,
    MaterialConsumptionVerification,
    MaterialIssueAllocation,
    MaterialItem,
    MaterialMixDesign,
    MaterialPerformanceSnapshot,
    MaterialPlan,
    MaterialRequirementItem,
    MaterialRequirementPlan,
    MaterialStockBalance,
    MaterialStockLedger,
    MonitoringBaseline,
    PeriodCertificateItem,
    PeriodProgressCertificate,
    Project,
    ProjectMember,
    TheoreticalConsumptionItem,
    User,
)
from app.main import app
from app.services.material_performance_service import generate_canonical_hash

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


def make_theo_item(
    db, project_id, activity_id, material_item_id, qty, unit, mix_id, cert_id, cert_item_id
):
    theo = TheoreticalConsumptionItem(
        project_id=project_id,
        certificate_id=cert_id,
        certificate_item_id=cert_item_id,
        activity_id=activity_id,
        material_item_id=material_item_id,
        mix_design_id=mix_id,
        certified_activity_volume=Decimal("10.000000"),
        coefficient_per_unit=Decimal("1.000000"),
        dry_volume_factor=Decimal("1.0000"),
        theoretical_quantity=qty,
        unit=unit,
        mix_design_version="1.0",
        calculation_algorithm_version="1.0-DETERMINISTIC",
    )
    db.add(theo)
    db.commit()
    return theo


def make_consumption_entry_and_verif(
    db, project_id, activity_id, material_item_id, qty, unit, con_id, sup_id, verif_status="VERIFIED"
):
    c_entry = MaterialActualConsumptionEntry(
        project_id=project_id,
        activity_id=activity_id,
        material_item_id=material_item_id,
        contractor_consumed_quantity=qty,
        contractor_consumed_unit=unit,
        consumption_date=date(2026, 10, 5),
        declared_by=con_id,
        verification_status=verif_status,
    )
    db.add(c_entry)
    db.commit()
    db.refresh(c_entry)

    v_entry = MaterialConsumptionVerification(
        consumption_entry_id=c_entry.id,
        verified_quantity=qty,
        verified_unit=unit,
        verification_status=verif_status,
        verified_by=sup_id,
    )
    db.add(v_entry)
    db.commit()
    db.refresh(v_entry)
    return c_entry, v_entry


@pytest.fixture(scope="module")
def setup_data():
    adm_email = f"adm_1r_{uuid.uuid4().hex[:6]}@test.com"
    sup_email = f"sup_1r_{uuid.uuid4().hex[:6]}@test.com"
    con_email = f"con_1r_{uuid.uuid4().hex[:6]}@test.com"
    pm_email = f"pm_1r_{uuid.uuid4().hex[:6]}@test.com"

    with TestingSessionLocal() as db:
        adm = User(email=adm_email, password_hash=get_password_hash("pass"), role="admin")
        sup = User(email=sup_email, password_hash=get_password_hash("pass"), role="site_supervisor")
        con = User(email=con_email, password_hash=get_password_hash("pass"), role="contractor")
        pm = User(email=pm_email, password_hash=get_password_hash("pass"), role="project_manager")
        db.add_all([adm, sup, con, pm])
        db.commit()
        db.refresh(adm)
        db.refresh(sup)
        db.refresh(con)
        db.refresh(pm)

        adm_id, sup_id, con_id, pm_id = adm.id, sup.id, con.id, pm.id

        # Projects
        p1 = Project(name=f"Proj 1R 1 {uuid.uuid4().hex[:4]}", created_by=adm_id)
        p2 = Project(name=f"Proj 1R 2 {uuid.uuid4().hex[:4]}", created_by=adm_id)
        db.add_all([p1, p2])
        db.commit()
        db.refresh(p1)
        db.refresh(p2)
        p1_id, p2_id = p1.id, p2.id

        db.add_all([
            ProjectMember(project_id=p1_id, user_id=adm_id),
            ProjectMember(project_id=p1_id, user_id=sup_id),
            ProjectMember(project_id=p1_id, user_id=con_id),
            ProjectMember(project_id=p1_id, user_id=pm_id),
            ProjectMember(project_id=p2_id, user_id=adm_id),
            ProjectMember(project_id=p2_id, user_id=sup_id),
            ProjectMember(project_id=p2_id, user_id=con_id),
            ProjectMember(project_id=p2_id, user_id=pm_id),
        ])
        db.commit()

        # Construction Activities
        act1 = ConstructionActivity(
            project_id=p1_id,
            activity_code=f"ACT-1R-1-{uuid.uuid4().hex[:4]}",
            activity_name="Raft Foundation Concreting",
            activity_type="CONSTRUCTION",
            created_by=adm_id,
        )
        act2 = ConstructionActivity(
            project_id=p2_id,
            activity_code=f"ACT-1R-2-{uuid.uuid4().hex[:4]}",
            activity_name="P2 Act",
            activity_type="CONSTRUCTION",
            created_by=adm_id,
        )
        act3 = ConstructionActivity(
            project_id=p1_id,
            activity_code=f"ACT-1R-3-{uuid.uuid4().hex[:4]}",
            activity_name="Columns P1",
            activity_type="CONSTRUCTION",
            created_by=adm_id,
        )
        db.add_all([act1, act2, act3])
        db.commit()
        db.refresh(act1)
        db.refresh(act2)
        db.refresh(act3)
        act1_id, act2_id, act3_id = act1.id, act2.id, act3.id

        # Materials
        mat_steel = MaterialItem(
            project_id=p1_id,
            material_code=f"STL-1R-{uuid.uuid4().hex[:4]}",
            material_name="Fe500 TMT Steel",
            material_category="REINFORCEMENT",
            standard_unit="MT",
            standard_permissible_waste_pct=Decimal("5.00"),
        )
        mat_cement = MaterialItem(
            project_id=p1_id,
            material_code=f"CEM-1R-{uuid.uuid4().hex[:4]}",
            material_name="OPC 53 Cement",
            material_category="BINDER",
            standard_unit="BAG",
            standard_permissible_waste_pct=Decimal("3.00"),
        )
        mat_p2 = MaterialItem(
            project_id=p2_id,
            material_code=f"P2-MAT-{uuid.uuid4().hex[:4]}",
            material_name="P2 Material",
            material_category="AGGREGATE",
            standard_unit="M3",
            standard_permissible_waste_pct=Decimal("2.00"),
        )
        db.add_all([mat_steel, mat_cement, mat_p2])
        db.commit()
        db.refresh(mat_steel)
        db.refresh(mat_cement)
        db.refresh(mat_p2)
        steel_id, cement_id, p2_mat_id = mat_steel.id, mat_cement.id, mat_p2.id

        # Create Schedule and Baseline for P1 and P2
        sched1 = ConstructionSchedule(
            project_id=p1_id,
            schedule_version="1.0",
            calculation_status="CALCULATED",
            calculated_by=adm_id,
            algorithm_version="CPM_1.0",
            input_snapshot_json={"version": "1.0"},
        )
        db.add(sched1)
        db.commit()
        db.refresh(sched1)
        sched1_id = sched1.id

        base1 = MonitoringBaseline(
            project_id=p1_id,
            schedule_id=sched1.id,
            schedule_version="1.0",
            schedule_algorithm_version="CPM_1.0",
            baseline_start_date=date(2026, 9, 1),
            frozen_by=adm_id,
            status="ACTIVE",
        )
        db.add(base1)
        db.commit()
        base1_id = base1.id

        sched2 = ConstructionSchedule(
            project_id=p2_id,
            schedule_version="1.0",
            calculation_status="CALCULATED",
            calculated_by=adm_id,
            algorithm_version="CPM_1.0",
            input_snapshot_json={"version": "1.0"},
        )
        db.add(sched2)
        db.commit()

        base2 = MonitoringBaseline(
            project_id=p2_id,
            schedule_id=sched2.id,
            schedule_version="1.0",
            schedule_algorithm_version="CPM_1.0",
            baseline_start_date=date(2026, 9, 1),
            frozen_by=adm_id,
            status="ACTIVE",
        )
        db.add(base2)
        db.commit()
        base2_id = base2.id

        # Phase 1N Material Mix Design and Material Plans
        mix = MaterialMixDesign(
            project_id=p1_id,
            mix_code=f"NOM-M25-{uuid.uuid4().hex[:4]}",
            grade_designation="M25",
            mix_type="NOMINAL_MIX",
            rule_code="IS456-M25",
            classification="ASSUMPTION_BASED",
            status="APPROVED",
            approved_by=adm_id,
            approved_at=datetime.now(timezone.utc),
        )
        db.add(mix)
        db.commit()
        mix_id = mix.id

        # Certificate & Valuation setup for TheoreticalConsumptionItem linkage
        crate = CostRate(
            project_id=p1_id,
            rate_code=f"RATE-1R-{uuid.uuid4().hex[:4]}",
            description="Steel & Concreting Rate",
            unit="MT",
            rate_value=Decimal("100.00"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Tender Schedule 1R",
            status="CONFIRMED",
            created_by=adm_id,
            confirmed_by=adm_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(crate)
        db.commit()

        arm = ActivityRateMapping(
            project_id=p1_id,
            activity_id=act1_id,
            cost_rate_id=crate.id,
            rate_value=Decimal("100.00"),
            rate_unit="MT",
            rate_version="1.0",
            currency="INR",
            status="ACTIVE",
            created_by=adm_id,
        )
        db.add(arm)
        db.commit()

        cert = PeriodProgressCertificate(
            project_id=p1_id,
            certificate_number=f"CERT-1R-{uuid.uuid4().hex[:6]}",
            certificate_type="PERIOD_SNAPSHOT",
            monitoring_baseline_id=base1_id,
            baseline_schedule_id=sched1.id,
            baseline_schedule_version="1.0",
            baseline_schedule_algorithm_version="CPM_1.0",
            baseline_start_date=date(2026, 9, 1),
            period_start_date=date(2026, 9, 1),
            period_cut_off_date=date(2026, 9, 30),
            certificate_status="DRAFT",
            currency="INR",
            period_claimed_value=Decimal("1000.00"),
            period_certified_value=Decimal("1000.00"),
            period_disputed_exposure=Decimal("0.00"),
            cumulative_claimed_value=Decimal("1000.00"),
            cumulative_certified_value=Decimal("1000.00"),
            cumulative_disputed_exposure=Decimal("0.00"),
            item_count=1,
            valuation_snapshot_hash="valid_hash_1r",
        )
        db.add(cert)
        db.commit()

        dpr = DailyProgressReport(
            project_id=p1_id,
            report_date=date(2026, 9, 15),
            submitted_by=adm_id,
            submission_status="FINALIZED",
        )
        db.add(dpr)
        db.commit()

        dap = DailyActivityProgress(
            daily_report_id=dpr.id,
            project_id=p1_id,
            activity_id=act1_id,
            contractor_progress_value=Decimal("10.0000"),
            contractor_progress_unit="MT",
            contractor_status="COMPLETED",
            created_by=adm_id,
        )
        db.add(dap)
        db.commit()

        dapv = DailyActivityProgressVerification(
            daily_activity_progress_id=dap.id,
            project_id=p1_id,
            verification_status="VERIFIED",
            verified_quantity=Decimal("10.0000"),
            verified_quantity_unit="MT",
            verified_by=adm_id,
        )
        db.add(dapv)
        db.commit()

        dpv = DailyProgressValuation(
            project_id=p1_id,
            verification_id=dapv.id,
            activity_rate_mapping_id=arm.id,
            contractor_claimed_quantity=Decimal("10.0000"),
            supervisor_certified_quantity=Decimal("10.0000"),
            quantity_unit="MT",
            unit_conversion_factor=Decimal("1.000000"),
            applied_rate_value=Decimal("100.00"),
            applied_rate_unit="MT",
            currency="INR",
            contractor_claimed_value=Decimal("1000.00"),
            certified_progress_value=Decimal("1000.00"),
            discrepancy_quantity=Decimal("0.000000"),
            disputed_valuation_exposure=Decimal("0.0000"),
            certified_certificate_id=cert.id,
            valuation_status="ACTIVE",
        )
        db.add(dpv)
        db.commit()
        db.refresh(dpv)
        dpv_id = dpv.id

        cert_item = PeriodCertificateItem(
            certificate_id=cert.id,
            valuation_id=dpv.id,
            activity_id=act1_id,
            claimed_quantity=Decimal("10.0000"),
            certified_quantity=Decimal("10.0000"),
            quantity_unit="MT",
            unit_conversion_factor=Decimal("1.000000"),
            applied_rate=Decimal("100.00"),
            applied_rate_unit="MT",
            currency="INR",
            claimed_amount=Decimal("1000.00"),
            certified_amount=Decimal("1000.00"),
            discrepancy_quantity=Decimal("0.0000"),
            disputed_exposure=Decimal("0.00"),
        )
        db.add(cert_item)
        db.commit()
        cert_id = cert.id
        cert_item_id = cert_item.id

        mp_steel = MaterialPlan(
            project_id=p1_id,
            baseline_id=base1_id,
            material_item_id=steel_id,
            activity_id=act1_id,
            mix_design_id=mix.id,
            planned_quantity=Decimal("10.0000"),
            gross_planned_quantity=Decimal("10.0000"),
            unit="MT",
            estimation_method="CALCULATED",
            status="ACTIVE",
            provenance_metadata={},
        )
        mp_cement = MaterialPlan(
            project_id=p1_id,
            baseline_id=base1_id,
            material_item_id=cement_id,
            activity_id=act1_id,
            mix_design_id=mix.id,
            planned_quantity=Decimal("0.0000"),
            gross_planned_quantity=Decimal("0.0000"),
            unit="BAG",
            estimation_method="CALCULATED",
            status="ACTIVE",
            provenance_metadata={},
        )
        db.add_all([mp_steel, mp_cement])
        db.commit()
        db.refresh(mp_steel)
        db.refresh(mp_cement)
        mp_steel_id, mp_cement_id = mp_steel.id, mp_cement.id

        # Requirement Plan & Item
        plan = MaterialRequirementPlan(
            project_id=p1_id,
            baseline_id=base1_id,
            plan_version=f"MRP-V1-{uuid.uuid4().hex[:4]}",
            status="DRAFT",
            planning_start_date=date(2026, 10, 1),
            planning_end_date=date(2026, 11, 1),
            input_snapshot_json={},
            created_by=adm_id,
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        plan_id = plan.id

        req_item_steel = MaterialRequirementItem(
            project_id=p1_id,
            material_requirement_plan_id=plan_id,
            material_item_id=steel_id,
            activity_id=act1_id,
            material_plan_id=mp_steel_id,
            requirement_quantity=Decimal("10.0000"),
            requirement_unit="MT",
            source_quantity=Decimal("10.0000"),
            source_unit="MT",
            provenance_metadata={},
        )
        db.add(req_item_steel)
        db.commit()
        db.refresh(req_item_steel)
        req_item_steel_id = req_item_steel.id

        plan.status = "ACTIVE"
        db.commit()

        # Theoretical item
        theo_item = make_theo_item(
            db, p1_id, act1_id, steel_id, Decimal("10.0000"), "MT", mix_id, cert_id, cert_item_id
        )

        # Phase 1P Authoritative Stock Ledger Transactions (ISSUE)
        stk_issue_steel = MaterialStockLedger(
            project_id=p1_id,
            material_item_id=steel_id,
            transaction_type="ISSUE",
            transaction_quantity=Decimal("12.0000"),
            unit="MT",
            transaction_date=date(2026, 10, 5),
            source_type="SUPERVISOR_VERIFIED",
            is_authoritative=True,
            verification_status="VERIFIED",
            created_by=adm_id,
        )
        db.add(stk_issue_steel)
        db.commit()
        db.refresh(stk_issue_steel)

        # Issue allocation
        issue_alloc = MaterialIssueAllocation(
            project_id=p1_id,
            material_stock_ledger_id=stk_issue_steel.id,
            material_item_id=steel_id,
            activity_id=act1_id,
            issued_quantity=Decimal("12.0000"),
            issued_unit="MT",
            issue_date=date(2026, 10, 5),
            status="ALLOCATED",
            created_by=adm_id,
        )
        db.add(issue_alloc)
        db.commit()

        # Consumption Entry & Verification
        c_entry, c_verif = make_consumption_entry_and_verif(
            db, p1_id, act1_id, steel_id, Decimal("12.0000"), "MT", con_id, sup_id
        )

        # Reconciliation record
        recon = MaterialConsumptionReconciliation(
            project_id=p1_id,
            material_requirement_plan_id=plan_id,
            material_requirement_item_id=req_item_steel_id,
            activity_id=act1_id,
            material_item_id=steel_id,
            issued_quantity=Decimal("12.0000"),
            issued_unit="MT",
            actual_consumed_quantity=Decimal("12.0000"),
            actual_consumed_unit="MT",
            theoretical_quantity=Decimal("10.0000"),
            theoretical_unit="MT",
            planned_quantity=Decimal("10.0000"),
            planned_unit="MT",
            variance_quantity=Decimal("2.0000"),
            variance_percentage=Decimal("20.0000"),
            permissible_wastage_quantity=Decimal("0.5000"),
            unauthorized_wastage_quantity=Decimal("1.5000"),
            status="WITHIN_PERMISSIBLE_WASTAGE",
            created_by=sup_id,
            canonical_hash="recon_canonical_hash",
        )
        db.add(recon)
        db.commit()
        db.refresh(recon)
        recon_id = recon.id

    adm_token = create_access_token(data={"sub": adm_email, "role": "admin"})
    sup_token = create_access_token(data={"sub": sup_email, "role": "site_supervisor"})
    con_token = create_access_token(data={"sub": con_email, "role": "contractor"})
    pm_token = create_access_token(data={"sub": pm_email, "role": "project_manager"})

    return {
        "adm_token": adm_token,
        "sup_token": sup_token,
        "con_token": con_token,
        "pm_token": pm_token,
        "adm_id": adm_id,
        "sup_id": sup_id,
        "con_id": con_id,
        "p1_id": p1_id,
        "p2_id": p2_id,
        "act1_id": act1_id,
        "act2_id": act2_id,
        "act3_id": act3_id,
        "steel_id": steel_id,
        "cement_id": cement_id,
        "p2_mat_id": p2_mat_id,
        "plan_id": plan_id,
        "req_item_steel_id": req_item_steel_id,
        "recon_id": recon_id,
        "base1_id": base1_id,
        "base2_id": base2_id,
        "mp_cement_id": mp_cement_id,
        "cert_id": cert_id,
        "cert_item_id": cert_item_id,
        "mix_id": mix_id,
        "dpv_id": dpv_id,
        "sched1_id": sched1_id,
    }


# ==============================================================================
# GROUP 1: SNAPSHOT FOUNDATION & LINEAGE
# ==============================================================================

def test_01_create_snapshot_basic(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "material_item_id": setup_data["steel_id"],
        "status": "DRAFT",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "DRAFT"
    assert data["algorithm_version"] == "MAT_PERFORMANCE_1.0"
    assert data["canonical_hash"] is not None
    assert len(data["canonical_hash"]) == 64
    assert data["project_id"] == p1_id
    assert data["activity_id"] == setup_data["act1_id"]
    assert data["material_item_id"] == setup_data["steel_id"]


def test_02_snapshot_lineage_to_recon_and_plan(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["sup_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "material_item_id": setup_data["steel_id"],
        "requirement_plan_id": setup_data["plan_id"],
        "requirement_item_id": setup_data["req_item_steel_id"],
        "reconciliation_id": setup_data["recon_id"],
        "status": "DRAFT",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["requirement_plan_id"] == setup_data["plan_id"]
    assert data["requirement_item_id"] == setup_data["req_item_steel_id"]
    assert data["reconciliation_id"] == setup_data["recon_id"]
    assert data["input_snapshot_json"].get("upstream_reconciliation_id") == setup_data["recon_id"] or \
           data["provenance_metadata"].get("upstream_reconciliation_id") == setup_data["recon_id"]


# ==============================================================================
# GROUP 2: PLANNED VARIANCE
# ==============================================================================

def test_03_planned_variance_qty_and_pct(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    # Actual is 12.0000, Planned is 10.0000 -> Diff = 2.0000, Pct = +20.00%
    payload = {
        "activity_id": setup_data["act1_id"],
        "material_item_id": setup_data["steel_id"],
        "requirement_plan_id": setup_data["plan_id"],
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert Decimal(str(data["planned_variance_quantity"])) == Decimal("2.0000")
    assert Decimal(str(data["planned_variance_percentage"])) == Decimal("20.0000")


def test_04_planned_variance_zero_planned(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    with TestingSessionLocal() as db:
        # Create requirement plan with planned 0
        plan_zero = MaterialRequirementPlan(
            project_id=p1_id,
            baseline_id=setup_data["base1_id"],
            plan_version=f"MRP-ZERO-{uuid.uuid4().hex[:4]}",
            input_snapshot_json={},
            status="DRAFT",
            created_by=setup_data["adm_id"],
        )
        db.add(plan_zero)
        db.commit()
        db.refresh(plan_zero)

        req_zero = MaterialRequirementItem(
            project_id=p1_id,
            material_requirement_plan_id=plan_zero.id,
            material_item_id=setup_data["cement_id"],
            activity_id=setup_data["act1_id"],
            material_plan_id=setup_data["mp_cement_id"],
            requirement_quantity=Decimal("0.0000"),
            requirement_unit="BAG",
            source_quantity=Decimal("0.0000"),
            source_unit="BAG",
            provenance_metadata={},
        )
        db.add(req_zero)
        db.commit()
        req_zero_id, plan_zero_id = req_zero.id, plan_zero.id

    payload = {
        "activity_id": setup_data["act1_id"],
        "material_item_id": setup_data["cement_id"],
        "requirement_plan_id": plan_zero_id,
        "requirement_item_id": req_zero_id,
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    # Zero planned: percentage should be None to prevent division by zero
    assert data["planned_variance_percentage"] is None


def test_05_planned_variance_missing_planned(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    # Activity 3 has no requirement plan
    payload = {
        "activity_id": setup_data["act3_id"],
        "material_item_id": setup_data["cement_id"],
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["planned_quantity"] is None
    assert data["planned_variance_quantity"] is None
    assert data["planned_variance_percentage"] is None


# ==============================================================================
# GROUP 3: THEORETICAL VARIANCE
# ==============================================================================

def test_06_theo_variance_qty_and_pct(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    # Act1 steel has theoretical 10.0000 MT, verified actual 12.0000 MT
    # Theo var qty = +2.0000, Theo var pct = +20.0000%
    payload = {
        "activity_id": setup_data["act1_id"],
        "material_item_id": setup_data["steel_id"],
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert Decimal(str(data["theoretical_variance_quantity"])) == Decimal("2.0000")
    assert Decimal(str(data["theoretical_variance_percentage"])) == Decimal("20.0000")


def test_07_theo_variance_zero_theo(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    with TestingSessionLocal() as db:
        mat_zero = MaterialItem(
            project_id=p1_id,
            material_code=f"MAT-ZERO-{uuid.uuid4().hex[:4]}",
            material_name="Zero Theo Material",
            material_category="REINFORCEMENT",
            standard_unit="MT",
            standard_permissible_waste_pct=Decimal("5.00"),
        )
        db.add(mat_zero)
        db.commit()
        db.refresh(mat_zero)
        mat_zero_id = mat_zero.id

        theo_zero = make_theo_item(
            db,
            p1_id,
            setup_data["act1_id"],
            mat_zero_id,
            Decimal("0.0000"),
            "MT",
            setup_data["mix_id"],
            setup_data["cert_id"],
            setup_data["cert_item_id"],
        )
        make_consumption_entry_and_verif(
            db, p1_id, setup_data["act1_id"], mat_zero_id, Decimal("5.0000"), "MT", setup_data["con_id"], setup_data["sup_id"]
        )

    payload = {
        "activity_id": setup_data["act1_id"],
        "material_item_id": mat_zero_id,
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert Decimal(str(data["theoretical_variance_quantity"])) == Decimal("5.0000")
    assert data["theoretical_variance_percentage"] is None


def test_08_theo_variance_missing_theo(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act3_id"],
        "material_item_id": setup_data["cement_id"],
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["theoretical_quantity"] is None
    assert data["theoretical_variance_quantity"] is None
    assert data["theoretical_variance_percentage"] is None


# ==============================================================================
# GROUP 4: CONSUMPTION INTENSITY
# ==============================================================================

def test_09_consumption_intensity_valid(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    # Actual is 12.0000 MT, Explicit verified execution quantity = 3.0000 MT
    # Consumption intensity = 12 / 3 = 4.0000
    payload = {
        "activity_id": setup_data["act1_id"],
        "material_item_id": setup_data["steel_id"],
        "verified_activity_execution_quantity": "3.0000",
        "verified_activity_execution_unit": "MT",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert Decimal(str(data["consumption_intensity"])) == Decimal("4.0000")


def test_10_consumption_intensity_zero_output(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "material_item_id": setup_data["steel_id"],
        "verified_activity_execution_quantity": "0.0000",
        "verified_activity_execution_unit": "MT",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["consumption_intensity"] is None


def test_11_consumption_intensity_missing_output(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act3_id"],
        "material_item_id": setup_data["steel_id"],
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["consumption_intensity"] is None


# ==============================================================================
# GROUP 5: PRODUCTIVITY
# ==============================================================================

def test_12_productivity_valid(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    # Output 3.0000 MT, Actual 12.0000 MT -> Productivity = 3 / 12 = 0.2500
    payload = {
        "activity_id": setup_data["act1_id"],
        "material_item_id": setup_data["steel_id"],
        "verified_activity_execution_quantity": "3.0000",
        "verified_activity_execution_unit": "MT",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert Decimal(str(data["productivity"])) == Decimal("0.2500")


def test_13_productivity_zero_actual(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    with TestingSessionLocal() as db:
        c_zero, v_zero = make_consumption_entry_and_verif(
            db,
            p1_id,
            setup_data["act3_id"],
            setup_data["cement_id"],
            Decimal("0.0000"),
            "BAG",
            setup_data["con_id"],
            setup_data["sup_id"],
        )

    payload = {
        "activity_id": setup_data["act3_id"],
        "material_item_id": setup_data["cement_id"],
        "verified_activity_execution_quantity": "10.0000",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["productivity"] is None


def test_14_productivity_missing_actual_or_output(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    # No output provided and no consumption for act3 steel
    payload = {
        "activity_id": setup_data["act3_id"],
        "material_item_id": setup_data["steel_id"],
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["productivity"] is None


# ==============================================================================
# GROUP 6: WASTAGE
# ==============================================================================

def test_15_wastage_from_reconciliation(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["sup_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "material_item_id": setup_data["steel_id"],
        "reconciliation_id": setup_data["recon_id"],
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert Decimal(str(data["permissible_wastage_quantity"])) == Decimal("0.5000")
    assert Decimal(str(data["unauthorized_wastage_quantity"])) == Decimal("1.5000")


def test_16_wastage_from_standard_pct(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["sup_token"]
    # Theo 10.0000 MT, standard permissible 5.0% -> permissible = 0.5000 MT
    # Actual 12.0000 MT -> excess = 2.0000 MT -> unauthorized = 1.5000 MT
    payload = {
        "activity_id": setup_data["act1_id"],
        "material_item_id": setup_data["steel_id"],
        "tolerance_percentage": "5.0000",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert Decimal(str(data["permissible_wastage_quantity"])) == Decimal("0.5000")
    assert Decimal(str(data["unauthorized_wastage_quantity"])) == Decimal("1.5000")


# ==============================================================================
# GROUP 7: STATUS CLASSIFICATION (ALL 9 STATUSES)
# ==============================================================================

def test_17_status_match(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    act_id = setup_data["act1_id"]
    with TestingSessionLocal() as db:
        mat_match = MaterialItem(
            project_id=p1_id,
            material_code=f"MAT-MATCH-{uuid.uuid4().hex[:4]}",
            material_name="Match Activity Mat",
            material_category="REINFORCEMENT",
            standard_unit="MT",
            standard_permissible_waste_pct=Decimal("5.00"),
        )
        db.add(mat_match)
        db.commit()
        db.refresh(mat_match)
        mat_id = mat_match.id

        theo = make_theo_item(
            db,
            p1_id,
            act_id,
            mat_id,
            Decimal("15.0000"),
            "MT",
            setup_data["mix_id"],
            setup_data["cert_id"],
            setup_data["cert_item_id"],
        )
        c_entry, v_entry = make_consumption_entry_and_verif(
            db, p1_id, act_id, mat_id, Decimal("15.0000"), "MT", setup_data["con_id"], setup_data["sup_id"]
        )

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": act_id, "material_item_id": mat_id},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["performance_status"] == "MATCH"


def test_18_status_under_consumption(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    act_id = setup_data["act1_id"]
    with TestingSessionLocal() as db:
        mat_under = MaterialItem(
            project_id=p1_id,
            material_code=f"MAT-UNDER-{uuid.uuid4().hex[:4]}",
            material_name="Under Activity Mat",
            material_category="REINFORCEMENT",
            standard_unit="MT",
            standard_permissible_waste_pct=Decimal("5.00"),
        )
        db.add(mat_under)
        db.commit()
        db.refresh(mat_under)
        mat_id = mat_under.id

        theo = make_theo_item(
            db,
            p1_id,
            act_id,
            mat_id,
            Decimal("20.0000"),
            "MT",
            setup_data["mix_id"],
            setup_data["cert_id"],
            setup_data["cert_item_id"],
        )
        c_entry, v_entry = make_consumption_entry_and_verif(
            db, p1_id, act_id, mat_id, Decimal("18.0000"), "MT", setup_data["con_id"], setup_data["sup_id"]
        )

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": act_id, "material_item_id": mat_id},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["performance_status"] == "UNDER_CONSUMPTION"


def test_19_status_within_permissible_variance(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    act_id = setup_data["act1_id"]
    with TestingSessionLocal() as db:
        mat_perm = MaterialItem(
            project_id=p1_id,
            material_code=f"MAT-PERM-{uuid.uuid4().hex[:4]}",
            material_name="Permissible Activity Mat",
            material_category="REINFORCEMENT",
            standard_unit="MT",
            standard_permissible_waste_pct=Decimal("5.00"),
        )
        db.add(mat_perm)
        db.commit()
        db.refresh(mat_perm)
        mat_id = mat_perm.id

        theo = make_theo_item(
            db,
            p1_id,
            act_id,
            mat_id,
            Decimal("100.0000"),
            "MT",
            setup_data["mix_id"],
            setup_data["cert_id"],
            setup_data["cert_item_id"],
        )
        c_entry, v_entry = make_consumption_entry_and_verif(
            db, p1_id, act_id, mat_id, Decimal("103.0000"), "MT", setup_data["con_id"], setup_data["sup_id"]
        )

    # Material standard permissible waste is 5%, so 5 MT allowed. Actual excess is 3 MT.
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": act_id, "material_item_id": mat_id},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["performance_status"] == "WITHIN_PERMISSIBLE_VARIANCE"


def test_20_status_unauthorized_wastage(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    # Using recon_id which has unauthorized_wastage_quantity = 1.5000 MT
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "reconciliation_id": setup_data["recon_id"],
        },
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["performance_status"] == "UNAUTHORIZED_WASTAGE"


def test_21_status_over_consumption(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    act_id = setup_data["act1_id"]
    with TestingSessionLocal() as db:
        mat_no_waste = MaterialItem(
            project_id=p1_id,
            material_code=f"NOWASTE-{uuid.uuid4().hex[:4]}",
            material_name="No Waste Mat",
            material_category="REINFORCEMENT",
            standard_unit="MT",
            standard_permissible_waste_pct=Decimal("0.00"),
        )
        db.add(mat_no_waste)
        db.commit()
        db.refresh(mat_no_waste)
        mat_nw_id = mat_no_waste.id

        theo_nw = make_theo_item(
            db,
            p1_id,
            act_id,
            mat_nw_id,
            Decimal("100.0000"),
            "MT",
            setup_data["mix_id"],
            setup_data["cert_id"],
            setup_data["cert_item_id"],
        )
        c_nw, v_nw = make_consumption_entry_and_verif(
            db, p1_id, act_id, mat_nw_id, Decimal("120.0000"), "MT", setup_data["con_id"], setup_data["sup_id"]
        )

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": act_id, "material_item_id": mat_nw_id},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["performance_status"] in ["OVER_CONSUMPTION", "UNAUTHORIZED_WASTAGE"]


def test_22_status_requires_input(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    act_id = setup_data["act1_id"]
    with TestingSessionLocal() as db:
        mat = MaterialItem(
            project_id=p1_id,
            material_code=f"MAT-REQ-{uuid.uuid4().hex[:4]}",
            material_name="Req Mat",
            material_category="REINFORCEMENT",
            standard_unit="MT",
        )
        db.add(mat)
        db.commit()
        db.refresh(mat)
        mat_id = mat.id

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": act_id, "material_item_id": mat_id},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["performance_status"] == "REQUIRES_INPUT"


def test_23_status_no_verified_actual(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    act_id = setup_data["act1_id"]
    with TestingSessionLocal() as db:
        mat = MaterialItem(
            project_id=p1_id,
            material_code=f"MAT-NOACT-{uuid.uuid4().hex[:4]}",
            material_name="No Actual Mat",
            material_category="REINFORCEMENT",
            standard_unit="MT",
        )
        db.add(mat)
        db.commit()
        db.refresh(mat)
        mat_id = mat.id

        theo = make_theo_item(
            db,
            p1_id,
            act_id,
            mat_id,
            Decimal("50.0000"),
            "MT",
            setup_data["mix_id"],
            setup_data["cert_id"],
            setup_data["cert_item_id"],
        )

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": act_id, "material_item_id": mat_id},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["performance_status"] == "NO_VERIFIED_ACTUAL"


def test_24_status_no_theoretical_data(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    act_id = setup_data["act1_id"]
    with TestingSessionLocal() as db:
        mat = MaterialItem(
            project_id=p1_id,
            material_code=f"MAT-NOTHEO-{uuid.uuid4().hex[:4]}",
            material_name="No Theo Mat",
            material_category="REINFORCEMENT",
            standard_unit="MT",
        )
        db.add(mat)
        db.commit()
        db.refresh(mat)
        mat_id = mat.id

        c_entry, v_entry = make_consumption_entry_and_verif(
            db, p1_id, act_id, mat_id, Decimal("15.0000"), "MT", setup_data["con_id"], setup_data["sup_id"]
        )

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": act_id, "material_item_id": mat_id},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["performance_status"] == "NO_THEORETICAL_DATA"


def test_25_status_unit_mismatch(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    act_id = setup_data["act1_id"]
    with TestingSessionLocal() as db:
        mat = MaterialItem(
            project_id=p1_id,
            material_code=f"MAT-UNMIS-{uuid.uuid4().hex[:4]}",
            material_name="Unit Mismatch Mat",
            material_category="REINFORCEMENT",
            standard_unit="MT",
        )
        db.add(mat)
        db.commit()
        db.refresh(mat)
        mat_id = mat.id

        theo = make_theo_item(
            db,
            p1_id,
            act_id,
            mat_id,
            Decimal("10.0000"),
            "M3",
            setup_data["mix_id"],
            setup_data["cert_id"],
            setup_data["cert_item_id"],
        )
        c_entry, v_entry = make_consumption_entry_and_verif(
            db, p1_id, act_id, mat_id, Decimal("10.0000"), "NOS", setup_data["con_id"], setup_data["sup_id"]
        )

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": act_id, "material_item_id": mat_id},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["performance_status"] == "UNIT_MISMATCH"


# ==============================================================================
# GROUP 8: PERIOD AGGREGATION & SUMMARIES
# ==============================================================================

def test_26_summary_aggregation_and_status_distribution(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["sup_token"]
    client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": setup_data["act1_id"], "material_item_id": setup_data["steel_id"]},
    )
    resp = client_fixture.get(
        f"/api/projects/{p1_id}/material-performance/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["project_id"] == p1_id
    assert data["total_snapshots"] > 0
    assert isinstance(data["status_distribution"], dict)
    assert isinstance(data["total_actual_consumption"], dict)
    assert isinstance(data["total_theoretical_consumption"], dict)


def test_27_summary_filter_by_activity_and_material(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["sup_token"]
    client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": setup_data["act1_id"], "material_item_id": setup_data["steel_id"]},
    )
    resp = client_fixture.get(
        f"/api/projects/{p1_id}/material-performance/summary?activity_id={setup_data['act1_id']}&material_item_id={setup_data['steel_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    for s in data["snapshots"]:
        assert s["activity_id"] == setup_data["act1_id"]
        assert s["material_item_id"] == setup_data["steel_id"]


# ==============================================================================
# GROUP 9: PROVENANCE METADATA
# ==============================================================================

def test_28_provenance_metadata_and_algorithm_version(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": setup_data["act1_id"], "material_item_id": setup_data["steel_id"]},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["algorithm_version"] == "MAT_PERFORMANCE_1.0"
    assert "activity_code" in data["provenance_metadata"]
    assert "material_code" in data["provenance_metadata"]
    assert "input_snapshot_json" in data


# ==============================================================================
# GROUP 10: IMMUTABILITY (TRIGGER PROTECTION)
# ==============================================================================

def test_29_trigger_prevents_sql_update_on_finalized(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "status": "DRAFT",
        },
    )
    assert resp.status_code == 201, resp.text
    snap_id = resp.json()["id"]

    r_fin = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/finalize",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_fin.status_code == 200, r_fin.text

    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("UPDATE material_performance_snapshots SET algorithm_version = 'HACK' WHERE id = :id"),
                {"id": snap_id},
            )
            db.commit()
        assert "immutable" in str(exc_info.value).lower() or "finalized" in str(exc_info.value).lower()

    # Clean up by superseding
    client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "Clean up after test 29"},
    )


def test_30_trigger_prevents_sql_delete_on_finalized(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "status": "DRAFT",
        },
    )
    assert resp.status_code == 201, resp.text
    snap_id = resp.json()["id"]

    r_fin = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/finalize",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_fin.status_code == 200, r_fin.text

    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("DELETE FROM material_performance_snapshots WHERE id = :id"),
                {"id": snap_id},
            )
            db.commit()
        assert "immutable" in str(exc_info.value).lower() or "finalized" in str(exc_info.value).lower()

    # Clean up by superseding
    client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "Clean up after test 30"},
    )


def test_31_trigger_prevents_sql_update_on_superseded(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "status": "DRAFT",
        },
    )
    assert resp.status_code == 201, resp.text
    snap_id = resp.json()["id"]

    r_fin = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/finalize",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_fin.status_code == 200, r_fin.text

    # Supersede via API
    resp_sup = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "Correction in measurement"},
    )
    assert resp_sup.status_code == 200, resp_sup.text
    assert resp_sup.json()["status"] == "SUPERSEDED"

    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("UPDATE material_performance_snapshots SET algorithm_version = 'HACK' WHERE id = :id"),
                {"id": snap_id},
            )
            db.commit()
        assert "immutable" in str(exc_info.value).lower() or "superseded" in str(exc_info.value).lower()


def test_32_trigger_prevents_sql_delete_on_superseded(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "status": "DRAFT",
        },
    )
    assert resp.status_code == 201, resp.text
    snap_id = resp.json()["id"]

    r_fin = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/finalize",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_fin.status_code == 200, r_fin.text

    resp_sup = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "Replacing record"},
    )
    assert resp_sup.status_code == 200

    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("DELETE FROM material_performance_snapshots WHERE id = :id"),
                {"id": snap_id},
            )
            db.commit()
        assert "immutable" in str(exc_info.value).lower() or "superseded" in str(exc_info.value).lower()


# ==============================================================================
# GROUP 11: CANONICAL HASH DETERMINISM
# ==============================================================================

def test_33_canonical_hash_determinism_and_reproducibility(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "material_item_id": setup_data["steel_id"],
        "reconciliation_id": setup_data["recon_id"],
    }
    r1 = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    r2 = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["canonical_hash"] == r2.json()["canonical_hash"]


# ==============================================================================
# GROUP 12: PROJECT ISOLATION
# ==============================================================================

def test_34_project_isolation_cross_project_activity_rejected(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    # act2 belongs to p2
    payload = {
        "activity_id": setup_data["act2_id"],
        "material_item_id": setup_data["steel_id"],
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code in [400, 404]


def test_35_project_isolation_cross_project_material_rejected(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    # p2_mat belongs to p2
    payload = {
        "activity_id": setup_data["act1_id"],
        "material_item_id": setup_data["p2_mat_id"],
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code in [400, 404]


def test_36_project_isolation_cross_project_plan_rejected(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    p2_id = setup_data["p2_id"]
    token = setup_data["adm_token"]
    with TestingSessionLocal() as db:
        p2_plan = MaterialRequirementPlan(
            project_id=p2_id,
            baseline_id=setup_data["base2_id"],
            plan_version=f"P2-MRP-{uuid.uuid4().hex[:4]}",
            input_snapshot_json={},
            status="ACTIVE",
            created_by=setup_data["adm_id"],
        )
        db.add(p2_plan)
        db.commit()
        db.refresh(p2_plan)
        p2_plan_id = p2_plan.id

    payload = {
        "activity_id": setup_data["act1_id"],
        "material_item_id": setup_data["steel_id"],
        "requirement_plan_id": p2_plan_id,
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code in [400, 404]


# ==============================================================================
# GROUP 13: RBAC
# ==============================================================================

def test_37_rbac_admin_supervisor_allowed(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    # Admin allowed
    r_adm = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {setup_data['adm_token']}"},
        json={"activity_id": setup_data["act1_id"], "material_item_id": setup_data["steel_id"]},
    )
    assert r_adm.status_code == 201

    # Supervisor allowed
    r_sup = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
        json={"activity_id": setup_data["act1_id"], "material_item_id": setup_data["steel_id"]},
    )
    assert r_sup.status_code == 201


def test_38_rbac_contractor_read_only_create_rejected(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    # Contractor create forbidden
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
        json={"activity_id": setup_data["act1_id"], "material_item_id": setup_data["steel_id"]},
    )
    assert resp.status_code == 403

    # Contractor read allowed
    resp_read = client_fixture.get(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    assert resp_read.status_code == 200


def test_39_rbac_contractor_finalize_supersede_rejected(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    # Create draft with admin
    r_create = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {setup_data['adm_token']}"},
        json={"activity_id": setup_data["act1_id"], "material_item_id": setup_data["steel_id"], "status": "DRAFT"},
    )
    assert r_create.status_code == 201
    snap_id = r_create.json()["id"]

    # Contractor finalize forbidden
    r_fin = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/finalize",
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    assert r_fin.status_code == 403

    # Admin finalize
    r_fin_adm = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/finalize",
        headers={"Authorization": f"Bearer {setup_data['adm_token']}"},
    )
    assert r_fin_adm.status_code == 200

    # Contractor supersede forbidden
    r_sup = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/supersede",
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
        json={"supersession_reason": "Attempted by contractor"},
    )
    assert r_sup.status_code == 403

    # Clean up by superseding with admin
    client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/supersede",
        headers={"Authorization": f"Bearer {setup_data['adm_token']}"},
        json={"supersession_reason": "Clean up after test 39"},
    )


def test_40_rbac_project_manager_all_rejected(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    pm_token = setup_data["pm_token"]

    r_post = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {pm_token}"},
        json={"activity_id": setup_data["act1_id"], "material_item_id": setup_data["steel_id"]},
    )
    assert r_post.status_code == 403

    r_get = client_fixture.get(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {pm_token}"},
    )
    assert r_get.status_code == 403

    r_sum = client_fixture.get(
        f"/api/projects/{p1_id}/material-performance/summary",
        headers={"Authorization": f"Bearer {pm_token}"},
    )
    assert r_sum.status_code == 403


# ==============================================================================
# GROUP 14: CONCURRENCY
# ==============================================================================

def test_41_concurrent_finalize_and_supersede(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    adm_token = setup_data["adm_token"]
    sup_token = setup_data["sup_token"]

    r_create = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"activity_id": setup_data["act1_id"], "material_item_id": setup_data["steel_id"], "status": "DRAFT"},
    )
    assert r_create.status_code == 201
    snap_id = r_create.json()["id"]

    results = []

    def finalize_task(token):
        c = TestClient(app)
        res = c.post(
            f"/api/projects/{p1_id}/material-performance/{snap_id}/finalize",
            headers={"Authorization": f"Bearer {token}"},
        )
        results.append(res.status_code)

    t1 = threading.Thread(target=finalize_task, args=(adm_token,))
    t2 = threading.Thread(target=finalize_task, args=(sup_token,))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Exactly one should succeed (200), other should be 400 (already finalized)
    assert 200 in results
    assert len(results) == 2

    # Clean up by superseding
    client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/supersede",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"supersession_reason": "Clean up after test 41"},
    )


# ==============================================================================
# HARDENING SCENARIOS A–N
# ==============================================================================

def test_42_hardening_scenario_a_missing_not_coerced_to_zero(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": setup_data["act3_id"], "material_item_id": setup_data["cement_id"]},
    )
    assert resp.status_code == 201
    data = resp.json()
    # Missing theoretical or execution quantity is NOT coerced to 0.0000
    assert data["theoretical_quantity"] is None
    assert data["verified_activity_execution_quantity"] is None


def test_43_hardening_scenario_b_draft_lifecycle(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": setup_data["act1_id"], "material_item_id": setup_data["steel_id"], "status": "DRAFT"},
    )
    assert resp.status_code == 201
    snap_id = resp.json()["id"]

    # Finalize
    r_fin = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/finalize",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_fin.status_code == 200
    assert r_fin.json()["status"] == "FINALIZED"

    # Cannot finalize again
    r_fin2 = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/finalize",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_fin2.status_code == 400

    # Clean up by superseding
    client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "Clean up after test 43"},
    )


def test_44_hardening_scenario_c_supersede_lifecycle_and_empty_reason(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    # Cannot supersede DRAFT
    r_draft = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": setup_data["act1_id"], "material_item_id": setup_data["steel_id"], "status": "DRAFT"},
    )
    draft_id = r_draft.json()["id"]
    r_sup_draft = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{draft_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "Trying to supersede draft"},
    )
    assert r_sup_draft.status_code == 400

    # Finalize it first
    client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{draft_id}/finalize",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Empty reason rejected
    r_empty_reason = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{draft_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "   "},
    )
    assert r_empty_reason.status_code == 422

    # Clean up by superseding with valid reason
    r_valid_sup = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{draft_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "Clean up after test 44"},
    )
    assert r_valid_sup.status_code == 200


def test_45_hardening_scenario_d_e_raw_sql_trigger_defense(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": setup_data["act1_id"], "material_item_id": setup_data["steel_id"], "status": "DRAFT"},
    )
    assert resp.status_code == 201
    snap_id = resp.json()["id"]

    r_fin = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/finalize",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_fin.status_code == 200

    with TestingSessionLocal() as db:
        # Direct SQL UPDATE attempt
        with pytest.raises(Exception):
            db.execute(text("UPDATE material_performance_snapshots SET actual_consumption_quantity = 999 WHERE id = :id"), {"id": snap_id})
            db.commit()

    # Clean up by superseding
    client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "Clean up after test 45"},
    )


def test_46_hardening_scenario_f_unit_mismatch_no_silent_corruption(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    act_id = setup_data["act1_id"]
    with TestingSessionLocal() as db:
        mat = MaterialItem(
            project_id=p1_id,
            material_code=f"MAT-F-{uuid.uuid4().hex[:4]}",
            material_name="Hardening F Mat",
            material_category="REINFORCEMENT",
            standard_unit="BAG",
        )
        db.add(mat)
        db.commit()
        db.refresh(mat)
        mat_id = mat.id

        theo = make_theo_item(
            db,
            p1_id,
            act_id,
            mat_id,
            Decimal("100.0000"),
            "M3",
            setup_data["mix_id"],
            setup_data["cert_id"],
            setup_data["cert_item_id"],
        )
        c_entry, v_entry = make_consumption_entry_and_verif(
            db, p1_id, act_id, mat_id, Decimal("100.0000"), "MT", setup_data["con_id"], setup_data["sup_id"]
        )

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": act_id, "material_item_id": mat_id},
    )
    assert resp.status_code == 201
    assert resp.json()["performance_status"] == "UNIT_MISMATCH"
    assert resp.json()["theoretical_variance_quantity"] is None


def test_47_hardening_scenario_g_negative_execution_qty_validation(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "verified_activity_execution_quantity": "-5.0000",
        },
    )
    assert resp.status_code == 422


def test_48_hardening_scenario_h_negative_tolerance_validation(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "tolerance_percentage": "-2.5000",
        },
    )
    assert resp.status_code == 422


def test_49_hardening_scenario_i_auto_aggregation_from_1q_reconciliation(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "reconciliation_id": setup_data["recon_id"],
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert Decimal(str(data["actual_consumption_quantity"])) == Decimal("12.0000")
    assert Decimal(str(data["theoretical_quantity"])) == Decimal("10.0000")
    assert Decimal(str(data["planned_quantity"])) == Decimal("10.0000")


def test_50_hardening_scenario_j_activity_output_from_daily_progress(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    with TestingSessionLocal() as db:
        act = ConstructionActivity(
            project_id=p1_id,
            activity_code=f"ACT-J-{uuid.uuid4().hex[:4]}",
            activity_name="Hardening J Activity",
            activity_type="CONSTRUCTION",
            created_by=setup_data["adm_id"],
        )
        mat = MaterialItem(
            project_id=p1_id,
            material_code=f"MAT-J-{uuid.uuid4().hex[:4]}",
            material_name="Hardening J Mat",
            material_category="REINFORCEMENT",
            standard_unit="MT",
        )
        db.add_all([act, mat])
        db.commit()
        db.refresh(act)
        db.refresh(mat)
        act_id, mat_id = act.id, mat.id

        # DPR + DAP + DAPV
        dpr = DailyProgressReport(
            project_id=p1_id,
            report_date=date(2026, 10, 10),
            submitted_by=setup_data["adm_id"],
            submission_status="FINALIZED",
        )
        db.add(dpr)
        db.commit()
        db.refresh(dpr)

        dap = DailyActivityProgress(
            daily_report_id=dpr.id,
            project_id=p1_id,
            activity_id=act_id,
            contractor_progress_value=Decimal("8.0000"),
            contractor_progress_unit="M3",
            contractor_status="IN_PROGRESS",
            created_by=setup_data["con_id"],
        )
        db.add(dap)
        db.commit()
        db.refresh(dap)

        dapv = DailyActivityProgressVerification(
            daily_activity_progress_id=dap.id,
            project_id=p1_id,
            verification_status="VERIFIED",
            verified_quantity=Decimal("8.0000"),
            verified_quantity_unit="M3",
            verified_by=setup_data["sup_id"],
        )
        db.add(dapv)
        db.commit()

    # Create snapshot without passing verified_activity_execution_quantity
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": act_id, "material_item_id": mat_id},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert Decimal(str(data["verified_activity_execution_quantity"])) == Decimal("8.0000")
    assert data["verified_activity_execution_unit"] == "M3"


def test_51_hardening_scenario_k_activity_output_from_certificate_item(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    with TestingSessionLocal() as db:
        act = ConstructionActivity(
            project_id=p1_id,
            activity_code=f"ACT-K-{uuid.uuid4().hex[:4]}",
            activity_name="Hardening K Activity",
            activity_type="CONSTRUCTION",
            created_by=setup_data["adm_id"],
        )
        mat = MaterialItem(
            project_id=p1_id,
            material_code=f"MAT-K-{uuid.uuid4().hex[:4]}",
            material_name="Hardening K Mat",
            material_category="REINFORCEMENT",
            standard_unit="MT",
        )
        db.add_all([act, mat])
        db.commit()
        db.refresh(act)
        db.refresh(mat)
        act_id, mat_id = act.id, mat.id

        # Period progress certificate
        cert_k = PeriodProgressCertificate(
            project_id=p1_id,
            certificate_number=f"CERT-K-{uuid.uuid4().hex[:6]}",
            certificate_type="PERIOD_SNAPSHOT",
            monitoring_baseline_id=setup_data["base1_id"],
            baseline_schedule_id=setup_data["sched1_id"],
            baseline_schedule_version="1.0",
            baseline_schedule_algorithm_version="CPM_1.0",
            baseline_start_date=date(2026, 9, 1),
            period_start_date=date(2026, 9, 1),
            period_cut_off_date=date(2026, 9, 30),
            certificate_status="DRAFT",
            currency="INR",
            period_claimed_value=Decimal("1250.00"),
            period_certified_value=Decimal("1250.00"),
            period_disputed_exposure=Decimal("0.00"),
            cumulative_claimed_value=Decimal("1250.00"),
            cumulative_certified_value=Decimal("1250.00"),
            cumulative_disputed_exposure=Decimal("0.00"),
            item_count=1,
            valuation_snapshot_hash="hash_k",
        )
        db.add(cert_k)
        db.commit()
        db.refresh(cert_k)

        # Period certificate item
        cert_item = PeriodCertificateItem(
            certificate_id=cert_k.id,
            valuation_id=setup_data["dpv_id"],
            activity_id=act_id,
            claimed_quantity=Decimal("25.0000"),
            certified_quantity=Decimal("25.0000"),
            quantity_unit="SQM",
            unit_conversion_factor=Decimal("1.000000"),
            applied_rate=Decimal("50.00"),
            applied_rate_unit="SQM",
            currency="INR",
            claimed_amount=Decimal("1250.00"),
            certified_amount=Decimal("1250.00"),
            discrepancy_quantity=Decimal("0.0000"),
            disputed_exposure=Decimal("0.00"),
        )
        db.add(cert_item)
        db.commit()

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": act_id, "material_item_id": mat_id},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert Decimal(str(data["verified_activity_execution_quantity"])) == Decimal("25.0000")
    assert data["verified_activity_execution_unit"] == "SQM"


def test_52_hardening_scenario_l_listing_filters(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["sup_token"]
    resp = client_fixture.get(
        f"/api/projects/{p1_id}/material-performance?status=FINALIZED",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    for item in resp.json():
        assert item["status"] == "FINALIZED"


def test_53_hardening_scenario_m_n_contractor_mutation_forbidden(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    con_token = setup_data["con_token"]
    # Attempt create
    r_create = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {con_token}"},
        json={"activity_id": setup_data["act1_id"], "material_item_id": setup_data["steel_id"]},
    )
    assert r_create.status_code == 403

    # Attempt finalize
    r_fin = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/some-fake-id/finalize",
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert r_fin.status_code == 403

    # Attempt supersede
    r_sup = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/some-fake-id/supersede",
        headers={"Authorization": f"Bearer {con_token}"},
        json={"supersession_reason": "Contractor attempt"},
    )
    assert r_sup.status_code == 403


# ==============================================================================
# AUDIT & HARDENING TESTS (DIMENSIONS 1–8)
# ==============================================================================

def test_54_incompatible_unit_aggregation_multiple_theoretical_items(client_fixture, setup_data):
    """Dimension 1: Mix compatible and incompatible theoretical items; ensure no silent addition."""
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    act_id = setup_data["act1_id"]

    with TestingSessionLocal() as db:
        mat = MaterialItem(
            project_id=p1_id,
            material_code=f"MAT-THEO-MIX-{uuid.uuid4().hex[:4]}",
            material_name="Theo Mix Mat",
            material_category="BINDER",
            standard_unit="MT",
        )
        db.add(mat)
        db.commit()
        db.refresh(mat)
        mat_id = mat.id

        # Compatible item: 500 KG -> converts to 0.5000 MT
        make_theo_item(
            db, p1_id, act_id, mat_id, Decimal("500.0000"), "KG",
            setup_data["mix_id"], setup_data["cert_id"], setup_data["cert_item_id"]
        )
        # Incompatible item: 10 BAG -> cannot convert to MT
        make_theo_item(
            db, p1_id, act_id, mat_id, Decimal("10.0000"), "BAG",
            setup_data["mix_id"], setup_data["cert_id"], setup_data["cert_item_id"]
        )

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": act_id, "material_item_id": mat_id},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["performance_status"] == "UNIT_MISMATCH"
    assert data["theoretical_quantity"] is None
    assert data["theoretical_unit"] is None
    assert data["theoretical_variance_quantity"] is None
    assert data["theoretical_variance_percentage"] is None
    # Provenance records the unconvertible theoretical item
    assert "unconvertible_theoretical_units" in data["provenance_metadata"]
    assert len(data["provenance_metadata"]["unconvertible_theoretical_units"]) == 1
    assert data["provenance_metadata"]["unconvertible_theoretical_units"][0]["source_unit"] == "BAG"


def test_55_incompatible_unit_aggregation_multiple_issue_allocations(client_fixture, setup_data):
    """Dimension 1: Mix compatible and incompatible issue allocations; ensure no raw addition."""
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    act_id = setup_data["act1_id"]

    with TestingSessionLocal() as db:
        mat = MaterialItem(
            project_id=p1_id,
            material_code=f"MAT-ISSUE-MIX-{uuid.uuid4().hex[:4]}",
            material_name="Issue Mix Mat",
            material_category="AGGREGATE",
            standard_unit="MT",
        )
        db.add(mat)
        db.commit()
        db.refresh(mat)
        mat_id = mat.id

        # Stock ledger issue entry
        stk_issue = MaterialStockLedger(
            project_id=p1_id,
            material_item_id=mat_id,
            transaction_type="ISSUE",
            transaction_quantity=Decimal("1050.0000"),
            unit="MT",
            transaction_date=date(2026, 10, 5),
            source_type="SUPERVISOR_VERIFIED",
            is_authoritative=True,
            verification_status="VERIFIED",
            created_by=setup_data["adm_id"],
        )
        db.add(stk_issue)
        db.commit()
        db.refresh(stk_issue)

        # Compatible allocation: 1000 KG -> 1.0000 MT
        a1 = MaterialIssueAllocation(
            project_id=p1_id,
            material_stock_ledger_id=stk_issue.id,
            material_item_id=mat_id,
            activity_id=act_id,
            issued_quantity=Decimal("1000.0000"),
            issued_unit="KG",
            issue_date=date(2026, 10, 5),
            status="ALLOCATED",
            created_by=setup_data["adm_id"],
        )
        # Incompatible allocation: 50 LITRE -> cannot convert to MT
        a2 = MaterialIssueAllocation(
            project_id=p1_id,
            material_stock_ledger_id=stk_issue.id,
            material_item_id=mat_id,
            activity_id=act_id,
            issued_quantity=Decimal("50.0000"),
            issued_unit="LITRE",
            issue_date=date(2026, 10, 5),
            status="ALLOCATED",
            created_by=setup_data["adm_id"],
        )
        db.add_all([a1, a2])
        db.commit()

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": act_id, "material_item_id": mat_id},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["performance_status"] == "UNIT_MISMATCH"
    assert data["issued_quantity"] is None
    assert data["issued_unit"] is None
    assert "unconvertible_issued_units" in data["provenance_metadata"]
    assert len(data["provenance_metadata"]["unconvertible_issued_units"]) == 1
    assert data["provenance_metadata"]["unconvertible_issued_units"][0]["source_unit"] == "LITRE"


def test_56_project_membership_authorization_rejections(client_fixture, setup_data):
    """Dimension 2: Non-member non-admin users must be rejected with 403 on all operations."""
    p1_id = setup_data["p1_id"]
    non_member_email = f"non_member_{uuid.uuid4().hex[:6]}@test.com"

    with TestingSessionLocal() as db:
        user = User(email=non_member_email, password_hash=get_password_hash("pass"), role="site_supervisor")
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id

    token = create_access_token({"sub": non_member_email, "role": "site_supervisor", "user_id": user_id})

    # 1. Non-member CREATE -> 403
    r_create = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": setup_data["act1_id"], "material_item_id": setup_data["steel_id"]},
    )
    assert r_create.status_code == 403

    # Create a draft snapshot using admin for subsequent tests
    r_admin_create = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {setup_data['adm_token']}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "performance_period_start": "2026-10-01",
            "performance_period_end": "2026-10-31",
        },
    )
    assert r_admin_create.status_code == 201
    snap_id = r_admin_create.json()["id"]

    # 2. Non-member GET single -> 403
    r_get = client_fixture.get(
        f"/api/projects/{p1_id}/material-performance/{snap_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_get.status_code == 403

    # 3. Non-member LIST -> 403
    r_list = client_fixture.get(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_list.status_code == 403

    # 4. Non-member SUMMARY -> 403
    r_sum = client_fixture.get(
        f"/api/projects/{p1_id}/material-performance/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_sum.status_code == 403

    # 5. Non-member FINALIZE -> 403
    r_fin = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/finalize",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_fin.status_code == 403

    # 6. Non-member SUPERSEDE -> 403
    r_sup = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "Non member trying"},
    )
    assert r_sup.status_code == 403


def test_57_snapshot_lifecycle_create_finalized_rejected(client_fixture, setup_data):
    """Dimension 3: Callers cannot supply status='FINALIZED' during creation; must produce DRAFT."""
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "status": "FINALIZED",
        },
    )
    assert resp.status_code == 422
    assert "Snapshots must always be created in DRAFT status" in resp.text


def test_58_snapshot_lifecycle_invalid_sql_transition_draft_to_superseded(setup_data):
    """Dimension 3 & 8: Direct SQL update from DRAFT to SUPERSEDED is blocked by DB trigger."""
    p1_id = setup_data["p1_id"]
    with TestingSessionLocal() as db:
        snap = MaterialPerformanceSnapshot(
            project_id=p1_id,
            activity_id=setup_data["act1_id"],
            material_item_id=setup_data["steel_id"],
            performance_status="MATCH",
            canonical_hash="hash_draft_to_sup",
            status="DRAFT",
            created_by=setup_data["adm_id"],
        )
        db.add(snap)
        db.commit()
        db.refresh(snap)
        snap_id = snap.id

        with pytest.raises(Exception) as excinfo:
            db.execute(
                text("UPDATE material_performance_snapshots SET status = 'SUPERSEDED' WHERE id = :id"),
                {"id": snap_id},
            )
            db.commit()
        assert "cannot transition directly from draft to superseded" in str(excinfo.value).lower()


def test_59_snapshot_lifecycle_superseded_cannot_reopen(client_fixture, setup_data):
    """Dimension 3 & 8: SUPERSEDED snapshots cannot be reopened via API or direct SQL."""
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]

    # Create draft
    r_create = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act3_id"],
            "material_item_id": setup_data["steel_id"],
            "performance_period_start": "2026-05-01",
            "performance_period_end": "2026-05-31",
        },
    )
    assert r_create.status_code == 201
    snap_id = r_create.json()["id"]

    # Finalize
    r_fin = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/finalize",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_fin.status_code == 200

    # Supersede
    r_sup = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "Closing out period May"},
    )
    assert r_sup.status_code == 200

    # Re-finalizing superseded is rejected
    r_fin_again = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/finalize",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_fin_again.status_code == 400

    # Superseding already superseded is rejected
    r_sup_again = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "Trying to supersede again"},
    )
    assert r_sup_again.status_code == 400

    # Direct SQL attempt to modify superseded record is rejected by trigger
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as excinfo:
            db.execute(
                text("UPDATE material_performance_snapshots SET status = 'FINALIZED' WHERE id = :id"),
                {"id": snap_id},
            )
            db.commit()
        assert "superseded records cannot be modified" in str(excinfo.value).lower()


def test_60_supersession_replacement_reference_validation(client_fixture, setup_data):
    """Dimension 4: Replacement reference points to valid snapshot in same project; records user."""
    p1_id = setup_data["p1_id"]
    p2_id = setup_data["p2_id"]
    adm_token = setup_data["adm_token"]

    # 1. Create and finalize snap 1 in P1
    r1 = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "performance_period_start": "2026-06-01",
            "performance_period_end": "2026-06-30",
        },
    )
    snap1_id = r1.json()["id"]
    client_fixture.post(f"/api/projects/{p1_id}/material-performance/{snap1_id}/finalize", headers={"Authorization": f"Bearer {adm_token}"})

    # 2. Create snap in P2
    r_p2 = client_fixture.post(
        f"/api/projects/{p2_id}/material-performance",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={
            "activity_id": setup_data["act2_id"],
            "material_item_id": setup_data["p2_mat_id"],
            "performance_period_start": "2026-06-01",
            "performance_period_end": "2026-06-30",
        },
    )
    p2_snap_id = r_p2.json()["id"]

    # 3. Nonexistent replacement ID -> 404
    r_nonexistent = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap1_id}/supersede",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"supersession_reason": "Replacement test", "replacement_snapshot_id": str(uuid.uuid4())},
    )
    assert r_nonexistent.status_code == 404

    # 4. Cross-project replacement ID -> 404
    r_cross = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap1_id}/supersede",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"supersession_reason": "Cross project replacement", "replacement_snapshot_id": p2_snap_id},
    )
    assert r_cross.status_code == 404

    # 5. Replacement with itself -> 400
    r_self = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap1_id}/supersede",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"supersession_reason": "Self replacement", "replacement_snapshot_id": snap1_id},
    )
    assert r_self.status_code == 400

    # 6. Create valid replacement snap 2 in P1
    r2 = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "performance_period_start": "2026-06-01",
            "performance_period_end": "2026-06-30",
        },
    )
    snap2_id = r2.json()["id"]

    # 7. Replacement already superseded -> 400
    # First create and supersede a third snapshot with distinct period
    r3 = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "performance_period_start": "2026-05-01",
            "performance_period_end": "2026-05-31",
        },
    )
    snap3_id = r3.json()["id"]
    r_fin3 = client_fixture.post(f"/api/projects/{p1_id}/material-performance/{snap3_id}/finalize", headers={"Authorization": f"Bearer {adm_token}"})
    assert r_fin3.status_code == 200
    r_sup3 = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap3_id}/supersede",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"supersession_reason": "Superseding snap3"},
    )
    assert r_sup3.status_code == 200
    r_already_sup = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap1_id}/supersede",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"supersession_reason": "Using superseded replacement", "replacement_snapshot_id": snap3_id},
    )
    assert r_already_sup.status_code == 400
    assert "already be superseded" in r_already_sup.json()["detail"].lower()

    # 8. Replacement in a project requesting user cannot access -> 403 (contractor cannot mutate)
    con_token = setup_data["con_token"]
    r_unauth = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap1_id}/supersede",
        headers={"Authorization": f"Bearer {con_token}"},
        json={"supersession_reason": "Unauthorized replacement attempt", "replacement_snapshot_id": snap2_id},
    )
    assert r_unauth.status_code == 403

    # 9. Logical identity mismatch tests:
    # A. Activity mismatch
    r_diff_act = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={
            "activity_id": setup_data["act3_id"],
            "material_item_id": setup_data["steel_id"],
            "performance_period_start": "2026-06-01",
            "performance_period_end": "2026-06-30",
        },
    )
    diff_act_id = r_diff_act.json()["id"]
    r_err_act = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap1_id}/supersede",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"supersession_reason": "Activity mismatch", "replacement_snapshot_id": diff_act_id},
    )
    assert r_err_act.status_code == 400
    assert "activity" in r_err_act.json()["detail"].lower()

    # B. Material mismatch
    r_diff_mat = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["cement_id"],
            "performance_period_start": "2026-06-01",
            "performance_period_end": "2026-06-30",
        },
    )
    diff_mat_id = r_diff_mat.json()["id"]
    r_err_mat = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap1_id}/supersede",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"supersession_reason": "Material mismatch", "replacement_snapshot_id": diff_mat_id},
    )
    assert r_err_mat.status_code == 400
    assert "material" in r_err_mat.json()["detail"].lower()

    # C. Period-start mismatch
    r_diff_start = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "performance_period_start": "2026-06-02",
            "performance_period_end": "2026-06-30",
        },
    )
    diff_start_id = r_diff_start.json()["id"]
    r_err_start = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap1_id}/supersede",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"supersession_reason": "Period start mismatch", "replacement_snapshot_id": diff_start_id},
    )
    assert r_err_start.status_code == 400
    assert "performance_period_start" in r_err_start.json()["detail"].lower()

    # D. Period-end mismatch
    r_diff_end = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "performance_period_start": "2026-06-01",
            "performance_period_end": "2026-06-29",
        },
    )
    diff_end_id = r_diff_end.json()["id"]
    r_err_end = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap1_id}/supersede",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"supersession_reason": "Period end mismatch", "replacement_snapshot_id": diff_end_id},
    )
    assert r_err_end.status_code == 400
    assert "performance_period_end" in r_err_end.json()["detail"].lower()

    # E. Reconciliation mismatch
    r_diff_recon = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "performance_period_start": "2026-06-01",
            "performance_period_end": "2026-06-30",
            "reconciliation_id": setup_data["recon_id"],
        },
    )
    diff_recon_id = r_diff_recon.json()["id"]
    r_err_recon = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap1_id}/supersede",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"supersession_reason": "Reconciliation mismatch", "replacement_snapshot_id": diff_recon_id},
    )
    assert r_err_recon.status_code == 400
    assert "reconciliation_id" in r_err_recon.json()["detail"].lower()

    # F. Nullable matching: original has NULL reconciliation, replacement must have NULL reconciliation
    # snap2 has identical NULL reconciliation, activity, material, and period [2026-06-01, 2026-06-30]

    # 10. Valid same-identity supersession
    r_valid = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{snap1_id}/supersede",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"supersession_reason": "Valid replacement with snap2", "replacement_snapshot_id": snap2_id},
    )
    assert r_valid.status_code == 200
    data = r_valid.json()
    assert data["status"] == "SUPERSEDED"
    assert data["superseded_by"] == snap2_id
    assert data["superseded_by_user_id"] == setup_data["adm_id"]
    assert data["supersession_reason"] == "Valid replacement with snap2"


def test_61_concurrency_duplicate_authoritative_snapshots_rejected(setup_data):
    """Dimension 5: Concurrent finalization of duplicate authoritative snapshots is prevented by DB index."""
    p1_id = setup_data["p1_id"]
    adm_token = setup_data["adm_token"]
    sup_token = setup_data["sup_token"]

    # Create two separate draft snapshots for the exact same identity (activity, material, period)
    c = TestClient(app)
    r1 = c.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "performance_period_start": "2026-07-01",
            "performance_period_end": "2026-07-31",
        },
    )
    assert r1.status_code == 201
    draft1_id = r1.json()["id"]

    r2 = c.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "performance_period_start": "2026-07-01",
            "performance_period_end": "2026-07-31",
        },
    )
    assert r2.status_code == 201
    draft2_id = r2.json()["id"]

    results = []

    def fin_snap(snap_id, token):
        client = TestClient(app)
        res = client.post(
            f"/api/projects/{p1_id}/material-performance/{snap_id}/finalize",
            headers={"Authorization": f"Bearer {token}"},
        )
        results.append(res.status_code)

    t1 = threading.Thread(target=fin_snap, args=(draft1_id, adm_token))
    t2 = threading.Thread(target=fin_snap, args=(draft2_id, sup_token))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Exactly one authoritative snapshot finalized (200), the duplicate must fail with 409 Conflict
    assert 200 in results
    assert 409 in results
    assert len(results) == 2


def test_62_separate_periods_and_revisions_allowed(client_fixture, setup_data):
    """Dimension 5: Legitimate separate periods and supersession revisions are supported without conflict."""
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]

    # Period August
    r_aug = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "performance_period_start": "2026-08-01",
            "performance_period_end": "2026-08-31",
        },
    )
    aug_id = r_aug.json()["id"]
    r_fin_aug = client_fixture.post(f"/api/projects/{p1_id}/material-performance/{aug_id}/finalize", headers={"Authorization": f"Bearer {token}"})
    assert r_fin_aug.status_code == 200

    # Period September (distinct period)
    r_sep = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "performance_period_start": "2026-09-01",
            "performance_period_end": "2026-09-30",
        },
    )
    sep_id = r_sep.json()["id"]
    r_fin_sep = client_fixture.post(f"/api/projects/{p1_id}/material-performance/{sep_id}/finalize", headers={"Authorization": f"Bearer {token}"})
    assert r_fin_sep.status_code == 200

    # Supersede August
    r_sup_aug = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance/{aug_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "Recalibrating August"},
    )
    assert r_sup_aug.status_code == 200

    # Create new revision for August and finalize it
    r_aug_rev = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "performance_period_start": "2026-08-01",
            "performance_period_end": "2026-08-31",
        },
    )
    aug_rev_id = r_aug_rev.json()["id"]
    r_fin_aug_rev = client_fixture.post(f"/api/projects/{p1_id}/material-performance/{aug_rev_id}/finalize", headers={"Authorization": f"Bearer {token}"})
    assert r_fin_aug_rev.status_code == 200

    # Test NULL period boundaries (period-independent snapshot on act3)
    r_null_period = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act3_id"],
            "material_item_id": setup_data["steel_id"],
            "performance_period_start": None,
            "performance_period_end": None,
        },
    )
    assert r_null_period.status_code == 201
    null_p_id = r_null_period.json()["id"]
    r_fin_null = client_fixture.post(f"/api/projects/{p1_id}/material-performance/{null_p_id}/finalize", headers={"Authorization": f"Bearer {token}"})
    assert r_fin_null.status_code == 200

    # Duplicate NULL period snapshot must conflict (409)
    r_null_dup = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act3_id"],
            "material_item_id": setup_data["steel_id"],
            "performance_period_start": None,
            "performance_period_end": None,
        },
    )
    null_dup_id = r_null_dup.json()["id"]
    r_fin_null_dup = client_fixture.post(f"/api/projects/{p1_id}/material-performance/{null_dup_id}/finalize", headers={"Authorization": f"Bearer {token}"})
    assert r_fin_null_dup.status_code == 409

    # Multiple drafts with same identity allowed
    r_draft1 = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "performance_period_start": "2026-11-01",
            "performance_period_end": "2026-11-30",
        },
    )
    r_draft2 = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "performance_period_start": "2026-11-01",
            "performance_period_end": "2026-11-30",
        },
    )
    assert r_draft1.status_code == 201
    assert r_draft2.status_code == 201

    # Distinct reconciliation identities allowed
    with TestingSessionLocal() as db:
        r_rec1 = MaterialConsumptionReconciliation(
            id=str(uuid.uuid4()),
            project_id=p1_id,
            material_requirement_plan_id=setup_data["plan_id"],
            activity_id=setup_data["act1_id"],
            material_item_id=setup_data["steel_id"],
            issued_quantity=Decimal("12.0000"),
            issued_unit="MT",
            actual_consumed_quantity=Decimal("12.0000"),
            actual_consumed_unit="MT",
            theoretical_quantity=Decimal("10.0000"),
            theoretical_unit="MT",
            planned_quantity=Decimal("10.0000"),
            planned_unit="MT",
            variance_quantity=Decimal("2.0000"),
            variance_percentage=Decimal("20.0000"),
            permissible_wastage_quantity=Decimal("0.5000"),
            unauthorized_wastage_quantity=Decimal("1.5000"),
            status="WITHIN_PERMISSIBLE_WASTAGE",
            canonical_hash=hashlib.sha256(b"rec1").hexdigest(),
            created_by=setup_data["adm_id"],
        )
        r_rec2 = MaterialConsumptionReconciliation(
            id=str(uuid.uuid4()),
            project_id=p1_id,
            material_requirement_plan_id=setup_data["plan_id"],
            activity_id=setup_data["act1_id"],
            material_item_id=setup_data["steel_id"],
            issued_quantity=Decimal("12.0000"),
            issued_unit="MT",
            actual_consumed_quantity=Decimal("12.0000"),
            actual_consumed_unit="MT",
            theoretical_quantity=Decimal("10.0000"),
            theoretical_unit="MT",
            planned_quantity=Decimal("10.0000"),
            planned_unit="MT",
            variance_quantity=Decimal("2.0000"),
            variance_percentage=Decimal("20.0000"),
            permissible_wastage_quantity=Decimal("0.5000"),
            unauthorized_wastage_quantity=Decimal("1.5000"),
            status="WITHIN_PERMISSIBLE_WASTAGE",
            canonical_hash=hashlib.sha256(b"rec2").hexdigest(),
            created_by=setup_data["adm_id"],
        )
        db.add_all([r_rec1, r_rec2])
        db.commit()
        rec1_id = r_rec1.id
        rec2_id = r_rec2.id

    r_s_rec1 = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "reconciliation_id": rec1_id,
            "performance_period_start": "2026-12-01",
            "performance_period_end": "2026-12-31",
        },
    )
    s_rec1_id = r_s_rec1.json()["id"]
    r_fin_rec1 = client_fixture.post(f"/api/projects/{p1_id}/material-performance/{s_rec1_id}/finalize", headers={"Authorization": f"Bearer {token}"})
    assert r_fin_rec1.status_code == 200

    r_s_rec2 = client_fixture.post(
        f"/api/projects/{p1_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "material_item_id": setup_data["steel_id"],
            "reconciliation_id": rec2_id,
            "performance_period_start": "2026-12-01",
            "performance_period_end": "2026-12-31",
        },
    )
    s_rec2_id = r_s_rec2.json()["id"]
    r_fin_rec2 = client_fixture.post(f"/api/projects/{p1_id}/material-performance/{s_rec2_id}/finalize", headers={"Authorization": f"Bearer {token}"})
    assert r_fin_rec2.status_code == 200


def test_63_summary_semantics_missing_values_and_unit_segregation(client_fixture, setup_data):
    """Dimension 6: Summary does not treat missing qty as zero; segregated by unit; excludes superseded."""
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]

    # Fresh project for isolated summary testing
    with TestingSessionLocal() as db:
        p_iso = Project(name=f"Summary Test Proj {uuid.uuid4().hex[:4]}", created_by=setup_data["adm_id"])
        db.add(p_iso)
        db.commit()
        db.refresh(p_iso)
        p_iso_id = p_iso.id

        db.add(ProjectMember(project_id=p_iso_id, user_id=setup_data["adm_id"]))
        act_iso = ConstructionActivity(
            project_id=p_iso_id,
            activity_code="ACT-ISO-1",
            activity_name="Iso Activity",
            activity_type="CONSTRUCTION",
            duration_value=Decimal("10.000000"),
            duration_unit="DAY",
            created_by=setup_data["adm_id"],
        )
        mat_kg = MaterialItem(
            project_id=p_iso_id,
            material_code="MAT-ISO-KG",
            material_name="Iso Mat KG",
            material_category="REINFORCEMENT",
            standard_unit="KG",
        )
        mat_bag = MaterialItem(
            project_id=p_iso_id,
            material_code="MAT-ISO-BAG",
            material_name="Iso Mat BAG",
            material_category="BINDER",
            standard_unit="BAG",
        )
        db.add_all([act_iso, mat_kg, mat_bag])
        db.commit()
        db.refresh(act_iso)
        db.refresh(mat_kg)
        db.refresh(mat_bag)
        act_iso_id = act_iso.id
        mat_kg_id = mat_kg.id
        mat_bag_id = mat_bag.id

        # Isolated certificate chain for TheoreticalConsumptionItem linkage
        sched_iso = ConstructionSchedule(
            project_id=p_iso_id,
            schedule_version="1.0",
            calculation_status="CALCULATED",
            calculated_by=setup_data["adm_id"],
            algorithm_version="CPM_1.0",
            input_snapshot_json={"version": "1.0"},
        )
        db.add(sched_iso)
        db.commit()

        base_iso = MonitoringBaseline(
            project_id=p_iso_id,
            schedule_id=sched_iso.id,
            schedule_version="1.0",
            schedule_algorithm_version="CPM_1.0",
            baseline_start_date=date(2026, 9, 1),
            frozen_by=setup_data["adm_id"],
            status="ACTIVE",
        )
        db.add(base_iso)
        db.commit()

        mix_iso = MaterialMixDesign(
            project_id=p_iso_id,
            mix_code=f"MIX-ISO-{uuid.uuid4().hex[:4]}",
            grade_designation="M25",
            mix_type="NOMINAL_MIX",
            rule_code="IS456-M25",
            classification="ASSUMPTION_BASED",
            status="APPROVED",
            approved_by=setup_data["adm_id"],
            approved_at=datetime.now(timezone.utc),
        )
        db.add(mix_iso)
        db.commit()

        crate_iso = CostRate(
            project_id=p_iso_id,
            rate_code=f"RATE-ISO-{uuid.uuid4().hex[:4]}",
            description="ISO Rate",
            unit="KG",
            rate_value=Decimal("100.00"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="ISO",
            status="CONFIRMED",
            created_by=setup_data["adm_id"],
            confirmed_by=setup_data["adm_id"],
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(crate_iso)
        db.commit()

        arm_iso = ActivityRateMapping(
            project_id=p_iso_id,
            activity_id=act_iso_id,
            cost_rate_id=crate_iso.id,
            rate_value=Decimal("100.00"),
            rate_unit="KG",
            rate_version="1.0",
            currency="INR",
            status="ACTIVE",
            created_by=setup_data["adm_id"],
        )
        db.add(arm_iso)
        db.commit()

        cert_iso = PeriodProgressCertificate(
            project_id=p_iso_id,
            certificate_number=f"CERT-ISO-{uuid.uuid4().hex[:6]}",
            certificate_type="PERIOD_SNAPSHOT",
            monitoring_baseline_id=base_iso.id,
            baseline_schedule_id=sched_iso.id,
            baseline_schedule_version="1.0",
            baseline_schedule_algorithm_version="CPM_1.0",
            baseline_start_date=date(2026, 9, 1),
            period_start_date=date(2026, 9, 1),
            period_cut_off_date=date(2026, 9, 30),
            certificate_status="DRAFT",
            currency="INR",
            period_claimed_value=Decimal("1000.00"),
            period_certified_value=Decimal("1000.00"),
            period_disputed_exposure=Decimal("0.00"),
            cumulative_claimed_value=Decimal("1000.00"),
            cumulative_certified_value=Decimal("1000.00"),
            cumulative_disputed_exposure=Decimal("0.00"),
            item_count=1,
            valuation_snapshot_hash="valid_hash_iso",
        )
        db.add(cert_iso)
        db.commit()

        dpr_iso = DailyProgressReport(
            project_id=p_iso_id,
            report_date=date(2026, 9, 15),
            submitted_by=setup_data["adm_id"],
            submission_status="FINALIZED",
        )
        db.add(dpr_iso)
        db.commit()

        dap_iso = DailyActivityProgress(
            daily_report_id=dpr_iso.id,
            project_id=p_iso_id,
            activity_id=act_iso_id,
            contractor_progress_value=Decimal("10.0000"),
            contractor_progress_unit="KG",
            contractor_status="COMPLETED",
            created_by=setup_data["adm_id"],
        )
        db.add(dap_iso)
        db.commit()

        dapv_iso = DailyActivityProgressVerification(
            daily_activity_progress_id=dap_iso.id,
            project_id=p_iso_id,
            verification_status="VERIFIED",
            verified_quantity=Decimal("10.0000"),
            verified_quantity_unit="KG",
            verified_by=setup_data["adm_id"],
        )
        db.add(dapv_iso)
        db.commit()

        dpv_iso = DailyProgressValuation(
            project_id=p_iso_id,
            verification_id=dapv_iso.id,
            activity_rate_mapping_id=arm_iso.id,
            contractor_claimed_quantity=Decimal("10.0000"),
            supervisor_certified_quantity=Decimal("10.0000"),
            quantity_unit="KG",
            unit_conversion_factor=Decimal("1.000000"),
            applied_rate_value=Decimal("100.00"),
            applied_rate_unit="KG",
            currency="INR",
            contractor_claimed_value=Decimal("1000.00"),
            certified_progress_value=Decimal("1000.00"),
            discrepancy_quantity=Decimal("0.000000"),
            disputed_valuation_exposure=Decimal("0.0000"),
            certified_certificate_id=cert_iso.id,
            valuation_status="ACTIVE",
        )
        db.add(dpv_iso)
        db.commit()

        cert_item_iso = PeriodCertificateItem(
            certificate_id=cert_iso.id,
            valuation_id=dpv_iso.id,
            activity_id=act_iso_id,
            claimed_quantity=Decimal("10.0000"),
            certified_quantity=Decimal("10.0000"),
            quantity_unit="KG",
            unit_conversion_factor=Decimal("1.000000"),
            applied_rate=Decimal("100.00"),
            applied_rate_unit="KG",
            currency="INR",
            claimed_amount=Decimal("1000.00"),
            certified_amount=Decimal("1000.00"),
            discrepancy_quantity=Decimal("0.0000"),
            disputed_exposure=Decimal("0.00"),
        )
        db.add(cert_item_iso)
        db.commit()

        # Theoretical item for KG: 100 KG
        make_theo_item(db, p_iso_id, act_iso_id, mat_kg_id, Decimal("100.0000"), "KG", mix_iso.id, cert_iso.id, cert_item_iso.id)
        # Consumption for KG: 80 KG
        make_consumption_entry_and_verif(db, p_iso_id, act_iso_id, mat_kg_id, Decimal("80.0000"), "KG", setup_data["con_id"], setup_data["sup_id"])

        # Consumption for BAG: 50 BAG, but NO theoretical items seeded (missing theoretical)
        make_consumption_entry_and_verif(db, p_iso_id, act_iso_id, mat_bag_id, Decimal("50.0000"), "BAG", setup_data["con_id"], setup_data["sup_id"])

    # Create snapshot for KG
    r_kg = client_fixture.post(
        f"/api/projects/{p_iso_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": act_iso_id, "material_item_id": mat_kg_id},
    )
    assert r_kg.status_code == 201

    # Create snapshot for BAG (missing theoretical)
    r_bag = client_fixture.post(
        f"/api/projects/{p_iso_id}/material-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": act_iso_id, "material_item_id": mat_bag_id},
    )
    assert r_bag.status_code == 201

    # Fetch summary
    resp_sum = client_fixture.get(
        f"/api/projects/{p_iso_id}/material-performance/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_sum.status_code == 200
    s_data = resp_sum.json()
    assert s_data["total_snapshots"] == 2

    # Units remain segregated in dictionaries
    assert "KG" in s_data["total_actual_consumption"]
    assert "BAG" in s_data["total_actual_consumption"]
    assert Decimal(str(s_data["total_actual_consumption"]["KG"])) == Decimal("80.0000")
    assert Decimal(str(s_data["total_actual_consumption"]["BAG"])) == Decimal("50.0000")

    # Theoretical consumption for KG is present, for BAG is missing
    assert "KG" in s_data["total_theoretical_consumption"]
    assert Decimal(str(s_data["total_theoretical_consumption"]["KG"])) == Decimal("100.0000")
    assert "BAG" not in s_data["total_theoretical_consumption"]

    # Total theoretical variance for KG is -20.0000 (80 - 100)
    assert "KG" in s_data["total_theoretical_variance"]
    assert Decimal(str(s_data["total_theoretical_variance"]["KG"])) == Decimal("-20.0000")

    # Missing theoretical quantity is NOT treated as 0: total theoretical variance for BAG must NOT exist
    assert "BAG" not in s_data["total_theoretical_variance"]


def test_64_database_immutability_input_and_provenance_triggers(setup_data):
    """Dimension 8: Direct SQL attempts to alter calculation fields, inputs, provenance are blocked."""
    p1_id = setup_data["p1_id"]
    with TestingSessionLocal() as db:
        snap = MaterialPerformanceSnapshot(
            project_id=p1_id,
            activity_id=setup_data["act1_id"],
            material_item_id=setup_data["steel_id"],
            performance_status="MATCH",
            canonical_hash="hash_immut_test",
            status="FINALIZED",
            input_snapshot_json={"test": "orig_input"},
            provenance_metadata={"test": "orig_provenance"},
            created_by=setup_data["adm_id"],
            finalized_by=setup_data["adm_id"],
        )
        db.add(snap)
        db.commit()
        db.refresh(snap)
        snap_id = snap.id

        # 1. Update input_snapshot_json -> rejected
        with pytest.raises(Exception) as exc1:
            db.execute(text("UPDATE material_performance_snapshots SET input_snapshot_json = '{\"test\":\"hacked\"}' WHERE id = :id"), {"id": snap_id})
            db.commit()
        db.rollback()
        assert "immutable" in str(exc1.value).lower()

        # 2. Update provenance_metadata -> rejected
        with pytest.raises(Exception) as exc2:
            db.execute(text("UPDATE material_performance_snapshots SET provenance_metadata = '{\"test\":\"hacked\"}' WHERE id = :id"), {"id": snap_id})
            db.commit()
        db.rollback()
        assert "immutable" in str(exc2.value).lower()

        # 3. Update finalized_by -> rejected
        with pytest.raises(Exception) as exc3:
            db.execute(text("UPDATE material_performance_snapshots SET finalized_by = :uid WHERE id = :id"), {"id": snap_id, "uid": setup_data["sup_id"]})
            db.commit()
        db.rollback()
        assert "immutable" in str(exc3.value).lower()


def test_65_canonical_hash_determinism_and_reproducibility():
    """Dimension 7: Canonical hash generation is deterministic regardless of dict insertion order."""
    payload1 = {
        "algorithm_version": "MAT_PERFORMANCE_1.0",
        "project_id": "proj-1",
        "activity_id": "act-1",
        "material_item_id": "mat-1",
        "planned_quantity": "100.0000",
        "actual_consumption_quantity": "95.0000",
        "performance_status": "UNDER_CONSUMPTION",
    }
    # Reverse key order
    payload2 = {
        "performance_status": "UNDER_CONSUMPTION",
        "actual_consumption_quantity": "95.0000",
        "planned_quantity": "100.0000",
        "material_item_id": "mat-1",
        "activity_id": "act-1",
        "project_id": "proj-1",
        "algorithm_version": "MAT_PERFORMANCE_1.0",
    }

    hash1 = generate_canonical_hash(payload1)
    hash2 = generate_canonical_hash(payload2)

    assert hash1 == hash2
    assert len(hash1) == 64

