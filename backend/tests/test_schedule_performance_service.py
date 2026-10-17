import hashlib
import json
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import sessionmaker

from app.core.security import get_password_hash
from app.db.database import engine
from app.db.models import (
    ActivityScheduleResult,
    ConstructionActivity,
    ConstructionSchedule,
    ContractVariationOrder,
    DailyActivityProgress,
    DailyActivityProgressVerification,
    DailyProgressReport,
    Document,
    MonitoringBaseline,
    Project,
    SchedulePerformanceSnapshot,
    User,
)
from app.schemas.schedule_performance import (
    SchedulePerformanceCreateRequest,
    SchedulePerformanceSnapshotResponse,
    SchedulePerformanceSupersedeRequest,
)
from app.services.schedule_performance_service import (
    calculate_actual_time_days,
    calculate_date_duration_days,
    calculate_earned_schedule_days,
    calculate_residual_float_days,
    calculate_schedule_performance_index,
    calculate_schedule_variance_days,
    create_schedule_performance_snapshot,
    finalize_schedule_performance_snapshot,
    generate_schedule_performance_canonical_hash,
    get_schedule_performance_summary,
    supersede_schedule_performance_snapshot,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def setup_service_test_data():
    adm_email = f"adm_1t_svc_{uuid.uuid4().hex[:6]}@test.com"
    sup_email = f"sup_1t_svc_{uuid.uuid4().hex[:6]}@test.com"
    cnt_email = f"cnt_1t_svc_{uuid.uuid4().hex[:6]}@test.com"

    with TestingSessionLocal() as db:
        adm = User(email=adm_email, password_hash=get_password_hash("pass"), role="admin")
        sup = User(email=sup_email, password_hash=get_password_hash("pass"), role="site_supervisor")
        cnt = User(email=cnt_email, password_hash=get_password_hash("pass"), role="contractor")
        db.add_all([adm, sup, cnt])
        db.commit()
        db.refresh(adm)
        db.refresh(sup)
        db.refresh(cnt)

        proj = Project(name=f"Proj 1T Svc {uuid.uuid4().hex[:4]}", created_by=adm.id)
        proj_b = Project(name=f"Proj 1T Svc B {uuid.uuid4().hex[:4]}", created_by=adm.id)
        db.add_all([proj, proj_b])
        db.commit()
        db.refresh(proj)
        db.refresh(proj_b)

        act = ConstructionActivity(
            project_id=proj.id,
            activity_code="ACT-1T-SVC-01",
            activity_name="Excavation Works",
            activity_type="CONSTRUCTION",
            created_by=adm.id,
        )
        act_b = ConstructionActivity(
            project_id=proj_b.id,
            activity_code="ACT-1T-SVC-B01",
            activity_name="Project B Excavation",
            activity_type="CONSTRUCTION",
            created_by=adm.id,
        )
        db.add_all([act, act_b])
        db.commit()
        db.refresh(act)
        db.refresh(act_b)

        sched = ConstructionSchedule(
            project_id=proj.id,
            schedule_version="1.0",
            calculation_status="CALCULATED",
            algorithm_version="1.0",
            input_snapshot_json={},
            calculated_by=adm.id,
        )
        db.add(sched)
        db.commit()
        db.refresh(sched)

        # CPM result for activity: planned start day 0, planned finish day 20, duration 20, float 5
        sched_res = ActivityScheduleResult(
            schedule_id=sched.id,
            activity_id=act.id,
            es=Decimal("0.000000"),
            ef=Decimal("20.000000"),
            ls=Decimal("5.000000"),
            lf=Decimal("25.000000"),
            total_float=Decimal("5.000000"),
            is_critical=False,
        )
        db.add(sched_res)
        db.commit()

        base = MonitoringBaseline(
            project_id=proj.id,
            schedule_id=sched.id,
            schedule_version="1.0",
            schedule_algorithm_version="1.0",
            baseline_start_date=date(2027, 1, 1),
            frozen_by=adm.id,
            status="ACTIVE",
        )
        db.add(base)
        db.commit()
        db.refresh(base)

        doc = Document(
            project_id=proj.id,
            original_filename="delay_notice.pdf",
            storage_key="docs/delay_notice.pdf",
            file_size_bytes=2048,
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            mime_type="application/pdf",
            document_type="DELAY_NOTICE",
            uploaded_by=adm.id,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        cvo = ContractVariationOrder(
            project_id=proj.id,
            variation_number=f"VO-1T-SVC-{uuid.uuid4().hex[:4]}",
            variation_type="EXTRA_ITEM_ADDITION",
            unit_of_measure="m3",
            quantity_delta=Decimal("25.0000"),
            rate_previous=Decimal("600.00"),
            rate_revised=Decimal("600.00"),
            effective_date=date(2027, 1, 15),
            status="DRAFT",
            description="Trench depth expansion",
        )
        db.add(cvo)
        db.commit()
        db.refresh(cvo)

        adm_id = adm.id
        sup_id = sup.id
        cnt_id = cnt.id
        proj_id = proj.id
        proj_b_id = proj_b.id

        from app.db.models import ProjectMember
        db.add_all([
            ProjectMember(project_id=proj_id, user_id=adm_id),
            ProjectMember(project_id=proj_id, user_id=sup_id),
            ProjectMember(project_id=proj_id, user_id=cnt_id),
            ProjectMember(project_id=proj_b_id, user_id=adm_id),
            ProjectMember(project_id=proj_b_id, user_id=sup_id),
        ])
        db.commit()

        return {
            "adm_id": adm_id,
            "sup_id": sup_id,
            "cnt_id": cnt_id,
            "proj_id": proj_id,
            "proj_b_id": proj_b_id,
            "act_id": act.id,
            "act_b_id": act_b.id,
            "sched_id": sched.id,
            "base_id": base.id,
            "doc_id": doc.id,
            "cvo_id": cvo.id,
        }


# ==============================================================================
# 1. UNIT TEST: DETERMINISTIC DATE DURATION & EARNED SCHEDULE MATHEMATICS
# ==============================================================================

def test_01_date_duration_inclusive_convention():
    """Verify standard construction inclusive date duration (finish - start + 1)."""
    # Same day = 1 day
    assert calculate_date_duration_days(date(2027, 1, 1), date(2027, 1, 1)) == 1
    # 2027-01-01 to 2027-01-20 = 20 days
    assert calculate_date_duration_days(date(2027, 1, 1), date(2027, 1, 20)) == 20
    # None operands return None
    assert calculate_date_duration_days(None, date(2027, 1, 20)) is None
    assert calculate_date_duration_days(date(2027, 1, 1), None) is None
    # Inverted dates raise ValueError
    with pytest.raises(ValueError):
        calculate_date_duration_days(date(2027, 1, 20), date(2027, 1, 10))


def test_02_actual_time_days_elapsed():
    """Verify AT elapsed calculation."""
    # 2027-01-01 to 2027-01-24 = 24 days
    at = calculate_actual_time_days(date(2027, 1, 1), date(2027, 1, 24))
    assert at == Decimal("24.0000")
    # None operands return None
    assert calculate_actual_time_days(None, date(2027, 1, 24)) is None
    # Evaluation prior to start returns 0.0000
    assert calculate_actual_time_days(date(2027, 1, 10), date(2027, 1, 5)) == Decimal("0.0000")


def test_03_earned_schedule_standard_and_boundary_cases():
    """Verify ES = PD * (Actual Pct / 100)."""
    # 20 days PD, 50% physical progress = 10 days ES
    es = calculate_earned_schedule_days(20, Decimal("50.0000"))
    assert es == Decimal("10.0000")

    # 30 days PD, 33.3333% progress = 9.99999 -> 10.0000
    es = calculate_earned_schedule_days(30, Decimal("33.3333"))
    assert es == Decimal("10.0000")

    # 100% progress = 20.0000 days
    es = calculate_earned_schedule_days(20, Decimal("100.0000"))
    assert es == Decimal("20.0000")

    # 0% progress = 0.0000 days
    es = calculate_earned_schedule_days(20, Decimal("0.0000"))
    assert es == Decimal("0.0000")

    # Missing operands never substitute zero
    assert calculate_earned_schedule_days(None, Decimal("50.0000")) is None
    assert calculate_earned_schedule_days(20, None) is None


def test_04_schedule_variance_and_performance_index():
    """Verify SV_t = ES - AT and SPI_t = ES / AT."""
    # Case: Ahead of schedule: ES = 24, AT = 20 => SV = +4, SPI = 1.200000
    es = Decimal("24.0000")
    at = Decimal("20.0000")
    assert calculate_schedule_variance_days(es, at) == Decimal("4.0000")
    assert calculate_schedule_performance_index(es, at) == Decimal("1.200000")

    # Case: Delayed: ES = 16, AT = 20 => SV = -4, SPI = 0.800000
    es_del = Decimal("16.0000")
    assert calculate_schedule_variance_days(es_del, at) == Decimal("-4.0000")
    assert calculate_schedule_performance_index(es_del, at) == Decimal("0.800000")

    # Zero denominator protection: AT = 0
    at_zero = Decimal("0.0000")
    assert calculate_schedule_performance_index(es, at_zero) is None
    assert calculate_schedule_performance_index(Decimal("0.0000"), at_zero) is None

    # Missing operands return None
    assert calculate_schedule_variance_days(None, at) is None
    assert calculate_schedule_performance_index(None, at) is None


def test_05_residual_float_absorption_and_depletion():
    """Verify residual float = baseline float - delay slip."""
    # Baseline float = 5 days, SV_t = -3 days (3 days delay slip) => Residual Float = 2 days
    assert calculate_residual_float_days(5, Decimal("-3.0000")) == 2

    # Baseline float = 5 days, SV_t = -5 days (exact absorption) => Residual Float = 0 days
    assert calculate_residual_float_days(5, Decimal("-5.0000")) == 0

    # Baseline float = 5 days, SV_t = -7 days (float breached) => Residual Float = -2 days
    assert calculate_residual_float_days(5, Decimal("-7.0000")) == -2

    # Ahead of schedule (SV_t = +2 days) => Residual Float remains unchanged at 5 days
    assert calculate_residual_float_days(5, Decimal("2.0000")) == 5

    # Missing operands return None
    assert calculate_residual_float_days(None, Decimal("-3.0000")) is None
    assert calculate_residual_float_days(5, None) is None


# ==============================================================================
# 2. SCHEMA VALIDATION TESTS
# ==============================================================================

def test_06_schema_rejects_client_setting_finalized_status():
    """Verify schema blocks callers from setting status='FINALIZED' on creation."""
    with pytest.raises(ValidationError) as exc:
        SchedulePerformanceCreateRequest(
            activity_id="act-1",
            evaluation_date=date(2027, 1, 31),
            status="FINALIZED",  # Disallowed!
        )
    assert "Snapshots must always be created in DRAFT status" in str(exc.value)


def test_07_schema_rejects_invalid_delay_enums():
    """Verify schema enforces valid delay and performance enums and forbids extra fields."""
    with pytest.raises(ValidationError) as exc:
        SchedulePerformanceCreateRequest(
            activity_id="act-1",
            evaluation_date=date(2027, 1, 31),
            supervisor_assessed_delay_status="NOT_A_VALID_DELAY",
        )
    assert "supervisor_assessed_delay_status must be one of" in str(exc.value)

    # Extra inputs like delay_status are forbidden
    with pytest.raises(ValidationError) as exc2:
        SchedulePerformanceCreateRequest(
            activity_id="act-1",
            evaluation_date=date(2027, 1, 31),
            delay_status="ON_SCHEDULE",
        )
    assert "Extra inputs are not permitted" in str(exc2.value)


def test_08_schema_rejects_inverted_dates():
    """Verify schema rejects inverted date pairs."""
    with pytest.raises(ValidationError) as exc:
        SchedulePerformanceCreateRequest(
            activity_id="act-1",
            evaluation_date=date(2027, 1, 31),
            performance_period_start=date(2027, 2, 1),
            performance_period_end=date(2027, 1, 1),  # Inverted!
        )
    assert "performance_period_start cannot be after performance_period_end" in str(exc.value)


# ==============================================================================
# 3. SERVICE WORKFLOW & PROVENANCE TESTS
# ==============================================================================

def test_09_create_snapshot_derived_from_cpm_and_baseline(setup_service_test_data):
    """Verify service creates draft snapshot linking CPM schedule result and baseline start date."""
    d = setup_service_test_data
    with TestingSessionLocal() as db:
        adm = db.query(User).filter(User.id == d["adm_id"]).first()
        req = SchedulePerformanceCreateRequest(
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            evaluation_date=date(2027, 1, 24),
            actual_start_date=date(2027, 1, 1),
            actual_cumulative_progress_pct=Decimal("80.0000"),
        )
        snap = create_schedule_performance_snapshot(db, d["proj_id"], req, adm)

        assert snap.id is not None
        assert snap.status == "DRAFT"
        assert snap.algorithm_version == "SCHED_PERFORMANCE_1.0_LINEAR"
        assert snap.provenance_metadata["planned_progress_curve_type"] == "LINEAR_CPM_APPROXIMATION"
        # Planned start derived from baseline anchor 2027-01-01 + es=0 => 2027-01-01
        assert snap.planned_start_date == date(2027, 1, 1)
        # Planned duration 20 days
        assert snap.planned_duration_days == 20
        # AT: 2027-01-01 to 2027-01-24 = 24 days
        assert snap.actual_time_days == Decimal("24.0000")
        # ES: 20 * 80% = 16.0000 days
        assert snap.earned_schedule_days == Decimal("16.0000")
        # SV_t = 16 - 24 = -8.0000 days
        assert snap.schedule_variance_days == Decimal("-8.0000")
        # SPI_t = 16 / 24 = 0.666667
        assert snap.schedule_performance_index == Decimal("0.666667")
        # Baseline float 5, slip 8 days => Residual float -3 days
        assert snap.residual_total_float_days == -3
        assert snap.delay_status == "CRITICAL_DELAY"
        assert snap.performance_status == "CRITICAL_DELAY"
        assert snap.canonical_hash is not None


def test_10_missing_operands_yield_requires_input(setup_service_test_data):
    """Verify missing progress or dates leaves metrics None and sets delay_status='REQUIRES_INPUT'."""
    d = setup_service_test_data
    with TestingSessionLocal() as db:
        adm = db.query(User).filter(User.id == d["adm_id"]).first()
        req = SchedulePerformanceCreateRequest(
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            evaluation_date=date(2027, 1, 15),
            # No actual start, no progress pct
        )
        snap = create_schedule_performance_snapshot(db, d["proj_id"], req, adm)

        assert snap.status == "DRAFT"
        assert snap.actual_time_days is None
        assert snap.earned_schedule_days is None
        assert snap.schedule_variance_days is None
        assert snap.delay_status == "REQUIRES_INPUT"
        assert snap.performance_status == "REQUIRES_INPUT"


def test_11_cross_project_isolation(setup_service_test_data):
    """Verify service strictly rejects activity from a different project."""
    d = setup_service_test_data
    with TestingSessionLocal() as db:
        adm = db.query(User).filter(User.id == d["adm_id"]).first()
        req = SchedulePerformanceCreateRequest(
            activity_id=d["act_b_id"],  # Belongs to proj_b!
            evaluation_date=date(2027, 1, 20),
        )
        with pytest.raises(Exception) as exc:
            create_schedule_performance_snapshot(db, d["proj_id"], req, adm)
        assert "not found in project" in str(exc.value)


def test_12_contractor_mutation_blocked(setup_service_test_data):
    """Verify contractor role cannot create or mutate performance snapshots."""
    d = setup_service_test_data
    with TestingSessionLocal() as db:
        cnt = db.query(User).filter(User.id == d["cnt_id"]).first()
        req = SchedulePerformanceCreateRequest(
            activity_id=d["act_id"],
            evaluation_date=date(2027, 1, 20),
        )
        with pytest.raises(Exception) as exc:
            create_schedule_performance_snapshot(db, d["proj_id"], req, cnt)
        assert "Operation not permitted for role" in str(exc.value)


def test_13_canonical_hash_sensitivity_and_tamper_resistance(setup_service_test_data):
    """Verify canonical SHA-256 is deterministic and sensitive to input/output changes."""
    payload_1 = {
        "project_id": "p1",
        "activity_id": "a1",
        "evaluation_date": "2027-01-31",
        "earned_schedule_days": "16.0000",
        "actual_time_days": "24.0000",
    }
    payload_2 = {
        "actual_time_days": "24.0000",
        "earned_schedule_days": "16.0000",
        "evaluation_date": "2027-01-31",
        "activity_id": "a1",
        "project_id": "p1",
    }
    payload_3 = {
        "project_id": "p1",
        "activity_id": "a1",
        "evaluation_date": "2027-01-31",
        "earned_schedule_days": "17.0000",  # Changed!
        "actual_time_days": "24.0000",
    }
    h1 = generate_schedule_performance_canonical_hash(payload_1)
    h2 = generate_schedule_performance_canonical_hash(payload_2)
    h3 = generate_schedule_performance_canonical_hash(payload_3)
    assert h1 == h2
    assert h1 != h3


def test_14_finalization_and_authoritative_locking(setup_service_test_data):
    """Verify service finalizes draft snapshot and prevents duplicate authoritative snapshots."""
    d = setup_service_test_data
    with TestingSessionLocal() as db:
        adm = db.query(User).filter(User.id == d["adm_id"]).first()
        req1 = SchedulePerformanceCreateRequest(
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            performance_period_start=date(2027, 2, 1),
            performance_period_end=date(2027, 2, 28),
            evaluation_date=date(2027, 2, 28),
            actual_start_date=date(2027, 2, 1),
            actual_cumulative_progress_pct=Decimal("100.0000"),
        )
        snap1 = create_schedule_performance_snapshot(db, d["proj_id"], req1, adm)
        finalized_1 = finalize_schedule_performance_snapshot(db, d["proj_id"], snap1.id, adm)

        assert finalized_1.status == "FINALIZED"
        assert finalized_1.finalized_by == d["adm_id"]
        assert finalized_1.finalized_at is not None

        # Create second draft for same period
        req2 = SchedulePerformanceCreateRequest(
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            performance_period_start=date(2027, 2, 1),
            performance_period_end=date(2027, 2, 28),
            evaluation_date=date(2027, 2, 28),
            actual_start_date=date(2027, 2, 1),
            actual_cumulative_progress_pct=Decimal("95.0000"),
        )
        snap2 = create_schedule_performance_snapshot(db, d["proj_id"], req2, adm)

        # Attempting to finalize snap2 must fail with HTTP 409 Conflict
        with pytest.raises(Exception) as exc:
            finalize_schedule_performance_snapshot(db, d["proj_id"], snap2.id, adm)
        assert "Authoritative finalized snapshot already exists" in str(exc.value)


def test_15_supersession_workflow_and_validation(setup_service_test_data):
    """Verify supersession validates reason, matching identity, and prevents self-reference."""
    d = setup_service_test_data
    with TestingSessionLocal() as db:
        adm = db.query(User).filter(User.id == d["adm_id"]).first()
        # 1. Create and finalize original snapshot
        req_orig = SchedulePerformanceCreateRequest(
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            performance_period_start=date(2027, 3, 1),
            performance_period_end=date(2027, 3, 31),
            evaluation_date=date(2027, 3, 31),
            actual_start_date=date(2027, 3, 1),
            actual_cumulative_progress_pct=Decimal("70.0000"),
        )
        snap_orig = create_schedule_performance_snapshot(db, d["proj_id"], req_orig, adm)
        finalize_schedule_performance_snapshot(db, d["proj_id"], snap_orig.id, adm)

        # 2. Self-supersession rejection
        with pytest.raises(Exception) as exc:
            supersede_schedule_performance_snapshot(
                db, d["proj_id"], snap_orig.id, "Self superseding", snap_orig.id, adm
            )
        assert "A snapshot cannot supersede itself" in str(exc.value)

        # 3. Create replacement snapshot for matching identity
        req_repl = SchedulePerformanceCreateRequest(
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            performance_period_start=date(2027, 3, 1),
            performance_period_end=date(2027, 3, 31),
            evaluation_date=date(2027, 3, 31),
            actual_start_date=date(2027, 3, 1),
            actual_cumulative_progress_pct=Decimal("75.0000"),
        )
        snap_repl = create_schedule_performance_snapshot(db, d["proj_id"], req_repl, adm)

        # 4. Perform valid supersession
        superseded = supersede_schedule_performance_snapshot(
            db, d["proj_id"], snap_orig.id, "Recalibrated physical progress via survey", snap_repl.id, adm
        )
        assert superseded.status == "SUPERSEDED"
        assert superseded.superseded_by == snap_repl.id
        assert superseded.supersession_reason == "Recalibrated physical progress via survey"

        # 5. Now snap_repl can be finalized without 409 conflict
        finalized_repl = finalize_schedule_performance_snapshot(db, d["proj_id"], snap_repl.id, adm)
        assert finalized_repl.status == "FINALIZED"


def test_16_schedule_performance_summary(setup_service_test_data):
    """Verify aggregated summary computes mean SPI, total SV, and distributions."""
    d = setup_service_test_data
    with TestingSessionLocal() as db:
        adm = db.query(User).filter(User.id == d["adm_id"]).first()
        summary = get_schedule_performance_summary(db, d["proj_id"], date(2027, 12, 31), adm)
        assert summary.project_id == d["proj_id"]
        assert summary.total_snapshots > 0
        assert summary.delay_status_distribution is not None


# ==============================================================================
# 4. STEP 2 HARDENING REVIEW TESTS
# ==============================================================================

def test_17_schedule_variance_tolerance_boundary_conditions():
    """Verify exact boundary conditions for +/- 0.5000 day schedule variance tolerance."""
    from app.services.schedule_performance_service import determine_delay_and_performance_status

    eval_d = date(2027, 1, 20)

    # 1. SV > +0.5000 days => AHEAD_OF_SCHEDULE
    d_st, p_st, _ = determine_delay_and_performance_status(
        None, date(2027, 1, 1), eval_d, Decimal("0.5001"), 5, False
    )
    assert d_st == "AHEAD_OF_SCHEDULE"
    assert p_st == "ON_TRACK"

    # 2. SV == +0.5000 days => ON_SCHEDULE (boundary)
    d_st, p_st, _ = determine_delay_and_performance_status(
        None, date(2027, 1, 1), eval_d, Decimal("0.5000"), 5, False
    )
    assert d_st == "ON_SCHEDULE"
    assert p_st == "ON_TRACK"

    # 3. SV == 0.0000 days => ON_SCHEDULE
    d_st, p_st, _ = determine_delay_and_performance_status(
        None, date(2027, 1, 1), eval_d, Decimal("0.0000"), 5, False
    )
    assert d_st == "ON_SCHEDULE"
    assert p_st == "ON_TRACK"

    # 4. SV == -0.5000 days => ON_SCHEDULE (boundary)
    d_st, p_st, _ = determine_delay_and_performance_status(
        None, date(2027, 1, 1), eval_d, Decimal("-0.5000"), 5, False
    )
    assert d_st == "ON_SCHEDULE"
    assert p_st == "ON_TRACK"

    # 5. SV == -0.5001 days => MINOR_DELAY (outside tolerance, non-critical, float remaining)
    d_st, p_st, _ = determine_delay_and_performance_status(
        None, date(2027, 1, 1), eval_d, Decimal("-0.5001"), 5, False
    )
    assert d_st == "MINOR_DELAY"
    assert p_st == "SCHEDULE_VARIANCE_WITHIN_TOLERANCE"

    # 6. SV < -0.5000 with float == 0 => FLOAT_ABSORBED
    d_st, p_st, _ = determine_delay_and_performance_status(
        None, date(2027, 1, 1), eval_d, Decimal("-3.0000"), 0, False
    )
    assert d_st == "FLOAT_ABSORBED"
    assert p_st == "SCHEDULE_VARIANCE_WITHIN_TOLERANCE"

    # 7. SV < -0.5000 with float < 0 => CRITICAL_DELAY (exhausted float)
    d_st, p_st, cp_imp = determine_delay_and_performance_status(
        None, date(2027, 1, 1), eval_d, Decimal("-6.0000"), -1, False
    )
    assert d_st == "CRITICAL_DELAY"
    assert p_st == "CRITICAL_DELAY"
    assert cp_imp == 1

    # 8. SV < -0.5000 on critical path => CRITICAL_DELAY
    d_st, p_st, cp_imp = determine_delay_and_performance_status(
        None, date(2027, 1, 1), eval_d, Decimal("-2.5000"), 0, True
    )
    assert d_st == "CRITICAL_DELAY"
    assert p_st == "CRITICAL_DELAY"
    assert cp_imp == 3


def test_18_supervisor_assessed_status_does_not_override_calculated_delay_status(setup_service_test_data):
    """Verify caller supervisor assessment is recorded in metadata but never overwrites calculated status."""
    d = setup_service_test_data
    with TestingSessionLocal() as db:
        adm = db.query(User).filter(User.id == d["adm_id"]).first()
        req = SchedulePerformanceCreateRequest(
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            evaluation_date=date(2027, 1, 24),
            actual_start_date=date(2027, 1, 1),
            actual_cumulative_progress_pct=Decimal("80.0000"),  # Results in SV = -8 (CRITICAL_DELAY)
            supervisor_assessed_delay_status="ON_SCHEDULE",    # Human assessment claims on schedule
            delay_justification="Supervisor claims minor catch-up on weekend",
        )
        snap = create_schedule_performance_snapshot(db, d["proj_id"], req, adm)

        # Deterministic calculation must remain authoritative on persisted delay_status
        assert snap.delay_status == "CRITICAL_DELAY"
        assert snap.performance_status == "CRITICAL_DELAY"

        # Human assessment is preserved in input snapshot and provenance
        assert snap.input_snapshot_json["supervisor_assessed_delay_status"] == "ON_SCHEDULE"
        assert snap.provenance_metadata["supervisor_assessed_delay_status"] == "ON_SCHEDULE"
        assert snap.provenance_metadata["computed_delay_status"] == "CRITICAL_DELAY"


def test_19_baseline_schedule_mismatch_rejection(setup_service_test_data):
    """Verify service rejects snapshot creation when monitoring_baseline_id schedule does not match schedule_id."""
    d = setup_service_test_data
    with TestingSessionLocal() as db:
        adm = db.query(User).filter(User.id == d["adm_id"]).first()

        # Create an alternative schedule for same project
        other_sched = ConstructionSchedule(
            project_id=d["proj_id"],
            schedule_version="2.0",
            calculation_status="CALCULATED",
            algorithm_version="1.0",
            input_snapshot_json={},
            calculated_by=adm.id,
        )
        db.add(other_sched)
        db.commit()
        db.refresh(other_sched)

        # Baseline d["base_id"] points to d["sched_id"]. Request targets other_sched.id!
        req = SchedulePerformanceCreateRequest(
            activity_id=d["act_id"],
            schedule_id=other_sched.id,
            monitoring_baseline_id=d["base_id"],  # Mismatch!
            evaluation_date=date(2027, 1, 24),
        )
        with pytest.raises(Exception) as exc:
            create_schedule_performance_snapshot(db, d["proj_id"], req, adm)
        assert "does not match snapshot schedule_id" in str(exc.value)


def test_20_progress_provenance_and_override_reason_requirement(setup_service_test_data):
    """Verify that overriding verified upstream progress requires override_reason."""
    d = setup_service_test_data
    with TestingSessionLocal() as db:
        adm = db.query(User).filter(User.id == d["adm_id"]).first()

        # 1. Without verifications, direct entry is classified as DIRECT_ENTRY_UNVERIFIED
        sched_b = ConstructionSchedule(
            project_id=d["proj_b_id"],
            schedule_version="1.0",
            calculation_status="CALCULATED",
            algorithm_version="1.0",
            input_snapshot_json={},
            calculated_by=adm.id,
        )
        db.add(sched_b)
        db.commit()
        db.refresh(sched_b)

        req_direct = SchedulePerformanceCreateRequest(
            activity_id=d["act_b_id"],
            schedule_id=sched_b.id,  # In proj_b, act_b has no verifications
            evaluation_date=date(2027, 1, 20),
            actual_start_date=date(2027, 1, 1),
            actual_cumulative_progress_pct=Decimal("50.0000"),
        )
        snap_direct = create_schedule_performance_snapshot(db, d["proj_b_id"], req_direct, adm)
        assert snap_direct.provenance_metadata["progress_provenance"] == "DIRECT_ENTRY_UNVERIFIED"

        # 2. Seed a verified daily progress record for act_id (50% verified progress)
        dpr = DailyProgressReport(
            project_id=d["proj_id"],
            report_date=date(2027, 1, 15),
            submitted_by=adm.id,
            submission_status="SUBMITTED",
        )
        db.add(dpr)
        db.commit()
        db.refresh(dpr)

        dap = DailyActivityProgress(
            daily_report_id=dpr.id,
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            contractor_percent_complete=Decimal("50.00"),
            contractor_status="IN_PROGRESS",
            created_by=adm.id,
        )
        db.add(dap)
        db.commit()
        db.refresh(dap)

        dapv = DailyActivityProgressVerification(
            project_id=d["proj_id"],
            daily_activity_progress_id=dap.id,
            verification_status="VERIFIED",
            verified_percent_complete=Decimal("50.0000"),
            verified_actual_start=date(2027, 1, 1),
            verified_by=adm.id,
        )
        db.add(dapv)
        db.commit()
        db.refresh(dapv)

        # If user supplies 60.0000 without override_reason, it must fail with HTTP 422
        req_override_no_reason = SchedulePerformanceCreateRequest(
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            evaluation_date=date(2027, 1, 20),
            actual_start_date=date(2027, 1, 1),
            actual_cumulative_progress_pct=Decimal("60.0000"),
            # override_reason is omitted!
        )
        with pytest.raises(Exception) as exc:
            create_schedule_performance_snapshot(db, d["proj_id"], req_override_no_reason, adm)
        assert "requires an explicit override_reason" in str(exc.value)

        # 3. If override_reason is provided, snapshot is accepted with MANUAL_OVERRIDE provenance
        req_override_valid = SchedulePerformanceCreateRequest(
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            evaluation_date=date(2027, 1, 20),
            actual_start_date=date(2027, 1, 1),
            actual_cumulative_progress_pct=Decimal("60.0000"),
            override_reason="Laser scanner measurement conducted after daily report submittal",
        )
        snap_override = create_schedule_performance_snapshot(db, d["proj_id"], req_override_valid, adm)
        assert snap_override.provenance_metadata["progress_provenance"] == "MANUAL_OVERRIDE"
        assert snap_override.provenance_metadata["override_reason"] == "Laser scanner measurement conducted after daily report submittal"
        assert dapv.id in snap_override.provenance_metadata["upstream_verification_ids"]


def test_21_canonical_hash_strict_typing_and_metadata_sensitivity():
    """Verify canonical hash uses strict type normalization (no default=str) and changes on any material field."""
    from app.services.schedule_performance_service import generate_schedule_performance_canonical_hash

    base_payload = {
        "project_id": "proj-1",
        "activity_id": "act-1",
        "schedule_id": "sched-1",
        "monitoring_baseline_id": "base-1",
        "evaluation_date": "2027-01-31",
        "earned_schedule_days": "16.0000",
        "actual_time_days": "24.0000",
        "delay_status": "CRITICAL_DELAY",
        "algorithm_version": "SCHED_PERFORMANCE_1.0_LINEAR",
    }
    h_base = generate_schedule_performance_canonical_hash(base_payload)

    # 1. Verify key order independence
    reversed_keys = {k: base_payload[k] for k in reversed(list(base_payload.keys()))}
    assert generate_schedule_performance_canonical_hash(reversed_keys) == h_base

    # 2. Verify sensitive to monitoring_baseline_id change
    payload_mod_base = dict(base_payload)
    payload_mod_base["monitoring_baseline_id"] = "base-2"
    assert generate_schedule_performance_canonical_hash(payload_mod_base) != h_base

    # 3. Verify sensitive to delay_status change
    payload_mod_status = dict(base_payload)
    payload_mod_status["delay_status"] = "ON_SCHEDULE"
    assert generate_schedule_performance_canonical_hash(payload_mod_status) != h_base

    # 4. Verify sensitive to algorithm_version change
    payload_mod_algo = dict(base_payload)
    payload_mod_algo["algorithm_version"] = "SCHED_PERFORMANCE_2.0"
    assert generate_schedule_performance_canonical_hash(payload_mod_algo) != h_base


def test_22_canonical_hash_rejects_unsupported_types_and_non_string_keys():
    """Verify canonical hash raises TypeError on non-string keys or unsupported objects."""
    from app.services.schedule_performance_service import generate_schedule_performance_canonical_hash

    # Non-string dictionary keys must raise TypeError
    with pytest.raises(TypeError) as exc1:
        generate_schedule_performance_canonical_hash({123: "numeric_key"})
    assert "dictionary keys must be strings" in str(exc1.value)

    # Arbitrary complex/custom objects must raise TypeError rather than str(obj)
    class ArbitraryCustomObject:
        pass

    with pytest.raises(TypeError) as exc2:
        generate_schedule_performance_canonical_hash({"obj": ArbitraryCustomObject()})
    assert "Unsupported type for canonical JSON serialization" in str(exc2.value)


def test_23_schedule_resolution_without_schedule_or_baseline_fails(setup_service_test_data):
    """Verify create_schedule_performance_snapshot rejects requests with no schedule_id and no baseline."""
    d = setup_service_test_data
    with TestingSessionLocal() as db:
        adm = db.query(User).filter(User.id == d["adm_id"]).first()
        req = SchedulePerformanceCreateRequest(
            activity_id=d["act_id"],
            schedule_id=None,
            monitoring_baseline_id=None,
            evaluation_date=date(2027, 1, 24),
        )
        with pytest.raises(Exception) as exc:
            create_schedule_performance_snapshot(db, d["proj_id"], req, adm)
        assert "schedule_id or an explicit monitoring_baseline_id must be provided" in str(exc.value)


def test_24_schedule_derived_from_explicit_baseline_without_schedule_id(setup_service_test_data):
    """Verify schedule_id is cleanly derived from explicit monitoring_baseline_id when omitted."""
    d = setup_service_test_data
    with TestingSessionLocal() as db:
        adm = db.query(User).filter(User.id == d["adm_id"]).first()
        req = SchedulePerformanceCreateRequest(
            activity_id=d["act_id"],
            schedule_id=None,  # Not provided, should be derived from baseline
            monitoring_baseline_id=d["base_id"],
            evaluation_date=date(2027, 1, 24),
            actual_start_date=date(2027, 1, 1),
            actual_cumulative_progress_pct=Decimal("50.0000"),
        )
        snap = create_schedule_performance_snapshot(db, d["proj_id"], req, adm)
        assert snap.schedule_id == d["sched_id"]
        assert snap.monitoring_baseline_id == d["base_id"]


def test_25_evaluation_date_before_performance_period_start_rejected():
    """Verify schema rejects evaluation_date that precedes performance_period_start."""
    with pytest.raises(ValidationError) as exc:
        SchedulePerformanceCreateRequest(
            activity_id="act-1",
            evaluation_date=date(2027, 1, 1),
            performance_period_start=date(2027, 1, 15),
            performance_period_end=date(2027, 1, 31),
        )
    assert "evaluation_date (2027-01-01) cannot be before performance_period_start" in str(exc.value)


def test_26_progress_percentage_out_of_bounds_rejected():
    """Verify schema strictly rejects negative progress or progress exceeding 100%."""
    with pytest.raises(ValidationError) as exc1:
        SchedulePerformanceCreateRequest(
            activity_id="act-1",
            evaluation_date=date(2027, 1, 31),
            actual_cumulative_progress_pct=Decimal("-5.0000"),
        )
    assert "actual_cumulative_progress_pct must be between 0.0000 and 100.0000" in str(exc1.value)

    with pytest.raises(ValidationError) as exc2:
        SchedulePerformanceCreateRequest(
            activity_id="act-1",
            evaluation_date=date(2027, 1, 31),
            actual_cumulative_progress_pct=Decimal("105.0000"),
        )
    assert "actual_cumulative_progress_pct must be between 0.0000 and 100.0000" in str(exc2.value)


def test_27_supersession_prevents_cycles_and_invalid_replacement_status(setup_service_test_data):
    """Verify supersession blocks self-supersession and circular supersession."""
    d = setup_service_test_data
    with TestingSessionLocal() as db:
        adm = db.query(User).filter(User.id == d["adm_id"]).first()

        # Create and finalize snap1
        req1 = SchedulePerformanceCreateRequest(
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            performance_period_start=date(2027, 5, 1),
            performance_period_end=date(2027, 5, 31),
            evaluation_date=date(2027, 5, 31),
            actual_start_date=date(2027, 5, 1),
            actual_cumulative_progress_pct=Decimal("60.0000"),
            override_reason="Progress re-estimated by supervisor",
        )
        snap1 = create_schedule_performance_snapshot(db, d["proj_id"], req1, adm)
        finalize_schedule_performance_snapshot(db, d["proj_id"], snap1.id, adm)

        # Create replacement snap2
        req2 = SchedulePerformanceCreateRequest(
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            performance_period_start=date(2027, 5, 1),
            performance_period_end=date(2027, 5, 31),
            evaluation_date=date(2027, 5, 31),
            actual_start_date=date(2027, 5, 1),
            actual_cumulative_progress_pct=Decimal("65.0000"),
            override_reason="Progress re-calibrated via survey",
        )
        snap2 = create_schedule_performance_snapshot(db, d["proj_id"], req2, adm)

        # Supersede snap1 with snap2
        supersede_schedule_performance_snapshot(
            db, d["proj_id"], snap1.id, "Corrected progress reading", snap2.id, adm
        )

        # Finalize snap2
        finalize_schedule_performance_snapshot(db, d["proj_id"], snap2.id, adm)

        # Attempt circular supersession: try superseding snap2 with snap1
        with pytest.raises(Exception) as exc:
            supersede_schedule_performance_snapshot(
                db, d["proj_id"], snap2.id, "Circular attempt", snap1.id, adm
            )
        assert "Replacement snapshot cannot already be SUPERSEDED" in str(exc.value) or "Cannot create cyclical" in str(exc.value)


def test_28_deterministic_verification_ordering_tie_breaking(setup_service_test_data):
    """Verify multiple verifications on same report date use verified_at and ID tie-breaking."""
    d = setup_service_test_data
    with TestingSessionLocal() as db:
        adm = db.query(User).filter(User.id == d["adm_id"]).first()

        dpr = DailyProgressReport(
            project_id=d["proj_id"],
            report_date=date(2027, 6, 15),
            submitted_by=adm.id,
            submission_status="SUBMITTED",
        )
        db.add(dpr)
        db.commit()
        db.refresh(dpr)

        dap = DailyActivityProgress(
            daily_report_id=dpr.id,
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            contractor_percent_complete=Decimal("40.00"),
            contractor_status="IN_PROGRESS",
            created_by=adm.id,
        )
        db.add(dap)
        db.commit()
        db.refresh(dap)

        # Seed two verifications for same activity on same report
        v1 = DailyActivityProgressVerification(
            project_id=d["proj_id"],
            daily_activity_progress_id=dap.id,
            verification_status="VERIFIED",
            verified_percent_complete=Decimal("42.0000"),
            verified_actual_start=date(2027, 6, 1),
            verified_by=adm.id,
            verified_at=datetime(2027, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
        )
        v2 = DailyActivityProgressVerification(
            project_id=d["proj_id"],
            daily_activity_progress_id=dap.id,
            verification_status="CORRECTED",
            verified_percent_complete=Decimal("45.0000"),
            verified_actual_start=date(2027, 6, 1),
            verified_by=adm.id,
            verified_at=datetime(2027, 6, 15, 14, 0, 0, tzinfo=timezone.utc), # Later time
        )
        db.add_all([v1, v2])
        db.commit()
        db.refresh(v1)
        db.refresh(v2)

        req = SchedulePerformanceCreateRequest(
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            evaluation_date=date(2027, 6, 20),
        )
        snap = create_schedule_performance_snapshot(db, d["proj_id"], req, adm)

        # v2 should win the deterministic tie-breaker (verified_at later)
        assert snap.actual_cumulative_progress_pct == Decimal("45.0000")
        assert snap.provenance_metadata["progress_provenance"] == "SUPERVISOR_VERIFIED"
        assert snap.provenance_metadata["upstream_verification_ids"][0] == v2.id


def test_29_pure_decimal_ceiling_residual_float_precision():
    """Verify calculate_residual_float_days operates without IEEE-754 binary floating-point drift."""
    from app.services.schedule_performance_service import calculate_residual_float_days

    # Exact fractional delay: -0.0001 days consumes 1 integer calendar day of float
    res = calculate_residual_float_days(10, Decimal("-0.0001"))
    assert res == 9

    # Delay of -0.9999 days consumes 1 integer calendar day
    res = calculate_residual_float_days(10, Decimal("-0.9999"))
    assert res == 9

    # Delay of -1.0000 days consumes 1 day
    res = calculate_residual_float_days(10, Decimal("-1.0000"))
    assert res == 9

    # Delay of -1.0001 days consumes 2 days
    res = calculate_residual_float_days(10, Decimal("-1.0001"))
    assert res == 8


def test_30_list_snapshots_filter_validation(setup_service_test_data):
    """Verify service rejects invalid query filters with HTTP 422."""
    from fastapi import HTTPException
    from app.services.schedule_performance_service import list_schedule_performance_snapshots

    d = setup_service_test_data
    with TestingSessionLocal() as db:
        adm = db.query(User).filter(User.id == d["adm_id"]).first()

        # 1. Invalid delay_status
        with pytest.raises(HTTPException) as exc1:
            list_schedule_performance_snapshots(db, d["proj_id"], adm, delay_status="INVALID_DELAY")
        assert exc1.value.status_code == 422
        assert "Invalid delay_status filter" in exc1.value.detail

        # 2. Invalid performance_status
        with pytest.raises(HTTPException) as exc2:
            list_schedule_performance_snapshots(db, d["proj_id"], adm, performance_status="INVALID_PERF")
        assert exc2.value.status_code == 422
        assert "Invalid performance_status filter" in exc2.value.detail

        # 3. Invalid status
        with pytest.raises(HTTPException) as exc3:
            list_schedule_performance_snapshots(db, d["proj_id"], adm, status_filter="INVALID_STATUS")
        assert exc3.value.status_code == 422
        assert "Invalid status filter" in exc3.value.detail
