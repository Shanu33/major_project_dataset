"""phase_1n_material_reconciliation

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-10-07 17:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, Sequence[str], None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Phase 1N: Material Requirements Planning, Mix Formulation & Theoretical Consumption Reconciliation Foundation."""

    # 1. material_items
    op.create_table(
        'material_items',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('material_code', sa.String(length=50), nullable=False),
        sa.Column('material_name', sa.String(length=100), nullable=False),
        sa.Column('material_category', sa.String(length=50), nullable=False),
        sa.Column('standard_unit', sa.String(length=20), nullable=False),
        sa.Column('density_kg_per_unit', sa.Numeric(12, 4), nullable=True),
        sa.Column('standard_permissible_waste_pct', sa.Numeric(5, 2), nullable=False, server_default='0.00'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint(
            "material_category IN ('BINDER', 'AGGREGATE', 'REINFORCEMENT', 'MASONRY', 'CHEMICAL', 'WATER', 'TIMBER', 'STEEL_SECTION')",
            name='ck_mat_item_category'
        ),
        sa.CheckConstraint(
            "standard_unit IN ('BAG', 'KG', 'MT', 'M3', 'LITRE', 'NOS', 'SQM')",
            name='ck_mat_item_unit'
        ),
        sa.CheckConstraint(
            "standard_permissible_waste_pct >= 0.00 AND standard_permissible_waste_pct <= 100.00",
            name='ck_mat_item_waste'
        ),
        sa.CheckConstraint(
            "density_kg_per_unit IS NULL OR density_kg_per_unit >= 0",
            name='ck_mat_item_density'
        ),
    )
    op.create_index('ix_mat_items_proj', 'material_items', ['project_id'])
    op.create_index('ix_mat_items_category', 'material_items', ['material_category'])
    op.execute("""
        CREATE UNIQUE INDEX uq_mat_item_proj_code ON material_items (project_id, material_code) WHERE project_id IS NOT NULL;
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_mat_item_global_code ON material_items (material_code) WHERE project_id IS NULL;
    """)

    # 2. material_mix_designs
    op.create_table(
        'material_mix_designs',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('mix_code', sa.String(length=50), nullable=False),
        sa.Column('grade_designation', sa.String(length=50), nullable=False),
        sa.Column('mix_type', sa.String(length=30), nullable=False),
        sa.Column('rule_code', sa.String(length=50), nullable=True),
        sa.Column('source_document_id', sa.String(length=36), sa.ForeignKey('documents.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('evidence_id', sa.String(length=36), sa.ForeignKey('evidence.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('dry_volume_factor', sa.Numeric(6, 4), nullable=False, server_default='1.5400'),
        sa.Column('water_cement_ratio', sa.Numeric(5, 3), nullable=True),
        sa.Column('classification', sa.String(length=30), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='DRAFT'),
        sa.Column('approved_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("mix_type IN ('DESIGN_MIX', 'NOMINAL_MIX')", name='ck_mmd_type'),
        sa.CheckConstraint("status IN ('DRAFT', 'APPROVED', 'SUPERSEDED')", name='ck_mmd_status'),
        sa.CheckConstraint("classification IN ('CALCULATED', 'DERIVED', 'ASSUMPTION_BASED')", name='ck_mmd_classification'),
        sa.CheckConstraint("dry_volume_factor > 0", name='ck_mmd_dry_vol_factor'),
        sa.CheckConstraint("water_cement_ratio IS NULL OR water_cement_ratio > 0", name='ck_mmd_wc_ratio'),
        sa.CheckConstraint("status != 'APPROVED' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)", name='ck_mmd_approval'),
        sa.CheckConstraint("mix_type != 'DESIGN_MIX' OR (source_document_id IS NOT NULL AND evidence_id IS NOT NULL)", name='ck_mmd_design_mix_evidence'),
        sa.CheckConstraint("mix_type != 'NOMINAL_MIX' OR (classification = 'ASSUMPTION_BASED' AND rule_code IS NOT NULL)", name='ck_mmd_nominal_mix_rule'),
    )
    op.create_index('ix_mmd_project', 'material_mix_designs', ['project_id'])
    op.create_index('ix_mmd_status', 'material_mix_designs', ['status'])
    op.create_index('uq_mmd_proj_code', 'material_mix_designs', ['project_id', 'mix_code'], unique=True)

    # 3. material_mix_constituents
    op.create_table(
        'material_mix_constituents',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('mix_design_id', sa.String(length=36), sa.ForeignKey('material_mix_designs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('material_item_id', sa.String(length=36), sa.ForeignKey('material_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('quantity_per_m3', sa.Numeric(14, 6), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.CheckConstraint("quantity_per_m3 > 0", name='ck_mmc_qty_positive'),
    )
    op.create_index('ix_mmc_mix', 'material_mix_constituents', ['mix_design_id'])
    op.create_index('ix_mmc_mat', 'material_mix_constituents', ['material_item_id'])
    op.create_index('uq_mmc_mix_material', 'material_mix_constituents', ['mix_design_id', 'material_item_id'], unique=True)

    # 4. material_plans
    op.create_table(
        'material_plans',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('baseline_id', sa.String(length=36), sa.ForeignKey('monitoring_baselines.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('material_item_id', sa.String(length=36), sa.ForeignKey('material_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('activity_id', sa.String(length=36), sa.ForeignKey('construction_activities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('mix_design_id', sa.String(length=36), sa.ForeignKey('material_mix_designs.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('planned_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('estimation_method', sa.String(length=30), nullable=False),
        sa.Column('waste_allowance_pct', sa.Numeric(5, 2), nullable=False, server_default='0.00'),
        sa.Column('gross_planned_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('provenance_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("estimation_method IN ('CALCULATED', 'DERIVED', 'ASSUMPTION_BASED', 'USER_PROVIDED')", name='ck_mat_plan_method'),
        sa.CheckConstraint("status IN ('ACTIVE', 'SUPERSEDED')", name='ck_mat_plan_status'),
        sa.CheckConstraint("planned_quantity >= 0 AND gross_planned_quantity >= planned_quantity", name='ck_mat_plan_quantities'),
    )
    op.create_index('ix_mat_plans_project', 'material_plans', ['project_id'])
    op.create_index('ix_mat_plans_baseline', 'material_plans', ['baseline_id'])
    op.create_index('ix_mat_plans_activity', 'material_plans', ['activity_id'])
    op.create_index('ix_mat_plans_material', 'material_plans', ['material_item_id'])

    # 5. material_consumption_entries
    op.create_table(
        'material_consumption_entries',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('certificate_id', sa.String(length=36), sa.ForeignKey('period_progress_certificates.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('material_item_id', sa.String(length=36), sa.ForeignKey('material_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('store_challan_reference', sa.String(length=100), nullable=False),
        sa.Column('consumption_date_start', sa.Date(), nullable=False),
        sa.Column('consumption_date_end', sa.Date(), nullable=False),
        sa.Column('contractor_declared_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('supervisor_verified_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('discrepancy_quantity', sa.Numeric(18, 4), nullable=False, server_default='0.0000'),
        sa.Column('is_disputed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('submission_status', sa.String(length=20), nullable=False, server_default='SUBMITTED'),
        sa.Column('supporting_document_id', sa.String(length=36), sa.ForeignKey('documents.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('submitted_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('verified_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("consumption_date_start <= consumption_date_end", name='ck_mce_dates'),
        sa.CheckConstraint("submission_status IN ('SUBMITTED', 'VERIFIED', 'REJECTED')", name='ck_mce_status'),
        sa.CheckConstraint("contractor_declared_quantity >= 0 AND (supervisor_verified_quantity IS NULL OR supervisor_verified_quantity >= 0)", name='ck_mce_quantities'),
        sa.CheckConstraint("submission_status != 'VERIFIED' OR (supervisor_verified_quantity IS NOT NULL AND verified_by IS NOT NULL AND verified_at IS NOT NULL)", name='ck_mce_verified_fields'),
    )
    op.create_index('ix_mce_proj_cert', 'material_consumption_entries', ['project_id', 'certificate_id'])
    op.create_index('ix_mce_material', 'material_consumption_entries', ['material_item_id'])
    op.create_index('ix_mce_status', 'material_consumption_entries', ['submission_status'])
    op.create_index('uq_mce_challan', 'material_consumption_entries', ['project_id', 'store_challan_reference'], unique=True)

    # 6. theoretical_consumption_items
    op.create_table(
        'theoretical_consumption_items',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('certificate_id', sa.String(length=36), sa.ForeignKey('period_progress_certificates.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('certificate_item_id', sa.String(length=36), sa.ForeignKey('period_certificate_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('activity_id', sa.String(length=36), sa.ForeignKey('construction_activities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('material_item_id', sa.String(length=36), sa.ForeignKey('material_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('mix_design_id', sa.String(length=36), sa.ForeignKey('material_mix_designs.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('certified_activity_volume', sa.Numeric(18, 6), nullable=False),
        sa.Column('coefficient_per_unit', sa.Numeric(14, 6), nullable=False),
        sa.Column('dry_volume_factor', sa.Numeric(6, 4), nullable=False),
        sa.Column('theoretical_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('mix_design_version', sa.String(length=50), nullable=False),
        sa.Column('calculation_algorithm_version', sa.String(length=20), nullable=False, server_default='1.0-DETERMINISTIC'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("certified_activity_volume >= 0 AND coefficient_per_unit > 0 AND theoretical_quantity >= 0", name='ck_tci_quantities'),
    )
    op.create_index('ix_tci_cert_material', 'theoretical_consumption_items', ['certificate_id', 'material_item_id'])
    op.create_index('ix_tci_activity', 'theoretical_consumption_items', ['activity_id'])
    op.create_index('ix_tci_cert_item', 'theoretical_consumption_items', ['certificate_item_id'])

    # 7. material_reconciliation_reports
    op.create_table(
        'material_reconciliation_reports',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('certificate_id', sa.String(length=36), sa.ForeignKey('period_progress_certificates.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('material_item_id', sa.String(length=36), sa.ForeignKey('material_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('revision_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='DRAFT'),
        sa.Column('cumulative_theoretical_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('cumulative_actual_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('variance_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('variance_percentage', sa.Numeric(8, 4), nullable=False),
        sa.Column('is_saving', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('permissible_waste_percentage', sa.Numeric(5, 2), nullable=False),
        sa.Column('permissible_waste_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('unauthorized_wastage_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('is_excess_flagged', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reconciliation_hash', sa.String(length=64), nullable=False),
        sa.Column('finalized_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('supersedes_report_id', sa.String(length=36), sa.ForeignKey('material_reconciliation_reports.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("status IN ('DRAFT', 'FINALIZED', 'SUPERSEDED')", name='ck_mrr_status'),
        sa.CheckConstraint(
            "cumulative_theoretical_quantity >= 0 AND cumulative_actual_quantity >= 0 AND permissible_waste_quantity >= 0 AND unauthorized_wastage_quantity >= 0",
            name='ck_mrr_quantities'
        ),
        sa.CheckConstraint("status != 'FINALIZED' OR (finalized_by IS NOT NULL AND finalized_at IS NOT NULL)", name='ck_mrr_finalized_fields'),
    )
    op.create_index('ix_mrr_proj_cert', 'material_reconciliation_reports', ['project_id', 'certificate_id'])
    op.create_index('ix_mrr_material', 'material_reconciliation_reports', ['material_item_id'])
    op.create_index('uq_mrr_cert_material_rev', 'material_reconciliation_reports', ['certificate_id', 'material_item_id', 'revision_number'], unique=True)

    # --------------------------------------------------------------------------
    # TRIGGERS
    # --------------------------------------------------------------------------

    # Trigger 1: Validate activity consistency between certificate item and theoretical consumption item
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_validate_theo_consumption_activity()
        RETURNS TRIGGER AS $$
        DECLARE
            v_item_act_id VARCHAR;
            v_item_cert_id VARCHAR;
            v_cert_project_id VARCHAR;
        BEGIN
            SELECT activity_id, certificate_id INTO v_item_act_id, v_item_cert_id
            FROM period_certificate_items
            WHERE id = NEW.certificate_item_id;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Referenced PeriodCertificateItem % not found', NEW.certificate_item_id;
            END IF;

            IF v_item_act_id != NEW.activity_id THEN
                RAISE EXCEPTION 'Theoretical consumption activity (%) does not match period certificate item activity (%)',
                    NEW.activity_id, v_item_act_id;
            END IF;

            IF v_item_cert_id != NEW.certificate_id THEN
                RAISE EXCEPTION 'Theoretical consumption certificate (%) does not match period certificate item certificate (%)',
                    NEW.certificate_id, v_item_cert_id;
            END IF;

            SELECT project_id INTO v_cert_project_id
            FROM period_progress_certificates
            WHERE id = NEW.certificate_id;

            IF v_cert_project_id != NEW.project_id THEN
                RAISE EXCEPTION 'Theoretical consumption project (%) does not match certificate project (%)',
                    NEW.project_id, v_cert_project_id;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_validate_theo_consumption_activity
        BEFORE INSERT OR UPDATE ON theoretical_consumption_items
        FOR EACH ROW EXECUTE FUNCTION fn_validate_theo_consumption_activity();
    """)

    # Trigger 2: Protect VERIFIED material consumption entries
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_protect_material_consumption_entry()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF OLD.submission_status = 'VERIFIED' THEN
                    RAISE EXCEPTION 'Cannot delete VERIFIED material consumption entry %', OLD.id;
                END IF;
                RETURN OLD;
            END IF;

            IF TG_OP = 'UPDATE' THEN
                IF OLD.submission_status = 'VERIFIED' THEN
                    -- Allow only supersession or authorized state transitions
                    IF current_setting('app.auth_consumption_mutation', true) = 'TRUE' THEN
                        RETURN NEW;
                    END IF;
                    RAISE EXCEPTION 'Cannot mutate VERIFIED material consumption entry %', OLD.id;
                END IF;
                RETURN NEW;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_protect_material_consumption_entry
        BEFORE UPDATE OR DELETE ON material_consumption_entries
        FOR EACH ROW EXECUTE FUNCTION fn_protect_material_consumption_entry();
    """)

    # Trigger 3: Lock finalized material reconciliation reports (immutability)
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_lock_material_reconciliation_report()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF OLD.status = 'FINALIZED' THEN
                    RAISE EXCEPTION 'material_reconciliation_reports are immutable historical audit records: deletion blocked for %', OLD.id;
                END IF;
                RETURN OLD;
            END IF;

            IF TG_OP = 'UPDATE' THEN
                IF OLD.status = 'FINALIZED' THEN
                    -- Allow transition from FINALIZED to SUPERSEDED only
                    IF NEW.status = 'SUPERSEDED' AND OLD.status = 'FINALIZED' THEN
                        -- Validate contractual quantities cannot change
                        IF NEW.cumulative_theoretical_quantity != OLD.cumulative_theoretical_quantity
                           OR NEW.cumulative_actual_quantity != OLD.cumulative_actual_quantity
                           OR NEW.variance_quantity != OLD.variance_quantity
                           OR NEW.reconciliation_hash != OLD.reconciliation_hash THEN
                            RAISE EXCEPTION 'Cannot mutate historical quantities when superseding finalized report %', OLD.id;
                        END IF;
                        RETURN NEW;
                    END IF;
                    RAISE EXCEPTION 'material_reconciliation_reports are immutable historical audit records: update blocked for %', OLD.id;
                END IF;
                RETURN NEW;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_lock_material_reconciliation_report
        BEFORE UPDATE OR DELETE ON material_reconciliation_reports
        FOR EACH ROW EXECUTE FUNCTION fn_lock_material_reconciliation_report();
    """)

    # Trigger 4: Protect APPROVED material mix designs
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_protect_approved_mix_design()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF OLD.status = 'APPROVED' THEN
                    RAISE EXCEPTION 'Cannot delete an APPROVED material mix design %', OLD.id;
                END IF;
                RETURN OLD;
            END IF;

            IF TG_OP = 'UPDATE' THEN
                IF OLD.status = 'APPROVED' THEN
                    -- Only allow transition to SUPERSEDED
                    IF NEW.status = 'SUPERSEDED' AND OLD.status = 'APPROVED' THEN
                        RETURN NEW;
                    END IF;
                    -- If staying APPROVED, contractual formulation attributes must not change
                    IF NEW.mix_code != OLD.mix_code
                       OR NEW.grade_designation != OLD.grade_designation
                       OR NEW.dry_volume_factor != OLD.dry_volume_factor
                       OR NEW.water_cement_ratio != OLD.water_cement_ratio THEN
                        RAISE EXCEPTION 'Approved material mix design % formulations are immutable', OLD.id;
                    END IF;
                END IF;
                RETURN NEW;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_protect_approved_mix_design
        BEFORE UPDATE OR DELETE ON material_mix_designs
        FOR EACH ROW EXECUTE FUNCTION fn_protect_approved_mix_design();
    """)


def downgrade() -> None:
    """Downgrade schema - remove Phase 1N material reconciliation objects."""
    # Drop triggers and functions
    op.execute("DROP TRIGGER IF EXISTS trg_protect_approved_mix_design ON material_mix_designs;")
    op.execute("DROP FUNCTION IF EXISTS fn_protect_approved_mix_design();")

    op.execute("DROP TRIGGER IF EXISTS trg_lock_material_reconciliation_report ON material_reconciliation_reports;")
    op.execute("DROP FUNCTION IF EXISTS fn_lock_material_reconciliation_report();")

    op.execute("DROP TRIGGER IF EXISTS trg_protect_material_consumption_entry ON material_consumption_entries;")
    op.execute("DROP FUNCTION IF EXISTS fn_protect_material_consumption_entry();")

    op.execute("DROP TRIGGER IF EXISTS trg_validate_theo_consumption_activity ON theoretical_consumption_items;")
    op.execute("DROP FUNCTION IF EXISTS fn_validate_theo_consumption_activity();")

    # Drop tables in reverse dependency order
    op.drop_table('material_reconciliation_reports')
    op.drop_table('theoretical_consumption_items')
    op.drop_table('material_consumption_entries')
    op.drop_table('material_plans')
    op.drop_table('material_mix_constituents')
    op.drop_table('material_mix_designs')
    op.drop_table('material_items')
