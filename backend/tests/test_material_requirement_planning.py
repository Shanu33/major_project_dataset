"""Phase 1O: Contractor Resource & Procurement Planning Foundation Test Suite.

Comprehensive Verification:
- Scenarios 1–6:   Plan Creation, Uniqueness, Lifecycle & Transitions
- Scenarios 7–11:  Phase 1N Lineage, Provenance & Schedule Date Derivation
- Scenarios 12–16: Unit Compatibility, Conversions & Missing Date Handling
- Scenarios 17–21: Procurement Requirements Mathematics & Missing Inputs
- Scenarios 22–25: Project Isolation & Global Material Support
- Scenarios 26–28: Role Authorization (Strict RBAC, PM/Contractor Boundaries)
- Scenarios 29–30: Database Trigger Immutability & Canonical Hash Determinism
"""
import uuid
import hashlib
import json
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
    ActivityScheduleResult,
    MonitoringBaseline,
    MaterialItem,
    MaterialMixDesign,
    MaterialMixConstituent,
    MaterialPlan,
    MaterialRequirementPlan,
    MaterialRequirementItem,
    ProcurementRequirement,
)
from app.core.security import get_password_hash, create_access_token
from app.services.material_requirement_planning_service import _compute_mrp_hash, convert_unit

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
def setup_phase_1o(client_fixture):
    admin_email = f"admin_1o_{uuid.uuid4().hex[:6]}@test.com"
    pm_email = f"pm_1o_{uuid.uuid4().hex[:6]}@test.com"
    sup_email = f"sup_1o_{uuid.uuid4().hex[:6]}@test.com"
    con_email = f"con_1o_{uuid.uuid4().hex[:6]}@test.com"

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
    r1 = client_fixture.post("/api/projects", json={"name": f"P1O Project 1 {uuid.uuid4().hex[:6]}"}, headers={"Authorization": f"Bearer {admin_token}"})
    p1_id = r1.json()["id"]

    r2 = client_fixture.post("/api/projects", json={"name": f"P1O Project 2 {uuid.uuid4().hex[:6]}"}, headers={"Authorization": f"Bearer {admin_token}"})
    p2_id = r2.json()["id"]

    db = TestingSessionLocal()
    u_adm = db.query(User).filter(User.email == admin_email).first()
    u_pm = db.query(User).filter(User.email == pm_email).first()
    u_sup = db.query(User).filter(User.email == sup_email).first()
    u_con = db.query(User).filter(User.email == con_email).first()

    db.add(ProjectMember(project_id=p1_id, user_id=u_pm.id))
    db.add(ProjectMember(project_id=p1_id, user_id=u_sup.id))
    db.add(ProjectMember(project_id=p1_id, user_id=u_con.id))
    db.add(ProjectMember(project_id=p2_id, user_id=u_sup.id))
    db.commit()

    # Materials for P1
    cement = MaterialItem(
        project_id=p1_id,
        material_code=f"OPC-53-{uuid.uuid4().hex[:4]}",
        material_name="Ordinary Portland Cement 53 Grade",
        material_category="BINDER",
        standard_unit="BAG",
        standard_permissible_waste_pct=Decimal("2.50"),
    )
    sand = MaterialItem(
        project_id=p1_id,
        material_code=f"SAND-{uuid.uuid4().hex[:4]}",
        material_name="River Sand Zone II",
        material_category="AGGREGATE",
        standard_unit="M3",
        standard_permissible_waste_pct=Decimal("3.00"),
    )
    steel = MaterialItem(
        project_id=p1_id,
        material_code=f"REBAR-{uuid.uuid4().hex[:4]}",
        material_name="TMT Fe500D 16mm",
        material_category="REINFORCEMENT",
        standard_unit="MT",
        standard_permissible_waste_pct=Decimal("1.50"),
    )
    db.add_all([cement, sand, steel])
    db.commit()

    # Construction Schedule & Activity for P1
    sched = ConstructionSchedule(
        project_id=p1_id,
        schedule_version="1.0",
        calculation_status="CALCULATED",
        calculated_by=u_adm.id,
        algorithm_version="CPM_1.0",
        input_snapshot_json={"version": "1.0"},
    )
    db.add(sched)
    db.commit()

    elem = EngineeringElement(
        project_id=p1_id,
        element_type="COLUMN",
        element_name="C1 Columns",
        created_by=u_adm.id,
    )
    db.add(elem)
    db.commit()

    act1 = ConstructionActivity(
        project_id=p1_id,
        engineering_element_id=elem.id,
        activity_code=f"ACT-CONC-{uuid.uuid4().hex[:4]}",
        activity_name="Column Concreting M25",
        activity_type="CONSTRUCTION",
        created_by=u_adm.id,
        status="ACTIVE",
        metadata_json={"planned_quantity": "100.0000"},
    )
    act2 = ConstructionActivity(
        project_id=p1_id,
        engineering_element_id=elem.id,
        activity_code=f"ACT-REBAR-{uuid.uuid4().hex[:4]}",
        activity_name="Column Reinforcement",
        activity_type="CONSTRUCTION",
        created_by=u_adm.id,
        status="ACTIVE",
        metadata_json={"planned_quantity": "50.0000"},
    )
    db.add_all([act1, act2])
    db.commit()

    # Schedule results: act1 (es=0, ef=10), act2 (es=10, ef=20)
    sr1 = ActivityScheduleResult(
        schedule_id=sched.id,
        activity_id=act1.id,
        es=Decimal("0.0"),
        ef=Decimal("10.0"),
        ls=Decimal("0.0"),
        lf=Decimal("10.0"),
        total_float=Decimal("0.0"),
        is_critical=True,
    )
    sr2 = ActivityScheduleResult(
        schedule_id=sched.id,
        activity_id=act2.id,
        es=Decimal("10.0"),
        ef=Decimal("20.0"),
        ls=Decimal("10.0"),
        lf=Decimal("20.0"),
        total_float=Decimal("0.0"),
        is_critical=True,
    )
    db.add_all([sr1, sr2])
    db.commit()

    # Monitoring Baseline for P1
    base_date = date(2026, 9, 1)
    baseline = MonitoringBaseline(
        project_id=p1_id,
        schedule_id=sched.id,
        schedule_version="1.0",
        schedule_algorithm_version="CPM_1.0",
        baseline_start_date=base_date,
        frozen_by=u_adm.id,
        status="ACTIVE",
    )
    db.add(baseline)
    db.commit()

    # Mix Design for P1
    mix = MaterialMixDesign(
        project_id=p1_id,
        mix_code=f"NOM-M25-{uuid.uuid4().hex[:4]}",
        grade_designation="M25",
        mix_type="NOMINAL_MIX",
        rule_code="IS456-M25",
        classification="ASSUMPTION_BASED",
        status="APPROVED",
        approved_by=u_adm.id,
        approved_at=datetime.now(timezone.utc),
    )
    db.add(mix)
    db.commit()

    const1 = MaterialMixConstituent(
        mix_design_id=mix.id,
        material_item_id=cement.id,
        quantity_per_m3=Decimal("8.2000"),
        unit="BAG",
    )
    const2 = MaterialMixConstituent(
        mix_design_id=mix.id,
        material_item_id=sand.id,
        quantity_per_m3=Decimal("0.4500"),
        unit="M3",
    )
    db.add_all([const1, const2])
    db.commit()

    # Phase 1N Material Plans for P1
    # 1. Cement for act1: net = 100 * 8.2 = 820 BAG, gross = 820 * 1.025 = 840.50 BAG
    mp1 = MaterialPlan(
        project_id=p1_id,
        baseline_id=baseline.id,
        material_item_id=cement.id,
        activity_id=act1.id,
        mix_design_id=mix.id,
        planned_quantity=Decimal("820.0000"),
        unit="BAG",
        estimation_method="CALCULATED",
        waste_allowance_pct=Decimal("2.50"),
        gross_planned_quantity=Decimal("840.5000"),
        provenance_metadata={"activity_code": act1.activity_code, "mix_code": mix.mix_code},
        status="ACTIVE",
    )
    # 2. Sand for act1: net = 100 * 0.45 = 45 M3, gross = 45 * 1.03 = 46.35 M3
    mp2 = MaterialPlan(
        project_id=p1_id,
        baseline_id=baseline.id,
        material_item_id=sand.id,
        activity_id=act1.id,
        mix_design_id=mix.id,
        planned_quantity=Decimal("45.0000"),
        unit="M3",
        estimation_method="CALCULATED",
        waste_allowance_pct=Decimal("3.00"),
        gross_planned_quantity=Decimal("46.3500"),
        provenance_metadata={"activity_code": act1.activity_code, "mix_code": mix.mix_code},
        status="ACTIVE",
    )
    # 3. Steel for act2: net = 50 * 0.1 = 5 MT, gross = 5 * 1.015 = 5.075 MT
    mp3 = MaterialPlan(
        project_id=p1_id,
        baseline_id=baseline.id,
        material_item_id=steel.id,
        activity_id=act2.id,
        mix_design_id=mix.id,
        planned_quantity=Decimal("5.0000"),
        unit="MT",
        estimation_method="CALCULATED",
        waste_allowance_pct=Decimal("1.50"),
        gross_planned_quantity=Decimal("5.0750"),
        provenance_metadata={"activity_code": act2.activity_code},
        status="ACTIVE",
    )
    db.add_all([mp1, mp2, mp3])
    db.commit()

    ret = {
        "admin_token": admin_token,
        "pm_token": pm_token,
        "sup_token": sup_token,
        "con_token": con_token,
        "u_adm_id": u_adm.id,
        "p1_id": p1_id,
        "p2_id": p2_id,
        "baseline_id": baseline.id,
        "sched_id": sched.id,
        "act1_id": act1.id,
        "act2_id": act2.id,
        "cement_id": cement.id,
        "sand_id": sand.id,
        "steel_id": steel.id,
        "mp1_id": mp1.id,
        "mp2_id": mp2.id,
        "mp3_id": mp3.id,
        "base_date": base_date,
    }
    db.close()
    return ret


