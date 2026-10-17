import uuid
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
    EngineeringElement,
    Rule,
    RuleBasedEstimation,
    EngineeringCalculation,
    ResourcePlan,
    ConstructionActivity,
    ConstructionActivityRevision,
    ActivityDependency,
    ActivityDependencyRevision,
    ConstructionSchedule,
    ActivityScheduleResult,
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
def setup_scheduling(client_fixture):
    # Setup test users and projects
    db = TestingSessionLocal()
    db.commit()
    db.close()

    admin_email = f"admin_sched_{uuid.uuid4().hex[:6]}@test.com"
    client_fixture.post("/api/auth/register/admin", json={"email": admin_email, "password": "pass", "role": "admin"})
    admin_token = client_fixture.post("/api/auth/login", data={"username": admin_email, "password": "pass"}).json()["access_token"]

    u1_email = f"u1_sched_{uuid.uuid4().hex[:6]}@test.com"
    u2_email = f"u2_sched_{uuid.uuid4().hex[:6]}@test.com"
    client_fixture.post("/api/auth/users", json={"email": u1_email, "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post("/api/auth/users", json={"email": u2_email, "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})

    u1_token = client_fixture.post("/api/auth/login", data={"username": u1_email, "password": "p"}).json()["access_token"]
    u2_token = client_fixture.post("/api/auth/login", data={"username": u2_email, "password": "p"}).json()["access_token"]

    # Create Project 1 owned by u1
    p1_resp = client_fixture.post("/api/projects", json={"name": f"Sched Project 1 {uuid.uuid4().hex[:6]}"}, headers={"Authorization": f"Bearer {u1_token}"})
    p1_id = p1_resp.json()["id"]

    # Create Project 2 owned by u2
    p2_resp = client_fixture.post("/api/projects", json={"name": f"Sched Project 2 {uuid.uuid4().hex[:6]}"}, headers={"Authorization": f"Bearer {u2_token}"})
    p2_id = p2_resp.json()["id"]

    return {
        "admin_token": admin_token,
        "u1_token": u1_token,
        "u2_token": u2_token,
        "p1_id": p1_id,
        "p2_id": p2_id,
    }


# ==============================================================================
# A. UNIT HANDLING TESTS
# ==============================================================================

