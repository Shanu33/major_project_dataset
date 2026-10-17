import hashlib
import json
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.core.security import get_password_hash
from app.db.database import engine
from app.db.models import (
    ConstructionActivity,
    ConstructionSchedule,
    Document,
    ContractVariationOrder,
    MonitoringBaseline,
    Project,
    SchedulePerformanceSnapshot,
    User,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def generate_schedule_performance_canonical_hash(payload: dict) -> str:
    """
    Deterministic canonical SHA-256 hash representation for schedule performance snapshot.
    Sorts dictionary keys recursively and generates hexadecimal digest.
    """
    canonical_json = json.dumps(payload, sort_keys=True, separators=(',', ':'), default=str)
    return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()


@pytest.fixture(scope="module")
def setup_db_data():
    adm_email = f"adm_1t_{uuid.uuid4().hex[:6]}@test.com"
    sup_email = f"sup_1t_{uuid.uuid4().hex[:6]}@test.com"

    with TestingSessionLocal() as db:
        adm = User(email=adm_email, password_hash=get_password_hash("pass"), role="admin")
        sup = User(email=sup_email, password_hash=get_password_hash("pass"), role="site_supervisor")
        db.add_all([adm, sup])
        db.commit()
        db.refresh(adm)
        db.refresh(sup)

        proj = Project(name=f"Proj 1T {uuid.uuid4().hex[:4]}", created_by=adm.id)
        db.add(proj)
        db.commit()
        db.refresh(proj)

        act = ConstructionActivity(
            project_id=proj.id,
            activity_code="ACT-1T-01",
            activity_name="Foundation Concrete",
            activity_type="CONSTRUCTION",
            created_by=adm.id,
        )
        db.add(act)
        db.commit()
        db.refresh(act)

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
            original_filename="site_instruction.pdf",
            storage_key="docs/site_instruction.pdf",
            file_size_bytes=1024,
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            mime_type="application/pdf",
            document_type="SITE_INSTRUCTION",
            uploaded_by=adm.id,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        cvo = ContractVariationOrder(
            project_id=proj.id,
            variation_number=f"VO-1T-{uuid.uuid4().hex[:4]}",
            variation_type="EXTRA_ITEM_ADDITION",
            unit_of_measure="m3",
            quantity_delta=Decimal("10.0000"),
            rate_previous=Decimal("500.00"),
            rate_revised=Decimal("500.00"),
            effective_date=date(2027, 1, 15),
            status="DRAFT",
            description="Foundation depth extension",
        )
        db.add(cvo)
        db.commit()
        db.refresh(cvo)

        # Setup Project B for cross-project integrity tests
        proj_b = Project(name=f"Proj 1T B {uuid.uuid4().hex[:4]}", created_by=adm.id)
        db.add(proj_b)
        db.commit()
        db.refresh(proj_b)

        act_b = ConstructionActivity(
            project_id=proj_b.id,
            activity_code="ACT-1T-02",
            activity_name="Project B Activity",
            activity_type="CONSTRUCTION",
            created_by=adm.id,
        )
        sched_b = ConstructionSchedule(
            project_id=proj_b.id,
            schedule_version="1.0",
            calculation_status="CALCULATED",
            algorithm_version="1.0",
            input_snapshot_json={},
            calculated_by=adm.id,
        )
        db.add_all([act_b, sched_b])
        db.commit()
        db.refresh(act_b)
        db.refresh(sched_b)

        base_b = MonitoringBaseline(
            project_id=proj_b.id,
            schedule_id=sched_b.id,
            schedule_version="1.0",
            schedule_algorithm_version="1.0",
            baseline_start_date=date(2027, 1, 1),
            frozen_by=adm.id,
            status="ACTIVE",
        )
        doc_b = Document(
            project_id=proj_b.id,
            original_filename="site_instruction_b.pdf",
            storage_key="docs/site_instruction_b.pdf",
            file_size_bytes=1024,
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            mime_type="application/pdf",
            document_type="SITE_INSTRUCTION",
            uploaded_by=adm.id,
        )
        cvo_b = ContractVariationOrder(
            project_id=proj_b.id,
            variation_number=f"VO-1T-B-{uuid.uuid4().hex[:4]}",
            variation_type="EXTRA_ITEM_ADDITION",
            unit_of_measure="m3",
            quantity_delta=Decimal("5.0000"),
            rate_previous=Decimal("500.00"),
            rate_revised=Decimal("500.00"),
            effective_date=date(2027, 1, 15),
            status="DRAFT",
            description="Project B VO",
        )
        db.add_all([base_b, doc_b, cvo_b])
        db.commit()
        db.refresh(base_b)
        db.refresh(doc_b)
        db.refresh(cvo_b)

        return {
            "adm_id": adm.id,
            "sup_id": sup.id,
            "proj_id": proj.id,
            "act_id": act.id,
            "sched_id": sched.id,
            "base_id": base.id,
            "doc_id": doc.id,
            "cvo_id": cvo.id,
            "proj_b_id": proj_b.id,
            "act_b_id": act_b.id,
            "sched_b_id": sched_b.id,
            "base_b_id": base_b.id,
            "doc_b_id": doc_b.id,
            "cvo_b_id": cvo_b.id,
        }


def test_01_valid_snapshot_creation_and_defaults(setup_db_data):
    """Verify that SchedulePerformanceSnapshot can be created in DRAFT with valid defaults."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            monitoring_baseline_id=d["base_id"],
            performance_period_start=date(2027, 1, 1),
            performance_period_end=date(2027, 1, 31),
            evaluation_date=date(2027, 1, 31),
            planned_start_date=date(2027, 1, 1),
            planned_finish_date=date(2027, 1, 20),
            planned_duration_days=20,
            actual_start_date=date(2027, 1, 5),
            actual_finish_date=date(2027, 1, 28),
            actual_duration_days=24,
            planned_cumulative_progress_pct=Decimal("100.0000"),
            actual_cumulative_progress_pct=Decimal("100.0000"),
            earned_schedule_days=Decimal("20.0000"),
            actual_time_days=Decimal("24.0000"),
            schedule_variance_days=Decimal("-4.0000"),
            schedule_performance_index=Decimal("0.833333"),
            baseline_total_float_days=5,
            residual_total_float_days=1,
            is_critical_path=False,
            critical_path_impact_days=0,
            delay_status="MINOR_DELAY",
            delay_classification="EXCUSABLE_NON_COMPENSABLE",
            delay_root_cause_category="WEATHER",
            delay_justification="Heavy unseasonal rainfall prevented site access.",
            delay_evidence_document_id=d["doc_id"],
            contract_variation_id=d["cvo_id"],
            performance_status="SCHEDULE_VARIANCE_WITHIN_TOLERANCE",
            canonical_hash="hash_test_01",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap)
        db.commit()
        db.refresh(snap)

        assert snap.id is not None
        assert snap.status == "DRAFT"
        assert snap.algorithm_version == "SCHED_PERFORMANCE_1.0"
        assert snap.schedule_variance_days == Decimal("-4.0000")
        assert snap.schedule_performance_index == Decimal("0.833333")
        assert snap.is_critical_path is False
        assert snap.delay_root_cause_category == "WEATHER"


def test_02_invalid_lifecycle_status_rejected(setup_db_data):
    """Verify check constraint ck_sps_status blocks invalid status values."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            evaluation_date=date(2027, 1, 31),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_02",
            status="UNKNOWN_STATUS",  # Invalid!
            created_by=d["adm_id"],
        )
        db.add(snap)
        with pytest.raises(Exception) as excinfo:
            db.commit()
        # Either trigger blocks non-draft insert or check constraint ck_sps_status fires
        assert "ck_sps_status" in str(excinfo.value) or "must be created in DRAFT" in str(excinfo.value)
        db.rollback()


