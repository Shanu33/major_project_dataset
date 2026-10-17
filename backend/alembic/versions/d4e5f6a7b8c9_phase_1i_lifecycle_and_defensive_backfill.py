"""phase_1i_lifecycle_and_defensive_backfill

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-10-05 16:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Phase 1I Final Correction Pass: Lifecycle Enforcement & Defensive Backfill."""
    # 1. Defensive backfill: safely handle valid dates, invalid dates (e.g. 2026-99-99), and missing dates
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
        WHERE baseline_start_date IS NULL
          AND metadata_json IS NOT NULL
          AND safe_cast_to_date(metadata_json->>'baseline_start_date') IS NOT NULL;
    """)

    op.execute("DROP FUNCTION IF EXISTS safe_cast_to_date(text);")

    # 2. Update trg_protect_monitoring_baseline() to strictly enforce lifecycle transitions at the DB level
    # Allowed transitions:
    # - ACTIVE -> SUPERSEDED (legitimate application superseding)
    # - ACTIVE -> ACTIVE (no-op)
    # - SUPERSEDED -> SUPERSEDED (no-op)
    # - REJECTED -> REJECTED (no-op)
    # Prohibited transitions:
    # - ACTIVE -> REJECTED
    # - SUPERSEDED -> ACTIVE
    # - SUPERSEDED -> REJECTED
    # - REJECTED -> ACTIVE
    # - REJECTED -> SUPERSEDED
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_protect_monitoring_baseline()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Monitoring baselines are historical and cannot be deleted.';
            ELSIF TG_OP = 'UPDATE' THEN
                -- Protect immutable historical attributes
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

                -- Enforce lifecycle state transitions:
                -- The only valid status transition is ACTIVE -> SUPERSEDED
                -- No-op transitions (OLD.status = NEW.status) are allowed
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
    """Downgrade schema - Revert Phase 1I Final Correction Pass."""
    # Revert trg_protect_monitoring_baseline() to the definition in c3d4e5f6a7b8
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
