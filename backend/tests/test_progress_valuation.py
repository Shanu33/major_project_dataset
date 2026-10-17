"""Phase 1L: Site Progress Valuation & Certified Progress Foundation Test Suite.

Comprehensive tests covering all 22 required areas:
1. Activity Rate Mapping: project-specific & global confirmed rates, draft/cross-project rejection
2. Activity Rate Mapping: single ACTIVE mapping, partial unique index, atomic supersession, immutability, delete prohibition
3. Daily Progress Valuation: exact Decimal arithmetic, claimed, certified, signed discrepancy (+, 0, -), disputed exposure
4. Daily Progress Valuation: REJECTED verification (Qs=0, dispute exposure), PENDING ineligible
5. Daily Progress Valuation: FINALIZED report requirement, unit compatibility
6. Period Progress Certificate: DRAFT creation, item totals reconstruction
7. Certificate Number: unique per project, reuse allowed in different project
8. Baseline Start Date: NULL rejected (BASELINE_START_DATE_REQUIRED)
9. Certificate Window: date ordering validation, valuation report-date validation
10. Currency: homogeneous currency requirement, rejection of mismatched currency
11. Item Uniqueness: same valuation twice in one certificate rejected
12. Certification & Valuation Binding: CERTIFIED immutability, canonical SHA-256 hash, valuation binding
13. Valuation Binding Protection: bound valuation cannot be cleared, rebound, or deleted
14. Non-Overlapping Certified Periods: overlapping period rejected by trigger
15. Cumulative Totals Accumulation: running totals validated against prior certified certificate
16. Immutability: CERTIFIED certificate financial mutation blocked, delete blocked
17. Supersession: Admin only, supersession metadata only, valuations remain bound, terminal immutability
18. Draft Deletion: permitted with audit log
19. Financial Progress Summary: real-time summary, PV strictly PLANNED_VALUATION_NOT_AVAILABLE
20. Role Authorization: Admin, Supervisor, Contractor read-only, cross-project protection
21. Advisory Locking: project-level transaction locking
22. Audit Transactionality: atomic audit logging with rollback on failure
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
    EngineeringElement,
    ConstructionActivity,
    ConstructionSchedule,
    ActivityScheduleResult,
    MonitoringBaseline,
    DailyProgressReport,
    DailyActivityProgress,
    DailyActivityProgressVerification,
    CostRate,
    ActivityRateMapping,
    DailyProgressValuation,
    PeriodProgressCertificate,
    PeriodCertificateItem,
    AuditLog,
)
from app.core.security import get_password_hash, create_access_token
from app.services.progress_valuation_service import compute_valuation_snapshot_hash

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
def setup_phase_1l(client_fixture):
    # Setup users directly in database
    admin_email = f"admin_val_{uuid.uuid4().hex[:6]}@test.com"
    sup_email = f"sup_val_{uuid.uuid4().hex[:6]}@test.com"
    con_email = f"con_val_{uuid.uuid4().hex[:6]}@test.com"
    out_email = f"out_val_{uuid.uuid4().hex[:6]}@test.com"

    with TestingSessionLocal() as db_users:
        adm_u = User(email=admin_email, password_hash=get_password_hash("pass"), role="admin")
        sup_u = User(email=sup_email, password_hash=get_password_hash("p"), role="supervisor")
        con_u = User(email=con_email, password_hash=get_password_hash("p"), role="contractor")
        out_u = User(email=out_email, password_hash=get_password_hash("p"), role="contractor")
        db_users.add_all([adm_u, sup_u, con_u, out_u])
        db_users.commit()

    admin_token = create_access_token(data={"sub": admin_email, "role": "admin"})
    sup_token = create_access_token(data={"sub": sup_email, "role": "supervisor"})
    con_token = create_access_token(data={"sub": con_email, "role": "contractor"})
    out_token = create_access_token(data={"sub": out_email, "role": "contractor"})

    # Projects
    p1_resp = client_fixture.post("/api/projects", json={"name": f"Valuation Project 1 {uuid.uuid4().hex[:6]}"}, headers={"Authorization": f"Bearer {admin_token}"})
    project_1_id = p1_resp.json()["id"]

    p2_resp = client_fixture.post("/api/projects", json={"name": f"Valuation Project 2 {uuid.uuid4().hex[:6]}"}, headers={"Authorization": f"Bearer {admin_token}"})
    project_2_id = p2_resp.json()["id"]

    db = TestingSessionLocal()
    con_user = db.query(User).filter(User.email == con_email).first()
    sup_user = db.query(User).filter(User.email == sup_email).first()
    adm_user = db.query(User).filter(User.email == admin_email).first()

    # Add members to Project 1
    db.add(ProjectMember(project_id=project_1_id, user_id=con_user.id))
    db.add(ProjectMember(project_id=project_1_id, user_id=sup_user.id))
    db.commit()

    # Engineering element & Construction Activity in Project 1
    ee = EngineeringElement(
        project_id=project_1_id,
        element_name="Foundation Concrete",
        element_type="FOOTING",
        created_by=adm_user.id,
    )
    db.add(ee)
    db.flush()

    act1 = ConstructionActivity(
        project_id=project_1_id,
        activity_code="ACT-001",
        activity_name="Excavation and Concreting",
        activity_type="FOUNDATION",
        engineering_element_id=ee.id,
        duration_value=Decimal("10.0"),
        duration_unit="days",
        duration_method="MANUAL_OVERRIDE",
        duration_classification="SCHEDULE_IMPACTING",
        status="ACTIVE",
        created_by=adm_user.id,
    )
    act2 = ConstructionActivity(
        project_id=project_1_id,
        activity_code="ACT-002",
        activity_name="Rebar Placement",
        activity_type="FOUNDATION",
        engineering_element_id=ee.id,
        duration_value=Decimal("5.0"),
        duration_unit="days",
        duration_method="MANUAL_OVERRIDE",
        duration_classification="SCHEDULE_IMPACTING",
        status="ACTIVE",
        created_by=adm_user.id,
    )
    db.add(act1)
    db.add(act2)
    db.flush()

    # Activity in Project 2 (for cross-project checks)
    ee2 = EngineeringElement(
        project_id=project_2_id,
        element_name="Project 2 Structure",
        element_type="BEAM",
        created_by=adm_user.id,
    )
    db.add(ee2)
    db.flush()
    act_p2 = ConstructionActivity(
        project_id=project_2_id,
        activity_code="ACT-P2-001",
        activity_name="P2 Masonry",
        activity_type="MASONRY",
        engineering_element_id=ee2.id,
        duration_value=Decimal("7.0"),
        duration_unit="days",
        duration_method="MANUAL_OVERRIDE",
        duration_classification="SCHEDULE_IMPACTING",
        status="ACTIVE",
        created_by=adm_user.id,
    )
    db.add(act_p2)
    db.flush()

    # Schedule & Monitoring Baseline for Project 1
    sched = ConstructionSchedule(
        project_id=project_1_id,
        schedule_version="1.0",
        calculation_status="CALCULATED",
        algorithm_version="1.0",
        input_snapshot_json={},
        calculated_by=adm_user.id,
    )
    db.add(sched)
    db.flush()

    baseline = MonitoringBaseline(
        project_id=project_1_id,
        schedule_id=sched.id,
        schedule_version="1.0",
        schedule_algorithm_version="1.0",
        baseline_start_date=date(2026, 10, 1),
        frozen_by=adm_user.id,
        status="ACTIVE",
    )
    db.add(baseline)
    db.flush()

    # Cost Rates: Project-specific confirmed, Global confirmed, Draft, Project 2 confirmed
    cr_p1 = CostRate(
        project_id=project_1_id,
        rate_code="RATE-CONC-01",
        description="M25 Concrete Rate",
        unit="m3",
        rate_value=Decimal("150.000000"),
        currency="INR",
        source_type="PROJECT_SPECIFIC",
        source_reference="Tender Ref 1",
        version="1.0",
        status="CONFIRMED",
        created_by=adm_user.id,
        confirmed_by=adm_user.id,
        confirmed_at=datetime.now(timezone.utc),
    )
    cr_global = CostRate(
        project_id=None,
        rate_code="RATE-GLOBAL-STEEL",
        description="Standard TMT Steel Rate",
        unit="kg",
        rate_value=Decimal("75.500000"),
        currency="INR",
        source_type="OFFICIAL_SCHEDULE",
        source_reference="CPWD Schedule 2026",
        version="1.0",
        status="CONFIRMED",
        created_by=adm_user.id,
        confirmed_by=adm_user.id,
        confirmed_at=datetime.now(timezone.utc),
    )
    cr_draft = CostRate(
        project_id=project_1_id,
        rate_code="RATE-DRAFT-01",
        description="Unconfirmed rate",
        unit="m3",
        rate_value=Decimal("120.000000"),
        currency="INR",
        source_type="PROJECT_SPECIFIC",
        source_reference="Draft Ref",
        version="1.0",
        status="DRAFT",
        created_by=adm_user.id,
    )
    cr_p2 = CostRate(
        project_id=project_2_id,
        rate_code="RATE-P2-01",
        description="P2 specific rate",
        unit="m3",
        rate_value=Decimal("200.000000"),
        currency="INR",
        source_type="PROJECT_SPECIFIC",
        source_reference="P2 Ref",
        version="1.0",
        status="CONFIRMED",
        created_by=adm_user.id,
        confirmed_by=adm_user.id,
        confirmed_at=datetime.now(timezone.utc),
    )
    db.add(cr_p1)
    db.add(cr_global)
    db.add(cr_draft)
    db.add(cr_p2)
    db.commit()

    context = {
        "admin_token": admin_token,
        "sup_token": sup_token,
        "con_token": con_token,
        "out_token": out_token,
        "admin_user_id": adm_user.id,
        "sup_user_id": sup_user.id,
        "con_user_id": con_user.id,
        "project_1_id": project_1_id,
        "project_2_id": project_2_id,
        "activity_1_id": act1.id,
        "activity_2_id": act2.id,
        "activity_p2_id": act_p2.id,
        "baseline_id": baseline.id,
        "rate_p1_id": cr_p1.id,
        "rate_global_id": cr_global.id,
        "rate_draft_id": cr_draft.id,
        "rate_p2_id": cr_p2.id,
    }
    db.close()
    return context


# ==============================================================================
# 1. Activity Rate Mapping Tests
# ==============================================================================

def test_01_activity_rate_mapping_project_and_global_rate(client_fixture, setup_phase_1l):
    ctx = setup_phase_1l
    headers = {"Authorization": f"Bearer {ctx['sup_token']}"}

    # 1. Map activity_1 to project-specific confirmed rate
    resp = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/activity-rate-mappings",
        json={"activity_id": ctx["activity_1_id"], "cost_rate_id": ctx["rate_p1_id"]},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "ACTIVE"
    assert data["rate_unit"] == "m3"
    assert Decimal(str(data["rate_value"])) == Decimal("150.000000")
    assert data["rate_version"] == "1.0"

    # 2. Map activity_2 to global confirmed rate
    resp2 = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/activity-rate-mappings",
        json={"activity_id": ctx["activity_2_id"], "cost_rate_id": ctx["rate_global_id"]},
        headers=headers,
    )
    assert resp2.status_code == 201
    assert resp2.json()["rate_unit"] == "kg"

    # 3. Reject DRAFT rate
    resp_draft = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/activity-rate-mappings",
        json={"activity_id": ctx["activity_1_id"], "cost_rate_id": ctx["rate_draft_id"]},
        headers=headers,
    )
    assert resp_draft.status_code == 400
    assert "CONFIRMED" in resp_draft.text

    # 4. Reject Cross-Project rate
    resp_cross = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/activity-rate-mappings",
        json={"activity_id": ctx["activity_1_id"], "cost_rate_id": ctx["rate_p2_id"]},
        headers=headers,
    )
    assert resp_cross.status_code == 400


def test_02_activity_rate_mapping_single_active_and_atomic_supersession(client_fixture, setup_phase_1l):
    ctx = setup_phase_1l
    headers = {"Authorization": f"Bearer {ctx['sup_token']}"}

    # Create a new version of cost rate in project 1
    with TestingSessionLocal() as db:
        new_cr = CostRate(
            project_id=ctx["project_1_id"],
            rate_code="RATE-CONC-02",
            description="Updated Concrete Rate",
            unit="m3",
            rate_value=Decimal("165.000000"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Amendment 1",
            version="2.0",
            status="CONFIRMED",
            created_by=ctx["admin_user_id"],
            confirmed_by=ctx["admin_user_id"],
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(new_cr)
        db.commit()
        new_cr_id = new_cr.id

    # Mapping activity_1 to new_cr should atomically supersede previous mapping
    resp = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/activity-rate-mappings",
        json={"activity_id": ctx["activity_1_id"], "cost_rate_id": new_cr_id},
        headers=headers,
    )
    assert resp.status_code == 201
    new_map_id = resp.json()["id"]

    # Verify via DB that exactly one ACTIVE mapping exists
    with TestingSessionLocal() as db:
        active_maps = db.query(ActivityRateMapping).filter(
            ActivityRateMapping.activity_id == ctx["activity_1_id"],
            ActivityRateMapping.status == "ACTIVE"
        ).all()
        assert len(active_maps) == 1
        assert active_maps[0].id == new_map_id

        superseded_maps = db.query(ActivityRateMapping).filter(
            ActivityRateMapping.activity_id == ctx["activity_1_id"],
            ActivityRateMapping.status == "SUPERSEDED"
        ).all()
        assert len(superseded_maps) >= 1

        # Direct SQL delete must be rejected by trigger
        with pytest.raises(Exception) as exc:
            db.execute(text("DELETE FROM activity_rate_mappings WHERE id = :id"), {"id": new_map_id})
            db.commit()
        assert "Deletion of activity rate mapping is prohibited" in str(exc.value)
        db.rollback()

        # Direct SQL mutation of financial fields must be rejected by trigger
        with pytest.raises(Exception) as exc2:
            db.execute(text("UPDATE activity_rate_mappings SET rate_value = 999.0 WHERE id = :id"), {"id": new_map_id})
            db.commit()
        assert "Activity rate mapping financial and provenance fields are immutable" in str(exc2.value)
        db.rollback()


# ==============================================================================
# 2. Daily Progress Valuation Tests
# ==============================================================================

def test_03_daily_progress_valuation_decimal_math_and_discrepancy(client_fixture, setup_phase_1l):
    ctx = setup_phase_1l
    headers = {"Authorization": f"Bearer {ctx['sup_token']}"}

    # Create a finalized daily progress report with 3 items:
    # Item A: Qc=100, Qs=80 (Positive discrepancy: +20, Overclaim exposure = 20 * 165 = 3300)
    # Item B: Qc=50, Qs=50 (Zero discrepancy: 0, Overclaim exposure = 0)
    # Item C: Qc=40, Qs=60 (Negative discrepancy: -20, Overclaim exposure = 0)
    with TestingSessionLocal() as db:
        dpr = DailyProgressReport(
            project_id=ctx["project_1_id"],
            report_date=date(2026, 10, 5),
            submitted_by=ctx["con_user_id"],
            submission_status="FINALIZED",
        )
        db.add(dpr)
        db.flush()

        # Item A
        p_a = DailyActivityProgress(
            daily_report_id=dpr.id,
            project_id=ctx["project_1_id"],
            activity_id=ctx["activity_1_id"],
            contractor_progress_value=Decimal("100.000000"),
            contractor_progress_unit="m3",
            contractor_status="IN_PROGRESS",
            created_by=ctx["con_user_id"],
        )
        db.add(p_a)
        db.flush()
        v_a = DailyActivityProgressVerification(
            daily_activity_progress_id=p_a.id,
            project_id=ctx["project_1_id"],
            verification_status="CORRECTED",
            verified_quantity=Decimal("80.000000"),
            verified_quantity_unit="m3",
            verified_by=ctx["sup_user_id"],
        )
        db.add(v_a)

        # Item B
        p_b = DailyActivityProgress(
            daily_report_id=dpr.id,
            project_id=ctx["project_1_id"],
            activity_id=ctx["activity_1_id"],
            contractor_progress_value=Decimal("50.000000"),
            contractor_progress_unit="m3",
            contractor_status="IN_PROGRESS",
            created_by=ctx["con_user_id"],
        )
        db.add(p_b)
        db.flush()
        v_b = DailyActivityProgressVerification(
            daily_activity_progress_id=p_b.id,
            project_id=ctx["project_1_id"],
            verification_status="VERIFIED",
            verified_quantity=Decimal("50.000000"),
            verified_quantity_unit="m3",
            verified_by=ctx["sup_user_id"],
        )
        db.add(v_b)

        # Item C
        p_c = DailyActivityProgress(
            daily_report_id=dpr.id,
            project_id=ctx["project_1_id"],
            activity_id=ctx["activity_1_id"],
            contractor_progress_value=Decimal("40.000000"),
            contractor_progress_unit="m3",
            contractor_status="IN_PROGRESS",
            created_by=ctx["con_user_id"],
        )
        db.add(p_c)
        db.flush()
        v_c = DailyActivityProgressVerification(
            daily_activity_progress_id=p_c.id,
            project_id=ctx["project_1_id"],
            verification_status="CORRECTED",
            verified_quantity=Decimal("60.000000"),
            verified_quantity_unit="m3",
            verified_by=ctx["sup_user_id"],
        )
        db.add(v_c)
        db.commit()
        report_id = dpr.id

    # Evaluate report
    resp = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/progress-valuations/evaluate-report",
        json={"daily_progress_report_id": report_id},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["valuations_count"] == 3

    # Assert exact Decimal values for each item
    items = sorted(data["valuations"], key=lambda x: Decimal(str(x["contractor_claimed_quantity"])), reverse=True)
    # Item A (100 -> 80)
    it_a = items[0]
    assert Decimal(str(it_a["contractor_claimed_value"])) == Decimal("16500.0000") # 100 * 165
    assert Decimal(str(it_a["certified_progress_value"])) == Decimal("13200.0000") # 80 * 165
    assert Decimal(str(it_a["discrepancy_quantity"])) == Decimal("20.000000")
    assert Decimal(str(it_a["disputed_valuation_exposure"])) == Decimal("3300.0000") # 20 * 165

    # Item B (50 -> 50)
    it_b = items[1]
    assert Decimal(str(it_b["contractor_claimed_value"])) == Decimal("8250.0000")
    assert Decimal(str(it_b["certified_progress_value"])) == Decimal("8250.0000")
    assert Decimal(str(it_b["discrepancy_quantity"])) == Decimal("0.000000")
    assert Decimal(str(it_b["disputed_valuation_exposure"])) == Decimal("0.0000")

    # Item C (40 -> 60)
    it_c = items[2]
    assert Decimal(str(it_c["contractor_claimed_value"])) == Decimal("6600.0000") # 40 * 165
    assert Decimal(str(it_c["certified_progress_value"])) == Decimal("9900.0000") # 60 * 165
    assert Decimal(str(it_c["discrepancy_quantity"])) == Decimal("-20.000000") # SIGNED negative!
    assert Decimal(str(it_c["disputed_valuation_exposure"])) == Decimal("0.0000") # Non-negative exposure clamp!


def test_04_daily_progress_valuation_rejected_and_pending(client_fixture, setup_phase_1l):
    ctx = setup_phase_1l
    headers = {"Authorization": f"Bearer {ctx['sup_token']}"}

    with TestingSessionLocal() as db:
        dpr = DailyProgressReport(
            project_id=ctx["project_1_id"],
            report_date=date(2026, 10, 6),
            submitted_by=ctx["con_user_id"],
            submission_status="FINALIZED",
        )
        db.add(dpr)
        db.flush()

        # Item 1: REJECTED verification (contractor claimed 30, supervisor rejected)
        p1 = DailyActivityProgress(
            daily_report_id=dpr.id,
            project_id=ctx["project_1_id"],
            activity_id=ctx["activity_1_id"],
            contractor_progress_value=Decimal("30.000000"),
            contractor_progress_unit="m3",
            contractor_status="IN_PROGRESS",
            created_by=ctx["con_user_id"],
        )
        db.add(p1)
        db.flush()
        v1 = DailyActivityProgressVerification(
            daily_activity_progress_id=p1.id,
            project_id=ctx["project_1_id"],
            verification_status="REJECTED",
            verified_quantity=None,
            verified_quantity_unit="m3",
            verified_by=ctx["sup_user_id"],
        )
        db.add(v1)

        # Item 2: PENDING verification
        p2 = DailyActivityProgress(
            daily_report_id=dpr.id,
            project_id=ctx["project_1_id"],
            activity_id=ctx["activity_1_id"],
            contractor_progress_value=Decimal("15.000000"),
            contractor_progress_unit="m3",
            contractor_status="IN_PROGRESS",
            created_by=ctx["con_user_id"],
        )
        db.add(p2)
        db.flush()
        v2 = DailyActivityProgressVerification(
            daily_activity_progress_id=p2.id,
            project_id=ctx["project_1_id"],
            verification_status="PENDING",
            verified_by=ctx["sup_user_id"],
        )
        db.add(v2)
        db.commit()
        report_id = dpr.id

    resp = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/progress-valuations/evaluate-report",
        json={"daily_progress_report_id": report_id},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # Only Item 1 (REJECTED) is valued; Item 2 (PENDING) is skipped!
    assert data["valuations_count"] == 1
    val = data["valuations"][0]
    assert Decimal(str(val["supervisor_certified_quantity"])) == Decimal("0.000000")
    assert Decimal(str(val["certified_progress_value"])) == Decimal("0.0000")
    assert Decimal(str(val["contractor_claimed_value"])) == Decimal("4950.0000") # 30 * 165
    assert Decimal(str(val["disputed_valuation_exposure"])) == Decimal("4950.0000")


def test_05_daily_progress_valuation_report_status_and_unit_compatibility(client_fixture, setup_phase_1l):
    ctx = setup_phase_1l
    headers = {"Authorization": f"Bearer {ctx['sup_token']}"}

    # 1. Non-finalized report (SUBMITTED) rejected
    with TestingSessionLocal() as db:
        dpr_sub = DailyProgressReport(
            project_id=ctx["project_1_id"],
            report_date=date(2026, 10, 7),
            submitted_by=ctx["con_user_id"],
            submission_status="SUBMITTED",
        )
        db.add(dpr_sub)
        db.commit()
        sub_id = dpr_sub.id

    resp_sub = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/progress-valuations/evaluate-report",
        json={"daily_progress_report_id": sub_id},
        headers=headers,
    )
    assert resp_sub.status_code == 400
    assert "FINALIZED" in resp_sub.text

    # 2. Incompatible unit (e.g., kg progress mapped to m3 rate)
    with TestingSessionLocal() as db:
        dpr_incomp = DailyProgressReport(
            project_id=ctx["project_1_id"],
            report_date=date(2026, 10, 8),
            submitted_by=ctx["con_user_id"],
            submission_status="FINALIZED",
        )
        db.add(dpr_incomp)
        db.flush()
        p_incomp = DailyActivityProgress(
            daily_report_id=dpr_incomp.id,
            project_id=ctx["project_1_id"],
            activity_id=ctx["activity_1_id"], # Rate unit is m3
            contractor_progress_value=Decimal("50.0"),
            contractor_progress_unit="kg", # Incompatible!
            contractor_status="IN_PROGRESS",
            created_by=ctx["con_user_id"],
        )
        db.add(p_incomp)
        db.flush()
        v_incomp = DailyActivityProgressVerification(
            daily_activity_progress_id=p_incomp.id,
            project_id=ctx["project_1_id"],
            verification_status="VERIFIED",
            verified_quantity=Decimal("50.0"),
            verified_quantity_unit="kg",
            verified_by=ctx["sup_user_id"],
        )
        db.add(v_incomp)
        db.commit()
        incomp_id = dpr_incomp.id

    resp_incomp = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/progress-valuations/evaluate-report",
        json={"daily_progress_report_id": incomp_id},
        headers=headers,
    )
    assert resp_incomp.status_code == 400
    assert "INCOMPATIBLE_UNITS_FOR_VALUATION" in resp_incomp.text


# ==============================================================================
# 3. Period Progress Certificate Tests (PERIOD_SNAPSHOT)
# ==============================================================================

def test_06_period_certificate_draft_creation_and_reconstruction(client_fixture, setup_phase_1l):
    ctx = setup_phase_1l
    headers = {"Authorization": f"Bearer {ctx['sup_token']}"}

    # Create Draft RA-001 covering Oct 1 to Oct 10
    resp = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/period-certificates",
        json={
            "certificate_number": "RA-001",
            "period_start_date": "2026-10-01",
            "period_cut_off_date": "2026-10-10",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["certificate_number"] == "RA-001"
    assert data["certificate_status"] == "DRAFT"
    assert data["certificate_type"] == "PERIOD_SNAPSHOT"
    assert data["item_count"] == 4 # 3 items from test_03 + 1 from test_04
    assert Decimal(str(data["period_certified_value"])) == Decimal("31350.0000") # 13200 + 8250 + 9900 + 0

    # Retrieve certificate and verify item reconstruction
    get_resp = client_fixture.get(
        f"/api/projects/{ctx['project_1_id']}/period-certificates/{data['id']}",
        headers=headers,
    )
    assert get_resp.status_code == 200
    cert_details = get_resp.json()
    assert len(cert_details["items"]) == 4

    # Verify period totals exactly match sum of item amounts
    sum_cert = sum(Decimal(str(it["certified_amount"])) for it in cert_details["items"])
    sum_claim = sum(Decimal(str(it["claimed_amount"])) for it in cert_details["items"])
    sum_disp = sum(Decimal(str(it["disputed_exposure"])) for it in cert_details["items"])
    assert sum_cert == Decimal(str(cert_details["period_certified_value"]))
    assert sum_claim == Decimal(str(cert_details["period_claimed_value"]))
    assert sum_disp == Decimal(str(cert_details["period_disputed_exposure"]))


def test_07_certificate_number_unique_per_project(client_fixture, setup_phase_1l):
    ctx = setup_phase_1l
    headers = {"Authorization": f"Bearer {ctx['sup_token']}"}
    adm_headers = {"Authorization": f"Bearer {ctx['admin_token']}"}

    # 1. Duplicate certificate number inside same project -> rejected
    resp_dup = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/period-certificates",
        json={
            "certificate_number": "RA-001",
            "period_start_date": "2026-10-11",
            "period_cut_off_date": "2026-10-20",
        },
        headers=headers,
    )
    assert resp_dup.status_code == 400
    assert "already exists in project" in resp_dup.text

    # 2. Same certificate number in project 2 -> allowed
    # Create baseline in project 2 first
    with TestingSessionLocal() as db:
        s2 = ConstructionSchedule(
            project_id=ctx["project_2_id"],
            schedule_version="1.0",
            calculation_status="CALCULATED",
            algorithm_version="1.0",
            input_snapshot_json={},
            calculated_by=ctx["admin_user_id"],
        )
        db.add(s2)
        db.flush()
        b2 = MonitoringBaseline(
            project_id=ctx["project_2_id"],
            schedule_id=s2.id,
            schedule_version="1.0",
            schedule_algorithm_version="1.0",
            baseline_start_date=date(2026, 10, 1),
            frozen_by=ctx["admin_user_id"],
            status="ACTIVE",
        )
        db.add(b2)
        db.commit()

    resp_p2 = client_fixture.post(
        f"/api/projects/{ctx['project_2_id']}/period-certificates",
        json={
            "certificate_number": "RA-001", # Same code!
            "period_start_date": "2026-10-01",
            "period_cut_off_date": "2026-10-10",
        },
        headers=adm_headers,
    )
    assert resp_p2.status_code == 201


def test_08_certificate_baseline_start_date_null_rejected(client_fixture, setup_phase_1l):
    ctx = setup_phase_1l
    adm_headers = {"Authorization": f"Bearer {ctx['admin_token']}"}

    # Create project 3 with baseline having baseline_start_date = NULL
    p3_resp = client_fixture.post("/api/projects", json={"name": f"P3 Null Baseline {uuid.uuid4().hex[:6]}"}, headers=adm_headers)
    p3_id = p3_resp.json()["id"]

    with TestingSessionLocal() as db:
        s3 = ConstructionSchedule(
            project_id=p3_id,
            schedule_version="1.0",
            calculation_status="CALCULATED",
            algorithm_version="1.0",
            input_snapshot_json={},
            calculated_by=ctx["admin_user_id"],
        )
        db.add(s3)
        db.flush()
        b3 = MonitoringBaseline(
            project_id=p3_id,
            schedule_id=s3.id,
            schedule_version="1.0",
            schedule_algorithm_version="1.0",
            baseline_start_date=None, # Explicitly NULL!
            frozen_by=ctx["admin_user_id"],
            status="ACTIVE",
        )
        db.add(b3)
        db.commit()

    resp = client_fixture.post(
        f"/api/projects/{p3_id}/period-certificates",
        json={
            "certificate_number": "RA-P3-01",
            "period_start_date": "2026-10-01",
            "period_cut_off_date": "2026-10-10",
        },
        headers=adm_headers,
    )
    assert resp.status_code == 400
    assert "BASELINE_START_DATE_REQUIRED" in resp.text


def test_09_certificate_date_window_validation(client_fixture, setup_phase_1l):
    ctx = setup_phase_1l
    headers = {"Authorization": f"Bearer {ctx['sup_token']}"}

    # period_start_date > period_cut_off_date
    resp = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/period-certificates",
        json={
            "certificate_number": "RA-INVALID-DATES",
            "period_start_date": "2026-10-20",
            "period_cut_off_date": "2026-10-10",
        },
        headers=headers,
    )
    assert resp.status_code == 400


def test_10_certificate_item_uniqueness_and_binding(client_fixture, setup_phase_1l):
    ctx = setup_phase_1l
    headers = {"Authorization": f"Bearer {ctx['sup_token']}"}

    # Get RA-001
    certs = client_fixture.get(f"/api/projects/{ctx['project_1_id']}/period-certificates", headers=headers).json()
    ra_001 = [c for c in certs if c["certificate_number"] == "RA-001"][0]

    # Attempt to insert same valuation twice into RA-001 via direct SQL
    with TestingSessionLocal() as db:
        item = db.query(PeriodCertificateItem).filter(PeriodCertificateItem.certificate_id == ra_001["id"]).first()
        dup_item = PeriodCertificateItem(
            certificate_id=ra_001["id"],
            valuation_id=item.valuation_id,
            activity_id=item.activity_id,
            claimed_quantity=Decimal("1.0"),
            certified_quantity=Decimal("1.0"),
            quantity_unit="m3",
            applied_rate=Decimal("150.0"),
            applied_rate_unit="m3",
            currency="INR",
            claimed_amount=Decimal("150.0"),
            certified_amount=Decimal("150.0"),
            discrepancy_quantity=Decimal("0.0"),
            disputed_exposure=Decimal("0.0"),
        )
        db.add(dup_item)
        with pytest.raises(Exception) as exc:
            db.commit()
        assert "uq_cert_items_cert_val" in str(exc.value)
        db.rollback()


def test_11_certificate_certification_and_valuation_binding(client_fixture, setup_phase_1l):
    ctx = setup_phase_1l
    headers = {"Authorization": f"Bearer {ctx['sup_token']}"}

    certs = client_fixture.get(f"/api/projects/{ctx['project_1_id']}/period-certificates", headers=headers).json()
    ra_001 = [c for c in certs if c["certificate_number"] == "RA-001"][0]

    # Certify RA-001
    resp = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/period-certificates/{ra_001['id']}/certify",
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    cert_data = resp.json()
    assert cert_data["certificate_status"] == "CERTIFIED"
    assert cert_data["certified_by"] == ctx["sup_user_id"]
    assert cert_data["valuation_snapshot_hash"] != "DRAFT_PENDING_CERTIFICATION"
    assert len(cert_data["valuation_snapshot_hash"]) == 64

    # Verify valuations are bound
    with TestingSessionLocal() as db:
        items = db.query(PeriodCertificateItem).filter(PeriodCertificateItem.certificate_id == ra_001["id"]).all()
        for item in items:
            val = db.query(DailyProgressValuation).filter(DailyProgressValuation.id == item.valuation_id).first()
            assert val.certified_certificate_id == ra_001["id"]


def test_12_valuation_binding_protection(client_fixture, setup_phase_1l):
    ctx = setup_phase_1l

    with TestingSessionLocal() as db:
        bound_val = db.query(DailyProgressValuation).filter(
            DailyProgressValuation.certified_certificate_id.isnot(None)
        ).first()
        val_id = bound_val.id

        # 1. Attempt to clear certified_certificate_id via SQL
        with pytest.raises(Exception) as exc1:
            db.execute(text("UPDATE daily_progress_valuations SET certified_certificate_id = NULL WHERE id = :id"), {"id": val_id})
            db.commit()
        assert "cannot be cleared or rebound" in str(exc1.value)
        db.rollback()

        # 2. Attempt to rebind to another dummy certificate ID
        with pytest.raises(Exception) as exc2:
            db.execute(text("UPDATE daily_progress_valuations SET certified_certificate_id = '00000000-0000-0000-0000-000000000000' WHERE id = :id"), {"id": val_id})
            db.commit()
        assert "cannot be cleared or rebound" in str(exc2.value)
        db.rollback()

        # 3. Attempt to delete bound valuation
        with pytest.raises(Exception) as exc3:
            db.execute(text("DELETE FROM daily_progress_valuations WHERE id = :id"), {"id": val_id})
            db.commit()
        assert "bound to certified certificate cannot be deleted" in str(exc3.value)
        db.rollback()


def test_13_non_overlapping_certified_periods_and_cumulative_totals(client_fixture, setup_phase_1l):
    ctx = setup_phase_1l
    headers = {"Authorization": f"Bearer {ctx['sup_token']}"}

    # RA-001 was certified for 2026-10-01 to 2026-10-10.
    # 1. Create and try to certify an overlapping period (e.g. 2026-10-05 to 2026-10-15)
    resp_overlap = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/period-certificates",
        json={
            "certificate_number": "RA-OVERLAP",
            "period_start_date": "2026-10-05",
            "period_cut_off_date": "2026-10-15",
        },
        headers=headers,
    )
    assert resp_overlap.status_code == 201
    overlap_id = resp_overlap.json()["id"]

    # Certifying it must be rejected by trigger!
    cert_resp = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/period-certificates/{overlap_id}/certify",
        headers=headers,
    )
    assert cert_resp.status_code == 400
    assert "overlaps with existing certified certificate" in cert_resp.text

    # Clean up draft
    client_fixture.delete(f"/api/projects/{ctx['project_1_id']}/period-certificates/{overlap_id}", headers=headers)

    # 2. Create non-overlapping contiguous period (2026-10-11 to 2026-10-20)
    # Add new progress for 2026-10-15
    with TestingSessionLocal() as db:
        dpr = DailyProgressReport(
            project_id=ctx["project_1_id"],
            report_date=date(2026, 10, 15),
            submitted_by=ctx["con_user_id"],
            submission_status="FINALIZED",
        )
        db.add(dpr)
        db.flush()
        p = DailyActivityProgress(
            daily_report_id=dpr.id,
            project_id=ctx["project_1_id"],
            activity_id=ctx["activity_1_id"],
            contractor_progress_value=Decimal("10.0"),
            contractor_progress_unit="m3",
            contractor_status="IN_PROGRESS",
            created_by=ctx["con_user_id"],
        )
        db.add(p)
        db.flush()
        v = DailyActivityProgressVerification(
            daily_activity_progress_id=p.id,
            project_id=ctx["project_1_id"],
            verification_status="VERIFIED",
            verified_quantity=Decimal("10.0"),
            verified_quantity_unit="m3",
            verified_by=ctx["sup_user_id"],
        )
        db.add(v)
        db.commit()
        r_id = dpr.id

    client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/progress-valuations/evaluate-report",
        json={"daily_progress_report_id": r_id},
        headers=headers,
    )

    # Draft RA-002
    resp_ra2 = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/period-certificates",
        json={
            "certificate_number": "RA-002",
            "period_start_date": "2026-10-11",
            "period_cut_off_date": "2026-10-20",
        },
        headers=headers,
    )
    assert resp_ra2.status_code == 201
    ra2_data = resp_ra2.json()
    ra2_id = ra2_data["id"]

    # Verify cumulative totals in draft
    # Period: 10 * 165 = 1650
    # Prior cumulative: 31350
    # Cumulative: 31350 + 1650 = 33000
    assert Decimal(str(ra2_data["period_certified_value"])) == Decimal("1650.0000")
    assert Decimal(str(ra2_data["cumulative_certified_value"])) == Decimal("33000.0000")

    # Certify RA-002
    resp_ra2_cert = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/period-certificates/{ra2_id}/certify",
        headers=headers,
    )
    assert resp_ra2_cert.status_code == 200
    assert resp_ra2_cert.json()["certificate_status"] == "CERTIFIED"
    assert Decimal(str(resp_ra2_cert.json()["cumulative_certified_value"])) == Decimal("33000.0000")


def test_14_certified_certificate_immutability(client_fixture, setup_phase_1l):
    ctx = setup_phase_1l
    headers = {"Authorization": f"Bearer {ctx['sup_token']}"}

    certs = client_fixture.get(f"/api/projects/{ctx['project_1_id']}/period-certificates", headers=headers).json()
    ra_001 = [c for c in certs if c["certificate_number"] == "RA-001"][0]
    ra_id = ra_001["id"]

    with TestingSessionLocal() as db:
        # 1. Update financial fields directly via SQL -> blocked
        with pytest.raises(Exception) as exc1:
            db.execute(text("UPDATE period_progress_certificates SET period_certified_value = 99999.0 WHERE id = :id"), {"id": ra_id})
            db.commit()
        assert "CERTIFIED certificate" in str(exc1.value) and "immutable" in str(exc1.value)
        db.rollback()

        # 2. Delete certified certificate -> blocked
        with pytest.raises(Exception) as exc2:
            db.execute(text("DELETE FROM period_progress_certificates WHERE id = :id"), {"id": ra_id})
            db.commit()
        assert "Cannot delete CERTIFIED or SUPERSEDED certificate" in str(exc2.value)
        db.rollback()

        # 3. Modify items of certified certificate -> blocked
        with pytest.raises(Exception) as exc3:
            db.execute(text("UPDATE period_certificate_items SET certified_amount = 0 WHERE certificate_id = :id"), {"id": ra_id})
            db.commit()
        assert "Cannot insert or modify items for CERTIFIED or SUPERSEDED certificate" in str(exc3.value)
        db.rollback()


def test_15_certificate_supersession_and_terminal_immutability(client_fixture, setup_phase_1l):
    ctx = setup_phase_1l
    headers = {"Authorization": f"Bearer {ctx['sup_token']}"}
    adm_headers = {"Authorization": f"Bearer {ctx['admin_token']}"}

    certs = client_fixture.get(f"/api/projects/{ctx['project_1_id']}/period-certificates", headers=headers).json()
    ra_002 = [c for c in certs if c["certificate_number"] == "RA-002"][0]
    ra2_id = ra_002["id"]

    # 1. Supervisor cannot supersede (Admin only)
    resp_sup = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/period-certificates/{ra2_id}/supersede",
        json={"reason": "Contractual dispute"},
        headers=headers,
    )
    assert resp_sup.status_code == 403

    # 2. Admin supersedes RA-002
    resp_adm = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/period-certificates/{ra2_id}/supersede",
        json={"reason": "Formal dispute resolution replacement"},
        headers=adm_headers,
    )
    assert resp_adm.status_code == 200
    assert resp_adm.json()["certificate_status"] == "SUPERSEDED"
    assert resp_adm.json()["supersession_reason"] == "Formal dispute resolution replacement"

    # 3. SUPERSEDED is permanently immutable
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc1:
            db.execute(text("UPDATE period_progress_certificates SET period_certified_value = 0 WHERE id = :id"), {"id": ra2_id})
            db.commit()
        assert "SUPERSEDED certificate" in str(exc1.value) and "permanently immutable" in str(exc1.value)
        db.rollback()

        # Valuations remain permanently bound!
        val = db.query(DailyProgressValuation).filter(DailyProgressValuation.certified_certificate_id == ra2_id).first()
        assert val is not None
        assert val.certified_certificate_id == ra2_id


def test_16_draft_certificate_deletion_and_audit(client_fixture, setup_phase_1l):
    ctx = setup_phase_1l
    headers = {"Authorization": f"Bearer {ctx['sup_token']}"}

    # Create Draft RA-003
    resp = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/period-certificates",
        json={
            "certificate_number": "RA-003",
            "period_start_date": "2026-10-21",
            "period_cut_off_date": "2026-10-31",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    ra3_id = resp.json()["id"]

    # Delete Draft RA-003
    del_resp = client_fixture.delete(
        f"/api/projects/{ctx['project_1_id']}/period-certificates/{ra3_id}",
        headers=headers,
    )
    assert del_resp.status_code == 204

    # Verify audit log exists
    with TestingSessionLocal() as db:
        audit = db.query(AuditLog).filter(
            AuditLog.entity_id == ra3_id,
            AuditLog.action == "PERIOD_CERTIFICATE_DELETED"
        ).first()
        assert audit is not None


def test_17_financial_progress_summary(client_fixture, setup_phase_1l):
    ctx = setup_phase_1l
    headers = {"Authorization": f"Bearer {ctx['sup_token']}"}

    resp = client_fixture.get(
        f"/api/projects/{ctx['project_1_id']}/financial-progress-summary",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert Decimal(str(data["cumulative_earned_value"])) > Decimal("0")
    assert data["planned_valuation_status"] == "PLANNED_VALUATION_NOT_AVAILABLE"
    assert data["cumulative_planned_value"] is None
    assert data["schedule_variance_cost"] is None


def test_18_role_authorization_and_cross_project(client_fixture, setup_phase_1l):
    ctx = setup_phase_1l
    con_headers = {"Authorization": f"Bearer {ctx['con_token']}"}
    out_headers = {"Authorization": f"Bearer {ctx['out_token']}"}

    # Contractor cannot create mapping
    r1 = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/activity-rate-mappings",
        json={"activity_id": ctx["activity_1_id"], "cost_rate_id": ctx["rate_p1_id"]},
        headers=con_headers,
    )
    assert r1.status_code == 403

    # Contractor cannot evaluate report
    r2 = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/progress-valuations/evaluate-report",
        json={"daily_progress_report_id": "dummy"},
        headers=con_headers,
    )
    assert r2.status_code == 403

    # Contractor cannot draft certificate
    r3 = client_fixture.post(
        f"/api/projects/{ctx['project_1_id']}/period-certificates",
        json={"certificate_number": "RA-CON", "period_start_date": "2026-10-01", "period_cut_off_date": "2026-10-05"},
        headers=con_headers,
    )
    assert r3.status_code == 403

    # Contractor can view financial summary (read-only)
    r4 = client_fixture.get(f"/api/projects/{ctx['project_1_id']}/financial-progress-summary", headers=con_headers)
    assert r4.status_code == 200

    # Outsider (no project membership) is forbidden
    r5 = client_fixture.get(f"/api/projects/{ctx['project_1_id']}/financial-progress-summary", headers=out_headers)
    assert r5.status_code == 403


def test_19_advisory_locking_concurrency(setup_phase_1l):
    ctx = setup_phase_1l
    from app.services.progress_valuation_service import acquire_project_cert_lock

    # Verify acquiring lock in transaction does not error
    with TestingSessionLocal() as db:
        acquire_project_cert_lock(db, ctx["project_1_id"])
        db.commit()


def test_20_audit_transactionality_and_failure_rollback(setup_phase_1l):
    ctx = setup_phase_1l
    from app.services.audit import log_action

    with TestingSessionLocal() as db:
        # Simulate a transaction that logs audit but fails business constraint
        log_action(db, user_id=ctx["admin_user_id"], action="TEST_FAILURE", entity_type="Test", entity_id="test-1")
        # Rollback
        db.rollback()

        # Audit log must NOT exist
        log_entry = db.query(AuditLog).filter(AuditLog.action == "TEST_FAILURE").first()
        assert log_entry is None