def test_03_invalid_delay_status_rejected(setup_db_data):
    """Verify check constraint ck_sps_delay_status blocks invalid delay statuses."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            evaluation_date=date(2027, 1, 31),
            delay_status="INVALID_DELAY",  # Invalid!
            performance_status="ON_TRACK",
            canonical_hash="hash_test_03",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap)
        with pytest.raises(Exception) as excinfo:
            db.commit()
        assert "ck_sps_delay_status" in str(excinfo.value)
        db.rollback()


def test_04_invalid_delay_classification_rejected(setup_db_data):
    """Verify check constraint ck_sps_delay_class blocks invalid classifications."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            evaluation_date=date(2027, 1, 31),
            delay_status="MINOR_DELAY",
            delay_classification="ILLEGAL_CLASS",  # Invalid!
            performance_status="ON_TRACK",
            canonical_hash="hash_test_04",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap)
        with pytest.raises(Exception) as excinfo:
            db.commit()
        assert "ck_sps_delay_class" in str(excinfo.value)
        db.rollback()


def test_05_invalid_performance_period_rejected(setup_db_data):
    """Verify check constraint ck_sps_period enforces period_start <= period_end."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            performance_period_start=date(2027, 2, 1),
            performance_period_end=date(2027, 1, 1),  # start > end!
            evaluation_date=date(2027, 2, 1),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_05",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap)
        with pytest.raises(Exception) as excinfo:
            db.commit()
        assert "ck_sps_period" in str(excinfo.value)
        db.rollback()


def test_06_invalid_planned_dates_rejected(setup_db_data):
    """Verify check constraint ck_sps_planned_dates enforces start <= finish."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            evaluation_date=date(2027, 1, 31),
            planned_start_date=date(2027, 1, 20),
            planned_finish_date=date(2027, 1, 10),  # start > finish!
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_06",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap)
        with pytest.raises(Exception) as excinfo:
            db.commit()
        assert "ck_sps_planned_dates" in str(excinfo.value)
        db.rollback()


