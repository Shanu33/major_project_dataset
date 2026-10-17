"""phase_1i_final_hardening_baseline_anchor

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-10-05 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Phase 1I Final Hardening Pass: Baseline Calendar Anchor & Integrity."""
    # 1. Add baseline_start_date column to monitoring_baselines
    op.add_column('monitoring_baselines', sa.Column('baseline_start_date', sa.Date(), nullable=True))

    # 2. Backfill baseline_start_date strictly from explicit metadata if already present; do NOT fabricate dates
    op.execute("""
        CREATE OR REPLACE FUNCTION safe_cast_to_date(val text) RETURNS date AS $$
        BEGIN
            RETURN val::date;
        EXCEPTION
            WHEN OTHERS THEN
                RETURN NULL;
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
    """)

    op.execute("""
        UPDATE monitoring_baselines
        SET baseline_start_date = safe_cast_to_date(metadata_json->>'baseline_start_date')
        WHERE metadata_json IS NOT NULL
          AND safe_cast_to_date(metadata_json->>'baseline_start_date') IS NOT NULL;
    """)

    op.execute("DROP FUNCTION IF EXISTS safe_cast_to_date(text);")

    # 3. Add partial unique index ensuring only one ACTIVE baseline per project at the database level
    op.create_index(
        'uq_monitoring_baseline_active_per_project',
        'monitoring_baselines',
        ['project_id'],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'")
    )

    # 4. Update Monitoring Baseline Immutability Trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_protect_monitoring_baseline()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Monitoring baselines are historical and cannot be deleted.';
            ELSIF TG_OP = 'UPDATE' THEN
                IF OLD.id <> NEW.id OR
                   OLD.project_id <> NEW.project_id OR
                   OLD.schedule_id <> NEW.schedule_id OR
                   OLD.schedule_version <> NEW.schedule_version OR
                   OLD.schedule_algorithm_version <> NEW.schedule_algorithm_version OR
                   OLD.baseline_start_date IS DISTINCT FROM NEW.baseline_start_date OR
                   OLD.frozen_by <> NEW.frozen_by OR
                   OLD.frozen_at <> NEW.frozen_at THEN
                    RAISE EXCEPTION 'Monitoring baseline historical attributes cannot be modified.';
                END IF;

                IF OLD.status <> NEW.status THEN
                    IF OLD.status = 'ACTIVE' AND NEW.status <> 'SUPERSEDED' THEN
                        RAISE EXCEPTION 'Active monitoring baselines may only transition to SUPERSEDED.';
                    END IF;

                    IF OLD.status = 'SUPERSEDED' THEN
                        RAISE EXCEPTION 'Superseded monitoring baselines cannot change status.';
                    END IF;

                    IF OLD.status = 'REJECTED' THEN
                        RAISE EXCEPTION 'Rejected monitoring baselines cannot change status.';
                    END IF;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """Downgrade schema - Revert Phase 1I Final Hardening Pass."""
    # 1. Revert trigger to b2c3d4e5f6a7 definition
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_protect_monitoring_baseline()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Monitoring baselines are historical and cannot be deleted.';
            ELSIF TG_OP = 'UPDATE' THEN
                IF OLD.id <> NEW.id OR
                   OLD.project_id <> NEW.project_id OR
                   OLD.schedule_id <> NEW.schedule_id OR
                   OLD.schedule_version <> NEW.schedule_version OR
                   OLD.schedule_algorithm_version <> NEW.schedule_algorithm_version OR
                   OLD.frozen_by <> NEW.frozen_by OR
                   OLD.frozen_at <> NEW.frozen_at THEN
                    RAISE EXCEPTION 'Monitoring baseline historical attributes cannot be modified.';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # 2. Drop partial unique index
    op.drop_index('uq_monitoring_baseline_active_per_project', table_name='monitoring_baselines')

    # 3. Drop column baseline_start_date
    op.drop_column('monitoring_baselines', 'baseline_start_date')

