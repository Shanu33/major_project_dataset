"""phase_1g_resource_planning

Revision ID: 7b6095282ecc
Revises: c9e3e92066ce
Create Date: 2026-10-04 20:47:08.545196

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b6095282ecc'
down_revision: Union[str, Sequence[str], None] = 'c9e3e92066ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Phase 1G: Resource Planning Foundation."""
    # 1. Create resources table
    op.create_table(
        'resources',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('resource_code', sa.String(), nullable=False),
        sa.Column('resource_name', sa.String(), nullable=False),
        sa.Column('resource_category', sa.String(), nullable=False),
        sa.Column('unit', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='ACTIVE'),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )
    op.create_index('uq_resource_code', 'resources', ['resource_code'], unique=True)
    op.create_index('ix_resources_category', 'resources', ['resource_category'])
    op.create_index('ix_resources_status', 'resources', ['status'])

    # 2. Create resource_plans table
    op.create_table(
        'resource_plans',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('engineering_element_id', sa.String(), sa.ForeignKey('engineering_elements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('resource_id', sa.String(), sa.ForeignKey('resources.id'), nullable=False),
        sa.Column('calculation_id', sa.String(), sa.ForeignKey('engineering_calculations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('estimation_id', sa.String(), sa.ForeignKey('rule_based_estimations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('planned_quantity', sa.Numeric(18, 6), nullable=True),
        sa.Column('planned_unit', sa.String(), nullable=True),
        sa.Column('resource_demand', sa.Numeric(18, 6), nullable=False),
        sa.Column('resource_demand_unit', sa.String(), nullable=False),
        sa.Column('planning_method', sa.String(), nullable=False),
        sa.Column('classification', sa.String(), nullable=False),
        sa.Column('assumptions_json', sa.JSON(), nullable=True),
        sa.Column('provenance_json', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='PLANNED'),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )
    op.create_index('ix_resource_plans_project', 'resource_plans', ['project_id'])
    op.create_index('ix_resource_plans_element', 'resource_plans', ['engineering_element_id'])
    op.create_index('ix_resource_plans_resource', 'resource_plans', ['resource_id'])
    op.create_index('ix_resource_plans_calc', 'resource_plans', ['calculation_id'])
    op.create_index('ix_resource_plans_estimation', 'resource_plans', ['estimation_id'])
    op.create_index('ix_resource_plans_status', 'resource_plans', ['status'])

    # 3. Create immutability trigger for resource_plans
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
    op.execute("""
        CREATE TRIGGER prevent_resource_plan_modification_trg
        BEFORE UPDATE OR DELETE ON resource_plans
        FOR EACH ROW
        EXECUTE FUNCTION trg_prevent_resource_plan_modification();
    """)

    # 4. Create trigger to prevent mutation of referenced resources
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_prevent_active_resource_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF EXISTS (SELECT 1 FROM resource_plans WHERE resource_id = OLD.id) THEN
                    RAISE EXCEPTION 'Cannot delete resource that is referenced by resource plan records.';
                END IF;
            ELSIF TG_OP = 'UPDATE' THEN
                IF EXISTS (SELECT 1 FROM resource_plans WHERE resource_id = OLD.id) THEN
                    IF OLD.id <> NEW.id OR
                       OLD.resource_code <> NEW.resource_code OR
                       OLD.resource_name <> NEW.resource_name OR
                       (OLD.description IS DISTINCT FROM NEW.description) OR
                       OLD.resource_category <> NEW.resource_category OR
                       OLD.unit <> NEW.unit OR
                       (OLD.metadata_json::text IS DISTINCT FROM NEW.metadata_json::text) OR
                       OLD.created_by <> NEW.created_by OR
                       OLD.created_at <> NEW.created_at THEN
                        RAISE EXCEPTION 'Cannot modify semantic definition fields of a resource referenced by existing resource plans. Only lifecycle status may be changed.';
                    END IF;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER prevent_resource_modification_trg
        BEFORE UPDATE OR DELETE ON resources
        FOR EACH ROW
        EXECUTE FUNCTION trg_prevent_active_resource_modification();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS prevent_resource_modification_trg ON resources;")
    op.execute("DROP FUNCTION IF EXISTS trg_prevent_active_resource_modification();")
    op.execute("DROP TRIGGER IF EXISTS prevent_resource_plan_modification_trg ON resource_plans;")
    op.execute("DROP FUNCTION IF EXISTS trg_prevent_resource_plan_modification();")
    op.drop_table('resource_plans')
    op.drop_table('resources')
