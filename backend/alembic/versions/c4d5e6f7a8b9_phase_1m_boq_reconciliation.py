"""phase_1m_boq_reconciliation

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-10-06 23:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, Sequence[str], None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Phase 1M: BOQ Quantity-to-Execution Reconciliation & Contract Variation Foundation."""
    # Ensure btree_gist extension is available
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")

    # 1. Create contract_execution_items
    op.create_table(
        'contract_execution_items',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('boq_item_id', sa.String(length=36), sa.ForeignKey('boq_items.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('originating_cvo_id', sa.String(length=36), nullable=True), # FK added after CVO table creation
        sa.Column('item_origin', sa.String(length=32), nullable=False),
        sa.Column('item_code', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('unit_of_measure', sa.String(length=32), nullable=False),
        sa.Column('original_contract_quantity', sa.Numeric(16, 4), nullable=False),
        sa.Column('effective_contract_quantity', sa.Numeric(16, 4), nullable=False),
        sa.Column('original_contract_rate', sa.Numeric(16, 4), nullable=False),
        sa.Column('current_contract_rate', sa.Numeric(16, 4), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=False, server_default='INR'),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('superseded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('superseding_item_id', sa.String(length=36), sa.ForeignKey('contract_execution_items.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("item_origin IN ('ORIGINAL_BOQ', 'EXTRA_ITEM')", name='chk_cei_item_origin'),
        sa.CheckConstraint("status IN ('ACTIVE', 'SUPERSEDED', 'CLOSED')", name='chk_cei_status'),
        sa.CheckConstraint('original_contract_quantity >= 0 AND effective_contract_quantity >= 0', name='chk_cei_quantities'),
        sa.CheckConstraint('original_contract_rate > 0 AND current_contract_rate > 0', name='chk_cei_rates'),
        sa.CheckConstraint(
            "(item_origin = 'ORIGINAL_BOQ' AND boq_item_id IS NOT NULL AND originating_cvo_id IS NULL) OR "
            "(item_origin = 'EXTRA_ITEM' AND boq_item_id IS NULL AND originating_cvo_id IS NOT NULL)",
            name='chk_cei_origin_identity'
        ),
        sa.CheckConstraint(
            "(status = 'SUPERSEDED' AND superseded_at IS NOT NULL AND superseding_item_id IS NOT NULL) OR "
            "(status != 'SUPERSEDED' AND superseded_at IS NULL AND superseding_item_id IS NULL)",
            name='chk_cei_supersession'
        ),
    )
    op.create_index('ix_cei_project_lookup', 'contract_execution_items', ['project_id', 'effective_date'])
    op.create_index(
        'uq_cei_active_item_code',
        'contract_execution_items',
        ['project_id', 'item_code'],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'")
    )
    op.create_index(
        'ix_cei_boq_item_id',
        'contract_execution_items',
        ['boq_item_id'],
        unique=False
    )
    op.create_index(
        'uq_cei_originating_cvo',
        'contract_execution_items',
        ['originating_cvo_id'],
        unique=True,
        postgresql_where=sa.text("item_origin = 'EXTRA_ITEM'")
    )

    # 2. Create activity_contract_mappings
    op.create_table(
        'activity_contract_mappings',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('activity_id', sa.String(length=36), sa.ForeignKey('construction_activities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('contract_execution_item_id', sa.String(length=36), sa.ForeignKey('contract_execution_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('allocation_percentage', sa.Numeric(6, 2), nullable=False, server_default='100.00'),
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('effective_to', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('allocation_percentage > 0.00 AND allocation_percentage <= 100.00', name='chk_acm_percentage'),
        sa.CheckConstraint('effective_to IS NULL OR effective_to >= effective_from', name='chk_acm_date_range'),
    )
    op.create_index('idx_acm_activity_temporal', 'activity_contract_mappings', ['activity_id', 'effective_from', 'effective_to'])
    op.create_index('idx_acm_cei_temporal', 'activity_contract_mappings', ['contract_execution_item_id', 'effective_from', 'effective_to'])
    op.execute("""
        ALTER TABLE activity_contract_mappings
        ADD CONSTRAINT ex_acm_no_temporal_overlap
        EXCLUDE USING gist (
            activity_id WITH =,
            contract_execution_item_id WITH =,
            daterange(effective_from, COALESCE(effective_to, '9999-12-31'::date), '[]') WITH &&
        );
    """)

    # 3. Create contract_variation_orders
    op.create_table(
        'contract_variation_orders',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('contract_execution_item_id', sa.String(length=36), sa.ForeignKey('contract_execution_items.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('variation_number', sa.String(length=64), nullable=False),
        sa.Column('variation_type', sa.String(length=32), nullable=False),
        sa.Column('unit_of_measure', sa.String(length=32), nullable=False),
        sa.Column('quantity_delta', sa.Numeric(16, 4), nullable=False, server_default='0.0000'),
        sa.Column('rate_previous', sa.Numeric(16, 4), nullable=False),
        sa.Column('rate_revised', sa.Numeric(16, 4), nullable=False),
        sa.Column('net_variation_amount', sa.Numeric(18, 4), nullable=True),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='DRAFT'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            "variation_type IN ('QUANTITY_VARIATION', 'RATE_REVISION', 'EXTRA_ITEM_ADDITION', 'SCOPE_OMISSION')",
            name='chk_cvo_type'
        ),
        sa.CheckConstraint("status IN ('DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED')", name='chk_cvo_status'),
        sa.CheckConstraint('rate_previous > 0 AND rate_revised > 0', name='chk_cvo_rates'),
        sa.CheckConstraint(
            "(variation_type IN ('QUANTITY_VARIATION', 'SCOPE_OMISSION', 'EXTRA_ITEM_ADDITION') AND rate_previous = rate_revised) OR "
            "(variation_type = 'RATE_REVISION' AND rate_previous != rate_revised)",
            name='chk_cvo_rate_semantics'
        ),
        sa.CheckConstraint(
            "(variation_type = 'EXTRA_ITEM_ADDITION' AND quantity_delta > 0) OR "
            "(variation_type = 'SCOPE_OMISSION' AND quantity_delta < 0) OR "
            "(variation_type = 'QUANTITY_VARIATION' AND quantity_delta != 0) OR "
            "(variation_type = 'RATE_REVISION' AND quantity_delta = 0)",
            name='chk_cvo_type_deltas'
        ),
        sa.CheckConstraint(
            """(variation_type = 'EXTRA_ITEM_ADDITION' AND status IN ('DRAFT', 'SUBMITTED', 'REJECTED') 
                AND contract_execution_item_id IS NULL AND approved_at IS NULL AND approved_by_user_id IS NULL AND net_variation_amount IS NULL) OR
            (variation_type = 'EXTRA_ITEM_ADDITION' AND status = 'APPROVED' 
                AND contract_execution_item_id IS NOT NULL AND approved_at IS NOT NULL AND approved_by_user_id IS NOT NULL AND net_variation_amount IS NOT NULL) OR
            (variation_type != 'EXTRA_ITEM_ADDITION' AND status IN ('DRAFT', 'SUBMITTED', 'REJECTED') 
                AND contract_execution_item_id IS NOT NULL AND approved_at IS NULL AND approved_by_user_id IS NULL AND net_variation_amount IS NULL) OR
            (variation_type != 'EXTRA_ITEM_ADDITION' AND status = 'APPROVED' 
                AND contract_execution_item_id IS NOT NULL AND approved_at IS NOT NULL AND approved_by_user_id IS NOT NULL AND net_variation_amount IS NOT NULL)""",
            name='chk_cvo_lifecycle_rules'
        ),
    )
    op.create_index('idx_cvo_item_temporal', 'contract_variation_orders', ['contract_execution_item_id', 'effective_date', 'approved_at'])
    op.create_index('uq_cvo_project_number', 'contract_variation_orders', ['project_id', 'variation_number'], unique=True)
    op.create_index(
        'uq_cvo_extra_item_cei',
        'contract_variation_orders',
        ['contract_execution_item_id'],
        unique=True,
        postgresql_where=sa.text("variation_type = 'EXTRA_ITEM_ADDITION' AND status = 'APPROVED'")
    )

    # 4. Add mutual FK from contract_execution_items to contract_variation_orders
    op.create_foreign_key(
        'fk_cei_originating_cvo',
        'contract_execution_items',
        'contract_variation_orders',
        ['originating_cvo_id'],
        ['id'],
        ondelete='RESTRICT'
    )

    # 5. Create boq_reconciliation_snapshots
    op.create_table(
        'boq_reconciliation_snapshots',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('certificate_id', sa.String(length=36), sa.ForeignKey('period_progress_certificates.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('contract_execution_item_id', sa.String(length=36), sa.ForeignKey('contract_execution_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('effective_contract_quantity', sa.Numeric(16, 4), nullable=False),
        sa.Column('cumulative_executed_quantity', sa.Numeric(16, 4), nullable=False),
        sa.Column('cumulative_executed_quantity_boq_unit', sa.Numeric(16, 4), nullable=False),
        sa.Column('gross_over_execution_quantity', sa.Numeric(16, 4), nullable=False),
        sa.Column('critical_deviation_quantity', sa.Numeric(16, 4), nullable=False),
        sa.Column('reconciliation_rate', sa.Numeric(16, 4), nullable=False),
        sa.Column('historical_period_valuation', sa.Numeric(18, 4), nullable=False),
        sa.Column('current_rate_valuation', sa.Numeric(18, 4), nullable=False),
        sa.Column('valuation_delta', sa.Numeric(18, 4), nullable=False),
        sa.Column('is_critical_deviation', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('snapshot_hash', sa.String(length=64), nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            'effective_contract_quantity >= 0 AND cumulative_executed_quantity >= 0 AND '
            'cumulative_executed_quantity_boq_unit >= 0 AND gross_over_execution_quantity >= 0 AND '
            'critical_deviation_quantity >= 0',
            name='chk_brs_quantities'
        ),
        sa.CheckConstraint('historical_period_valuation >= 0 AND current_rate_valuation >= 0', name='chk_brs_valuation'),
    )
    op.create_index('uq_brs_cert_item', 'boq_reconciliation_snapshots', ['certificate_id', 'contract_execution_item_id'], unique=True)
    op.create_index('idx_brs_project_cert', 'boq_reconciliation_snapshots', ['project_id', 'certificate_id'])

    # 6. Create PostgreSQL Functions and Triggers
    op.execute("""
        -- Trigger 1: Two-way deferred constraint trigger on contract_execution_items
        CREATE OR REPLACE FUNCTION fn_verify_extra_item_cei_bidirectional()
        RETURNS TRIGGER AS $$
        DECLARE
            v_cvo RECORD;
        BEGIN
            IF NEW.item_origin = 'EXTRA_ITEM' THEN
                SELECT * INTO v_cvo FROM contract_variation_orders WHERE id = NEW.originating_cvo_id;
                IF NOT FOUND THEN
                    RAISE EXCEPTION 'EXTRA_ITEM CEI % points to non-existent CVO %.', NEW.id, NEW.originating_cvo_id;
                END IF;

                IF v_cvo.status != 'APPROVED' THEN
                    RAISE EXCEPTION 'EXTRA_ITEM CEI % cannot be committed against CVO % with status % (must be APPROVED).',
                        NEW.id, v_cvo.id, v_cvo.status;
                END IF;

                IF v_cvo.contract_execution_item_id IS DISTINCT FROM NEW.id THEN
                    RAISE EXCEPTION 'Bidirectional link mismatch: CEI % points to CVO %, but CVO points to CEI %.',
                        NEW.id, v_cvo.id, v_cvo.contract_execution_item_id;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE CONSTRAINT TRIGGER trg_verify_extra_item_cei_bidirectional
        AFTER INSERT OR UPDATE ON contract_execution_items
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE FUNCTION fn_verify_extra_item_cei_bidirectional();


        -- Trigger 2: Two-way deferred constraint trigger on contract_variation_orders
        CREATE OR REPLACE FUNCTION fn_verify_extra_item_cvo_bidirectional()
        RETURNS TRIGGER AS $$
        DECLARE
            v_cei RECORD;
        BEGIN
            IF NEW.variation_type = 'EXTRA_ITEM_ADDITION' THEN
                IF NEW.status = 'APPROVED' THEN
                    IF NEW.contract_execution_item_id IS NULL THEN
                        RAISE EXCEPTION 'Approved EXTRA_ITEM CVO % must have non-null contract_execution_item_id.', NEW.id;
                    END IF;

                    SELECT * INTO v_cei FROM contract_execution_items WHERE id = NEW.contract_execution_item_id;
                    IF NOT FOUND THEN
                        RAISE EXCEPTION 'Approved EXTRA_ITEM CVO % points to non-existent CEI %.', NEW.id, NEW.contract_execution_item_id;
                    END IF;

                    IF v_cei.item_origin != 'EXTRA_ITEM' THEN
                        RAISE EXCEPTION 'Approved EXTRA_ITEM CVO % must point to an EXTRA_ITEM CEI (found %)', NEW.id, v_cei.item_origin;
                    END IF;

                    IF v_cei.originating_cvo_id IS DISTINCT FROM NEW.id THEN
                        RAISE EXCEPTION 'Bidirectional link mismatch: CVO % points to CEI %, but CEI points to CVO %.',
                            NEW.id, NEW.contract_execution_item_id, v_cei.originating_cvo_id;
                    END IF;
                ELSE
                    -- DRAFT, SUBMITTED, REJECTED
                    IF NEW.contract_execution_item_id IS NOT NULL THEN
                        RAISE EXCEPTION 'Non-approved EXTRA_ITEM CVO % cannot have contract_execution_item_id attached.', NEW.id;
                    END IF;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE CONSTRAINT TRIGGER trg_verify_extra_item_cvo_bidirectional
        AFTER INSERT OR UPDATE ON contract_variation_orders
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE FUNCTION fn_verify_extra_item_cvo_bidirectional();


        -- Trigger 3: Protect ContractExecutionItem baseline & enforce state mutation authorization
        CREATE OR REPLACE FUNCTION fn_protect_contract_execution_item()
        RETURNS TRIGGER AS $$
        DECLARE
            v_super_date DATE;
            v_replacement RECORD;
            v_originating_cvo RECORD;
            v_ctx TEXT;
        BEGIN
            IF TG_OP = 'INSERT' THEN
                IF NEW.item_origin = 'EXTRA_ITEM' THEN
                    BEGIN
                        v_ctx := current_setting('app.auth_extra_item_creation', true);
                    EXCEPTION WHEN OTHERS THEN v_ctx := NULL; END;

                    IF v_ctx IS DISTINCT FROM 'TRUE' THEN
                        RAISE EXCEPTION 'Direct insertion of EXTRA_ITEM CEI is prohibited without app.auth_extra_item_creation.';
                    END IF;

                    SELECT * INTO v_originating_cvo FROM contract_variation_orders WHERE id = NEW.originating_cvo_id;
                    IF NOT FOUND THEN
                        RAISE EXCEPTION 'Originating CVO % does not exist.', NEW.originating_cvo_id;
                    END IF;
                    IF v_originating_cvo.project_id != NEW.project_id THEN
                        RAISE EXCEPTION 'Originating CVO project_id (%) does not match CEI project_id (%).', v_originating_cvo.project_id, NEW.project_id;
                    END IF;
                    IF v_originating_cvo.variation_type != 'EXTRA_ITEM_ADDITION' THEN
                        RAISE EXCEPTION 'Originating CVO must be EXTRA_ITEM_ADDITION.';
                    END IF;
                    IF NEW.unit_of_measure != v_originating_cvo.unit_of_measure THEN
                        RAISE EXCEPTION 'EXTRA_ITEM CEI unit_of_measure (%) must match CVO unit_of_measure (%).', NEW.unit_of_measure, v_originating_cvo.unit_of_measure;
                    END IF;
                END IF;
                RETURN NEW;
            END IF;

            IF TG_OP = 'UPDATE' THEN
                -- Baseline Fields Immutability
                IF OLD.project_id != NEW.project_id OR
                   OLD.item_origin != NEW.item_origin OR
                   OLD.boq_item_id IS DISTINCT FROM NEW.boq_item_id OR
                   OLD.originating_cvo_id IS DISTINCT FROM NEW.originating_cvo_id OR
                   OLD.original_contract_quantity != NEW.original_contract_quantity OR
                   OLD.original_contract_rate != NEW.original_contract_rate OR
                   OLD.unit_of_measure != NEW.unit_of_measure OR
                   OLD.effective_date != NEW.effective_date THEN
                    RAISE EXCEPTION 'ContractExecutionItem baseline fields are permanently immutable once created.';
                END IF;

                -- Live State Mutation Authorization
                IF OLD.effective_contract_quantity != NEW.effective_contract_quantity OR
                   OLD.current_contract_rate != NEW.current_contract_rate THEN
                    BEGIN
                        v_ctx := current_setting('app.auth_cei_state_mutation', true);
                    EXCEPTION WHEN OTHERS THEN v_ctx := NULL; END;

                    IF v_ctx IS DISTINCT FROM 'TRUE' THEN
                        RAISE EXCEPTION 'Direct mutation of CEI live state is prohibited without app.auth_cei_state_mutation.';
                    END IF;
                END IF;

                -- Supersession Validation
                IF OLD.status = 'ACTIVE' AND NEW.status = 'SUPERSEDED' THEN
                    IF OLD.item_origin = 'EXTRA_ITEM' THEN
                        RAISE EXCEPTION 'EXTRA_ITEM_CANNOT_BE_SUPERSEDED: Extra items cannot undergo generic supersession. Use contract variation orders for scope or rate evolution.';
                    END IF;

                    BEGIN
                        v_ctx := current_setting('app.auth_cei_supersession', true);
                    EXCEPTION WHEN OTHERS THEN v_ctx := NULL; END;

                    IF v_ctx IS DISTINCT FROM 'TRUE' THEN
                        RAISE EXCEPTION 'Direct supersession of CEI is prohibited without app.auth_cei_supersession.';
                    END IF;

                    IF NEW.superseded_at IS NULL OR NEW.superseding_item_id IS NULL THEN
                        RAISE EXCEPTION 'superseded_at and superseding_item_id must be provided when superseding an item.';
                    END IF;

                    IF NEW.superseding_item_id = NEW.id THEN
                        RAISE EXCEPTION 'CEI cannot supersede itself.';
                    END IF;

                    SELECT * INTO v_replacement FROM contract_execution_items WHERE id = NEW.superseding_item_id;
                    IF NOT FOUND THEN
                        RAISE EXCEPTION 'Replacement ContractExecutionItem does not exist.';
                    END IF;
                    IF v_replacement.project_id != NEW.project_id THEN
                        RAISE EXCEPTION 'Cross-project supersession is strictly prohibited.';
                    END IF;
                    IF v_replacement.status != 'ACTIVE' THEN
                        RAISE EXCEPTION 'Replacement ContractExecutionItem must be ACTIVE.';
                    END IF;
                    IF v_replacement.superseding_item_id IS NOT NULL THEN
                        RAISE EXCEPTION 'Replacement item cannot itself be superseded.';
                    END IF;

                    v_super_date := (NEW.superseded_at AT TIME ZONE 'UTC')::date;
                    IF v_replacement.effective_date != v_super_date THEN
                        RAISE EXCEPTION 'Replacement item effective_date (%) must match supersession date (%).', v_replacement.effective_date, v_super_date;
                    END IF;

                    -- Close active mappings: effective_to = v_super_date - 1 day
                    UPDATE activity_contract_mappings
                    SET effective_to = LEAST(
                            COALESCE(effective_to, '9999-12-31'::date),
                            (v_super_date - INTERVAL '1 day')::date
                        ),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE contract_execution_item_id = NEW.id
                      AND (effective_to IS NULL OR effective_to >= v_super_date);
                END IF;

                IF OLD.status IN ('SUPERSEDED', 'CLOSED') AND NEW.status = 'ACTIVE' THEN
                    RAISE EXCEPTION 'Cannot reactivate a superseded or closed ContractExecutionItem.';
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_protect_contract_execution_item
        BEFORE INSERT OR UPDATE ON contract_execution_items
        FOR EACH ROW
        EXECUTE FUNCTION fn_protect_contract_execution_item();


        -- Trigger 4: Mapping Effective-Date & Tripartite Project Isolation
        CREATE OR REPLACE FUNCTION fn_check_mapping_cei_validity()
        RETURNS TRIGGER AS $$
        DECLARE
            v_cei RECORD;
            v_activity RECORD;
            v_super_date DATE;
        BEGIN
            SELECT * INTO v_activity FROM construction_activities WHERE id = NEW.activity_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'Target construction activity does not exist.';
            END IF;

            SELECT * INTO v_cei FROM contract_execution_items WHERE id = NEW.contract_execution_item_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'Target ContractExecutionItem does not exist.';
            END IF;

            -- Tripartite Project Boundary Isolation
            IF v_activity.project_id != NEW.project_id OR v_cei.project_id != NEW.project_id THEN
                RAISE EXCEPTION 'PROJECT_ISOLATION_VIOLATION: activity (%), CEI (%), and mapping (%) must belong to the same project.',
                    v_activity.project_id, v_cei.project_id, NEW.project_id;
            END IF;

            -- Mapping effective_from cannot precede CEI effective_date
            IF NEW.effective_from < v_cei.effective_date THEN
                RAISE EXCEPTION 'CONTRACT_ITEM_NOT_EFFECTIVE_FOR_MAPPING: mapping effective_from (%) cannot precede contract execution item effective_date (%).',
                    NEW.effective_from, v_cei.effective_date;
            END IF;

            IF v_cei.status = 'CLOSED' THEN
                RAISE EXCEPTION 'Cannot create mapping for a closed ContractExecutionItem.';
            END IF;

            IF v_cei.status = 'SUPERSEDED' THEN
                v_super_date := (v_cei.superseded_at AT TIME ZONE 'UTC')::date;
                IF NEW.effective_from >= v_super_date THEN
                    RAISE EXCEPTION 'CONTRACT_ITEM_SUPERSEDED_FOR_MAPPING: mapping effective_from (%) cannot be on or after supersession date (%).',
                        NEW.effective_from, v_super_date;
                END IF;
                IF NEW.effective_to IS NOT NULL AND NEW.effective_to >= v_super_date THEN
                    RAISE EXCEPTION 'CONTRACT_ITEM_SUPERSEDED_FOR_MAPPING: mapping effective_to (%) exceeds CEI supersession date (%).',
                        NEW.effective_to, v_super_date;
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_check_mapping_cei_validity
        BEFORE INSERT OR UPDATE ON activity_contract_mappings
        FOR EACH ROW
        EXECUTE FUNCTION fn_check_mapping_cei_validity();


        -- Trigger 5: CVO Lifecycle, Rate Freshness & Approval Authorization
        CREATE OR REPLACE FUNCTION fn_enforce_cvo_lifecycle()
        RETURNS TRIGGER AS $$
        DECLARE
            v_cei RECORD;
            v_ctx TEXT;
        BEGIN
            IF TG_OP = 'INSERT' THEN
                IF NEW.contract_execution_item_id IS NOT NULL THEN
                    SELECT * INTO v_cei FROM contract_execution_items WHERE id = NEW.contract_execution_item_id;
                    IF NOT FOUND THEN
                        RAISE EXCEPTION 'Referenced CEI does not exist.';
                    END IF;
                    IF v_cei.project_id != NEW.project_id THEN
                        RAISE EXCEPTION 'Referenced CEI belongs to another project.';
                    END IF;
                    IF NEW.unit_of_measure != v_cei.unit_of_measure THEN
                        RAISE EXCEPTION 'CVO unit_of_measure (%) must match CEI unit_of_measure (%).', NEW.unit_of_measure, v_cei.unit_of_measure;
                    END IF;
                    IF NEW.rate_previous != v_cei.current_contract_rate THEN
                        RAISE EXCEPTION 'RATE_REVISION_STALE_AT_CREATION: CVO rate_previous (%) must match CEI current_contract_rate (%).',
                            NEW.rate_previous, v_cei.current_contract_rate;
                    END IF;
                END IF;
                RETURN NEW;
            END IF;

            IF TG_OP = 'UPDATE' THEN
                IF OLD.status IN ('APPROVED', 'REJECTED') THEN
                    RAISE EXCEPTION 'ContractVariationOrder in terminal state % cannot be modified.', OLD.status;
                END IF;

                IF OLD.status = 'DRAFT' AND NEW.status NOT IN ('DRAFT', 'SUBMITTED', 'REJECTED') THEN
                    RAISE EXCEPTION 'Invalid transition from DRAFT to %.', NEW.status;
                END IF;

                IF OLD.status = 'SUBMITTED' AND NEW.status NOT IN ('SUBMITTED', 'APPROVED', 'REJECTED') THEN
                    RAISE EXCEPTION 'Invalid transition from SUBMITTED to %.', NEW.status;
                END IF;

                -- Revalidate rate freshness at SUBMISSION
                IF OLD.status = 'DRAFT' AND NEW.status = 'SUBMITTED' AND NEW.variation_type = 'RATE_REVISION' THEN
                    SELECT * INTO v_cei FROM contract_execution_items WHERE id = NEW.contract_execution_item_id;
                    IF NEW.rate_previous != v_cei.current_contract_rate THEN
                        RAISE EXCEPTION 'RATE_REVISION_STALE_AT_SUBMISSION: rate_previous (%) differs from live CEI rate (%).',
                            NEW.rate_previous, v_cei.current_contract_rate;
                    END IF;
                END IF;

                -- Revalidate rate freshness and authorization at APPROVAL
                IF OLD.status = 'SUBMITTED' AND NEW.status = 'APPROVED' THEN
                    BEGIN
                        v_ctx := current_setting('app.auth_cvo_approval', true);
                    EXCEPTION WHEN OTHERS THEN v_ctx := NULL; END;

                    IF v_ctx IS DISTINCT FROM 'TRUE' THEN
                        RAISE EXCEPTION 'Direct transition to APPROVED prohibited without app.auth_cvo_approval.';
                    END IF;

                    IF NEW.variation_type = 'RATE_REVISION' THEN
                        SELECT * INTO v_cei FROM contract_execution_items WHERE id = NEW.contract_execution_item_id;
                        IF NEW.rate_previous != v_cei.current_contract_rate THEN
                            RAISE EXCEPTION 'RATE_REVISION_STALE_AT_APPROVAL: rate_previous (%) differs from live CEI rate (%). Another variation modified the rate.',
                                NEW.rate_previous, v_cei.current_contract_rate;
                        END IF;
                    END IF;
                END IF;

                -- Immutable financial terms once submitted
                IF OLD.status = 'SUBMITTED' AND NEW.status = 'SUBMITTED' THEN
                    IF OLD.quantity_delta != NEW.quantity_delta OR
                       OLD.rate_previous != NEW.rate_previous OR
                       OLD.rate_revised != NEW.rate_revised OR
                       OLD.effective_date != NEW.effective_date OR
                       OLD.unit_of_measure != NEW.unit_of_measure THEN
                        RAISE EXCEPTION 'Cannot modify terms of a SUBMITTED variation order.';
                    END IF;
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_enforce_cvo_lifecycle
        BEFORE INSERT OR UPDATE ON contract_variation_orders
        FOR EACH ROW
        EXECUTE FUNCTION fn_enforce_cvo_lifecycle();


        -- Trigger 6: Historical Reconciliation Snapshot Immutability
        CREATE OR REPLACE FUNCTION fn_lock_reconciliation_snapshot()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'boq_reconciliation_snapshots are immutable historical audit records. UPDATE and DELETE are strictly prohibited.';
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_lock_reconciliation_snapshot
        BEFORE UPDATE OR DELETE ON boq_reconciliation_snapshots
        FOR EACH ROW
        EXECUTE FUNCTION fn_lock_reconciliation_snapshot();
    """)


def downgrade() -> None:
    """Downgrade schema - remove Phase 1M objects in reverse order."""
    # 1. Drop triggers and functions
    op.execute("DROP TRIGGER IF EXISTS trg_lock_reconciliation_snapshot ON boq_reconciliation_snapshots;")
    op.execute("DROP FUNCTION IF EXISTS fn_lock_reconciliation_snapshot();")

    op.execute("DROP TRIGGER IF EXISTS trg_enforce_cvo_lifecycle ON contract_variation_orders;")
    op.execute("DROP FUNCTION IF EXISTS fn_enforce_cvo_lifecycle();")

    op.execute("DROP TRIGGER IF EXISTS trg_check_mapping_cei_validity ON activity_contract_mappings;")
    op.execute("DROP FUNCTION IF EXISTS fn_check_mapping_cei_validity();")

    op.execute("DROP TRIGGER IF EXISTS trg_protect_contract_execution_item ON contract_execution_items;")
    op.execute("DROP FUNCTION IF EXISTS fn_protect_contract_execution_item();")

    op.execute("DROP TRIGGER IF EXISTS trg_verify_extra_item_cvo_bidirectional ON contract_variation_orders;")
    op.execute("DROP FUNCTION IF EXISTS fn_verify_extra_item_cvo_bidirectional();")

    op.execute("DROP TRIGGER IF EXISTS trg_verify_extra_item_cei_bidirectional ON contract_execution_items;")
    op.execute("DROP FUNCTION IF EXISTS fn_verify_extra_item_cei_bidirectional();")

    # 2. Drop tables in reverse order
    op.drop_table('boq_reconciliation_snapshots')
    op.drop_constraint('fk_cei_originating_cvo', 'contract_execution_items', type_='foreignkey')
    op.drop_table('contract_variation_orders')
    op.drop_table('activity_contract_mappings')
    op.drop_table('contract_execution_items')
