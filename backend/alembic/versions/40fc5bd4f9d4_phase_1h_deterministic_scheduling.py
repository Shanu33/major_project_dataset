"""phase_1h_deterministic_scheduling

Revision ID: 40fc5bd4f9d4
Revises: f07d48e03b5d
Create Date: 2026-10-04 21:15:45.130017

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40fc5bd4f9d4'
down_revision: Union[str, Sequence[str], None] = 'f07d48e03b5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Phase 1H: Deterministic Construction Scheduling Foundation."""
    # 1. Create construction_activities table
    op.create_table(
        'construction_activities',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('engineering_element_id', sa.String(), sa.ForeignKey('engineering_elements.id', ondelete='SET NULL'), nullable=True),
        sa.Column('activity_code', sa.String(), nullable=False),
        sa.Column('activity_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('activity_type', sa.String(), nullable=False),
        sa.Column('duration_value', sa.Numeric(18, 6), nullable=True),
        sa.Column('duration_unit', sa.String(), nullable=True),
        sa.Column('duration_method', sa.String(), nullable=False, server_default='USER_PROVIDED'),
        sa.Column('duration_classification', sa.String(), nullable=False, server_default='USER_PROVIDED'),
        sa.Column('status', sa.String(), nullable=False, server_default='ACTIVE'),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )
    op.create_index(
        'uq_activity_project_code',
        'construction_activities',
        ['project_id', 'activity_code'],
        unique=True
    )
    op.create_index('ix_activities_project', 'construction_activities', ['project_id'])
    op.create_index('ix_activities_element', 'construction_activities', ['engineering_element_id'])
    op.create_index('ix_activities_status', 'construction_activities', ['status'])

    # 2. Create activity_dependencies table
    op.create_table(
        'activity_dependencies',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('predecessor_activity_id', sa.String(), sa.ForeignKey('construction_activities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('successor_activity_id', sa.String(), sa.ForeignKey('construction_activities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dependency_type', sa.String(), nullable=False, server_default='FINISH_TO_START'),
        sa.Column('lag_value', sa.Numeric(18, 6), nullable=False, server_default='0'),
        sa.Column('lag_unit', sa.String(), nullable=False, server_default='day'),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.CheckConstraint('predecessor_activity_id != successor_activity_id', name='ck_no_self_dependency')
    )
    op.create_index(
        'uq_activity_dependency',
        'activity_dependencies',
        ['project_id', 'predecessor_activity_id', 'successor_activity_id'],
        unique=True
    )
    op.create_index('ix_dependencies_project', 'activity_dependencies', ['project_id'])
    op.create_index('ix_dependencies_pred', 'activity_dependencies', ['predecessor_activity_id'])
    op.create_index('ix_dependencies_succ', 'activity_dependencies', ['successor_activity_id'])

    # 3. Create construction_schedules table
    op.create_table(
        'construction_schedules',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('schedule_version', sa.String(), nullable=False),
        sa.Column('calculation_status', sa.String(), nullable=False, server_default='CALCULATED'),
        sa.Column('project_duration', sa.Numeric(18, 6), nullable=True),
        sa.Column('duration_unit', sa.String(), nullable=False, server_default='day'),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('calculated_by', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('algorithm_version', sa.String(), nullable=False, server_default='CPM_1.0'),
        sa.Column('input_snapshot_json', sa.JSON(), nullable=False),
        sa.Column('result_summary_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_schedules_project', 'construction_schedules', ['project_id'])
    op.create_index('ix_schedules_status', 'construction_schedules', ['calculation_status'])

    # 4. Create activity_schedule_results table
    op.create_table(
        'activity_schedule_results',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('schedule_id', sa.String(), sa.ForeignKey('construction_schedules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('activity_id', sa.String(), sa.ForeignKey('construction_activities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('es', sa.Numeric(18, 6), nullable=False),
        sa.Column('ef', sa.Numeric(18, 6), nullable=False),
        sa.Column('ls', sa.Numeric(18, 6), nullable=False),
        sa.Column('lf', sa.Numeric(18, 6), nullable=False),
        sa.Column('total_float', sa.Numeric(18, 6), nullable=False),
        sa.Column('is_critical', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index(
        'uq_sched_result_activity',
        'activity_schedule_results',
        ['schedule_id', 'activity_id'],
        unique=True
    )
    op.create_index('ix_sched_results_schedule', 'activity_schedule_results', ['schedule_id'])
    op.create_index('ix_sched_results_activity', 'activity_schedule_results', ['activity_id'])

    # 5. Database triggers
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_validate_activity_dependency()
        RETURNS TRIGGER AS $$
        DECLARE
            pred_proj text;
            succ_proj text;
        BEGIN
            IF NEW.predecessor_activity_id = NEW.successor_activity_id THEN
                RAISE EXCEPTION 'Self-dependency is prohibited. Activity cannot depend on itself.';
            END IF;

            SELECT project_id INTO pred_proj FROM construction_activities WHERE id = NEW.predecessor_activity_id;
            SELECT project_id INTO succ_proj FROM construction_activities WHERE id = NEW.successor_activity_id;

            IF pred_proj IS NULL OR succ_proj IS NULL THEN
                RAISE EXCEPTION 'Predecessor or successor activity does not exist.';
            END IF;

            IF pred_proj <> NEW.project_id OR succ_proj <> NEW.project_id THEN
                RAISE EXCEPTION 'Cross-project dependencies are prohibited.';
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER validate_activity_dependency_trg
        BEFORE INSERT OR UPDATE ON activity_dependencies
        FOR EACH ROW
        EXECUTE FUNCTION trg_validate_activity_dependency();
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION trg_prevent_schedule_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Construction schedules are historical and immutable. Cannot delete schedule records.';
            ELSIF TG_OP = 'UPDATE' THEN
                IF OLD.calculation_status = 'CALCULATED' AND NEW.calculation_status = 'SUPERSEDED' THEN
                    IF OLD.id = NEW.id AND
                       OLD.project_id = NEW.project_id AND
                       OLD.schedule_version = NEW.schedule_version AND
                       (OLD.project_duration IS NOT DISTINCT FROM NEW.project_duration) AND
                       OLD.duration_unit = NEW.duration_unit AND
                       OLD.calculated_by = NEW.calculated_by AND
                       OLD.algorithm_version = NEW.algorithm_version AND
                       (OLD.input_snapshot_json::text IS NOT DISTINCT FROM NEW.input_snapshot_json::text) AND
                       (OLD.result_summary_json::text IS NOT DISTINCT FROM NEW.result_summary_json::text) AND
                       OLD.created_at = NEW.created_at THEN
                        RETURN NEW;
                    ELSE
                        RAISE EXCEPTION 'Cannot modify schedule calculation inputs or results during status change to SUPERSEDED.';
                    END IF;
                ELSE
                    RAISE EXCEPTION 'Construction schedules are immutable. Only transition from CALCULATED to SUPERSEDED is permitted.';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER prevent_schedule_modification_trg
        BEFORE UPDATE OR DELETE ON construction_schedules
        FOR EACH ROW
        EXECUTE FUNCTION trg_prevent_schedule_modification();
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION trg_prevent_schedule_result_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Activity schedule results are historical and immutable. Cannot delete results.';
            ELSIF TG_OP = 'UPDATE' THEN
                RAISE EXCEPTION 'Activity schedule results are immutable and cannot be updated.';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER prevent_schedule_result_modification_trg
        BEFORE UPDATE OR DELETE ON activity_schedule_results
        FOR EACH ROW
        EXECUTE FUNCTION trg_prevent_schedule_result_modification();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS prevent_schedule_result_modification_trg ON activity_schedule_results;")
    op.execute("DROP FUNCTION IF EXISTS trg_prevent_schedule_result_modification();")
    op.execute("DROP TRIGGER IF EXISTS prevent_schedule_modification_trg ON construction_schedules;")
    op.execute("DROP FUNCTION IF EXISTS trg_prevent_schedule_modification();")
    op.execute("DROP TRIGGER IF EXISTS validate_activity_dependency_trg ON activity_dependencies;")
    op.execute("DROP FUNCTION IF EXISTS trg_validate_activity_dependency();")

    op.drop_table('activity_schedule_results')
    op.drop_table('construction_schedules')
    op.drop_table('activity_dependencies')
    op.drop_table('construction_activities')
