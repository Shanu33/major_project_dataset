"""phase_1i_hardening_site_monitoring

Revision ID: b2c3d4e5f6a7
Revises: e1a9b2c3d4f5
Create Date: 2026-10-04 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'e1a9b2c3d4f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Phase 1I Hardening Pass."""
    # 1. Add schedule_algorithm_version to monitoring_baselines
    op.add_column('monitoring_baselines', sa.Column('schedule_algorithm_version', sa.String(50), nullable=True))
    
    # Backfill schedule_algorithm_version from referenced construction_schedules
    op.execute("""
        UPDATE monitoring_baselines mb
        SET schedule_algorithm_version = COALESCE(cs.algorithm_version, 'CPM_1.0')
        FROM construction_schedules cs
        WHERE mb.schedule_id = cs.id;
    """)
    op.execute("""
        UPDATE monitoring_baselines
        SET schedule_algorithm_version = 'CPM_1.0'
        WHERE schedule_algorithm_version IS NULL;
    """)
    op.alter_column('monitoring_baselines', 'schedule_algorithm_version', nullable=False)

    # 2. Add CHECK constraints for status / lifecycle integrity
    # Monitoring baseline valid statuses
    op.create_check_constraint(
        'ck_monitoring_baseline_status',
        'monitoring_baselines',
        "status IN ('ACTIVE', 'SUPERSEDED', 'REJECTED')"
    )

    # Daily progress report valid statuses
    op.create_check_constraint(
        'ck_daily_progress_report_status',
        'daily_progress_reports',
        "submission_status IN ('DRAFT', 'SUBMITTED', 'FINALIZED')"
    )

    # Daily activity progress valid contractor statuses
    op.create_check_constraint(
        'ck_daily_act_prog_status',
        'daily_activity_progress',
        "contractor_status IN ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'ON_HOLD')"
    )

    # Daily activity progress unit requirement
    op.create_check_constraint(
        'ck_contractor_progress_unit_required',
        'daily_activity_progress',
        "contractor_progress_value IS NULL OR (contractor_progress_unit IS NOT NULL AND length(trim(contractor_progress_unit)) > 0)"
    )

    # Daily activity progress date ordering
    op.create_check_constraint(
        'ck_contractor_actual_dates',
        'daily_activity_progress',
        "contractor_actual_start IS NULL OR contractor_actual_finish IS NULL OR contractor_actual_finish >= contractor_actual_start"
    )

    # Daily activity progress verification valid statuses
    op.create_check_constraint(
        'ck_verification_status',
        'daily_activity_progress_verifications',
        "verification_status IN ('PENDING', 'VERIFIED', 'CORRECTED', 'REJECTED')"
    )

    # Verification unit requirement
    op.create_check_constraint(
        'ck_verified_quantity_unit_required',
        'daily_activity_progress_verifications',
        "verified_quantity IS NULL OR (verified_quantity_unit IS NOT NULL AND length(trim(verified_quantity_unit)) > 0)"
    )

    # Verification date ordering
    op.create_check_constraint(
        'ck_verified_actual_dates',
        'daily_activity_progress_verifications',
        "verified_actual_start IS NULL OR verified_actual_finish IS NULL OR verified_actual_finish >= verified_actual_start"
    )

    # 3. Harden PostgreSQL triggers
    # Trigger A: Harden Monitoring Baseline Immutability (protect schedule_algorithm_version)
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_protect_monitoring_baseline()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Monitoring baselines are historical and cannot be deleted.';
            ELSIF TG_OP = 'UPDATE' THEN
                IF OLD.id <> NEW.id OR
                   OLD.project_id <> NEW.project_id OR
                   OLD.schedule_id <> NEW.schedule_id OR
                   OLD.schedule_version <> NEW.schedule_version OR
                   OLD.schedule_algorithm_version <> NEW.schedule_algorithm_version OR
                   OLD.frozen_by <> NEW.frozen_by OR
                   OLD.frozen_at <> NEW.frozen_at THEN
                    RAISE EXCEPTION 'Monitoring baseline historical attributes cannot be modified.';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Trigger B: Harden Daily Progress Report Lifecycle transitions
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_protect_daily_progress_report()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF OLD.submission_status = 'FINALIZED' THEN
                    RAISE EXCEPTION 'Finalized daily progress reports are immutable and cannot be deleted.';
                END IF;
            ELSIF TG_OP = 'UPDATE' THEN
                IF OLD.submission_status = 'FINALIZED' THEN
                    RAISE EXCEPTION 'Finalized daily progress reports are immutable and cannot be updated.';
                ELSIF OLD.submission_status = 'SUBMITTED' AND NEW.submission_status = 'DRAFT' THEN
                    RAISE EXCEPTION 'Cannot transition daily report from SUBMITTED back to DRAFT.';
                ELSIF OLD.submission_status = 'SUBMITTED' AND NEW.submission_status NOT IN ('SUBMITTED', 'FINALIZED') THEN
                    RAISE EXCEPTION 'Invalid status transition from SUBMITTED.';
                ELSIF OLD.submission_status = 'DRAFT' AND NEW.submission_status NOT IN ('DRAFT', 'SUBMITTED') THEN
                    RAISE EXCEPTION 'Invalid status transition from DRAFT.';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """Downgrade schema - Revert Phase 1I Hardening Pass."""
    # Revert trigger functions
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_protect_monitoring_baseline()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Monitoring baselines are historical and cannot be deleted.';
            ELSIF TG_OP = 'UPDATE' THEN
                IF OLD.id <> NEW.id OR
                   OLD.project_id <> NEW.project_id OR
                   OLD.schedule_id <> NEW.schedule_id OR
                   OLD.schedule_version <> NEW.schedule_version OR
                   OLD.frozen_by <> NEW.frozen_by OR
                   OLD.frozen_at <> NEW.frozen_at THEN
                    RAISE EXCEPTION 'Monitoring baseline historical attributes cannot be modified.';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION trg_protect_daily_progress_report()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF OLD.submission_status = 'FINALIZED' THEN
                    RAISE EXCEPTION 'Finalized daily progress reports are immutable and cannot be deleted.';
                END IF;
            ELSIF TG_OP = 'UPDATE' THEN
                IF OLD.submission_status = 'FINALIZED' THEN
                    RAISE EXCEPTION 'Finalized daily progress reports are immutable and cannot be updated.';
                ELSIF OLD.submission_status = 'SUBMITTED' AND NEW.submission_status = 'DRAFT' THEN
                    RAISE EXCEPTION 'Cannot transition daily report from SUBMITTED back to DRAFT.';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Drop constraints
    op.drop_constraint('ck_verified_actual_dates', 'daily_activity_progress_verifications', type_='check')
    op.drop_constraint('ck_verified_quantity_unit_required', 'daily_activity_progress_verifications', type_='check')
    op.drop_constraint('ck_verification_status', 'daily_activity_progress_verifications', type_='check')
    op.drop_constraint('ck_contractor_actual_dates', 'daily_activity_progress', type_='check')
    op.drop_constraint('ck_contractor_progress_unit_required', 'daily_activity_progress', type_='check')
    op.drop_constraint('ck_daily_act_prog_status', 'daily_activity_progress', type_='check')
    op.drop_constraint('ck_daily_progress_report_status', 'daily_progress_reports', type_='check')
    op.drop_constraint('ck_monitoring_baseline_status', 'monitoring_baselines', type_='check')

    # Drop column
    op.drop_column('monitoring_baselines', 'schedule_algorithm_version')