def test_01_to_06_plan_creation_uniqueness_and_lifecycle(client_fixture, setup_phase_1o):
    p1 = setup_phase_1o["p1_id"]
    token = setup_phase_1o["sup_token"]
    baseline_id = setup_phase_1o["baseline_id"]

    # Scenario 1: Create DRAFT plan
    r = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans",
        json={"baseline_id": baseline_id, "plan_version": "v1.0"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    plan1 = r.json()
    assert plan1["status"] == "DRAFT"
    assert plan1["algorithm_version"] == "MRP_1.0"
    assert plan1["plan_version"] == "v1.0"
    plan1_id = plan1["id"]

    # Scenario 2: Duplicate version within same project rejected with 409
    r_dup = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans",
        json={"baseline_id": baseline_id, "plan_version": "v1.0"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_dup.status_code == 409

    # Generate items for plan1
    r_gen = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan1_id}/generate",
        json={"quantity_source": "GROSS"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_gen.status_code == 200
    assert len(r_gen.json()) == 3

    # Scenario 3: Plan activation transitions DRAFT -> ACTIVE
    r_act = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan1_id}/activate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_act.status_code == 200
    assert r_act.json()["status"] == "ACTIVE"

    # Scenario 4: Activating a second plan sets previous active plan to SUPERSEDED
    r_p2 = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans",
        json={"baseline_id": baseline_id, "plan_version": "v2.0"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_p2.status_code == 201
    plan2_id = r_p2.json()["id"]

    client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan2_id}/generate",
        json={"quantity_source": "GROSS"},
        headers={"Authorization": f"Bearer {token}"},
    )
    r_act2 = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan2_id}/activate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_act2.status_code == 200
    assert r_act2.json()["status"] == "ACTIVE"

    # Verify plan1 became SUPERSEDED
    r_p1_check = client_fixture.get(
        f"/api/projects/{p1}/material-requirement-plans/{plan1_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_p1_check.json()["status"] == "SUPERSEDED"
    assert r_p1_check.json()["superseded_at"] is not None

    # Scenario 5: Supersede plan2 directly via endpoint
    r_sup = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan2_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_sup.status_code == 200
    assert r_sup.json()["status"] == "SUPERSEDED"

    # Scenario 6: Invalid lifecycle transitions rejected
    # Cannot activate an already SUPERSEDED plan
    r_re_act = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan2_id}/activate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_re_act.status_code == 422

    # Cannot supersede a DRAFT plan
    r_draft = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans",
        json={"baseline_id": baseline_id, "plan_version": "v3.0"},
        headers={"Authorization": f"Bearer {token}"},
    )
    plan3_id = r_draft.json()["id"]
    r_sup_draft = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan3_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_sup_draft.status_code == 422


