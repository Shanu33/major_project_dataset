"""phase_1c_data_integrity_and_immutability

Revision ID: 66a6e5154ae8
Revises: 4f7dff80930a
Create Date: 2026-10-03 21:12:09.353705

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66a6e5154ae8'
down_revision: Union[str, Sequence[str], None] = '4f7dff80930a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Update Evidence.locator to JSON and adjust unique index for JSON expression
    op.drop_index('uq_evidence_identity', table_name='evidence')
    op.execute("""
        ALTER TABLE evidence 
        ALTER COLUMN locator TYPE JSON 
        USING CASE 
            WHEN locator IS NULL OR locator = '' THEN NULL 
            WHEN locator ~ '^\\s*[\\[\\{]' THEN locator::json 
            ELSE to_json(locator) 
        END;
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_evidence_identity 
        ON evidence (document_id, evidence_type, source_reference, ((locator::text)));
    """)

    # 2. Update ExtractedFact.normalized_value to NUMERIC(18, 6)
    op.alter_column('extracted_facts', 'normalized_value', type_=sa.Numeric(18, 6), postgresql_using='normalized_value::numeric(18,6)')

    # 3. Update FactVerification.corrected_value to NUMERIC(18, 6)
    op.alter_column('fact_verifications', 'corrected_value', type_=sa.Numeric(18, 6), postgresql_using='corrected_value::numeric(18,6)')

    # 4. Create immutability trigger for fact_verifications
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_prevent_fact_verification_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Fact verification records are immutable and cannot be updated or deleted.';
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER prevent_fact_verification_modification_trg
        BEFORE UPDATE OR DELETE ON fact_verifications
        FOR EACH ROW
        EXECUTE FUNCTION trg_prevent_fact_verification_modification();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Drop immutability trigger on fact_verifications
    op.execute("DROP TRIGGER IF EXISTS prevent_fact_verification_modification_trg ON fact_verifications;")
    op.execute("DROP FUNCTION IF EXISTS trg_prevent_fact_verification_modification();")

    # 2. Downgrade numeric types to float
    op.alter_column('fact_verifications', 'corrected_value', type_=sa.Float(), postgresql_using='corrected_value::float')
    op.alter_column('extracted_facts', 'normalized_value', type_=sa.Float(), postgresql_using='normalized_value::float')

    # 3. Revert Evidence.locator to VARCHAR and restore original unique index
    op.execute("DROP INDEX IF EXISTS uq_evidence_identity;")
    op.execute("ALTER TABLE evidence ALTER COLUMN locator TYPE VARCHAR USING locator::text;")
    op.create_index('uq_evidence_identity', 'evidence', ['document_id', 'evidence_type', 'source_reference', 'locator'], unique=True)

