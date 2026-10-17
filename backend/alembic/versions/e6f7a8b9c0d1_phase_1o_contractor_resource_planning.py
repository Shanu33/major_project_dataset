"""phase_1o_contractor_resource_planning

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-10-07 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e6f7a8b9c0d1'
down_revision: Union[str, Sequence[str], None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Phase 1O: Contractor Resource & Procurement Planning Foundation."""

    # 1. material_requirement_plans
    op.create_table(
        'material_requirement_plans',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('baseline_id', sa.String(length=36), sa.ForeignKey('monitoring_baselines.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('plan_version', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='DRAFT'),
        sa.Column('planning_start_date', sa.Date(), nullable=True),
        sa.Column('planning_end_date', sa.Date(), nullable=True),
        sa.Column('algorithm_version', sa.String(length=50), nullable=False, server_default='MRP_1.0'),
        sa.Column('input_snapshot_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('superseded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.UniqueConstraint('project_id', 'plan_version', name='uq_mrp_project_version'),
        sa.CheckConstraint("status IN ('DRAFT', 'ACTIVE', 'SUPERSEDED')", name='ck_mrp_status'),
        sa.CheckConstraint('planning_end_date IS NULL OR planning_start_date IS NULL OR planning_end_date >= planning_start_date', name='ck_mrp_dates'),
    )
    op.create_index('ix_mrp_project', 'material_requirement_plans', ['project_id'])
    op.create_index('ix_mrp_baseline', 'material_requirement_plans', ['baseline_id'])
    op.create_index('ix_mrp_status', 'material_requirement_plans', ['status'])
    op.execute("""
        CREATE UNIQUE INDEX uq_mrp_active_per_project ON material_requirement_plans (project_id) WHERE status = 'ACTIVE';
    """)

    # 2. material_requirement_items
    op.create_table(
        'material_requirement_items',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('material_requirement_plan_id', sa.String(length=36), sa.ForeignKey('material_requirement_plans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('material_item_id', sa.String(length=36), sa.ForeignKey('material_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('activity_id', sa.String(length=36), sa.ForeignKey('construction_activities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('material_plan_id', sa.String(length=36), sa.ForeignKey('material_plans.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('requirement_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('requirement_unit', sa.String(length=20), nullable=False),
        sa.Column('requirement_date_start', sa.Date(), nullable=True),
        sa.Column('requirement_date_end', sa.Date(), nullable=True),
        sa.Column('source_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('source_unit', sa.String(length=20), nullable=False),
        sa.Column('conversion_factor', sa.Numeric(18, 6), nullable=False, server_default='1.000000'),
        sa.Column('planning_method', sa.String(length=50), nullable=False, server_default='DIRECT_PHASE_1N_DERIVATION'),
        sa.Column('classification', sa.String(length=30), nullable=False, server_default='CALCULATED'),
        sa.Column('provenance_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PLANNED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('material_requirement_plan_id', 'material_plan_id', name='uq_mri_plan_mat_plan'),
        sa.CheckConstraint("classification IN ('CALCULATED', 'DERIVED', 'ASSUMPTION_BASED', 'USER_PROVIDED', 'REQUIRES_INPUT')", name='ck_mri_classification'),
        sa.CheckConstraint("status IN ('PLANNED', 'REQUIRES_INPUT', 'SUPERSEDED')", name='ck_mri_status'),
        sa.CheckConstraint('requirement_quantity >= 0', name='ck_mri_req_qty_positive'),
        sa.CheckConstraint('source_quantity >= 0', name='ck_mri_src_qty_positive'),
        sa.CheckConstraint('conversion_factor > 0', name='ck_mri_conv_factor_positive'),
        sa.CheckConstraint('requirement_date_end IS NULL OR requirement_date_start IS NULL OR requirement_date_end >= requirement_date_start', name='ck_mri_dates'),
    )
    op.create_index('ix_mri_plan', 'material_requirement_items', ['material_requirement_plan_id'])
    op.create_index('ix_mri_project', 'material_requirement_items', ['project_id'])
    op.create_index('ix_mri_material', 'material_requirement_items', ['material_item_id'])
    op.create_index('ix_mri_activity', 'material_requirement_items', ['activity_id'])
    op.create_index('ix_mri_mat_plan', 'material_requirement_items', ['material_plan_id'])

    # 3. procurement_requirements
    op.create_table(
        'procurement_requirements',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('material_requirement_plan_id', sa.String(length=36), sa.ForeignKey('material_requirement_plans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('material_item_id', sa.String(length=36), sa.ForeignKey('material_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('requirement_period_start', sa.Date(), nullable=True),
        sa.Column('requirement_period_end', sa.Date(), nullable=True),
        sa.Column('required_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('already_planned_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('procurement_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('planning_method', sa.String(length=50), nullable=False, server_default='PERIOD_AGGREGATED_NET_REQUIREMENT'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PLANNED'),
        sa.Column('provenance_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("status IN ('PLANNED', 'REQUIRES_INPUT', 'SUPERSEDED')", name='ck_procreq_status'),
        sa.CheckConstraint('required_quantity >= 0', name='ck_procreq_req_qty_positive'),
        sa.CheckConstraint('already_planned_quantity IS NULL OR already_planned_quantity >= 0', name='ck_procreq_planned_qty_positive'),
        sa.CheckConstraint('procurement_quantity IS NULL OR procurement_quantity >= 0', name='ck_procreq_proc_qty_positive'),
        sa.CheckConstraint('requirement_period_end IS NULL OR requirement_period_start IS NULL OR requirement_period_end >= requirement_period_start', name='ck_procreq_dates'),
    )
    op.create_index('ix_procreq_plan', 'procurement_requirements', ['material_requirement_plan_id'])
    op.create_index('ix_procreq_project', 'procurement_requirements', ['project_id'])
    op.create_index('ix_procreq_material', 'procurement_requirements', ['material_item_id'])

    # 4. Immutability Triggers
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_enforce_mrp_immutability()
        RETURNS TRIGGER AS $$
        BEGIN
            IF OLD.status = 'SUPERSEDED' THEN
                RAISE EXCEPTION 'Historical SUPERSEDED MaterialRequirementPlan % is immutable and cannot be updated or deleted.', OLD.id;
            END IF;
            IF OLD.status = 'ACTIVE' THEN
                IF TG_OP = 'DELETE' THEN
                    RAISE EXCEPTION 'ACTIVE MaterialRequirementPlan % cannot be deleted.', OLD.id;
                END IF;
                IF TG_OP = 'UPDATE' THEN
                    IF NEW.status != 'SUPERSEDED' THEN
                        RAISE EXCEPTION 'ACTIVE MaterialRequirementPlan % can only transition to SUPERSEDED.', OLD.id;
                    END IF;
                    IF NEW.id != OLD.id OR NEW.project_id != OLD.project_id OR NEW.baseline_id != OLD.baseline_id OR NEW.plan_version != OLD.plan_version OR NEW.created_by != OLD.created_by THEN
                        RAISE EXCEPTION 'Core attributes of ACTIVE MaterialRequirementPlan % cannot be modified.', OLD.id;
                    END IF;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_enforce_mrp_immutability
        BEFORE UPDATE OR DELETE ON material_requirement_plans
        FOR EACH ROW
        EXECUTE FUNCTION fn_enforce_mrp_immutability();
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION fn_enforce_mri_immutability()
        RETURNS TRIGGER AS $$
        DECLARE
            parent_status VARCHAR(20);
            target_plan_id VARCHAR(36);
        BEGIN
            IF TG_OP = 'DELETE' THEN
                target_plan_id := OLD.material_requirement_plan_id;
            ELSE
                target_plan_id := NEW.material_requirement_plan_id;
            END IF;

            SELECT status INTO parent_status FROM material_requirement_plans WHERE id = target_plan_id;
            IF parent_status IN ('ACTIVE', 'SUPERSEDED') THEN
                RAISE EXCEPTION 'Cannot modify or delete material requirement items belonging to an ACTIVE or SUPERSEDED plan (%).', target_plan_id;
            END IF;

            IF TG_OP = 'DELETE' THEN
                RETURN OLD;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_enforce_mri_immutability
        BEFORE INSERT OR UPDATE OR DELETE ON material_requirement_items
        FOR EACH ROW
        EXECUTE FUNCTION fn_enforce_mri_immutability();
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION fn_enforce_procreq_immutability()
        RETURNS TRIGGER AS $$
        DECLARE
            parent_status VARCHAR(20);
            target_plan_id VARCHAR(36);
        BEGIN
            IF TG_OP = 'DELETE' THEN
                target_plan_id := OLD.material_requirement_plan_id;
            ELSE
                target_plan_id := NEW.material_requirement_plan_id;
            END IF;

            SELECT status INTO parent_status FROM material_requirement_plans WHERE id = target_plan_id;
            IF parent_status IN ('ACTIVE', 'SUPERSEDED') THEN
                RAISE EXCEPTION 'Cannot modify or delete procurement requirements belonging to an ACTIVE or SUPERSEDED plan (%).', target_plan_id;
            END IF;

            IF TG_OP = 'DELETE' THEN
                RETURN OLD;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_enforce_procreq_immutability
        BEFORE INSERT OR UPDATE OR DELETE ON procurement_requirements
        FOR EACH ROW
        EXECUTE FUNCTION fn_enforce_procreq_immutability();
    """)


def downgrade() -> None:
    """Downgrade schema - Phase 1O revert."""

    # 1. Drop triggers and functions
    op.execute("DROP TRIGGER IF EXISTS trg_enforce_procreq_immutability ON procurement_requirements;")
    op.execute("DROP FUNCTION IF EXISTS fn_enforce_procreq_immutability();")

    op.execute("DROP TRIGGER IF EXISTS trg_enforce_mri_immutability ON material_requirement_items;")
    op.execute("DROP FUNCTION IF EXISTS fn_enforce_mri_immutability();")

    op.execute("DROP TRIGGER IF EXISTS trg_enforce_mrp_immutability ON material_requirement_plans;")
    op.execute("DROP FUNCTION IF EXISTS fn_enforce_mrp_immutability();")

    # 2. Drop tables in reverse order
    op.drop_table('procurement_requirements')
    op.drop_table('material_requirement_items')
    op.drop_table('material_requirement_plans')

