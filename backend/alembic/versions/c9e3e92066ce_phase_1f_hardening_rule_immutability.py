"""phase_1f_hardening_rule_immutability

Revision ID: c9e3e92066ce
Revises: 53bb531a7d4f
Create Date: 2026-10-04 20:37:53.790040

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9e3e92066ce'
down_revision: Union[str, Sequence[str], None] = '53bb531a7d4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Harden rule immutability for all semantic definition fields."""
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_prevent_active_rule_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF EXISTS (SELECT 1 FROM rule_based_estimations WHERE rule_id = OLD.id) THEN
                    RAISE EXCEPTION 'Cannot delete rule version that is referenced by estimation records.';
                END IF;
            ELSIF TG_OP = 'UPDATE' THEN
                IF EXISTS (SELECT 1 FROM rule_based_estimations WHERE rule_id = OLD.id) THEN
                    -- Check if any semantic definition or identity field is being modified
                    IF OLD.id <> NEW.id OR
                       OLD.rule_code <> NEW.rule_code OR
                       OLD.rule_name <> NEW.rule_name OR
                       (OLD.description IS DISTINCT FROM NEW.description) OR
                       OLD.rule_category <> NEW.rule_category OR
                       OLD.input_unit <> NEW.input_unit OR
                       OLD.output_unit <> NEW.output_unit OR
                       OLD.formula_identifier <> NEW.formula_identifier OR
                       OLD.formula_expression <> NEW.formula_expression OR
                       (OLD.parameters_json::text IS DISTINCT FROM NEW.parameters_json::text) OR
                       (OLD.source_reference IS DISTINCT FROM NEW.source_reference) OR
                       OLD.version <> NEW.version OR
                       (OLD.metadata_json::text IS DISTINCT FROM NEW.metadata_json::text) OR
                       OLD.created_by <> NEW.created_by OR
                       OLD.created_at <> NEW.created_at THEN
                        RAISE EXCEPTION 'Cannot modify semantic definition fields of a rule version referenced by existing estimations. Only lifecycle status may be changed.';
                    END IF;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """Downgrade schema - Restore original rule trigger function."""
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
