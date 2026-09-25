import os
import csv

project_root = '/home/shahnawaz/Documents/DataRequirement/NIT-Nalanda'
files_to_check = []

for root, _, files in os.walk(project_root):
    for f in files:
        if f.endswith('.pdf') or f.endswith('.csv'):
            files_to_check.append(os.path.join(root, f))

csv_path = os.path.join(project_root, '09_Calculation_Audit', 'source_evidence_register.csv')

with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow([
        'document_id', 'document_category', 'filename', 'relative_path', 'file_size_bytes',
        'project_identity_match', 'selected_scope_match', 'authority_status',
        'usable_for_model_input', 'usable_as_training_target_evidence', 'notes'
    ])
    
    doc_idx = 1
    for path in sorted(files_to_check):
        rel_path = os.path.relpath(path, project_root)
        filename = os.path.basename(path)
        size = os.path.getsize(path)
        
        category = "CSV Dataset" if filename.endswith('.csv') else "PDF Document"
        usable_for_model = "YES" if "00_Core_Intelligence_Dataset" not in rel_path and ("04_" in rel_path or "05_" in rel_path or "finalnit" in filename.lower() or "specifications" in filename.lower()) else "NO"
        usable_target = "YES" if "boq" in filename.lower() or "ecpt" in filename.lower() else "NO"
        if usable_target == "YES":
            usable_for_model = "NO"

        writer.writerow([
            f"NAL-DOC-{doc_idx:03d}",
            category,
            filename,
            rel_path,
            size,
            "YES",
            "PARTIAL",
            "OFFICIAL_DOCUMENT",
            usable_for_model,
            usable_target,
            ""
        ])
        doc_idx += 1
