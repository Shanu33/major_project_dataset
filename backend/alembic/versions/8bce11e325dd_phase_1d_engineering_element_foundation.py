"""phase_1d_engineering_element_foundation

Revision ID: 8bce11e325dd
Revises: 66a6e5154ae8
Create Date: 2026-10-04 01:27:24.450425

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8bce11e325dd'
down_revision: Union[str, Sequence[str], None] = '66a6e5154ae8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Create engineering_elements table
    op.create_table(
        'engineering_elements',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('element_type', sa.String(), nullable=False),
        sa.Column('element_name', sa.String(), nullable=False),
        sa.Column('source_document_id', sa.String(), nullable=True),
        sa.Column('source_page_id', sa.String(), nullable=True),
        sa.Column('source_fact_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='ACTIVE'),
        sa.Column('verification_status', sa.String(), nullable=False, server_default='PENDING'),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_document_id'], ['documents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['source_page_id'], ['document_pages.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['source_fact_id'], ['extracted_facts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_engineering_elements_project', 'engineering_elements', ['project_id'])
    op.create_index('ix_engineering_elements_type', 'engineering_elements', ['project_id', 'element_type'])

    # 2. Create engineering_element_revisions table
    op.create_table(
        'engineering_element_revisions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('element_id', sa.String(), nullable=False),
        sa.Column('revision_number', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('element_type', sa.String(), nullable=False),
        sa.Column('element_name', sa.String(), nullable=False),
        sa.Column('source_document_id', sa.String(), nullable=True),
        sa.Column('source_page_id', sa.String(), nullable=True),
        sa.Column('source_fact_id', sa.String(), nullable=True),
        sa.Column('verification_status', sa.String(), nullable=False, server_default='PENDING'),
        sa.Column('revision_note', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['element_id'], ['engineering_elements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_document_id'], ['documents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['source_page_id'], ['document_pages.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['source_fact_id'], ['extracted_facts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('uq_element_revision_num', 'engineering_element_revisions', ['element_id', 'revision_number'], unique=True)
    op.create_index('ix_element_revisions_fact', 'engineering_element_revisions', ['source_fact_id'])

    # 3. Create immutability trigger for engineering_element_revisions
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_prevent_element_revision_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Engineering element revisions are immutable and cannot be updated or deleted.';
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER prevent_element_revision_modification_trg
        BEFORE UPDATE OR DELETE ON engineering_element_revisions
        FOR EACH ROW
        EXECUTE FUNCTION trg_prevent_element_revision_modification();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS prevent_element_revision_modification_trg ON engineering_element_revisions;")
    op.execute("DROP FUNCTION IF EXISTS trg_prevent_element_revision_modification();")

    op.drop_index('ix_element_revisions_fact', table_name='engineering_element_revisions')
    op.drop_index('uq_element_revision_num', table_name='engineering_element_revisions')
    op.drop_table('engineering_element_revisions')

    op.drop_index('ix_engineering_elements_type', table_name='engineering_elements')
    op.drop_index('ix_engineering_elements_project', table_name='engineering_elements')
    op.drop_table('engineering_elements')