def test_unit_handling_all_day_and_hour(client_fixture, setup_scheduling):
    """Test activities with 'day' and 'hour' units normalize correctly."""
    u1_token = setup_scheduling["u1_token"]
    p1_id = setup_scheduling["p1_id"]

    # 1. Day duration
    act_day_resp = client_fixture.post(
        f"/api/projects/{p1_id}/activities",
        json={
            "activity_code": f"ACT-DAY-{uuid.uuid4().hex[:6]}",
            "activity_name": "Day Activity",
            "activity_type": "EXCAVATION",
            "duration_value": 2.5,
            "duration_unit": "day",
        },
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert act_day_resp.status_code == 201

    # 2. Hour duration (24 hours = 1 day)
    act_hr_resp = client_fixture.post(
        f"/api/projects/{p1_id}/activities",
        json={
            "activity_code": f"ACT-HR-{uuid.uuid4().hex[:6]}",
            "activity_name": "Hour Activity",
            "activity_type": "CONCRETING",
            "duration_value": 48.0,
            "duration_unit": "hour",
        },
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert act_hr_resp.status_code == 201


def test_unit_handling_mixed_hour_and_day_cpm(client_fixture, setup_scheduling):
    """Test CPM schedule calculation across mixed hour and day activities."""
    u1_token = setup_scheduling["u1_token"]
    
    # Create isolated project
    p_resp = client_fixture.post("/api/projects", json={"name": "Mixed Units Project"}, headers={"Authorization": f"Bearer {u1_token}"})
    p_id = p_resp.json()["id"]

    # Act 1: 24 hours (= 1.0 day)
    a1_resp = client_fixture.post(
        f"/api/projects/{p_id}/activities",
        json={
            "activity_code": "M-ACT-1",
            "activity_name": "Task 1 (Hours)",
            "activity_type": "EXCAVATION",
            "duration_value": 24.0,
            "duration_unit": "hour",
        },
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    a1_id = a1_resp.json()["id"]

    # Act 2: 2 days (= 2.0 days)
    a2_resp = client_fixture.post(
        f"/api/projects/{p_id}/activities",
        json={
            "activity_code": "M-ACT-2",
            "activity_name": "Task 2 (Days)",
            "activity_type": "CONCRETING",
            "duration_value": 2.0,
            "duration_unit": "day",
        },
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    a2_id = a2_resp.json()["id"]

    # Dependency: a1 -> a2 with 12 hour lag (= 0.5 day)
    dep_resp = client_fixture.post(
        f"/api/projects/{p_id}/activities/{a1_id}/dependencies",
        json={
            "successor_activity_id": a2_id,
            "dependency_type": "FINISH_TO_START",
            "lag_value": 12.0,
            "lag_unit": "hour",
        },
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert dep_resp.status_code == 201

    # Calculate schedule
    calc_resp = client_fixture.post(
        f"/api/projects/{p_id}/schedules/calculate",
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert calc_resp.status_code == 201
    sched = calc_resp.json()
    assert sched["duration_unit"] == "day"
    assert sched["canonical_schedule_unit"] == "day"

    # ES(a1) = 0.0, EF(a1) = 1.0
    # ES(a2) = EF(a1) + lag = 1.0 + 0.5 = 1.5
    # EF(a2) = ES(a2) + 2.0 = 3.5
    # Total duration = 3.5 days
    assert Decimal(str(sched["project_duration"])) == Decimal("3.5")


def test_unit_handling_unsupported_and_missing_units(client_fixture, setup_scheduling):
    """Test unsupported units and missing units are rejected with 400 INVALID_INPUT."""
    u1_token = setup_scheduling["u1_token"]
    p1_id = setup_scheduling["p1_id"]

    # 1. Unsupported duration unit
    bad_unit_resp = client_fixture.post(
        f"/api/projects/{p1_id}/activities",
        json={
            "activity_code": f"ACT-BAD-{uuid.uuid4().hex[:6]}",
            "activity_name": "Bad Unit Activity",
            "activity_type": "EXCAVATION",
            "duration_value": 5.0,
            "duration_unit": "month",
        },
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert bad_unit_resp.status_code == 400
    assert "INVALID_INPUT" in bad_unit_resp.json()["detail"]

    # 2. Missing unit when value exists
    missing_unit_resp = client_fixture.post(
        f"/api/projects/{p1_id}/activities",
        json={
            "activity_code": f"ACT-NOUNIT-{uuid.uuid4().hex[:6]}",
            "activity_name": "Missing Unit Activity",
            "activity_type": "EXCAVATION",
            "duration_value": 5.0,
            "duration_unit": "",
        },
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert missing_unit_resp.status_code == 400
    assert "INVALID_INPUT" in missing_unit_resp.json()["detail"]


# ==============================================================================
# B. DURATION VALIDATION (ZERO & NEGATIVE)
# ==============================================================================

def test_zero_and_negative_duration_rejected(client_fixture, setup_scheduling):
    """Test zero and negative durations are rejected with 400 INVALID_INPUT."""
    u1_token = setup_scheduling["u1_token"]
    p1_id = setup_scheduling["p1_id"]

    # Zero duration
    zero_resp = client_fixture.post(
        f"/api/projects/{p1_id}/activities",
        json={
            "activity_code": f"ACT-ZERO-{uuid.uuid4().hex[:6]}",
            "activity_name": "Zero Duration",
            "activity_type": "EXCAVATION",
            "duration_value": 0.0,
            "duration_unit": "day",
        },
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert zero_resp.status_code == 400
    assert "INVALID_INPUT" in zero_resp.json()["detail"]

    # Negative duration
    neg_resp = client_fixture.post(
        f"/api/projects/{p1_id}/activities",
        json={
            "activity_code": f"ACT-NEG-{uuid.uuid4().hex[:6]}",
            "activity_name": "Negative Duration",
            "activity_type": "EXCAVATION",
            "duration_value": -5.0,
            "duration_unit": "day",
        },
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert neg_resp.status_code == 400
    assert "INVALID_INPUT" in neg_resp.json()["detail"]


def test_negative_lag_rejected(client_fixture, setup_scheduling):
    """Test negative dependency lag is rejected with 400 INVALID_INPUT."""
    u1_token = setup_scheduling["u1_token"]
    p1_id = setup_scheduling["p1_id"]

    a1 = client_fixture.post(
        f"/api/projects/{p1_id}/activities",
        json={"activity_code": f"A1-LAG-{uuid.uuid4().hex[:6]}", "activity_name": "A1", "activity_type": "EXCAVATION", "duration_value": 1.0, "duration_unit": "day"},
        headers={"Authorization": f"Bearer {u1_token}"},
    ).json()["id"]

    a2 = client_fixture.post(
        f"/api/projects/{p1_id}/activities",
        json={"activity_code": f"A2-LAG-{uuid.uuid4().hex[:6]}", "activity_name": "A2", "activity_type": "CONCRETING", "duration_value": 1.0, "duration_unit": "day"},
        headers={"Authorization": f"Bearer {u1_token}"},
    ).json()["id"]

    dep_neg = client_fixture.post(
        f"/api/projects/{p1_id}/activities/{a1}/dependencies",
        json={"successor_activity_id": a2, "dependency_type": "FINISH_TO_START", "lag_value": -2.0, "lag_unit": "day"},
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert dep_neg.status_code == 400
    assert "INVALID_INPUT" in dep_neg.json()["detail"]


# ==============================================================================
# C. PROVENANCE VALIDATION
# ==============================================================================

def test_duration_provenance_validation(client_fixture, setup_scheduling):
    """Test duration provenance checks for USER_PROVIDED, RULE_BASED, DETERMINISTIC."""
    u1_token = setup_scheduling["u1_token"]
    p1_id = setup_scheduling["p1_id"]

    # 1. USER_PROVIDED with valid classification
    up_resp = client_fixture.post(
        f"/api/projects/{p1_id}/activities",
        json={
            "activity_code": f"ACT-UP-{uuid.uuid4().hex[:6]}",
            "activity_name": "User Provided",
            "activity_type": "EXCAVATION",
            "duration_value": 3.0,
            "duration_unit": "day",
            "duration_method": "USER_PROVIDED",
            "duration_classification": "USER_PROVIDED",
            "metadata_json": {"source_type": "USER_PROVIDED"},
        },
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert up_resp.status_code == 201

    # 2. RULE_BASED without valid source_id -> 400 INVALID_INPUT
    rb_invalid_resp = client_fixture.post(
        f"/api/projects/{p1_id}/activities",
        json={
            "activity_code": f"ACT-RB-BAD-{uuid.uuid4().hex[:6]}",
            "activity_name": "Invalid Rule Based",
            "activity_type": "CONCRETING",
            "duration_value": 4.0,
            "duration_unit": "day",
            "duration_method": "RULE_BASED",
            "duration_classification": "CALCULATED",
            "metadata_json": {"source_type": "RULE_BASED", "source_id": "non-existent-rule-id"},
        },
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert rb_invalid_resp.status_code == 400
    assert "INVALID_INPUT" in rb_invalid_resp.json()["detail"]

    # 3. DETERMINISTIC without valid source_id -> 400 INVALID_INPUT
    det_invalid_resp = client_fixture.post(
        f"/api/projects/{p1_id}/activities",
        json={
            "activity_code": f"ACT-DET-BAD-{uuid.uuid4().hex[:6]}",
            "activity_name": "Invalid Deterministic",
            "activity_type": "CONCRETING",
            "duration_value": 5.0,
            "duration_unit": "day",
            "duration_method": "DETERMINISTIC",
            "duration_classification": "CALCULATED",
            "metadata_json": {"source_type": "DETERMINISTIC", "source_id": "non-existent-calc-id"},
        },
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert det_invalid_resp.status_code == 400
    assert "INVALID_INPUT" in det_invalid_resp.json()["detail"]


def test_duration_provenance_with_valid_rule_source(client_fixture, setup_scheduling):
    """Test valid RULE_BASED duration referencing an active RuleDefinition succeeds."""
    u1_token = setup_scheduling["u1_token"]
    p1_id = setup_scheduling["p1_id"]

    db = TestingSessionLocal()
    admin_user = db.query(User).filter(User.role == "admin").first()
    rule = Rule(
        id=str(uuid.uuid4()),
        rule_code=f"RULE_{uuid.uuid4().hex[:6]}",
        rule_name="Test Duration Rule",
        rule_category="LABOUR_PRODUCTIVITY",
        input_unit="m3",
        output_unit="labour-hour",
        formula_identifier="FORMULA_TEST",
        formula_expression="input * 1.5",
        parameters_json={},
        status="ACTIVE",
        version="1.0",
        created_by=admin_user.id,
    )
    db.add(rule)
    db.commit()
    rule_id = rule.id
    db.close()

    rb_valid_resp = client_fixture.post(
        f"/api/projects/{p1_id}/activities",
        json={
            "activity_code": f"ACT-RB-OK-{uuid.uuid4().hex[:6]}",
            "activity_name": "Valid Rule Based",
            "activity_type": "CONCRETING",
            "duration_value": 6.0,
            "duration_unit": "day",
            "duration_method": "RULE_BASED",
            "duration_classification": "CALCULATED",
            "metadata_json": {"source_type": "RULE_BASED", "source_id": rule_id},
        },
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert rb_valid_resp.status_code == 201


# ==============================================================================
# D. HISTORICAL INTEGRITY & DB TRIGGERS
# ==============================================================================

def test_activity_revision_creation_and_immutability(client_fixture, setup_scheduling):
    """Test activity revision 1 is created and revisions cannot be updated or deleted."""
    u1_token = setup_scheduling["u1_token"]
    p1_id = setup_scheduling["p1_id"]

    act_resp = client_fixture.post(
        f"/api/projects/{p1_id}/activities",
        json={
            "activity_code": f"ACT-REV-{uuid.uuid4().hex[:6]}",
            "activity_name": "Revision Tracked Activity",
            "activity_type": "EXCAVATION",
            "duration_value": 3.0,
            "duration_unit": "day",
        },
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert act_resp.status_code == 201
    act_id = act_resp.json()["id"]

    # Check GET revisions endpoint
    rev_resp = client_fixture.get(
        f"/api/projects/{p1_id}/activities/{act_id}/revisions",
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert rev_resp.status_code == 200
    revs = rev_resp.json()
    assert len(revs) == 1
    assert revs[0]["revision_number"] == 1
    rev_id = revs[0]["id"]

    # Database-level trigger test: UPDATE prohibited
    db = TestingSessionLocal()
    with pytest.raises(Exception) as exc_up:
        db.execute(text("UPDATE construction_activity_revisions SET activity_name = 'Hacked' WHERE id = :id"), {"id": rev_id})
        db.commit()
    db.rollback()
    assert "append-only and immutable" in str(exc_up.value).lower()

    # Database-level trigger test: DELETE prohibited
    with pytest.raises(Exception) as exc_del:
        db.execute(text("DELETE FROM construction_activity_revisions WHERE id = :id"), {"id": rev_id})
        db.commit()
    db.rollback()
    assert "append-only and immutable" in str(exc_del.value).lower()
    db.close()


def test_dependency_revision_creation_and_immutability(client_fixture, setup_scheduling):
    """Test dependency revision 1 is created and revisions cannot be updated or deleted."""
    u1_token = setup_scheduling["u1_token"]
    p1_id = setup_scheduling["p1_id"]

    a1 = client_fixture.post(
        f"/api/projects/{p1_id}/activities",
        json={"activity_code": f"D1-{uuid.uuid4().hex[:6]}", "activity_name": "D1", "activity_type": "EXCAVATION", "duration_value": 2.0, "duration_unit": "day"},
        headers={"Authorization": f"Bearer {u1_token}"},
    ).json()["id"]

    a2 = client_fixture.post(
        f"/api/projects/{p1_id}/activities",
        json={"activity_code": f"D2-{uuid.uuid4().hex[:6]}", "activity_name": "D2", "activity_type": "CONCRETING", "duration_value": 2.0, "duration_unit": "day"},
        headers={"Authorization": f"Bearer {u1_token}"},
    ).json()["id"]

    dep_resp = client_fixture.post(
        f"/api/projects/{p1_id}/activities/{a1}/dependencies",
        json={"successor_activity_id": a2, "dependency_type": "FINISH_TO_START", "lag_value": 1.0, "lag_unit": "day"},
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert dep_resp.status_code == 201
    dep_id = dep_resp.json()["id"]

    # Check GET dependency revisions endpoint
    rev_resp = client_fixture.get(
        f"/api/projects/{p1_id}/dependencies/{dep_id}/revisions",
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert rev_resp.status_code == 200
    revs = rev_resp.json()
    assert len(revs) == 1
    assert revs[0]["revision_number"] == 1
    rev_id = revs[0]["id"]

    # Database-level trigger test: UPDATE prohibited
    db = TestingSessionLocal()
    with pytest.raises(Exception) as exc_up:
        db.execute(text("UPDATE activity_dependency_revisions SET lag_value = 99.0 WHERE id = :id"), {"id": rev_id})
        db.commit()
    db.rollback()
    assert "append-only and immutable" in str(exc_up.value).lower()

    # Database-level trigger test: DELETE prohibited
    with pytest.raises(Exception) as exc_del:
        db.execute(text("DELETE FROM activity_dependency_revisions WHERE id = :id"), {"id": rev_id})
        db.commit()
    db.rollback()
    assert "append-only and immutable" in str(exc_del.value).lower()
    db.close()


def test_database_immutability_triggers_on_schedules_and_results(client_fixture, setup_scheduling):
    """Test PostgreSQL triggers preventing unauthorized modification of schedules and results."""
    u1_token = setup_scheduling["u1_token"]

    p_resp = client_fixture.post("/api/projects", json={"name": "Immutability Project"}, headers={"Authorization": f"Bearer {u1_token}"})
    p_id = p_resp.json()["id"]

    client_fixture.post(
        f"/api/projects/{p_id}/activities",
        json={"activity_code": "IMM-1", "activity_name": "Task 1", "activity_type": "EXCAVATION", "duration_value": 2.0, "duration_unit": "day"},
        headers={"Authorization": f"Bearer {u1_token}"},
    )

    sched_resp = client_fixture.post(
        f"/api/projects/{p_id}/schedules/calculate",
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert sched_resp.status_code == 201
    sched_id = sched_resp.json()["id"]

    db = TestingSessionLocal()
    # 1. DELETE on construction_schedules prohibited
    with pytest.raises(Exception) as exc_del:
        db.execute(text("DELETE FROM construction_schedules WHERE id = :id"), {"id": sched_id})
        db.commit()
    db.rollback()
    assert "immutable" in str(exc_del.value).lower()

    # 2. UPDATE altering duration on construction_schedules prohibited
    with pytest.raises(Exception) as exc_up:
        db.execute(text("UPDATE construction_schedules SET project_duration = 99.0 WHERE id = :id"), {"id": sched_id})
        db.commit()
    db.rollback()
    assert "immutable" in str(exc_up.value).lower()

    # 3. UPDATE on activity_schedule_results prohibited
    res = db.query(ActivityScheduleResult).filter(ActivityScheduleResult.schedule_id == sched_id).first()
    assert res is not None
    with pytest.raises(Exception) as exc_res_up:
        db.execute(text("UPDATE activity_schedule_results SET es = 10.0 WHERE id = :id"), {"id": res.id})
        db.commit()
    db.rollback()
    assert "immutable" in str(exc_res_up.value).lower()

    # 4. DELETE on activity_schedule_results prohibited
    with pytest.raises(Exception) as exc_res_del:
        db.execute(text("DELETE FROM activity_schedule_results WHERE id = :id"), {"id": res.id})
        db.commit()
    db.rollback()
    assert "immutable" in str(exc_res_del.value).lower()
    db.close()


# ==============================================================================
# E. TRANSACTION-SAFE VERSIONING & SNAPSHOTS
# ==============================================================================

def test_schedule_versioning_and_uniqueness_constraint(client_fixture, setup_scheduling):
    """Test transactional version generation (1.0 -> 2.0) and DB unique constraint."""
    u1_token = setup_scheduling["u1_token"]

    p_resp = client_fixture.post("/api/projects", json={"name": "Versioning Project"}, headers={"Authorization": f"Bearer {u1_token}"})
    p_id = p_resp.json()["id"]

    client_fixture.post(
        f"/api/projects/{p_id}/activities",
        json={"activity_code": "V-ACT-1", "activity_name": "Task 1", "activity_type": "EXCAVATION", "duration_value": 4.0, "duration_unit": "day"},
        headers={"Authorization": f"Bearer {u1_token}"},
    )

    # First schedule: version 1.0
    s1_resp = client_fixture.post(f"/api/projects/{p_id}/schedules/calculate", headers={"Authorization": f"Bearer {u1_token}"})
    assert s1_resp.status_code == 201
    s1 = s1_resp.json()
    assert s1["schedule_version"] == "1.0"
    assert s1["calculation_status"] == "CALCULATED"

    # Second schedule: version 2.0; previous becomes SUPERSEDED
    s2_resp = client_fixture.post(f"/api/projects/{p_id}/schedules/calculate", headers={"Authorization": f"Bearer {u1_token}"})
    assert s2_resp.status_code == 201
    s2 = s2_resp.json()
    assert s2["schedule_version"] == "2.0"
    assert s2["calculation_status"] == "CALCULATED"

    # Verify s1 is now SUPERSEDED
    s1_check = client_fixture.get(f"/api/projects/{p_id}/schedules/{s1['id']}", headers={"Authorization": f"Bearer {u1_token}"}).json()
    assert s1_check["calculation_status"] == "SUPERSEDED"

    # Verify UNIQUE(project_id, schedule_version) rejects duplicate
    db = TestingSessionLocal()
    admin_user = db.query(User).filter(User.role == "admin").first()
    dup_sched = ConstructionSchedule(
        id=str(uuid.uuid4()),
        project_id=p_id,
        schedule_version="1.0", # Duplicate!
        calculation_status="SUPERSEDED",
        project_duration=Decimal("4.0"),
        duration_unit="day",
        calculated_by=admin_user.id,
        algorithm_version="CPM_1.0_DETERMINISTIC",
        input_snapshot_json={},
    )
    db.add(dup_sched)
    with pytest.raises(Exception) as exc_dup:
        db.commit()
    db.rollback()
    assert "uq_schedule_project_version" in str(exc_dup.value).lower() or "unique" in str(exc_dup.value).lower()
    db.close()


def test_complete_input_snapshot_preservation(client_fixture, setup_scheduling):
    """Test input snapshot preserves complete activity and dependency attributes."""
    u1_token = setup_scheduling["u1_token"]

    p_resp = client_fixture.post("/api/projects", json={"name": "Snapshot Project"}, headers={"Authorization": f"Bearer {u1_token}"})
    p_id = p_resp.json()["id"]

    a1 = client_fixture.post(
        f"/api/projects/{p_id}/activities",
        json={"activity_code": "SNAP-1", "activity_name": "Task 1", "activity_type": "EXCAVATION", "duration_value": 24.0, "duration_unit": "hour"},
        headers={"Authorization": f"Bearer {u1_token}"},
    ).json()["id"]

    a2 = client_fixture.post(
        f"/api/projects/{p_id}/activities",
        json={"activity_code": "SNAP-2", "activity_name": "Task 2", "activity_type": "CONCRETING", "duration_value": 3.0, "duration_unit": "day"},
        headers={"Authorization": f"Bearer {u1_token}"},
    ).json()["id"]

    client_fixture.post(
        f"/api/projects/{p_id}/activities/{a1}/dependencies",
        json={"successor_activity_id": a2, "dependency_type": "FINISH_TO_START", "lag_value": 12.0, "lag_unit": "hour"},
        headers={"Authorization": f"Bearer {u1_token}"},
    )

    s_resp = client_fixture.post(f"/api/projects/{p_id}/schedules/calculate", headers={"Authorization": f"Bearer {u1_token}"})
    assert s_resp.status_code == 201
    snapshot = s_resp.json()["input_snapshot_json"]

    assert snapshot["algorithm_version"] == "CPM_1.0_DETERMINISTIC"
    assert snapshot["canonical_schedule_unit"] == "day"
    assert len(snapshot["activities"]) == 2
    assert len(snapshot["dependencies"]) == 1

    act_snap = snapshot["activities"][0]
    required_act_keys = {
        "id", "project_id", "activity_code", "activity_name", "description",
        "activity_type", "engineering_element_id", "duration_value", "duration_unit",
        "normalized_duration_value", "normalized_duration_unit", "duration_method",
        "duration_classification", "status", "metadata_json"
    }
    for k in required_act_keys:
        assert k in act_snap, f"Missing key {k} in activity snapshot"

    dep_snap = snapshot["dependencies"][0]
    required_dep_keys = {
        "id", "project_id", "predecessor_activity_id", "successor_activity_id",
        "dependency_type", "lag_value", "lag_unit", "normalized_lag_value",
        "normalized_lag_unit", "metadata_json"
    }
    for k in required_dep_keys:
        assert k in dep_snap, f"Missing key {k} in dependency snapshot"


# ==============================================================================
# F. CPM CALCULATIONS & GRAPH INTEGRITY
# ==============================================================================

def test_cpm_linear_parallel_float_and_critical_path(client_fixture, setup_scheduling):
    """Test CPM math: forward/backward pass, total float, and critical path."""
    u1_token = setup_scheduling["u1_token"]

    p_resp = client_fixture.post("/api/projects", json={"name": "CPM Diamond Project"}, headers={"Authorization": f"Bearer {u1_token}"})
    p_id = p_resp.json()["id"]

    # Graph structure:
    # A (3 days) -> B (4 days) -> D (2 days)   (Path 1: 3 + 4 + 2 = 9 days, CRITICAL)
    # A (3 days) -> C (2 days) -> D (2 days)   (Path 2: 3 + 2 + 2 = 7 days, Float = 2 days)
    a_id = client_fixture.post(f"/api/projects/{p_id}/activities", json={"activity_code": "CPM-A", "activity_name": "A", "activity_type": "EXCAVATION", "duration_value": 3.0, "duration_unit": "day"}, headers={"Authorization": f"Bearer {u1_token}"}).json()["id"]
    b_id = client_fixture.post(f"/api/projects/{p_id}/activities", json={"activity_code": "CPM-B", "activity_name": "B", "activity_type": "FORMWORK", "duration_value": 4.0, "duration_unit": "day"}, headers={"Authorization": f"Bearer {u1_token}"}).json()["id"]
    c_id = client_fixture.post(f"/api/projects/{p_id}/activities", json={"activity_code": "CPM-C", "activity_name": "C", "activity_type": "REINFORCEMENT", "duration_value": 2.0, "duration_unit": "day"}, headers={"Authorization": f"Bearer {u1_token}"}).json()["id"]
    d_id = client_fixture.post(f"/api/projects/{p_id}/activities", json={"activity_code": "CPM-D", "activity_name": "D", "activity_type": "CONCRETING", "duration_value": 2.0, "duration_unit": "day"}, headers={"Authorization": f"Bearer {u1_token}"}).json()["id"]

    client_fixture.post(f"/api/projects/{p_id}/activities/{a_id}/dependencies", json={"successor_activity_id": b_id}, headers={"Authorization": f"Bearer {u1_token}"})
    client_fixture.post(f"/api/projects/{p_id}/activities/{a_id}/dependencies", json={"successor_activity_id": c_id}, headers={"Authorization": f"Bearer {u1_token}"})
    client_fixture.post(f"/api/projects/{p_id}/activities/{b_id}/dependencies", json={"successor_activity_id": d_id}, headers={"Authorization": f"Bearer {u1_token}"})
    client_fixture.post(f"/api/projects/{p_id}/activities/{c_id}/dependencies", json={"successor_activity_id": d_id}, headers={"Authorization": f"Bearer {u1_token}"})

    sched_resp = client_fixture.post(f"/api/projects/{p_id}/schedules/calculate", headers={"Authorization": f"Bearer {u1_token}"})
    assert sched_resp.status_code == 201
    sched = sched_resp.json()
    assert Decimal(str(sched["project_duration"])) == Decimal("9.0")

    results_map = {r["activity_id"]: r for r in sched["results"]}
    
    # A: ES=0, EF=3, LS=0, LF=3, TF=0 (Critical)
    assert Decimal(str(results_map[a_id]["es"])) == Decimal("0.0")
    assert Decimal(str(results_map[a_id]["ef"])) == Decimal("3.0")
    assert Decimal(str(results_map[a_id]["ls"])) == Decimal("0.0")
    assert Decimal(str(results_map[a_id]["lf"])) == Decimal("3.0")
    assert Decimal(str(results_map[a_id]["total_float"])) == Decimal("0.0")
    assert results_map[a_id]["is_critical"] is True

    # B: ES=3, EF=7, LS=3, LF=7, TF=0 (Critical)
    assert Decimal(str(results_map[b_id]["es"])) == Decimal("3.0")
    assert Decimal(str(results_map[b_id]["ef"])) == Decimal("7.0")
    assert Decimal(str(results_map[b_id]["total_float"])) == Decimal("0.0")
    assert results_map[b_id]["is_critical"] is True

    # C: ES=3, EF=5, LS=5, LF=7, TF=2 (Non-critical)
    assert Decimal(str(results_map[c_id]["es"])) == Decimal("3.0")
    assert Decimal(str(results_map[c_id]["ef"])) == Decimal("5.0")
    assert Decimal(str(results_map[c_id]["ls"])) == Decimal("5.0")
    assert Decimal(str(results_map[c_id]["lf"])) == Decimal("7.0")
    assert Decimal(str(results_map[c_id]["total_float"])) == Decimal("2.0")
    assert results_map[c_id]["is_critical"] is False

    # D: ES=7, EF=9, LS=7, LF=9, TF=0 (Critical)
    assert Decimal(str(results_map[d_id]["es"])) == Decimal("7.0")
    assert Decimal(str(results_map[d_id]["ef"])) == Decimal("9.0")
    assert Decimal(str(results_map[d_id]["total_float"])) == Decimal("0.0")
    assert results_map[d_id]["is_critical"] is True

    # Critical path activity order
    assert sched["critical_path"] == [a_id, b_id, d_id]


def test_circular_dependency_rejection(client_fixture, setup_scheduling):
    """Test graph cycle detection rejects circular dependencies with 400 CIRCULAR_DEPENDENCY."""
    u1_token = setup_scheduling["u1_token"]

    p_resp = client_fixture.post("/api/projects", json={"name": "Cycle Project"}, headers={"Authorization": f"Bearer {u1_token}"})
    p_id = p_resp.json()["id"]

    a1 = client_fixture.post(f"/api/projects/{p_id}/activities", json={"activity_code": "CYC-1", "activity_name": "C1", "activity_type": "EXCAVATION", "duration_value": 2.0, "duration_unit": "day"}, headers={"Authorization": f"Bearer {u1_token}"}).json()["id"]
    a2 = client_fixture.post(f"/api/projects/{p_id}/activities", json={"activity_code": "CYC-2", "activity_name": "C2", "activity_type": "CONCRETING", "duration_value": 2.0, "duration_unit": "day"}, headers={"Authorization": f"Bearer {u1_token}"}).json()["id"]

    # a1 -> a2
    client_fixture.post(f"/api/projects/{p_id}/activities/{a1}/dependencies", json={"successor_activity_id": a2}, headers={"Authorization": f"Bearer {u1_token}"})

    # a2 -> a1 (cycle!)
    cycle_resp = client_fixture.post(
        f"/api/projects/{p_id}/activities/{a2}/dependencies",
        json={"successor_activity_id": a1},
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert cycle_resp.status_code == 400
    assert "CIRCULAR_DEPENDENCY" in cycle_resp.json()["detail"]


# ==============================================================================
# G. RESOURCE PLAN SEMANTIC ISOLATION
# ==============================================================================

def test_resource_plan_semantic_isolation(client_fixture, setup_scheduling):
    """Test that ResourcePlan records cannot be automatically converted to activity durations."""
    u1_token = setup_scheduling["u1_token"]
    p1_id = setup_scheduling["p1_id"]

    # Attempt to pass a ResourcePlan source directly as duration
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/activities",
        json={
            "activity_code": f"ACT-RP-ISO-{uuid.uuid4().hex[:6]}",
            "activity_name": "Resource Plan Activity",
            "activity_type": "CONCRETING",
            "duration_value": 10.0,
            "duration_unit": "day",
            "duration_method": "USER_PROVIDED",
            "metadata_json": {"source_type": "RESOURCE_PLAN", "source_id": str(uuid.uuid4())},
        },
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert resp.status_code == 400
    assert "ResourcePlan cannot be directly converted" in resp.json()["detail"]


# ==============================================================================
# H. AUTHORIZATION & CROSS-PROJECT CHECKS
# ==============================================================================

def test_authorization_and_cross_project_rejections(client_fixture, setup_scheduling):
    """Test cross-project rejections and unauthorized schedule access."""
    u1_token = setup_scheduling["u1_token"]
    u2_token = setup_scheduling["u2_token"]
    p1_id = setup_scheduling["p1_id"]
    p2_id = setup_scheduling["p2_id"]

    # 1. User 2 cannot access Project 1 activities
    unauth_resp = client_fixture.get(
        f"/api/projects/{p1_id}/activities",
        headers={"Authorization": f"Bearer {u2_token}"},
    )
    assert unauth_resp.status_code == 403

    # 2. User 2 cannot calculate Project 1 schedule
    unauth_calc = client_fixture.post(
        f"/api/projects/{p1_id}/schedules/calculate",
        headers={"Authorization": f"Bearer {u2_token}"},
    )
    assert unauth_calc.status_code == 403

    # 3. Cross-project dependency rejection
    a1_p1 = client_fixture.post(
        f"/api/projects/{p1_id}/activities",
        json={"activity_code": f"P1-ACT-{uuid.uuid4().hex[:6]}", "activity_name": "P1 Act", "activity_type": "EXCAVATION", "duration_value": 1.0, "duration_unit": "day"},
        headers={"Authorization": f"Bearer {u1_token}"},
    ).json()["id"]

    a2_p2 = client_fixture.post(
        f"/api/projects/{p2_id}/activities",
        json={"activity_code": f"P2-ACT-{uuid.uuid4().hex[:6]}", "activity_name": "P2 Act", "activity_type": "CONCRETING", "duration_value": 1.0, "duration_unit": "day"},
        headers={"Authorization": f"Bearer {u2_token}"},
    ).json()["id"]

    # Attempt to link a1_p1 -> a2_p2 in project 1
    cross_resp = client_fixture.post(
        f"/api/projects/{p1_id}/activities/{a1_p1}/dependencies",
        json={"successor_activity_id": a2_p2},
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert cross_resp.status_code in (400, 404)


def test_unit_handling_decimal_precision(client_fixture, setup_scheduling):
    """Test fractional hour durations maintain exact Decimal precision without binary float drift."""
    u1_token = setup_scheduling["u1_token"]

    p_resp = client_fixture.post("/api/projects", json={"name": "Decimal Precision Project"}, headers={"Authorization": f"Bearer {u1_token}"})
    p_id = p_resp.json()["id"]

    # 8 hours = 8/24 = 1/3 day
    client_fixture.post(
        f"/api/projects/{p_id}/activities",
        json={"activity_code": "DEC-1", "activity_name": "Task 1", "activity_type": "EXCAVATION", "duration_value": 8.0, "duration_unit": "hour"},
        headers={"Authorization": f"Bearer {u1_token}"},
    )

    sched_resp = client_fixture.post(f"/api/projects/{p_id}/schedules/calculate", headers={"Authorization": f"Bearer {u1_token}"})
    assert sched_resp.status_code == 201
    sched = sched_resp.json()
    expected = (Decimal("8") / Decimal("24")).quantize(Decimal("0.000001"))
    actual = Decimal(str(sched["project_duration"])).quantize(Decimal("0.000001"))
    assert actual == expected


def test_duration_provenance_with_valid_deterministic_source(client_fixture, setup_scheduling):
    """Test valid DETERMINISTIC duration referencing an existing EngineeringCalculation succeeds."""
    u1_token = setup_scheduling["u1_token"]
    p1_id = setup_scheduling["p1_id"]

    db = TestingSessionLocal()
    try:
        admin_user = db.query(User).filter(User.role == "admin").first()

        element = EngineeringElement(
            id=str(uuid.uuid4()),
            project_id=p1_id,
            element_name=f"Test Element {uuid.uuid4().hex[:6]}",
            element_type="beam",
            created_by=admin_user.id,
        )
        db.add(element)
        db.commit()

        calc = EngineeringCalculation(
            id=str(uuid.uuid4()),
            project_id=p1_id,
            engineering_element_id=element.id,
            calculation_type="CONCRETE_VOLUME_RECTANGULAR",
            calculation_version="1.0",
            status="CALCULATED",
            result_value=Decimal("12.500000"),
            result_unit="m3",
            formula_identifier="RECTANGULAR_VOLUME",
            formula_expression="length_m * width_m * depth_m",
            inputs_json={"length_m": 5, "width_m": 1, "depth_m": 2.5},
            created_by=admin_user.id,
        )
        db.add(calc)
        db.commit()
        calc_id = calc.id
    finally:
        db.close()

    det_valid_resp = client_fixture.post(
        f"/api/projects/{p1_id}/activities",
        json={
            "activity_code": f"ACT-DET-OK-{uuid.uuid4().hex[:6]}",
            "activity_name": "Valid Deterministic Act",
            "activity_type": "CONCRETING",
            "duration_value": 5.0,
            "duration_unit": "day",
            "duration_method": "DETERMINISTIC",
            "duration_classification": "CALCULATED",
            "metadata_json": {"source_type": "DETERMINISTIC", "source_id": calc_id},
        },
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    assert det_valid_resp.status_code == 201


def test_cpm_single_activity(client_fixture, setup_scheduling):
    """Test CPM schedule with a single activity."""
    u1_token = setup_scheduling["u1_token"]

    p_resp = client_fixture.post("/api/projects", json={"name": "Single Activity Project"}, headers={"Authorization": f"Bearer {u1_token}"})
    p_id = p_resp.json()["id"]

    a_resp = client_fixture.post(
        f"/api/projects/{p_id}/activities",
        json={"activity_code": "SINGLE-1", "activity_name": "Single Task", "activity_type": "EXCAVATION", "duration_value": 5.0, "duration_unit": "day"},
        headers={"Authorization": f"Bearer {u1_token}"},
    )
    a_id = a_resp.json()["id"]

    sched_resp = client_fixture.post(f"/api/projects/{p_id}/schedules/calculate", headers={"Authorization": f"Bearer {u1_token}"})
    assert sched_resp.status_code == 201
    sched = sched_resp.json()
    assert Decimal(str(sched["project_duration"])) == Decimal("5.0")
    assert sched["critical_path"] == [a_id]
    r = sched["results"][0]
    assert Decimal(str(r["es"])) == Decimal("0.0")
    assert Decimal(str(r["ef"])) == Decimal("5.0")
    assert Decimal(str(r["ls"])) == Decimal("0.0")
    assert Decimal(str(r["lf"])) == Decimal("5.0")
    assert Decimal(str(r["total_float"])) == Decimal("0.0")
    assert r["is_critical"] is True


def test_cpm_linear_chain(client_fixture, setup_scheduling):
    """Test CPM schedule with a simple 3-task linear chain."""
    u1_token = setup_scheduling["u1_token"]

    p_resp = client_fixture.post("/api/projects", json={"name": "Linear Chain Project"}, headers={"Authorization": f"Bearer {u1_token}"})
    p_id = p_resp.json()["id"]

    # Chain: A (2 days) -> B (3 days) -> C (4 days) = Total 9 days
    a_id = client_fixture.post(f"/api/projects/{p_id}/activities", json={"activity_code": "LIN-A", "activity_name": "A", "activity_type": "EXCAVATION", "duration_value": 2.0, "duration_unit": "day"}, headers={"Authorization": f"Bearer {u1_token}"}).json()["id"]
    b_id = client_fixture.post(f"/api/projects/{p_id}/activities", json={"activity_code": "LIN-B", "activity_name": "B", "activity_type": "FOUNDATION", "duration_value": 3.0, "duration_unit": "day"}, headers={"Authorization": f"Bearer {u1_token}"}).json()["id"]
    c_id = client_fixture.post(f"/api/projects/{p_id}/activities", json={"activity_code": "LIN-C", "activity_name": "C", "activity_type": "CONCRETING", "duration_value": 4.0, "duration_unit": "day"}, headers={"Authorization": f"Bearer {u1_token}"}).json()["id"]

    client_fixture.post(f"/api/projects/{p_id}/activities/{a_id}/dependencies", json={"successor_activity_id": b_id}, headers={"Authorization": f"Bearer {u1_token}"})
    client_fixture.post(f"/api/projects/{p_id}/activities/{b_id}/dependencies", json={"successor_activity_id": c_id}, headers={"Authorization": f"Bearer {u1_token}"})

    sched_resp = client_fixture.post(f"/api/projects/{p_id}/schedules/calculate", headers={"Authorization": f"Bearer {u1_token}"})
    assert sched_resp.status_code == 201
    sched = sched_resp.json()
    assert Decimal(str(sched["project_duration"])) == Decimal("9.0")
    assert sched["critical_path"] == [a_id, b_id, c_id]


def test_cpm_multiple_terminal_activities(client_fixture, setup_scheduling):
    """Test CPM schedule with multiple terminal nodes ending at different times."""
    u1_token = setup_scheduling["u1_token"]

    p_resp = client_fixture.post("/api/projects", json={"name": "Terminal Nodes Project"}, headers={"Authorization": f"Bearer {u1_token}"})
    p_id = p_resp.json()["id"]

    # Start: S (2 days)
    # Branch 1: S -> T1 (6 days)  [Total = 2 + 6 = 8 days, CRITICAL]
    # Branch 2: S -> T2 (3 days)  [Total = 2 + 3 = 5 days, Float = 8 - 5 = 3 days]
    s_id = client_fixture.post(f"/api/projects/{p_id}/activities", json={"activity_code": "TERM-S", "activity_name": "Start", "activity_type": "EXCAVATION", "duration_value": 2.0, "duration_unit": "day"}, headers={"Authorization": f"Bearer {u1_token}"}).json()["id"]
    t1_id = client_fixture.post(f"/api/projects/{p_id}/activities", json={"activity_code": "TERM-T1", "activity_name": "Terminal 1", "activity_type": "CONCRETING", "duration_value": 6.0, "duration_unit": "day"}, headers={"Authorization": f"Bearer {u1_token}"}).json()["id"]
    t2_id = client_fixture.post(f"/api/projects/{p_id}/activities", json={"activity_code": "TERM-T2", "activity_name": "Terminal 2", "activity_type": "PAINTING", "duration_value": 3.0, "duration_unit": "day"}, headers={"Authorization": f"Bearer {u1_token}"}).json()["id"]

    client_fixture.post(f"/api/projects/{p_id}/activities/{s_id}/dependencies", json={"successor_activity_id": t1_id}, headers={"Authorization": f"Bearer {u1_token}"})
    client_fixture.post(f"/api/projects/{p_id}/activities/{s_id}/dependencies", json={"successor_activity_id": t2_id}, headers={"Authorization": f"Bearer {u1_token}"})

    sched_resp = client_fixture.post(f"/api/projects/{p_id}/schedules/calculate", headers={"Authorization": f"Bearer {u1_token}"})
    assert sched_resp.status_code == 201
    sched = sched_resp.json()
    assert Decimal(str(sched["project_duration"])) == Decimal("8.0")
    assert sched["critical_path"] == [s_id, t1_id]

    r_map = {r["activity_id"]: r for r in sched["results"]}
    # T2 should have LF = 8.0, LS = 5.0, ES = 2.0, EF = 5.0, TF = 3.0
    assert Decimal(str(r_map[t2_id]["total_float"])) == Decimal("3.0")
    assert r_map[t2_id]["is_critical"] is False


def test_cpm_deterministic_topological_tie_breaking(client_fixture, setup_scheduling):
    """Test topological ordering is completely deterministic across multiple runs."""
    u1_token = setup_scheduling["u1_token"]

    p_resp = client_fixture.post("/api/projects", json={"name": "Deterministic Ordering Project"}, headers={"Authorization": f"Bearer {u1_token}"})
    p_id = p_resp.json()["id"]

    # Create 4 independent parallel activities
    codes = ["ORDER-D", "ORDER-B", "ORDER-A", "ORDER-C"]
    for c in codes:
        client_fixture.post(
            f"/api/projects/{p_id}/activities",
            json={"activity_code": c, "activity_name": c, "activity_type": "EXCAVATION", "duration_value": 1.0, "duration_unit": "day"},
            headers={"Authorization": f"Bearer {u1_token}"},
        )

    # First run
    s1 = client_fixture.post(f"/api/projects/{p_id}/schedules/calculate", headers={"Authorization": f"Bearer {u1_token}"}).json()
    # Second run
    s2 = client_fixture.post(f"/api/projects/{p_id}/schedules/calculate", headers={"Authorization": f"Bearer {u1_token}"}).json()

    s1_codes = [r["activity_code"] for r in s1["results"]]
    s2_codes = [r["activity_code"] for r in s2["results"]]
    # Should sort alphabetically: ORDER-A, ORDER-B, ORDER-C, ORDER-D
    assert s1_codes == ["ORDER-A", "ORDER-B", "ORDER-C", "ORDER-D"]
    assert s1_codes == s2_codes

