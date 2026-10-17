"""phase_1r_hardening

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-10-09 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8e9f0a1b2c3'
down_revision: Union[str, Sequence[str], None] = 'c7d8e9f0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add superseded_by_user_id column referencing users(id)
    op.add_column(
        'material_performance_snapshots',
        sa.Column('superseded_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True)
    )

    # 2. Data migration: copy any existing superseded_by user id into superseded_by_user_id
    op.execute("UPDATE material_performance_snapshots SET superseded_by_user_id = superseded_by WHERE superseded_by IS NOT NULL;")
    op.execute("UPDATE material_performance_snapshots SET superseded_by = NULL;")

    # 3. Drop existing FK constraint from superseded_by to users
    op.drop_constraint('material_performance_snapshots_superseded_by_fkey', 'material_performance_snapshots', type_='foreignkey')

    # 4. Create new FK constraint from superseded_by to material_performance_snapshots.id
    op.create_foreign_key(
        'fk_mps_superseded_by_snapshot',
        'material_performance_snapshots',
        'material_performance_snapshots',
        ['superseded_by'],
        ['id'],
        ondelete='SET NULL'
    )

    # 5. Add unique partial index for authoritative snapshots to prevent duplicate finalized snapshots
    op.execute("""
        CREATE UNIQUE INDEX uq_mps_authoritative_identity ON material_performance_snapshots (
            project_id,
            activity_id,
            material_item_id,
            COALESCE(performance_period_start, '1970-01-01'::date),
            COALESCE(performance_period_end, '1970-01-01'::date),
            COALESCE(reconciliation_id, '00000000-0000-0000-0000-000000000000')
        ) WHERE status = 'FINALIZED';
    """)

    # 6. Update trigger function to cover all calculation fields, inputs, provenance, finalized metadata
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
                       (OLD.input_snapshot_json IS DISTINCT FROM NEW.input_snapshot_json) OR
                       (OLD.provenance_metadata IS DISTINCT FROM NEW.provenance_metadata) OR
                       (OLD.canonical_hash IS DISTINCT FROM NEW.canonical_hash) OR
                       (OLD.created_by IS DISTINCT FROM NEW.created_by) OR
                       (OLD.created_at IS DISTINCT FROM NEW.created_at) OR
                       (OLD.finalized_by IS DISTINCT FROM NEW.finalized_by) OR
                       (OLD.finalized_at IS DISTINCT FROM NEW.finalized_at) THEN
                        RAISE EXCEPTION 'MaterialPerformanceSnapshot calculation fields, provenance, inputs, and finalization metadata are immutable: %', OLD.id;
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
    """)


def downgrade() -> None:
    # 1. Restore trigger function from c7d8e9f0a1b2
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
    """)

    # 2. Drop unique partial index
    op.execute("DROP INDEX IF EXISTS uq_mps_authoritative_identity;")

    # 3. Drop snapshot FK on superseded_by
    op.drop_constraint('fk_mps_superseded_by_snapshot', 'material_performance_snapshots', type_='foreignkey')

    # 4. Re-create user FK on superseded_by
    op.create_foreign_key(
        'material_performance_snapshots_superseded_by_fkey',
        'material_performance_snapshots',
        'users',
        ['superseded_by'],
        ['id'],
        ondelete='RESTRICT'
    )

    # 5. Restore user id back to superseded_by where available
    op.execute("UPDATE material_performance_snapshots SET superseded_by = superseded_by_user_id WHERE superseded_by_user_id IS NOT NULL;")

    # 6. Drop superseded_by_user_id column
    op.drop_column('material_performance_snapshots', 'superseded_by_user_id')