def test_07_to_11_material_plan_lineage_and_quantity_provenance(client_fixture, setup_phase_1o):
    p1 = setup_phase_1o["p1_id"]
    token = setup_phase_1o["sup_token"]
    baseline_id = setup_phase_1o["baseline_id"]
    base_date = setup_phase_1o["base_date"]

    r = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans",
        json={"baseline_id": baseline_id, "plan_version": f"v-lineage-{uuid.uuid4().hex[:4]}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    plan_id = r.json()["id"]

    # Scenario 7 & 8: GROSS quantity provenance
    r_gen = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id}/generate",
        json={"quantity_source": "GROSS"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_gen.status_code == 200
    items = r_gen.json()
    assert len(items) == 3

    cement_item = next(it for it in items if it["material_item_id"] == setup_phase_1o["cement_id"])
    assert Decimal(str(cement_item["requirement_quantity"])) == Decimal("840.5000")
    assert cement_item["requirement_unit"] == "BAG"
    assert cement_item["provenance_metadata"]["quantity_source"] == "GROSS"
    assert cement_item["provenance_metadata"]["net_planned_quantity"] == "820.0000"
    assert cement_item["provenance_metadata"]["waste_allowance_pct"] == "2.50"
    assert cement_item["classification"] == "CALCULATED"
    assert cement_item["status"] == "PLANNED"

    # Scenario 10 & 11: Schedule dates derivation
    # Act1 (cement & sand) has es=0, ef=10 => start = 2026-09-01, end = 2026-09-11
    assert cement_item["requirement_date_start"] == base_date.isoformat()
    assert cement_item["requirement_date_end"] == (base_date + timedelta(days=10)).isoformat()

    steel_item = next(it for it in items if it["material_item_id"] == setup_phase_1o["steel_id"])
    # Act2 (steel) has es=10, ef=20 => start = 2026-09-11, end = 2026-09-21
    assert steel_item["requirement_date_start"] == (base_date + timedelta(days=10)).isoformat()
    assert steel_item["requirement_date_end"] == (base_date + timedelta(days=20)).isoformat()

    # Scenario 9: NET quantity provenance
    r_net = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id}/generate",
        json={"quantity_source": "NET"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_net.status_code == 200
    items_net = r_net.json()
    cement_net = next(it for it in items_net if it["material_item_id"] == setup_phase_1o["cement_id"])
    assert Decimal(str(cement_net["requirement_quantity"])) == Decimal("820.0000")
    assert cement_net["provenance_metadata"]["quantity_source"] == "NET"


def test_12_to_16_unit_compatibility_and_conversions(client_fixture, setup_phase_1o):
    p1 = setup_phase_1o["p1_id"]
    token = setup_phase_1o["sup_token"]
    baseline_id = setup_phase_1o["baseline_id"]

    # Scenario 12: Supported conversion TONNE -> KG
    r = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans",
        json={"baseline_id": baseline_id, "plan_version": f"v-unit-{uuid.uuid4().hex[:4]}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    plan_id = r.json()["id"]

    # Target unit KG: steel was 5.075 TONNE => 5075 KG
    r_conv = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id}/generate",
        json={"quantity_source": "GROSS", "target_unit": "KG"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_conv.status_code == 200
    items = r_conv.json()

    steel_item = next(it for it in items if it["material_item_id"] == setup_phase_1o["steel_id"])
    assert Decimal(str(steel_item["requirement_quantity"])) == Decimal("5075.0000")
    assert steel_item["requirement_unit"] == "KG"
    assert Decimal(str(steel_item["conversion_factor"])) == Decimal("1000.000000")
    assert steel_item["classification"] == "CALCULATED"

    # Scenario 14: Unsupported conversion (cement was BAG, target unit KG) => REQUIRES_INPUT
    cement_item = next(it for it in items if it["material_item_id"] == setup_phase_1o["cement_id"])
    assert cement_item["requirement_unit"] == "BAG"  # kept original unit
    assert cement_item["classification"] == "REQUIRES_INPUT"
    assert cement_item["status"] == "REQUIRES_INPUT"

    # Scenario 13: Unit conversion function direct checks
    qty, factor, ok = convert_unit(Decimal("10.0"), "M", "CM")
    assert ok is True and qty == Decimal("1000.0") and factor == Decimal("100.000000")

    qty, factor, ok = convert_unit(Decimal("500.0"), "MM", "M")
    assert ok is True and qty == Decimal("0.500") and factor == Decimal("0.001000")

    qty, factor, ok = convert_unit(Decimal("10.0"), "BAG", "KG")
    assert ok is False

    # Scenario 15: Missing baseline start date => dates are None, REQUIRES_INPUT
    p2 = setup_phase_1o["p2_id"]
    with TestingSessionLocal() as db:
        sched2 = ConstructionSchedule(
            project_id=p2,
            schedule_version="1.0",
            calculation_status="CALCULATED",
            calculated_by=setup_phase_1o["u_adm_id"],
            algorithm_version="CPM_1.0",
            input_snapshot_json={"version": "1.0"},
        )
        db.add(sched2)
        db.commit()

        base_nodate = MonitoringBaseline(
            project_id=p2,
            schedule_id=sched2.id,
            schedule_version="1.0",
            schedule_algorithm_version="CPM_1.0",
            baseline_start_date=None,  # No date!
            frozen_by=setup_phase_1o["u_adm_id"],
            status="ACTIVE",
        )
        db.add(base_nodate)
        db.commit()
        nodate_id = base_nodate.id

        elem2 = EngineeringElement(
            project_id=p2,
            element_type="COLUMN",
            element_name="P2 Column",
            created_by=setup_phase_1o["u_adm_id"],
        )
        db.add(elem2)
        db.commit()

        act_p2 = ConstructionActivity(
            project_id=p2,
            engineering_element_id=elem2.id,
            activity_code=f"ACT-P2-{uuid.uuid4().hex[:4]}",
            activity_name="P2 Concreting",
            activity_type="CONSTRUCTION",
            created_by=setup_phase_1o["u_adm_id"],
            status="ACTIVE",
        )
        db.add(act_p2)
        db.commit()

        mat_p2 = MaterialItem(
            project_id=p2,
            material_code=f"P2-MAT-{uuid.uuid4().hex[:4]}",
            material_name="P2 Material",
            material_category="BINDER",
            standard_unit="BAG",
        )
        db.add(mat_p2)
        db.commit()

        mix_p2 = MaterialMixDesign(
            project_id=p2,
            mix_code=f"NOM-P2-{uuid.uuid4().hex[:4]}",
            grade_designation="M20",
            mix_type="NOMINAL_MIX",
            rule_code="IS456-M20",
            classification="ASSUMPTION_BASED",
            status="APPROVED",
            approved_by=setup_phase_1o["u_adm_id"],
            approved_at=datetime.now(timezone.utc),
        )
        db.add(mix_p2)
        db.commit()

        mp_p2 = MaterialPlan(
            project_id=p2,
            baseline_id=nodate_id,
            material_item_id=mat_p2.id,
            activity_id=act_p2.id,
            mix_design_id=mix_p2.id,
            planned_quantity=Decimal("100.0000"),
            unit="BAG",
            estimation_method="CALCULATED",
            waste_allowance_pct=Decimal("0.00"),
            gross_planned_quantity=Decimal("100.0000"),
            provenance_metadata={},
            status="ACTIVE",
        )
        db.add(mp_p2)
        db.commit()

    r_nodate_plan = client_fixture.post(
        f"/api/projects/{p2}/material-requirement-plans",
        json={"baseline_id": nodate_id, "plan_version": f"v-nodate-{uuid.uuid4().hex[:4]}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_nodate_plan.status_code == 201
    nodate_plan_id = r_nodate_plan.json()["id"]

    r_nodate_gen = client_fixture.post(
        f"/api/projects/{p2}/material-requirement-plans/{nodate_plan_id}/generate",
        json={"quantity_source": "GROSS"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_nodate_gen.status_code == 200
    nodate_item = r_nodate_gen.json()[0]
    assert nodate_item["requirement_date_start"] is None
    assert nodate_item["requirement_date_end"] is None
    assert nodate_item["classification"] == "REQUIRES_INPUT"

    # Scenario 16: Negative quantity rejection
    r_neg = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id}/generate",
        json={"quantity_source": "INVALID_SOURCE"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_neg.status_code == 422


def test_17_to_21_procurement_requirements_mathematics_and_inputs(client_fixture, setup_phase_1o):
    p1 = setup_phase_1o["p1_id"]
    token = setup_phase_1o["sup_token"]
    baseline_id = setup_phase_1o["baseline_id"]
    cement_id = setup_phase_1o["cement_id"]
    sand_id = setup_phase_1o["sand_id"]

    r = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans",
        json={"baseline_id": baseline_id, "plan_version": f"v-proc-{uuid.uuid4().hex[:4]}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    plan_id = r.json()["id"]

    client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id}/generate",
        json={"quantity_source": "GROSS"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Scenario 18: Generate procurement requirements without already_planned_quantity input
    # Must NOT assume zero! Return REQUIRES_INPUT status and procurement_quantity=None
    r_pr_noinput = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id}/procurement-requirements",
        json={"inputs": []},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_pr_noinput.status_code == 200
    proc_reqs = r_pr_noinput.json()
    assert len(proc_reqs) == 3

    cement_pr = next(pr for pr in proc_reqs if pr["material_item_id"] == cement_id)
    assert Decimal(str(cement_pr["required_quantity"])) == Decimal("840.5000")
    assert cement_pr["already_planned_quantity"] is None
    assert cement_pr["procurement_quantity"] is None
    assert cement_pr["status"] == "REQUIRES_INPUT"

    # Scenario 19: Explicit already_planned_quantity input provided
    # cement required: 840.50, already_planned: 340.50 => procurement_quantity = 500.00
    # sand required: 46.35, already_planned: 50.00 => procurement_quantity = max(0, 46.35 - 50.00) = 0.00 (Scenario 20)
    r_pr_input = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id}/procurement-requirements",
        json={
            "inputs": [
                {"material_item_id": cement_id, "already_planned_quantity": "340.5000"},
                {"material_item_id": sand_id, "already_planned_quantity": "50.0000"},
            ]
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_pr_input.status_code == 200
    proc_reqs2 = r_pr_input.json()

    cement_pr2 = next(pr for pr in proc_reqs2 if pr["material_item_id"] == cement_id)
    assert Decimal(str(cement_pr2["procurement_quantity"])) == Decimal("500.0000")
    assert Decimal(str(cement_pr2["already_planned_quantity"])) == Decimal("340.5000")
    assert cement_pr2["status"] == "PLANNED"

    # Scenario 20: No negative procurement quantity
    sand_pr2 = next(pr for pr in proc_reqs2 if pr["material_item_id"] == sand_id)
    assert Decimal(str(sand_pr2["procurement_quantity"])) == Decimal("0.0000")
    assert sand_pr2["status"] == "PLANNED"

    # Scenario 21: Negative already_planned_quantity rejected with 422
    r_neg = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id}/procurement-requirements",
        json={"inputs": [{"material_item_id": cement_id, "already_planned_quantity": "-10.0000"}]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_neg.status_code == 422


def test_22_to_25_project_isolation_and_global_materials(client_fixture, setup_phase_1o):
    p1 = setup_phase_1o["p1_id"]
    p2 = setup_phase_1o["p2_id"]
    token = setup_phase_1o["sup_token"]

    # Scenario 22: Global material support
    with TestingSessionLocal() as db:
        g_mat = MaterialItem(
            project_id=None,  # Global
            material_code=f"GLOB-TIMBER-{uuid.uuid4().hex[:4]}",
            material_name="Formwork Timber",
            material_category="TIMBER",
            standard_unit="M3",
            standard_permissible_waste_pct=Decimal("5.00"),
        )
        db.add(g_mat)
        db.commit()
        g_mat_id = g_mat.id

        # Attach global material to P1 MaterialPlan
        mp_glob = MaterialPlan(
            project_id=p1,
            baseline_id=setup_phase_1o["baseline_id"],
            material_item_id=g_mat_id,
            activity_id=setup_phase_1o["act1_id"],
            mix_design_id=db.query(MaterialMixDesign).filter(MaterialMixDesign.project_id == p1).first().id,
            planned_quantity=Decimal("10.0000"),
            unit="M3",
            estimation_method="CALCULATED",
            waste_allowance_pct=Decimal("5.00"),
            gross_planned_quantity=Decimal("10.5000"),
            provenance_metadata={},
            status="ACTIVE",
        )
        db.add(mp_glob)
        db.commit()

    r = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans",
        json={"baseline_id": setup_phase_1o["baseline_id"], "plan_version": f"v-glob-{uuid.uuid4().hex[:4]}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    plan_glob_id = r.json()["id"]

    r_gen = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_glob_id}/generate",
        json={"quantity_source": "GROSS"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_gen.status_code == 200
    # Verified global material accepted
    assert any(it["material_item_id"] == g_mat_id for it in r_gen.json())

    # Scenario 23, 24, 25: Cross-project baseline / access rejection
    # Attempt to create plan in P2 using P1 baseline
    r_cross_base = client_fixture.post(
        f"/api/projects/{p2}/material-requirement-plans",
        json={"baseline_id": setup_phase_1o["baseline_id"], "plan_version": "v-cross-1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_cross_base.status_code == 422


def test_26_to_28_role_authorization_and_contractor_restrictions(client_fixture, setup_phase_1o):
    p1 = setup_phase_1o["p1_id"]
    pm_token = setup_phase_1o["pm_token"]
    con_token = setup_phase_1o["con_token"]
    sup_token = setup_phase_1o["sup_token"]
    adm_token = setup_phase_1o["admin_token"]
    baseline_id = setup_phase_1o["baseline_id"]

    # Scenario 26: project_manager completely rejected with 403
    r_pm = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans",
        json={"baseline_id": baseline_id, "plan_version": "v-pm-fail"},
        headers={"Authorization": f"Bearer {pm_token}"},
    )
    assert r_pm.status_code == 403

    # Scenario 27: contractor cannot create plans, generate items, activate, or supersede
    r_con_create = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans",
        json={"baseline_id": baseline_id, "plan_version": "v-con-fail"},
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert r_con_create.status_code == 403

    # Create plan via admin
    r_adm = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans",
        json={"baseline_id": baseline_id, "plan_version": f"v-auth-{uuid.uuid4().hex[:4]}"},
        headers={"Authorization": f"Bearer {adm_token}"},
    )
    assert r_adm.status_code == 201
    plan_id = r_adm.json()["id"]

    # Contractor cannot generate items (Scenario 27)
    r_con_gen = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id}/generate",
        json={"quantity_source": "GROSS"},
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert r_con_gen.status_code == 403

    # Generate via supervisor
    client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id}/generate",
        json={"quantity_source": "GROSS"},
        headers={"Authorization": f"Bearer {sup_token}"},
    )

    # Scenario 28: contractor CAN submit procurement inputs
    r_con_proc = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id}/procurement-requirements",
        json={"inputs": [{"material_item_id": setup_phase_1o["cement_id"], "already_planned_quantity": "100.00"}]},
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert r_con_proc.status_code == 200

    # Contractor CAN view plans and items
    r_con_view = client_fixture.get(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id}/items",
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert r_con_view.status_code == 200

    # Contractor CANNOT activate plan
    r_con_act = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id}/activate",
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert r_con_act.status_code == 403


def test_29_to_30_immutability_triggers_and_hash_determinism(client_fixture, setup_phase_1o):
    p1 = setup_phase_1o["p1_id"]
    token = setup_phase_1o["admin_token"]
    baseline_id = setup_phase_1o["baseline_id"]

    # Create and activate plan
    r = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans",
        json={"baseline_id": baseline_id, "plan_version": f"v-immut-{uuid.uuid4().hex[:4]}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    plan_id = r.json()["id"]

    client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id}/generate",
        json={"quantity_source": "GROSS"},
        headers={"Authorization": f"Bearer {token}"},
    )
    client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id}/procurement-requirements",
        json={"inputs": [{"material_item_id": setup_phase_1o["cement_id"], "already_planned_quantity": "200.00"}]},
        headers={"Authorization": f"Bearer {token}"},
    )
    client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id}/activate",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Scenario 29: Database trigger immutability
    # Direct DB delete on ACTIVE plan fails
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc_info:
            db.execute(text(f"DELETE FROM material_requirement_plans WHERE id = '{plan_id}'"))
            db.commit()
        db.rollback()
        assert "ACTIVE MaterialRequirementPlan" in str(exc_info.value)

    # Direct DB item modification on ACTIVE plan fails
    with TestingSessionLocal() as db:
        item = db.query(MaterialRequirementItem).filter(MaterialRequirementItem.material_requirement_plan_id == plan_id).first()
        with pytest.raises(Exception) as exc_info:
            db.execute(text(f"UPDATE material_requirement_items SET requirement_quantity = 999 WHERE id = '{item.id}'"))
            db.commit()
        db.rollback()
        assert "Cannot modify or delete material requirement items" in str(exc_info.value)

    # Direct DB procurement requirement delete on ACTIVE plan fails
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc_info:
            db.execute(text(f"DELETE FROM procurement_requirements WHERE material_requirement_plan_id = '{plan_id}'"))
            db.commit()
        db.rollback()
        assert "Cannot modify or delete procurement requirements" in str(exc_info.value)

    # Supersede plan
    client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Direct DB update on SUPERSEDED plan fails
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc_info:
            db.execute(text(f"UPDATE material_requirement_plans SET metadata_json = '{{\"foo\": \"bar\"}}' WHERE id = '{plan_id}'"))
            db.commit()
        db.rollback()
        assert "Historical SUPERSEDED MaterialRequirementPlan" in str(exc_info.value)

    # Scenario 30: Canonical hash determinism
    with TestingSessionLocal() as db:
        items = db.query(MaterialRequirementItem).filter(MaterialRequirementItem.material_requirement_plan_id == plan_id).all()
        h1 = _compute_mrp_hash(plan_id, p1, baseline_id, "v1", items)
        h2 = _compute_mrp_hash(plan_id, p1, baseline_id, "v1", items)
        assert h1 == h2
        assert len(h1) == 64

        h3 = _compute_mrp_hash(plan_id, p1, baseline_id, "v2", items)
        assert h1 != h3


