"""phase_1h_scheduling_hardening

Revision ID: c7b1a4d8e2f3
Revises: 40fc5bd4f9d4
Create Date: 2026-10-04 21:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7b1a4d8e2f3'
down_revision: Union[str, Sequence[str], None] = '40fc5bd4f9d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Phase 1H Hardening: Activity & Dependency Revisions, Schedule Uniqueness, and Immutability."""
    # 1. Create construction_activity_revisions table
    op.create_table(
        'construction_activity_revisions',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('activity_id', sa.String(), sa.ForeignKey('construction_activities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('revision_number', sa.Integer(), nullable=False),
        sa.Column('activity_code', sa.String(), nullable=False),
        sa.Column('activity_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('activity_type', sa.String(), nullable=False),
        sa.Column('engineering_element_id', sa.String(), sa.ForeignKey('engineering_elements.id', ondelete='SET NULL'), nullable=True),
        sa.Column('duration_value', sa.Numeric(18, 6), nullable=True),
        sa.Column('duration_unit', sa.String(), nullable=True),
        sa.Column('duration_method', sa.String(), nullable=False),
        sa.Column('duration_classification', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('revision_note', sa.Text(), nullable=True),
        sa.UniqueConstraint('activity_id', 'revision_number', name='uq_activity_revision'),
    )
    op.create_index('ix_act_rev_activity', 'construction_activity_revisions', ['activity_id'])
    op.create_index('ix_act_rev_project', 'construction_activity_revisions', ['project_id'])

    # 2. Create activity_dependency_revisions table
    op.create_table(
        'activity_dependency_revisions',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('dependency_id', sa.String(), sa.ForeignKey('activity_dependencies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('revision_number', sa.Integer(), nullable=False),
        sa.Column('predecessor_activity_id', sa.String(), sa.ForeignKey('construction_activities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('successor_activity_id', sa.String(), sa.ForeignKey('construction_activities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dependency_type', sa.String(), nullable=False),
        sa.Column('lag_value', sa.Numeric(18, 6), nullable=False),
        sa.Column('lag_unit', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('revision_note', sa.Text(), nullable=True),
        sa.UniqueConstraint('dependency_id', 'revision_number', name='uq_dependency_revision'),
    )
    op.create_index('ix_dep_rev_dependency', 'activity_dependency_revisions', ['dependency_id'])
    op.create_index('ix_dep_rev_project', 'activity_dependency_revisions', ['project_id'])

    # 3. Add unique constraint on construction_schedules (project_id, schedule_version)
    op.create_unique_constraint(
        'uq_schedule_project_version',
        'construction_schedules',
        ['project_id', 'schedule_version']
    )

    # 4. Backfill existing records if any exist
    op.execute("""
        INSERT INTO construction_activity_revisions (
            id, activity_id, project_id, revision_number, activity_code, activity_name,
            description, activity_type, engineering_element_id, duration_value, duration_unit,
            duration_method, duration_classification, status, metadata_json, created_by,
            created_at, revision_note
        )
        SELECT
            gen_random_uuid()::text, id, project_id, 1, activity_code, activity_name,
            description, activity_type, engineering_element_id, duration_value, duration_unit,
            duration_method, duration_classification, status, metadata_json, created_by,
            created_at, 'Initial activity revision backfill'
        FROM construction_activities
        ON CONFLICT DO NOTHING;
    """)

    op.execute("""
        INSERT INTO activity_dependency_revisions (
            id, dependency_id, project_id, revision_number, predecessor_activity_id,
            successor_activity_id, dependency_type, lag_value, lag_unit, created_by,
            created_at, revision_note
        )
        SELECT
            gen_random_uuid()::text, id, project_id, 1, predecessor_activity_id,
            successor_activity_id, dependency_type, lag_value, lag_unit, created_by,
            created_at, 'Initial dependency revision backfill'
        FROM activity_dependencies
        ON CONFLICT DO NOTHING;
    """)

    # 5. Database triggers for append-only immutability of revisions
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_prevent_activity_revision_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Construction activity revisions are append-only and immutable. Cannot delete revision.';
            ELSIF TG_OP = 'UPDATE' THEN
                RAISE EXCEPTION 'Construction activity revisions are append-only and immutable. Cannot update revision.';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER prevent_activity_revision_modification_trg
        BEFORE UPDATE OR DELETE ON construction_activity_revisions
        FOR EACH ROW
        EXECUTE FUNCTION trg_prevent_activity_revision_modification();
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION trg_prevent_dependency_revision_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Activity dependency revisions are append-only and immutable. Cannot delete revision.';
            ELSIF TG_OP = 'UPDATE' THEN
                RAISE EXCEPTION 'Activity dependency revisions are append-only and immutable. Cannot update revision.';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER prevent_dependency_revision_modification_trg
        BEFORE UPDATE OR DELETE ON activity_dependency_revisions
        FOR EACH ROW
        EXECUTE FUNCTION trg_prevent_dependency_revision_modification();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS prevent_dependency_revision_modification_trg ON activity_dependency_revisions;")
    op.execute("DROP FUNCTION IF EXISTS trg_prevent_dependency_revision_modification();")
    op.execute("DROP TRIGGER IF EXISTS prevent_activity_revision_modification_trg ON construction_activity_revisions;")
    op.execute("DROP FUNCTION IF EXISTS trg_prevent_activity_revision_modification();")

    op.drop_constraint('uq_schedule_project_version', 'construction_schedules', type_='unique')
    op.drop_table('activity_dependency_revisions')
    op.drop_table('construction_activity_revisions')
