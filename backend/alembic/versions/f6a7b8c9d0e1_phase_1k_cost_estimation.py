"""phase_1k_cost_estimation

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-10-05 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Phase 1K: Deterministic Cost Estimation & Rate-Based Valuation Foundation."""
    # 1. Create cost_rates table
    op.create_table(
        'cost_rates',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),
        sa.Column('rate_code', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('rate_value', sa.Numeric(18, 6), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='INR'),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('source_reference', sa.String(length=255), nullable=False),
        sa.Column('source_document_id', sa.String(), sa.ForeignKey('documents.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('source_evidence_id', sa.String(), sa.ForeignKey('evidence.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('version', sa.String(length=50), nullable=False, server_default='1.0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='DRAFT'),
        sa.Column('replaces_rate_id', sa.String(), sa.ForeignKey('cost_rates.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('confirmed_by', sa.String(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.CheckConstraint('rate_value >= 0', name='ck_cost_rates_rate_val_nonneg'),
        sa.CheckConstraint("status IN ('DRAFT', 'CONFIRMED', 'SUPERSEDED')", name='ck_cost_rates_status'),
        sa.CheckConstraint("source_type IN ('OFFICIAL_SCHEDULE', 'PROJECT_SPECIFIC', 'USER_PROVIDED', 'ASSUMPTION_BASED')", name='ck_cost_rates_source_type'),
        sa.CheckConstraint("length(trim(rate_code)) > 0", name='ck_cost_rates_code_nonempty'),
        sa.CheckConstraint("length(trim(unit)) > 0", name='ck_cost_rates_unit_nonempty'),
        sa.CheckConstraint("length(trim(currency)) > 0", name='ck_cost_rates_currency_nonempty'),
        sa.CheckConstraint("status != 'CONFIRMED' OR (confirmed_by IS NOT NULL AND confirmed_at IS NOT NULL)", name='ck_cost_rates_confirmed_fields'),
        sa.CheckConstraint("project_id IS NOT NULL OR (source_document_id IS NULL AND source_evidence_id IS NULL)", name='ck_cost_rates_global_no_doc'),
        sa.CheckConstraint("source_evidence_id IS NULL OR source_document_id IS NOT NULL", name='ck_cost_rates_evidence_requires_doc'),
        sa.CheckConstraint("replaces_rate_id IS NULL OR replaces_rate_id != id", name='ck_cost_rates_no_self_replace'),
    )
    op.create_index('ix_cost_rates_project', 'cost_rates', ['project_id'])
    op.create_index('ix_cost_rates_code', 'cost_rates', ['rate_code'])
    op.create_index('ix_cost_rates_status', 'cost_rates', ['status'])
    # Global active confirmed uniqueness
    op.create_index(
        'uq_cost_rates_global_active_code',
        'cost_rates',
        ['rate_code'],
        unique=True,
        postgresql_where=sa.text("project_id IS NULL AND status = 'CONFIRMED'")
    )
    # Project-specific active confirmed uniqueness
    op.create_index(
        'uq_cost_rates_project_active_code',
        'cost_rates',
        ['project_id', 'rate_code'],
        unique=True,
        postgresql_where=sa.text("project_id IS NOT NULL AND status = 'CONFIRMED'")
    )

    # 2. Create cost_calculations table
    op.create_table(
        'cost_calculations',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cost_rate_id', sa.String(), sa.ForeignKey('cost_rates.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('quantity_basis', sa.String(length=30), nullable=False),
        sa.Column('boq_item_id', sa.String(), sa.ForeignKey('boq_items.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('calculation_id', sa.String(), sa.ForeignKey('engineering_calculations.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('reconciliation_id', sa.String(), sa.ForeignKey('boq_reconciliations.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('reconciliation_decision', sa.String(length=30), nullable=True),
        sa.Column('decision_reason', sa.Text(), nullable=True),
        sa.Column('decided_by', sa.String(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('quantity_value', sa.Numeric(18, 6), nullable=False),
        sa.Column('quantity_unit', sa.String(length=50), nullable=False),
        sa.Column('rate_value', sa.Numeric(18, 6), nullable=False),
        sa.Column('rate_unit', sa.String(length=50), nullable=False),
        sa.Column('rate_version', sa.String(length=50), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('total_cost', sa.Numeric(18, 6), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='CALCULATED'),
        sa.Column('formula_identifier', sa.String(length=100), nullable=False, server_default='DIRECT_RATE_VALUATION'),
        sa.Column('formula_expression', sa.String(length=255), nullable=False, server_default='total_cost = quantity * rate'),
        sa.Column('algorithm_version', sa.String(length=50), nullable=False, server_default='1.0'),
        sa.Column('provenance_json', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.CheckConstraint('quantity_value >= 0', name='ck_cost_calc_qty_val_nonneg'),
        sa.CheckConstraint('rate_value >= 0', name='ck_cost_calc_rate_val_nonneg'),
        sa.CheckConstraint('total_cost >= 0', name='ck_cost_calc_total_cost_nonneg'),
        sa.CheckConstraint("quantity_basis IN ('BOQ_STATED', 'ENGINEERING_CALCULATED', 'VERIFIED_RECONCILED')", name='ck_cost_calc_qty_basis'),
        sa.CheckConstraint("status IN ('CALCULATED', 'SUPERSEDED')", name='ck_cost_calc_status'),
        sa.CheckConstraint(
            "(quantity_basis = 'BOQ_STATED' AND boq_item_id IS NOT NULL AND calculation_id IS NULL AND reconciliation_id IS NULL AND reconciliation_decision IS NULL AND decision_reason IS NULL AND decided_by IS NULL AND decided_at IS NULL) OR "
            "(quantity_basis = 'ENGINEERING_CALCULATED' AND calculation_id IS NOT NULL AND boq_item_id IS NULL AND reconciliation_id IS NULL AND reconciliation_decision IS NULL AND decision_reason IS NULL AND decided_by IS NULL AND decided_at IS NULL) OR "
            "(quantity_basis = 'VERIFIED_RECONCILED' AND reconciliation_id IS NOT NULL AND boq_item_id IS NULL AND calculation_id IS NULL AND reconciliation_decision IS NOT NULL AND reconciliation_decision IN ('ACCEPT_MATCH', 'ACCEPT_CALCULATED', 'ACCEPT_BOQ') AND decision_reason IS NOT NULL AND decided_by IS NOT NULL AND decided_at IS NOT NULL)",
            name='ck_cost_calc_basis_sources'
        ),
    )
    op.create_index('ix_cost_calc_project', 'cost_calculations', ['project_id'])
    op.create_index('ix_cost_calc_rate', 'cost_calculations', ['cost_rate_id'])
    op.create_index('ix_cost_calc_status', 'cost_calculations', ['status'])
    op.create_index('ix_cost_calc_basis', 'cost_calculations', ['quantity_basis'])
    # Active 1:1 identity constraints
    op.create_index(
        'uq_cost_calc_active_boq',
        'cost_calculations',
        ['boq_item_id'],
        unique=True,
        postgresql_where=sa.text("status = 'CALCULATED' AND quantity_basis = 'BOQ_STATED'")
    )
    op.create_index(
        'uq_cost_calc_active_eng',
        'cost_calculations',
        ['calculation_id'],
        unique=True,
        postgresql_where=sa.text("status = 'CALCULATED' AND quantity_basis = 'ENGINEERING_CALCULATED'")
    )
    op.create_index(
        'uq_cost_calc_active_rec',
        'cost_calculations',
        ['reconciliation_id'],
        unique=True,
        postgresql_where=sa.text("status = 'CALCULATED' AND quantity_basis = 'VERIFIED_RECONCILED'")
    )

    # 3. Triggers & Functions
    # 3.1 Validate cost rate document scope and replaces_rate
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_validate_cost_rate_source()
        RETURNS TRIGGER AS $$
        DECLARE
            doc_rec RECORD;
            ev_rec RECORD;
            rep_rec RECORD;
        BEGIN
            -- Global rates cannot depend on project-owned documents
            IF NEW.project_id IS NULL THEN
                IF NEW.source_document_id IS NOT NULL OR NEW.source_evidence_id IS NOT NULL THEN
                    RAISE EXCEPTION 'Global cost rates cannot reference project-owned documents or evidence.';
                END IF;
            ELSE
                -- Project-specific rates: validate document belongs to same project
                IF NEW.source_document_id IS NOT NULL THEN
                    SELECT id, project_id INTO doc_rec FROM documents WHERE id = NEW.source_document_id;
                    IF NOT FOUND THEN
                        RAISE EXCEPTION 'Referenced source document % does not exist.', NEW.source_document_id;
                    END IF;
                    IF doc_rec.project_id <> NEW.project_id THEN
                        RAISE EXCEPTION 'Cost rate source document does not belong to the project.';
                    END IF;
                END IF;

                IF NEW.source_evidence_id IS NOT NULL THEN
                    IF NEW.source_document_id IS NULL THEN
                        RAISE EXCEPTION 'source_evidence_id requires source_document_id to be specified.';
                    END IF;
                    SELECT id, document_id INTO ev_rec FROM evidence WHERE id = NEW.source_evidence_id;
                    IF NOT FOUND THEN
                        RAISE EXCEPTION 'Referenced source evidence % does not exist.', NEW.source_evidence_id;
                    END IF;
                    IF ev_rec.document_id <> NEW.source_document_id THEN
                        RAISE EXCEPTION 'Referenced source evidence does not belong to the rate source document.';
                    END IF;
                END IF;
            END IF;

            -- Validate replaced rate scope, code, and status
            IF NEW.replaces_rate_id IS NOT NULL THEN
                IF NEW.replaces_rate_id = NEW.id THEN
                    RAISE EXCEPTION 'A cost rate cannot replace itself.';
                END IF;
                SELECT id, project_id, rate_code, status INTO rep_rec FROM cost_rates WHERE id = NEW.replaces_rate_id;
                IF NOT FOUND THEN
                    RAISE EXCEPTION 'Replaced cost rate % does not exist.', NEW.replaces_rate_id;
                END IF;
                IF TG_OP = 'INSERT' AND rep_rec.status <> 'CONFIRMED' THEN
                    RAISE EXCEPTION 'A new rate version can only replace a CONFIRMED rate, got %.', rep_rec.status;
                ELSIF TG_OP = 'UPDATE' AND rep_rec.status NOT IN ('CONFIRMED', 'SUPERSEDED') THEN
                    RAISE EXCEPTION 'A new rate version can only replace a CONFIRMED rate, got %.', rep_rec.status;
                END IF;
                IF rep_rec.rate_code <> NEW.rate_code THEN
                    RAISE EXCEPTION 'New rate version must maintain the same rate_code.';
                END IF;
                IF (rep_rec.project_id IS NULL AND NEW.project_id IS NOT NULL) OR
                   (rep_rec.project_id IS NOT NULL AND NEW.project_id IS NULL) OR
                   (rep_rec.project_id <> NEW.project_id) THEN
                    RAISE EXCEPTION 'New rate version cannot change project scope.';
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_validate_cost_rate_source
        BEFORE INSERT OR UPDATE ON cost_rates
        FOR EACH ROW
        EXECUTE FUNCTION fn_validate_cost_rate_source();
    """)

    # 3.2 Protect cost rate lifecycle and confirmed immutability
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_protect_cost_rate()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF OLD.status IN ('CONFIRMED', 'SUPERSEDED') THEN
                    RAISE EXCEPTION 'Confirmed and superseded cost rates cannot be deleted.';
                END IF;
                RETURN OLD;
            ELSIF TG_OP = 'UPDATE' THEN
                -- Validate status transitions: ONLY DRAFT -> CONFIRMED and CONFIRMED -> SUPERSEDED
                IF OLD.status <> NEW.status THEN
                    IF OLD.status = 'DRAFT' AND NEW.status = 'CONFIRMED' THEN
                        NULL;
                    ELSIF OLD.status = 'CONFIRMED' AND NEW.status = 'SUPERSEDED' THEN
                        NULL;
                    ELSE
                        RAISE EXCEPTION 'Illegal cost rate status transition from % to %.', OLD.status, NEW.status;
                    END IF;
                END IF;

                -- Contractual fields immutability once CONFIRMED or SUPERSEDED
                IF OLD.status IN ('CONFIRMED', 'SUPERSEDED') THEN
                    IF OLD.id <> NEW.id OR
                       OLD.project_id IS DISTINCT FROM NEW.project_id OR
                       OLD.rate_code <> NEW.rate_code OR
                       OLD.description <> NEW.description OR
                       OLD.unit <> NEW.unit OR
                       OLD.rate_value <> NEW.rate_value OR
                       OLD.currency <> NEW.currency OR
                       OLD.source_type <> NEW.source_type OR
                       OLD.source_reference <> NEW.source_reference OR
                       OLD.source_document_id IS DISTINCT FROM NEW.source_document_id OR
                       OLD.source_evidence_id IS DISTINCT FROM NEW.source_evidence_id OR
                       OLD.version <> NEW.version OR
                       OLD.replaces_rate_id IS DISTINCT FROM NEW.replaces_rate_id OR
                       OLD.created_by <> NEW.created_by OR
                       OLD.created_at <> NEW.created_at OR
                       OLD.confirmed_by IS DISTINCT FROM NEW.confirmed_by OR
                       OLD.confirmed_at IS DISTINCT FROM NEW.confirmed_at OR
                       OLD.metadata_json::TEXT IS DISTINCT FROM NEW.metadata_json::TEXT THEN
                        RAISE EXCEPTION 'Confirmed or superseded cost rate contractual fields cannot be modified.';
                    END IF;
                END IF;

                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_protect_cost_rate
        BEFORE UPDATE OR DELETE ON cost_rates
        FOR EACH ROW
        EXECUTE FUNCTION fn_protect_cost_rate();
    """)

    # 3.3 Validate cost calculation cross-project integrity & snapshot consistency
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_validate_cost_calc_cross_project()
        RETURNS TRIGGER AS $$
        DECLARE
            rate_rec RECORD;
            boq_rec RECORD;
            calc_rec RECORD;
            rec_rec RECORD;
        BEGIN
            -- Validate rate
            SELECT id, project_id, rate_value, currency, unit, version, status INTO rate_rec FROM cost_rates WHERE id = NEW.cost_rate_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'Referenced cost rate % does not exist.', NEW.cost_rate_id;
            END IF;

            -- Valuation can only be created against CONFIRMED rate
            IF TG_OP = 'INSERT' AND rate_rec.status <> 'CONFIRMED' THEN
                RAISE EXCEPTION 'Cost calculation can only be created against a CONFIRMED cost rate, got %.', rate_rec.status;
            END IF;

            IF rate_rec.project_id IS NOT NULL AND rate_rec.project_id <> NEW.project_id THEN
                RAISE EXCEPTION 'Project-specific cost rate does not belong to calculation project.';
            END IF;

            -- Rate snapshot consistency
            IF NEW.currency <> rate_rec.currency THEN
                RAISE EXCEPTION 'Cost calculation currency must match rate currency.';
            END IF;

            IF NEW.rate_value <> rate_rec.rate_value THEN
                RAISE EXCEPTION 'Cost calculation rate_value must match rate snapshot.';
            END IF;

            IF NEW.rate_unit <> rate_rec.unit THEN
                RAISE EXCEPTION 'Cost calculation rate_unit must match rate snapshot unit.';
            END IF;

            IF NEW.rate_version <> rate_rec.version THEN
                RAISE EXCEPTION 'Cost calculation rate_version must match rate snapshot version.';
            END IF;

            -- Exact arithmetic check: total_cost = quantity * rate
            IF NEW.total_cost <> ROUND(NEW.quantity_value * NEW.rate_value, 6) THEN
                RAISE EXCEPTION 'Cost calculation total_cost must equal quantity * rate.';
            END IF;

            -- Validate quantity source by basis
            IF NEW.quantity_basis = 'BOQ_STATED' THEN
                SELECT id, project_id, stated_quantity, unit INTO boq_rec FROM boq_items WHERE id = NEW.boq_item_id;
                IF NOT FOUND THEN
                    RAISE EXCEPTION 'Referenced BOQ item % does not exist.', NEW.boq_item_id;
                END IF;
                IF boq_rec.project_id <> NEW.project_id THEN
                    RAISE EXCEPTION 'BOQ item does not belong to calculation project.';
                END IF;
                IF NEW.quantity_value <> boq_rec.stated_quantity THEN
                    RAISE EXCEPTION 'Calculation quantity does not match BOQ stated quantity.';
                END IF;
                IF NEW.quantity_unit <> boq_rec.unit THEN
                    RAISE EXCEPTION 'Calculation unit does not match BOQ unit.';
                END IF;
            ELSIF NEW.quantity_basis = 'ENGINEERING_CALCULATED' THEN
                SELECT id, project_id, result_value, result_unit INTO calc_rec FROM engineering_calculations WHERE id = NEW.calculation_id;
                IF NOT FOUND THEN
                    RAISE EXCEPTION 'Referenced engineering calculation % does not exist.', NEW.calculation_id;
                END IF;
                IF calc_rec.project_id <> NEW.project_id THEN
                    RAISE EXCEPTION 'Engineering calculation does not belong to calculation project.';
                END IF;
                IF NEW.quantity_value <> calc_rec.result_value THEN
                    RAISE EXCEPTION 'Calculation quantity does not match engineering calculation result value.';
                END IF;
                IF NEW.quantity_unit <> calc_rec.result_unit THEN
                    RAISE EXCEPTION 'Calculation unit does not match engineering calculation result unit.';
                END IF;
            ELSIF NEW.quantity_basis = 'VERIFIED_RECONCILED' THEN
                SELECT id, project_id, discrepancy_status, calculated_quantity, calculated_unit, boq_quantity, boq_unit
                INTO rec_rec FROM boq_reconciliations WHERE id = NEW.reconciliation_id;
                IF NOT FOUND THEN
                    RAISE EXCEPTION 'Referenced reconciliation % does not exist.', NEW.reconciliation_id;
                END IF;
                IF rec_rec.project_id <> NEW.project_id THEN
                    RAISE EXCEPTION 'Reconciliation does not belong to calculation project.';
                END IF;

                IF NEW.reconciliation_decision = 'ACCEPT_MATCH' THEN
                    IF rec_rec.discrepancy_status <> 'MATCH' THEN
                        RAISE EXCEPTION 'ACCEPT_MATCH decision only valid when discrepancy status is MATCH, got %.', rec_rec.discrepancy_status;
                    END IF;
                    IF NEW.quantity_value <> rec_rec.calculated_quantity THEN
                        RAISE EXCEPTION 'Calculation quantity does not match reconciliation calculated quantity for ACCEPT_MATCH.';
                    END IF;
                    IF NEW.quantity_unit <> rec_rec.calculated_unit THEN
                        RAISE EXCEPTION 'Calculation unit does not match reconciliation calculated unit for ACCEPT_MATCH.';
                    END IF;
                ELSIF NEW.reconciliation_decision = 'ACCEPT_CALCULATED' THEN
                    IF NEW.quantity_value <> rec_rec.calculated_quantity THEN
                        RAISE EXCEPTION 'Calculation quantity does not match reconciliation calculated quantity for ACCEPT_CALCULATED.';
                    END IF;
                    IF NEW.quantity_unit <> rec_rec.calculated_unit THEN
                        RAISE EXCEPTION 'Calculation unit does not match reconciliation calculated unit for ACCEPT_CALCULATED.';
                    END IF;
                ELSIF NEW.reconciliation_decision = 'ACCEPT_BOQ' THEN
                    IF NEW.quantity_value <> rec_rec.boq_quantity THEN
                        RAISE EXCEPTION 'Calculation quantity does not match reconciliation boq quantity for ACCEPT_BOQ.';
                    END IF;
                    IF NEW.quantity_unit <> rec_rec.boq_unit THEN
                        RAISE EXCEPTION 'Calculation unit does not match reconciliation boq unit for ACCEPT_BOQ.';
                    END IF;
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_validate_cost_calc_cross_project
        BEFORE INSERT OR UPDATE ON cost_calculations
        FOR EACH ROW
        EXECUTE FUNCTION fn_validate_cost_calc_cross_project();
    """)

    # 3.4 Protect cost calculation mathematical immutability and prevent deletion
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_protect_cost_calculation()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Cost calculations are immutable audit records and cannot be deleted.';
            ELSIF TG_OP = 'UPDATE' THEN
                -- Only CALCULATED -> SUPERSEDED is allowed
                IF OLD.status <> NEW.status THEN
                    IF OLD.status = 'CALCULATED' AND NEW.status = 'SUPERSEDED' THEN
                        NULL;
                    ELSE
                        RAISE EXCEPTION 'Illegal cost calculation status transition from % to %.', OLD.status, NEW.status;
                    END IF;
                END IF;

                -- All 25 historical columns must be strictly immutable
                IF OLD.id <> NEW.id OR
                   OLD.project_id <> NEW.project_id OR
                   OLD.cost_rate_id <> NEW.cost_rate_id OR
                   OLD.quantity_basis <> NEW.quantity_basis OR
                   OLD.boq_item_id IS DISTINCT FROM NEW.boq_item_id OR
                   OLD.calculation_id IS DISTINCT FROM NEW.calculation_id OR
                   OLD.reconciliation_id IS DISTINCT FROM NEW.reconciliation_id OR
                   OLD.reconciliation_decision IS DISTINCT FROM NEW.reconciliation_decision OR
                   OLD.decision_reason IS DISTINCT FROM NEW.decision_reason OR
                   OLD.decided_by IS DISTINCT FROM NEW.decided_by OR
                   OLD.decided_at IS DISTINCT FROM NEW.decided_at OR
                   OLD.quantity_value <> NEW.quantity_value OR
                   OLD.quantity_unit <> NEW.quantity_unit OR
                   OLD.rate_value <> NEW.rate_value OR
                   OLD.rate_unit <> NEW.rate_unit OR
                   OLD.rate_version <> NEW.rate_version OR
                   OLD.currency <> NEW.currency OR
                   OLD.total_cost <> NEW.total_cost OR
                   OLD.formula_identifier <> NEW.formula_identifier OR
                   OLD.formula_expression <> NEW.formula_expression OR
                   OLD.algorithm_version <> NEW.algorithm_version OR
                   OLD.created_by <> NEW.created_by OR
                   OLD.created_at <> NEW.created_at OR
                   OLD.provenance_json::TEXT IS DISTINCT FROM NEW.provenance_json::TEXT OR
                   OLD.metadata_json::TEXT IS DISTINCT FROM NEW.metadata_json::TEXT THEN
                    RAISE EXCEPTION 'Mathematical and provenance fields of cost calculation cannot be modified.';
                END IF;

                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_protect_cost_calculation
        BEFORE UPDATE OR DELETE ON cost_calculations
        FOR EACH ROW
        EXECUTE FUNCTION fn_protect_cost_calculation();
    """)


def downgrade() -> None:
    """Downgrade schema - Phase 1K."""
    # 1. Drop triggers and functions
    op.execute("DROP TRIGGER IF EXISTS trg_protect_cost_calculation ON cost_calculations;")
    op.execute("DROP FUNCTION IF EXISTS fn_protect_cost_calculation();")

    op.execute("DROP TRIGGER IF EXISTS trg_validate_cost_calc_cross_project ON cost_calculations;")
    op.execute("DROP FUNCTION IF EXISTS fn_validate_cost_calc_cross_project();")

    op.execute("DROP TRIGGER IF EXISTS trg_protect_cost_rate ON cost_rates;")
    op.execute("DROP FUNCTION IF EXISTS fn_protect_cost_rate();")

    op.execute("DROP TRIGGER IF EXISTS trg_validate_cost_rate_source ON cost_rates;")
    op.execute("DROP FUNCTION IF EXISTS fn_validate_cost_rate_source();")

    # 2. Drop tables
    op.drop_table('cost_calculations')
    op.drop_table('cost_rates')