def test_hardening_01_cross_project_procurement_inputs(client_fixture, setup_phase_1o):
    p1 = setup_phase_1o["p1_id"]
    p2 = setup_phase_1o["p2_id"]
    token = setup_phase_1o["sup_token"]
    baseline_id = setup_phase_1o["baseline_id"]

    # Create material in P2
    with TestingSessionLocal() as db:
        p2_mat = MaterialItem(
            project_id=p2,
            material_code=f"P2-MAT-ISOL-{uuid.uuid4().hex[:4]}",
            material_name="P2 Isolated Material",
            material_category="AGGREGATE",
            standard_unit="M3",
        )
        db.add(p2_mat)
        db.commit()
        p2_mat_id = p2_mat.id

    r_plan = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans",
        json={"baseline_id": baseline_id, "plan_version": f"v-hard-p1-{uuid.uuid4().hex[:4]}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    plan_id = r_plan.json()["id"]

    client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id}/generate",
        json={"quantity_source": "GROSS"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Submitting P2 material in P1 procurement input must fail with 422
    r_cross_inp = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id}/procurement-requirements",
        json={"inputs": [{"material_item_id": p2_mat_id, "already_planned_quantity": "50.00"}]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_cross_inp.status_code == 422
    assert "not part of requirement plan" in r_cross_inp.json()["detail"]


def test_hardening_02_pm_rejected_on_all_endpoints(client_fixture, setup_phase_1o):
    p1 = setup_phase_1o["p1_id"]
    pm_token = setup_phase_1o["pm_token"]
    sup_token = setup_phase_1o["sup_token"]
    baseline_id = setup_phase_1o["baseline_id"]

    # 1. POST create plan
    r = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans",
        json={"baseline_id": baseline_id, "plan_version": f"v-pm-{uuid.uuid4().hex[:4]}"},
        headers={"Authorization": f"Bearer {pm_token}"},
    )
    assert r.status_code == 403

    # Create plan via supervisor
    r_ok = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans",
        json={"baseline_id": baseline_id, "plan_version": f"v-pm-view-{uuid.uuid4().hex[:4]}"},
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    plan_id = r_ok.json()["id"]

    # 2. GET plans
    assert client_fixture.get(f"/api/projects/{p1}/material-requirement-plans", headers={"Authorization": f"Bearer {pm_token}"}).status_code == 403

    # 3. GET plan
    assert client_fixture.get(f"/api/projects/{p1}/material-requirement-plans/{plan_id}", headers={"Authorization": f"Bearer {pm_token}"}).status_code == 403

    # 4. POST generate items
    assert client_fixture.post(f"/api/projects/{p1}/material-requirement-plans/{plan_id}/generate", json={"quantity_source": "GROSS"}, headers={"Authorization": f"Bearer {pm_token}"}).status_code == 403

    # Generate items via supervisor
    client_fixture.post(f"/api/projects/{p1}/material-requirement-plans/{plan_id}/generate", json={"quantity_source": "GROSS"}, headers={"Authorization": f"Bearer {sup_token}"})

    # 5. GET items
    assert client_fixture.get(f"/api/projects/{p1}/material-requirement-plans/{plan_id}/items", headers={"Authorization": f"Bearer {pm_token}"}).status_code == 403

    # 6. POST procurement requirements
    assert client_fixture.post(f"/api/projects/{p1}/material-requirement-plans/{plan_id}/procurement-requirements", json={"inputs": []}, headers={"Authorization": f"Bearer {pm_token}"}).status_code == 403

    # 7. GET procurement requirements
    assert client_fixture.get(f"/api/projects/{p1}/material-requirement-plans/{plan_id}/procurement-requirements", headers={"Authorization": f"Bearer {pm_token}"}).status_code == 403

    # 8. POST activate
    assert client_fixture.post(f"/api/projects/{p1}/material-requirement-plans/{plan_id}/activate", headers={"Authorization": f"Bearer {pm_token}"}).status_code == 403

    # 9. POST supersede
    assert client_fixture.post(f"/api/projects/{p1}/material-requirement-plans/{plan_id}/supersede", headers={"Authorization": f"Bearer {pm_token}"}).status_code == 403


