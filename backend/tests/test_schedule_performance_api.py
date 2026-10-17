import hashlib
import json
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token, get_password_hash
from app.db.database import engine, get_db
from app.db.models import (
    ActivityScheduleResult,
    ConstructionActivity,
    ConstructionSchedule,
    DailyActivityProgress,
    DailyActivityProgressVerification,
    DailyProgressReport,
    Document,
    MonitoringBaseline,
    Project,
    ProjectMember,
    SchedulePerformanceSnapshot,
    User,
)
from app.main import app

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
def setup_api_data():
    adm_email = f"adm_1t_api_{uuid.uuid4().hex[:6]}@test.com"
    sup_email = f"sup_1t_api_{uuid.uuid4().hex[:6]}@test.com"
    sup_alias_email = f"sup_alias_1t_{uuid.uuid4().hex[:6]}@test.com"
    pm_email = f"pm_1t_{uuid.uuid4().hex[:6]}@test.com"
    cnt_email = f"cnt_1t_api_{uuid.uuid4().hex[:6]}@test.com"
    unauth_email = f"unauth_1t_api_{uuid.uuid4().hex[:6]}@test.com"

    with TestingSessionLocal() as db:
        adm = User(email=adm_email, password_hash=get_password_hash("pass"), role="admin")
        sup = User(email=sup_email, password_hash=get_password_hash("pass"), role="site_supervisor")
        sup_alias = User(email=sup_alias_email, password_hash=get_password_hash("pass"), role="supervisor")
        pm = User(email=pm_email, password_hash=get_password_hash("pass"), role="project_manager")
        cnt = User(email=cnt_email, password_hash=get_password_hash("pass"), role="contractor")
        unauth = User(email=unauth_email, password_hash=get_password_hash("pass"), role="site_supervisor")
        db.add_all([adm, sup, sup_alias, pm, cnt, unauth])
        db.commit()
        db.refresh(adm)
        db.refresh(sup)
        db.refresh(sup_alias)
        db.refresh(pm)
        db.refresh(cnt)
        db.refresh(unauth)

        # Projects
        p1 = Project(name=f"Proj 1T API 1 {uuid.uuid4().hex[:4]}", created_by=adm.id)
        p2 = Project(name=f"Proj 1T API 2 {uuid.uuid4().hex[:4]}", created_by=adm.id)
        db.add_all([p1, p2])
        db.commit()
        db.refresh(p1)
        db.refresh(p2)

        # Membership: adm, sup, sup_alias, pm, cnt belong to p1. unauth does not belong to p1.
        db.add_all([
            ProjectMember(project_id=p1.id, user_id=adm.id),
            ProjectMember(project_id=p1.id, user_id=sup.id),
            ProjectMember(project_id=p1.id, user_id=sup_alias.id),
            ProjectMember(project_id=p1.id, user_id=pm.id),
            ProjectMember(project_id=p1.id, user_id=cnt.id),
            ProjectMember(project_id=p2.id, user_id=adm.id),
        ])
        db.commit()

        # Activities for p1
        act1 = ConstructionActivity(
            project_id=p1.id,
            activity_code="ACT-API-01",
            activity_name="Foundation Works",
            activity_type="CONSTRUCTION",
            created_by=adm.id,
        )
        act2 = ConstructionActivity(
            project_id=p1.id,
            activity_code="ACT-API-02",
            activity_name="Superstructure",
            activity_type="CONSTRUCTION",
            created_by=adm.id,
        )
        # Activity for p2 (foreign)
        act_p2 = ConstructionActivity(
            project_id=p2.id,
            activity_code="ACT-P2-01",
            activity_name="Project 2 Works",
            activity_type="CONSTRUCTION",
            created_by=adm.id,
        )
        db.add_all([act1, act2, act_p2])
        db.commit()
        db.refresh(act1)
        db.refresh(act2)
        db.refresh(act_p2)

        # Schedule and Activity Results for p1
        sched1 = ConstructionSchedule(
            project_id=p1.id,
            schedule_version="1.0",
            calculation_status="CALCULATED",
            algorithm_version="1.0",
            input_snapshot_json={},
            calculated_by=adm.id,
        )
        db.add(sched1)
        db.commit()
        db.refresh(sched1)

        res1 = ActivityScheduleResult(
            schedule_id=sched1.id,
            activity_id=act1.id,
            es=Decimal("0.000000"),
            ef=Decimal("30.000000"),
            ls=Decimal("5.000000"),
            lf=Decimal("35.000000"),
            total_float=Decimal("5.000000"),
            is_critical=False,
        )
        res2 = ActivityScheduleResult(
            schedule_id=sched1.id,
            activity_id=act2.id,
            es=Decimal("31.000000"),
            ef=Decimal("60.000000"),
            ls=Decimal("31.000000"),
            lf=Decimal("60.000000"),
            total_float=Decimal("0.000000"),
            is_critical=True,
        )
        db.add_all([res1, res2])
        db.commit()

        # Baseline for p1
        baseline1 = MonitoringBaseline(
            project_id=p1.id,
            schedule_id=sched1.id,
            schedule_version="1.0",
            schedule_algorithm_version="1.0",
            baseline_start_date=date(2026, 3, 1),
            frozen_by=adm.id,
            status="ACTIVE",
        )
        db.add(baseline1)
        db.commit()
        db.refresh(baseline1)

        # Document
        doc1 = Document(
            project_id=p1.id,
            original_filename="delay_notice_api.pdf",
            storage_key="docs/delay_notice_api.pdf",
            file_size_bytes=1024,
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            mime_type="application/pdf",
            document_type="DELAY_NOTICE",
            uploaded_by=adm.id,
        )
        db.add(doc1)
        db.commit()
        db.refresh(doc1)

        # Verified Daily Progress on 2026-03-15 for act1
        dpr = DailyProgressReport(
            project_id=p1.id,
            report_date=date(2026, 3, 15),
            submitted_by=sup.id,
            submission_status="SUBMITTED",
        )
        db.add(dpr)
        db.commit()
        db.refresh(dpr)

        dap = DailyActivityProgress(
            daily_report_id=dpr.id,
            project_id=p1.id,
            activity_id=act1.id,
            contractor_percent_complete=Decimal("50.00"),
            contractor_status="IN_PROGRESS",
            created_by=sup.id,
        )
        db.add(dap)
        db.commit()
        db.refresh(dap)

        dapv = DailyActivityProgressVerification(
            project_id=p1.id,
            daily_activity_progress_id=dap.id,
            verification_status="VERIFIED",
            verified_percent_complete=Decimal("50.0000"),
            verified_actual_start=date(2026, 3, 1),
            verified_by=sup.id,
        )
        db.add(dapv)
        db.commit()

        # Capture IDs
        p1_id = p1.id
        p2_id = p2.id
        act1_id = act1.id
        act2_id = act2.id
        act_p2_id = act_p2.id
        sched1_id = sched1.id
        baseline1_id = baseline1.id
        doc1_id = doc1.id

    adm_token = create_access_token(data={"sub": adm_email})
    sup_token = create_access_token(data={"sub": sup_email})
    sup_alias_token = create_access_token(data={"sub": sup_alias_email})
    pm_token = create_access_token(data={"sub": pm_email})
    cnt_token = create_access_token(data={"sub": cnt_email})
    unauth_token = create_access_token(data={"sub": unauth_email})

    return {
        "adm_token": adm_token,
        "sup_token": sup_token,
        "sup_alias_token": sup_alias_token,
        "pm_token": pm_token,
        "cnt_token": cnt_token,
        "unauth_token": unauth_token,
        "p1_id": p1_id,
        "p2_id": p2_id,
        "act1_id": act1_id,
        "act2_id": act2_id,
        "act_p2_id": act_p2_id,
        "sched1_id": sched1_id,
        "baseline1_id": baseline1_id,
        "doc1_id": doc1_id,
    }