def test_07_foreign_key_protection_on_delete_activity(setup_db_data):
    """Verify foreign key RESTRICT prevents deleting referenced activity."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            evaluation_date=date(2027, 1, 31),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_07",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap)
        db.commit()

        # Attempt to delete activity -> fails with FK error
        with pytest.raises(Exception):
            db.execute(text("DELETE FROM construction_activities WHERE id = :id"), {"id": d["act_id"]})
            db.commit()
        db.rollback()


def test_08_duplicate_finalized_authoritative_identity_rejected(setup_db_data):
    """Verify partial unique index uq_sps_authoritative_identity blocks two FINALIZED snapshots for same identity."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap1 = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            performance_period_start=date(2027, 3, 1),
            performance_period_end=date(2027, 3, 31),
            evaluation_date=date(2027, 3, 31),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_08_1",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap1)
        db.commit()

        # Finalize snap1
        snap1.status = "FINALIZED"
        snap1.finalized_by = d["adm_id"]
        snap1.finalized_at = datetime.now(timezone.utc)
        db.commit()

        # Insert second draft snapshot with identical (project, activity, period)
        snap2 = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            performance_period_start=date(2027, 3, 1),
            performance_period_end=date(2027, 3, 31),
            evaluation_date=date(2027, 3, 31),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_08_2",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap2)
        db.commit()

        # Attempting to finalize snap2 must violate partial unique index
        snap2.status = "FINALIZED"
        snap2.finalized_by = d["adm_id"]
        snap2.finalized_at = datetime.now(timezone.utc)
        with pytest.raises(Exception) as excinfo:
            db.commit()
        assert "uq_sps_authoritative_identity" in str(excinfo.value)
        db.rollback()


def test_09_trigger_prevents_sql_update_on_finalized(setup_db_data):
    """Verify PostgreSQL trigger blocks modifying calculation fields on a FINALIZED snapshot."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            performance_period_start=date(2027, 4, 1),
            performance_period_end=date(2027, 4, 30),
            evaluation_date=date(2027, 4, 30),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_09",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap)
        db.commit()

        snap.status = "FINALIZED"
        snap.finalized_by = d["adm_id"]
        snap.finalized_at = datetime.now(timezone.utc)
        db.commit()
        snap_id = snap.id

        # Attempt to modify earned_schedule_days -> fails via trigger
        with pytest.raises(Exception) as excinfo:
            db.execute(text("UPDATE schedule_performance_snapshots SET earned_schedule_days = 99.0 WHERE id = :id"), {"id": snap_id})
            db.commit()
        assert "immutable" in str(excinfo.value).lower()
        db.rollback()


def test_10_trigger_prevents_sql_delete_on_finalized(setup_db_data):
    """Verify PostgreSQL trigger blocks SQL DELETE on a FINALIZED snapshot."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            performance_period_start=date(2027, 5, 1),
            performance_period_end=date(2027, 5, 31),
            evaluation_date=date(2027, 5, 31),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_10",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap)
        db.commit()

        snap.status = "FINALIZED"
        snap.finalized_by = d["adm_id"]
        snap.finalized_at = datetime.now(timezone.utc)
        db.commit()
        snap_id = snap.id

        # Attempt to delete -> fails via trigger
        with pytest.raises(Exception) as excinfo:
            db.execute(text("DELETE FROM schedule_performance_snapshots WHERE id = :id"), {"id": snap_id})
            db.commit()
        assert "immutable" in str(excinfo.value).lower()
        db.rollback()