def test_hardening_03_site_supervisor_parity_with_supervisor(client_fixture, setup_phase_1o):
    p1 = setup_phase_1o["p1_id"]
    sup_token = setup_phase_1o["sup_token"]  # role = site_supervisor
    baseline_id = setup_phase_1o["baseline_id"]

    # Create a user with explicit role = 'supervisor'
    with TestingSessionLocal() as db:
        sup_pure = User(
            email=f"pure_sup_{uuid.uuid4().hex[:6]}@test.com",
            password_hash=get_password_hash("p"),
            role="supervisor",
        )
        db.add(sup_pure)
        db.commit()
        db.add(ProjectMember(project_id=p1, user_id=sup_pure.id))
        db.commit()
        pure_sup_email = sup_pure.email

    pure_sup_token = create_access_token(data={"sub": pure_sup_email, "role": "supervisor"})

    # Both site_supervisor and supervisor can create, generate, activate, supersede
    r1 = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans",
        json={"baseline_id": baseline_id, "plan_version": f"v-pure-sup-{uuid.uuid4().hex[:4]}"},
        headers={"Authorization": f"Bearer {pure_sup_token}"},
    )
    assert r1.status_code == 201
    plan_id1 = r1.json()["id"]

    r2 = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id1}/generate",
        json={"quantity_source": "GROSS"},
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert r2.status_code == 200

    r3 = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id1}/activate",
        headers={"Authorization": f"Bearer {pure_sup_token}"},
    )
    assert r3.status_code == 200
    assert r3.json()["status"] == "ACTIVE"


