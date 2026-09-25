import os

base = "/home/shahnawaz/Documents/DataRequirement/Stage_19"

files = {
    "18_Final_Report/project_acquisition_score.csv": "project_id,drawing_status,structural_status,boq_status,quantity_detail,provenance,completeness,status",
    "18_Final_Report/document_integrity_register.csv": "document_id,project_id,filename,file_size,page_count,sha256_hash,is_corrupt,duplicate_status,acquisition_channel",
    "18_Final_Report/project_linkage_matrix.csv": "project_id,drawing_set_id,boq_id,linkage_status,confidence",
    "18_Final_Report/drawing_register.csv": "document_id,project_id,drawing_type,page_count,visual_verification_status",
    "18_Final_Report/boq_register.csv": "document_id,project_id,boq_type,item_count,verification_status",
    "18_Final_Report/engineering_elements.csv": "element_id,project_id,drawing_id,element_type,dimensions,origin",
    "18_Final_Report/boq_element_mapping.csv": "element_id,boq_item_id,project_id,mapping_status,verification_method",
    "18_Final_Report/feature_matrix_X.csv": "element_id,project_id,element_type,dim_l,dim_w,dim_d,volume,origin",
    "18_Final_Report/target_matrix_Y.csv": "element_id,project_id,boq_quantity,boq_unit,boq_rate,boq_amount",
    "18_Final_Report/provenance_log.csv": "document_id,project_id,source_url,acquisition_timestamp,acquired_by",
    "18_Final_Report/validation_log.csv": "validation_id,project_id,check_type,status,message",
    "18_Final_Report/project_independence_matrix.csv": "project_id,is_independent,group_id,notes",
    "18_Final_Report/dataset_quality_report.csv": "metric,value,notes"
}

for rel_path, header in files.items():
    full_path = os.path.join(base, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(header + "\n")

print("CSVs initialized.")
