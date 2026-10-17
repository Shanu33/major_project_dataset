import uuid
from datetime import date, timedelta
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
    EngineeringElement,
    EngineeringCalculation,
    ConstructionActivity,
    ConstructionSchedule,
    ActivityScheduleResult,
    MonitoringBaseline,
    DailyProgressReport,
    DailyActivityProgress,
    DailyActivityProgressVerification,
    AuditLog,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def client_fixture():
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="module")
def setup_monitoring(client_fixture):
    # Setup test users: admin, supervisor, contractor, outsider
    admin_email = f"admin_mon_{uuid.uuid4().hex[:6]}@test.com"
    client_fixture.post("/api/auth/register/admin", json={"email": admin_email, "password": "pass", "role": "admin"})
    admin_token = client_fixture.post("/api/auth/login", data={"username": admin_email, "password": "pass"}).json()["access_token"]

    sup_email = f"sup_mon_{uuid.uuid4().hex[:6]}@test.com"
    con_email = f"con_mon_{uuid.uuid4().hex[:6]}@test.com"
    out_email = f"out_mon_{uuid.uuid4().hex[:6]}@test.com"

    client_fixture.post("/api/auth/users", json={"email": sup_email, "password": "p", "role": "supervisor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post("/api/auth/users", json={"email": con_email, "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post("/api/auth/users", json={"email": out_email, "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})

    sup_token = client_fixture.post("/api/auth/login", data={"username": sup_email, "password": "p"}).json()["access_token"]
    con_token = client_fixture.post("/api/auth/login", data={"username": con_email, "password": "p"}).json()["access_token"]
    out_token = client_fixture.post("/api/auth/login", data={"username": out_email, "password": "p"}).json()["access_token"]

    # Create project 1 owned by admin, add contractor and supervisor as members
    p_resp = client_fixture.post("/api/projects", json={"name": f"Monitoring Project 1 {uuid.uuid4().hex[:6]}"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert p_resp.status_code == 200
    project_id = p_resp.json()["id"]

    # Create project 2 for cross-project isolation tests
    p2_resp = client_fixture.post("/api/projects", json={"name": f"Monitoring Project 2 {uuid.uuid4().hex[:6]}"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert p2_resp.status_code == 200
    project_id_2 = p2_resp.json()["id"]

    db = TestingSessionLocal()
    con_user = db.query(User).filter(User.email == con_email).first()
    sup_user = db.query(User).filter(User.email == sup_email).first()
    pm1 = ProjectMember(project_id=project_id, user_id=con_user.id)
    pm2 = ProjectMember(project_id=project_id, user_id=sup_user.id)
    db.add(pm1)
    db.add(pm2)
    db.commit()
    db.close()

    return {
        "admin_token": admin_token,
        "sup_token": sup_token,
        "con_token": con_token,
        "out_token": out_token,
        "project_id": project_id,
        "project_id_2": project_id_2,
    }


# ==============================================================================
# GROUP 1: BASELINE (Scenarios 1 - 12)
# ==============================================================================

def test_01_baseline_start_date_accepted(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    project_id = setup_monitoring["project_id"]

    client_fixture.post(
        f"/api/projects/{project_id}/activities",
        json={"activity_code": f"B1-{uuid.uuid4().hex[:4]}", "activity_name": "Base Act 1", "activity_type": "EXCAVATION", "duration_value": 3.0, "duration_unit": "day"},
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    sched = client_fixture.post(f"/api/projects/{project_id}/schedules/calculate", headers={"Authorization": f"Bearer {sup_token}"}).json()

    resp = client_fixture.post(
        f"/api/projects/{project_id}/monitoring-baselines",
        json={"schedule_id": sched["id"], "baseline_start_date": "2026-10-01"},
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["baseline_start_date"] == "2026-10-01"


def test_02_baseline_start_date_returned_by_api(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    project_id = setup_monitoring["project_id"]

    sched = client_fixture.post(f"/api/projects/{project_id}/schedules/calculate", headers={"Authorization": f"Bearer {sup_token}"}).json()
    b_resp = client_fixture.post(
        f"/api/projects/{project_id}/monitoring-baselines",
        json={"schedule_id": sched["id"], "baseline_start_date": "2026-11-15"},
        headers={"Authorization": f"Bearer {sup_token}"},
    ).json()

    get_resp = client_fixture.get(
        f"/api/projects/{project_id}/monitoring-baselines/{b_resp['id']}",
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["baseline_start_date"] == "2026-11-15"


def test_03_schedule_algorithm_version_copied_exactly(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    project_id = setup_monitoring["project_id"]

    sched = client_fixture.post(f"/api/projects/{project_id}/schedules/calculate", headers={"Authorization": f"Bearer {sup_token}"}).json()
    b_resp = client_fixture.post(
        f"/api/projects/{project_id}/monitoring-baselines",
        json={"schedule_id": sched["id"], "baseline_start_date": "2026-10-01"},
        headers={"Authorization": f"Bearer {sup_token}"},
    ).json()

    assert b_resp["schedule_algorithm_version"] == sched["algorithm_version"]


def test_04_missing_algorithm_version_rejected_for_new_baseline(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    project_id = setup_monitoring["project_id"]

    # Insert a dummy schedule with empty algorithm_version
    db = TestingSessionLocal()
    fake_sched_id = str(uuid.uuid4())
    db.execute(
        text("INSERT INTO construction_schedules (id, project_id, schedule_version, calculation_status, calculated_by, algorithm_version, input_snapshot_json) "
             "VALUES (:id, :pid, 'V_NO_ALGO', 'CALCULATED', (SELECT id FROM users LIMIT 1), '', '{}'::json)"),
        {"id": fake_sched_id, "pid": project_id}
    )
    db.commit()
    db.close()

    resp = client_fixture.post(
        f"/api/projects/{project_id}/monitoring-baselines",
        json={"schedule_id": fake_sched_id, "baseline_start_date": "2026-10-01"},
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert resp.status_code == 400
    assert "algorithm_version is missing" in resp.json()["detail"]


def test_05_baseline_start_date_sql_mutation_rejected(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    project_id = setup_monitoring["project_id"]

    sched = client_fixture.post(f"/api/projects/{project_id}/schedules/calculate", headers={"Authorization": f"Bearer {sup_token}"}).json()
    b = client_fixture.post(
        f"/api/projects/{project_id}/monitoring-baselines",
        json={"schedule_id": sched["id"], "baseline_start_date": "2026-10-01"},
        headers={"Authorization": f"Bearer {sup_token}"},
    ).json()

    db = TestingSessionLocal()
    try:
        with pytest.raises(Exception) as exc_info:
            db.execute(text("UPDATE monitoring_baselines SET baseline_start_date = '2026-12-01' WHERE id = :bid"), {"bid": b["id"]})
            db.commit()
        db.rollback()
        assert "historical attributes cannot be modified" in str(exc_info.value)
    finally:
        db.close()


def test_06_schedule_algorithm_version_sql_mutation_rejected(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    project_id = setup_monitoring["project_id"]

    sched = client_fixture.post(f"/api/projects/{project_id}/schedules/calculate", headers={"Authorization": f"Bearer {sup_token}"}).json()
    b = client_fixture.post(
        f"/api/projects/{project_id}/monitoring-baselines",
        json={"schedule_id": sched["id"], "baseline_start_date": "2026-10-01"},
        headers={"Authorization": f"Bearer {sup_token}"},
    ).json()

    db = TestingSessionLocal()
    try:
        with pytest.raises(Exception) as exc_info:
            db.execute(text("UPDATE monitoring_baselines SET schedule_algorithm_version = 'CPM_MUTATED' WHERE id = :bid"), {"bid": b["id"]})
            db.commit()
        db.rollback()
        assert "historical attributes cannot be modified" in str(exc_info.value)
    finally:
        db.close()


def test_07_schedule_id_sql_mutation_rejected(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    project_id = setup_monitoring["project_id"]

    sched = client_fixture.post(f"/api/projects/{project_id}/schedules/calculate", headers={"Authorization": f"Bearer {sup_token}"}).json()
    b = client_fixture.post(
        f"/api/projects/{project_id}/monitoring-baselines",
        json={"schedule_id": sched["id"], "baseline_start_date": "2026-10-01"},
        headers={"Authorization": f"Bearer {sup_token}"},
    ).json()

    db = TestingSessionLocal()
    try:
        with pytest.raises(Exception) as exc_info:
            db.execute(text("UPDATE monitoring_baselines SET schedule_id = :sid WHERE id = :bid"), {"sid": str(uuid.uuid4()), "bid": b["id"]})
            db.commit()
        db.rollback()
        assert "historical attributes cannot be modified" in str(exc_info.value)
    finally:
        db.close()


def test_08_project_id_sql_mutation_rejected(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    project_id = setup_monitoring["project_id"]

    sched = client_fixture.post(f"/api/projects/{project_id}/schedules/calculate", headers={"Authorization": f"Bearer {sup_token}"}).json()
    b = client_fixture.post(
        f"/api/projects/{project_id}/monitoring-baselines",
        json={"schedule_id": sched["id"], "baseline_start_date": "2026-10-01"},
        headers={"Authorization": f"Bearer {sup_token}"},
    ).json()

    db = TestingSessionLocal()
    try:
        with pytest.raises(Exception) as exc_info:
            db.execute(text("UPDATE monitoring_baselines SET project_id = :pid WHERE id = :bid"), {"pid": str(uuid.uuid4()), "bid": b["id"]})
            db.commit()
        db.rollback()
        assert "historical attributes cannot be modified" in str(exc_info.value)
    finally:
        db.close()


def test_09_frozen_at_sql_mutation_rejected(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    project_id = setup_monitoring["project_id"]

    sched = client_fixture.post(f"/api/projects/{project_id}/schedules/calculate", headers={"Authorization": f"Bearer {sup_token}"}).json()
    b = client_fixture.post(
        f"/api/projects/{project_id}/monitoring-baselines",
        json={"schedule_id": sched["id"], "baseline_start_date": "2026-10-01"},
        headers={"Authorization": f"Bearer {sup_token}"},
    ).json()

    db = TestingSessionLocal()
    try:
        with pytest.raises(Exception) as exc_info:
            db.execute(text("UPDATE monitoring_baselines SET frozen_at = NOW() - INTERVAL '10 days' WHERE id = :bid"), {"bid": b["id"]})
            db.commit()
        db.rollback()
        assert "historical attributes cannot be modified" in str(exc_info.value)
    finally:
        db.close()


def test_10_baseline_delete_rejected(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    project_id = setup_monitoring["project_id"]

    sched = client_fixture.post(f"/api/projects/{project_id}/schedules/calculate", headers={"Authorization": f"Bearer {sup_token}"}).json()
    b = client_fixture.post(
        f"/api/projects/{project_id}/monitoring-baselines",
        json={"schedule_id": sched["id"], "baseline_start_date": "2026-10-01"},
        headers={"Authorization": f"Bearer {sup_token}"},
    ).json()

    db = TestingSessionLocal()
    try:
        with pytest.raises(Exception) as exc_info:
            db.execute(text("DELETE FROM monitoring_baselines WHERE id = :bid"), {"bid": b["id"]})
            db.commit()
        db.rollback()
        assert "cannot be deleted" in str(exc_info.value)
    finally:
        db.close()


def test_11_active_baseline_can_become_superseded(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    project_id = setup_monitoring["project_id"]

    sched = client_fixture.post(f"/api/projects/{project_id}/schedules/calculate", headers={"Authorization": f"Bearer {sup_token}"}).json()
    b1 = client_fixture.post(
        f"/api/projects/{project_id}/monitoring-baselines",
        json={"schedule_id": sched["id"], "baseline_start_date": "2026-10-01"},
        headers={"Authorization": f"Bearer {sup_token}"},
    ).json()
    assert b1["status"] == "ACTIVE"

    # Creating a new baseline must supersede the previous one
    b2 = client_fixture.post(
        f"/api/projects/{project_id}/monitoring-baselines",
        json={"schedule_id": sched["id"], "baseline_start_date": "2026-10-05"},
        headers={"Authorization": f"Bearer {sup_token}"},
    ).json()
    assert b2["status"] == "ACTIVE"

    b1_refreshed = client_fixture.get(f"/api/projects/{project_id}/monitoring-baselines/{b1['id']}", headers={"Authorization": f"Bearer {sup_token}"}).json()
    assert b1_refreshed["status"] == "SUPERSEDED"


def test_12_only_one_active_baseline_exists(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    project_id = setup_monitoring["project_id"]

    active_list = client_fixture.get(f"/api/projects/{project_id}/monitoring-baselines?status=ACTIVE", headers={"Authorization": f"Bearer {sup_token}"}).json()
    assert len(active_list) == 1

    # Verify that directly inserting a second ACTIVE baseline in SQL is rejected by DB unique index
    db = TestingSessionLocal()
    try:
        sched_id = db.query(ConstructionSchedule.id).filter(ConstructionSchedule.project_id == project_id).first()[0]
        user_id = db.query(User.id).first()[0]
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("INSERT INTO monitoring_baselines (id, project_id, schedule_id, schedule_version, schedule_algorithm_version, baseline_start_date, frozen_by, status) "
                     "VALUES (:id, :pid, :sid, 'V1', 'CPM_1.0', '2026-10-01', :uid, 'ACTIVE')"),
                {"id": str(uuid.uuid4()), "pid": project_id, "sid": sched_id, "uid": user_id}
            )
            db.commit()
        db.rollback()
        assert "uq_monitoring_baseline_active_per_project" in str(exc_info.value)
    finally:
        db.close()


# ==============================================================================
# GROUP 2: CALENDAR / VARIANCE (Scenarios 13 - 23)
# ==============================================================================

@pytest.fixture(scope="module")
def setup_variance_scenario(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    project_id = setup_monitoring["project_id"]

    # Engineering Element
    elem = client_fixture.post(
        f"/api/projects/{project_id}/engineering-elements",
        json={"element_type": "SLAB", "element_name": f"PVA Slab {uuid.uuid4().hex[:4]}"},
        headers={"Authorization": f"Bearer {sup_token}"},
    ).json()

    # Calculation: 50.0 m3
    db = TestingSessionLocal()
    calc_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO engineering_calculations "
            "(id, project_id, engineering_element_id, calculation_type, calculation_version, formula_identifier, "
            "formula_expression, inputs_json, result_value, result_unit, status, created_by) "
            "VALUES (:id, :pid, :eid, 'CONCRETE_VOLUME_RECTANGULAR', '1.0', 'RECT_VOL', 'l*w*d', "
            "'{}'::jsonb, 50.0, 'm3', 'CALCULATED', (SELECT id FROM users LIMIT 1))"
        ),
        {"id": calc_id, "pid": project_id, "eid": elem["id"]},
    )
    db.commit()
    db.close()

    # Activity duration = 5 days (ES=0, EF=5)
    act = client_fixture.post(
        f"/api/projects/{project_id}/activities",
        json={
            "activity_code": f"ACT-CAL-{uuid.uuid4().hex[:4]}",
            "activity_name": "Cal Act",
            "activity_type": "CONCRETING",
            "duration_value": 5.0,
            "duration_unit": "day",
            "engineering_element_id": elem["id"],
        },
        headers={"Authorization": f"Bearer {sup_token}"},
    ).json()

    sched = client_fixture.post(f"/api/projects/{project_id}/schedules/calculate", headers={"Authorization": f"Bearer {sup_token}"}).json()

    # Freeze baseline with authoritative calendar anchor 2026-10-01
    baseline = client_fixture.post(
        f"/api/projects/{project_id}/monitoring-baselines",
        json={"schedule_id": sched["id"], "baseline_start_date": "2026-10-01"},
        headers={"Authorization": f"Bearer {sup_token}"},
    ).json()

    report = client_fixture.post(
        f"/api/projects/{project_id}/daily-progress-reports",
        json={"report_date": "2026-10-10"},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()

    return {
        "project_id": project_id,
        "element_id": elem["id"],
        "activity_id": act["id"],
        "schedule_id": sched["id"],
        "baseline_id": baseline["id"],
        "report_id": report["id"],
    }


def test_13_baseline_start_date_produces_planned_start(client_fixture, setup_monitoring, setup_variance_scenario):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    sc = setup_variance_scenario

    p = client_fixture.post(
        f"/api/projects/{sc['project_id']}/daily-progress-reports/{sc['report_id']}/activities",
        json={"activity_id": sc["activity_id"], "contractor_actual_start": "2026-10-01", "contractor_actual_finish": "2026-10-06"},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()

    v = client_fixture.get(f"/api/projects/{sc['project_id']}/progress/{p['id']}/variance", headers={"Authorization": f"Bearer {sup_token}"}).json()
    assert v["planned_start"] == "2026-10-01"


def test_14_baseline_start_date_produces_planned_finish(client_fixture, setup_monitoring, setup_variance_scenario):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    sc = setup_variance_scenario

    p = client_fixture.post(
        f"/api/projects/{sc['project_id']}/daily-progress-reports/{sc['report_id']}/activities",
        json={"activity_id": sc["activity_id"], "contractor_actual_start": "2026-10-01", "contractor_actual_finish": "2026-10-06"},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()

    v = client_fixture.get(f"/api/projects/{sc['project_id']}/progress/{p['id']}/variance", headers={"Authorization": f"Bearer {sup_token}"}).json()
    # 2026-10-01 + 5 days = 2026-10-06
    assert v["planned_finish"] == "2026-10-06"


def test_15_finish_variance_positive_delayed(client_fixture, setup_monitoring, setup_variance_scenario):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    sc = setup_variance_scenario

    # Planned finish: 2026-10-06, actual finish: 2026-10-08 -> finish_variance = +2 -> DELAYED
    p = client_fixture.post(
        f"/api/projects/{sc['project_id']}/daily-progress-reports/{sc['report_id']}/activities",
        json={"activity_id": sc["activity_id"], "contractor_actual_start": "2026-10-01", "contractor_actual_finish": "2026-10-08"},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()

    v = client_fixture.get(f"/api/projects/{sc['project_id']}/progress/{p['id']}/variance", headers={"Authorization": f"Bearer {sup_token}"}).json()
    assert Decimal(str(v["finish_variance"])) == Decimal("2")
    assert v["variance_status"] == "DELAYED"
    assert v["status"] == "DELAYED"


def test_16_finish_variance_zero_on_schedule(client_fixture, setup_monitoring, setup_variance_scenario):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    sc = setup_variance_scenario

    # Planned finish: 2026-10-06, actual finish: 2026-10-06 -> finish_variance = 0 -> ON_SCHEDULE
    p = client_fixture.post(
        f"/api/projects/{sc['project_id']}/daily-progress-reports/{sc['report_id']}/activities",
        json={"activity_id": sc["activity_id"], "contractor_actual_start": "2026-10-01", "contractor_actual_finish": "2026-10-06"},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()

    v = client_fixture.get(f"/api/projects/{sc['project_id']}/progress/{p['id']}/variance", headers={"Authorization": f"Bearer {sup_token}"}).json()
    assert Decimal(str(v["finish_variance"])) == Decimal("0")
    assert v["variance_status"] == "ON_SCHEDULE"
    assert v["status"] == "ON_SCHEDULE"


def test_17_finish_variance_negative_ahead(client_fixture, setup_monitoring, setup_variance_scenario):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    sc = setup_variance_scenario

    # Planned finish: 2026-10-06, actual finish: 2026-10-04 -> finish_variance = -2 -> AHEAD
    p = client_fixture.post(
        f"/api/projects/{sc['project_id']}/daily-progress-reports/{sc['report_id']}/activities",
        json={"activity_id": sc["activity_id"], "contractor_actual_start": "2026-10-01", "contractor_actual_finish": "2026-10-04"},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()

    v = client_fixture.get(f"/api/projects/{sc['project_id']}/progress/{p['id']}/variance", headers={"Authorization": f"Bearer {sup_token}"}).json()
    assert Decimal(str(v["finish_variance"])) == Decimal("-2")
    assert v["variance_status"] == "AHEAD"
    assert v["status"] == "AHEAD"


def test_18_missing_baseline_start_date_not_available(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    admin_token = setup_monitoring["admin_token"]

    # Dedicated project for test_18 to test legacy baseline without baseline_start_date
    p_resp = client_fixture.post("/api/projects", json={"name": f"P18 {uuid.uuid4().hex[:4]}"}, headers={"Authorization": f"Bearer {admin_token}"}).json()
    p_id = p_resp["id"]

    db = TestingSessionLocal()
    con_user = db.query(User).filter(User.role == "contractor").first()
    sup_user = db.query(User).filter(User.role == "supervisor").first()
    db.add(ProjectMember(project_id=p_id, user_id=con_user.id))
    db.add(ProjectMember(project_id=p_id, user_id=sup_user.id))
    db.commit()

    # Activity & Schedule
    act = client_fixture.post(
        f"/api/projects/{p_id}/activities",
        json={"activity_code": f"ACT-18-{uuid.uuid4().hex[:4]}", "activity_name": "Act 18", "activity_type": "EXCAVATION", "duration_value": 3.0, "duration_unit": "day"},
        headers={"Authorization": f"Bearer {sup_token}"},
    ).json()
    sched = client_fixture.post(f"/api/projects/{p_id}/schedules/calculate", headers={"Authorization": f"Bearer {sup_token}"}).json()

    # Insert a legacy baseline without baseline_start_date
    legacy_base_id = str(uuid.uuid4())
    db.execute(
        text("INSERT INTO monitoring_baselines (id, project_id, schedule_id, schedule_version, schedule_algorithm_version, baseline_start_date, frozen_by, status) "
             "VALUES (:id, :pid, :sid, 'LEGACY_V', 'CPM_1.0', NULL, :uid, 'ACTIVE')"),
        {"id": legacy_base_id, "pid": p_id, "sid": sched["id"], "uid": sup_user.id}
    )
    db.commit()
    db.close()

    rep = client_fixture.post(
        f"/api/projects/{p_id}/daily-progress-reports",
        json={"report_date": "2026-10-10"},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()

    p = client_fixture.post(
        f"/api/projects/{p_id}/daily-progress-reports/{rep['id']}/activities",
        json={"activity_id": act["id"], "contractor_actual_start": "2026-10-01", "contractor_actual_finish": "2026-10-08"},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()

    v = client_fixture.get(f"/api/projects/{p_id}/progress/{p['id']}/variance", headers={"Authorization": f"Bearer {sup_token}"}).json()
    assert v["planned_start"] is None
    assert v["planned_finish"] is None
    assert v["finish_variance"] is None
    assert v["variance_status"] == "NOT_AVAILABLE"
    assert v["status"] == "NOT_AVAILABLE"


def test_19_missing_actual_finish_not_available(client_fixture, setup_monitoring, setup_variance_scenario):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    sc = setup_variance_scenario

    # Progress with only actual_start, no actual_finish
    p = client_fixture.post(
        f"/api/projects/{sc['project_id']}/daily-progress-reports/{sc['report_id']}/activities",
        json={"activity_id": sc["activity_id"], "contractor_actual_start": "2026-10-01"},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()

    v = client_fixture.get(f"/api/projects/{sc['project_id']}/progress/{p['id']}/variance", headers={"Authorization": f"Bearer {sup_token}"}).json()
    assert v["actual_finish"] is None
    assert v["finish_variance"] is None
    assert v["variance_status"] == "NOT_AVAILABLE"
    assert v["status"] == "NOT_AVAILABLE"


def test_20_duration_variance_calculated_correctly(client_fixture, setup_monitoring, setup_variance_scenario):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    sc = setup_variance_scenario

    # Planned duration = 5. Actual: 2026-10-01 to 2026-10-08 -> (8 - 1) + 1 = 8 days -> duration_variance = 8 - 5 = 3
    p = client_fixture.post(
        f"/api/projects/{sc['project_id']}/daily-progress-reports/{sc['report_id']}/activities",
        json={"activity_id": sc["activity_id"], "contractor_actual_start": "2026-10-01", "contractor_actual_finish": "2026-10-08"},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()

    v = client_fixture.get(f"/api/projects/{sc['project_id']}/progress/{p['id']}/variance", headers={"Authorization": f"Bearer {sup_token}"}).json()
    assert Decimal(str(v["planned_duration"])) == Decimal("5")
    assert Decimal(str(v["actual_duration"])) == Decimal("8")
    assert Decimal(str(v["duration_variance"])) == Decimal("3")


def test_21_actual_duration_uses_inclusive_plus_one_convention(client_fixture, setup_monitoring, setup_variance_scenario):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    sc = setup_variance_scenario

    # Same day start and finish: 2026-10-01 to 2026-10-01 -> (1 - 1) + 1 = 1 day
    p = client_fixture.post(
        f"/api/projects/{sc['project_id']}/daily-progress-reports/{sc['report_id']}/activities",
        json={"activity_id": sc["activity_id"], "contractor_actual_start": "2026-10-01", "contractor_actual_finish": "2026-10-01"},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()

    v = client_fixture.get(f"/api/projects/{sc['project_id']}/progress/{p['id']}/variance", headers={"Authorization": f"Bearer {sup_token}"}).json()
    assert Decimal(str(v["actual_duration"])) == Decimal("1")


def test_22_quantity_variance_only_with_compatible_units(client_fixture, setup_monitoring, setup_variance_scenario):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    sc = setup_variance_scenario

    # Planned quantity is 50.0 m3. Contractor reports 55.0 m3. Compatible units -> variance = 5.0
    p = client_fixture.post(
        f"/api/projects/{sc['project_id']}/daily-progress-reports/{sc['report_id']}/activities",
        json={"activity_id": sc["activity_id"], "contractor_progress_value": 55.0, "contractor_progress_unit": "m3"},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()

    v = client_fixture.get(f"/api/projects/{sc['project_id']}/progress/{p['id']}/variance", headers={"Authorization": f"Bearer {sup_token}"}).json()
    assert Decimal(str(v["planned_quantity"])) == Decimal("50.0")
    assert Decimal(str(v["operational_quantity"])) == Decimal("55.0")
    assert Decimal(str(v["quantity_variance"])) == Decimal("5.0")


def test_23_incompatible_quantity_units_null(client_fixture, setup_monitoring, setup_variance_scenario):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    sc = setup_variance_scenario

    # Planned quantity is 50.0 m3. Contractor reports 120.0 sqft. Incompatible units -> variance must be NULL
    p = client_fixture.post(
        f"/api/projects/{sc['project_id']}/daily-progress-reports/{sc['report_id']}/activities",
        json={"activity_id": sc["activity_id"], "contractor_progress_value": 120.0, "contractor_progress_unit": "sqft"},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()

    v = client_fixture.get(f"/api/projects/{sc['project_id']}/progress/{p['id']}/variance", headers={"Authorization": f"Bearer {sup_token}"}).json()
    assert Decimal(str(v["planned_quantity"])) == Decimal("50.0")
    assert Decimal(str(v["operational_quantity"])) == Decimal("120.0")
    assert v["quantity_variance"] is None


# ==============================================================================
# GROUP 3: OPERATIONAL VALUE (Scenarios 24 - 28)
# ==============================================================================

def test_24_contractor_value_preserved(client_fixture, setup_monitoring, setup_variance_scenario):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    sc = setup_variance_scenario

    p = client_fixture.post(
        f"/api/projects/{sc['project_id']}/daily-progress-reports/{sc['report_id']}/activities",
        json={"activity_id": sc["activity_id"], "contractor_progress_value": 20.0, "contractor_progress_unit": "m3", "contractor_percent_complete": 40.0},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()

    # Supervisor verifies with correction
    client_fixture.post(
        f"/api/projects/{sc['project_id']}/progress/{p['id']}/verify",
        json={"verification_status": "CORRECTED", "verified_quantity": 18.0, "verified_quantity_unit": "m3", "verified_percent_complete": 36.0},
        headers={"Authorization": f"Bearer {sup_token}"},
    )

    items = client_fixture.get(f"/api/projects/{sc['project_id']}/daily-progress-reports/{sc['report_id']}/activities", headers={"Authorization": f"Bearer {sup_token}"}).json()
    matched = [it for it in items if it["id"] == p["id"]][0]
    # Original contractor fields remain strictly intact
    assert Decimal(str(matched["contractor_progress_value"])) == Decimal("20.0")
    assert Decimal(str(matched["contractor_percent_complete"])) == Decimal("40.0")


def test_25_verified_supervisor_value_becomes_operational(client_fixture, setup_monitoring, setup_variance_scenario):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    sc = setup_variance_scenario

    p = client_fixture.post(
        f"/api/projects/{sc['project_id']}/daily-progress-reports/{sc['report_id']}/activities",
        json={"activity_id": sc["activity_id"], "contractor_progress_value": 30.0, "contractor_progress_unit": "m3", "contractor_percent_complete": 60.0},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()

    client_fixture.post(
        f"/api/projects/{sc['project_id']}/progress/{p['id']}/verify",
        json={"verification_status": "VERIFIED", "verified_quantity": 30.0, "verified_quantity_unit": "m3", "verified_percent_complete": 60.0},
        headers={"Authorization": f"Bearer {sup_token}"},
    )

    items = client_fixture.get(f"/api/projects/{sc['project_id']}/daily-progress-reports/{sc['report_id']}/activities", headers={"Authorization": f"Bearer {sup_token}"}).json()
    matched = [it for it in items if it["id"] == p["id"]][0]
    assert Decimal(str(matched["operational_value"])) == Decimal("30.0")
    assert Decimal(str(matched["operational_percent"])) == Decimal("60.0")
    assert matched["verification_status"] == "VERIFIED"


def test_26_corrected_supervisor_value_becomes_operational(client_fixture, setup_monitoring, setup_variance_scenario):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    sc = setup_variance_scenario

    p = client_fixture.post(
        f"/api/projects/{sc['project_id']}/daily-progress-reports/{sc['report_id']}/activities",
        json={"activity_id": sc["activity_id"], "contractor_progress_value": 40.0, "contractor_progress_unit": "m3", "contractor_percent_complete": 80.0},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()

    client_fixture.post(
        f"/api/projects/{sc['project_id']}/progress/{p['id']}/verify",
        json={"verification_status": "CORRECTED", "verified_quantity": 35.0, "verified_quantity_unit": "m3", "verified_percent_complete": 70.0},
        headers={"Authorization": f"Bearer {sup_token}"},
    )

    items = client_fixture.get(f"/api/projects/{sc['project_id']}/daily-progress-reports/{sc['report_id']}/activities", headers={"Authorization": f"Bearer {sup_token}"}).json()
    matched = [it for it in items if it["id"] == p["id"]][0]
    assert Decimal(str(matched["operational_value"])) == Decimal("35.0")
    assert Decimal(str(matched["operational_percent"])) == Decimal("70.0")
    assert matched["verification_status"] == "CORRECTED"


def test_27_rejected_verification_does_not_become_operational(client_fixture, setup_monitoring, setup_variance_scenario):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    sc = setup_variance_scenario

    p = client_fixture.post(
        f"/api/projects/{sc['project_id']}/daily-progress-reports/{sc['report_id']}/activities",
        json={"activity_id": sc["activity_id"], "contractor_progress_value": 15.0, "contractor_progress_unit": "m3", "contractor_percent_complete": 30.0},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()

    client_fixture.post(
        f"/api/projects/{sc['project_id']}/progress/{p['id']}/verify",
        json={"verification_status": "REJECTED", "verification_note": "Inspection failed"},
        headers={"Authorization": f"Bearer {sup_token}"},
    )

    items = client_fixture.get(f"/api/projects/{sc['project_id']}/daily-progress-reports/{sc['report_id']}/activities", headers={"Authorization": f"Bearer {sup_token}"}).json()
    matched = [it for it in items if it["id"] == p["id"]][0]
    # Operational value falls back to contractor value
    assert Decimal(str(matched["operational_value"])) == Decimal("15.0")
    assert Decimal(str(matched["operational_percent"])) == Decimal("30.0")
    assert matched["verification_status"] == "REJECTED"


def test_28_latest_verification_selection_is_deterministic(client_fixture, setup_monitoring, setup_variance_scenario):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    sc = setup_variance_scenario

    p = client_fixture.post(
        f"/api/projects/{sc['project_id']}/daily-progress-reports/{sc['report_id']}/activities",
        json={"activity_id": sc["activity_id"], "contractor_progress_value": 10.0, "contractor_progress_unit": "m3"},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()

    # First verification: VERIFIED 10.0
    client_fixture.post(
        f"/api/projects/{sc['project_id']}/progress/{p['id']}/verify",
        json={"verification_status": "VERIFIED", "verified_quantity": 10.0, "verified_quantity_unit": "m3"},
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    # Second verification later: CORRECTED 12.0
    client_fixture.post(
        f"/api/projects/{sc['project_id']}/progress/{p['id']}/verify",
        json={"verification_status": "CORRECTED", "verified_quantity": 12.0, "verified_quantity_unit": "m3"},
        headers={"Authorization": f"Bearer {sup_token}"},
    )

    v = client_fixture.get(f"/api/projects/{sc['project_id']}/progress/{p['id']}/variance", headers={"Authorization": f"Bearer {sup_token}"}).json()
    assert Decimal(str(v["operational_quantity"])) == Decimal("12.0")
    assert v["verification_status"] == "CORRECTED"


# ==============================================================================
# GROUP 4: LIFECYCLE (Scenarios 29 - 35)
# ==============================================================================

def test_29_draft_to_submitted_succeeds(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    project_id = setup_monitoring["project_id"]

    rep = client_fixture.post(
        f"/api/projects/{project_id}/daily-progress-reports",
        json={"report_date": (date.today() - timedelta(days=20)).isoformat()},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()
    assert rep["submission_status"] == "DRAFT"

    sub_resp = client_fixture.post(
        f"/api/projects/{project_id}/daily-progress-reports/{rep['id']}/submit",
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert sub_resp.status_code == 200
    assert sub_resp.json()["submission_status"] == "SUBMITTED"


def test_30_submitted_to_finalized_succeeds(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    project_id = setup_monitoring["project_id"]

    rep = client_fixture.post(
        f"/api/projects/{project_id}/daily-progress-reports",
        json={"report_date": (date.today() - timedelta(days=21)).isoformat()},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()

    client_fixture.post(
        f"/api/projects/{project_id}/daily-progress-reports/{rep['id']}/submit",
        headers={"Authorization": f"Bearer {con_token}"},
    )

    fin_resp = client_fixture.post(
        f"/api/projects/{project_id}/daily-progress-reports/{rep['id']}/finalize",
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert fin_resp.status_code == 200
    assert fin_resp.json()["submission_status"] == "FINALIZED"


def test_31_submitted_to_draft_rejected(client_fixture, setup_monitoring):
    con_token = setup_monitoring["con_token"]
    project_id = setup_monitoring["project_id"]

    rep = client_fixture.post(
        f"/api/projects/{project_id}/daily-progress-reports",
        json={"report_date": (date.today() - timedelta(days=22)).isoformat()},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()

    client_fixture.post(
        f"/api/projects/{project_id}/daily-progress-reports/{rep['id']}/submit",
        headers={"Authorization": f"Bearer {con_token}"},
    )

    db = TestingSessionLocal()
    try:
        with pytest.raises(Exception) as exc_info:
            db.execute(text("UPDATE daily_progress_reports SET submission_status = 'DRAFT' WHERE id = :rid"), {"rid": rep["id"]})
            db.commit()
        db.rollback()
        assert "Cannot transition daily report from SUBMITTED back to DRAFT" in str(exc_info.value)
    finally:
        db.close()


def test_32_finalized_to_draft_rejected(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    project_id = setup_monitoring["project_id"]

    rep = client_fixture.post(
        f"/api/projects/{project_id}/daily-progress-reports",
        json={"report_date": (date.today() - timedelta(days=23)).isoformat()},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()
    client_fixture.post(f"/api/projects/{project_id}/daily-progress-reports/{rep['id']}/submit", headers={"Authorization": f"Bearer {con_token}"})
    client_fixture.post(f"/api/projects/{project_id}/daily-progress-reports/{rep['id']}/finalize", headers={"Authorization": f"Bearer {sup_token}"})

    db = TestingSessionLocal()
    try:
        with pytest.raises(Exception) as exc_info:
            db.execute(text("UPDATE daily_progress_reports SET submission_status = 'DRAFT' WHERE id = :rid"), {"rid": rep["id"]})
            db.commit()
        db.rollback()
        assert "immutable" in str(exc_info.value)
    finally:
        db.close()


def test_33_finalized_to_submitted_rejected(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    project_id = setup_monitoring["project_id"]

    rep = client_fixture.post(
        f"/api/projects/{project_id}/daily-progress-reports",
        json={"report_date": (date.today() - timedelta(days=24)).isoformat()},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()
    client_fixture.post(f"/api/projects/{project_id}/daily-progress-reports/{rep['id']}/submit", headers={"Authorization": f"Bearer {con_token}"})
    client_fixture.post(f"/api/projects/{project_id}/daily-progress-reports/{rep['id']}/finalize", headers={"Authorization": f"Bearer {sup_token}"})

    db = TestingSessionLocal()
    try:
        with pytest.raises(Exception) as exc_info:
            db.execute(text("UPDATE daily_progress_reports SET submission_status = 'SUBMITTED' WHERE id = :rid"), {"rid": rep["id"]})
            db.commit()
        db.rollback()
        assert "immutable" in str(exc_info.value)
    finally:
        db.close()


def test_34_finalized_direct_sql_update_rejected(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    project_id = setup_monitoring["project_id"]

    rep = client_fixture.post(
        f"/api/projects/{project_id}/daily-progress-reports",
        json={"report_date": (date.today() - timedelta(days=25)).isoformat()},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()
    client_fixture.post(f"/api/projects/{project_id}/daily-progress-reports/{rep['id']}/submit", headers={"Authorization": f"Bearer {con_token}"})
    client_fixture.post(f"/api/projects/{project_id}/daily-progress-reports/{rep['id']}/finalize", headers={"Authorization": f"Bearer {sup_token}"})

    db = TestingSessionLocal()
    try:
        with pytest.raises(Exception) as exc_info:
            db.execute(text("UPDATE daily_progress_reports SET metadata_json = '{\"mutated\": true}' WHERE id = :rid"), {"rid": rep["id"]})
            db.commit()
        db.rollback()
        assert "immutable" in str(exc_info.value)
    finally:
        db.close()


def test_35_finalized_direct_sql_delete_rejected(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    con_token = setup_monitoring["con_token"]
    project_id = setup_monitoring["project_id"]

    rep = client_fixture.post(
        f"/api/projects/{project_id}/daily-progress-reports",
        json={"report_date": (date.today() - timedelta(days=26)).isoformat()},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()
    client_fixture.post(f"/api/projects/{project_id}/daily-progress-reports/{rep['id']}/submit", headers={"Authorization": f"Bearer {con_token}"})
    client_fixture.post(f"/api/projects/{project_id}/daily-progress-reports/{rep['id']}/finalize", headers={"Authorization": f"Bearer {sup_token}"})

    db = TestingSessionLocal()
    try:
        with pytest.raises(Exception) as exc_info:
            db.execute(text("DELETE FROM daily_progress_reports WHERE id = :rid"), {"rid": rep["id"]})
            db.commit()
        db.rollback()
        assert "immutable" in str(exc_info.value)
    finally:
        db.close()


# ==============================================================================
# GROUP 5: DATABASE CONSTRAINTS (Scenarios 36 - 42)
# ==============================================================================

def test_36_invalid_baseline_status_rejected(setup_monitoring):
    project_id = setup_monitoring["project_id"]
    db = TestingSessionLocal()
    try:
        sched_id = db.query(ConstructionSchedule.id).filter(ConstructionSchedule.project_id == project_id).first()[0]
        user_id = db.query(User.id).first()[0]
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("INSERT INTO monitoring_baselines (id, project_id, schedule_id, schedule_version, schedule_algorithm_version, frozen_by, status) "
                     "VALUES (:id, :pid, :sid, 'V1', 'CPM_1.0', :uid, 'INVALID_STATUS')"),
                {"id": str(uuid.uuid4()), "pid": project_id, "sid": sched_id, "uid": user_id}
            )
            db.commit()
        db.rollback()
        assert "ck_monitoring_baseline_status" in str(exc_info.value)
    finally:
        db.close()


def test_37_invalid_report_status_rejected(setup_monitoring):
    project_id = setup_monitoring["project_id"]
    db = TestingSessionLocal()
    try:
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("INSERT INTO daily_progress_reports (id, project_id, report_date, submitted_by, submission_status) "
                     "VALUES (:id, :pid, CURRENT_DATE, (SELECT id FROM users LIMIT 1), 'BOGUS')"),
                {"id": str(uuid.uuid4()), "pid": project_id}
            )
            db.commit()
        db.rollback()
        assert "ck_daily_progress_report_status" in str(exc_info.value)
    finally:
        db.close()


def test_38_invalid_activity_status_rejected(setup_monitoring, setup_variance_scenario):
    sc = setup_variance_scenario
    db = TestingSessionLocal()
    try:
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("INSERT INTO daily_activity_progress (id, daily_report_id, project_id, activity_id, contractor_status, created_by) "
                     "VALUES (:id, :rid, :pid, :aid, 'FLYING', (SELECT id FROM users LIMIT 1))"),
                {"id": str(uuid.uuid4()), "rid": sc["report_id"], "pid": sc["project_id"], "aid": sc["activity_id"]}
            )
            db.commit()
        db.rollback()
        assert "ck_daily_act_prog_status" in str(exc_info.value)
    finally:
        db.close()


def test_39_invalid_verification_status_rejected(setup_monitoring, setup_variance_scenario):
    sc = setup_variance_scenario
    db = TestingSessionLocal()
    try:
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("INSERT INTO daily_activity_progress_verifications (id, daily_activity_progress_id, project_id, verification_status, verified_by) "
                     "VALUES (:id, (SELECT id FROM daily_activity_progress WHERE project_id = :pid LIMIT 1), :pid, 'MAYBE', (SELECT id FROM users LIMIT 1))"),
                {"id": str(uuid.uuid4()), "pid": sc["project_id"]}
            )
            db.commit()
        db.rollback()
        assert "ck_verification_status" in str(exc_info.value)
    finally:
        db.close()


def test_40_missing_quantity_unit_rejected_where_required(setup_monitoring, setup_variance_scenario):
    sc = setup_variance_scenario
    db = TestingSessionLocal()
    try:
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("INSERT INTO daily_activity_progress (id, daily_report_id, project_id, activity_id, contractor_progress_value, contractor_progress_unit, created_by) "
                     "VALUES (:id, :rid, :pid, :aid, 15.0, NULL, (SELECT id FROM users LIMIT 1))"),
                {"id": str(uuid.uuid4()), "rid": sc["report_id"], "pid": sc["project_id"], "aid": sc["activity_id"]}
            )
            db.commit()
        db.rollback()
        assert "ck_contractor_progress_unit_required" in str(exc_info.value)
    finally:
        db.close()


def test_41_invalid_actual_date_ordering_rejected(setup_monitoring, setup_variance_scenario):
    sc = setup_variance_scenario
    db = TestingSessionLocal()
    try:
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("INSERT INTO daily_activity_progress (id, daily_report_id, project_id, activity_id, contractor_actual_start, contractor_actual_finish, created_by) "
                     "VALUES (:id, :rid, :pid, :aid, '2026-10-10', '2026-10-01', (SELECT id FROM users LIMIT 1))"),
                {"id": str(uuid.uuid4()), "rid": sc["report_id"], "pid": sc["project_id"], "aid": sc["activity_id"]}
            )
            db.commit()
        db.rollback()
        assert "ck_contractor_actual_dates" in str(exc_info.value)
    finally:
        db.close()


def test_42_invalid_verified_date_ordering_rejected(setup_monitoring, setup_variance_scenario):
    sc = setup_variance_scenario
    db = TestingSessionLocal()
    try:
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("INSERT INTO daily_activity_progress_verifications (id, daily_activity_progress_id, project_id, verification_status, verified_actual_start, verified_actual_finish, verified_by) "
                     "VALUES (:id, (SELECT id FROM daily_activity_progress WHERE project_id = :pid LIMIT 1), :pid, 'VERIFIED', '2026-10-15', '2026-10-05', (SELECT id FROM users LIMIT 1))"),
                {"id": str(uuid.uuid4()), "pid": sc["project_id"]}
            )
            db.commit()
        db.rollback()
        assert "ck_verified_actual_dates" in str(exc_info.value)
    finally:
        db.close()


# ==============================================================================
# GROUP 6: SECURITY (Scenarios 43 - 47)
# ==============================================================================

def test_43_cross_project_baseline_access_rejected(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    project_id = setup_monitoring["project_id"]
    project_id_2 = setup_monitoring["project_id_2"]
    admin_token = setup_monitoring["admin_token"]

    # Create activity & schedule in project 2
    client_fixture.post(
        f"/api/projects/{project_id_2}/activities",
        json={"activity_code": f"P2-{uuid.uuid4().hex[:4]}", "activity_name": "P2 Act", "activity_type": "EXCAVATION", "duration_value": 2.0, "duration_unit": "day"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    sched_p2 = client_fixture.post(f"/api/projects/{project_id_2}/schedules/calculate", headers={"Authorization": f"Bearer {admin_token}"}).json()

    # Attempt to freeze schedule from project 2 inside project 1
    resp = client_fixture.post(
        f"/api/projects/{project_id}/monitoring-baselines",
        json={"schedule_id": sched_p2["id"], "baseline_start_date": "2026-10-01"},
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert resp.status_code == 404


def test_44_cross_project_progress_access_rejected(client_fixture, setup_monitoring, setup_variance_scenario):
    sup_token = setup_monitoring["sup_token"]
    project_id_2 = setup_monitoring["project_id_2"]
    sc = setup_variance_scenario

    # Attempt to access progress variance using wrong project id
    resp = client_fixture.get(
        f"/api/projects/{project_id_2}/progress/{sc['activity_id']}/variance",
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert resp.status_code in (403, 404)


def test_45_cross_project_verification_rejected(client_fixture, setup_monitoring, setup_variance_scenario):
    sup_token = setup_monitoring["sup_token"]
    project_id_2 = setup_monitoring["project_id_2"]
    sc = setup_variance_scenario

    resp = client_fixture.post(
        f"/api/projects/{project_id_2}/progress/fake-prog-id/verify",
        json={"verification_status": "VERIFIED"},
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert resp.status_code in (403, 404)


def test_46_contractor_cannot_perform_supervisor_verification(client_fixture, setup_monitoring, setup_variance_scenario):
    con_token = setup_monitoring["con_token"]
    sc = setup_variance_scenario

    p = client_fixture.post(
        f"/api/projects/{sc['project_id']}/daily-progress-reports/{sc['report_id']}/activities",
        json={"activity_id": sc["activity_id"], "contractor_progress_value": 5.0, "contractor_progress_unit": "m3"},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()

    # Contractor attempting verification must get 403 Forbidden
    resp = client_fixture.post(
        f"/api/projects/{sc['project_id']}/progress/{p['id']}/verify",
        json={"verification_status": "VERIFIED"},
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert resp.status_code == 403


def test_47_unauthorized_user_rejected(client_fixture, setup_monitoring, setup_variance_scenario):
    out_token = setup_monitoring["out_token"]
    sc = setup_variance_scenario

    # Outsider attempting to list baselines or progress
    resp = client_fixture.get(
        f"/api/projects/{sc['project_id']}/monitoring-baselines",
        headers={"Authorization": f"Bearer {out_token}"},
    )
    assert resp.status_code == 403


# ==============================================================================
# GROUP 7: TRANSACTIONALITY (Scenarios 48 - 50)
# ==============================================================================

def test_48_failed_baseline_mutation_rolls_back(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    project_id = setup_monitoring["project_id"]

    db = TestingSessionLocal()
    initial_audit_count = db.query(AuditLog).filter(AuditLog.action == "FREEZE_MONITORING_BASELINE").count()
    db.close()

    # Non-existent schedule causes failure
    resp = client_fixture.post(
        f"/api/projects/{project_id}/monitoring-baselines",
        json={"schedule_id": str(uuid.uuid4()), "baseline_start_date": "2026-10-01"},
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert resp.status_code == 404

    db = TestingSessionLocal()
    current_audit_count = db.query(AuditLog).filter(AuditLog.action == "FREEZE_MONITORING_BASELINE").count()
    db.close()
    assert current_audit_count == initial_audit_count


def test_49_failed_report_mutation_rolls_back(client_fixture, setup_monitoring):
    con_token = setup_monitoring["con_token"]
    project_id = setup_monitoring["project_id"]

    # Duplicate finalized report causes 400 rejection and rollback
    rep_date = (date.today() - timedelta(days=50)).isoformat()
    rep = client_fixture.post(
        f"/api/projects/{project_id}/daily-progress-reports",
        json={"report_date": rep_date},
        headers={"Authorization": f"Bearer {con_token}"},
    ).json()
    client_fixture.post(f"/api/projects/{project_id}/daily-progress-reports/{rep['id']}/submit", headers={"Authorization": f"Bearer {con_token}"})
    client_fixture.post(f"/api/projects/{project_id}/daily-progress-reports/{rep['id']}/finalize", headers={"Authorization": f"Bearer {setup_monitoring['sup_token']}"})

    # Try creating another report on the same date
    resp = client_fixture.post(
        f"/api/projects/{project_id}/daily-progress-reports",
        json={"report_date": rep_date},
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert resp.status_code == 400


def test_50_failed_verification_mutation_rolls_back(client_fixture, setup_monitoring, setup_variance_scenario):
    sup_token = setup_monitoring["sup_token"]
    sc = setup_variance_scenario

    db = TestingSessionLocal()
    initial_audit_count = db.query(AuditLog).filter(AuditLog.action == "VERIFY_ACTIVITY_PROGRESS").count()
    db.close()

    # Non-existent progress item verification failure
    resp = client_fixture.post(
        f"/api/projects/{sc['project_id']}/progress/{str(uuid.uuid4())}/verify",
        json={"verification_status": "VERIFIED"},
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert resp.status_code == 404

    db = TestingSessionLocal()
    current_audit_count = db.query(AuditLog).filter(AuditLog.action == "VERIFY_ACTIVITY_PROGRESS").count()
    db.close()
    assert current_audit_count == initial_audit_count


# ==============================================================================
# GROUP 8: DIRECT DATABASE-LEVEL LIFECYCLE & DEFENSIVE BACKFILL (Scenarios 51 - 56)
# ==============================================================================

def test_51_active_to_rejected_sql_rejected(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    project_id = setup_monitoring["project_id"]

    sched = client_fixture.post(f"/api/projects/{project_id}/schedules/calculate", headers={"Authorization": f"Bearer {sup_token}"}).json()
    b = client_fixture.post(
        f"/api/projects/{project_id}/monitoring-baselines",
        json={"schedule_id": sched["id"], "baseline_start_date": "2026-10-01"},
        headers={"Authorization": f"Bearer {sup_token}"},
    ).json()

    db = TestingSessionLocal()
    try:
        with pytest.raises(Exception) as exc_info:
            db.execute(text("UPDATE monitoring_baselines SET status = 'REJECTED' WHERE id = :bid"), {"bid": b["id"]})
            db.commit()
        db.rollback()
        assert "Active monitoring baselines may only transition to SUPERSEDED" in str(exc_info.value)
        status = db.execute(text("SELECT status FROM monitoring_baselines WHERE id = :bid"), {"bid": b["id"]}).scalar()
        assert status == "ACTIVE"

        # Verify direct SQL ACTIVE -> SUPERSEDED is allowed
        db.execute(text("UPDATE monitoring_baselines SET status = 'SUPERSEDED' WHERE id = :bid"), {"bid": b["id"]})
        db.commit()
        status_superseded = db.execute(text("SELECT status FROM monitoring_baselines WHERE id = :bid"), {"bid": b["id"]}).scalar()
        assert status_superseded == "SUPERSEDED"
    finally:
        db.close()


def test_52_superseded_is_terminal(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    project_id = setup_monitoring["project_id"]

    sched = client_fixture.post(f"/api/projects/{project_id}/schedules/calculate", headers={"Authorization": f"Bearer {sup_token}"}).json()
    b1 = client_fixture.post(
        f"/api/projects/{project_id}/monitoring-baselines",
        json={"schedule_id": sched["id"], "baseline_start_date": "2026-10-01"},
        headers={"Authorization": f"Bearer {sup_token}"},
    ).json()

    # Freezing another baseline supersedes b1
    client_fixture.post(
        f"/api/projects/{project_id}/monitoring-baselines",
        json={"schedule_id": sched["id"], "baseline_start_date": "2026-10-05"},
        headers={"Authorization": f"Bearer {sup_token}"},
    )

    db = TestingSessionLocal()
    try:
        # SUPERSEDED -> ACTIVE must fail
        with pytest.raises(Exception) as exc_info:
            db.execute(text("UPDATE monitoring_baselines SET status = 'ACTIVE' WHERE id = :bid"), {"bid": b1["id"]})
            db.commit()
        db.rollback()
        assert "Superseded monitoring baselines cannot change status" in str(exc_info.value)
        status = db.execute(text("SELECT status FROM monitoring_baselines WHERE id = :bid"), {"bid": b1["id"]}).scalar()
        assert status == "SUPERSEDED"

        # SUPERSEDED -> REJECTED must fail
        with pytest.raises(Exception) as exc_info:
            db.execute(text("UPDATE monitoring_baselines SET status = 'REJECTED' WHERE id = :bid"), {"bid": b1["id"]})
            db.commit()
        db.rollback()
        assert "Superseded monitoring baselines cannot change status" in str(exc_info.value)
        status = db.execute(text("SELECT status FROM monitoring_baselines WHERE id = :bid"), {"bid": b1["id"]}).scalar()
        assert status == "SUPERSEDED"
    finally:
        db.close()


def test_53_rejected_is_terminal(client_fixture, setup_monitoring):
    project_id = setup_monitoring["project_id"]
    sup_token = setup_monitoring["sup_token"]

    sched = client_fixture.post(f"/api/projects/{project_id}/schedules/calculate", headers={"Authorization": f"Bearer {sup_token}"}).json()

    db = TestingSessionLocal()
    rej_id = str(uuid.uuid4())
    sup_user = db.query(User).filter(User.role == "supervisor").first()
    try:
        db.execute(
            text("INSERT INTO monitoring_baselines (id, project_id, schedule_id, schedule_version, schedule_algorithm_version, baseline_start_date, frozen_by, status) "
                 "VALUES (:id, :pid, :sid, 'V_REJ', 'CPM_1.0', '2026-10-01', :uid, 'REJECTED')"),
            {"id": rej_id, "pid": project_id, "sid": sched["id"], "uid": sup_user.id}
        )
        db.commit()

        # REJECTED -> ACTIVE must fail
        with pytest.raises(Exception) as exc_info:
            db.execute(text("UPDATE monitoring_baselines SET status = 'ACTIVE' WHERE id = :bid"), {"bid": rej_id})
            db.commit()
        db.rollback()
        assert "Rejected monitoring baselines cannot change status" in str(exc_info.value)
        status = db.execute(text("SELECT status FROM monitoring_baselines WHERE id = :bid"), {"bid": rej_id}).scalar()
        assert status == "REJECTED"

        # REJECTED -> SUPERSEDED must fail
        with pytest.raises(Exception) as exc_info:
            db.execute(text("UPDATE monitoring_baselines SET status = 'SUPERSEDED' WHERE id = :bid"), {"bid": rej_id})
            db.commit()
        db.rollback()
        assert "Rejected monitoring baselines cannot change status" in str(exc_info.value)
        status = db.execute(text("SELECT status FROM monitoring_baselines WHERE id = :bid"), {"bid": rej_id}).scalar()
        assert status == "REJECTED"
    finally:
        db.close()


def test_54_historical_attributes_remain_immutable_direct_sql(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    project_id = setup_monitoring["project_id"]

    sched = client_fixture.post(f"/api/projects/{project_id}/schedules/calculate", headers={"Authorization": f"Bearer {sup_token}"}).json()
    b = client_fixture.post(
        f"/api/projects/{project_id}/monitoring-baselines",
        json={"schedule_id": sched["id"], "baseline_start_date": "2026-10-01"},
        headers={"Authorization": f"Bearer {sup_token}"},
    ).json()

    db = TestingSessionLocal()
    try:
        # 1. baseline_start_date
        with pytest.raises(Exception) as exc_info:
            db.execute(text("UPDATE monitoring_baselines SET baseline_start_date = '2026-12-25' WHERE id = :bid"), {"bid": b["id"]})
            db.commit()
        db.rollback()
        assert "historical attributes cannot be modified" in str(exc_info.value)

        # 2. schedule_algorithm_version
        with pytest.raises(Exception) as exc_info:
            db.execute(text("UPDATE monitoring_baselines SET schedule_algorithm_version = 'CPM_CUSTOM' WHERE id = :bid"), {"bid": b["id"]})
            db.commit()
        db.rollback()
        assert "historical attributes cannot be modified" in str(exc_info.value)

        # 3. schedule_id
        with pytest.raises(Exception) as exc_info:
            db.execute(text("UPDATE monitoring_baselines SET schedule_id = :sid WHERE id = :bid"), {"sid": str(uuid.uuid4()), "bid": b["id"]})
            db.commit()
        db.rollback()
        assert "historical attributes cannot be modified" in str(exc_info.value)

        # 4. schedule_version
        with pytest.raises(Exception) as exc_info:
            db.execute(text("UPDATE monitoring_baselines SET schedule_version = 'V_MODIFIED' WHERE id = :bid"), {"bid": b["id"]})
            db.commit()
        db.rollback()
        assert "historical attributes cannot be modified" in str(exc_info.value)

        # 5. project_id
        with pytest.raises(Exception) as exc_info:
            db.execute(text("UPDATE monitoring_baselines SET project_id = :pid WHERE id = :bid"), {"pid": str(uuid.uuid4()), "bid": b["id"]})
            db.commit()
        db.rollback()
        assert "historical attributes cannot be modified" in str(exc_info.value)

        # 6. frozen_by
        with pytest.raises(Exception) as exc_info:
            db.execute(text("UPDATE monitoring_baselines SET frozen_by = :uid WHERE id = :bid"), {"uid": str(uuid.uuid4()), "bid": b["id"]})
            db.commit()
        db.rollback()
        assert "historical attributes cannot be modified" in str(exc_info.value)

        # 7. frozen_at
        with pytest.raises(Exception) as exc_info:
            db.execute(text("UPDATE monitoring_baselines SET frozen_at = NOW() - INTERVAL '5 days' WHERE id = :bid"), {"bid": b["id"]})
            db.commit()
        db.rollback()
        assert "historical attributes cannot be modified" in str(exc_info.value)
    finally:
        db.close()


def test_55_delete_remains_prohibited_direct_sql(client_fixture, setup_monitoring):
    sup_token = setup_monitoring["sup_token"]
    project_id = setup_monitoring["project_id"]

    client_fixture.post(
        f"/api/projects/{project_id}/activities",
        json={"activity_code": f"B55-{uuid.uuid4().hex[:4]}", "activity_name": "Base Act 55", "activity_type": "EXCAVATION", "duration_value": 3.0, "duration_unit": "day"},
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    sched = client_fixture.post(f"/api/projects/{project_id}/schedules/calculate", headers={"Authorization": f"Bearer {sup_token}"}).json()
    b = client_fixture.post(
        f"/api/projects/{project_id}/monitoring-baselines",
        json={"schedule_id": sched["id"], "baseline_start_date": "2026-10-01"},
        headers={"Authorization": f"Bearer {sup_token}"},
    ).json()

    db = TestingSessionLocal()
    try:
        with pytest.raises(Exception) as exc_info:
            db.execute(text("DELETE FROM monitoring_baselines WHERE id = :bid"), {"bid": b["id"]})
            db.commit()
        db.rollback()
        assert "cannot be deleted" in str(exc_info.value)
    finally:
        db.close()


def test_56_defensive_backfill_invalid_legacy_date_leaves_null(client_fixture, setup_monitoring):
    project_id = setup_monitoring["project_id"]
    sup_token = setup_monitoring["sup_token"]

    client_fixture.post(
        f"/api/projects/{project_id}/activities",
        json={"activity_code": f"B56-{uuid.uuid4().hex[:4]}", "activity_name": "Base Act 56", "activity_type": "EXCAVATION", "duration_value": 3.0, "duration_unit": "day"},
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    sched = client_fixture.post(f"/api/projects/{project_id}/schedules/calculate", headers={"Authorization": f"Bearer {sup_token}"}).json()

    db = TestingSessionLocal()
    sup_user = db.query(User).filter(User.role == "supervisor").first()

    id_invalid = str(uuid.uuid4())
    id_feb30 = str(uuid.uuid4())
    id_malformed = str(uuid.uuid4())
    id_missing = str(uuid.uuid4())

    try:
        # 1. Test safe_cast_to_date function behavior directly across all input variants
        db.execute(text("""
            CREATE OR REPLACE FUNCTION safe_cast_to_date_test(val text) RETURNS date AS $$
            BEGIN
                RETURN val::date;
            EXCEPTION
                WHEN OTHERS THEN
                    RETURN NULL;
            END;
            $$ LANGUAGE plpgsql IMMUTABLE;
        """))

        res_valid = db.execute(text("SELECT safe_cast_to_date_test('2026-10-01')")).scalar()
        res_inv = db.execute(text("SELECT safe_cast_to_date_test('2026-99-99')")).scalar()
        res_feb30 = db.execute(text("SELECT safe_cast_to_date_test('2026-02-30')")).scalar()
        res_malformed = db.execute(text("SELECT safe_cast_to_date_test('invalid-date')")).scalar()
        res_null = db.execute(text("SELECT safe_cast_to_date_test(NULL)")).scalar()

        assert str(res_valid) == "2026-10-01"
        assert res_inv is None
        assert res_feb30 is None
        assert res_malformed is None
        assert res_null is None

        # 2. Test backfill UPDATE logic on rows with invalid and missing dates
        cases = [
            (id_invalid, '{"baseline_start_date": "2026-99-99"}'),
            (id_feb30, '{"baseline_start_date": "2026-02-30"}'),
            (id_malformed, '{"baseline_start_date": "invalid-date"}'),
            (id_missing, '{"unrelated": "data"}'),
        ]
        for bid, meta in cases:
            db.execute(
                text("INSERT INTO monitoring_baselines (id, project_id, schedule_id, schedule_version, schedule_algorithm_version, baseline_start_date, frozen_by, status, metadata_json) "
                     "VALUES (:id, :pid, :sid, 'V1', 'CPM_1.0', NULL, :uid, 'SUPERSEDED', CAST(:meta AS json))"),
                {"id": bid, "pid": project_id, "sid": sched["id"], "uid": sup_user.id, "meta": meta}
            )
        db.commit()

        # Run defensive backfill UPDATE query
        db.execute(text("""
            UPDATE monitoring_baselines
            SET baseline_start_date = safe_cast_to_date_test(metadata_json->>'baseline_start_date')
            WHERE baseline_start_date IS NULL
              AND metadata_json IS NOT NULL
              AND safe_cast_to_date_test(metadata_json->>'baseline_start_date') IS NOT NULL;
        """))
        db.execute(text("DROP FUNCTION IF EXISTS safe_cast_to_date_test(text);"))
        db.commit()

        # Verify all invalid and missing dates safely remained NULL without error
        for bid, _ in cases:
            val = db.execute(text("SELECT baseline_start_date FROM monitoring_baselines WHERE id = :bid"), {"bid": bid}).scalar()
            assert val is None

    finally:
        db.close()


def test_57_migration_chain_upgrade_path():
    """Validates full migration path: b2c3d4e5f6a7 -> c3d4e5f6a7b8 -> d4e5f6a7b8c9 with legacy rows."""
    from alembic.config import Config
    from alembic import command
    import json

    alembic_cfg = Config("alembic.ini")

    # Step 1: Downgrade schema to b2c3d4e5f6a7 (where baseline_start_date column does not yet exist)
    command.downgrade(alembic_cfg, "b2c3d4e5f6a7")

    with engine.connect() as conn:
        u_id = str(uuid.uuid4())
        p_id = str(uuid.uuid4())
        s_id = str(uuid.uuid4())

        conn.execute(text("""
            INSERT INTO users (id, email, password_hash, role)
            VALUES (:id, 'migtest57@example.com', 'hash', 'supervisor')
        """), {"id": u_id})

        conn.execute(text("""
            INSERT INTO projects (id, name, created_by)
            VALUES (:id, 'Mig Test Proj 57', :u)
        """), {"id": p_id, "u": u_id})

        conn.execute(text("""
            INSERT INTO construction_schedules (id, project_id, schedule_version, calculation_status, algorithm_version, project_duration, duration_unit, calculated_by, input_snapshot_json)
            VALUES (:id, :p, 1, 'FINALIZED', 'CPM_V1', 10, 'DAYS', :u, CAST('{}' AS json))
        """), {"id": s_id, "p": p_id, "u": u_id})

        id_valid = str(uuid.uuid4())
        id_inv = str(uuid.uuid4())
        id_f30 = str(uuid.uuid4())
        id_mal = str(uuid.uuid4())
        id_mis = str(uuid.uuid4())

        # Insert test legacy rows in b2c3d4e5f6a7 schema
        cases = [
            (id_valid, {"baseline_start_date": "2026-10-01"}),
            (id_inv, {"baseline_start_date": "2026-99-99"}),
            (id_f30, {"baseline_start_date": "2026-02-30"}),
            (id_mal, {"baseline_start_date": "invalid-date"}),
            (id_mis, {"unrelated": "data"}),
        ]
        for bid, meta in cases:
            conn.execute(text("""
                INSERT INTO monitoring_baselines (id, project_id, schedule_id, schedule_version, schedule_algorithm_version, frozen_by, status, metadata_json)
                VALUES (:id, :p, :s, 1, 'CPM_V1', :u, 'SUPERSEDED', CAST(:m AS json))
            """), {"id": bid, "p": p_id, "s": s_id, "u": u_id, "m": json.dumps(meta)})
        conn.commit()

    # Step 2: Upgrade to c3d4e5f6a7b8
    command.upgrade(alembic_cfg, "c3d4e5f6a7b8")

    with engine.connect() as conn:
        assert str(conn.execute(text("SELECT baseline_start_date FROM monitoring_baselines WHERE id = :id"), {"id": id_valid}).scalar()) == "2026-10-01"
        assert conn.execute(text("SELECT baseline_start_date FROM monitoring_baselines WHERE id = :id"), {"id": id_inv}).scalar() is None
        assert conn.execute(text("SELECT baseline_start_date FROM monitoring_baselines WHERE id = :id"), {"id": id_f30}).scalar() is None
        assert conn.execute(text("SELECT baseline_start_date FROM monitoring_baselines WHERE id = :id"), {"id": id_mal}).scalar() is None
        assert conn.execute(text("SELECT baseline_start_date FROM monitoring_baselines WHERE id = :id"), {"id": id_mis}).scalar() is None

    # Step 3: Upgrade to head (d4e5f6a7b8c9)
    command.upgrade(alembic_cfg, "head")

    with engine.connect() as conn:
        assert str(conn.execute(text("SELECT baseline_start_date FROM monitoring_baselines WHERE id = :id"), {"id": id_valid}).scalar()) == "2026-10-01"
        assert conn.execute(text("SELECT baseline_start_date FROM monitoring_baselines WHERE id = :id"), {"id": id_inv}).scalar() is None
        assert conn.execute(text("SELECT baseline_start_date FROM monitoring_baselines WHERE id = :id"), {"id": id_f30}).scalar() is None
        assert conn.execute(text("SELECT baseline_start_date FROM monitoring_baselines WHERE id = :id"), {"id": id_mal}).scalar() is None
        assert conn.execute(text("SELECT baseline_start_date FROM monitoring_baselines WHERE id = :id"), {"id": id_mis}).scalar() is None
