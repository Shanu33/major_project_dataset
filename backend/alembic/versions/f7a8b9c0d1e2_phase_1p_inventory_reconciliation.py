"""phase_1p_inventory_reconciliation

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-10-07 19:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f7a8b9c0d1e2'
down_revision: Union[str, Sequence[str], None] = 'e6f7a8b9c0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Phase 1P: Inventory & Material Availability Reconciliation Foundation."""

    # 1. material_stock_ledger
    op.create_table(
        'material_stock_ledger',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('material_item_id', sa.String(length=36), sa.ForeignKey('material_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('transaction_type', sa.String(length=30), nullable=False),
        sa.Column('transaction_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('reference_type', sa.String(length=50), nullable=True),
        sa.Column('reference_id', sa.String(length=100), nullable=True),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('source_reference', sa.String(length=100), nullable=True),
        sa.Column('created_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.CheckConstraint(
            "transaction_type IN ('RECEIPT', 'ISSUE', 'ADJUSTMENT_IN', 'ADJUSTMENT_OUT', 'RETURN', 'TRANSFER_IN', 'TRANSFER_OUT')",
            name='ck_stk_ledger_type'
        ),
        sa.CheckConstraint(
            "source_type IN ('CONTRACTOR_DECLARED', 'SUPERVISOR_VERIFIED', 'SUPERVISOR_CORRECTED', 'SYSTEM_ADJUSTED')",
            name='ck_stk_ledger_source'
        ),
        sa.CheckConstraint('transaction_quantity > 0', name='ck_stk_ledger_qty_pos'),
    )
    op.create_index('ix_stk_ledger_project', 'material_stock_ledger', ['project_id'])
    op.create_index('ix_stk_ledger_material', 'material_stock_ledger', ['material_item_id'])
    op.create_index('ix_stk_ledger_proj_mat', 'material_stock_ledger', ['project_id', 'material_item_id'])
    op.create_index('ix_stk_ledger_date', 'material_stock_ledger', ['transaction_date'])
    op.create_index('ix_stk_ledger_type', 'material_stock_ledger', ['transaction_type'])

    # 2. material_stock_balances
    op.create_table(
        'material_stock_balances',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('material_item_id', sa.String(length=36), sa.ForeignKey('material_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('total_received', sa.Numeric(18, 4), nullable=False, server_default='0.0000'),
        sa.Column('total_issued', sa.Numeric(18, 4), nullable=False, server_default='0.0000'),
        sa.Column('total_adjustment_in', sa.Numeric(18, 4), nullable=False, server_default='0.0000'),
        sa.Column('total_adjustment_out', sa.Numeric(18, 4), nullable=False, server_default='0.0000'),
        sa.Column('total_returned', sa.Numeric(18, 4), nullable=False, server_default='0.0000'),
        sa.Column('total_transfer_in', sa.Numeric(18, 4), nullable=False, server_default='0.0000'),
        sa.Column('total_transfer_out', sa.Numeric(18, 4), nullable=False, server_default='0.0000'),
        sa.Column('on_hand_quantity', sa.Numeric(18, 4), nullable=False, server_default='0.0000'),
        sa.Column('reserved_quantity', sa.Numeric(18, 4), nullable=False, server_default='0.0000'),
        sa.Column('available_quantity', sa.Numeric(18, 4), nullable=False, server_default='0.0000'),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('calculation_algorithm_version', sa.String(length=50), nullable=False, server_default='STK_1.0'),
        sa.Column('provenance_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('project_id', 'material_item_id', name='uq_stock_balance_proj_material'),
        sa.CheckConstraint('on_hand_quantity >= 0', name='ck_stock_balance_on_hand_nonneg'),
        sa.CheckConstraint('reserved_quantity >= 0', name='ck_stock_balance_reserved_nonneg'),
        sa.CheckConstraint('available_quantity >= 0', name='ck_stock_balance_available_nonneg'),
        sa.CheckConstraint('total_received >= 0', name='ck_stock_balance_received_nonneg'),
        sa.CheckConstraint('total_issued >= 0', name='ck_stock_balance_issued_nonneg'),
        sa.CheckConstraint('total_adjustment_in >= 0', name='ck_stock_balance_adj_in_nonneg'),
        sa.CheckConstraint('total_adjustment_out >= 0', name='ck_stock_balance_adj_out_nonneg'),
        sa.CheckConstraint('total_returned >= 0', name='ck_stock_balance_returned_nonneg'),
        sa.CheckConstraint('total_transfer_in >= 0', name='ck_stock_balance_transfer_in_nonneg'),
        sa.CheckConstraint('total_transfer_out >= 0', name='ck_stock_balance_transfer_out_nonneg'),
    )
    op.create_index('ix_stk_balance_project', 'material_stock_balances', ['project_id'])
    op.create_index('ix_stk_balance_material', 'material_stock_balances', ['material_item_id'])

    # 3. material_reservations
    op.create_table(
        'material_reservations',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('material_item_id', sa.String(length=36), sa.ForeignKey('material_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('material_requirement_plan_id', sa.String(length=36), sa.ForeignKey('material_requirement_plans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('material_requirement_item_id', sa.String(length=36), sa.ForeignKey('material_requirement_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reserved_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('reservation_date', sa.Date(), nullable=False),
        sa.Column('created_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('released_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('released_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.CheckConstraint("status IN ('ACTIVE', 'RELEASED', 'SUPERSEDED')", name='ck_mat_res_status'),
        sa.CheckConstraint('reserved_quantity > 0', name='ck_mat_res_qty_positive'),
    )
    op.create_index('ix_mat_res_project', 'material_reservations', ['project_id'])
    op.create_index('ix_mat_res_material', 'material_reservations', ['material_item_id'])
    op.create_index('ix_mat_res_mrp_plan', 'material_reservations', ['material_requirement_plan_id'])
    op.create_index('ix_mat_res_mrp_item', 'material_reservations', ['material_requirement_item_id'])
    op.create_index('ix_mat_res_status', 'material_reservations', ['status'])

    # 4. material_availability_reconciliations
    op.create_table(
        'material_availability_reconciliations',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('material_requirement_plan_id', sa.String(length=36), sa.ForeignKey('material_requirement_plans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('material_requirement_item_id', sa.String(length=36), sa.ForeignKey('material_requirement_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('material_item_id', sa.String(length=36), sa.ForeignKey('material_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('required_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('required_unit', sa.String(length=20), nullable=False),
        sa.Column('on_hand_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('reserved_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('available_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('shortage_quantity', sa.Numeric(18, 4), nullable=False, server_default='0.0000'),
        sa.Column('availability_status', sa.String(length=30), nullable=False),
        sa.Column('calculation_algorithm_version', sa.String(length=50), nullable=False, server_default='AVAIL_1.0'),
        sa.Column('provenance_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.CheckConstraint(
            "availability_status IN ('AVAILABLE', 'PARTIALLY_AVAILABLE', 'SHORTAGE', 'NO_STOCK_DATA', 'UNIT_MISMATCH', 'REQUIRES_INPUT')",
            name='ck_avail_status'
        ),
        sa.CheckConstraint('shortage_quantity >= 0', name='ck_avail_shortage_nonneg'),
        sa.CheckConstraint('required_quantity >= 0', name='ck_avail_req_qty_positive'),
    )
    op.create_index('ix_avail_recon_project', 'material_availability_reconciliations', ['project_id'])
    op.create_index('ix_avail_recon_plan', 'material_availability_reconciliations', ['material_requirement_plan_id'])
    op.create_index('ix_avail_recon_mrp_item', 'material_availability_reconciliations', ['material_requirement_item_id'])
    op.create_index('ix_avail_recon_material', 'material_availability_reconciliations', ['material_item_id'])
    op.create_index('ix_avail_recon_status', 'material_availability_reconciliations', ['availability_status'])

    # Triggers
    # Trigger 1: Stock ledger immutability (No UPDATE or DELETE)
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_enforce_stock_ledger_immutability()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'UPDATE' THEN
                RAISE EXCEPTION 'MaterialStockLedger records are append-only immutable audit entries: UPDATE is prohibited on %', OLD.id;
            END IF;
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'MaterialStockLedger records are append-only immutable audit entries: DELETE is prohibited on %', OLD.id;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_enforce_stock_ledger_immutability
        BEFORE UPDATE OR DELETE ON material_stock_ledger
        FOR EACH ROW EXECUTE FUNCTION fn_enforce_stock_ledger_immutability();
    """)

    # Trigger 2: Availability reconciliation immutability (No UPDATE or DELETE)
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_enforce_avail_reconciliation_immutability()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'UPDATE' THEN
                RAISE EXCEPTION 'MaterialAvailabilityReconciliation records are immutable historical audit snapshots: UPDATE is prohibited on %', OLD.id;
            END IF;
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'MaterialAvailabilityReconciliation records are immutable historical audit snapshots: DELETE is prohibited on %', OLD.id;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_enforce_avail_reconciliation_immutability
        BEFORE UPDATE OR DELETE ON material_availability_reconciliations
        FOR EACH ROW EXECUTE FUNCTION fn_enforce_avail_reconciliation_immutability();
    """)


def downgrade() -> None:
    """Downgrade schema - remove Phase 1P material inventory objects."""
    # Drop triggers and functions
    op.execute("DROP TRIGGER IF EXISTS trg_enforce_avail_reconciliation_immutability ON material_availability_reconciliations;")
    op.execute("DROP FUNCTION IF EXISTS fn_enforce_avail_reconciliation_immutability();")

    op.execute("DROP TRIGGER IF EXISTS trg_enforce_stock_ledger_immutability ON material_stock_ledger;")
    op.execute("DROP FUNCTION IF EXISTS fn_enforce_stock_ledger_immutability();")

    # Drop tables in reverse order
    op.drop_table('material_availability_reconciliations')
    op.drop_table('material_reservations')
    op.drop_table('material_stock_balances')
    op.drop_table('material_stock_ledger')

