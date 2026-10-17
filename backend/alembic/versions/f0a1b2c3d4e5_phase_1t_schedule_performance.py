"""phase_1t_schedule_performance

Revision ID: f0a1b2c3d4e5
Revises: e9f0a1b2c3d4
Create Date: 2026-10-10 21:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0a1b2c3d4e5'
down_revision: Union[str, Sequence[str], None] = 'e9f0a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'schedule_performance_snapshots',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('activity_id', sa.String(length=36), sa.ForeignKey('construction_activities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('schedule_id', sa.String(length=36), sa.ForeignKey('construction_schedules.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('monitoring_baseline_id', sa.String(length=36), sa.ForeignKey('monitoring_baselines.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('performance_period_start', sa.Date(), nullable=True),
        sa.Column('performance_period_end', sa.Date(), nullable=True),
        sa.Column('evaluation_date', sa.Date(), nullable=False),

        sa.Column('planned_start_date', sa.Date(), nullable=True),
        sa.Column('planned_finish_date', sa.Date(), nullable=True),
        sa.Column('planned_duration_days', sa.Integer(), nullable=True),
        sa.Column('actual_start_date', sa.Date(), nullable=True),
        sa.Column('actual_finish_date', sa.Date(), nullable=True),
        sa.Column('actual_duration_days', sa.Integer(), nullable=True),

        sa.Column('planned_cumulative_progress_pct', sa.Numeric(precision=7, scale=4), nullable=True),
        sa.Column('actual_cumulative_progress_pct', sa.Numeric(precision=7, scale=4), nullable=True),
        sa.Column('earned_schedule_days', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('actual_time_days', sa.Numeric(precision=10, scale=4), nullable=True),

        sa.Column('schedule_variance_days', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('schedule_performance_index', sa.Numeric(precision=10, scale=6), nullable=True),

        sa.Column('baseline_total_float_days', sa.Integer(), nullable=True),
        sa.Column('residual_total_float_days', sa.Integer(), nullable=True),
        sa.Column('is_critical_path', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('critical_path_impact_days', sa.Integer(), nullable=True),

        sa.Column('delay_status', sa.String(length=40), nullable=False),
        sa.Column('delay_classification', sa.String(length=40), nullable=True),
        sa.Column('delay_root_cause_category', sa.String(length=50), nullable=True),
        sa.Column('delay_justification', sa.Text(), nullable=True),
        sa.Column('delay_evidence_document_id', sa.String(length=36), sa.ForeignKey('documents.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('contract_variation_id', sa.String(length=36), sa.ForeignKey('contract_variation_orders.id', ondelete='RESTRICT'), nullable=True),

        sa.Column('performance_status', sa.String(length=40), nullable=False),
        sa.Column('algorithm_version', sa.String(length=50), nullable=False, server_default='SCHED_PERFORMANCE_1.0'),
        sa.Column('input_snapshot_json', sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column('provenance_metadata', sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column('canonical_hash', sa.String(length=64), nullable=False),

        sa.Column('status', sa.String(length=20), nullable=False, server_default='DRAFT'),
        sa.Column('created_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('finalized_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('superseded_by', sa.String(length=36), sa.ForeignKey('schedule_performance_snapshots.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('superseded_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('superseded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('supersession_reason', sa.Text(), nullable=True),

        sa.CheckConstraint(
            "status IN ('DRAFT', 'FINALIZED', 'SUPERSEDED')",
            name='ck_sps_status'
        ),
        sa.CheckConstraint(
            "delay_status IN ('ON_SCHEDULE', 'AHEAD_OF_SCHEDULE', 'MINOR_DELAY', 'CRITICAL_DELAY', 'FLOAT_ABSORBED', 'SCHEDULE_BREACH', 'REQUIRES_INPUT')",
            name='ck_sps_delay_status'
        ),
        sa.CheckConstraint(
            "delay_classification IS NULL OR delay_classification IN ('EXCUSABLE_COMPENSABLE', 'EXCUSABLE_NON_COMPENSABLE', 'NON_EXCUSABLE', 'CONCURRENT_DELAY', 'NO_DELAY')",
            name='ck_sps_delay_class'
        ),
        sa.CheckConstraint(
            "performance_status IN ('ON_TRACK', 'SCHEDULE_VARIANCE_WITHIN_TOLERANCE', 'CRITICAL_DELAY', 'SCHEDULE_BREACH', 'REQUIRES_INPUT', 'DATA_MISMATCH')",
            name='ck_sps_perf_status'
        ),
        sa.CheckConstraint(
            "performance_period_start IS NULL OR performance_period_end IS NULL OR performance_period_start <= performance_period_end",
            name='ck_sps_period'
        ),
        sa.CheckConstraint(
            "planned_start_date IS NULL OR planned_finish_date IS NULL OR planned_start_date <= planned_finish_date",
            name='ck_sps_planned_dates'
        ),
        sa.CheckConstraint(
            "actual_start_date IS NULL OR actual_finish_date IS NULL OR actual_start_date <= actual_finish_date",
            name='ck_sps_actual_dates'
        ),
        sa.CheckConstraint(
            "planned_duration_days IS NULL OR planned_duration_days >= 0",
            name='ck_sps_planned_duration'
        ),
        sa.CheckConstraint(
            "actual_duration_days IS NULL OR actual_duration_days >= 0",
            name='ck_sps_actual_duration'
        ),
        sa.CheckConstraint(
            "planned_cumulative_progress_pct IS NULL OR (planned_cumulative_progress_pct >= 0 AND planned_cumulative_progress_pct <= 100)",
            name='ck_sps_planned_pct'
        ),
        sa.CheckConstraint(
            "actual_cumulative_progress_pct IS NULL OR (actual_cumulative_progress_pct >= 0 AND actual_cumulative_progress_pct <= 100)",
            name='ck_sps_actual_pct'
        ),
        sa.CheckConstraint(
            """(status = 'DRAFT' AND finalized_by IS NULL AND finalized_at IS NULL AND superseded_by IS NULL AND superseded_by_user_id IS NULL AND superseded_at IS NULL AND supersession_reason IS NULL) OR
               (status = 'FINALIZED' AND finalized_by IS NOT NULL AND finalized_at IS NOT NULL AND superseded_by IS NULL AND superseded_by_user_id IS NULL AND superseded_at IS NULL AND supersession_reason IS NULL) OR
               (status = 'SUPERSEDED' AND finalized_by IS NOT NULL AND finalized_at IS NOT NULL AND superseded_by IS NOT NULL AND superseded_by_user_id IS NOT NULL AND superseded_at IS NOT NULL AND supersession_reason IS NOT NULL)""",
            name='ck_sps_lifecycle_metadata'
        ),
    )

    op.create_index('ix_sps_project', 'schedule_performance_snapshots', ['project_id'])
    op.create_index('ix_sps_activity', 'schedule_performance_snapshots', ['activity_id'])
    op.create_index('ix_sps_schedule', 'schedule_performance_snapshots', ['schedule_id'])
    op.create_index('ix_sps_status', 'schedule_performance_snapshots', ['status'])
    op.create_index('ix_sps_delay_status', 'schedule_performance_snapshots', ['delay_status'])
    op.create_index('ix_sps_perf_status', 'schedule_performance_snapshots', ['performance_status'])

    # Partial unique index for authoritative identity:
    # Requires explicit performance_period_start and performance_period_end when FINALIZED.
    # Open-ended periods are permitted only when both start and end are NULL (e.g. project-inception snapshots).
    op.execute("""
        CREATE UNIQUE INDEX uq_sps_authoritative_identity ON schedule_performance_snapshots (
            project_id,
            activity_id,
            performance_period_start,
            performance_period_end
        ) WHERE status = 'FINALIZED' AND performance_period_start IS NOT NULL AND performance_period_end IS NOT NULL;
    """)

    op.execute("""
        CREATE UNIQUE INDEX uq_sps_authoritative_identity_null_period ON schedule_performance_snapshots (
            project_id,
            activity_id
        ) WHERE status = 'FINALIZED' AND performance_period_start IS NULL AND performance_period_end IS NULL;
    """)

    # Function and Trigger for project cross-reference integrity and immutability
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_validate_sps_project_integrity()
        RETURNS TRIGGER AS $$
        DECLARE
            v_act_proj VARCHAR(36);
            v_sched_proj VARCHAR(36);
            v_base_proj VARCHAR(36);
            v_doc_proj VARCHAR(36);
            v_cvo_proj VARCHAR(36);
            v_rep_proj VARCHAR(36);
            v_rep_act VARCHAR(36);
        BEGIN
            -- 1. Validate activity belongs to project
            SELECT project_id INTO v_act_proj FROM construction_activities WHERE id = NEW.activity_id;
            IF v_act_proj IS NULL OR v_act_proj != NEW.project_id THEN
                RAISE EXCEPTION 'SchedulePerformanceSnapshot activity % belongs to project %, not snapshot project %', NEW.activity_id, v_act_proj, NEW.project_id;
            END IF;

            -- 2. Validate schedule belongs to project
            SELECT project_id INTO v_sched_proj FROM construction_schedules WHERE id = NEW.schedule_id;
            IF v_sched_proj IS NULL OR v_sched_proj != NEW.project_id THEN
                RAISE EXCEPTION 'SchedulePerformanceSnapshot schedule % belongs to project %, not snapshot project %', NEW.schedule_id, v_sched_proj, NEW.project_id;
            END IF;

            -- 3. Validate baseline belongs to project if specified
            IF NEW.monitoring_baseline_id IS NOT NULL THEN
                SELECT project_id INTO v_base_proj FROM monitoring_baselines WHERE id = NEW.monitoring_baseline_id;
                IF v_base_proj IS NULL OR v_base_proj != NEW.project_id THEN
                    RAISE EXCEPTION 'SchedulePerformanceSnapshot baseline % belongs to project %, not snapshot project %', NEW.monitoring_baseline_id, v_base_proj, NEW.project_id;
                END IF;
            END IF;

            -- 4. Validate evidence document belongs to project if specified
            IF NEW.delay_evidence_document_id IS NOT NULL THEN
                SELECT project_id INTO v_doc_proj FROM documents WHERE id = NEW.delay_evidence_document_id;
                IF v_doc_proj IS NULL OR v_doc_proj != NEW.project_id THEN
                    RAISE EXCEPTION 'SchedulePerformanceSnapshot delay evidence document % belongs to project %, not snapshot project %', NEW.delay_evidence_document_id, v_doc_proj, NEW.project_id;
                END IF;
            END IF;

            -- 5. Validate contract variation belongs to project if specified
            IF NEW.contract_variation_id IS NOT NULL THEN
                SELECT project_id INTO v_cvo_proj FROM contract_variation_orders WHERE id = NEW.contract_variation_id;
                IF v_cvo_proj IS NULL OR v_cvo_proj != NEW.project_id THEN
                    RAISE EXCEPTION 'SchedulePerformanceSnapshot contract variation % belongs to project %, not snapshot project %', NEW.contract_variation_id, v_cvo_proj, NEW.project_id;
                END IF;
            END IF;

            -- 6. Validate replacement snapshot on supersession
            IF NEW.superseded_by IS NOT NULL THEN
                SELECT project_id, activity_id INTO v_rep_proj, v_rep_act FROM schedule_performance_snapshots WHERE id = NEW.superseded_by;
                IF v_rep_proj IS NULL OR v_rep_proj != NEW.project_id THEN
                    RAISE EXCEPTION 'Replacement snapshot % belongs to project %, expected snapshot project %', NEW.superseded_by, v_rep_proj, NEW.project_id;
                END IF;
                IF v_rep_act IS NULL OR v_rep_act != NEW.activity_id THEN
                    RAISE EXCEPTION 'Replacement snapshot % activity % does not match target activity %', NEW.superseded_by, v_rep_act, NEW.activity_id;
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION fn_protect_schedule_performance_snapshot()
        RETURNS TRIGGER AS $$
        BEGIN
            -- INSERT rule: new snapshots must start as DRAFT
            IF TG_OP = 'INSERT' THEN
                IF NEW.status != 'DRAFT' THEN
                    RAISE EXCEPTION 'SchedulePerformanceSnapshot must be created in DRAFT status, cannot directly insert status %: %', NEW.status, NEW.id;
                END IF;
                RETURN NEW;
            END IF;

            -- DELETE rule: finalized or superseded records are completely immutable
            IF TG_OP = 'DELETE' THEN
                IF OLD.status IN ('FINALIZED', 'SUPERSEDED') THEN
                    RAISE EXCEPTION 'SchedulePerformanceSnapshot finalized or superseded records are immutable and cannot be deleted: %', OLD.id;
                END IF;
                RETURN OLD;
            END IF;

            -- UPDATE rules
            IF TG_OP = 'UPDATE' THEN
                IF OLD.status = 'SUPERSEDED' THEN
                    RAISE EXCEPTION 'SchedulePerformanceSnapshot superseded records cannot be modified: %', OLD.id;
                END IF;

                IF OLD.status = 'DRAFT' THEN
                    IF NEW.status = 'SUPERSEDED' THEN
                        RAISE EXCEPTION 'SchedulePerformanceSnapshot draft records cannot be directly superseded: %', OLD.id;
                    END IF;
                END IF;

                IF OLD.status = 'FINALIZED' THEN
                    IF NEW.status != 'SUPERSEDED' THEN
                        RAISE EXCEPTION 'SchedulePerformanceSnapshot finalized records are immutable and can only transition to SUPERSEDED: %', OLD.id;
                    END IF;

                    -- Immutability check on all calculation, input, and provenance attributes
                    IF (OLD.project_id IS DISTINCT FROM NEW.project_id) OR
                       (OLD.activity_id IS DISTINCT FROM NEW.activity_id) OR
                       (OLD.schedule_id IS DISTINCT FROM NEW.schedule_id) OR
                       (OLD.monitoring_baseline_id IS DISTINCT FROM NEW.monitoring_baseline_id) OR
                       (OLD.performance_period_start IS DISTINCT FROM NEW.performance_period_start) OR
                       (OLD.performance_period_end IS DISTINCT FROM NEW.performance_period_end) OR
                       (OLD.evaluation_date IS DISTINCT FROM NEW.evaluation_date) OR
                       (OLD.planned_start_date IS DISTINCT FROM NEW.planned_start_date) OR
                       (OLD.planned_finish_date IS DISTINCT FROM NEW.planned_finish_date) OR
                       (OLD.planned_duration_days IS DISTINCT FROM NEW.planned_duration_days) OR
                       (OLD.actual_start_date IS DISTINCT FROM NEW.actual_start_date) OR
                       (OLD.actual_finish_date IS DISTINCT FROM NEW.actual_finish_date) OR
                       (OLD.actual_duration_days IS DISTINCT FROM NEW.actual_duration_days) OR
                       (OLD.planned_cumulative_progress_pct IS DISTINCT FROM NEW.planned_cumulative_progress_pct) OR
                       (OLD.actual_cumulative_progress_pct IS DISTINCT FROM NEW.actual_cumulative_progress_pct) OR
                       (OLD.earned_schedule_days IS DISTINCT FROM NEW.earned_schedule_days) OR
                       (OLD.actual_time_days IS DISTINCT FROM NEW.actual_time_days) OR
                       (OLD.schedule_variance_days IS DISTINCT FROM NEW.schedule_variance_days) OR
                       (OLD.schedule_performance_index IS DISTINCT FROM NEW.schedule_performance_index) OR
                       (OLD.baseline_total_float_days IS DISTINCT FROM NEW.baseline_total_float_days) OR
                       (OLD.residual_total_float_days IS DISTINCT FROM NEW.residual_total_float_days) OR
                       (OLD.is_critical_path IS DISTINCT FROM NEW.is_critical_path) OR
                       (OLD.critical_path_impact_days IS DISTINCT FROM NEW.critical_path_impact_days) OR
                       (OLD.delay_status IS DISTINCT FROM NEW.delay_status) OR
                       (OLD.delay_classification IS DISTINCT FROM NEW.delay_classification) OR
                       (OLD.delay_root_cause_category IS DISTINCT FROM NEW.delay_root_cause_category) OR
                       (OLD.delay_justification IS DISTINCT FROM NEW.delay_justification) OR
                       (OLD.delay_evidence_document_id IS DISTINCT FROM NEW.delay_evidence_document_id) OR
                       (OLD.contract_variation_id IS DISTINCT FROM NEW.contract_variation_id) OR
                       (OLD.performance_status IS DISTINCT FROM NEW.performance_status) OR
                       (OLD.algorithm_version IS DISTINCT FROM NEW.algorithm_version) OR
                       (OLD.input_snapshot_json::text IS DISTINCT FROM NEW.input_snapshot_json::text) OR
                       (OLD.provenance_metadata::text IS DISTINCT FROM NEW.provenance_metadata::text) OR
                       (OLD.canonical_hash IS DISTINCT FROM NEW.canonical_hash) OR
                       (OLD.created_by IS DISTINCT FROM NEW.created_by) OR
                       (OLD.created_at IS DISTINCT FROM NEW.created_at) OR
                       (OLD.finalized_by IS DISTINCT FROM NEW.finalized_by) OR
                       (OLD.finalized_at IS DISTINCT FROM NEW.finalized_at) THEN
                        RAISE EXCEPTION 'SchedulePerformanceSnapshot calculation fields, provenance, inputs, and finalizer metadata are immutable upon finalization: %', OLD.id;
                    END IF;

                    IF NEW.superseded_by IS NULL OR NEW.superseded_by_user_id IS NULL OR NEW.superseded_at IS NULL OR NEW.supersession_reason IS NULL THEN
                        RAISE EXCEPTION 'Superseding a finalized SchedulePerformanceSnapshot requires superseded_by, superseded_by_user_id, superseded_at, and supersession_reason: %', OLD.id;
                    END IF;
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_validate_sps_project_integrity
        BEFORE INSERT OR UPDATE ON schedule_performance_snapshots
        FOR EACH ROW
        EXECUTE FUNCTION fn_validate_sps_project_integrity();
    """)

    op.execute("""
        CREATE TRIGGER trg_protect_schedule_performance_snapshot
        BEFORE INSERT OR UPDATE OR DELETE ON schedule_performance_snapshots
        FOR EACH ROW
        EXECUTE FUNCTION fn_protect_schedule_performance_snapshot();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_protect_schedule_performance_snapshot ON schedule_performance_snapshots;")
    op.execute("DROP TRIGGER IF EXISTS trg_validate_sps_project_integrity ON schedule_performance_snapshots;")
    op.execute("DROP FUNCTION IF EXISTS fn_protect_schedule_performance_snapshot();")
    op.execute("DROP FUNCTION IF EXISTS fn_validate_sps_project_integrity();")
    op.execute("DROP INDEX IF EXISTS uq_sps_authoritative_identity_null_period;")
    op.execute("DROP INDEX IF EXISTS uq_sps_authoritative_identity;")
    op.drop_table('schedule_performance_snapshots')