def test_11_trigger_blocks_draft_to_superseded_direct_transition(setup_db_data):
    """Verify trigger blocks transitioning a DRAFT directly to SUPERSEDED."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            evaluation_date=date(2027, 6, 30),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_11",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap)
        db.commit()
        db.refresh(snap)
        snap_id = snap.id

        # Attempt draft -> superseded directly -> fails via trigger
        with pytest.raises(Exception) as excinfo:
            db.execute(text("UPDATE schedule_performance_snapshots SET status = 'SUPERSEDED' WHERE id = :id"), {"id": snap_id})
            db.commit()
        assert "draft records cannot be directly superseded" in str(excinfo.value).lower()
        db.rollback()


def test_12_draft_mutation_allowed(setup_db_data):
    """Verify that a DRAFT snapshot CAN be edited and updated prior to finalization."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            evaluation_date=date(2027, 7, 31),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_12_orig",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap)
        db.commit()
        db.refresh(snap)
        snap_id = snap.id

        # Modify fields in draft -> succeeds
        snap.schedule_variance_days = Decimal("2.5000")
        snap.delay_status = "AHEAD_OF_SCHEDULE"
        db.commit()
        db.refresh(snap)

        assert snap.schedule_variance_days == Decimal("2.5000")
        assert snap.delay_status == "AHEAD_OF_SCHEDULE"


def test_13_canonical_hash_determinism_and_sensitivity():
    """Verify that canonical SHA-256 hash is deterministic and sensitive to input variation."""
    payload_a = {
        "project_id": "proj-1",
        "activity_id": "act-1",
        "evaluation_date": "2027-01-31",
        "earned_schedule_days": "20.0000",
        "actual_time_days": "24.0000",
    }
    payload_b = {
        "actual_time_days": "24.0000",
        "earned_schedule_days": "20.0000",
        "evaluation_date": "2027-01-31",
        "activity_id": "act-1",
        "project_id": "proj-1",
    }
    payload_c = {
        "project_id": "proj-1",
        "activity_id": "act-1",
        "evaluation_date": "2027-01-31",
        "earned_schedule_days": "21.0000", # Modified
        "actual_time_days": "24.0000",
    }

    hash_a = generate_schedule_performance_canonical_hash(payload_a)
    hash_b = generate_schedule_performance_canonical_hash(payload_b)
    hash_c = generate_schedule_performance_canonical_hash(payload_c)

    # Identical content with different key ordering must yield identical hash
    assert hash_a == hash_b
    assert len(hash_a) == 64
    # Modified value must yield different hash
    assert hash_a != hash_c


def test_14_direct_insert_finalized_rejected(setup_db_data):
    """Verify fn_protect_schedule_performance_snapshot blocks direct SQL INSERT with status='FINALIZED'."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            evaluation_date=date(2027, 8, 1),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_14",
            status="FINALIZED",
            created_by=d["adm_id"],
            finalized_by=d["adm_id"],
            finalized_at=datetime.now(timezone.utc),
        )
        db.add(snap)
        with pytest.raises(Exception) as excinfo:
            db.commit()
        assert "must be created in DRAFT status" in str(excinfo.value)
        db.rollback()


def test_15_direct_insert_superseded_rejected(setup_db_data):
    """Verify fn_protect_schedule_performance_snapshot blocks direct SQL INSERT with status='SUPERSEDED'."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            evaluation_date=date(2027, 8, 2),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_15",
            status="SUPERSEDED",
            created_by=d["adm_id"],
            finalized_by=d["adm_id"],
            finalized_at=datetime.now(timezone.utc),
            superseded_by_user_id=d["adm_id"],
            superseded_at=datetime.now(timezone.utc),
            supersession_reason="Testing direct insert rejection",
        )
        db.add(snap)
        with pytest.raises(Exception) as excinfo:
            db.commit()
        assert "must be created in DRAFT status" in str(excinfo.value)
        db.rollback()


