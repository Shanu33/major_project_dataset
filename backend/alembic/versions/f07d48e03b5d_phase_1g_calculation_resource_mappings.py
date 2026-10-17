"""phase_1g_calculation_resource_mappings

Revision ID: f07d48e03b5d
Revises: 7b6095282ecc
Create Date: 2026-10-04 21:01:51.732473

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f07d48e03b5d'
down_revision: Union[str, Sequence[str], None] = '7b6095282ecc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Explicit calculation-to-resource semantic mapping."""
    # 1. Create calculation_resource_mappings table
    op.create_table(
        'calculation_resource_mappings',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('calculation_type', sa.String(), nullable=False),
        sa.Column('calculation_version', sa.String(), nullable=False),
        sa.Column('resource_id', sa.String(), sa.ForeignKey('resources.id'), nullable=False),
        sa.Column('source_unit', sa.String(), nullable=False),
        sa.Column('resource_unit', sa.String(), nullable=False),
        sa.Column('mapping_method', sa.String(), nullable=False, server_default='DIRECT'),
        sa.Column('status', sa.String(), nullable=False, server_default='ACTIVE'),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )
    op.create_index(
        'uq_calc_res_mapping',
        'calculation_resource_mappings',
        ['calculation_type', 'calculation_version', 'resource_id', 'source_unit'],
        unique=True
    )
    op.create_index('ix_calc_res_mappings_res', 'calculation_resource_mappings', ['resource_id'])
    op.create_index('ix_calc_res_mappings_status', 'calculation_resource_mappings', ['status'])

    # 2. Add mapping_id column to resource_plans
    op.add_column(
        'resource_plans',
        sa.Column('mapping_id', sa.String(), sa.ForeignKey('calculation_resource_mappings.id'), nullable=True)
    )
    op.create_index('ix_resource_plans_mapping', 'resource_plans', ['mapping_id'])

    # 3. Update immutability trigger on resource_plans to preserve mapping_id
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_prevent_resource_plan_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Resource plan records are immutable and cannot be deleted.';
            ELSIF TG_OP = 'UPDATE' THEN
                IF OLD.status = 'PLANNED' AND NEW.status = 'SUPERSEDED' THEN
                    IF OLD.id = NEW.id AND
                       OLD.project_id = NEW.project_id AND
                       OLD.engineering_element_id = NEW.engineering_element_id AND
                       OLD.resource_id = NEW.resource_id AND
                       (OLD.calculation_id IS NOT DISTINCT FROM NEW.calculation_id) AND
                       (OLD.estimation_id IS NOT DISTINCT FROM NEW.estimation_id) AND
                       (OLD.mapping_id IS NOT DISTINCT FROM NEW.mapping_id) AND
                       (OLD.planned_quantity IS NOT DISTINCT FROM NEW.planned_quantity) AND
                       (OLD.planned_unit IS NOT DISTINCT FROM NEW.planned_unit) AND
                       OLD.resource_demand IS NOT DISTINCT FROM NEW.resource_demand AND
                       OLD.resource_demand_unit IS NOT DISTINCT FROM NEW.resource_demand_unit AND
                       OLD.planning_method = NEW.planning_method AND
                       OLD.classification = NEW.classification AND
                       (OLD.assumptions_json::text IS NOT DISTINCT FROM NEW.assumptions_json::text) AND
                       (OLD.provenance_json::text IS NOT DISTINCT FROM NEW.provenance_json::text) AND
                       OLD.created_by = NEW.created_by AND
                       OLD.created_at = NEW.created_at THEN
                        RETURN NEW;
                    ELSE
                        RAISE EXCEPTION 'Cannot modify resource plan inputs, parameters, or demand during status change to SUPERSEDED.';
                    END IF;
                ELSE
                    RAISE EXCEPTION 'Resource plans are immutable. Only status transition from PLANNED to SUPERSEDED is permitted.';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # 4. Create trigger to prevent mutation of referenced mappings
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_prevent_active_mapping_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF EXISTS (SELECT 1 FROM resource_plans WHERE mapping_id = OLD.id) THEN
                    RAISE EXCEPTION 'Cannot delete mapping that is referenced by resource plan records.';
                END IF;
            ELSIF TG_OP = 'UPDATE' THEN
                IF EXISTS (SELECT 1 FROM resource_plans WHERE mapping_id = OLD.id) THEN
                    IF OLD.id <> NEW.id OR
                       OLD.calculation_type <> NEW.calculation_type OR
                       OLD.calculation_version <> NEW.calculation_version OR
                       OLD.resource_id <> NEW.resource_id OR
                       OLD.source_unit <> NEW.source_unit OR
                       OLD.resource_unit <> NEW.resource_unit OR
                       OLD.mapping_method <> NEW.mapping_method OR
                       (OLD.metadata_json::text IS DISTINCT FROM NEW.metadata_json::text) OR
                       OLD.created_by <> NEW.created_by OR
                       OLD.created_at <> NEW.created_at THEN
                        RAISE EXCEPTION 'Cannot modify semantic definition fields of a mapping referenced by existing resource plans. Only lifecycle status may be changed.';
                    END IF;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER prevent_mapping_modification_trg
        BEFORE UPDATE OR DELETE ON calculation_resource_mappings
        FOR EACH ROW
        EXECUTE FUNCTION trg_prevent_active_mapping_modification();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS prevent_mapping_modification_trg ON calculation_resource_mappings;")
    op.execute("DROP FUNCTION IF EXISTS trg_prevent_active_mapping_modification();")

    # Restore previous resource_plans trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_prevent_resource_plan_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Resource plan records are immutable and cannot be deleted.';
            ELSIF TG_OP = 'UPDATE' THEN
                IF OLD.status = 'PLANNED' AND NEW.status = 'SUPERSEDED' THEN
                    IF OLD.id = NEW.id AND
                       OLD.project_id = NEW.project_id AND
                       OLD.engineering_element_id = NEW.engineering_element_id AND
                       OLD.resource_id = NEW.resource_id AND
                       (OLD.calculation_id IS NOT DISTINCT FROM NEW.calculation_id) AND
                       (OLD.estimation_id IS NOT DISTINCT FROM NEW.estimation_id) AND
                       (OLD.planned_quantity IS NOT DISTINCT FROM NEW.planned_quantity) AND
                       (OLD.planned_unit IS NOT DISTINCT FROM NEW.planned_unit) AND
                       OLD.resource_demand IS NOT DISTINCT FROM NEW.resource_demand AND
                       OLD.resource_demand_unit IS NOT DISTINCT FROM NEW.resource_demand_unit AND
                       OLD.planning_method = NEW.planning_method AND
                       OLD.classification = NEW.classification AND
                       (OLD.assumptions_json::text IS NOT DISTINCT FROM NEW.assumptions_json::text) AND
                       (OLD.provenance_json::text IS NOT DISTINCT FROM NEW.provenance_json::text) AND
                       OLD.created_by = NEW.created_by AND
                       OLD.created_at = NEW.created_at THEN
                        RETURN NEW;
                    ELSE
                        RAISE EXCEPTION 'Cannot modify resource plan inputs, parameters, or demand during status change to SUPERSEDED.';
                    END IF;
                ELSE
                    RAISE EXCEPTION 'Resource plans are immutable. Only status transition from PLANNED to SUPERSEDED is permitted.';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.drop_index('ix_resource_plans_mapping', table_name='resource_plans')
    op.drop_column('resource_plans', 'mapping_id')
    op.drop_table('calculation_resource_mappings')
