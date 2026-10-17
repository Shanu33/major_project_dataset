"""phase_1r_material_performance

Revision ID: c7d8e9f0a1b2
Revises: b5c6d7e8f9a0
Create Date: 2026-10-08 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, Sequence[str], None] = 'b5c6d7e8f9a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Phase 1R: Material Productivity, Consumption Efficiency & Resource Performance."""

    op.create_table(
        'material_performance_snapshots',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('activity_id', sa.String(length=36), sa.ForeignKey('construction_activities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('material_item_id', sa.String(length=36), sa.ForeignKey('material_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('reconciliation_id', sa.String(length=36), sa.ForeignKey('material_consumption_reconciliations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('requirement_plan_id', sa.String(length=36), sa.ForeignKey('material_requirement_plans.id', ondelete='SET NULL'), nullable=True),
        sa.Column('requirement_item_id', sa.String(length=36), sa.ForeignKey('material_requirement_items.id', ondelete='SET NULL'), nullable=True),
        sa.Column('performance_period_start', sa.Date(), nullable=True),
        sa.Column('performance_period_end', sa.Date(), nullable=True),
        sa.Column('planned_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('planned_unit', sa.String(length=20), nullable=True),
        sa.Column('theoretical_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('theoretical_unit', sa.String(length=20), nullable=True),
        sa.Column('issued_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('issued_unit', sa.String(length=20), nullable=True),
        sa.Column('actual_consumption_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('actual_consumption_unit', sa.String(length=20), nullable=True),
        sa.Column('verified_activity_execution_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('verified_activity_execution_unit', sa.String(length=20), nullable=True),
        sa.Column('permissible_wastage_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('unauthorized_wastage_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('planned_variance_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('theoretical_variance_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('planned_variance_percentage', sa.Numeric(18, 4), nullable=True),
        sa.Column('theoretical_variance_percentage', sa.Numeric(18, 4), nullable=True),
        sa.Column('consumption_intensity', sa.Numeric(18, 6), nullable=True),
        sa.Column('productivity', sa.Numeric(18, 6), nullable=True),
        sa.Column('performance_status', sa.String(length=30), nullable=False),
        sa.Column('algorithm_version', sa.String(length=50), nullable=False, server_default='MAT_PERFORMANCE_1.0'),
        sa.Column('input_snapshot_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('provenance_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('canonical_hash', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='DRAFT'),
        sa.Column('created_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('finalized_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('superseded_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('superseded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('supersession_reason', sa.Text(), nullable=True),
        sa.CheckConstraint("status IN ('DRAFT', 'FINALIZED', 'SUPERSEDED')", name='ck_mps_status'),
        sa.CheckConstraint(
            "performance_status IN ('MATCH', 'WITHIN_PERMISSIBLE_VARIANCE', 'OVER_CONSUMPTION', 'UNDER_CONSUMPTION', 'UNAUTHORIZED_WASTAGE', 'REQUIRES_INPUT', 'NO_VERIFIED_ACTUAL', 'NO_THEORETICAL_DATA', 'UNIT_MISMATCH')",
            name='ck_mps_perf_status'
        ),
        sa.CheckConstraint('planned_quantity IS NULL OR planned_quantity >= 0', name='ck_mps_planned_qty'),
        sa.CheckConstraint('theoretical_quantity IS NULL OR theoretical_quantity >= 0', name='ck_mps_theo_qty'),
        sa.CheckConstraint('issued_quantity IS NULL OR issued_quantity >= 0', name='ck_mps_issued_qty'),
        sa.CheckConstraint('actual_consumption_quantity IS NULL OR actual_consumption_quantity >= 0', name='ck_mps_act_qty'),
        sa.CheckConstraint('verified_activity_execution_quantity IS NULL OR verified_activity_execution_quantity >= 0', name='ck_mps_exec_qty'),
        sa.CheckConstraint(
            'performance_period_start IS NULL OR performance_period_end IS NULL OR performance_period_start <= performance_period_end',
            name='ck_mps_period'
        ),
    )

    op.create_index('ix_mps_project', 'material_performance_snapshots', ['project_id'])
    op.create_index('ix_mps_activity', 'material_performance_snapshots', ['activity_id'])
    op.create_index('ix_mps_material', 'material_performance_snapshots', ['material_item_id'])
    op.create_index('ix_mps_status', 'material_performance_snapshots', ['status'])
    op.create_index('ix_mps_perf_status', 'material_performance_snapshots', ['performance_status'])

    # PostgreSQL Trigger to enforce finalized and superseded immutability
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_protect_material_performance_snapshot()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF OLD.status IN ('FINALIZED', 'SUPERSEDED') THEN
                    RAISE EXCEPTION 'MaterialPerformanceSnapshot finalized or superseded records are immutable and cannot be deleted: %', OLD.id;
                END IF;
            END IF;

            IF TG_OP = 'UPDATE' THEN
                IF OLD.status = 'SUPERSEDED' THEN
                    RAISE EXCEPTION 'MaterialPerformanceSnapshot superseded records cannot be modified: %', OLD.id;
                END IF;

                IF OLD.status = 'FINALIZED' THEN
                    IF NEW.status != 'SUPERSEDED' THEN
                        RAISE EXCEPTION 'MaterialPerformanceSnapshot finalized records are immutable and can only transition to SUPERSEDED: %', OLD.id;
                    END IF;

                    IF (OLD.project_id IS DISTINCT FROM NEW.project_id) OR
                       (OLD.activity_id IS DISTINCT FROM NEW.activity_id) OR
                       (OLD.material_item_id IS DISTINCT FROM NEW.material_item_id) OR
                       (OLD.reconciliation_id IS DISTINCT FROM NEW.reconciliation_id) OR
                       (OLD.requirement_plan_id IS DISTINCT FROM NEW.requirement_plan_id) OR
                       (OLD.requirement_item_id IS DISTINCT FROM NEW.requirement_item_id) OR
                       (OLD.performance_period_start IS DISTINCT FROM NEW.performance_period_start) OR
                       (OLD.performance_period_end IS DISTINCT FROM NEW.performance_period_end) OR
                       (OLD.planned_quantity IS DISTINCT FROM NEW.planned_quantity) OR
                       (OLD.planned_unit IS DISTINCT FROM NEW.planned_unit) OR
                       (OLD.theoretical_quantity IS DISTINCT FROM NEW.theoretical_quantity) OR
                       (OLD.theoretical_unit IS DISTINCT FROM NEW.theoretical_unit) OR
                       (OLD.issued_quantity IS DISTINCT FROM NEW.issued_quantity) OR
                       (OLD.issued_unit IS DISTINCT FROM NEW.issued_unit) OR
                       (OLD.actual_consumption_quantity IS DISTINCT FROM NEW.actual_consumption_quantity) OR
                       (OLD.actual_consumption_unit IS DISTINCT FROM NEW.actual_consumption_unit) OR
                       (OLD.verified_activity_execution_quantity IS DISTINCT FROM NEW.verified_activity_execution_quantity) OR
                       (OLD.verified_activity_execution_unit IS DISTINCT FROM NEW.verified_activity_execution_unit) OR
                       (OLD.permissible_wastage_quantity IS DISTINCT FROM NEW.permissible_wastage_quantity) OR
                       (OLD.unauthorized_wastage_quantity IS DISTINCT FROM NEW.unauthorized_wastage_quantity) OR
                       (OLD.planned_variance_quantity IS DISTINCT FROM NEW.planned_variance_quantity) OR
                       (OLD.planned_variance_percentage IS DISTINCT FROM NEW.planned_variance_percentage) OR
                       (OLD.theoretical_variance_quantity IS DISTINCT FROM NEW.theoretical_variance_quantity) OR
                       (OLD.theoretical_variance_percentage IS DISTINCT FROM NEW.theoretical_variance_percentage) OR
                       (OLD.consumption_intensity IS DISTINCT FROM NEW.consumption_intensity) OR
                       (OLD.productivity IS DISTINCT FROM NEW.productivity) OR
                       (OLD.performance_status IS DISTINCT FROM NEW.performance_status) OR
                       (OLD.algorithm_version IS DISTINCT FROM NEW.algorithm_version) OR
                       (OLD.canonical_hash IS DISTINCT FROM NEW.canonical_hash) OR
                       (OLD.created_by IS DISTINCT FROM NEW.created_by) OR
                       (OLD.created_at IS DISTINCT FROM NEW.created_at) THEN
                        RAISE EXCEPTION 'MaterialPerformanceSnapshot calculation fields are immutable: %', OLD.id;
                    END IF;

                    IF NEW.superseded_at IS NULL THEN
                        NEW.superseded_at := now();
                    END IF;
                END IF;

                IF OLD.status = 'DRAFT' AND NEW.status = 'SUPERSEDED' THEN
                    RAISE EXCEPTION 'MaterialPerformanceSnapshot cannot transition directly from DRAFT to SUPERSEDED: %', OLD.id;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_protect_material_performance_snapshot
        BEFORE UPDATE OR DELETE ON material_performance_snapshots
        FOR EACH ROW EXECUTE FUNCTION fn_protect_material_performance_snapshot();
    """)


def downgrade() -> None:
    """Downgrade schema - Remove Phase 1R triggers and tables."""
    op.execute("DROP TRIGGER IF EXISTS trg_protect_material_performance_snapshot ON material_performance_snapshots;")
    op.execute("DROP FUNCTION IF EXISTS fn_protect_material_performance_snapshot();")
    op.drop_table('material_performance_snapshots')

