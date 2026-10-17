"""phase_1j_boq_reconciliation

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-10-05 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Phase 1J: BOQ Ingestion, Line Item Representation & Quantity Reconciliation."""
    # 1. Create boq_items table
    op.create_table(
        'boq_items',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', sa.String(), sa.ForeignKey('documents.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('evidence_id', sa.String(), sa.ForeignKey('evidence.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('item_code', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('stated_quantity', sa.Numeric(18, 6), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='DRAFT'),
        sa.Column('classification', sa.String(length=50), nullable=False, server_default='DOCUMENT_DERIVED'),
        sa.Column('replaces_boq_item_id', sa.String(), sa.ForeignKey('boq_items.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('provenance_json', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('confirmed_by', sa.String(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.CheckConstraint('stated_quantity >= 0', name='ck_boq_items_stated_quantity_nonneg'),
        sa.CheckConstraint("status IN ('DRAFT', 'CONFIRMED', 'SUPERSEDED')", name='ck_boq_items_status'),
        sa.CheckConstraint("length(trim(item_code)) > 0", name='ck_boq_items_item_code_nonempty'),
        sa.CheckConstraint("length(trim(unit)) > 0", name='ck_boq_items_unit_nonempty'),
        sa.CheckConstraint("status != 'CONFIRMED' OR (confirmed_by IS NOT NULL AND confirmed_at IS NOT NULL)", name='ck_boq_items_confirmed_fields'),
    )
    op.create_index('ix_boq_items_project', 'boq_items', ['project_id'])
    op.create_index('ix_boq_items_document', 'boq_items', ['document_id'])
    op.create_index('ix_boq_items_status', 'boq_items', ['status'])
    op.create_index(
        'uq_boq_items_doc_item_code',
        'boq_items',
        ['document_id', 'item_code'],
        unique=True,
        postgresql_where=sa.text("status IN ('DRAFT', 'CONFIRMED')")
    )

    # 2. Create boq_calculation_mappings table
    op.create_table(
        'boq_calculation_mappings',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('boq_item_id', sa.String(), sa.ForeignKey('boq_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('calculation_id', sa.String(), sa.ForeignKey('engineering_calculations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('mapping_type', sa.String(length=20), nullable=False, server_default='DIRECT'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PROPOSED'),
        sa.Column('verified_by', sa.String(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.CheckConstraint("mapping_type = 'DIRECT'", name='ck_boq_mappings_type_direct'),
        sa.CheckConstraint("status IN ('PROPOSED', 'VERIFIED', 'REJECTED', 'SUPERSEDED')", name='ck_boq_mappings_status'),
        sa.CheckConstraint("status != 'VERIFIED' OR (verified_by IS NOT NULL AND verified_at IS NOT NULL)", name='ck_boq_mappings_verified_fields'),
        sa.CheckConstraint("status != 'REJECTED' OR (verified_by IS NOT NULL AND verified_at IS NOT NULL AND rejection_reason IS NOT NULL AND length(trim(rejection_reason)) > 0)", name='ck_boq_mappings_rejected_fields'),
    )
    op.create_index('ix_boq_mappings_project', 'boq_calculation_mappings', ['project_id'])
    op.create_index('ix_boq_mappings_boq_item', 'boq_calculation_mappings', ['boq_item_id'])
    op.create_index('ix_boq_mappings_calculation', 'boq_calculation_mappings', ['calculation_id'])
    op.create_index('ix_boq_mappings_status', 'boq_calculation_mappings', ['status'])
    op.create_index(
        'uq_boq_mappings_active_boq',
        'boq_calculation_mappings',
        ['boq_item_id'],
        unique=True,
        postgresql_where=sa.text("status IN ('PROPOSED', 'VERIFIED')")
    )
    op.create_index(
        'uq_boq_mappings_active_calc',
        'boq_calculation_mappings',
        ['calculation_id'],
        unique=True,
        postgresql_where=sa.text("status IN ('PROPOSED', 'VERIFIED')")
    )

    # 3. Create boq_reconciliations table
    op.create_table(
        'boq_reconciliations',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('mapping_id', sa.String(), sa.ForeignKey('boq_calculation_mappings.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('boq_item_id', sa.String(), sa.ForeignKey('boq_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('calculation_id', sa.String(), sa.ForeignKey('engineering_calculations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('boq_quantity', sa.Numeric(18, 6), nullable=False),
        sa.Column('boq_unit', sa.String(length=50), nullable=False),
        sa.Column('calculated_quantity', sa.Numeric(18, 6), nullable=False),
        sa.Column('calculated_unit', sa.String(length=50), nullable=False),
        sa.Column('quantity_delta', sa.Numeric(18, 6), nullable=True),
        sa.Column('variance_percentage', sa.Numeric(18, 6), nullable=True),
        sa.Column('tolerance_threshold', sa.Numeric(18, 6), nullable=False, server_default='0.000000'),
        sa.Column('discrepancy_status', sa.String(length=30), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='CALCULATED'),
        sa.Column('algorithm_version', sa.String(length=50), nullable=False, server_default='1.0'),
        sa.Column('provenance_json', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.CheckConstraint('boq_quantity >= 0', name='ck_boq_reconciliations_boq_qty_nonneg'),
        sa.CheckConstraint('calculated_quantity >= 0', name='ck_boq_reconciliations_calc_qty_nonneg'),
        sa.CheckConstraint('tolerance_threshold >= 0', name='ck_boq_reconciliations_tolerance_nonneg'),
        sa.CheckConstraint("discrepancy_status IN ('MATCH', 'OVER_CALCULATED', 'UNDER_CALCULATED', 'UNIT_MISMATCH')", name='ck_boq_reconciliations_discrepancy_status'),
        sa.CheckConstraint("status IN ('CALCULATED', 'SUPERSEDED')", name='ck_boq_reconciliations_status'),
    )
    op.create_index('ix_boq_reconciliations_project', 'boq_reconciliations', ['project_id'])
    op.create_index('ix_boq_reconciliations_mapping', 'boq_reconciliations', ['mapping_id'])
    op.create_index('ix_boq_reconciliations_boq_item', 'boq_reconciliations', ['boq_item_id'])
    op.create_index('ix_boq_reconciliations_calculation', 'boq_reconciliations', ['calculation_id'])
    op.create_index('ix_boq_reconciliations_status', 'boq_reconciliations', ['status'])
    op.create_index('ix_boq_reconciliations_discrepancy', 'boq_reconciliations', ['discrepancy_status'])
    op.create_index(
        'uq_boq_reconciliations_active_mapping',
        'boq_reconciliations',
        ['mapping_id'],
        unique=True,
        postgresql_where=sa.text("status = 'CALCULATED'")
    )

    # 4. Triggers & Functions
    # 4.1 Validate BOQ item document and evidence
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_validate_boq_item_document()
        RETURNS TRIGGER AS $$
        DECLARE
            doc_rec RECORD;
            ev_rec RECORD;
        BEGIN
            SELECT id, project_id, document_type, classified_document_type
            INTO doc_rec
            FROM documents
            WHERE id = NEW.document_id;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Referenced document % does not exist.', NEW.document_id;
            END IF;

            IF doc_rec.project_id <> NEW.project_id THEN
                RAISE EXCEPTION 'BOQ item document does not belong to the project.';
            END IF;

            IF doc_rec.document_type <> 'BOQ' AND (doc_rec.classified_document_type IS NULL OR doc_rec.classified_document_type <> 'BOQ') THEN
                RAISE EXCEPTION 'Referenced document is not a BOQ document.';
            END IF;

            IF NEW.evidence_id IS NOT NULL THEN
                SELECT id, document_id
                INTO ev_rec
                FROM evidence
                WHERE id = NEW.evidence_id;

                IF NOT FOUND THEN
                    RAISE EXCEPTION 'Referenced evidence % does not exist.', NEW.evidence_id;
                END IF;

                IF ev_rec.document_id <> NEW.document_id THEN
                    RAISE EXCEPTION 'Referenced evidence does not belong to the BOQ item document.';
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_validate_boq_item_document
        BEFORE INSERT OR UPDATE ON boq_items
        FOR EACH ROW
        EXECUTE FUNCTION fn_validate_boq_item_document();
    """)

    # 4.2 Protect BOQ item lifecycle and contractual immutability
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_protect_boq_item()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF OLD.status IN ('CONFIRMED', 'SUPERSEDED') THEN
                    RAISE EXCEPTION 'Confirmed and superseded BOQ items cannot be deleted.';
                END IF;
                RETURN OLD;
            ELSIF TG_OP = 'UPDATE' THEN
                -- Validate status transitions
                IF OLD.status <> NEW.status THEN
                    IF OLD.status = 'DRAFT' AND NEW.status IN ('CONFIRMED', 'SUPERSEDED') THEN
                        NULL;
                    ELSIF OLD.status = 'CONFIRMED' AND NEW.status = 'SUPERSEDED' THEN
                        NULL;
                    ELSE
                        RAISE EXCEPTION 'Illegal BOQ item status transition from % to %.', OLD.status, NEW.status;
                    END IF;
                END IF;

                -- Contractual fields immutability once CONFIRMED or SUPERSEDED
                IF OLD.status IN ('CONFIRMED', 'SUPERSEDED') THEN
                    IF OLD.id <> NEW.id OR
                       OLD.project_id <> NEW.project_id OR
                       OLD.document_id <> NEW.document_id OR
                       OLD.evidence_id IS DISTINCT FROM NEW.evidence_id OR
                       OLD.item_code <> NEW.item_code OR
                       OLD.description <> NEW.description OR
                       OLD.unit <> NEW.unit OR
                       OLD.stated_quantity <> NEW.stated_quantity OR
                       OLD.classification <> NEW.classification OR
                       OLD.replaces_boq_item_id IS DISTINCT FROM NEW.replaces_boq_item_id OR
                       OLD.created_by <> NEW.created_by OR
                       OLD.created_at <> NEW.created_at THEN
                        RAISE EXCEPTION 'Confirmed or superseded BOQ item contractual fields cannot be modified.';
                    END IF;
                END IF;

                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_protect_boq_item
        BEFORE UPDATE OR DELETE ON boq_items
        FOR EACH ROW
        EXECUTE FUNCTION fn_protect_boq_item();
    """)

    # 4.3 Validate BOQ mapping cross-project alignment
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_validate_boq_mapping_cross_project()
        RETURNS TRIGGER AS $$
        DECLARE
            boq_rec RECORD;
            calc_rec RECORD;
        BEGIN
            SELECT id, project_id, status
            INTO boq_rec
            FROM boq_items
            WHERE id = NEW.boq_item_id;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Referenced BOQ item % does not exist.', NEW.boq_item_id;
            END IF;

            IF boq_rec.project_id <> NEW.project_id THEN
                RAISE EXCEPTION 'BOQ item does not belong to the mapping project.';
            END IF;

            SELECT id, project_id, status
            INTO calc_rec
            FROM engineering_calculations
            WHERE id = NEW.calculation_id;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Referenced calculation % does not exist.', NEW.calculation_id;
            END IF;

            IF calc_rec.project_id <> NEW.project_id THEN
                RAISE EXCEPTION 'Engineering calculation does not belong to the mapping project.';
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_validate_boq_mapping_cross_project
        BEFORE INSERT OR UPDATE ON boq_calculation_mappings
        FOR EACH ROW
        EXECUTE FUNCTION fn_validate_boq_mapping_cross_project();
    """)

    # 4.4 Protect BOQ mapping lifecycle and targets immutability
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_protect_boq_mapping()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF OLD.status IN ('VERIFIED', 'SUPERSEDED') THEN
                    RAISE EXCEPTION 'Verified and superseded mappings cannot be deleted.';
                END IF;
                RETURN OLD;
            ELSIF TG_OP = 'UPDATE' THEN
                -- Validate status transitions
                IF OLD.status <> NEW.status THEN
                    IF OLD.status = 'PROPOSED' AND NEW.status IN ('VERIFIED', 'REJECTED') THEN
                        NULL;
                    ELSIF OLD.status = 'VERIFIED' AND NEW.status = 'SUPERSEDED' THEN
                        NULL;
                    ELSE
                        RAISE EXCEPTION 'Illegal BOQ mapping status transition from % to %.', OLD.status, NEW.status;
                    END IF;
                END IF;

                -- Target immutability once VERIFIED or SUPERSEDED
                IF OLD.status IN ('VERIFIED', 'SUPERSEDED') THEN
                    IF OLD.id <> NEW.id OR
                       OLD.project_id <> NEW.project_id OR
                       OLD.boq_item_id <> NEW.boq_item_id OR
                       OLD.calculation_id <> NEW.calculation_id OR
                       OLD.mapping_type <> NEW.mapping_type OR
                       OLD.created_by <> NEW.created_by OR
                       OLD.created_at <> NEW.created_at THEN
                        RAISE EXCEPTION 'Verified mapping targets and immutable attributes cannot be modified.';
                    END IF;
                END IF;

                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_protect_boq_mapping
        BEFORE UPDATE OR DELETE ON boq_calculation_mappings
        FOR EACH ROW
        EXECUTE FUNCTION fn_protect_boq_mapping();
    """)

    # 4.5 Validate BOQ reconciliation cross-project alignment
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_validate_boq_reconciliation_cross_project()
        RETURNS TRIGGER AS $$
        DECLARE
            map_rec RECORD;
            boq_rec RECORD;
            calc_rec RECORD;
        BEGIN
            SELECT id, project_id, boq_item_id, calculation_id, status
            INTO map_rec
            FROM boq_calculation_mappings
            WHERE id = NEW.mapping_id;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Referenced mapping % does not exist.', NEW.mapping_id;
            END IF;

            IF map_rec.project_id <> NEW.project_id THEN
                RAISE EXCEPTION 'Mapping does not belong to reconciliation project.';
            END IF;

            IF map_rec.boq_item_id <> NEW.boq_item_id THEN
                RAISE EXCEPTION 'Reconciliation boq_item_id does not match mapping boq_item_id.';
            END IF;

            IF map_rec.calculation_id <> NEW.calculation_id THEN
                RAISE EXCEPTION 'Reconciliation calculation_id does not match mapping calculation_id.';
            END IF;

            SELECT id, project_id
            INTO boq_rec
            FROM boq_items
            WHERE id = NEW.boq_item_id;

            IF NOT FOUND OR boq_rec.project_id <> NEW.project_id THEN
                RAISE EXCEPTION 'BOQ item does not belong to reconciliation project.';
            END IF;

            SELECT id, project_id
            INTO calc_rec
            FROM engineering_calculations
            WHERE id = NEW.calculation_id;

            IF NOT FOUND OR calc_rec.project_id <> NEW.project_id THEN
                RAISE EXCEPTION 'Calculation does not belong to reconciliation project.';
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_validate_boq_reconciliation_cross_project
        BEFORE INSERT OR UPDATE ON boq_reconciliations
        FOR EACH ROW
        EXECUTE FUNCTION fn_validate_boq_reconciliation_cross_project();
    """)

    # 4.6 Protect BOQ reconciliation mathematical result immutability
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_protect_boq_reconciliation()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'BOQ reconciliations are immutable audit records and cannot be deleted.';
            ELSIF TG_OP = 'UPDATE' THEN
                -- Only CALCULATED -> SUPERSEDED is allowed
                IF OLD.status <> NEW.status THEN
                    IF OLD.status = 'CALCULATED' AND NEW.status = 'SUPERSEDED' THEN
                        NULL;
                    ELSE
                        RAISE EXCEPTION 'Illegal BOQ reconciliation status transition from % to %.', OLD.status, NEW.status;
                    END IF;
                END IF;

                -- Mathematical and structural fields must be strictly immutable
                IF OLD.id <> NEW.id OR
                   OLD.project_id <> NEW.project_id OR
                   OLD.mapping_id <> NEW.mapping_id OR
                   OLD.boq_item_id <> NEW.boq_item_id OR
                   OLD.calculation_id <> NEW.calculation_id OR
                   OLD.boq_quantity <> NEW.boq_quantity OR
                   OLD.boq_unit <> NEW.boq_unit OR
                   OLD.calculated_quantity <> NEW.calculated_quantity OR
                   OLD.calculated_unit <> NEW.calculated_unit OR
                   OLD.quantity_delta IS DISTINCT FROM NEW.quantity_delta OR
                   OLD.variance_percentage IS DISTINCT FROM NEW.variance_percentage OR
                   OLD.tolerance_threshold <> NEW.tolerance_threshold OR
                   OLD.discrepancy_status <> NEW.discrepancy_status OR
                   OLD.algorithm_version <> NEW.algorithm_version OR
                   OLD.created_by <> NEW.created_by OR
                   OLD.created_at <> NEW.created_at THEN
                    RAISE EXCEPTION 'Mathematical and provenance fields of BOQ reconciliation cannot be modified.';
                END IF;

                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_protect_boq_reconciliation
        BEFORE UPDATE OR DELETE ON boq_reconciliations
        FOR EACH ROW
        EXECUTE FUNCTION fn_protect_boq_reconciliation();
    """)


def downgrade() -> None:
    """Downgrade schema - Phase 1J."""
    # 1. Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trg_protect_boq_reconciliation ON boq_reconciliations;")
    op.execute("DROP FUNCTION IF EXISTS fn_protect_boq_reconciliation();")

    op.execute("DROP TRIGGER IF EXISTS trg_validate_boq_reconciliation_cross_project ON boq_reconciliations;")
    op.execute("DROP FUNCTION IF EXISTS fn_validate_boq_reconciliation_cross_project();")

    op.execute("DROP TRIGGER IF EXISTS trg_protect_boq_mapping ON boq_calculation_mappings;")
    op.execute("DROP FUNCTION IF EXISTS fn_protect_boq_mapping();")

    op.execute("DROP TRIGGER IF EXISTS trg_validate_boq_mapping_cross_project ON boq_calculation_mappings;")
    op.execute("DROP FUNCTION IF EXISTS fn_validate_boq_mapping_cross_project();")

    op.execute("DROP TRIGGER IF EXISTS trg_protect_boq_item ON boq_items;")
    op.execute("DROP FUNCTION IF EXISTS fn_protect_boq_item();")

    op.execute("DROP TRIGGER IF EXISTS trg_validate_boq_item_document ON boq_items;")
    op.execute("DROP FUNCTION IF EXISTS fn_validate_boq_item_document();")

    # 2. Drop tables
    op.drop_table('boq_reconciliations')
    op.drop_table('boq_calculation_mappings')
    op.drop_table('boq_items')
