"""phase_1s_resource_performance

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2026-10-10 17:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9f0a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'd8e9f0a1b2c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'resource_performance_snapshots',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('activity_id', sa.String(length=36), sa.ForeignKey('construction_activities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('resource_id', sa.String(length=36), sa.ForeignKey('resources.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('material_item_id', sa.String(length=36), sa.ForeignKey('material_items.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('resource_category', sa.String(length=20), nullable=False),
        sa.Column('performance_period_start', sa.Date(), nullable=True),
        sa.Column('performance_period_end', sa.Date(), nullable=True),
        sa.Column('resource_plan_id', sa.String(length=36), sa.ForeignKey('resource_plans.id', ondelete='SET NULL'), nullable=True),
        sa.Column('material_performance_snapshot_id', sa.String(length=36), sa.ForeignKey('material_performance_snapshots.id', ondelete='SET NULL'), nullable=True),
        sa.Column('cost_rate_id', sa.String(length=36), sa.ForeignKey('cost_rates.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('rate_mapping_id', sa.String(length=36), sa.ForeignKey('activity_rate_mappings.id', ondelete='SET NULL'), nullable=True),
        sa.Column('cost_rate_version', sa.String(length=50), nullable=True),
        sa.Column('applied_cost_rate_value', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('applied_cost_rate_unit', sa.String(length=50), nullable=True),
        sa.Column('planned_quantity', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('planned_unit', sa.String(length=50), nullable=True),
        sa.Column('actual_resource_quantity', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('actual_resource_unit', sa.String(length=50), nullable=True),
        sa.Column('verified_output_quantity', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('verified_output_unit', sa.String(length=50), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=True),
        sa.Column('planned_cost', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('actual_cost', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('resource_variance', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('resource_variance_percentage', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('cost_variance', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('productivity', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('productivity_unit', sa.String(length=50), nullable=True),
        sa.Column('resource_intensity', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('resource_intensity_unit', sa.String(length=50), nullable=True),
        sa.Column('cost_intensity', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('cost_intensity_unit', sa.String(length=50), nullable=True),
        sa.Column('tolerance_percentage', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('performance_status', sa.String(length=40), nullable=False),
        sa.Column('algorithm_version', sa.String(length=50), server_default='RES_PERFORMANCE_1.0', nullable=False),
        sa.Column('input_snapshot_json', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('provenance_metadata', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('canonical_hash', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='DRAFT', nullable=False),
        sa.Column('created_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('finalized_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('superseded_by', sa.String(length=36), sa.ForeignKey('resource_performance_snapshots.id', ondelete='SET NULL'), nullable=True),
        sa.Column('superseded_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('superseded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('supersession_reason', sa.Text(), nullable=True),
        sa.CheckConstraint(
            "resource_category IN ('LABOUR', 'MATERIAL', 'EQUIPMENT')",
            name='ck_rps_category'
        ),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'FINALIZED', 'SUPERSEDED')",
            name='ck_rps_status'
        ),
        sa.CheckConstraint(
            "performance_status IN ('MATCH', 'WITHIN_PERMISSIBLE_VARIANCE', 'OVER_RESOURCE_CONSUMPTION', 'UNDER_RESOURCE_CONSUMPTION', 'COST_OVER_RUN', 'COST_UNDER_RUN', 'REQUIRES_INPUT', 'NO_VERIFIED_OUTPUT', 'UNIT_MISMATCH', 'CURRENCY_MISMATCH', 'RATE_UNAVAILABLE')",
            name='ck_rps_perf_status'
        ),
        sa.CheckConstraint('planned_quantity IS NULL OR planned_quantity >= 0', name='ck_rps_planned_qty'),
        sa.CheckConstraint('actual_resource_quantity IS NULL OR actual_resource_quantity >= 0', name='ck_rps_act_qty'),
        sa.CheckConstraint('verified_output_quantity IS NULL OR verified_output_quantity >= 0', name='ck_rps_exec_qty'),
        sa.CheckConstraint('planned_cost IS NULL OR planned_cost >= 0', name='ck_rps_planned_cost'),
        sa.CheckConstraint('actual_cost IS NULL OR actual_cost >= 0', name='ck_rps_act_cost'),
        sa.CheckConstraint(
            'performance_period_start IS NULL OR performance_period_end IS NULL OR performance_period_start <= performance_period_end',
            name='ck_rps_period'
        ),
        sa.CheckConstraint('tolerance_percentage IS NULL OR tolerance_percentage >= 0', name='ck_rps_tol'),
    )

    op.create_index('ix_rps_project', 'resource_performance_snapshots', ['project_id'])
    op.create_index('ix_rps_activity', 'resource_performance_snapshots', ['activity_id'])
    op.create_index('ix_rps_resource', 'resource_performance_snapshots', ['resource_id'])
    op.create_index('ix_rps_material', 'resource_performance_snapshots', ['material_item_id'])
    op.create_index('ix_rps_category', 'resource_performance_snapshots', ['resource_category'])
    op.create_index('ix_rps_status', 'resource_performance_snapshots', ['status'])
    op.create_index('ix_rps_perf_status', 'resource_performance_snapshots', ['performance_status'])

    op.execute("""
        CREATE UNIQUE INDEX uq_rps_authoritative_identity ON resource_performance_snapshots (
            project_id,
            activity_id,
            resource_category,
            COALESCE(resource_id, '00000000-0000-0000-0000-000000000000'),
            COALESCE(material_item_id, '00000000-0000-0000-0000-000000000000'),
            COALESCE(performance_period_start, '1970-01-01'::date),
            COALESCE(performance_period_end, '1970-01-01'::date)
        ) WHERE status = 'FINALIZED';
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION fn_protect_resource_performance_snapshot()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF OLD.status IN ('FINALIZED', 'SUPERSEDED') THEN
                    RAISE EXCEPTION 'ResourcePerformanceSnapshot finalized or superseded records are immutable and cannot be deleted: %', OLD.id;
                END IF;
            END IF;

            IF TG_OP = 'UPDATE' THEN
                IF OLD.status = 'SUPERSEDED' THEN
                    RAISE EXCEPTION 'ResourcePerformanceSnapshot superseded records cannot be modified: %', OLD.id;
                END IF;

                IF OLD.status = 'DRAFT' THEN
                    IF NEW.status = 'SUPERSEDED' THEN
                        RAISE EXCEPTION 'ResourcePerformanceSnapshot draft records cannot be directly superseded: %', OLD.id;
                    END IF;
                END IF;

                IF OLD.status = 'FINALIZED' THEN
                    IF NEW.status != 'SUPERSEDED' THEN
                        RAISE EXCEPTION 'ResourcePerformanceSnapshot finalized records are immutable and can only transition to SUPERSEDED: %', OLD.id;
                    END IF;

                    IF (OLD.project_id IS DISTINCT FROM NEW.project_id) OR
                       (OLD.activity_id IS DISTINCT FROM NEW.activity_id) OR
                       (OLD.resource_id IS DISTINCT FROM NEW.resource_id) OR
                       (OLD.material_item_id IS DISTINCT FROM NEW.material_item_id) OR
                       (OLD.resource_category IS DISTINCT FROM NEW.resource_category) OR
                       (OLD.performance_period_start IS DISTINCT FROM NEW.performance_period_start) OR
                       (OLD.performance_period_end IS DISTINCT FROM NEW.performance_period_end) OR
                       (OLD.resource_plan_id IS DISTINCT FROM NEW.resource_plan_id) OR
                       (OLD.material_performance_snapshot_id IS DISTINCT FROM NEW.material_performance_snapshot_id) OR
                       (OLD.cost_rate_id IS DISTINCT FROM NEW.cost_rate_id) OR
                       (OLD.rate_mapping_id IS DISTINCT FROM NEW.rate_mapping_id) OR
                       (OLD.cost_rate_version IS DISTINCT FROM NEW.cost_rate_version) OR
                       (OLD.applied_cost_rate_value IS DISTINCT FROM NEW.applied_cost_rate_value) OR
                       (OLD.applied_cost_rate_unit IS DISTINCT FROM NEW.applied_cost_rate_unit) OR
                       (OLD.planned_quantity IS DISTINCT FROM NEW.planned_quantity) OR
                       (OLD.planned_unit IS DISTINCT FROM NEW.planned_unit) OR
                       (OLD.actual_resource_quantity IS DISTINCT FROM NEW.actual_resource_quantity) OR
                       (OLD.actual_resource_unit IS DISTINCT FROM NEW.actual_resource_unit) OR
                       (OLD.verified_output_quantity IS DISTINCT FROM NEW.verified_output_quantity) OR
                       (OLD.verified_output_unit IS DISTINCT FROM NEW.verified_output_unit) OR
                       (OLD.currency IS DISTINCT FROM NEW.currency) OR
                       (OLD.planned_cost IS DISTINCT FROM NEW.planned_cost) OR
                       (OLD.actual_cost IS DISTINCT FROM NEW.actual_cost) OR
                       (OLD.resource_variance IS DISTINCT FROM NEW.resource_variance) OR
                       (OLD.resource_variance_percentage IS DISTINCT FROM NEW.resource_variance_percentage) OR
                       (OLD.cost_variance IS DISTINCT FROM NEW.cost_variance) OR
                       (OLD.productivity IS DISTINCT FROM NEW.productivity) OR
                       (OLD.productivity_unit IS DISTINCT FROM NEW.productivity_unit) OR
                       (OLD.resource_intensity IS DISTINCT FROM NEW.resource_intensity) OR
                       (OLD.resource_intensity_unit IS DISTINCT FROM NEW.resource_intensity_unit) OR
                       (OLD.cost_intensity IS DISTINCT FROM NEW.cost_intensity) OR
                       (OLD.cost_intensity_unit IS DISTINCT FROM NEW.cost_intensity_unit) OR
                       (OLD.tolerance_percentage IS DISTINCT FROM NEW.tolerance_percentage) OR
                       (OLD.performance_status IS DISTINCT FROM NEW.performance_status) OR
                       (OLD.algorithm_version IS DISTINCT FROM NEW.algorithm_version) OR
                       (OLD.input_snapshot_json::text IS DISTINCT FROM NEW.input_snapshot_json::text) OR
                       (OLD.provenance_metadata::text IS DISTINCT FROM NEW.provenance_metadata::text) OR
                       (OLD.canonical_hash IS DISTINCT FROM NEW.canonical_hash) OR
                       (OLD.created_by IS DISTINCT FROM NEW.created_by) OR
                       (OLD.created_at IS DISTINCT FROM NEW.created_at) OR
                       (OLD.finalized_by IS DISTINCT FROM NEW.finalized_by) OR
                       (OLD.finalized_at IS DISTINCT FROM NEW.finalized_at) THEN
                        RAISE EXCEPTION 'ResourcePerformanceSnapshot calculation fields, provenance, inputs, and finalizer metadata are immutable upon finalization: %', OLD.id;
                    END IF;

                    IF NEW.superseded_by_user_id IS NULL OR NEW.superseded_at IS NULL OR NEW.supersession_reason IS NULL THEN
                        RAISE EXCEPTION 'Superseding a finalized ResourcePerformanceSnapshot requires superseded_by_user_id, superseded_at, and supersession_reason: %', OLD.id;
                    END IF;
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_protect_resource_performance_snapshot
        BEFORE UPDATE OR DELETE ON resource_performance_snapshots
        FOR EACH ROW
        EXECUTE FUNCTION fn_protect_resource_performance_snapshot();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_protect_resource_performance_snapshot ON resource_performance_snapshots;")
    op.execute("DROP FUNCTION IF EXISTS fn_protect_resource_performance_snapshot();")
    op.execute("DROP INDEX IF EXISTS uq_rps_authoritative_identity;")
    op.drop_table('resource_performance_snapshots')