def test_hardening_04_schema_validation_empty_values(client_fixture, setup_phase_1o):
    p1 = setup_phase_1o["p1_id"]
    token = setup_phase_1o["sup_token"]
    baseline_id = setup_phase_1o["baseline_id"]

    # Empty plan_version
    r_empty_ver = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans",
        json={"baseline_id": baseline_id, "plan_version": "   "},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_empty_ver.status_code == 422

    # Empty baseline_id
    r_empty_base = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans",
        json={"baseline_id": "   ", "plan_version": "v-valid"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_empty_base.status_code == 422

    # Valid plan for item checks
    r_ok = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans",
        json={"baseline_id": baseline_id, "plan_version": f"v-schema-check-{uuid.uuid4().hex[:4]}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    plan_id = r_ok.json()["id"]

    # Invalid quantity_source
    r_bad_source = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans/{plan_id}/generate",
        json={"quantity_source": "INVALID_QUANTITY_SOURCE"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_bad_source.status_code == 422


def test_hardening_05_hash_mutation_detection():
    # 1. Deterministic inputs
    class DummyItem:
        def __init__(self, mp_id, mat_id, act_id, req_qty, req_u, src_qty, src_u, conv):
            self.material_plan_id = mp_id
            self.material_item_id = mat_id
            self.activity_id = act_id
            self.requirement_quantity = Decimal(str(req_qty))
            self.requirement_unit = req_u
            self.source_quantity = Decimal(str(src_qty))
            self.source_unit = src_u
            self.conversion_factor = Decimal(str(conv))

    it1 = DummyItem("mp-1", "mat-1", "act-1", "100.0000", "BAG", "100.0000", "BAG", "1.000000")
    it2 = DummyItem("mp-2", "mat-2", "act-2", "50.0000", "M3", "50.0000", "M3", "1.000000")

    h_original = _compute_mrp_hash("p1", "proj1", "base1", "v1", [it1, it2])
    # Reversed list order must produce IDENTICAL hash
    h_reversed = _compute_mrp_hash("p1", "proj1", "base1", "v1", [it2, it1])
    assert h_original == h_reversed

    # Changing requirement quantity must produce DIFFERENT hash
    it1_mutated = DummyItem("mp-1", "mat-1", "act-1", "105.0000", "BAG", "100.0000", "BAG", "1.000000")
    h_mutated_qty = _compute_mrp_hash("p1", "proj1", "base1", "v1", [it1_mutated, it2])
    assert h_original != h_mutated_qty

    # Changing source material plan must produce DIFFERENT hash
    it1_mutated_mp = DummyItem("mp-999", "mat-1", "act-1", "100.0000", "BAG", "100.0000", "BAG", "1.000000")
    h_mutated_mp = _compute_mrp_hash("p1", "proj1", "base1", "v1", [it1_mutated_mp, it2])
    assert h_original != h_mutated_mp


def test_hardening_06_concurrent_activation_atomic_guarantee(client_fixture, setup_phase_1o):
    p1 = setup_phase_1o["p1_id"]
    token = setup_phase_1o["sup_token"]
    baseline_id = setup_phase_1o["baseline_id"]

    # Create plan A
    r_a = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans",
        json={"baseline_id": baseline_id, "plan_version": f"v-conc-a-{uuid.uuid4().hex[:4]}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    plan_a_id = r_a.json()["id"]
    client_fixture.post(f"/api/projects/{p1}/material-requirement-plans/{plan_a_id}/generate", json={"quantity_source": "GROSS"}, headers={"Authorization": f"Bearer {token}"})

    # Create plan B
    r_b = client_fixture.post(
        f"/api/projects/{p1}/material-requirement-plans",
        json={"baseline_id": baseline_id, "plan_version": f"v-conc-b-{uuid.uuid4().hex[:4]}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    plan_b_id = r_b.json()["id"]
    client_fixture.post(f"/api/projects/{p1}/material-requirement-plans/{plan_b_id}/generate", json={"quantity_source": "GROSS"}, headers={"Authorization": f"Bearer {token}"})

    # Activate Plan A
    r_act_a = client_fixture.post(f"/api/projects/{p1}/material-requirement-plans/{plan_a_id}/activate", headers={"Authorization": f"Bearer {token}"})
    assert r_act_a.status_code == 200

    # Activate Plan B
    r_act_b = client_fixture.post(f"/api/projects/{p1}/material-requirement-plans/{plan_b_id}/activate", headers={"Authorization": f"Bearer {token}"})
    assert r_act_b.status_code == 200

    # Verify at direct database level that exactly ONE plan is ACTIVE for project p1
    with TestingSessionLocal() as db:
        active_plans = db.query(MaterialRequirementPlan).filter(
            MaterialRequirementPlan.project_id == p1,
            MaterialRequirementPlan.status == "ACTIVE",
        ).all()
        assert len(active_plans) == 1
        assert active_plans[0].id == plan_b_id

        superseded_plan_a = db.query(MaterialRequirementPlan).filter(MaterialRequirementPlan.id == plan_a_id).first()
        assert superseded_plan_a.status == "SUPERSEDED"
        assert superseded_plan_a.superseded_at is not None

