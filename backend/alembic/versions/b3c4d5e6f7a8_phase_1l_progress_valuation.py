"""phase_1l_progress_valuation

Revision ID: b3c4d5e6f7a8
Revises: f6a7b8c9d0e1
Create Date: 2026-10-05 21:58:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, Sequence[str], None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Phase 1L: Site Progress Valuation & Certified Progress Foundation."""
    # 1. Create activity_rate_mappings table
    op.create_table(
        'activity_rate_mappings',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('activity_id', sa.String(), sa.ForeignKey('construction_activities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cost_rate_id', sa.String(), sa.ForeignKey('cost_rates.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('rate_value', sa.Numeric(18, 6), nullable=False),
        sa.Column('rate_unit', sa.String(length=50), nullable=False),
        sa.Column('rate_version', sa.String(length=50), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('rate_value > 0', name='ck_act_rate_map_rate_val_positive'),
        sa.CheckConstraint("status IN ('ACTIVE', 'SUPERSEDED')", name='ck_act_rate_map_status'),
    )
    op.create_index('ix_act_rate_map_project', 'activity_rate_mappings', ['project_id'])
    op.create_index('ix_act_rate_map_activity', 'activity_rate_mappings', ['activity_id'])
    op.create_index('ix_act_rate_map_cost_rate', 'activity_rate_mappings', ['cost_rate_id'])
    op.create_index('ix_act_rate_map_status', 'activity_rate_mappings', ['status'])
    op.create_index(
        'uq_act_rate_map_active',
        'activity_rate_mappings',
        ['activity_id'],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'")
    )

    # 2. Create period_progress_certificates table (before daily_progress_valuations so FK can resolve)
    op.create_table(
        'period_progress_certificates',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('certificate_number', sa.String(length=100), nullable=False),
        sa.Column('certificate_type', sa.String(length=30), nullable=False, server_default='PERIOD_SNAPSHOT'),
        sa.Column('monitoring_baseline_id', sa.String(), sa.ForeignKey('monitoring_baselines.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('baseline_schedule_id', sa.String(), nullable=False),
        sa.Column('baseline_schedule_version', sa.String(length=50), nullable=False),
        sa.Column('baseline_schedule_algorithm_version', sa.String(length=50), nullable=False),
        sa.Column('baseline_start_date', sa.Date(), nullable=False),
        sa.Column('period_start_date', sa.Date(), nullable=False),
        sa.Column('period_cut_off_date', sa.Date(), nullable=False),
        sa.Column('certificate_status', sa.String(length=20), nullable=False, server_default='DRAFT'),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('period_claimed_value', sa.Numeric(18, 4), nullable=False, server_default='0'),
        sa.Column('period_certified_value', sa.Numeric(18, 4), nullable=False, server_default='0'),
        sa.Column('period_disputed_exposure', sa.Numeric(18, 4), nullable=False, server_default='0'),
        sa.Column('cumulative_claimed_value', sa.Numeric(18, 4), nullable=False, server_default='0'),
        sa.Column('cumulative_certified_value', sa.Numeric(18, 4), nullable=False, server_default='0'),
        sa.Column('cumulative_disputed_exposure', sa.Numeric(18, 4), nullable=False, server_default='0'),
        sa.Column('item_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('valuation_snapshot_hash', sa.String(length=64), nullable=False),
        sa.Column('algorithm_version', sa.String(length=20), nullable=False, server_default='1.0'),
        sa.Column('certified_by', sa.String(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('certified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('superseded_by', sa.String(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('superseded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('supersession_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('project_id', 'certificate_number', name='uq_project_certificate_number'),
        sa.CheckConstraint('period_start_date <= period_cut_off_date', name='ck_ppc_date_window'),
        sa.CheckConstraint("certificate_status IN ('DRAFT', 'CERTIFIED', 'SUPERSEDED')", name='ck_ppc_status'),
        sa.CheckConstraint('item_count >= 0', name='ck_ppc_item_count_nonneg'),
    )
    op.create_index('ix_ppc_project', 'period_progress_certificates', ['project_id'])
    op.create_index('ix_ppc_status', 'period_progress_certificates', ['certificate_status'])
    op.create_index('ix_ppc_dates', 'period_progress_certificates', ['project_id', 'period_start_date', 'period_cut_off_date'])

    # 3. Create daily_progress_valuations table
    op.create_table(
        'daily_progress_valuations',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('verification_id', sa.String(), sa.ForeignKey('daily_activity_progress_verifications.id', ondelete='RESTRICT'), unique=True, nullable=False),
        sa.Column('activity_rate_mapping_id', sa.String(), sa.ForeignKey('activity_rate_mappings.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('contractor_claimed_quantity', sa.Numeric(18, 6), nullable=False),
        sa.Column('supervisor_certified_quantity', sa.Numeric(18, 6), nullable=False),
        sa.Column('quantity_unit', sa.String(length=50), nullable=False),
        sa.Column('unit_conversion_factor', sa.Numeric(18, 6), nullable=False, server_default='1.0'),
        sa.Column('applied_rate_value', sa.Numeric(18, 6), nullable=False),
        sa.Column('applied_rate_unit', sa.String(length=50), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('contractor_claimed_value', sa.Numeric(18, 4), nullable=False),
        sa.Column('certified_progress_value', sa.Numeric(18, 4), nullable=False),
        sa.Column('discrepancy_quantity', sa.Numeric(18, 6), nullable=False),
        sa.Column('disputed_valuation_exposure', sa.Numeric(18, 4), nullable=False),
        sa.Column('certified_certificate_id', sa.String(), sa.ForeignKey('period_progress_certificates.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('valuation_status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('contractor_claimed_quantity >= 0', name='ck_dpv_claimed_qty_nonneg'),
        sa.CheckConstraint('supervisor_certified_quantity >= 0', name='ck_dpv_certified_qty_nonneg'),
        sa.CheckConstraint('applied_rate_value > 0', name='ck_dpv_applied_rate_positive'),
        sa.CheckConstraint('contractor_claimed_value >= 0', name='ck_dpv_claimed_val_nonneg'),
        sa.CheckConstraint('certified_progress_value >= 0', name='ck_dpv_certified_val_nonneg'),
        sa.CheckConstraint('disputed_valuation_exposure >= 0', name='ck_dpv_disputed_exposure_nonneg'),
        sa.CheckConstraint("valuation_status IN ('ACTIVE', 'SUPERSEDED')", name='ck_dpv_status'),
    )
    op.create_index('ix_dpv_project', 'daily_progress_valuations', ['project_id'])
    op.create_index('ix_dpv_verification', 'daily_progress_valuations', ['verification_id'])
    op.create_index('ix_dpv_mapping', 'daily_progress_valuations', ['activity_rate_mapping_id'])
    op.create_index('ix_dpv_status', 'daily_progress_valuations', ['valuation_status'])
    op.create_index('ix_dpv_cert_binding', 'daily_progress_valuations', ['certified_certificate_id'])

    # 4. Create period_certificate_items table
    op.create_table(
        'period_certificate_items',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('certificate_id', sa.String(), sa.ForeignKey('period_progress_certificates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('valuation_id', sa.String(), sa.ForeignKey('daily_progress_valuations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('activity_id', sa.String(), sa.ForeignKey('construction_activities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('claimed_quantity', sa.Numeric(18, 6), nullable=False),
        sa.Column('certified_quantity', sa.Numeric(18, 6), nullable=False),
        sa.Column('quantity_unit', sa.String(length=50), nullable=False),
        sa.Column('unit_conversion_factor', sa.Numeric(18, 6), nullable=False, server_default='1.0'),
        sa.Column('applied_rate', sa.Numeric(18, 6), nullable=False),
        sa.Column('applied_rate_unit', sa.String(length=50), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('claimed_amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('certified_amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('discrepancy_quantity', sa.Numeric(18, 6), nullable=False),
        sa.Column('disputed_exposure', sa.Numeric(18, 4), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('certificate_id', 'valuation_id', name='uq_cert_items_cert_val'),
        sa.CheckConstraint('claimed_quantity >= 0', name='ck_pci_claimed_qty_nonneg'),
        sa.CheckConstraint('certified_quantity >= 0', name='ck_pci_certified_qty_nonneg'),
        sa.CheckConstraint('applied_rate > 0', name='ck_pci_applied_rate_positive'),
        sa.CheckConstraint('claimed_amount >= 0', name='ck_pci_claimed_amt_nonneg'),
        sa.CheckConstraint('certified_amount >= 0', name='ck_pci_certified_amt_nonneg'),
        sa.CheckConstraint('disputed_exposure >= 0', name='ck_pci_disputed_exposure_nonneg'),
    )
    op.create_index('ix_pci_certificate', 'period_certificate_items', ['certificate_id'])
    op.create_index('ix_pci_valuation', 'period_certificate_items', ['valuation_id'])
    op.create_index('ix_pci_activity', 'period_certificate_items', ['activity_id'])

    # 5. PostgreSQL Triggers & Functions

    # 5.1 Activity Rate Mapping Validation & Immutability Trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_validate_activity_rate_mapping()
        RETURNS TRIGGER AS $$
        DECLARE
            act_proj VARCHAR;
            rate_proj VARCHAR;
            rate_stat VARCHAR;
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Deletion of activity rate mapping is prohibited.';
            END IF;

            -- Verify activity belongs to same project
            SELECT project_id INTO act_proj FROM construction_activities WHERE id = NEW.activity_id;
            IF act_proj IS NULL THEN
                RAISE EXCEPTION 'Referenced activity % does not exist.', NEW.activity_id;
            END IF;
            IF act_proj <> NEW.project_id THEN
                RAISE EXCEPTION 'Cross-project activity mapping forbidden. Activity belongs to project %, not %.', act_proj, NEW.project_id;
            END IF;

            -- Verify cost rate exists, is CONFIRMED, and belongs to same project or is global
            SELECT project_id, status INTO rate_proj, rate_stat FROM cost_rates WHERE id = NEW.cost_rate_id;
            IF rate_stat IS NULL THEN
                RAISE EXCEPTION 'Referenced cost rate % does not exist.', NEW.cost_rate_id;
            END IF;
            IF rate_stat <> 'CONFIRMED' THEN
                RAISE EXCEPTION 'Activity rate mapping requires CONFIRMED cost rate. Current status: %.', rate_stat;
            END IF;
            IF rate_proj IS NOT NULL AND rate_proj <> NEW.project_id THEN
                RAISE EXCEPTION 'Cost rate project % does not match mapping project %.', rate_proj, NEW.project_id;
            END IF;

            IF TG_OP = 'UPDATE' THEN
                -- Validate immutable fields
                IF OLD.project_id <> NEW.project_id OR
                   OLD.activity_id <> NEW.activity_id OR
                   OLD.cost_rate_id <> NEW.cost_rate_id OR
                   OLD.rate_value <> NEW.rate_value OR
                   OLD.rate_unit <> NEW.rate_unit OR
                   OLD.rate_version <> NEW.rate_version OR
                   OLD.currency <> NEW.currency OR
                   OLD.created_by <> NEW.created_by OR
                   OLD.created_at <> NEW.created_at OR
                   OLD.effective_from <> NEW.effective_from THEN
                    RAISE EXCEPTION 'Activity rate mapping financial and provenance fields are immutable.';
                END IF;

                -- Validate lifecycle transition
                IF OLD.status <> NEW.status THEN
                    IF OLD.status = 'ACTIVE' AND NEW.status = 'SUPERSEDED' THEN
                        NULL;
                    ELSE
                        RAISE EXCEPTION 'Illegal activity rate mapping status transition from % to %.', OLD.status, NEW.status;
                    END IF;
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_validate_activity_rate_mapping
        BEFORE INSERT OR UPDATE OR DELETE ON activity_rate_mappings
        FOR EACH ROW
        EXECUTE FUNCTION fn_validate_activity_rate_mapping();
    """)

    # 5.2 Daily Progress Valuation Protection & Binding Trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_protect_daily_progress_valuation()
        RETURNS TRIGGER AS $$
        DECLARE
            map_proj VARCHAR;
            ver_proj VARCHAR;
            rep_stat VARCHAR;
            ver_stat VARCHAR;
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF OLD.certified_certificate_id IS NOT NULL THEN
                    RAISE EXCEPTION 'Valuation % bound to certified certificate cannot be deleted.', OLD.id;
                END IF;
                RETURN OLD;
            END IF;

            IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
                -- Validate cross-project references
                SELECT project_id INTO map_proj FROM activity_rate_mappings WHERE id = NEW.activity_rate_mapping_id;
                IF map_proj <> NEW.project_id THEN
                    RAISE EXCEPTION 'Mapping project % does not match valuation project %.', map_proj, NEW.project_id;
                END IF;

                SELECT project_id INTO ver_proj FROM daily_activity_progress_verifications WHERE id = NEW.verification_id;
                IF ver_proj <> NEW.project_id THEN
                    RAISE EXCEPTION 'Verification project % does not match valuation project %.', ver_proj, NEW.project_id;
                END IF;

                -- Validate report status is FINALIZED
                SELECT dpr.submission_status INTO rep_stat
                FROM daily_activity_progress_verifications dapv
                JOIN daily_activity_progress dap ON dap.id = dapv.daily_activity_progress_id
                JOIN daily_progress_reports dpr ON dpr.id = dap.daily_report_id
                WHERE dapv.id = NEW.verification_id;

                IF rep_stat IS NULL OR rep_stat <> 'FINALIZED' THEN
                    RAISE EXCEPTION 'Valuation requires a FINALIZED DailyProgressReport. Current status: %.', rep_stat;
                END IF;

                -- Validate verification status is not PENDING
                SELECT dapv.verification_status INTO ver_stat
                FROM daily_activity_progress_verifications dapv
                WHERE dapv.id = NEW.verification_id;

                IF ver_stat = 'PENDING' THEN
                    RAISE EXCEPTION 'Verification in PENDING status is not eligible for valuation.';
                END IF;
            END IF;

            IF TG_OP = 'UPDATE' THEN
                -- Protect certified_certificate_id binding
                IF OLD.certified_certificate_id IS NOT NULL THEN
                    IF NEW.certified_certificate_id IS NULL OR NEW.certified_certificate_id <> OLD.certified_certificate_id THEN
                        RAISE EXCEPTION 'Bound valuation % cannot be cleared or rebound to another certificate.', OLD.id;
                    END IF;
                    -- If bound, financial fields are completely immutable
                    IF OLD.contractor_claimed_quantity <> NEW.contractor_claimed_quantity OR
                       OLD.supervisor_certified_quantity <> NEW.supervisor_certified_quantity OR
                       OLD.applied_rate_value <> NEW.applied_rate_value OR
                       OLD.contractor_claimed_value <> NEW.contractor_claimed_value OR
                       OLD.certified_progress_value <> NEW.certified_progress_value OR
                       OLD.discrepancy_quantity <> NEW.discrepancy_quantity OR
                       OLD.disputed_valuation_exposure <> NEW.disputed_valuation_exposure OR
                       OLD.quantity_unit <> NEW.quantity_unit OR
                       OLD.applied_rate_unit <> NEW.applied_rate_unit OR
                       OLD.currency <> NEW.currency OR
                       OLD.unit_conversion_factor <> NEW.unit_conversion_factor THEN
                        RAISE EXCEPTION 'Valuation bound to certified certificate cannot be modified.';
                    END IF;
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_protect_daily_progress_valuation
        BEFORE INSERT OR UPDATE OR DELETE ON daily_progress_valuations
        FOR EACH ROW
        EXECUTE FUNCTION fn_protect_daily_progress_valuation();
    """)

    # 5.3 Non-Overlapping Certified Periods Trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_check_cert_period_overlap()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.certificate_status = 'CERTIFIED' THEN
                IF EXISTS (
                    SELECT 1 FROM period_progress_certificates
                    WHERE project_id = NEW.project_id
                      AND certificate_status = 'CERTIFIED'
                      AND id <> NEW.id
                      AND daterange(period_start_date, period_cut_off_date, '[]') && 
                          daterange(NEW.period_start_date, NEW.period_cut_off_date, '[]')
                ) THEN
                    RAISE EXCEPTION 'Certified period date range [%, %] overlaps with an existing certified certificate in project %.',
                        NEW.period_start_date, NEW.period_cut_off_date, NEW.project_id;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_check_cert_period_overlap
        BEFORE INSERT OR UPDATE ON period_progress_certificates
        FOR EACH ROW
        EXECUTE FUNCTION fn_check_cert_period_overlap();
    """)

    # 5.4 Period Progress Certificate Immutability & Total Validation Trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_protect_period_progress_certificate()
        RETURNS TRIGGER AS $$
        DECLARE
            sum_cert NUMERIC(18, 4);
            sum_claim NUMERIC(18, 4);
            sum_disp NUMERIC(18, 4);
            cnt INTEGER;
            prev_cum_cert NUMERIC(18, 4);
            prev_cum_claim NUMERIC(18, 4);
            prev_cum_disp NUMERIC(18, 4);
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF OLD.certificate_status IN ('CERTIFIED', 'SUPERSEDED') THEN
                    RAISE EXCEPTION 'Cannot delete CERTIFIED or SUPERSEDED certificate %.', OLD.id;
                END IF;
                RETURN OLD;
            END IF;

            IF TG_OP = 'INSERT' THEN
                IF NEW.baseline_start_date IS NULL THEN
                    RAISE EXCEPTION 'BASELINE_START_DATE_REQUIRED: baseline_start_date cannot be null.';
                END IF;
                IF NEW.period_start_date > NEW.period_cut_off_date THEN
                    RAISE EXCEPTION 'period_start_date cannot be greater than period_cut_off_date.';
                END IF;
            END IF;

            IF TG_OP = 'UPDATE' THEN
                IF OLD.certificate_status = 'CERTIFIED' THEN
                    IF NEW.certificate_status = 'SUPERSEDED' THEN
                        -- Validate that ONLY status and supersession metadata changed
                        IF OLD.certificate_number <> NEW.certificate_number OR
                           OLD.certificate_type <> NEW.certificate_type OR
                           OLD.project_id <> NEW.project_id OR
                           OLD.monitoring_baseline_id <> NEW.monitoring_baseline_id OR
                           OLD.baseline_schedule_id <> NEW.baseline_schedule_id OR
                           OLD.baseline_schedule_version <> NEW.baseline_schedule_version OR
                           OLD.baseline_schedule_algorithm_version <> NEW.baseline_schedule_algorithm_version OR
                           OLD.baseline_start_date <> NEW.baseline_start_date OR
                           OLD.period_start_date <> NEW.period_start_date OR
                           OLD.period_cut_off_date <> NEW.period_cut_off_date OR
                           OLD.currency <> NEW.currency OR
                           OLD.period_claimed_value <> NEW.period_claimed_value OR
                           OLD.period_certified_value <> NEW.period_certified_value OR
                           OLD.period_disputed_exposure <> NEW.period_disputed_exposure OR
                           OLD.cumulative_claimed_value <> NEW.cumulative_claimed_value OR
                           OLD.cumulative_certified_value <> NEW.cumulative_certified_value OR
                           OLD.cumulative_disputed_exposure <> NEW.cumulative_disputed_exposure OR
                           OLD.item_count <> NEW.item_count OR
                           OLD.valuation_snapshot_hash <> NEW.valuation_snapshot_hash OR
                           OLD.algorithm_version <> NEW.algorithm_version OR
                           OLD.certified_by IS DISTINCT FROM NEW.certified_by OR
                           OLD.certified_at IS DISTINCT FROM NEW.certified_at OR
                           OLD.created_at <> NEW.created_at THEN
                            RAISE EXCEPTION 'Superseding CERTIFIED certificate cannot modify any snapshot or financial fields.';
                        END IF;
                    ELSE
                        RAISE EXCEPTION 'CERTIFIED certificate % is permanently immutable.', OLD.id;
                    END IF;
                ELSIF OLD.certificate_status = 'SUPERSEDED' THEN
                    RAISE EXCEPTION 'SUPERSEDED certificate % is permanently immutable.', OLD.id;
                ELSIF OLD.certificate_status = 'DRAFT' AND NEW.certificate_status = 'CERTIFIED' THEN
                    -- Certification validations
                    IF NEW.certified_by IS NULL OR NEW.certified_at IS NULL THEN
                        RAISE EXCEPTION 'Certification requires certified_by and certified_at.';
                    END IF;

                    -- Period totals reconstruction validation
                    SELECT COALESCE(SUM(certified_amount), 0),
                           COALESCE(SUM(claimed_amount), 0),
                           COALESCE(SUM(disputed_exposure), 0),
                           COUNT(*)
                    INTO sum_cert, sum_claim, sum_disp, cnt
                    FROM period_certificate_items
                    WHERE certificate_id = NEW.id;

                    IF NEW.period_certified_value <> sum_cert OR
                       NEW.period_claimed_value <> sum_claim OR
                       NEW.period_disputed_exposure <> sum_disp OR
                       NEW.item_count <> cnt THEN
                        RAISE EXCEPTION 'Certificate period totals do not match sum of items.';
                    END IF;

                    -- Cumulative totals reconstruction validation
                    SELECT cumulative_certified_value, cumulative_claimed_value, cumulative_disputed_exposure
                    INTO prev_cum_cert, prev_cum_claim, prev_cum_disp
                    FROM period_progress_certificates
                    WHERE project_id = NEW.project_id
                      AND certificate_status = 'CERTIFIED'
                      AND period_cut_off_date < NEW.period_start_date
                    ORDER BY period_cut_off_date DESC, created_at DESC
                    LIMIT 1;

                    IF prev_cum_cert IS NULL THEN
                        prev_cum_cert := 0;
                        prev_cum_claim := 0;
                        prev_cum_disp := 0;
                    END IF;

                    IF NEW.cumulative_certified_value <> (prev_cum_cert + NEW.period_certified_value) OR
                       NEW.cumulative_claimed_value <> (prev_cum_claim + NEW.period_claimed_value) OR
                       NEW.cumulative_disputed_exposure <> (prev_cum_disp + NEW.period_disputed_exposure) THEN
                        RAISE EXCEPTION 'Certificate cumulative totals inconsistent with previous certified certificate in project %.', NEW.project_id;
                    END IF;
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_protect_period_progress_certificate
        BEFORE INSERT OR UPDATE OR DELETE ON period_progress_certificates
        FOR EACH ROW
        EXECUTE FUNCTION fn_protect_period_progress_certificate();
    """)

    # 5.5 Period Certificate Item Protection Trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_protect_period_certificate_item()
        RETURNS TRIGGER AS $$
        DECLARE
            p_status VARCHAR;
            p_curr VARCHAR;
            p_start DATE;
            p_cutoff DATE;
            p_proj VARCHAR;
            v_date DATE;
            v_proj VARCHAR;
        BEGIN
            IF TG_OP = 'DELETE' THEN
                SELECT certificate_status INTO p_status
                FROM period_progress_certificates
                WHERE id = OLD.certificate_id;

                IF p_status IN ('CERTIFIED', 'SUPERSEDED') THEN
                    RAISE EXCEPTION 'Cannot delete items from CERTIFIED or SUPERSEDED certificate %.', OLD.certificate_id;
                END IF;
                RETURN OLD;
            END IF;

            -- Check parent certificate
            SELECT certificate_status, currency, period_start_date, period_cut_off_date, project_id
            INTO p_status, p_curr, p_start, p_cutoff, p_proj
            FROM period_progress_certificates
            WHERE id = NEW.certificate_id;

            IF p_status IN ('CERTIFIED', 'SUPERSEDED') THEN
                RAISE EXCEPTION 'Cannot insert or modify items for CERTIFIED or SUPERSEDED certificate %.', NEW.certificate_id;
            END IF;

            IF NEW.currency <> p_curr THEN
                RAISE EXCEPTION 'Item currency % must match certificate currency %.', NEW.currency, p_curr;
            END IF;

            -- Verify valuation belongs to same project and report date is within certificate period
            SELECT dpr.report_date, dpv.project_id INTO v_date, v_proj
            FROM daily_progress_valuations dpv
            JOIN daily_activity_progress_verifications dapv ON dapv.id = dpv.verification_id
            JOIN daily_activity_progress dap ON dap.id = dapv.daily_activity_progress_id
            JOIN daily_progress_reports dpr ON dpr.id = dap.daily_report_id
            WHERE dpv.id = NEW.valuation_id;

            IF v_proj <> p_proj THEN
                RAISE EXCEPTION 'Cross-project valuation item forbidden.';
            END IF;

            IF v_date < p_start OR v_date > p_cutoff THEN
                RAISE EXCEPTION 'Valuation report date % is outside certificate window [%, %].', v_date, p_start, p_cutoff;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_protect_period_certificate_item
        BEFORE INSERT OR UPDATE OR DELETE ON period_certificate_items
        FOR EACH ROW
        EXECUTE FUNCTION fn_protect_period_certificate_item();
    """)


def downgrade() -> None:
    """Downgrade schema - remove Phase 1L objects in reverse order."""
    # 1. Drop triggers and functions
    op.execute("DROP TRIGGER IF EXISTS trg_protect_period_certificate_item ON period_certificate_items;")
    op.execute("DROP FUNCTION IF EXISTS fn_protect_period_certificate_item();")

    op.execute("DROP TRIGGER IF EXISTS trg_protect_period_progress_certificate ON period_progress_certificates;")
    op.execute("DROP FUNCTION IF EXISTS fn_protect_period_progress_certificate();")

    op.execute("DROP TRIGGER IF EXISTS trg_check_cert_period_overlap ON period_progress_certificates;")
    op.execute("DROP FUNCTION IF EXISTS fn_check_cert_period_overlap();")

    op.execute("DROP TRIGGER IF EXISTS trg_protect_daily_progress_valuation ON daily_progress_valuations;")
    op.execute("DROP FUNCTION IF EXISTS fn_protect_daily_progress_valuation();")

    op.execute("DROP TRIGGER IF EXISTS trg_validate_activity_rate_mapping ON activity_rate_mappings;")
    op.execute("DROP FUNCTION IF EXISTS fn_validate_activity_rate_mapping();")

    # 2. Drop tables in reverse order
    op.drop_table('period_certificate_items')
    op.drop_table('daily_progress_valuations')
    op.drop_table('period_progress_certificates')
    op.drop_table('activity_rate_mappings')
