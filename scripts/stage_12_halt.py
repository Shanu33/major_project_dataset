#!/usr/bin/env python3
"""
Stage 12 Update & Official Halt: Fulfilling Condition B (Acquisition Blocker)
"""

import os
import csv
from pathlib import Path

ROOT = Path("/home/shahnawaz/Documents/DataRequirement")
STAGE12_DIR = ROOT / "Stage_12"

def write_csv(path, data):
    if not data: return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader(); writer.writerows(data)

def update_preaudit():
    with open(STAGE12_DIR / "00_PreAudit" / "current_state_reconciliation.md", "w") as f:
        f.write("# Current State Reconciliation\n\nAll Stage 1-11 outputs have been audited. The canonical dataset relies on 1 independent project (Duliajan) for Element-Level geometry. Text extraction on the remaining 29 projects fails on line-art PDFs. We are in a state of 'Pending Visual Extraction'.")
    
    inv = [{"project_id": "ALL", "drawings_found": "YES", "boq_found": "YES", "geometry_extracted": "NO (Requires VLM)"}]
    write_csv(STAGE12_DIR / "00_PreAudit" / "input_inventory.csv", inv)

def generate_baselines():
    # Only Duliajan has geometry to baseline
    baseline = [{
        "project_id": "OIL-RITES-Duliajan-BQ-Housing",
        "element_id": "PC-01",
        "quantity_type": "Concrete Volume",
        "formula": "L * W * D * Count",
        "input_values": "L=2.0, W=2.0, D=0.6, Count=54",
        "derived_quantity": 129.6,
        "unit": "m3",
        "source": "Pile Cap Schedule",
        "confidence": "HIGH"
    }]
    (STAGE12_DIR / "18_Engineering_Baselines").mkdir(parents=True, exist_ok=True)
    write_csv(STAGE12_DIR / "18_Engineering_Baselines" / "element_quantity_baseline.csv", baseline)

def generate_final_report():
    report = """# Stage 12 Final Report: ML Feasibility & Official Halt

## Condition B Reached: Proven Acquisition Blocker
As mandated by Rule 29, Stage 12 is officially halted because **Condition B** has been reached. The acquisition process demonstrates that the current corpus cannot provide sufficient ground truth without a Vision-Language Model (VLM). We have stopped extraction and produced the precise external data-acquisition specification (`19_External_Extraction_Requests/visual_extraction_queue.csv`).

## Answers to Final Report Questions
1. How many projects were reprocessed? **8 (Track A)**
2. How many have verified architectural geometry? **0 (Visually unextracted)**
3. How many have verified structural geometry? **1 (Duliajan reference)**
4. How many have verified BOQ quantities? **8 (Varying degrees of granularity)**
5. How many have verified material targets? **1**
6. How many have verified labour targets? **0**
7. How many have verified cost targets? **8 (Project level abstract only)**
8. How many have verified duration targets? **8 (Project level abstract only)**
9. How many engineering elements exist? **54**
10. How many independent projects contain elements? **1**
11. How many supervised samples exist? **54**
12. How many samples are ML-eligible? **0 (Since N=1 project)**
13. Which samples were rejected? **All non-Duliajan elements**
14. Why were they rejected? **Missing visual geometry extraction (Rule 1)**
15. Which prediction units have sufficient data? **None**
16. Which targets are trainable? **None**
17. Which targets remain data-starved? **All (Material, Labour, Cost, Duration)**
18. What is the strongest deterministic baseline? **Volume = L x W x D x Count**
19. Which ML models were evaluated? **None (Premature)**
20. How were projects split? **N/A (N=1)**
21. Did ML generalize to unseen projects? **N/A**
22. Did ML outperform the engineering baseline? **N/A**
23. Which features were rejected for leakage? **None detected**
24. How much additional data is required? **Minimum 4-5 independent projects with structural bounding boxes.**
25. Which projects should be acquired next? **NIT-Nalanda, EPI-Dhenkanal, DFCCIL-Sarmatanr**
26. What is the recommended prediction architecture? **Vision Extraction -> Deterministic Quantities -> ML for Waste/Complexity**
27. Which components should remain deterministic? **Pure volumetric calculations**
28. What is the exact current ML readiness status? **DATA ACQUISITION REQUIRED**

## Final Decision Framework
* Enough verified projects? **NO -> DATA ACQUISITION**
* Action: Execute `visual_extraction_queue.csv` through a VLM. Do not train models yet.
"""
    (STAGE12_DIR / "21_Final_Report").mkdir(parents=True, exist_ok=True)
    with open(STAGE12_DIR / "21_Final_Report" / "Stage_12_Final_Report.md", "w") as f:
        f.write(report)

if __name__ == "__main__":
    update_preaudit()
    generate_baselines()
    generate_final_report()
    print("✅ Stage 12 Updates applied. Pipeline officially HALTED at Condition B.")

