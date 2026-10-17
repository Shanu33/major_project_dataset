"""phase_1q_material_consumption_reconciliation

Revision ID: b5c6d7e8f9a0
Revises: a1b2c3d4e5f6
Create Date: 2026-10-07 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b5c6d7e8f9a0'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Phase 1Q: Material Issue Allocation, Actual Consumption & Planned vs Actual Reconciliation."""

    # 1. material_issue_allocations
    op.create_table(
        'material_issue_allocations',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('material_item_id', sa.String(length=36), sa.ForeignKey('material_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('material_stock_ledger_id', sa.String(length=36), sa.ForeignKey('material_stock_ledger.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('activity_id', sa.String(length=36), sa.ForeignKey('construction_activities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('material_requirement_plan_id', sa.String(length=36), sa.ForeignKey('material_requirement_plans.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('material_requirement_item_id', sa.String(length=36), sa.ForeignKey('material_requirement_items.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('issued_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('issued_unit', sa.String(length=20), nullable=False),
        sa.Column('issue_date', sa.Date(), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='STORE_ISSUE'),
        sa.Column('reference_type', sa.String(length=50), nullable=True),
        sa.Column('reference_id', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='ALLOCATED'),
        sa.Column('created_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.CheckConstraint('issued_quantity > 0', name='ck_issue_alloc_qty_pos'),
        sa.CheckConstraint("status IN ('ALLOCATED', 'CANCELLED', 'SUPERSEDED')", name='ck_issue_alloc_status'),
    )
    op.create_index('ix_issue_alloc_project', 'material_issue_allocations', ['project_id'])
    op.create_index('ix_issue_alloc_material', 'material_issue_allocations', ['material_item_id'])
    op.create_index('ix_issue_alloc_ledger', 'material_issue_allocations', ['material_stock_ledger_id'])
    op.create_index('ix_issue_alloc_activity', 'material_issue_allocations', ['activity_id'])
    op.create_index('ix_issue_alloc_plan', 'material_issue_allocations', ['material_requirement_plan_id'])
    op.create_index('ix_issue_alloc_status', 'material_issue_allocations', ['status'])

    # 2. material_actual_consumption_entries
    op.create_table(
        'material_actual_consumption_entries',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('material_item_id', sa.String(length=36), sa.ForeignKey('material_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('activity_id', sa.String(length=36), sa.ForeignKey('construction_activities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('material_requirement_plan_id', sa.String(length=36), sa.ForeignKey('material_requirement_plans.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('material_requirement_item_id', sa.String(length=36), sa.ForeignKey('material_requirement_items.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('issue_allocation_id', sa.String(length=36), sa.ForeignKey('material_issue_allocations.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('contractor_consumed_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('contractor_consumed_unit', sa.String(length=20), nullable=False),
        sa.Column('consumption_date', sa.Date(), nullable=False),
        sa.Column('declared_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('declared_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('verification_status', sa.String(length=30), nullable=False, server_default='PENDING_VERIFICATION'),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.CheckConstraint('contractor_consumed_quantity >= 0', name='ck_mat_cons_qty_nonneg'),
        sa.CheckConstraint(
            "verification_status IN ('PENDING_VERIFICATION', 'VERIFIED', 'CORRECTED', 'REJECTED')",
            name='ck_mat_cons_verif_status'
        ),
    )
    op.create_index('ix_mat_cons_project', 'material_actual_consumption_entries', ['project_id'])
    op.create_index('ix_mat_cons_material', 'material_actual_consumption_entries', ['material_item_id'])
    op.create_index('ix_mat_cons_activity', 'material_actual_consumption_entries', ['activity_id'])
    op.create_index('ix_mat_cons_plan', 'material_actual_consumption_entries', ['material_requirement_plan_id'])
    op.create_index('ix_mat_cons_status', 'material_actual_consumption_entries', ['verification_status'])

    # 3. material_consumption_verifications
    op.create_table(
        'material_consumption_verifications',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('consumption_entry_id', sa.String(length=36), sa.ForeignKey('material_actual_consumption_entries.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('verified_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('verified_unit', sa.String(length=20), nullable=False),
        sa.Column('verification_status', sa.String(length=30), nullable=False),
        sa.Column('correction_reason', sa.Text(), nullable=True),
        sa.Column('verified_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.CheckConstraint('verified_quantity >= 0', name='ck_mat_verif_qty_nonneg'),
        sa.CheckConstraint("verification_status IN ('VERIFIED', 'CORRECTED', 'REJECTED')", name='ck_mat_verif_status'),
    )
    op.create_index('ix_mat_verif_entry', 'material_consumption_verifications', ['consumption_entry_id'])
    op.create_index('ix_mat_verif_status', 'material_consumption_verifications', ['verification_status'])

    # 4. material_consumption_reconciliations
    op.create_table(
        'material_consumption_reconciliations',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('material_requirement_plan_id', sa.String(length=36), sa.ForeignKey('material_requirement_plans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('material_requirement_item_id', sa.String(length=36), sa.ForeignKey('material_requirement_items.id', ondelete='CASCADE'), nullable=True),
        sa.Column('activity_id', sa.String(length=36), sa.ForeignKey('construction_activities.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('material_item_id', sa.String(length=36), sa.ForeignKey('material_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('planned_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('planned_unit', sa.String(length=20), nullable=True),
        sa.Column('theoretical_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('theoretical_unit', sa.String(length=20), nullable=True),
        sa.Column('issued_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('issued_unit', sa.String(length=20), nullable=True),
        sa.Column('actual_consumed_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('actual_consumed_unit', sa.String(length=20), nullable=True),
        sa.Column('variance_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('variance_percentage', sa.Numeric(18, 4), nullable=True),
        sa.Column('permissible_wastage_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('unauthorized_wastage_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('algorithm_version', sa.String(length=50), nullable=False, server_default='MAT_CONSUMPTION_RECON_1.0'),
        sa.Column('input_snapshot_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('provenance_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('canonical_hash', sa.String(length=64), nullable=False),
        sa.Column('created_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint(
            "status IN ('MATCH', 'WITHIN_PERMISSIBLE_WASTAGE', 'OVER_CONSUMPTION', 'UNDER_CONSUMPTION', 'REQUIRES_INPUT', 'UNIT_MISMATCH', 'NO_VERIFIED_ACTUAL', 'CALCULATED', 'SUPERSEDED')",
            name='ck_mat_recon_status'
        ),
    )
    op.create_index('ix_mat_recon_project', 'material_consumption_reconciliations', ['project_id'])
    op.create_index('ix_mat_recon_plan', 'material_consumption_reconciliations', ['material_requirement_plan_id'])
    op.create_index('ix_mat_recon_activity', 'material_consumption_reconciliations', ['activity_id'])
    op.create_index('ix_mat_recon_material', 'material_consumption_reconciliations', ['material_item_id'])
    op.create_index('ix_mat_recon_status', 'material_consumption_reconciliations', ['status'])

    # Triggers for Immutability and State Protection

    # 1. Trigger: Protect MaterialIssueAllocation identity and quantity
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_protect_issue_allocation()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'MaterialIssueAllocation records cannot be deleted: %', OLD.id;
            END IF;

            IF TG_OP = 'UPDATE' THEN
                IF (OLD.project_id IS DISTINCT FROM NEW.project_id) OR
                   (OLD.material_item_id IS DISTINCT FROM NEW.material_item_id) OR
                   (OLD.material_stock_ledger_id IS DISTINCT FROM NEW.material_stock_ledger_id) OR
                   (OLD.activity_id IS DISTINCT FROM NEW.activity_id) OR
                   (OLD.material_requirement_plan_id IS DISTINCT FROM NEW.material_requirement_plan_id) OR
                   (OLD.material_requirement_item_id IS DISTINCT FROM NEW.material_requirement_item_id) OR
                   (OLD.issued_quantity IS DISTINCT FROM NEW.issued_quantity) OR
                   (OLD.issued_unit IS DISTINCT FROM NEW.issued_unit) OR
                   (OLD.issue_date IS DISTINCT FROM NEW.issue_date) OR
                   (OLD.created_by IS DISTINCT FROM NEW.created_by) OR
                   (OLD.created_at IS DISTINCT FROM NEW.created_at) THEN
                    RAISE EXCEPTION 'MaterialIssueAllocation identity and quantity fields are immutable once allocated: %', OLD.id;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_protect_issue_allocation
        BEFORE UPDATE OR DELETE ON material_issue_allocations
        FOR EACH ROW EXECUTE FUNCTION fn_protect_issue_allocation();
    """)

    # 2. Trigger: Protect MaterialConsumptionEntry original contractor declaration
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_protect_consumption_entry()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'MaterialConsumptionEntry records cannot be deleted: %', OLD.id;
            END IF;

            IF TG_OP = 'UPDATE' THEN
                -- Contractor declaration fields are strictly immutable
                IF (OLD.project_id IS DISTINCT FROM NEW.project_id) OR
                   (OLD.material_item_id IS DISTINCT FROM NEW.material_item_id) OR
                   (OLD.activity_id IS DISTINCT FROM NEW.activity_id) OR
                   (OLD.material_requirement_plan_id IS DISTINCT FROM NEW.material_requirement_plan_id) OR
                   (OLD.material_requirement_item_id IS DISTINCT FROM NEW.material_requirement_item_id) OR
                   (OLD.issue_allocation_id IS DISTINCT FROM NEW.issue_allocation_id) OR
                   (OLD.contractor_consumed_quantity IS DISTINCT FROM NEW.contractor_consumed_quantity) OR
                   (OLD.contractor_consumed_unit IS DISTINCT FROM NEW.contractor_consumed_unit) OR
                   (OLD.consumption_date IS DISTINCT FROM NEW.consumption_date) OR
                   (OLD.declared_by IS DISTINCT FROM NEW.declared_by) OR
                   (OLD.declared_at IS DISTINCT FROM NEW.declared_at) THEN
                    RAISE EXCEPTION 'MaterialConsumptionEntry original contractor declaration is immutable: %', OLD.id;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_protect_consumption_entry
        BEFORE UPDATE OR DELETE ON material_actual_consumption_entries
        FOR EACH ROW EXECUTE FUNCTION fn_protect_consumption_entry();
    """)

    # 3. Trigger: Protect MaterialConsumptionVerification (strictly append-only)
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_protect_consumption_verification()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'UPDATE' THEN
                RAISE EXCEPTION 'MaterialConsumptionVerification records are append-only audit entries: UPDATE is prohibited on %', OLD.id;
            END IF;
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'MaterialConsumptionVerification records are append-only audit entries: DELETE is prohibited on %', OLD.id;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_protect_consumption_verification
        BEFORE UPDATE OR DELETE ON material_consumption_verifications
        FOR EACH ROW EXECUTE FUNCTION fn_protect_consumption_verification();
    """)

    # 4. Trigger: Protect MaterialConsumptionReconciliation immutability
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_protect_consumption_reconciliation()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'MaterialConsumptionReconciliation records are immutable snapshots and cannot be deleted: %', OLD.id;
            END IF;

            IF TG_OP = 'UPDATE' THEN
                -- Prohibit updating any calculation, identity, or provenance fields
                IF (OLD.project_id IS DISTINCT FROM NEW.project_id) OR
                   (OLD.material_requirement_plan_id IS DISTINCT FROM NEW.material_requirement_plan_id) OR
                   (OLD.material_requirement_item_id IS DISTINCT FROM NEW.material_requirement_item_id) OR
                   (OLD.activity_id IS DISTINCT FROM NEW.activity_id) OR
                   (OLD.material_item_id IS DISTINCT FROM NEW.material_item_id) OR
                   (OLD.planned_quantity IS DISTINCT FROM NEW.planned_quantity) OR
                   (OLD.planned_unit IS DISTINCT FROM NEW.planned_unit) OR
                   (OLD.theoretical_quantity IS DISTINCT FROM NEW.theoretical_quantity) OR
                   (OLD.theoretical_unit IS DISTINCT FROM NEW.theoretical_unit) OR
                   (OLD.issued_quantity IS DISTINCT FROM NEW.issued_quantity) OR
                   (OLD.issued_unit IS DISTINCT FROM NEW.issued_unit) OR
                   (OLD.actual_consumed_quantity IS DISTINCT FROM NEW.actual_consumed_quantity) OR
                   (OLD.actual_consumed_unit IS DISTINCT FROM NEW.actual_consumed_unit) OR
                   (OLD.variance_quantity IS DISTINCT FROM NEW.variance_quantity) OR
                   (OLD.variance_percentage IS DISTINCT FROM NEW.variance_percentage) OR
                   (OLD.permissible_wastage_quantity IS DISTINCT FROM NEW.permissible_wastage_quantity) OR
                   (OLD.unauthorized_wastage_quantity IS DISTINCT FROM NEW.unauthorized_wastage_quantity) OR
                   (OLD.algorithm_version IS DISTINCT FROM NEW.algorithm_version) OR
                   (OLD.canonical_hash IS DISTINCT FROM NEW.canonical_hash) OR
                   (OLD.created_by IS DISTINCT FROM NEW.created_by) OR
                   (OLD.created_at IS DISTINCT FROM NEW.created_at) THEN
                    RAISE EXCEPTION 'MaterialConsumptionReconciliation calculation fields are immutable: %', OLD.id;
                END IF;

                -- Allow only transition to SUPERSEDED
                IF OLD.status IS DISTINCT FROM NEW.status THEN
                    IF NEW.status != 'SUPERSEDED' THEN
                        RAISE EXCEPTION 'MaterialConsumptionReconciliation % cannot transition from % to %', OLD.id, OLD.status, NEW.status;
                    END IF;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_protect_consumption_reconciliation
        BEFORE UPDATE OR DELETE ON material_consumption_reconciliations
        FOR EACH ROW EXECUTE FUNCTION fn_protect_consumption_reconciliation();
    """)


def downgrade() -> None:
    """Downgrade schema - Remove Phase 1Q triggers and tables."""
    op.execute("DROP TRIGGER IF EXISTS trg_protect_consumption_reconciliation ON material_consumption_reconciliations;")
    op.execute("DROP FUNCTION IF EXISTS fn_protect_consumption_reconciliation();")

    op.execute("DROP TRIGGER IF EXISTS trg_protect_consumption_verification ON material_consumption_verifications;")
    op.execute("DROP FUNCTION IF EXISTS fn_protect_consumption_verification();")

    op.execute("DROP TRIGGER IF EXISTS trg_protect_consumption_entry ON material_actual_consumption_entries;")
    op.execute("DROP FUNCTION IF EXISTS fn_protect_consumption_entry();")

    op.execute("DROP TRIGGER IF EXISTS trg_protect_issue_allocation ON material_issue_allocations;")
    op.execute("DROP FUNCTION IF EXISTS fn_protect_issue_allocation();")

    op.drop_table('material_consumption_reconciliations')
    op.drop_table('material_consumption_verifications')
    op.drop_table('material_actual_consumption_entries')
    op.drop_table('material_issue_allocations')
