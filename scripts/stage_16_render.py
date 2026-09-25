#!/usr/bin/env python3
import os
import csv
from pathlib import Path

try:
    import fitz
    HAVE_FITZ = True
except ImportError:
    HAVE_FITZ = False

ROOT = Path("/home/shahnawaz/Documents/DataRequirement")
STAGE16_DIR = ROOT / "Stage_16"
DIRS = [
    "00_PreAudit", "01_Previous_State_Reconciliation", "02_Project_Prioritization",
    "03_Rendered_Drawings", "04_Visual_Ground_Truth", "05_Engineering_Elements",
    "06_BOQ_Element_Mapping", "07_Quantity_Reconstruction", "08_BOQ_Geometry_Validation",
    "09_Targets", "10_Feature_Matrix", "11_Prediction_Tasks", "12_Supervised_Datasets",
    "13_Validation", "14_Provenance", "15_Quarantine", "16_Dataset_Readiness",
    "17_Engineering_Baselines", "18_Final_Report"
]

def setup_dirs():
    for d in DIRS:
        (STAGE16_DIR / d).mkdir(parents=True, exist_ok=True)

def render_candidates():
    if not HAVE_FITZ:
        print("PyMuPDF not found. Cannot render.")
        return

    projects_and_pdfs = {
        "EPI-Dhenkanal-ICDS-Staff-Quarters": ["volume02.pdf", "Volume3.pdf"],
        "DFCCIL-Sarmatanr-Larabad-Koderma-Quarters": ["Tender_Document_Larabad.pdf"],
        "MHDC-PMAY-Khairi-Kamptee-Nagpur": ["VolumeIK-P1.pdf"],
        "TCIL-NVS-JNV-Azamgarh-Quarters": ["Volume2_Financial_Bid_BOQ_Drawings.pdf"]
    }

    out_dir = STAGE16_DIR / "03_Rendered_Drawings"
    
    for proj, files in projects_and_pdfs.items():
        proj_dir = ROOT / proj
        for file in files:
            # Recursively find the file
            found = list(proj_dir.rglob(file))
            if found:
                pdf_path = found[0]
                try:
                    doc = fitz.open(pdf_path)
                    # Just render pages 10, 11, 20 to find drawings/BOQs
                    # (Drawings are often later in the tender, BOQs are often scattered)
                    # Let's render the first 15 pages to find something, or specific pages if doc is large.
                    pages_to_render = [0, 1, 2, 5, 10, 15, 20] 
                    for p in pages_to_render:
                        if p < len(doc):
                            page = doc[p]
                            pix = page.get_pixmap(dpi=100)
                            out_name = f"{proj}_{file}_page{p+1}.png"
                            pix.save(str(out_dir / out_name))
                            print(f"Rendered {out_name}")
                    doc.close()
                except Exception as e:
                    print(f"Failed to render {pdf_path}: {e}")

if __name__ == "__main__":
    setup_dirs()
    render_candidates()
    print("Stage 16 Directories Created and Candidate Renderings Completed.")

