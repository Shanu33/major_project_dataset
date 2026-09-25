"""
Download authentic tender volumes and BoG award minutes for IIT Hyderabad Faculty Housing
Project: Construction of Precast 2 Nos. Faculty Housing Towers (G+12),
3 Nos. Staff Housing Towers (G+12) and 3 Nos. Hostel Blocks (G+6) RCC Structures at IIT Hyderabad
"""

import os
import sys
import shutil
import requests

BASE_DIR = r"c:\Users\shahnawaz khan\OneDrive\Documents\DataRequirement\IIT-Hyderabad-Faculty-Housing"

FILES_TO_DOWNLOAD = [
    {
        "url": "https://www.iith.ac.in/assets/files/pdf/BoG_MoM/IITH%2041st%20BoG%20Meeting%20Minutes-Revised.pdf",
        "dest": os.path.join(BASE_DIR, "00_Core_Intelligence_Dataset", "IITH_41st_BoG_Meeting_Minutes_Contract_Award_Teemage.pdf")
    },
    {
        "url": "https://www.iith.ac.in/assets/files/tenders/volume_01_notice_inviting_tender_special_conditions_of_contract.pdf",
        "dest": os.path.join(BASE_DIR, "01_Tender_NIT_PreBid", "Volume_01_Notice_Inviting_Tender_Special_Conditions_of_Contract.pdf")
    },
    {
        "url": "https://www.iith.ac.in/assets/files/tenders/volume_06_general_conditions_epc.pdf",
        "dest": os.path.join(BASE_DIR, "01_Tender_NIT_PreBid", "Volume_06_General_Conditions_EPC.pdf")
    },
    {
        "url": "https://www.iith.ac.in/assets/files/tenders/General_Conditions_Contract.pdf",
        "dest": os.path.join(BASE_DIR, "01_Tender_NIT_PreBid", "General_Conditions_Contract_IITH.pdf")
    },
    {
        "url": "https://www.iith.ac.in/assets/files/tenders/volume_02_b_payment_schedule_annexure.pdf",
        "dest": os.path.join(BASE_DIR, "02_Cost_BOQ_Makes", "Volume_02_b_Payment_Schedule_Annexure.pdf")
    },
    {
        "url": "https://www.iith.ac.in/assets/files/tenders/volume_03_technical_specs_civil_works.pdf",
        "dest": os.path.join(BASE_DIR, "03_Technical_Specifications_Reports", "Volume_03_Technical_Specs_Civil_Works.pdf")
    },
    {
        "url": "https://www.iith.ac.in/assets/files/tenders/volume_04_scope_tech_specs_em_components.pdf",
        "dest": os.path.join(BASE_DIR, "06_MEP_Services", "Volume_04_Scope_Tech_Specs_EM_Components.pdf")
    },
    {
        "url": "https://www.iith.ac.in/assets/files/tenders/volume_05_concept_drawings_subsoil_report.pdf",
        "dest": os.path.join(BASE_DIR, "04_Architectural_Drawings", "Volume_05_Concept_Drawings_Subsoil_Report.pdf")
    }
]

def download_file(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    fname = os.path.basename(dest)
    print(f"Starting download: {fname}...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    with requests.get(url, headers=headers, stream=True, timeout=60) as r:
        r.raise_for_status()
        total_len = int(r.headers.get("content-length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    pct = (downloaded / total_len * 100) if total_len > 0 else 0
                    sys.stdout.write(f"\r  Downloaded: {downloaded / (1024*1024):.1f} MB / {total_len / (1024*1024):.1f} MB ({pct:.1f}%)")
                    sys.stdout.flush()
    print(f"\nCompleted {fname}: {os.path.getsize(dest):,} bytes.")

def main():
    print("=== Downloading Official IIT Hyderabad Tender Volumes ===")
    for item in FILES_TO_DOWNLOAD:
        if os.path.exists(item["dest"]) and os.path.getsize(item["dest"]) > 1000:
            print(f"Already exists: {os.path.basename(item['dest'])} ({os.path.getsize(item['dest']):,} bytes)")
            continue
        download_file(item["url"], item["dest"])

    # Copy Volume 05 to Structural Drawings for geotechnical and foundation reference
    v5_src = os.path.join(BASE_DIR, "04_Architectural_Drawings", "Volume_05_Concept_Drawings_Subsoil_Report.pdf")
    v5_dst = os.path.join(BASE_DIR, "05_Structural_Drawings", "Volume_05_Concept_Drawings_Subsoil_Report_Structural_Foundation.pdf")
    if os.path.exists(v5_src) and not os.path.exists(v5_dst):
        shutil.copy2(v5_src, v5_dst)
        print(f"Copied Volume 05 to Structural Drawings: {v5_dst}")

    print("\nAll downloads finished successfully!")

if __name__ == "__main__":
    main()

