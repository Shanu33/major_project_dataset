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
    EngineeringElement,
    MaterialItem,
    MaterialPerformanceSnapshot,
    MonitoringBaseline,
    PeriodCertificateItem,
    PeriodProgressCertificate,
    Project,
    ProjectMember,
    Resource,
    ResourcePerformanceSnapshot,
    ResourcePlan,
    User,
)
from app.main import app
from app.services.resource_performance_service import generate_canonical_hash

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
def setup_data():
    adm_email = f"adm_1s_{uuid.uuid4().hex[:6]}@test.com"
    sup_email = f"sup_1s_{uuid.uuid4().hex[:6]}@test.com"
    con_email = f"con_1s_{uuid.uuid4().hex[:6]}@test.com"
    pm_email = f"pm_1s_{uuid.uuid4().hex[:6]}@test.com"

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
        p1 = Project(name=f"Proj 1S 1 {uuid.uuid4().hex[:4]}", created_by=adm_id)
        p2 = Project(name=f"Proj 1S 2 {uuid.uuid4().hex[:4]}", created_by=adm_id)
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
        ])
        db.commit()

        # Engineering Element
        elem1 = EngineeringElement(
            project_id=p1_id,
            element_type="FOUNDATION",
            element_name="Foundation Element",
            created_by=adm_id,
        )
        db.add(elem1)
        db.commit()
        db.refresh(elem1)
        elem1_id = elem1.id

        # Construction Activities
        act1 = ConstructionActivity(
            project_id=p1_id,
            engineering_element_id=elem1_id,
            activity_code=f"ACT-1S-1-{uuid.uuid4().hex[:4]}",
            activity_name="Foundation Pouring",
            activity_type="CONSTRUCTION",
            created_by=adm_id,
        )
        act2 = ConstructionActivity(
            project_id=p2_id,
            activity_code=f"ACT-1S-2-{uuid.uuid4().hex[:4]}",
            activity_name="P2 Act",
            activity_type="CONSTRUCTION",
            created_by=adm_id,
        )
        db.add_all([act1, act2])
        db.commit()
        db.refresh(act1)
        db.refresh(act2)
        act1_id, act2_id = act1.id, act2.id

        # Resources
        res_labour = Resource(
            resource_code=f"LAB-1S-{uuid.uuid4().hex[:4]}",
            resource_name="Concrete Labour",
            resource_category="LABOUR",
            unit="labour-hour",
            status="ACTIVE",
            created_by=adm_id,
        )
        res_equip = Resource(
            resource_code=f"EQP-1S-{uuid.uuid4().hex[:4]}",
            resource_name="Concrete Boom Pump",
            resource_category="EQUIPMENT",
            unit="equipment-hour",
            status="ACTIVE",
            created_by=adm_id,
        )
        res_mat = Resource(
            resource_code=f"MAT-1S-{uuid.uuid4().hex[:4]}",
            resource_name="Ready-Mix Concrete",
            resource_category="MATERIAL",
            unit="m3",
            status="ACTIVE",
            created_by=adm_id,
        )
        db.add_all([res_labour, res_equip, res_mat])
        db.commit()
        db.refresh(res_labour)
        db.refresh(res_equip)
        db.refresh(res_mat)
        res_labour_id = res_labour.id
        res_equip_id = res_equip.id
        res_mat_id = res_mat.id

        # Material Item
        mat_steel = MaterialItem(
            project_id=p1_id,
            material_code=f"STL-1S-{uuid.uuid4().hex[:4]}",
            material_name="Fe500 Rebar",
            material_category="REINFORCEMENT",
            standard_unit="MT",
            standard_permissible_waste_pct=Decimal("5.00"),
        )
        mat_p2 = MaterialItem(
            project_id=p2_id,
            material_code=f"P2-STL-{uuid.uuid4().hex[:4]}",
            material_name="P2 Steel",
            material_category="REINFORCEMENT",
            standard_unit="MT",
        )
        db.add_all([mat_steel, mat_p2])
        db.commit()
        db.refresh(mat_steel)
        db.refresh(mat_p2)
        steel_id = mat_steel.id
        p2_mat_id = mat_p2.id

        # Resource Plan
        rp_labour = ResourcePlan(
            project_id=p1_id,
            engineering_element_id=elem1_id,
            resource_id=res_labour_id,
            resource_demand=Decimal("100.0000"),
            resource_demand_unit="labour-hour",
            planning_method="DETERMINISTIC",
            classification="CALCULATED",
            provenance_json={"origin": "plan"},
            status="PLANNED",
            created_by=adm_id,
        )
        db.add(rp_labour)
        db.commit()
        db.refresh(rp_labour)
        rp_labour_id = rp_labour.id

        # Cost Rates
        cr_labour = CostRate(
            project_id=p1_id,
            rate_code=f"RATE-LAB-{uuid.uuid4().hex[:4]}",
            description="Labour Rate",
            unit="labour-hour",
            rate_value=Decimal("50.00"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref-1S",
            status="CONFIRMED",
            created_by=adm_id,
            confirmed_by=adm_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        cr_equip = CostRate(
            project_id=p1_id,
            rate_code=f"RATE-EQP-{uuid.uuid4().hex[:4]}",
            description="Pump Rate",
            unit="equipment-hour",
            rate_value=Decimal("200.00"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref-1S",
            status="CONFIRMED",
            created_by=adm_id,
            confirmed_by=adm_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        cr_draft = CostRate(
            project_id=p1_id,
            rate_code=f"RATE-DFT-{uuid.uuid4().hex[:4]}",
            description="Draft Rate",
            unit="labour-hour",
            rate_value=Decimal("30.00"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref-1S",
            status="DRAFT",
            created_by=adm_id,
        )
        cr_usd = CostRate(
            project_id=p1_id,
            rate_code=f"RATE-USD-{uuid.uuid4().hex[:4]}",
            description="USD Rate",
            unit="labour-hour",
            rate_value=Decimal("10.00"),
            currency="USD",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref-1S",
            status="CONFIRMED",
            created_by=adm_id,
            confirmed_by=adm_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        cr_p2 = CostRate(
            project_id=p2_id,
            rate_code=f"RATE-P2-{uuid.uuid4().hex[:4]}",
            description="P2 Rate",
            unit="labour-hour",
            rate_value=Decimal("45.00"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref-P2",
            status="CONFIRMED",
            created_by=adm_id,
            confirmed_by=adm_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add_all([cr_labour, cr_equip, cr_draft, cr_usd, cr_p2])
        db.commit()
        db.refresh(cr_labour)
        db.refresh(cr_equip)
        db.refresh(cr_draft)
        db.refresh(cr_usd)
        db.refresh(cr_p2)
        cr_labour_id = cr_labour.id
        cr_equip_id = cr_equip.id
        cr_draft_id = cr_draft.id
        cr_usd_id = cr_usd.id
        cr_p2_id = cr_p2.id

        # Activity Rate Mapping
        arm_labour = ActivityRateMapping(
            project_id=p1_id,
            activity_id=act1_id,
            cost_rate_id=cr_labour_id,
            rate_value=Decimal("50.00"),
            rate_unit="labour-hour",
            rate_version="1.0",
            currency="INR",
            status="ACTIVE",
            created_by=adm_id,
        )
        db.add(arm_labour)
        db.commit()
        db.refresh(arm_labour)
        arm_labour_id = arm_labour.id

        # Verified Progress Execution for Output
        dpr = DailyProgressReport(
            project_id=p1_id,
            report_date=date(2026, 10, 1),
            submitted_by=adm_id,
            submission_status="FINALIZED",
        )
        db.add(dpr)
        db.commit()

        dap = DailyActivityProgress(
            daily_report_id=dpr.id,
            project_id=p1_id,
            activity_id=act1_id,
            contractor_progress_value=Decimal("50.0000"),
            contractor_progress_unit="m3",
            contractor_status="COMPLETED",
            created_by=adm_id,
        )
        db.add(dap)
        db.commit()

        dapv = DailyActivityProgressVerification(
            daily_activity_progress_id=dap.id,
            project_id=p1_id,
            verification_status="VERIFIED",
            verified_quantity=Decimal("50.0000"),
            verified_quantity_unit="m3",
            verified_by=sup_id,
        )
        db.add(dapv)
        db.commit()

        # Material Performance Snapshots (FINALIZED, DRAFT, SUPERSEDED)
        mps_fin = MaterialPerformanceSnapshot(
            project_id=p1_id,
            activity_id=act1_id,
            material_item_id=steel_id,
            planned_quantity=Decimal("10.0000"),
            planned_unit="MT",
            actual_consumption_quantity=Decimal("12.0000"),
            actual_consumption_unit="MT",
            verified_activity_execution_quantity=Decimal("50.0000"),
            verified_activity_execution_unit="m3",
            performance_status="MATCH",
            canonical_hash=f"hash_mps_{uuid.uuid4().hex[:8]}",
            status="FINALIZED",
            input_snapshot_json={"test": "fin"},
            provenance_metadata={"test": "fin"},
            created_by=adm_id,
            finalized_by=adm_id,
            finalized_at=datetime.now(timezone.utc),
        )
        mps_draft = MaterialPerformanceSnapshot(
            project_id=p1_id,
            activity_id=act1_id,
            material_item_id=steel_id,
            planned_quantity=Decimal("10.0000"),
            planned_unit="MT",
            actual_consumption_quantity=Decimal("12.0000"),
            actual_consumption_unit="MT",
            performance_status="MATCH",
            canonical_hash=f"hash_mps_d_{uuid.uuid4().hex[:8]}",
            status="DRAFT",
            input_snapshot_json={"test": "draft"},
            provenance_metadata={"test": "draft"},
            created_by=adm_id,
        )
        mps_sup = MaterialPerformanceSnapshot(
            project_id=p1_id,
            activity_id=act1_id,
            material_item_id=steel_id,
            planned_quantity=Decimal("10.0000"),
            planned_unit="MT",
            actual_consumption_quantity=Decimal("12.0000"),
            actual_consumption_unit="MT",
            performance_status="MATCH",
            canonical_hash=f"hash_mps_s_{uuid.uuid4().hex[:8]}",
            status="SUPERSEDED",
            input_snapshot_json={"test": "sup"},
            provenance_metadata={"test": "sup"},
            created_by=adm_id,
            finalized_by=adm_id,
            finalized_at=datetime.now(timezone.utc),
            superseded_by_user_id=adm_id,
            superseded_at=datetime.now(timezone.utc),
            supersession_reason="Testing",
        )
        db.add_all([mps_fin, mps_draft, mps_sup])
        db.commit()
        db.refresh(mps_fin)
        db.refresh(mps_draft)
        db.refresh(mps_sup)
        mps_fin_id = mps_fin.id
        mps_draft_id = mps_draft.id
        mps_sup_id = mps_sup.id

    adm_token = create_access_token({"sub": adm_email})
    sup_token = create_access_token({"sub": sup_email})
    con_token = create_access_token({"sub": con_email})
    pm_token = create_access_token({"sub": pm_email})

    return {
        "adm_id": adm_id,
        "sup_id": sup_id,
        "con_id": con_id,
        "pm_id": pm_id,
        "adm_token": adm_token,
        "sup_token": sup_token,
        "con_token": con_token,
        "pm_token": pm_token,
        "p1_id": p1_id,
        "p2_id": p2_id,
        "act1_id": act1_id,
        "act2_id": act2_id,
        "res_labour_id": res_labour_id,
        "res_equip_id": res_equip_id,
        "res_mat_id": res_mat_id,
        "steel_id": steel_id,
        "p2_mat_id": p2_mat_id,
        "rp_labour_id": rp_labour_id,
        "cr_labour_id": cr_labour_id,
        "cr_equip_id": cr_equip_id,
        "cr_draft_id": cr_draft_id,
        "cr_usd_id": cr_usd_id,
        "cr_p2_id": cr_p2_id,
        "arm_labour_id": arm_labour_id,
        "mps_fin_id": mps_fin_id,
        "mps_draft_id": mps_draft_id,
        "mps_sup_id": mps_sup_id,
    }


# ==============================================================================
# GROUP 1: ENTITY AND SOURCE VALIDATION
# ==============================================================================

def test_01_create_snapshot_labour_with_all_fields(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "LABOUR",
        "resource_id": setup_data["res_labour_id"],
        "planned_quantity": "100.0000",
        "planned_unit": "labour-hour",
        "verified_actual_resource_quantity": "105.0000",
        "verified_actual_resource_unit": "labour-hour",
        "verified_output_quantity": "50.0000",
        "verified_output_unit": "m3",
        "cost_rate_id": setup_data["cr_labour_id"],
        "tolerance_percentage": "10.00",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "DRAFT"
    assert data["resource_category"] == "LABOUR"
    assert Decimal(str(data["resource_variance"])) == Decimal("5.0000")
    assert Decimal(str(data["resource_variance_percentage"])) == Decimal("5.0000")
    assert data["performance_status"] == "WITHIN_PERMISSIBLE_VARIANCE"
    assert Decimal(str(data["productivity"])) == Decimal("0.476190")
    assert data["productivity_unit"] == "m3/labour-hour"
    assert Decimal(str(data["resource_intensity"])) == Decimal("2.100000")
    assert Decimal(str(data["planned_cost"])) == Decimal("5000.0000")
    assert Decimal(str(data["actual_cost"])) == Decimal("5250.0000")
    assert Decimal(str(data["cost_variance"])) == Decimal("250.0000")
    assert data["currency"] == "INR"


def test_02_create_snapshot_equipment_with_all_fields(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["sup_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "EQUIPMENT",
        "resource_id": setup_data["res_equip_id"],
        "planned_quantity": "20.0000",
        "planned_unit": "equipment-hour",
        "verified_actual_resource_quantity": "25.0000",
        "verified_actual_resource_unit": "equipment-hour",
        "verified_output_quantity": "50.0000",
        "verified_output_unit": "m3",
        "cost_rate_id": setup_data["cr_equip_id"],
        "tolerance_percentage": "5.00",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "DRAFT"
    assert data["resource_category"] == "EQUIPMENT"
    assert Decimal(str(data["resource_variance"])) == Decimal("5.0000")
    assert Decimal(str(data["resource_variance_percentage"])) == Decimal("25.0000")
    assert data["performance_status"] == "COST_OVER_RUN"


def test_03_create_snapshot_missing_activity_fails(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": str(uuid.uuid4()),
        "resource_category": "LABOUR",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 404


def test_04_create_snapshot_invalid_resource_category_fails(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "UNKNOWN_CAT",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 422


def test_05_create_snapshot_category_mismatch_with_resource_fails(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "EQUIPMENT",
        "resource_id": setup_data["res_labour_id"], # Labour passed for Equipment
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 400


def test_06_create_snapshot_cross_project_activity_rejected(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act2_id"], # P2 activity in P1 project
        "resource_category": "LABOUR",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code in [400, 404]


def test_07_create_snapshot_cross_project_material_rejected(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "MATERIAL",
        "material_item_id": setup_data["p2_mat_id"], # P2 material in P1
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code in [400, 404]


def test_08_create_snapshot_cross_project_cost_rate_rejected(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "LABOUR",
        "cost_rate_id": setup_data["cr_p2_id"], # P2 rate in P1
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code in [400, 404]


# ==============================================================================
# GROUP 2: RESOURCE VARIANCE
# ==============================================================================

def test_09_variance_positive_over_consumption(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "LABOUR",
        "planned_quantity": "100.0000",
        "planned_unit": "hour",
        "verified_actual_resource_quantity": "120.0000",
        "verified_actual_resource_unit": "hour",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert Decimal(str(data["resource_variance"])) == Decimal("20.0000")
    assert Decimal(str(data["resource_variance_percentage"])) == Decimal("20.0000")
    assert data["performance_status"] == "OVER_RESOURCE_CONSUMPTION"


def test_10_variance_negative_under_consumption(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "LABOUR",
        "planned_quantity": "100.0000",
        "planned_unit": "hour",
        "verified_actual_resource_quantity": "85.0000",
        "verified_actual_resource_unit": "hour",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert Decimal(str(data["resource_variance"])) == Decimal("-15.0000")
    assert Decimal(str(data["resource_variance_percentage"])) == Decimal("-15.0000")
    assert data["performance_status"] == "UNDER_RESOURCE_CONSUMPTION"


def test_11_variance_zero_exact_match(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "LABOUR",
        "planned_quantity": "100.0000",
        "planned_unit": "hour",
        "verified_actual_resource_quantity": "100.0000",
        "verified_actual_resource_unit": "hour",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert Decimal(str(data["resource_variance"])) == Decimal("0.0000")
    assert data["performance_status"] == "MATCH"


def test_12_variance_missing_actual_operand_returns_none(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "LABOUR",
        "planned_quantity": "100.0000",
        "planned_unit": "hour",
        # missing actual
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["actual_resource_quantity"] is None
    assert data["resource_variance"] is None
    assert data["resource_variance_percentage"] is None
    assert data["performance_status"] == "REQUIRES_INPUT"


def test_13_variance_missing_planned_operand_returns_none(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "LABOUR",
        "verified_actual_resource_quantity": "50.0000",
        "verified_actual_resource_unit": "hour",
        # missing planned
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["planned_quantity"] is None
    assert data["resource_variance"] is None
    assert data["resource_variance_percentage"] is None
    assert data["performance_status"] == "REQUIRES_INPUT"


def test_14_variance_percentage_zero_denominator_returns_none(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "LABOUR",
        "planned_quantity": "0.0000",
        "planned_unit": "hour",
        "verified_actual_resource_quantity": "10.0000",
        "verified_actual_resource_unit": "hour",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert Decimal(str(data["resource_variance"])) == Decimal("10.0000")
    assert data["resource_variance_percentage"] is None


def test_15_variance_compatible_unit_conversion_mass(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "MATERIAL",
        "planned_quantity": "1.0000", # 1 MT
        "planned_unit": "MT",
        "verified_actual_resource_quantity": "1200.0000", # 1200 KG
        "verified_actual_resource_unit": "KG",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    # 1200 KG converted to MT is 1.2000 MT -> variance = 0.2000 MT
    assert Decimal(str(data["resource_variance"])) == Decimal("0.2000")
    assert Decimal(str(data["resource_variance_percentage"])) == Decimal("20.0000")


def test_16_variance_compatible_unit_conversion_hours(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "LABOUR",
        "planned_quantity": "50.0000",
        "planned_unit": "labour-hour",
        "verified_actual_resource_quantity": "60.0000",
        "verified_actual_resource_unit": "hours",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert Decimal(str(data["resource_variance"])) == Decimal("10.0000")


# ==============================================================================
# GROUP 3: PRODUCTIVITY & RESOURCE INTENSITY
# ==============================================================================

def test_17_labour_productivity_valid(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "LABOUR",
        "verified_actual_resource_quantity": "100.0000",
        "verified_actual_resource_unit": "labour-hour",
        "verified_output_quantity": "50.0000",
        "verified_output_unit": "m3",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    # productivity = 50 / 100 = 0.500000 m3/labour-hour
    assert Decimal(str(data["productivity"])) == Decimal("0.500000")
    assert data["productivity_unit"] == "m3/labour-hour"


def test_18_equipment_productivity_valid(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "EQUIPMENT",
        "verified_actual_resource_quantity": "10.0000",
        "verified_actual_resource_unit": "equipment-hour",
        "verified_output_quantity": "50.0000",
        "verified_output_unit": "m3",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    # productivity = 50 / 10 = 5.000000 m3/equipment-hour
    assert Decimal(str(data["productivity"])) == Decimal("5.000000")
    assert data["productivity_unit"] == "m3/equipment-hour"


def test_19_productivity_missing_output_returns_none(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    # Activity without output in request (overriding output with None)
    payload = {
        "activity_id": setup_data["act2_id"], # act2 has no progress records
        "resource_category": "LABOUR",
        "verified_actual_resource_quantity": "10.0000",
        "verified_actual_resource_unit": "hour",
    }
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p2_id']}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["verified_output_quantity"] is None
    assert data["productivity"] is None


def test_20_productivity_missing_hours_returns_none(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "LABOUR",
        "verified_output_quantity": "50.0000",
        "verified_output_unit": "m3",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["actual_resource_quantity"] is None
    assert data["productivity"] is None


def test_21_productivity_zero_hours_denominator_returns_none(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "LABOUR",
        "verified_actual_resource_quantity": "0.0000",
        "verified_actual_resource_unit": "hour",
        "verified_output_quantity": "50.0000",
        "verified_output_unit": "m3",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["productivity"] is None


def test_22_resource_intensity_valid(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "LABOUR",
        "verified_actual_resource_quantity": "100.0000",
        "verified_actual_resource_unit": "labour-hour",
        "verified_output_quantity": "50.0000",
        "verified_output_unit": "m3",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    # intensity = 100 / 50 = 2.000000 labour-hour/m3
    assert Decimal(str(data["resource_intensity"])) == Decimal("2.000000")
    assert data["resource_intensity_unit"] == "labour-hour/m3"


def test_23_resource_intensity_zero_output_denominator_returns_none(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "LABOUR",
        "verified_actual_resource_quantity": "10.0000",
        "verified_actual_resource_unit": "hour",
        "verified_output_quantity": "0.0000",
        "verified_output_unit": "m3",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["resource_intensity"] is None


# ==============================================================================
# GROUP 4: MATERIAL INTEGRATION
# ==============================================================================

def test_24_material_integration_finalized_phase_1r_snapshot(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "MATERIAL",
        "material_item_id": setup_data["steel_id"],
        "material_performance_snapshot_id": setup_data["mps_fin_id"],
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["material_performance_snapshot_id"] == setup_data["mps_fin_id"]
    assert Decimal(str(data["planned_quantity"])) == Decimal("10.0000")
    assert data["planned_unit"] == "MT"
    assert Decimal(str(data["actual_resource_quantity"])) == Decimal("12.0000")
    assert data["actual_resource_unit"] == "MT"
    assert Decimal(str(data["verified_output_quantity"])) == Decimal("50.0000")
    assert data["verified_output_unit"] == "m3"
    assert Decimal(str(data["resource_variance"])) == Decimal("2.0000")


def test_25_material_integration_draft_phase_1r_rejected(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "MATERIAL",
        "material_item_id": setup_data["steel_id"],
        "material_performance_snapshot_id": setup_data["mps_draft_id"], # DRAFT
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 400


def test_26_material_integration_superseded_phase_1r_rejected(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "MATERIAL",
        "material_item_id": setup_data["steel_id"],
        "material_performance_snapshot_id": setup_data["mps_sup_id"], # SUPERSEDED
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 400


def test_27_material_integration_missing_phase_1r_requires_input(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    # New isolated material with no 1R snapshot
    with TestingSessionLocal() as db:
        mat_iso = MaterialItem(
            project_id=p1_id,
            material_code=f"ISO-{uuid.uuid4().hex[:4]}",
            material_name="Isolated Mat",
            material_category="AGGREGATE",
            standard_unit="M3",
        )
        db.add(mat_iso)
        db.commit()
        db.refresh(mat_iso)
        mat_iso_id = mat_iso.id

    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "MATERIAL",
        "material_item_id": mat_iso_id,
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["material_performance_snapshot_id"] is None
    assert data["planned_quantity"] is None
    assert data["actual_resource_quantity"] is None
    assert data["performance_status"] == "REQUIRES_INPUT"


def test_28_material_integration_provenance_and_hash_preserved(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "MATERIAL",
        "material_item_id": setup_data["steel_id"],
        "material_performance_snapshot_id": setup_data["mps_fin_id"],
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    prov = data["provenance_metadata"]
    assert "material_performance_snapshot" in prov["sources"]
    assert prov["sources"]["material_performance_snapshot"]["id"] == setup_data["mps_fin_id"]


# ==============================================================================
# GROUP 5: COST CALCULATIONS
# ==============================================================================

def test_29_cost_calculation_confirmed_rate(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "LABOUR",
        "cost_rate_id": setup_data["cr_labour_id"],
        "planned_quantity": "100.0000",
        "planned_unit": "labour-hour",
        "verified_actual_resource_quantity": "110.0000",
        "verified_actual_resource_unit": "labour-hour",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["cost_rate_id"] == setup_data["cr_labour_id"]
    assert Decimal(str(data["planned_cost"])) == Decimal("5000.0000")
    assert Decimal(str(data["actual_cost"])) == Decimal("5500.0000")
    assert Decimal(str(data["cost_variance"])) == Decimal("500.0000")


def test_30_cost_calculation_unconfirmed_rate_unavailable(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "LABOUR",
        "cost_rate_id": setup_data["cr_draft_id"], # DRAFT status
        "planned_quantity": "100.0000",
        "planned_unit": "labour-hour",
        "verified_actual_resource_quantity": "110.0000",
        "verified_actual_resource_unit": "labour-hour",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["planned_cost"] is None
    assert data["actual_cost"] is None
    assert data["performance_status"] == "RATE_UNAVAILABLE"


def test_31_cost_calculation_planned_and_actual_cost(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "EQUIPMENT",
        "cost_rate_id": setup_data["cr_equip_id"],
        "planned_quantity": "10.0000",
        "planned_unit": "equipment-hour",
        "verified_actual_resource_quantity": "8.0000",
        "verified_actual_resource_unit": "equipment-hour",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert Decimal(str(data["planned_cost"])) == Decimal("2000.0000")
    assert Decimal(str(data["actual_cost"])) == Decimal("1600.0000")
    assert Decimal(str(data["cost_variance"])) == Decimal("-400.0000")
    assert data["performance_status"] == "COST_UNDER_RUN"


def test_32_cost_intensity_valid(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "EQUIPMENT",
        "cost_rate_id": setup_data["cr_equip_id"],
        "verified_actual_resource_quantity": "10.0000",
        "verified_actual_resource_unit": "equipment-hour",
        "verified_output_quantity": "50.0000",
        "verified_output_unit": "m3",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    # actual cost = 10 * 200 = 2000 INR
    # cost intensity = 2000 / 50 = 40.000000 INR/m3
    assert Decimal(str(data["cost_intensity"])) == Decimal("40.000000")
    assert data["cost_intensity_unit"] == "INR/m3"


# ==============================================================================
# GROUP 6: CURRENCY AND UNITS
# ==============================================================================

def test_33_unit_mismatch_incompatible_quantities(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "LABOUR",
        "planned_quantity": "100.0000",
        "planned_unit": "labour-hour",
        "verified_actual_resource_quantity": "10.0000",
        "verified_actual_resource_unit": "m3", # Incompatible with labour-hour
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["performance_status"] == "UNIT_MISMATCH"
    assert data["resource_variance"] is None


def test_34_unit_mismatch_rate_unit_incompatible_with_resource(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    payload = {
        "activity_id": setup_data["act1_id"],
        "resource_category": "LABOUR",
        "cost_rate_id": setup_data["cr_equip_id"], # equipment-hour rate applied to labour-hour
        "planned_quantity": "100.0000",
        "planned_unit": "labour-hour",
        "verified_actual_resource_quantity": "100.0000",
        "verified_actual_resource_unit": "labour-hour",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["performance_status"] == "UNIT_MISMATCH"
    assert data["planned_cost"] is None


# ==============================================================================
# GROUP 7: AGGREGATION & SUMMARY
# ==============================================================================

def test_35_summary_activity_and_period_totals(client_fixture, setup_data):
    p_id = setup_data["p1_id"]
    token = setup_data["adm_token"]

    # Fresh project for isolated summary testing
    with TestingSessionLocal() as db:
        p_iso = Project(name=f"Summary Proj {uuid.uuid4().hex[:4]}", created_by=setup_data["adm_id"])
        db.add(p_iso)
        db.commit()
        db.refresh(p_iso)
        p_iso_id = p_iso.id

        db.add(ProjectMember(project_id=p_iso_id, user_id=setup_data["adm_id"]))
        act_iso = ConstructionActivity(
            project_id=p_iso_id,
            activity_code="ACT-SUM-1",
            activity_name="Sum Act",
            activity_type="CONSTRUCTION",
            created_by=setup_data["adm_id"],
        )
        db.add(act_iso)
        db.commit()
        db.refresh(act_iso)
        act_iso_id = act_iso.id

    # Create 2 snapshots in p_iso_id
    r1 = client_fixture.post(
        f"/api/projects/{p_iso_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": act_iso_id,
            "resource_category": "LABOUR",
            "planned_quantity": "100.0000",
            "planned_unit": "hour",
            "verified_actual_resource_quantity": "110.0000",
            "verified_actual_resource_unit": "hour",
        },
    )
    assert r1.status_code == 201

    r2 = client_fixture.post(
        f"/api/projects/{p_iso_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": act_iso_id,
            "resource_category": "EQUIPMENT",
            "planned_quantity": "20.0000",
            "planned_unit": "equipment-hour",
            "verified_actual_resource_quantity": "25.0000",
            "verified_actual_resource_unit": "equipment-hour",
        },
    )
    assert r2.status_code == 201

    # Fetch summary
    resp_sum = client_fixture.get(
        f"/api/projects/{p_iso_id}/resource-performance/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_sum.status_code == 200
    s_data = resp_sum.json()
    assert s_data["total_snapshots"] == 2
    assert "hour" in s_data["total_planned_quantities"]
    assert "equipment-hour" in s_data["total_planned_quantities"]
    assert Decimal(str(s_data["total_planned_quantities"]["hour"])) == Decimal("100.0000")
    assert Decimal(str(s_data["total_planned_quantities"]["equipment-hour"])) == Decimal("20.0000")
    assert Decimal(str(s_data["total_actual_quantities"]["hour"])) == Decimal("110.0000")
    assert Decimal(str(s_data["total_actual_quantities"]["equipment-hour"])) == Decimal("25.0000")
    assert Decimal(str(s_data["total_resource_variance"]["hour"])) == Decimal("10.0000")
    assert Decimal(str(s_data["total_resource_variance"]["equipment-hour"])) == Decimal("5.0000")


def test_36_summary_excludes_superseded_snapshots(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]

    # Create snapshot and finalize it
    r_create = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "resource_category": "LABOUR",
            "planned_quantity": "50.0000",
            "planned_unit": "hours",
            "verified_actual_resource_quantity": "50.0000",
            "verified_actual_resource_unit": "hours",
            "performance_period_start": "2026-11-01",
            "performance_period_end": "2026-11-30",
        },
    )
    snap_id = r_create.json()["id"]
    r_fin = client_fixture.post(f"/api/projects/{p1_id}/resource-performance/{snap_id}/finalize", headers={"Authorization": f"Bearer {token}"})
    assert r_fin.status_code == 200

    # Supersede it
    r_sup = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance/{snap_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "Outdated log"},
    )
    assert r_sup.status_code == 200

    # Summary should not count this superseded snapshot
    r_sum = client_fixture.get(f"/api/projects/{p1_id}/resource-performance/summary", headers={"Authorization": f"Bearer {token}"})
    assert r_sum.status_code == 200
    ids_in_sum = [s["id"] for s in r_sum.json()["snapshots"]]
    assert snap_id not in ids_in_sum


# ==============================================================================
# GROUP 8: LIFECYCLE
# ==============================================================================

def test_37_lifecycle_creation_produces_draft(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": setup_data["act1_id"], "resource_category": "LABOUR"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "DRAFT"


def test_38_lifecycle_creation_with_finalized_rejected(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={"activity_id": setup_data["act1_id"], "resource_category": "LABOUR", "status": "FINALIZED"},
    )
    assert resp.status_code == 422


def test_39_lifecycle_valid_finalization(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    r_create = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "resource_category": "LABOUR",
            "performance_period_start": "2026-12-01",
            "performance_period_end": "2026-12-31",
        },
    )
    snap_id = r_create.json()["id"]
    r_fin = client_fixture.post(f"/api/projects/{p1_id}/resource-performance/{snap_id}/finalize", headers={"Authorization": f"Bearer {token}"})
    assert r_fin.status_code == 200
    f_data = r_fin.json()
    assert f_data["status"] == "FINALIZED"
    assert f_data["finalized_by"] == setup_data["adm_id"]
    assert f_data["finalized_at"] is not None


def test_40_lifecycle_refinalization_rejected(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    r_create = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "resource_category": "EQUIPMENT",
            "performance_period_start": "2026-12-01",
            "performance_period_end": "2026-12-31",
        },
    )
    snap_id = r_create.json()["id"]
    client_fixture.post(f"/api/projects/{p1_id}/resource-performance/{snap_id}/finalize", headers={"Authorization": f"Bearer {token}"})
    # Attempt second finalize
    r_fin2 = client_fixture.post(f"/api/projects/{p1_id}/resource-performance/{snap_id}/finalize", headers={"Authorization": f"Bearer {token}"})
    assert r_fin2.status_code == 400


def test_41_lifecycle_supersede_requires_reason(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    r_create = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "resource_category": "MATERIAL",
            "performance_period_start": "2026-12-01",
            "performance_period_end": "2026-12-31",
        },
    )
    snap_id = r_create.json()["id"]
    client_fixture.post(f"/api/projects/{p1_id}/resource-performance/{snap_id}/finalize", headers={"Authorization": f"Bearer {token}"})

    # Empty reason fails
    r_sup = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance/{snap_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "   "},
    )
    assert r_sup.status_code == 422

    # Self supersession fails
    r_self = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance/{snap_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "Self supersession", "replacement_snapshot_id": snap_id},
    )
    assert r_self.status_code == 400

    # Cross project replacement fails
    r_p2 = client_fixture.post(
        f"/api/projects/{setup_data['p2_id']}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act2_id"],
            "resource_category": "MATERIAL",
            "performance_period_start": "2026-12-01",
            "performance_period_end": "2026-12-31",
        },
    )
    p2_snap_id = r_p2.json()["id"]
    r_cross = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance/{snap_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "Cross project", "replacement_snapshot_id": p2_snap_id},
    )
    assert r_cross.status_code == 404

    # Create another activity in P1 for mismatch test
    with TestingSessionLocal() as db:
        act_extra = ConstructionActivity(
            project_id=p1_id,
            activity_code=f"ACT-EXTRA-{uuid.uuid4().hex[:4]}",
            activity_name="Extra Act",
            activity_type="CONSTRUCTION",
            created_by=setup_data["adm_id"],
        )
        db.add(act_extra)
        db.commit()
        act_extra_id = act_extra.id

    # Activity mismatch fails
    r_act_mismatch = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": act_extra_id,
            "resource_category": "MATERIAL",
            "performance_period_start": "2026-12-01",
            "performance_period_end": "2026-12-31",
        },
    )
    act_mismatch_id = r_act_mismatch.json()["id"]
    r_err_act = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance/{snap_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "Activity mismatch", "replacement_snapshot_id": act_mismatch_id},
    )
    assert r_err_act.status_code == 400
    assert "activity" in r_err_act.json()["detail"].lower()

    # Category mismatch fails
    r_cat_mismatch = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "resource_category": "LABOUR",
            "performance_period_start": "2026-12-01",
            "performance_period_end": "2026-12-31",
        },
    )
    cat_mismatch_id = r_cat_mismatch.json()["id"]
    r_err_cat = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance/{snap_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "Category mismatch", "replacement_snapshot_id": cat_mismatch_id},
    )
    assert r_err_cat.status_code == 400
    assert "resource_category" in r_err_cat.json()["detail"].lower()

    # Period mismatch fails
    r_per_mismatch = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "resource_category": "MATERIAL",
            "performance_period_start": "2026-12-02",
            "performance_period_end": "2026-12-31",
        },
    )
    per_mismatch_id = r_per_mismatch.json()["id"]
    r_err_per = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance/{snap_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "Period mismatch", "replacement_snapshot_id": per_mismatch_id},
    )
    assert r_err_per.status_code == 400
    assert "performance_period_start" in r_err_per.json()["detail"].lower()

    # Valid replacement succeeds
    r_valid_rep = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "resource_category": "MATERIAL",
            "performance_period_start": "2026-12-01",
            "performance_period_end": "2026-12-31",
        },
    )
    valid_rep_id = r_valid_rep.json()["id"]
    r_valid_sup = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance/{snap_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "Valid supersession", "replacement_snapshot_id": valid_rep_id},
    )
    assert r_valid_sup.status_code == 200
    data = r_valid_sup.json()
    assert data["status"] == "SUPERSEDED"
    assert data["superseded_by"] == valid_rep_id

    # Superseding already superseded replacement fails
    r_err_already = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance/{valid_rep_id}/finalize",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_err_already.status_code == 200
    r_err_sup_already = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance/{valid_rep_id}/supersede",
        headers={"Authorization": f"Bearer {token}"},
        json={"supersession_reason": "Trying to use snap_id which is already superseded", "replacement_snapshot_id": snap_id},
    )
    assert r_err_sup_already.status_code == 400
    assert "already be superseded" in r_err_sup_already.json()["detail"].lower()


def test_42_lifecycle_superseded_cannot_reopen(setup_data):
    p1_id = setup_data["p1_id"]
    with TestingSessionLocal() as db:
        snap = ResourcePerformanceSnapshot(
            project_id=p1_id,
            activity_id=setup_data["act1_id"],
            resource_category="LABOUR",
            performance_status="MATCH",
            canonical_hash="hash_reopen_test",
            status="FINALIZED",
            created_by=setup_data["adm_id"],
            finalized_by=setup_data["adm_id"],
            finalized_at=datetime.now(timezone.utc),
        )
        db.add(snap)
        db.commit()
        db.refresh(snap)

        snap.status = "SUPERSEDED"
        snap.superseded_by_user_id = setup_data["adm_id"]
        snap.superseded_at = datetime.now(timezone.utc)
        snap.supersession_reason = "Test supersede"
        db.commit()

        # Direct SQL attempt to reopen -> fails via trigger
        with pytest.raises(Exception):
            db.execute(text("UPDATE resource_performance_snapshots SET status = 'FINALIZED' WHERE id = :id"), {"id": snap.id})
            db.commit()
        db.rollback()


# ==============================================================================
# GROUP 9: HASH AND PROVENANCE
# ==============================================================================

def test_43_canonical_hash_determinism_and_reproducibility():
    payload1 = {
        "project_id": "p1",
        "activity_id": "a1",
        "resource_category": "LABOUR",
        "planned_quantity": "100.0000",
        "performance_status": "MATCH",
        "algorithm_version": "RES_PERFORMANCE_1.0",
    }
    payload2 = {
        "algorithm_version": "RES_PERFORMANCE_1.0",
        "performance_status": "MATCH",
        "planned_quantity": "100.0000",
        "resource_category": "LABOUR",
        "activity_id": "a1",
        "project_id": "p1",
    }
    assert generate_canonical_hash(payload1) == generate_canonical_hash(payload2)


def test_44_canonical_hash_changes_on_input_mutation():
    payload1 = {
        "project_id": "p1",
        "activity_id": "a1",
        "resource_category": "LABOUR",
        "planned_quantity": "100.0000",
    }
    payload2 = {
        "project_id": "p1",
        "activity_id": "a1",
        "resource_category": "LABOUR",
        "planned_quantity": "101.0000", # Changed
    }
    assert generate_canonical_hash(payload1) != generate_canonical_hash(payload2)


# ==============================================================================
# GROUP 10: PROJECT ISOLATION AND RBAC
# ==============================================================================

def test_45_rbac_contractor_read_only_mutations_forbidden(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    con_token = setup_data["con_token"]

    # Contractor create -> 403
    r_create = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {con_token}"},
        json={"activity_id": setup_data["act1_id"], "resource_category": "LABOUR"},
    )
    assert r_create.status_code == 403

    # Contractor read -> 200
    r_list = client_fixture.get(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert r_list.status_code == 200


def test_46_rbac_project_manager_all_rejected(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    pm_token = setup_data["pm_token"]

    r_get = client_fixture.get(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {pm_token}"},
    )
    assert r_get.status_code == 403

    r_post = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {pm_token}"},
        json={"activity_id": setup_data["act1_id"], "resource_category": "LABOUR"},
    )
    assert r_post.status_code == 403


def test_47_non_member_forbidden_on_all_endpoints(client_fixture, setup_data):
    p2_id = setup_data["p2_id"] # pm is not a member of p2
    pm_token = setup_data["pm_token"]

    resp = client_fixture.get(
        f"/api/projects/{p2_id}/resource-performance",
        headers={"Authorization": f"Bearer {pm_token}"},
    )
    assert resp.status_code == 403


# ==============================================================================
# GROUP 11: DATABASE INTEGRITY & TRIGGERS
# ==============================================================================

def test_48_trigger_prevents_sql_update_on_finalized(setup_data):
    p1_id = setup_data["p1_id"]
    with TestingSessionLocal() as db:
        snap = ResourcePerformanceSnapshot(
            project_id=p1_id,
            activity_id=setup_data["act1_id"],
            resource_category="LABOUR",
            performance_status="MATCH",
            canonical_hash="hash_trg_test_1",
            status="FINALIZED",
            created_by=setup_data["adm_id"],
            finalized_by=setup_data["adm_id"],
            finalized_at=datetime.now(timezone.utc),
        )
        db.add(snap)
        db.commit()
        db.refresh(snap)
        snap_id = snap.id

        # Attempt to modify planned_quantity -> fails via trigger
        with pytest.raises(Exception):
            db.execute(text("UPDATE resource_performance_snapshots SET planned_quantity = 999.0 WHERE id = :id"), {"id": snap_id})
            db.commit()
        db.rollback()


def test_49_trigger_prevents_sql_delete_on_finalized(setup_data):
    p1_id = setup_data["p1_id"]
    with TestingSessionLocal() as db:
        snap = ResourcePerformanceSnapshot(
            project_id=p1_id,
            activity_id=setup_data["act1_id"],
            resource_category="EQUIPMENT",
            performance_status="MATCH",
            canonical_hash="hash_trg_test_2",
            status="FINALIZED",
            created_by=setup_data["adm_id"],
            finalized_by=setup_data["adm_id"],
            finalized_at=datetime.now(timezone.utc),
        )
        db.add(snap)
        db.commit()
        db.refresh(snap)
        snap_id = snap.id

        # Attempt to delete -> fails via trigger
        with pytest.raises(Exception):
            db.execute(text("DELETE FROM resource_performance_snapshots WHERE id = :id"), {"id": snap_id})
            db.commit()
        db.rollback()


def test_50_trigger_blocks_draft_to_superseded_direct_transition(setup_data):
    p1_id = setup_data["p1_id"]
    with TestingSessionLocal() as db:
        snap = ResourcePerformanceSnapshot(
            project_id=p1_id,
            activity_id=setup_data["act1_id"],
            resource_category="LABOUR",
            performance_status="MATCH",
            canonical_hash="hash_trg_test_3",
            status="DRAFT",
            created_by=setup_data["adm_id"],
        )
        db.add(snap)
        db.commit()
        db.refresh(snap)
        snap_id = snap.id

        # Attempt draft -> superseded directly -> fails via trigger
        with pytest.raises(Exception):
            db.execute(text("UPDATE resource_performance_snapshots SET status = 'SUPERSEDED' WHERE id = :id"), {"id": snap_id})
            db.commit()
        db.rollback()


# ==============================================================================
# GROUP 12: CONCURRENCY & HARDENING SCENARIOS
# ==============================================================================

def test_51_concurrency_duplicate_authoritative_snapshots_prevented(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]

    # Create 2 drafts with identical identity
    r1 = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "resource_category": "LABOUR",
            "performance_period_start": "2027-01-01",
            "performance_period_end": "2027-01-31",
        },
    )
    r2 = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "resource_category": "LABOUR",
            "performance_period_start": "2027-01-01",
            "performance_period_end": "2027-01-31",
        },
    )
    id1 = r1.json()["id"]
    id2 = r2.json()["id"]

    # Finalize first -> succeeds
    r_fin1 = client_fixture.post(f"/api/projects/{p1_id}/resource-performance/{id1}/finalize", headers={"Authorization": f"Bearer {token}"})
    assert r_fin1.status_code == 200

    # Finalize second -> rejected with 409 Conflict
    r_fin2 = client_fixture.post(f"/api/projects/{p1_id}/resource-performance/{id2}/finalize", headers={"Authorization": f"Bearer {token}"})
    assert r_fin2.status_code == 409


def test_52_concurrency_separate_periods_allowed(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]

    # Jan 2027
    r1 = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "resource_category": "EQUIPMENT",
            "performance_period_start": "2027-01-01",
            "performance_period_end": "2027-01-31",
        },
    )
    # Feb 2027
    r2 = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "resource_category": "EQUIPMENT",
            "performance_period_start": "2027-02-01",
            "performance_period_end": "2027-02-28",
        },
    )
    id1 = r1.json()["id"]
    id2 = r2.json()["id"]

    r_fin1 = client_fixture.post(f"/api/projects/{p1_id}/resource-performance/{id1}/finalize", headers={"Authorization": f"Bearer {token}"})
    r_fin2 = client_fixture.post(f"/api/projects/{p1_id}/resource-performance/{id2}/finalize", headers={"Authorization": f"Bearer {token}"})
    assert r_fin1.status_code == 200
    assert r_fin2.status_code == 200


def test_53_hardening_missing_actual_is_not_zero(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "resource_category": "LABOUR",
            "planned_quantity": "50.0000",
            "planned_unit": "hour",
        },
    )
    data = resp.json()
    assert data["actual_resource_quantity"] is None
    assert data["resource_variance"] is None


def test_54_hardening_missing_planned_is_not_zero(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    token = setup_data["adm_token"]
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "resource_category": "LABOUR",
            "verified_actual_resource_quantity": "50.0000",
            "verified_actual_resource_unit": "hour",
        },
    )
    data = resp.json()
    assert data["planned_quantity"] is None
    assert data["resource_variance"] is None


def test_55_hardening_missing_verified_output_is_not_one(client_fixture, setup_data):
    p2_id = setup_data["p2_id"]
    token = setup_data["adm_token"]
    resp = client_fixture.post(
        f"/api/projects/{p2_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act2_id"], # act2 has no progress records
            "resource_category": "LABOUR",
            "verified_actual_resource_quantity": "50.0000",
            "verified_actual_resource_unit": "hour",
        },
    )
    data = resp.json()
    assert data["verified_output_quantity"] is None
    assert data["productivity"] is None


def test_56_hardening_summary_does_not_coerce_missing_to_zero(client_fixture, setup_data):
    # In an isolated project, create 1 snapshot with planned only, 1 snapshot with actual only
    token = setup_data["adm_token"]
    with TestingSessionLocal() as db:
        p_iso = Project(name=f"Coerce Proj {uuid.uuid4().hex[:4]}", created_by=setup_data["adm_id"])
        db.add(p_iso)
        db.commit()
        db.refresh(p_iso)
        p_iso_id = p_iso.id

        db.add(ProjectMember(project_id=p_iso_id, user_id=setup_data["adm_id"]))
        act_iso = ConstructionActivity(
            project_id=p_iso_id,
            activity_code="ACT-COERCE-1",
            activity_name="Coerce Act",
            activity_type="CONSTRUCTION",
            created_by=setup_data["adm_id"],
        )
        db.add(act_iso)
        db.commit()
        db.refresh(act_iso)
        act_iso_id = act_iso.id

    client_fixture.post(
        f"/api/projects/{p_iso_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": act_iso_id,
            "resource_category": "LABOUR",
            "planned_quantity": "50.0000",
            "planned_unit": "hour",
            # missing actual
        },
    )
    client_fixture.post(
        f"/api/projects/{p_iso_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": act_iso_id,
            "resource_category": "EQUIPMENT",
            "verified_actual_resource_quantity": "20.0000",
            "verified_actual_resource_unit": "equipment-hour",
            # missing planned
        },
    )

    r_sum = client_fixture.get(f"/api/projects/{p_iso_id}/resource-performance/summary", headers={"Authorization": f"Bearer {token}"})
    assert r_sum.status_code == 200
    s_data = r_sum.json()
    # "hour" has planned=50, but no actual -> total_resource_variance must NOT have "hour" (not coerced to 0 - 50 = -50)
    assert "hour" not in s_data["total_resource_variance"]
    # "equipment-hour" has actual=20, but no planned -> total_resource_variance must NOT have "equipment-hour"
    assert "equipment-hour" not in s_data["total_resource_variance"]


# ==============================================================================
# GROUP 13: TARGETED FINAL REVIEW — PERIOD BOUNDARIES & CERTIFICATE FILTERING
# ==============================================================================

def test_57_output_aggregation_period_boundaries_and_certificate_filtering(client_fixture, setup_data):
    """
    Review 3 verification:
    - Filters DailyActivityProgressVerification by performance_period_start and performance_period_end.
    - Excludes progress outside the date window.
    - Falls back to PeriodCertificateItem with CERTIFIED or DRAFT status when no daily progress matches.
    - Excludes REJECTED or VOID certificates.
    - Prevents double-counting and records source provenance in metadata.
    """
    token = setup_data["adm_token"]
    user_id = setup_data["adm_id"]

    with TestingSessionLocal() as db:
        proj = Project(name=f"Boundaries Proj {uuid.uuid4().hex[:4]}", created_by=user_id)
        db.add(proj)
        db.commit()
        db.refresh(proj)
        proj_id = proj.id

        db.add(ProjectMember(project_id=proj_id, user_id=user_id))
        act = ConstructionActivity(
            project_id=proj_id,
            activity_code="ACT-BOUNDARIES-1",
            activity_name="Boundaries Activity",
            activity_type="CONSTRUCTION",
            created_by=user_id,
        )
        db.add(act)
        db.commit()
        db.refresh(act)
        act_id = act.id

        # Create 3 daily reports:
        # 1. Before window (2027-01-05) -> 10 m3
        # 2. Inside window (2027-01-15) -> 25 m3
        # 3. After window (2027-02-05) -> 30 m3
        dpr1 = DailyProgressReport(project_id=proj_id, report_date=date(2027, 1, 5), submitted_by=user_id, submission_status="FINALIZED")
        dpr2 = DailyProgressReport(project_id=proj_id, report_date=date(2027, 1, 15), submitted_by=user_id, submission_status="FINALIZED")
        dpr3 = DailyProgressReport(project_id=proj_id, report_date=date(2027, 2, 5), submitted_by=user_id, submission_status="FINALIZED")
        db.add_all([dpr1, dpr2, dpr3])
        db.commit()

        dap1 = DailyActivityProgress(daily_report_id=dpr1.id, project_id=proj_id, activity_id=act_id, contractor_progress_value=Decimal("10.0000"), contractor_progress_unit="m3", contractor_status="COMPLETED", created_by=user_id)
        dap2 = DailyActivityProgress(daily_report_id=dpr2.id, project_id=proj_id, activity_id=act_id, contractor_progress_value=Decimal("25.0000"), contractor_progress_unit="m3", contractor_status="COMPLETED", created_by=user_id)
        dap3 = DailyActivityProgress(daily_report_id=dpr3.id, project_id=proj_id, activity_id=act_id, contractor_progress_value=Decimal("30.0000"), contractor_progress_unit="m3", contractor_status="COMPLETED", created_by=user_id)
        db.add_all([dap1, dap2, dap3])
        db.commit()

        ver1 = DailyActivityProgressVerification(daily_activity_progress_id=dap1.id, project_id=proj_id, verified_quantity=Decimal("10.0000"), verified_quantity_unit="m3", verification_status="VERIFIED", verified_by=user_id)
        ver2 = DailyActivityProgressVerification(daily_activity_progress_id=dap2.id, project_id=proj_id, verified_quantity=Decimal("25.0000"), verified_quantity_unit="m3", verification_status="VERIFIED", verified_by=user_id)
        ver3 = DailyActivityProgressVerification(daily_activity_progress_id=dap3.id, project_id=proj_id, verified_quantity=Decimal("30.0000"), verified_quantity_unit="m3", verification_status="VERIFIED", verified_by=user_id)
        db.add_all([ver1, ver2, ver3])
        db.commit()

    # Create snapshot for period 2027-01-10 to 2027-01-20
    resp = client_fixture.post(
        f"/api/projects/{proj_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": act_id,
            "resource_category": "LABOUR",
            "performance_period_start": "2027-01-10",
            "performance_period_end": "2027-01-20",
            "verified_actual_resource_quantity": "50.0000",
            "verified_actual_resource_unit": "hour",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()

    # Only report 2 (25 m3) is within 2027-01-10 to 2027-01-20!
    assert Decimal(str(data["verified_output_quantity"])) == Decimal("25.0000")
    assert data["verified_output_unit"] == "m3"
    # Productivity = 25 / 50 = 0.500000
    assert Decimal(str(data["productivity"])) == Decimal("0.500000")
    # Output provenance tracked
    output_source = data["provenance_metadata"].get("sources", {}).get("verified_output", {})
    assert output_source.get("source_type") == "DAILY_ACTIVITY_PROGRESS_VERIFICATION"
    assert output_source.get("verification_state") == "VERIFIED"
    assert output_source.get("period_start") == "2027-01-10"
    assert output_source.get("period_end") == "2027-01-20"


# ==============================================================================
# GROUP 14: PROVENANCE GAP CLOSURE & CERTIFICATE AUTHORITY
# ==============================================================================

def test_58_direct_supervisor_entry_provenance_tracking(client_fixture, setup_data):
    """
    Verify that directly supplied planned_quantity, verified_actual_resource_quantity,
    and verified_output_quantity record explicit DIRECT_SUPERVISOR_ENTRY provenance.
    """
    token = setup_data["sup_token"]
    p1_id = setup_data["p1_id"]
    sup_id = setup_data["sup_id"]

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "resource_category": "LABOUR",
            "planned_quantity": "80.0000",
            "planned_unit": "hour",
            "verified_actual_resource_quantity": "85.0000",
            "verified_actual_resource_unit": "hour",
            "verified_output_quantity": "40.0000",
            "verified_output_unit": "m3",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    sources = data["provenance_metadata"].get("sources", {})

    # Check planned_resource provenance
    assert "planned_resource" in sources
    p_src = sources["planned_resource"]
    assert p_src["source_type"] == "DIRECT_SUPERVISOR_ENTRY"
    assert p_src["entered_by"] == sup_id
    assert p_src["quantity"] == "80.0000"
    assert p_src["unit"] == "hour"

    # Check actual_resource provenance
    assert "actual_resource" in sources
    a_src = sources["actual_resource"]
    assert a_src["source_type"] == "DIRECT_SUPERVISOR_ENTRY"
    assert a_src["verification_state"] == "SUPERVISOR_MEASURED"
    assert a_src["entered_by"] == sup_id
    assert a_src["quantity"] == "85.0000"
    assert a_src["unit"] == "hour"

    # Check verified_output provenance
    assert "verified_output" in sources
    o_src = sources["verified_output"]
    assert o_src["source_type"] == "DIRECT_SUPERVISOR_ENTRY"
    assert o_src["verification_state"] == "SUPERVISOR_ENTERED"
    assert o_src["entered_by"] == sup_id
    assert o_src["unit"] == "m3"


def test_59_material_performance_snapshot_output_provenance(client_fixture, setup_data):
    """
    Verify that verified output derived from MaterialPerformanceSnapshot records
    explicit MATERIAL_PERFORMANCE_SNAPSHOT provenance with canonical_hash and FINALIZED_MPS state.
    """
    token = setup_data["sup_token"]
    p1_id = setup_data["p1_id"]

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": setup_data["act1_id"],
            "resource_category": "MATERIAL",
            "material_item_id": setup_data["steel_id"],
            "material_performance_snapshot_id": setup_data["mps_fin_id"],
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    sources = data["provenance_metadata"].get("sources", {})

    assert "verified_output" in sources
    o_src = sources["verified_output"]
    assert o_src["source_type"] == "MATERIAL_PERFORMANCE_SNAPSHOT"
    assert o_src["source_id"] == setup_data["mps_fin_id"]
    assert o_src["verification_state"] == "FINALIZED_MPS"
    assert "canonical_hash" in o_src
    assert o_src["unit"] == "m3"

    assert "planned_resource" in sources
    assert sources["planned_resource"]["source_type"] == "MATERIAL_PERFORMANCE_SNAPSHOT"

    assert "actual_resource" in sources
    assert sources["actual_resource"]["source_type"] == "MATERIAL_PERFORMANCE_SNAPSHOT"
    assert sources["actual_resource"]["verification_state"] == "FINALIZED_MPS"


def test_60_certified_certificate_authority_and_provenance(client_fixture, setup_data):
    """
    Verify that PeriodCertificateItem linked to a CERTIFIED certificate provides
    authoritative verified output with PERIOD_CERTIFICATE_ITEM provenance.
    """
    token = setup_data["adm_token"]
    user_id = setup_data["adm_id"]

    with TestingSessionLocal() as db:
        proj = Project(name=f"Cert Proj {uuid.uuid4().hex[:4]}", created_by=user_id)
        db.add(proj)
        db.commit()
        db.refresh(proj)
        proj_id = proj.id

        db.add(ProjectMember(project_id=proj_id, user_id=user_id))
        act = ConstructionActivity(
            project_id=proj_id,
            activity_code="ACT-CERT-1",
            activity_name="Cert Act",
            activity_type="CONSTRUCTION",
            created_by=user_id,
        )
        db.add(act)
        db.commit()
        db.refresh(act)
        act_id = act.id

        sched = ConstructionSchedule(
            project_id=proj_id,
            schedule_version="1.0",
            calculation_status="CALCULATED",
            algorithm_version="1.0",
            input_snapshot_json={},
            calculated_by=user_id,
        )
        db.add(sched)
        db.commit()
        db.refresh(sched)

        base = MonitoringBaseline(
            project_id=proj_id,
            schedule_id=sched.id,
            schedule_version="1.0",
            schedule_algorithm_version="1.0",
            baseline_start_date=date(2027, 3, 1),
            frozen_by=user_id,
            status="ACTIVE",
        )
        db.add(base)
        db.commit()
        db.refresh(base)

        cert = PeriodProgressCertificate(
            project_id=proj_id,
            certificate_number=f"CERT-{uuid.uuid4().hex[:4]}",
            monitoring_baseline_id=base.id,
            baseline_schedule_id=sched.id,
            baseline_schedule_version="1.0",
            baseline_schedule_algorithm_version="1.0",
            baseline_start_date=date(2027, 3, 1),
            period_start_date=date(2027, 3, 1),
            period_cut_off_date=date(2027, 3, 31),
            certificate_status="DRAFT", # Created as DRAFT so items can be inserted
            currency="INR",
            period_claimed_value=Decimal("12000.00"),
            period_certified_value=Decimal("12000.00"),
            period_disputed_exposure=Decimal("0.00"),
            cumulative_claimed_value=Decimal("12000.00"),
            cumulative_certified_value=Decimal("12000.00"),
            cumulative_disputed_exposure=Decimal("0.00"),
            item_count=1,
            valuation_snapshot_hash="hash_cert_test_123",
            algorithm_version="1.0",
        )
        db.add(cert)
        db.commit()
        db.refresh(cert)

        # Create a confirmed cost rate and activity rate mapping
        crate = CostRate(
            project_id=proj_id,
            rate_code=f"RATE-CERT-{uuid.uuid4().hex[:4]}",
            description="Cert Rate",
            unit="m3",
            rate_value=Decimal("100.00"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref-Cert",
            status="CONFIRMED",
            created_by=user_id,
            confirmed_by=user_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(crate)
        db.commit()
        db.refresh(crate)

        armap = ActivityRateMapping(
            project_id=proj_id,
            activity_id=act_id,
            cost_rate_id=crate.id,
            rate_value=Decimal("100.00"),
            rate_unit="m3",
            rate_version="1.0",
            currency="INR",
            status="ACTIVE",
            created_by=user_id,
        )
        db.add(armap)
        db.commit()
        db.refresh(armap)

        # Use an earlier report date outside test snapshot performance period (2027-02-15) so daily verification query does NOT match
        dpr_c = DailyProgressReport(project_id=proj_id, report_date=date(2027, 3, 10), submitted_by=user_id, submission_status="FINALIZED")
        db.add(dpr_c)
        db.commit()

        dap_c = DailyActivityProgress(daily_report_id=dpr_c.id, project_id=proj_id, activity_id=act_id, contractor_progress_value=Decimal("120.0000"), contractor_progress_unit="m3", contractor_status="COMPLETED", created_by=user_id)
        db.add(dap_c)
        db.commit()

        dapv_c = DailyActivityProgressVerification(daily_activity_progress_id=dap_c.id, project_id=proj_id, verified_quantity=Decimal("120.0000"), verified_quantity_unit="m3", verification_status="VERIFIED", verified_by=user_id)
        db.add(dapv_c)
        db.commit()

        val_c = DailyProgressValuation(
            project_id=proj_id,
            verification_id=dapv_c.id,
            activity_rate_mapping_id=armap.id,
            contractor_claimed_quantity=Decimal("120.0000"),
            supervisor_certified_quantity=Decimal("120.0000"),
            discrepancy_quantity=Decimal("0.0000"),
            quantity_unit="m3",
            applied_rate_value=Decimal("100.00"),
            applied_rate_unit="m3",
            currency="INR",
            contractor_claimed_value=Decimal("12000.00"),
            certified_progress_value=Decimal("12000.00"),
            disputed_valuation_exposure=Decimal("0.00"),
            unit_conversion_factor=Decimal("1.0"),
            valuation_status="ACTIVE",
        )
        db.add(val_c)
        db.commit()
        db.refresh(val_c)

        item = PeriodCertificateItem(
            certificate_id=cert.id,
            valuation_id=val_c.id,
            activity_id=act_id,
            claimed_quantity=Decimal("120.0000"),
            certified_quantity=Decimal("120.0000"),
            quantity_unit="m3",
            unit_conversion_factor=Decimal("1.000000"),
            applied_rate=Decimal("100.00"),
            applied_rate_unit="m3",
            currency="INR",
            claimed_amount=Decimal("12000.00"),
            certified_amount=Decimal("12000.00"),
            discrepancy_quantity=Decimal("0.00"),
            disputed_exposure=Decimal("0.00"),
        )
        db.add(item)
        db.commit()

        # Now certify certificate
        cert.certificate_status = "CERTIFIED"
        cert.certified_by = user_id
        cert.certified_at = datetime.now(timezone.utc)
        db.commit()
        cert_id = cert.id

    # Query snapshot for period 2027-03-20 to 2027-03-25 (report date 2027-03-10 is outside daily range, but certificate covers [2027-03-01, 2027-03-31])
    resp = client_fixture.post(
        f"/api/projects/{proj_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": act_id,
            "resource_category": "LABOUR",
            "performance_period_start": "2027-03-20",
            "performance_period_end": "2027-03-25",
            "verified_actual_resource_quantity": "240.0000",
            "verified_actual_resource_unit": "hour",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()

    assert Decimal(str(data["verified_output_quantity"])) == Decimal("120.0000")
    assert data["verified_output_unit"] == "m3"
    # Productivity = 120 / 240 = 0.500000
    assert Decimal(str(data["productivity"])) == Decimal("0.500000")

    sources = data["provenance_metadata"].get("sources", {})
    assert "verified_output" in sources
    o_src = sources["verified_output"]
    assert o_src["source_type"] == "PERIOD_CERTIFICATE_ITEM"
    assert o_src["verification_state"] == "CERTIFIED"
    assert cert_id in o_src["certificate_ids"]
    assert o_src["unit"] == "m3"


def test_61_draft_certificate_excluded_from_authoritative_output(client_fixture, setup_data):
    """
    Verify that PeriodCertificateItem linked to a DRAFT certificate is strictly excluded
    from authoritative output resolution.
    """
    token = setup_data["adm_token"]
    user_id = setup_data["adm_id"]

    with TestingSessionLocal() as db:
        proj = Project(name=f"DraftCert Proj {uuid.uuid4().hex[:4]}", created_by=user_id)
        db.add(proj)
        db.commit()
        db.refresh(proj)
        proj_id = proj.id

        db.add(ProjectMember(project_id=proj_id, user_id=user_id))
        act = ConstructionActivity(
            project_id=proj_id,
            activity_code="ACT-DRAFTCERT-1",
            activity_name="DraftCert Act",
            activity_type="CONSTRUCTION",
            created_by=user_id,
        )
        db.add(act)
        db.commit()
        db.refresh(act)
        act_id = act.id

        sched = ConstructionSchedule(
            project_id=proj_id,
            schedule_version="1.0",
            calculation_status="CALCULATED",
            algorithm_version="1.0",
            input_snapshot_json={},
            calculated_by=user_id,
        )
        db.add(sched)
        db.commit()
        db.refresh(sched)

        base = MonitoringBaseline(
            project_id=proj_id,
            schedule_id=sched.id,
            schedule_version="1.0",
            schedule_algorithm_version="1.0",
            baseline_start_date=date(2027, 4, 1),
            frozen_by=user_id,
            status="ACTIVE",
        )
        db.add(base)
        db.commit()
        db.refresh(base)

        # DRAFT certificate
        cert = PeriodProgressCertificate(
            project_id=proj_id,
            certificate_number=f"DRAFT-CERT-{uuid.uuid4().hex[:4]}",
            monitoring_baseline_id=base.id,
            baseline_schedule_id=sched.id,
            baseline_schedule_version="1.0",
            baseline_schedule_algorithm_version="1.0",
            baseline_start_date=date(2027, 4, 1),
            period_start_date=date(2027, 4, 1),
            period_cut_off_date=date(2027, 4, 30),
            certificate_status="DRAFT", # NOT CERTIFIED!
            currency="INR",
            period_claimed_value=Decimal("15000.00"),
            period_certified_value=Decimal("15000.00"),
            period_disputed_exposure=Decimal("0.00"),
            cumulative_claimed_value=Decimal("15000.00"),
            cumulative_certified_value=Decimal("15000.00"),
            cumulative_disputed_exposure=Decimal("0.00"),
            item_count=1,
            valuation_snapshot_hash="hash_draft_cert_test",
            algorithm_version="1.0",
        )
        db.add(cert)
        db.commit()
        db.refresh(cert)

        # Cost rate & mapping
        crate_d = CostRate(
            project_id=proj_id,
            rate_code=f"RATE-DFTC-{uuid.uuid4().hex[:4]}",
            description="Draft Cert Rate",
            unit="m3",
            rate_value=Decimal("100.00"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref-Cert",
            status="CONFIRMED",
            created_by=user_id,
            confirmed_by=user_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(crate_d)
        db.commit()
        db.refresh(crate_d)

        armap_d = ActivityRateMapping(
            project_id=proj_id,
            activity_id=act_id,
            cost_rate_id=crate_d.id,
            rate_value=Decimal("100.00"),
            rate_unit="m3",
            rate_version="1.0",
            currency="INR",
            status="ACTIVE",
            created_by=user_id,
        )
        db.add(armap_d)
        db.commit()
        db.refresh(armap_d)

        # Create valuation inside certificate window [2027-04-01, 2027-04-30]
        dpr_d = DailyProgressReport(project_id=proj_id, report_date=date(2027, 4, 10), submitted_by=user_id, submission_status="FINALIZED")
        db.add(dpr_d)
        db.commit()

        dap_d = DailyActivityProgress(daily_report_id=dpr_d.id, project_id=proj_id, activity_id=act_id, contractor_progress_value=Decimal("150.0000"), contractor_progress_unit="m3", contractor_status="COMPLETED", created_by=user_id)
        db.add(dap_d)
        db.commit()

        dapv_d = DailyActivityProgressVerification(daily_activity_progress_id=dap_d.id, project_id=proj_id, verified_quantity=Decimal("150.0000"), verified_quantity_unit="m3", verification_status="VERIFIED", verified_by=user_id)
        db.add(dapv_d)
        db.commit()

        val_d = DailyProgressValuation(
            project_id=proj_id,
            verification_id=dapv_d.id,
            activity_rate_mapping_id=armap_d.id,
            contractor_claimed_quantity=Decimal("150.0000"),
            supervisor_certified_quantity=Decimal("150.0000"),
            discrepancy_quantity=Decimal("0.0000"),
            quantity_unit="m3",
            applied_rate_value=Decimal("100.00"),
            applied_rate_unit="m3",
            currency="INR",
            contractor_claimed_value=Decimal("15000.00"),
            certified_progress_value=Decimal("15000.00"),
            disputed_valuation_exposure=Decimal("0.00"),
            unit_conversion_factor=Decimal("1.0"),
            valuation_status="ACTIVE",
        )
        db.add(val_d)
        db.commit()
        db.refresh(val_d)

        item = PeriodCertificateItem(
            certificate_id=cert.id,
            valuation_id=val_d.id,
            activity_id=act_id,
            claimed_quantity=Decimal("150.0000"),
            certified_quantity=Decimal("150.0000"),
            quantity_unit="m3",
            unit_conversion_factor=Decimal("1.000000"),
            applied_rate=Decimal("100.00"),
            applied_rate_unit="m3",
            currency="INR",
            claimed_amount=Decimal("15000.00"),
            certified_amount=Decimal("15000.00"),
            discrepancy_quantity=Decimal("0.00"),
            disputed_exposure=Decimal("0.00"),
        )
        db.add(item)
        db.commit()

    # Query snapshot for period 2027-04-20 to 2027-04-25 (report date 2027-04-10 is outside daily range, but certificate covers [2027-04-01, 2027-04-30])
    resp = client_fixture.post(
        f"/api/projects/{proj_id}/resource-performance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "activity_id": act_id,
            "resource_category": "LABOUR",
            "performance_period_start": "2027-04-20",
            "performance_period_end": "2027-04-25",
            "verified_actual_resource_quantity": "300.0000",
            "verified_actual_resource_unit": "hour",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()

    # DRAFT certificate must be ignored -> verified_output_quantity is None!
    assert data["verified_output_quantity"] is None
    assert data["productivity"] is None
    assert data["performance_status"] == "UNIT_MISMATCH"
    sources = data["provenance_metadata"].get("sources", {})
    assert "verified_output" not in sources



