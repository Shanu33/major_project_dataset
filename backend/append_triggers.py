import sys

filename = sys.argv[1]
with open(filename, 'r') as f:
    content = f.read()

upgrade_trigger = """
    # --- ADDED TRIGGERS ---
    op.execute('''
        CREATE OR REPLACE FUNCTION trg_prevent_update_delete_report()
        RETURNS TRIGGER AS $$
        BEGIN
            IF OLD.is_finalized = true THEN
                RAISE EXCEPTION 'Cannot update or delete a finalized daily report.';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    ''')
    op.execute('''
        CREATE TRIGGER prevent_update_delete_report_trg
        BEFORE UPDATE OR DELETE ON daily_reports
        FOR EACH ROW
        EXECUTE FUNCTION trg_prevent_update_delete_report();
    ''')
    op.execute('''
        CREATE OR REPLACE FUNCTION trg_prevent_audit_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Audit log records are append-only and cannot be updated or deleted.';
        END;
        $$ LANGUAGE plpgsql;
    ''')
    op.execute('''
        CREATE TRIGGER prevent_audit_modification_trg
        BEFORE UPDATE OR DELETE ON audit_log
        FOR EACH ROW
        EXECUTE FUNCTION trg_prevent_audit_modification();
    ''')
"""

downgrade_trigger = """
    # --- REMOVED TRIGGERS ---
    op.execute('DROP TRIGGER IF EXISTS prevent_audit_modification_trg ON audit_log')
    op.execute('DROP FUNCTION IF EXISTS trg_prevent_audit_modification()')
    op.execute('DROP TRIGGER IF EXISTS prevent_update_delete_report_trg ON daily_reports')
    op.execute('DROP FUNCTION IF EXISTS trg_prevent_update_delete_report()')
"""

# Replace in content by finding the end of upgrade() and downgrade()
upgrade_parts = content.split("def downgrade()")
upgrade_body = upgrade_parts[0] + upgrade_trigger + "\n\n"
downgrade_body = "def downgrade()" + downgrade_parts[1] if False else "" # Will do it manually in script

with open(filename, 'w') as f:
    f.write(content.replace("    # ### end Alembic commands ###", downgrade_trigger + "    # ### end Alembic commands ###", 1)) # Wait, this replaces downgrade