def test_unauthenticated_requests(client_fixture, setup_api_data):
    p1_id = setup_api_data["p1_id"]
    # POST
    resp = client_fixture.post(f"/api/projects/{p1_id}/schedule-performance", json={})
    assert resp.status_code == 401
    # GET list
    resp = client_fixture.get(f"/api/projects/{p1_id}/schedule-performance")
    assert resp.status_code == 401
    # GET summary
    resp = client_fixture.get(f"/api/projects/{p1_id}/schedule-performance/summary")
    assert resp.status_code == 401
    # GET single
    resp = client_fixture.get(f"/api/projects/{p1_id}/schedule-performance/{uuid.uuid4()}")
    assert resp.status_code == 401


def test_project_membership_and_role_authorization(client_fixture, setup_api_data):
    p1_id = setup_api_data["p1_id"]
    act1_id = setup_api_data["act1_id"]
    sched1_id = setup_api_data["sched1_id"]
    payload = {
        "activity_id": act1_id,
        "schedule_id": sched1_id,
        "evaluation_date": "2026-03-15",
    }

    # 1. Non-member user -> 403 Forbidden on create, list, summary
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/schedule-performance",
        json=payload,
        headers={"Authorization": f"Bearer {setup_api_data['unauth_token']}"},
    )
    assert resp.status_code == 403

    resp = client_fixture.get(
        f"/api/projects/{p1_id}/schedule-performance",
        headers={"Authorization": f"Bearer {setup_api_data['unauth_token']}"},
    )
    assert resp.status_code == 403

    resp = client_fixture.get(
        f"/api/projects/{p1_id}/schedule-performance/summary",
        headers={"Authorization": f"Bearer {setup_api_data['unauth_token']}"},
    )
    assert resp.status_code == 403

    # 2. Contractor role is permitted read-only (list, summary) but forbidden from mutation (create)
    resp = client_fixture.get(
        f"/api/projects/{p1_id}/schedule-performance",
        headers={"Authorization": f"Bearer {setup_api_data['cnt_token']}"},
    )
    assert resp.status_code == 200

    resp = client_fixture.get(
        f"/api/projects/{p1_id}/schedule-performance/summary",
        headers={"Authorization": f"Bearer {setup_api_data['cnt_token']}"},
    )
    assert resp.status_code == 200

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/schedule-performance",
        json=payload,
        headers={"Authorization": f"Bearer {setup_api_data['cnt_token']}"},
    )
    assert resp.status_code == 403

    # 3. Project Manager role is NOT in allowed mutation roles -> 403 Forbidden on create
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/schedule-performance",
        json=payload,
        headers={"Authorization": f"Bearer {setup_api_data['pm_token']}"},
    )
    assert resp.status_code == 403

    # 4. Supervisor alias role ('supervisor') is permitted to create
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/schedule-performance",
        json=payload,
        headers={"Authorization": f"Bearer {setup_api_data['sup_alias_token']}"},
    )
    assert resp.status_code == 201