def test_16_finalization_missing_metadata_rejected(setup_db_data):
    """Verify ck_sps_lifecycle_metadata requires finalized_by and finalized_at when transitioning to FINALIZED."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            performance_period_start=date(2027, 8, 3),
            performance_period_end=date(2027, 8, 3),
            evaluation_date=date(2027, 8, 3),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_16",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap)
        db.commit()

        # Attempt to transition to FINALIZED without finalized_by / finalized_at
        snap.status = "FINALIZED"
        with pytest.raises(Exception) as excinfo:
            db.commit()
        assert "ck_sps_lifecycle_metadata" in str(excinfo.value)
        db.rollback()


def test_17_supersession_missing_metadata_rejected(setup_db_data):
    """Verify ck_sps_lifecycle_metadata and trigger require full supersession metadata when transitioning to SUPERSEDED."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        # Create and finalize snap1
        snap1 = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            performance_period_start=date(2027, 8, 4),
            performance_period_end=date(2027, 8, 4),
            evaluation_date=date(2027, 8, 4),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_17_1",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap1)
        db.commit()

        snap1.status = "FINALIZED"
        snap1.finalized_by = d["adm_id"]
        snap1.finalized_at = datetime.now(timezone.utc)
        db.commit()

        # Create replacement snapshot snap2
        snap2 = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            performance_period_start=date(2027, 8, 4),
            performance_period_end=date(2027, 8, 4),
            evaluation_date=date(2027, 8, 4),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_17_2",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap2)
        db.commit()

        # Attempt to supersede snap1 without supersession_reason
        snap1.status = "SUPERSEDED"
        snap1.superseded_by = snap2.id
        snap1.superseded_by_user_id = d["adm_id"]
        snap1.superseded_at = datetime.now(timezone.utc)
        snap1.supersession_reason = None  # Missing!
        with pytest.raises(Exception) as excinfo:
            db.commit()
        assert "ck_sps_lifecycle_metadata" in str(excinfo.value) or "supersession_reason" in str(excinfo.value)
        db.rollback()


def test_18_cross_project_activity_rejected(setup_db_data):
    """Verify trg_validate_sps_project_integrity rejects snapshot referencing activity from another project."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_b_id"],  # Activity belongs to proj_b!
            schedule_id=d["sched_id"],
            evaluation_date=date(2027, 8, 5),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_18",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap)
        with pytest.raises(Exception) as excinfo:
            db.commit()
        assert "not snapshot project" in str(excinfo.value) and "activity" in str(excinfo.value)
        db.rollback()


def test_19_cross_project_schedule_rejected(setup_db_data):
    """Verify trg_validate_sps_project_integrity rejects snapshot referencing schedule from another project."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_b_id"],  # Schedule belongs to proj_b!
            evaluation_date=date(2027, 8, 6),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_19",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap)
        with pytest.raises(Exception) as excinfo:
            db.commit()
        assert "not snapshot project" in str(excinfo.value) and "schedule" in str(excinfo.value)
        db.rollback()


def test_20_cross_project_baseline_rejected(setup_db_data):
    """Verify trg_validate_sps_project_integrity rejects snapshot referencing monitoring baseline from another project."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            monitoring_baseline_id=d["base_b_id"],  # Baseline belongs to proj_b!
            evaluation_date=date(2027, 8, 7),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_20",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap)
        with pytest.raises(Exception) as excinfo:
            db.commit()
        assert "not snapshot project" in str(excinfo.value) and "baseline" in str(excinfo.value)
        db.rollback()


def test_21_cross_project_document_rejected(setup_db_data):
    """Verify trg_validate_sps_project_integrity rejects snapshot referencing document from another project."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            delay_evidence_document_id=d["doc_b_id"],  # Document belongs to proj_b!
            evaluation_date=date(2027, 8, 8),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_21",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap)
        with pytest.raises(Exception) as excinfo:
            db.commit()
        assert "not snapshot project" in str(excinfo.value) and "evidence document" in str(excinfo.value)
        db.rollback()


