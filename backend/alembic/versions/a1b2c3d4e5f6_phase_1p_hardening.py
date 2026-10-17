"""phase_1p_hardening

Revision ID: a1b2c3d4e5f6
Revises: f7a8b9c0d1e2
Create Date: 2026-10-07 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f7a8b9c0d1e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Phase 1P Hardening: Authoritative verification, balance protection, reservation lifecycle immutability, and nullable shortage for NO_STOCK_DATA."""

    # 1. Add verification and authoritative flags to material_stock_ledger
    op.add_column('material_stock_ledger', sa.Column('is_authoritative', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('material_stock_ledger', sa.Column('verification_status', sa.String(length=30), nullable=False, server_default='VERIFIED'))
    op.create_index('ix_stk_ledger_authoritative', 'material_stock_ledger', ['is_authoritative'])
    op.create_index('ix_stk_ledger_verif_status', 'material_stock_ledger', ['verification_status'])
    op.create_check_constraint(
        'ck_stk_ledger_verif_status',
        'material_stock_ledger',
        "verification_status IN ('PENDING_VERIFICATION', 'VERIFIED', 'CORRECTED', 'REJECTED')"
    )

    # 2. Relax shortage_quantity on material_availability_reconciliations to allow NULL for NO_STOCK_DATA
    op.drop_constraint('ck_avail_shortage_nonneg', 'material_availability_reconciliations', type_='check')
    op.alter_column('material_availability_reconciliations', 'shortage_quantity', nullable=True)
    op.create_check_constraint(
        'ck_avail_shortage_nonneg',
        'material_availability_reconciliations',
        'shortage_quantity IS NULL OR shortage_quantity >= 0'
    )

    # 3. Trigger: Protect MaterialStockBalance from arbitrary direct SQL mutation
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_protect_stock_balance()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'MaterialStockBalance records cannot be deleted: %', OLD.id;
            END IF;

            IF TG_OP = 'UPDATE' THEN
                -- Allow if session variable is explicitly set by the application service
                IF NULLIF(current_setting('app.allow_stock_balance_mutation', true), '') = 'true' THEN
                    RETURN NEW;
                END IF;

                -- Otherwise block arbitrary direct SQL update of quantitative balance fields
                IF (OLD.total_received IS DISTINCT FROM NEW.total_received) OR
                   (OLD.total_issued IS DISTINCT FROM NEW.total_issued) OR
                   (OLD.total_adjustment_in IS DISTINCT FROM NEW.total_adjustment_in) OR
                   (OLD.total_adjustment_out IS DISTINCT FROM NEW.total_adjustment_out) OR
                   (OLD.total_returned IS DISTINCT FROM NEW.total_returned) OR
                   (OLD.total_transfer_in IS DISTINCT FROM NEW.total_transfer_in) OR
                   (OLD.total_transfer_out IS DISTINCT FROM NEW.total_transfer_out) OR
                   (OLD.on_hand_quantity IS DISTINCT FROM NEW.on_hand_quantity) OR
                   (OLD.reserved_quantity IS DISTINCT FROM NEW.reserved_quantity) OR
                   (OLD.available_quantity IS DISTINCT FROM NEW.available_quantity) OR
                   (OLD.unit IS DISTINCT FROM NEW.unit) OR
                   (OLD.project_id IS DISTINCT FROM NEW.project_id) OR
                   (OLD.material_item_id IS DISTINCT FROM NEW.material_item_id) THEN
                    RAISE EXCEPTION 'Direct SQL mutation of MaterialStockBalance quantities or units is prohibited. Balances are derived from MaterialStockLedger.';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_protect_stock_balance
        BEFORE UPDATE OR DELETE ON material_stock_balances
        FOR EACH ROW EXECUTE FUNCTION fn_protect_stock_balance();
    """)

    # 4. Trigger: Enforce MaterialReservation identity immutability and lifecycle transitions
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_protect_material_reservation()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'MaterialReservation records are immutable audit records and cannot be deleted: %', OLD.id;
            END IF;

            IF TG_OP = 'UPDATE' THEN
                -- Check immutable identity and quantity fields
                IF (OLD.project_id IS DISTINCT FROM NEW.project_id) OR
                   (OLD.material_item_id IS DISTINCT FROM NEW.material_item_id) OR
                   (OLD.material_requirement_plan_id IS DISTINCT FROM NEW.material_requirement_plan_id) OR
                   (OLD.material_requirement_item_id IS DISTINCT FROM NEW.material_requirement_item_id) OR
                   (OLD.reserved_quantity IS DISTINCT FROM NEW.reserved_quantity) OR
                   (OLD.unit IS DISTINCT FROM NEW.unit) OR
                   (OLD.reservation_date IS DISTINCT FROM NEW.reservation_date) OR
                   (OLD.created_by IS DISTINCT FROM NEW.created_by) OR
                   (OLD.created_at IS DISTINCT FROM NEW.created_at) THEN
                    RAISE EXCEPTION 'MaterialReservation identity and quantity fields are immutable once created: %', OLD.id;
                END IF;

                -- Terminal state enforcement
                IF OLD.status IN ('RELEASED', 'SUPERSEDED') THEN
                    IF NEW.status IS DISTINCT FROM OLD.status THEN
                        RAISE EXCEPTION 'MaterialReservation % is terminal (%) and cannot transition to %', OLD.id, OLD.status, NEW.status;
                    END IF;
                END IF;

                -- Permitted transitions: ACTIVE -> RELEASED, ACTIVE -> SUPERSEDED
                IF OLD.status = 'ACTIVE' AND NEW.status NOT IN ('ACTIVE', 'RELEASED', 'SUPERSEDED') THEN
                    RAISE EXCEPTION 'Invalid status transition for MaterialReservation % from ACTIVE to %', OLD.id, NEW.status;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_protect_material_reservation
        BEFORE UPDATE OR DELETE ON material_reservations
        FOR EACH ROW EXECUTE FUNCTION fn_protect_material_reservation();
    """)


def downgrade() -> None:
    """Downgrade schema - Remove Phase 1P hardening triggers and columns."""
    op.execute("DROP TRIGGER IF EXISTS trg_protect_material_reservation ON material_reservations;")
    op.execute("DROP FUNCTION IF EXISTS fn_protect_material_reservation();")

    op.execute("DROP TRIGGER IF EXISTS trg_protect_stock_balance ON material_stock_balances;")
    op.execute("DROP FUNCTION IF EXISTS fn_protect_stock_balance();")

    op.drop_constraint('ck_avail_shortage_nonneg', 'material_availability_reconciliations', type_='check')
    op.alter_column('material_availability_reconciliations', 'shortage_quantity', nullable=False, server_default='0.0000')
    op.create_check_constraint(
        'ck_avail_shortage_nonneg',
        'material_availability_reconciliations',
        'shortage_quantity >= 0'
    )

    op.drop_constraint('ck_stk_ledger_verif_status', 'material_stock_ledger', type_='check')
    op.drop_index('ix_stk_ledger_verif_status', 'material_stock_ledger')
    op.drop_index('ix_stk_ledger_authoritative', 'material_stock_ledger')
    op.drop_column('material_stock_ledger', 'verification_status')
    op.drop_column('material_stock_ledger', 'is_authoritative')