def test_create_schedule_performance_snapshot_success(client_fixture, setup_api_data):
    p1_id = setup_api_data["p1_id"]
    act1_id = setup_api_data["act1_id"]
    sched1_id = setup_api_data["sched1_id"]
    baseline1_id = setup_api_data["baseline1_id"]
    doc1_id = setup_api_data["doc1_id"]

    payload = {
        "activity_id": act1_id,
        "schedule_id": sched1_id,
        "monitoring_baseline_id": baseline1_id,
        "evaluation_date": "2026-03-15",
        "delay_classification": "NON_EXCUSABLE",
        "delay_root_cause_category": "EQUIPMENT",
        "delay_justification": "Slow excavation equipment deployment",
        "delay_evidence_document_id": doc1_id,
    }

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/schedule-performance",
        json=payload,
        headers={"Authorization": f"Bearer {setup_api_data['sup_token']}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()

    assert data["project_id"] == p1_id
    assert data["activity_id"] == act1_id
    assert data["schedule_id"] == sched1_id
    assert data["monitoring_baseline_id"] == baseline1_id
    assert data["status"] == "DRAFT"
    assert data["algorithm_version"] == "SCHED_PERFORMANCE_1.0_LINEAR"
    assert data["planned_duration_days"] == 30
    assert float(data["actual_time_days"]) == 15.0  # 2026-03-01 to 2026-03-15 inclusive = 15 days
    assert float(data["actual_cumulative_progress_pct"]) == 50.0
    assert float(data["earned_schedule_days"]) == 15.0  # 30 * 50% = 15.0
    assert float(data["schedule_variance_days"]) == 0.0  # 15.0 - 15.0 = 0.0
    assert float(data["schedule_performance_index"]) == 1.0  # 15.0 / 15.0 = 1.0
    assert data["delay_status"] == "ON_SCHEDULE"
    assert data["delay_classification"] == "NON_EXCUSABLE"
    assert data["delay_root_cause_category"] == "EQUIPMENT"
    assert data["delay_evidence_document_id"] == doc1_id
    assert data["canonical_hash"] is not None


def test_create_snapshot_schema_validation_rejects_extra_fields(client_fixture, setup_api_data):
    p1_id = setup_api_data["p1_id"]
    act1_id = setup_api_data["act1_id"]
    sched1_id = setup_api_data["sched1_id"]

    # Extra/forbidden fields like status or earned_schedule_days cannot be injected by client
    payload = {
        "activity_id": act1_id,
        "schedule_id": sched1_id,
        "evaluation_date": "2026-03-15",
        "status": "FINALIZED",
        "earned_schedule_days": 999.0,
    }

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/schedule-performance",
        json=payload,
        headers={"Authorization": f"Bearer {setup_api_data['sup_token']}"},
    )
    assert resp.status_code == 422