def test_22_cross_project_variation_rejected(setup_db_data):
    """Verify trg_validate_sps_project_integrity rejects snapshot referencing variation order from another project."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            contract_variation_id=d["cvo_b_id"],  # Variation belongs to proj_b!
            evaluation_date=date(2027, 8, 9),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_22",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap)
        with pytest.raises(Exception) as excinfo:
            db.commit()
        assert "not snapshot project" in str(excinfo.value) and "contract variation" in str(excinfo.value)
        db.rollback()


def test_23_cross_project_replacement_rejected(setup_db_data):
    """Verify trg_validate_sps_project_integrity rejects superseding with a snapshot from another project."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        # Create finalized snapshot in proj
        snap_a = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            performance_period_start=date(2027, 8, 10),
            performance_period_end=date(2027, 8, 10),
            evaluation_date=date(2027, 8, 10),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_23_a",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        # Create draft snapshot in proj_b
        snap_b = SchedulePerformanceSnapshot(
            project_id=d["proj_b_id"],
            activity_id=d["act_b_id"],
            schedule_id=d["sched_b_id"],
            performance_period_start=date(2027, 8, 10),
            performance_period_end=date(2027, 8, 10),
            evaluation_date=date(2027, 8, 10),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_23_b",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add_all([snap_a, snap_b])
        db.commit()

        snap_a.status = "FINALIZED"
        snap_a.finalized_by = d["adm_id"]
        snap_a.finalized_at = datetime.now(timezone.utc)
        db.commit()

        # Attempt to supersede snap_a using snap_b from different project
        snap_a.status = "SUPERSEDED"
        snap_a.superseded_by = snap_b.id
        snap_a.superseded_by_user_id = d["adm_id"]
        snap_a.superseded_at = datetime.now(timezone.utc)
        snap_a.supersession_reason = "Cross project supersession attempt"
        with pytest.raises(Exception) as excinfo:
            db.commit()
        assert "Replacement snapshot" in str(excinfo.value) and "expected snapshot project" in str(excinfo.value)
        db.rollback()


def test_24_delete_evidence_document_blocked_when_referenced(setup_db_data):
    """Verify ON DELETE RESTRICT on delay_evidence_document_id prevents deleting referenced document."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        # Create unique document for this test
        doc = Document(
            project_id=d["proj_id"],
            original_filename="audit_evidence.pdf",
            storage_key=f"docs/audit_evidence_{uuid.uuid4().hex[:6]}.pdf",
            file_size_bytes=2048,
            sha256_hash="f" * 64,
            mime_type="application/pdf",
            document_type="DELAY_NOTICE",
            uploaded_by=d["adm_id"],
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        snap = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            delay_evidence_document_id=doc.id,
            evaluation_date=date(2027, 8, 11),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_24",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap)
        db.commit()

        # Attempt to delete document -> blocked by foreign key ON DELETE RESTRICT
        with pytest.raises(Exception) as excinfo:
            db.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc.id})
            db.commit()
        assert "foreign key" in str(excinfo.value).lower() or "violates foreign key constraint" in str(excinfo.value).lower()
        db.rollback()


def test_25_null_period_authoritative_uniqueness(setup_db_data):
    """Verify partial unique index uq_sps_authoritative_identity_null_period prevents duplicate finalized snapshots with null periods."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        # Create a dedicated activity to isolate null period uniqueness testing
        act_null = ConstructionActivity(
            project_id=d["proj_id"],
            activity_code=f"ACT-NULL-{uuid.uuid4().hex[:4]}",
            activity_name="Null Period Activity",
            activity_type="CONSTRUCTION",
            created_by=d["adm_id"],
        )
        db.add(act_null)
        db.commit()
        db.refresh(act_null)

        # Snapshot 1 with null period
        snap1 = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=act_null.id,
            schedule_id=d["sched_id"],
            performance_period_start=None,
            performance_period_end=None,
            evaluation_date=date(2027, 8, 12),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_25_1",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap1)
        db.commit()

        snap1.status = "FINALIZED"
        snap1.finalized_by = d["adm_id"]
        snap1.finalized_at = datetime.now(timezone.utc)
        db.commit()

        # Snapshot 2 with null period for same (project_id, activity_id)
        snap2 = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=act_null.id,
            schedule_id=d["sched_id"],
            performance_period_start=None,
            performance_period_end=None,
            evaluation_date=date(2027, 8, 12),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_25_2",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap2)
        db.commit()

        snap2.status = "FINALIZED"
        snap2.finalized_by = d["adm_id"]
        snap2.finalized_at = datetime.now(timezone.utc)
        with pytest.raises(Exception) as excinfo:
            db.commit()
        assert "uq_sps_authoritative_identity_null_period" in str(excinfo.value)
        db.rollback()


def test_26_valid_supersession_transition_flow(setup_db_data):
    """Verify that a valid FINALIZED snapshot can be superseded by a valid replacement snapshot."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap_orig = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            performance_period_start=date(2027, 9, 1),
            performance_period_end=date(2027, 9, 30),
            evaluation_date=date(2027, 9, 30),
            delay_status="MINOR_DELAY",
            performance_status="ON_TRACK",
            canonical_hash="hash_test_26_orig",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap_orig)
        db.commit()

        snap_orig.status = "FINALIZED"
        snap_orig.finalized_by = d["adm_id"]
        snap_orig.finalized_at = datetime.now(timezone.utc)
        db.commit()
        orig_id = snap_orig.id

        # Create replacement snapshot
        snap_repl = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            performance_period_start=date(2027, 9, 1),
            performance_period_end=date(2027, 9, 30),
            evaluation_date=date(2027, 9, 30),
            delay_status="CRITICAL_DELAY",
            performance_status="CRITICAL_DELAY",
            canonical_hash="hash_test_26_repl",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap_repl)
        db.commit()

        # Supersede original
        snap_orig.status = "SUPERSEDED"
        snap_orig.superseded_by = snap_repl.id
        snap_orig.superseded_by_user_id = d["adm_id"]
        snap_orig.superseded_at = datetime.now(timezone.utc)
        snap_orig.supersession_reason = "Updated baseline float recalculated"
        db.commit()

        # Now snap_repl can be finalized without violating partial unique index because snap_orig is SUPERSEDED!
        snap_repl.status = "FINALIZED"
        snap_repl.finalized_by = d["adm_id"]
        snap_repl.finalized_at = datetime.now(timezone.utc)
        db.commit()

        db.refresh(snap_orig)
        db.refresh(snap_repl)
        assert snap_orig.status == "SUPERSEDED"
        assert snap_orig.superseded_by == snap_repl.id
        assert snap_repl.status == "FINALIZED"


def test_27_db_immutability_blocks_sql_tampering(setup_db_data):
    """Verify database trigger fn_protect_schedule_performance_snapshot blocks modifying any calculation or hash field on FINALIZED snapshot."""
    d = setup_db_data
    with TestingSessionLocal() as db:
        snap = SchedulePerformanceSnapshot(
            project_id=d["proj_id"],
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            performance_period_start=date(2027, 10, 1),
            performance_period_end=date(2027, 10, 31),
            evaluation_date=date(2027, 10, 31),
            earned_schedule_days=Decimal("20.0000"),
            actual_time_days=Decimal("20.0000"),
            schedule_variance_days=Decimal("0.0000"),
            delay_status="ON_SCHEDULE",
            performance_status="ON_TRACK",
            canonical_hash="orig_hash_test_27",
            status="DRAFT",
            created_by=d["adm_id"],
        )
        db.add(snap)
        db.commit()

        snap.status = "FINALIZED"
        snap.finalized_by = d["adm_id"]
        snap.finalized_at = datetime.now(timezone.utc)
        db.commit()
        snap_id = snap.id

        # 1. Attempt direct SQL update of earned_schedule_days -> blocked by trigger
        with pytest.raises(Exception) as exc1:
            db.execute(text("UPDATE schedule_performance_snapshots SET earned_schedule_days = 25.0 WHERE id = :id"), {"id": snap_id})
            db.commit()
        assert "immutable" in str(exc1.value).lower()
        db.rollback()

        # 2. Attempt direct SQL update of canonical_hash -> blocked by trigger
        with pytest.raises(Exception) as exc2:
            db.execute(text("UPDATE schedule_performance_snapshots SET canonical_hash = 'tampered_hash' WHERE id = :id"), {"id": snap_id})
            db.commit()
        assert "immutable" in str(exc2.value).lower()
        db.rollback()


def test_28_independent_hash_verification_detects_tampered_payload(setup_db_data):
    """Verify that a real persisted snapshot's canonical_hash matches independent payload reconstruction, and that altering a hash-covered field in-memory breaks the digest match."""
    from app.services.schedule_performance_service import (
        create_schedule_performance_snapshot,
        generate_schedule_performance_canonical_hash,
    )
    from app.schemas.schedule_performance import SchedulePerformanceCreateRequest

    d = setup_db_data
    with TestingSessionLocal() as db:
        adm = db.query(User).filter(User.id == d["adm_id"]).first()

        # 1. Create a real snapshot persisted to PostgreSQL via service
        req = SchedulePerformanceCreateRequest(
            activity_id=d["act_id"],
            schedule_id=d["sched_id"],
            monitoring_baseline_id=d["base_id"],
            performance_period_start=date(2027, 11, 1),
            performance_period_end=date(2027, 11, 30),
            evaluation_date=date(2027, 11, 30),
            actual_start_date=date(2027, 11, 1),
            actual_cumulative_progress_pct=Decimal("80.0000"),
            override_reason="Hash audit verification snapshot",
        )
        created_snap = create_schedule_performance_snapshot(db, d["proj_id"], req, adm)
        snap_id = created_snap.id
        stored_hash = created_snap.canonical_hash

        # 2. Reload the real persisted snapshot in a fresh query
        persisted_snap = db.query(SchedulePerformanceSnapshot).filter(SchedulePerformanceSnapshot.id == snap_id).first()
        assert persisted_snap is not None
        assert persisted_snap.canonical_hash == stored_hash

        # 3. Independently reconstruct canonical payload from persisted database columns
        reconstructed_payload = {
            "project_id": persisted_snap.project_id,
            "activity_id": persisted_snap.activity_id,
            "schedule_id": persisted_snap.schedule_id,
            "monitoring_baseline_id": persisted_snap.monitoring_baseline_id,
            "performance_period_start": str(persisted_snap.performance_period_start) if persisted_snap.performance_period_start else None,
            "performance_period_end": str(persisted_snap.performance_period_end) if persisted_snap.performance_period_end else None,
            "evaluation_date": str(persisted_snap.evaluation_date),
            "planned_start_date": str(persisted_snap.planned_start_date) if persisted_snap.planned_start_date else None,
            "planned_finish_date": str(persisted_snap.planned_finish_date) if persisted_snap.planned_finish_date else None,
            "planned_duration_days": persisted_snap.planned_duration_days,
            "actual_start_date": str(persisted_snap.actual_start_date) if persisted_snap.actual_start_date else None,
            "actual_finish_date": str(persisted_snap.actual_finish_date) if persisted_snap.actual_finish_date else None,
            "actual_duration_days": persisted_snap.actual_duration_days,
            "planned_cumulative_progress_pct": str(persisted_snap.planned_cumulative_progress_pct) if persisted_snap.planned_cumulative_progress_pct is not None else None,
            "actual_cumulative_progress_pct": str(persisted_snap.actual_cumulative_progress_pct) if persisted_snap.actual_cumulative_progress_pct is not None else None,
            "actual_time_days": str(persisted_snap.actual_time_days) if persisted_snap.actual_time_days is not None else None,
            "earned_schedule_days": str(persisted_snap.earned_schedule_days) if persisted_snap.earned_schedule_days is not None else None,
            "schedule_variance_days": str(persisted_snap.schedule_variance_days) if persisted_snap.schedule_variance_days is not None else None,
            "schedule_performance_index": str(persisted_snap.schedule_performance_index) if persisted_snap.schedule_performance_index is not None else None,
            "baseline_total_float_days": persisted_snap.baseline_total_float_days,
            "residual_total_float_days": persisted_snap.residual_total_float_days,
            "is_critical_path": persisted_snap.is_critical_path,
            "critical_path_impact_days": persisted_snap.critical_path_impact_days,
            "delay_status": persisted_snap.delay_status,
            "supervisor_assessed_delay_status": persisted_snap.input_snapshot_json.get("supervisor_assessed_delay_status"),
            "performance_status": persisted_snap.performance_status,
            "delay_classification": persisted_snap.delay_classification,
            "delay_root_cause_category": persisted_snap.delay_root_cause_category,
            "delay_justification": persisted_snap.delay_justification,
            "delay_evidence_document_id": persisted_snap.delay_evidence_document_id,
            "contract_variation_id": persisted_snap.contract_variation_id,
            "progress_provenance": persisted_snap.provenance_metadata.get("progress_provenance"),
            "algorithm_version": persisted_snap.algorithm_version,
        }

        # 4. Confirm independently reconstructed digest matches stored digest
        recomputed_hash = generate_schedule_performance_canonical_hash(reconstructed_payload)
        assert recomputed_hash == stored_hash, f"Recomputed hash {recomputed_hash} did not match stored {stored_hash}"

        # 5. In a separate in-memory payload, alter a hash-covered field and confirm the digest no longer matches
        tampered_in_memory_payload = dict(reconstructed_payload)
        tampered_in_memory_payload["earned_schedule_days"] = "99.0000"
        altered_digest = generate_schedule_performance_canonical_hash(tampered_in_memory_payload)
        assert altered_digest != stored_hash

        tampered_in_memory_payload_2 = dict(reconstructed_payload)
        tampered_in_memory_payload_2["delay_status"] = "AHEAD_OF_SCHEDULE"
        altered_digest_2 = generate_schedule_performance_canonical_hash(tampered_in_memory_payload_2)
        assert altered_digest_2 != stored_hash




