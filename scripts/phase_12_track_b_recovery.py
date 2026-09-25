#!/usr/bin/env python3
"""
Track B Lighter Pass — Evidence Recovery Package Generation
For all Track B projects, this script generates the missing evidence request register
based on the gaps identified in the Phase 2 Primary Evidence Audit.
"""

import csv
import os
from pathlib import Path

ROOT = Path("/home/shahnawaz/Documents/DataRequirement")
AUDIT_DIR = ROOT / "13_Corpus_Audit"

def load_triage_decisions() -> dict:
    triage = {}
    path = AUDIT_DIR / "phase_3_triage_decision_register.csv"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                triage[row["project_folder"]] = row
    return triage

def load_evidence_audit() -> dict:
    audit = {}
    path = AUDIT_DIR / "phase_2_primary_evidence_audit.csv"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                audit[row["project_folder"]] = row
    return audit

def generate_track_b_recovery():
    triage = load_triage_decisions()
    audit = load_evidence_audit()

    track_b_projects = [k for k, v in triage.items() if v["assigned_track"] == "B"]
    
    for project in track_b_projects:
        project_dir = ROOT / project
        recovery_dir = project_dir / "12_Evidence_Recovery_Package"
        recovery_dir.mkdir(parents=True, exist_ok=True)
        
        audit_row = audit.get(project, {})
        missing_items = []
        
        # Determine missing items based on Phase 2 evidence
        if audit_row.get("has_real_arch_drawing") != "True":
            missing_items.append({
                "request_id": f"REQ-{project[:5]}-ARCH",
                "priority": "HIGH",
                "missing_document": "Complete Architectural Drawing Set (Floor plans, elevations, sections)",
                "reason": "Required for building entity footprint and envelope modeling."
            })
            
        if audit_row.get("has_real_struct_drawing") != "True":
            missing_items.append({
                "request_id": f"REQ-{project[:5]}-STR",
                "priority": "HIGH",
                "missing_document": "Complete Structural Drawing Set (Foundation, framing, sections)",
                "reason": "Required for structural element quantification and rebar modeling."
            })
            
        if audit_row.get("has_real_boq") != "True":
            missing_items.append({
                "request_id": f"REQ-{project[:5]}-BOQ",
                "priority": "CRITICAL",
                "missing_document": "Itemized Bill of Quantities (BOQ)",
                "reason": "Required for ground-truth training targets and cost analysis."
            })
            
        if audit_row.get("has_real_tender_nit") != "True":
            missing_items.append({
                "request_id": f"REQ-{project[:5]}-NIT",
                "priority": "MEDIUM",
                "missing_document": "Notice Inviting Tender (NIT) / Conditions of Contract",
                "reason": "Required for project scope, metadata, and duration timelines."
            })

        # If a tender exists but drawings/BOQ are missing, it might be embedded
        if audit_row.get("has_real_tender_nit") == "True" and len(missing_items) > 0:
            missing_items.append({
                "request_id": f"REQ-{project[:5]}-EXTRACTION",
                "priority": "HIGH",
                "missing_document": "Deep PDF Extraction of existing Tender Volumes",
                "reason": "Missing drawings or BOQ may be embedded within the main tender PDF."
            })

        csv_path = recovery_dir / "missing_evidence_request_register.csv"
        fieldnames = ["request_id", "priority", "missing_document", "reason"]
        
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            if missing_items:
                writer.writerows(missing_items)
            else:
                # Fallback if no specific gaps flagged but still Track B
                writer.writerow({
                    "request_id": f"REQ-{project[:5]}-GENERAL",
                    "priority": "MEDIUM",
                    "missing_document": "Detailed Engineering Documents",
                    "reason": "Project assigned to Track B. Requires deeper document analysis to promote to Track A."
                })
        
        print(f"Generated Evidence Recovery Package for Track B project: {project}")

if __name__ == "__main__":
    generate_track_b_recovery()

