"""phase_1i_site_monitoring_foundation

Revision ID: e1a9b2c3d4f5
Revises: c7b1a4d8e2f3
Create Date: 2026-10-04 22:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1a9b2c3d4f5'
down_revision: Union[str, Sequence[str], None] = 'c7b1a4d8e2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Phase 1I: Daily Site Progress Monitoring & Activity Progress Tracking Foundation."""
    # 1. Create monitoring_baselines table
    op.create_table(
        'monitoring_baselines',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('schedule_id', sa.String(), sa.ForeignKey('construction_schedules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('schedule_version', sa.String(), nullable=False),
        sa.Column('frozen_by', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('frozen_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='ACTIVE'),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )
    op.create_index('ix_monitoring_baselines_project', 'monitoring_baselines', ['project_id'])
    op.create_index('ix_monitoring_baselines_schedule', 'monitoring_baselines', ['schedule_id'])
    op.create_index('ix_monitoring_baselines_status', 'monitoring_baselines', ['status'])

    # 2. Create daily_progress_reports table
    op.create_table(
        'daily_progress_reports',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('report_date', sa.Date(), nullable=False),
        sa.Column('submitted_by', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('submission_status', sa.String(), nullable=False, server_default='DRAFT'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )
    op.create_index('ix_daily_progress_reports_project', 'daily_progress_reports', ['project_id'])
    op.create_index('ix_daily_progress_reports_date', 'daily_progress_reports', ['report_date'])
    op.create_index('ix_daily_progress_reports_status', 'daily_progress_reports', ['submission_status'])
    op.create_index(
        'uq_finalized_daily_report_date',
        'daily_progress_reports',
        ['project_id', 'report_date'],
        unique=True,
        postgresql_where=sa.text("submission_status = 'FINALIZED'")
    )

    # 3. Create daily_activity_progress table
    op.create_table(
        'daily_activity_progress',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('daily_report_id', sa.String(), sa.ForeignKey('daily_progress_reports.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('activity_id', sa.String(), sa.ForeignKey('construction_activities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scheduled_activity_reference', sa.String(), nullable=True),
        sa.Column('contractor_progress_value', sa.Numeric(18, 6), nullable=True),
        sa.Column('contractor_progress_unit', sa.String(), nullable=True),
        sa.Column('contractor_percent_complete', sa.Numeric(5, 2), nullable=True),
        sa.Column('contractor_actual_start', sa.Date(), nullable=True),
        sa.Column('contractor_actual_finish', sa.Date(), nullable=True),
        sa.Column('contractor_remaining_duration', sa.Numeric(18, 6), nullable=True),
        sa.Column('contractor_status', sa.String(), nullable=False, server_default='NOT_STARTED'),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.CheckConstraint('contractor_progress_value IS NULL OR contractor_progress_value >= 0', name='ck_contractor_progress_nonneg'),
        sa.CheckConstraint('contractor_percent_complete IS NULL OR (contractor_percent_complete >= 0 AND contractor_percent_complete <= 100)', name='ck_contractor_percent_range'),
        sa.CheckConstraint('contractor_remaining_duration IS NULL OR contractor_remaining_duration >= 0', name='ck_contractor_remaining_dur_nonneg')
    )
    op.create_index('ix_daily_act_prog_report', 'daily_activity_progress', ['daily_report_id'])
    op.create_index('ix_daily_act_prog_activity', 'daily_activity_progress', ['activity_id'])
    op.create_index('ix_daily_act_prog_project', 'daily_activity_progress', ['project_id'])

    # 4. Create daily_activity_progress_verifications table
    op.create_table(
        'daily_activity_progress_verifications',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('daily_activity_progress_id', sa.String(), sa.ForeignKey('daily_activity_progress.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('verification_status', sa.String(), nullable=False),
        sa.Column('verified_quantity', sa.Numeric(18, 6), nullable=True),
        sa.Column('verified_quantity_unit', sa.String(), nullable=True),
        sa.Column('verified_percent_complete', sa.Numeric(5, 2), nullable=True),
        sa.Column('verified_actual_start', sa.Date(), nullable=True),
        sa.Column('verified_actual_finish', sa.Date(), nullable=True),
        sa.Column('verified_remaining_duration', sa.Numeric(18, 6), nullable=True),
        sa.Column('verified_status', sa.String(), nullable=True),
        sa.Column('verification_note', sa.Text(), nullable=True),
        sa.Column('verified_by', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.CheckConstraint('verified_quantity IS NULL OR verified_quantity >= 0', name='ck_verified_quantity_nonneg'),
        sa.CheckConstraint('verified_percent_complete IS NULL OR (verified_percent_complete >= 0 AND verified_percent_complete <= 100)', name='ck_verified_percent_range'),
        sa.CheckConstraint('verified_remaining_duration IS NULL OR verified_remaining_duration >= 0', name='ck_verified_remaining_dur_nonneg')
    )
    op.create_index('ix_verifications_progress', 'daily_activity_progress_verifications', ['daily_activity_progress_id'])
    op.create_index('ix_verifications_project', 'daily_activity_progress_verifications', ['project_id'])
    op.create_index('ix_verifications_status', 'daily_activity_progress_verifications', ['verification_status'])

    # 5. Database triggers for immutability and lifecycle protection

    # Trigger A: Protect Daily Progress Reports
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
    op.execute("""
        CREATE TRIGGER protect_daily_progress_report_trg
        BEFORE UPDATE OR DELETE ON daily_progress_reports
        FOR EACH ROW
        EXECUTE FUNCTION trg_protect_daily_progress_report();
    """)

    # Trigger B: Protect Daily Activity Progress under Finalized Reports
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_protect_daily_activity_progress()
        RETURNS TRIGGER AS $$
        DECLARE
            parent_status text;
        BEGIN
            IF TG_OP = 'DELETE' THEN
                SELECT submission_status INTO parent_status FROM daily_progress_reports WHERE id = OLD.daily_report_id;
                IF parent_status = 'FINALIZED' THEN
                    RAISE EXCEPTION 'Cannot delete activity progress of a finalized daily report.';
                END IF;
                RETURN OLD;
            ELSIF TG_OP = 'UPDATE' THEN
                SELECT submission_status INTO parent_status FROM daily_progress_reports WHERE id = OLD.daily_report_id;
                IF parent_status = 'FINALIZED' THEN
                    RAISE EXCEPTION 'Cannot update activity progress of a finalized daily report.';
                END IF;
                RETURN NEW;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER protect_daily_activity_progress_trg
        BEFORE UPDATE OR DELETE ON daily_activity_progress
        FOR EACH ROW
        EXECUTE FUNCTION trg_protect_daily_activity_progress();
    """)

    # Trigger C: Protect Supervisor Verifications (Append-only & Immutable)
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_protect_daily_activity_progress_verifications()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Supervisor verifications are append-only and cannot be deleted.';
            ELSIF TG_OP = 'UPDATE' THEN
                RAISE EXCEPTION 'Supervisor verifications are append-only and cannot be updated.';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER protect_daily_activity_progress_verifications_trg
        BEFORE UPDATE OR DELETE ON daily_activity_progress_verifications
        FOR EACH ROW
        EXECUTE FUNCTION trg_protect_daily_activity_progress_verifications();
    """)

    # Trigger D: Protect Monitoring Baselines
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
        CREATE TRIGGER protect_monitoring_baseline_trg
        BEFORE UPDATE OR DELETE ON monitoring_baselines
        FOR EACH ROW
        EXECUTE FUNCTION trg_protect_monitoring_baseline();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS protect_monitoring_baseline_trg ON monitoring_baselines;")
    op.execute("DROP FUNCTION IF EXISTS trg_protect_monitoring_baseline();")
    op.execute("DROP TRIGGER IF EXISTS protect_daily_activity_progress_verifications_trg ON daily_activity_progress_verifications;")
    op.execute("DROP FUNCTION IF EXISTS trg_protect_daily_activity_progress_verifications();")
    op.execute("DROP TRIGGER IF EXISTS protect_daily_activity_progress_trg ON daily_activity_progress;")
    op.execute("DROP FUNCTION IF EXISTS trg_protect_daily_activity_progress();")
    op.execute("DROP TRIGGER IF EXISTS protect_daily_progress_report_trg ON daily_progress_reports;")
    op.execute("DROP FUNCTION IF EXISTS trg_protect_daily_progress_report();")

    op.drop_table('daily_activity_progress_verifications')
    op.drop_table('daily_activity_progress')
    op.drop_table('daily_progress_reports')
    op.drop_table('monitoring_baselines')
