"""phase_1e_deterministic_engineering_calculations

Revision ID: 8561c2714e60
Revises: 8bce11e325dd
Create Date: 2026-10-04 20:04:01.507347

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8561c2714e60'
down_revision: Union[str, Sequence[str], None] = '8bce11e325dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Create engineering_calculations table
    op.create_table(
        'engineering_calculations',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('engineering_element_id', sa.String(), sa.ForeignKey('engineering_elements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('calculation_type', sa.String(), nullable=False),
        sa.Column('calculation_version', sa.String(), nullable=False, server_default='1.0'),
        sa.Column('status', sa.String(), nullable=False, server_default='CALCULATED'),
        sa.Column('result_value', sa.Numeric(18, 6), nullable=True),
        sa.Column('result_unit', sa.String(), nullable=True),
        sa.Column('formula_identifier', sa.String(), nullable=False),
        sa.Column('formula_expression', sa.String(), nullable=False),
        sa.Column('inputs_json', sa.JSON(), nullable=False),
        sa.Column('assumptions_json', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 2. Create indexes
    op.create_index('ix_calculations_element', 'engineering_calculations', ['engineering_element_id'])
    op.create_index('ix_calculations_project', 'engineering_calculations', ['project_id'])
    op.create_index('ix_calculations_type', 'engineering_calculations', ['project_id', 'calculation_type'])

    # 3. Create immutability trigger for engineering_calculations
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_prevent_calculation_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Engineering calculations are immutable and cannot be deleted.';
            ELSIF TG_OP = 'UPDATE' THEN
                IF OLD.status = 'CALCULATED' AND NEW.status = 'SUPERSEDED' THEN
                    IF OLD.id = NEW.id AND
                       OLD.project_id = NEW.project_id AND
                       OLD.engineering_element_id = NEW.engineering_element_id AND
                       OLD.calculation_type = NEW.calculation_type AND
                       OLD.calculation_version = NEW.calculation_version AND
                       OLD.result_value IS NOT DISTINCT FROM NEW.result_value AND
                       OLD.result_unit IS NOT DISTINCT FROM NEW.result_unit AND
                       OLD.formula_identifier = NEW.formula_identifier AND
                       OLD.formula_expression = NEW.formula_expression AND
                       (OLD.inputs_json::text = NEW.inputs_json::text) AND
                       (OLD.assumptions_json::text IS NOT DISTINCT FROM NEW.assumptions_json::text) AND
                       OLD.created_by = NEW.created_by AND
                       OLD.created_at = NEW.created_at THEN
                        RETURN NEW;
                    ELSE
                        RAISE EXCEPTION 'Cannot modify calculation inputs, formulas, or results during status change to SUPERSEDED.';
                    END IF;
                ELSE
                    RAISE EXCEPTION 'Engineering calculations are immutable. Only status transition from CALCULATED to SUPERSEDED is permitted.';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER prevent_calculation_modification_trg
        BEFORE UPDATE OR DELETE ON engineering_calculations
        FOR EACH ROW
        EXECUTE FUNCTION trg_prevent_calculation_modification();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS prevent_calculation_modification_trg ON engineering_calculations;")
    op.execute("DROP FUNCTION IF EXISTS trg_prevent_calculation_modification();")
    op.drop_index('ix_calculations_type', table_name='engineering_calculations')
    op.drop_index('ix_calculations_project', table_name='engineering_calculations')
    op.drop_index('ix_calculations_element', table_name='engineering_calculations')
    op.drop_table('engineering_calculations')
