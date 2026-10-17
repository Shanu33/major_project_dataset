"""phase_1f_rule_based_estimations

Revision ID: 53bb531a7d4f
Revises: 8561c2714e60
Create Date: 2026-10-04 20:22:18.559552

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '53bb531a7d4f'
down_revision: Union[str, Sequence[str], None] = '8561c2714e60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Create rules table
    op.create_table(
        'rules',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('rule_code', sa.String(), nullable=False),
        sa.Column('rule_name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('rule_category', sa.String(), nullable=False),
        sa.Column('input_unit', sa.String(), nullable=False),
        sa.Column('output_unit', sa.String(), nullable=False),
        sa.Column('formula_identifier', sa.String(), nullable=False),
        sa.Column('formula_expression', sa.String(), nullable=False),
        sa.Column('parameters_json', sa.JSON(), nullable=False),
        sa.Column('source_reference', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=False, server_default='1.0'),
        sa.Column('status', sa.String(), nullable=False, server_default='ACTIVE'),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )
    op.create_index('uq_rule_code_version', 'rules', ['rule_code', 'version'], unique=True)
    op.create_index('ix_rules_status', 'rules', ['status'])

    # 2. Create rule_based_estimations table
    op.create_table(
        'rule_based_estimations',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('engineering_element_id', sa.String(), sa.ForeignKey('engineering_elements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('calculation_id', sa.String(), sa.ForeignKey('engineering_calculations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_id', sa.String(), sa.ForeignKey('rules.id'), nullable=False),
        sa.Column('rule_version', sa.String(), nullable=False),
        sa.Column('estimation_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='ESTIMATED'),
        sa.Column('input_value', sa.Numeric(18, 6), nullable=False),
        sa.Column('input_unit', sa.String(), nullable=False),
        sa.Column('result_value', sa.Numeric(18, 6), nullable=False),
        sa.Column('result_unit', sa.String(), nullable=False),
        sa.Column('parameters_json', sa.JSON(), nullable=False),
        sa.Column('assumptions_json', sa.JSON(), nullable=False),
        sa.Column('provenance_json', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )
    op.create_index('ix_estimations_project', 'rule_based_estimations', ['project_id'])
    op.create_index('ix_estimations_element', 'rule_based_estimations', ['engineering_element_id'])
    op.create_index('ix_estimations_calc', 'rule_based_estimations', ['calculation_id'])
    op.create_index('ix_estimations_rule', 'rule_based_estimations', ['rule_id'])

    # 3. Create immutability trigger for rule_based_estimations
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_prevent_estimation_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Rule-based estimation records are immutable and cannot be deleted.';
            ELSIF TG_OP = 'UPDATE' THEN
                IF OLD.status = 'ESTIMATED' AND NEW.status = 'SUPERSEDED' THEN
                    IF OLD.id = NEW.id AND
                       OLD.project_id = NEW.project_id AND
                       OLD.engineering_element_id = NEW.engineering_element_id AND
                       OLD.calculation_id = NEW.calculation_id AND
                       OLD.rule_id = NEW.rule_id AND
                       OLD.rule_version = NEW.rule_version AND
                       OLD.estimation_type = NEW.estimation_type AND
                       OLD.input_value IS NOT DISTINCT FROM NEW.input_value AND
                       OLD.input_unit IS NOT DISTINCT FROM NEW.input_unit AND
                       OLD.result_value IS NOT DISTINCT FROM NEW.result_value AND
                       OLD.result_unit IS NOT DISTINCT FROM NEW.result_unit AND
                       (OLD.parameters_json::text = NEW.parameters_json::text) AND
                       (OLD.assumptions_json::text = NEW.assumptions_json::text) AND
                       (OLD.provenance_json::text = NEW.provenance_json::text) AND
                       OLD.created_by = NEW.created_by AND
                       OLD.created_at = NEW.created_at THEN
                        RETURN NEW;
                    ELSE
                        RAISE EXCEPTION 'Cannot modify estimation inputs, parameters, or results during status change to SUPERSEDED.';
                    END IF;
                ELSE
                    RAISE EXCEPTION 'Rule-based estimations are immutable. Only status transition from ESTIMATED to SUPERSEDED is permitted.';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER prevent_estimation_modification_trg
        BEFORE UPDATE OR DELETE ON rule_based_estimations
        FOR EACH ROW
        EXECUTE FUNCTION trg_prevent_estimation_modification();
    """)

    # 4. Create trigger to prevent mutation of referenced rules
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_prevent_active_rule_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF EXISTS (SELECT 1 FROM rule_based_estimations WHERE rule_id = OLD.id) THEN
                    RAISE EXCEPTION 'Cannot delete rule version that is referenced by estimation records.';
                END IF;
            ELSIF TG_OP = 'UPDATE' THEN
                IF (OLD.formula_expression <> NEW.formula_expression OR
                    OLD.formula_identifier <> NEW.formula_identifier OR
                    OLD.rule_code <> NEW.rule_code OR
                    OLD.version <> NEW.version) THEN
                    IF EXISTS (SELECT 1 FROM rule_based_estimations WHERE rule_id = OLD.id) THEN
                        RAISE EXCEPTION 'Cannot modify formula or identity of a rule version referenced by existing estimations. Create a new version instead.';
                    END IF;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER prevent_rule_modification_trg
        BEFORE UPDATE OR DELETE ON rules
        FOR EACH ROW
        EXECUTE FUNCTION trg_prevent_active_rule_modification();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS prevent_rule_modification_trg ON rules;")
    op.execute("DROP FUNCTION IF EXISTS trg_prevent_active_rule_modification();")

    op.execute("DROP TRIGGER IF EXISTS prevent_estimation_modification_trg ON rule_based_estimations;")
    op.execute("DROP FUNCTION IF EXISTS trg_prevent_estimation_modification();")

    op.drop_index('ix_estimations_rule', table_name='rule_based_estimations')
    op.drop_index('ix_estimations_calc', table_name='rule_based_estimations')
    op.drop_index('ix_estimations_element', table_name='rule_based_estimations')
    op.drop_index('ix_estimations_project', table_name='rule_based_estimations')
    op.drop_table('rule_based_estimations')

    op.drop_index('ix_rules_status', table_name='rules')
    op.drop_index('uq_rule_code_version', table_name='rules')
    op.drop_table('rules')
