import os

base = "/home/shahnawaz/Documents/DataRequirement/Stage_20"

files = {
    "01_Project_Inventory/project_inventory.csv": "project_id,project_name,source,drawing_files,boq_files,metadata_present,document_count,acquisition_status,completeness_status",
    "02_Document_Integrity/document_integrity_register.csv": "document_id,project_id,filename,file_type,file_size,page_count,sha256_hash,is_corrupt,duplicate_status,source",
    "03_Project_Linkage/project_linkage_matrix.csv": "project_id,drawing_set_id,boq_id,linkage_status,confidence,reason",
    "06_Engineering_Elements/engineering_elements.csv": "element_id,project_id,element_type,drawing_id,page_number,drawing_reference,length,width,depth_height,diameter,count,material_grade,source_evidence,origin,confidence",
    "05_BOQ_Verification/boq_ground_truth.csv": "boq_item_id,project_id,description,quantity,unit,rate,amount,page_number,source_document,source_evidence",
    "07_BOQ_Element_Mapping/boq_element_mapping.csv": "element_id,boq_item_id,project_id,mapping_status,mapping_reason,drawing_evidence,boq_evidence,confidence",
    "09_Feature_Matrix/feature_matrix_X.csv": "element_id,project_id,element_type,length,width,depth,diameter,perimeter,area,geometric_volume,material_grade,structural_category,complexity_indicators,drawing_derived_attributes,origin",
    "10_Target_Matrix/target_matrix_Y.csv": "element_id,project_id,target_type,quantity,unit,observed_ground_truth,engineering_derived_target,status",
    "11_Leakage_Audit/leakage_audit.csv": "audit_id,project_id,feature_column,target_column,leakage_detected,severity,notes",
    "12_Project_Independence/project_independence_matrix.csv": "project_id,is_independent,group_id,notes",
    "14_Validation/validation_log.csv": "validation_id,project_id,check_type,status,message",
    "15_Provenance/provenance_log.csv": "document_id,project_id,source_url,acquisition_timestamp,acquired_by",
    "13_ML_Eligibility/prediction_task_matrix.csv": "prediction_task,projects,elements,status,evidence",
    "18_Final_Report/dataset_quality_report.csv": "metric,value,notes"
}

for rel_path, header in files.items():
    full_path = os.path.join(base, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(header + "\n")

print("CSVs initialized.")