def test_create_snapshot_foreign_activity_rejection(client_fixture, setup_api_data):
    p1_id = setup_api_data["p1_id"]
    act_p2_id = setup_api_data["act_p2_id"]
    sched1_id = setup_api_data["sched1_id"]

    # Activity belongs to Project 2, cannot be posted to Project 1
    payload = {
        "activity_id": act_p2_id,
        "schedule_id": sched1_id,
        "evaluation_date": "2026-03-15",
    }

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/schedule-performance",
        json=payload,
        headers={"Authorization": f"Bearer {setup_api_data['sup_token']}"},
    )
    assert resp.status_code == 404
    assert "not found in project" in resp.json()["detail"]


def test_get_and_list_snapshots_endpoints(client_fixture, setup_api_data):
    p1_id = setup_api_data["p1_id"]
    act1_id = setup_api_data["act1_id"]

    # List snapshots for project
    resp = client_fixture.get(
        f"/api/projects/{p1_id}/schedule-performance",
        headers={"Authorization": f"Bearer {setup_api_data['sup_token']}"},
    )
    assert resp.status_code == 200
    snaps = resp.json()
    assert len(snaps) >= 1
    snap_id = snaps[0]["id"]

    # Get single snapshot
    resp = client_fixture.get(
        f"/api/projects/{p1_id}/schedule-performance/{snap_id}",
        headers={"Authorization": f"Bearer {setup_api_data['sup_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == snap_id

    # Cross-project get isolation: querying snap_id with project 2 should 404
    p2_id = setup_api_data["p2_id"]
    resp = client_fixture.get(
        f"/api/projects/{p2_id}/schedule-performance/{snap_id}",
        headers={"Authorization": f"Bearer {setup_api_data['adm_token']}"},
    )
    assert resp.status_code == 404

    # Activity-specific list route
    resp = client_fixture.get(
        f"/api/projects/{p1_id}/activities/{act1_id}/schedule-performance",
        headers={"Authorization": f"Bearer {setup_api_data['sup_token']}"},
    )
    assert resp.status_code == 200
    act_snaps = resp.json()
    assert len(act_snaps) >= 1
    assert all(s["activity_id"] == act1_id for s in act_snaps)

    # Activity from another project requested via activity route -> 404
    act_p2_id = setup_api_data["act_p2_id"]
    resp = client_fixture.get(
        f"/api/projects/{p1_id}/activities/{act_p2_id}/schedule-performance",
        headers={"Authorization": f"Bearer {setup_api_data['sup_token']}"},
    )
    assert resp.status_code == 404


def test_summary_endpoint(client_fixture, setup_api_data):
    p1_id = setup_api_data["p1_id"]

    resp = client_fixture.get(
        f"/api/projects/{p1_id}/schedule-performance/summary?evaluation_date=2026-03-15",
        headers={"Authorization": f"Bearer {setup_api_data['sup_token']}"},
    )
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["project_id"] == p1_id
    assert summary["total_snapshots"] >= 1
    assert "ON_SCHEDULE" in summary["delay_status_distribution"]
    assert summary["mean_schedule_performance_index"] is not None


def test_finalization_and_supersession_workflow(client_fixture, setup_api_data):
    p1_id = setup_api_data["p1_id"]
    act1_id = setup_api_data["act1_id"]
    sched1_id = setup_api_data["sched1_id"]

    # 1. Create a fresh snapshot
    payload = {
        "activity_id": act1_id,
        "schedule_id": sched1_id,
        "evaluation_date": "2026-03-15",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/schedule-performance",
        json=payload,
        headers={"Authorization": f"Bearer {setup_api_data['adm_token']}"},
    )
    assert resp.status_code == 201
    snap = resp.json()
    snap_id = snap["id"]
    assert snap["status"] == "DRAFT"

    # 2. Contractor cannot finalize -> 403
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/schedule-performance/{snap_id}/finalize",
        headers={"Authorization": f"Bearer {setup_api_data['cnt_token']}"},
    )
    assert resp.status_code == 403

    # 3. Admin finalizes -> 200 OK
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/schedule-performance/{snap_id}/finalize",
        headers={"Authorization": f"Bearer {setup_api_data['adm_token']}"},
    )
    assert resp.status_code == 200
    fin_snap = resp.json()
    assert fin_snap["status"] == "FINALIZED"
    assert fin_snap["finalized_at"] is not None
    assert fin_snap["finalized_by"] is not None

    # 4. Finalizing again fails -> 400
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/schedule-performance/{snap_id}/finalize",
        headers={"Authorization": f"Bearer {setup_api_data['adm_token']}"},
    )
    assert resp.status_code == 400

    # 5. Create replacement draft
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/schedule-performance",
        json=payload,
        headers={"Authorization": f"Bearer {setup_api_data['adm_token']}"},
    )
    assert resp.status_code == 201
    rep_snap = resp.json()
    rep_id = rep_snap["id"]

    # Finalize the replacement
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/schedule-performance/{rep_id}/finalize",
        headers={"Authorization": f"Bearer {setup_api_data['adm_token']}"},
    )
    # Note: DB partial unique index enforces only one FINALIZED per activity + evaluation_date!
    # Because snap_id is already FINALIZED on 2026-03-15, finalizing rep_id should be rejected with 409
    assert resp.status_code == 409

    # Now supersede snap_id with rep_id (draft replacement is permitted by supersession service)
    super_payload = {
        "supersession_reason": "Corrected weather delay root cause identification",
        "replacement_snapshot_id": rep_id,
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/schedule-performance/{snap_id}/supersede",
        json=super_payload,
        headers={"Authorization": f"Bearer {setup_api_data['adm_token']}"},
    )
    assert resp.status_code == 200
    sup_snap = resp.json()
    assert sup_snap["status"] == "SUPERSEDED"
    assert sup_snap["superseded_at"] is not None
    assert sup_snap["superseded_by_user_id"] is not None
    assert sup_snap["supersession_reason"] == "Corrected weather delay root cause identification"
    assert sup_snap["superseded_by"] == rep_id

    # Now that snap_id is SUPERSEDED, rep_id can be finalized without unique conflict!
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/schedule-performance/{rep_id}/finalize",
        headers={"Authorization": f"Bearer {setup_api_data['adm_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "FINALIZED"


def test_invalid_query_filter_validation(client_fixture, setup_api_data):
    p1_id = setup_api_data["p1_id"]
    sup_token = setup_api_data["sup_token"]

    # Invalid delay_status
    resp = client_fixture.get(
        f"/api/projects/{p1_id}/schedule-performance?delay_status=NOT_A_VALID_STATUS",
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert resp.status_code == 422
    assert "Invalid delay_status filter" in resp.json()["detail"]

    # Invalid performance_status
    resp = client_fixture.get(
        f"/api/projects/{p1_id}/schedule-performance?performance_status=BOGUS_PERF",
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert resp.status_code == 422
    assert "Invalid performance_status filter" in resp.json()["detail"]

    # Invalid status_filter
    resp = client_fixture.get(
        f"/api/projects/{p1_id}/schedule-performance?status=BOGUS_STATUS",
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert resp.status_code == 422
    assert "Invalid status filter" in resp.json()["detail"]


def test_summary_authoritative_only_and_date_filtering(client_fixture, setup_api_data):
    """Verify summary uses authoritative snapshots and respects evaluation_date."""
    p1_id = setup_api_data["p1_id"]
    sup_token = setup_api_data["sup_token"]

    # Request summary before any snapshots exist (2025-01-01)
    resp = client_fixture.get(
        f"/api/projects/{p1_id}/schedule-performance/summary?evaluation_date=2025-01-01",
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["total_snapshots"] == 0
    assert summary["mean_schedule_performance_index"] is None
    assert summary["total_schedule_variance_days"] is None
    assert summary["critical_path_delayed_activities_count"] == 0
    assert len(summary["snapshots"]) == 0


def test_concurrent_finalization_one_authoritative_invariant(client_fixture, setup_api_data):
    """Verify concurrent finalization requests on the same snapshot or identical identity preserve exactly one authoritative snapshot."""
    import threading
    p1_id = setup_api_data["p1_id"]
    act2_id = setup_api_data["act2_id"]
    sched1_id = setup_api_data["sched1_id"]
    adm_token = setup_api_data["adm_token"]
    sup_token = setup_api_data["sup_token"]

    # Create snapshot for act2
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/schedule-performance",
        json={
            "activity_id": act2_id,
            "schedule_id": sched1_id,
            "performance_period_start": "2026-04-01",
            "performance_period_end": "2026-04-30",
            "evaluation_date": "2026-04-30",
        },
        headers={"Authorization": f"Bearer {adm_token}"},
    )
    assert resp.status_code == 201
    snap_id = resp.json()["id"]

    results = []

    def run_finalize(token):
        c = TestClient(app)
        r = c.post(
            f"/api/projects/{p1_id}/schedule-performance/{snap_id}/finalize",
            headers={"Authorization": f"Bearer {token}"},
        )
        results.append(r.status_code)

    t1 = threading.Thread(target=run_finalize, args=(adm_token,))
    t2 = threading.Thread(target=run_finalize, args=(sup_token,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Exactly one must succeed (200), and the other must be rejected (400 or 409)
    assert 200 in results
    assert len(results) == 2
    assert (400 in results) or (409 in results)


def test_concurrent_finalization_different_drafts_same_identity(client_fixture, setup_api_data):
    """Verify that when two distinct DRAFT snapshots share identical identity (project, activity, period), concurrent finalization across separate sessions allows at most one to become FINALIZED and safely rejects the other with 409."""
    import threading
    p1_id = setup_api_data["p1_id"]
    act1_id = setup_api_data["act1_id"]
    sched1_id = setup_api_data["sched1_id"]
    adm_token = setup_api_data["adm_token"]
    sup_token = setup_api_data["sup_token"]

    # 1. Create Draft 1
    resp1 = client_fixture.post(
        f"/api/projects/{p1_id}/schedule-performance",
        json={
            "activity_id": act1_id,
            "schedule_id": sched1_id,
            "performance_period_start": "2026-05-01",
            "performance_period_end": "2026-05-31",
            "evaluation_date": "2026-05-31",
            "actual_start_date": "2026-05-01",
            "actual_cumulative_progress_pct": "80.0000",
            "override_reason": "Draft 1 inspection",
        },
        headers={"Authorization": f"Bearer {adm_token}"},
    )
    assert resp1.status_code == 201
    draft_1_id = resp1.json()["id"]

    # 2. Create Draft 2 with identical project, activity, and reporting period
    resp2 = client_fixture.post(
        f"/api/projects/{p1_id}/schedule-performance",
        json={
            "activity_id": act1_id,
            "schedule_id": sched1_id,
            "performance_period_start": "2026-05-01",
            "performance_period_end": "2026-05-31",
            "evaluation_date": "2026-05-31",
            "actual_start_date": "2026-05-01",
            "actual_cumulative_progress_pct": "85.0000",
            "override_reason": "Draft 2 inspection",
        },
        headers={"Authorization": f"Bearer {adm_token}"},
    )
    assert resp2.status_code == 201
    draft_2_id = resp2.json()["id"]
    assert draft_1_id != draft_2_id

    # 3. Finalize concurrently using separate client / DB sessions
    results = []

    def finalize_draft(token, snap_id):
        c = TestClient(app)
        r = c.post(
            f"/api/projects/{p1_id}/schedule-performance/{snap_id}/finalize",
            headers={"Authorization": f"Bearer {token}"},
        )
        results.append((snap_id, r.status_code))

    t1 = threading.Thread(target=finalize_draft, args=(adm_token, draft_1_id))
    t2 = threading.Thread(target=finalize_draft, args=(sup_token, draft_2_id))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Exactly one must succeed (200), and the other must be rejected (409 Conflict)
    status_codes = [status for _, status in results]
    assert 200 in status_codes
    assert 409 in status_codes
    assert len(results) == 2

    # Verify database state: exactly one is FINALIZED, the other remains DRAFT
    r1 = client_fixture.get(f"/api/projects/{p1_id}/schedule-performance/{draft_1_id}", headers={"Authorization": f"Bearer {adm_token}"})
    r2 = client_fixture.get(f"/api/projects/{p1_id}/schedule-performance/{draft_2_id}", headers={"Authorization": f"Bearer {adm_token}"})
    statuses = {r1.json()["status"], r2.json()["status"]}
    assert statuses == {"FINALIZED", "DRAFT"}



def test_hash_integrity_independent_recomputation(client_fixture, setup_api_data):
    """Verify that stored canonical_hash in persisted snapshot exactly matches independent recomputation."""
    from app.services.schedule_performance_service import generate_schedule_performance_canonical_hash

    p1_id = setup_api_data["p1_id"]
    adm_token = setup_api_data["adm_token"]

    resp = client_fixture.get(
        f"/api/projects/{p1_id}/schedule-performance",
        headers={"Authorization": f"Bearer {adm_token}"},
    )
    assert resp.status_code == 200
    snaps = resp.json()
    assert len(snaps) >= 1

    for snap in snaps:
        stored_hash = snap["canonical_hash"]
        # Independently reconstruct canonical payload from persisted attributes
        independent_payload = {
            "project_id": snap["project_id"],
            "activity_id": snap["activity_id"],
            "schedule_id": snap["schedule_id"],
            "monitoring_baseline_id": snap["monitoring_baseline_id"],
            "performance_period_start": snap["performance_period_start"],
            "performance_period_end": snap["performance_period_end"],
            "evaluation_date": snap["evaluation_date"],
            "planned_start_date": snap["planned_start_date"],
            "planned_finish_date": snap["planned_finish_date"],
            "planned_duration_days": snap["planned_duration_days"],
            "actual_start_date": snap["actual_start_date"],
            "actual_finish_date": snap["actual_finish_date"],
            "actual_duration_days": snap["actual_duration_days"],
            "planned_cumulative_progress_pct": str(snap["planned_cumulative_progress_pct"]) if snap["planned_cumulative_progress_pct"] is not None else None,
            "actual_cumulative_progress_pct": str(snap["actual_cumulative_progress_pct"]) if snap["actual_cumulative_progress_pct"] is not None else None,
            "actual_time_days": str(snap["actual_time_days"]) if snap["actual_time_days"] is not None else None,
            "earned_schedule_days": str(snap["earned_schedule_days"]) if snap["earned_schedule_days"] is not None else None,
            "schedule_variance_days": str(snap["schedule_variance_days"]) if snap["schedule_variance_days"] is not None else None,
            "schedule_performance_index": str(snap["schedule_performance_index"]) if snap["schedule_performance_index"] is not None else None,
            "baseline_total_float_days": snap["baseline_total_float_days"],
            "residual_total_float_days": snap["residual_total_float_days"],
            "is_critical_path": snap["is_critical_path"],
            "critical_path_impact_days": snap["critical_path_impact_days"],
            "delay_status": snap["delay_status"],
            "supervisor_assessed_delay_status": snap["provenance_metadata"].get("supervisor_assessed_delay_status"),
            "performance_status": snap["performance_status"],
            "delay_classification": snap["delay_classification"],
            "delay_root_cause_category": snap["delay_root_cause_category"],
            "delay_justification": snap["delay_justification"],
            "delay_evidence_document_id": snap["delay_evidence_document_id"],
            "contract_variation_id": snap["contract_variation_id"],
            "progress_provenance": snap["provenance_metadata"].get("progress_provenance"),
            "algorithm_version": snap["algorithm_version"],
        }
        recomputed_hash = generate_schedule_performance_canonical_hash(independent_payload)
        assert stored_hash == recomputed_hash, f"Hash mismatch for snapshot {snap['id']}: stored={stored_hash}, recomputed={recomputed_hash}"

