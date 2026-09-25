#!/usr/bin/env python3
"""
Download the 7 Core Intelligence Benchmark files for OIL / RITES Duliajan BQ Workmen Housing.
Saves them both to 00_Core_Intelligence_Dataset and to their designated discipline directories.
"""

import os
import sys
import ssl
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CORE_DIR = os.path.join(BASE_DIR, "00_Core_Intelligence_Dataset")

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

CORE_FILES = [
    {
        "filename": "NIT_9_pdf-2025-Aug-28-17-28-23.pdf",
        "url": "https://www.rites.com/Upload/Tender/NIT_9_pdf-2025-Aug-28-17-28-23.pdf",
        "category": "01_Tender_NIT_Contract/01_NIT_Conditions",
        "label": "1. NIT (full conditions)"
    },
    {
        "filename": "Technical_Bid_pdf-2025-Aug-28-19-39-38.pdf",
        "url": "https://www.rites.com/Upload/Tender/Technical_Bid_pdf-2025-Aug-28-19-39-38.pdf",
        "category": "01_Tender_NIT_Contract/02_Technical_Bid_Volume",
        "label": "2. Technical Bid (full tender / specs volume)"
    },
    {
        "filename": "DBR_pdf-2025-Aug-28-17-46-57.pdf",
        "url": "https://www.rites.com/Upload/Tender/DBR_pdf-2025-Aug-28-17-46-57.pdf",
        "category": "03_Specs_DBR_Finishes/Design_Basis_Report_DBR",
        "label": "3. Design Basis Report (DBR)"
    },
    {
        "filename": "BoQ_1_pdf-2025-Aug-28-17-27-34.pdf",
        "url": "https://www.rites.com/Upload/Tender/BoQ_1_pdf-2025-Aug-28-17-27-34.pdf",
        "category": "02_Cost_BOQ_EPC/BoQ_Part_1",
        "label": "4. BOQ Part 1 (EPC Lump-sum Scope)"
    },
    {
        "filename": "Tender_drawing_3_pdf-2025-Aug-28-17-39-16.pdf",
        "url": "https://www.rites.com/Upload/Tender/Tender_drawing_3_pdf-2025-Aug-28-17-39-16.pdf",
        "category": "05_Tender_Drawings/Vol_3_Structural_Housing_GuestHouse",
        "label": "5. Drawing 3 — Structural Housing & GH"
    },
    {
        "filename": "Tender_drawing_4_pdf-2025-Aug-28-17-39-32.pdf",
        "url": "https://www.rites.com/Upload/Tender/Tender_drawing_4_pdf-2025-Aug-28-17-39-32.pdf",
        "category": "05_Tender_Drawings/Vol_4_Structural_CommunityCentre_Electrical_MEP",
        "label": "6. Drawing 4 — Structural & Electrical MEP"
    },
    {
        "filename": "GT_report_pdf-2025-Aug-28-17-46-44.pdf",
        "url": "https://www.rites.com/Upload/Tender/GT_report_pdf-2025-Aug-28-17-46-44.pdf",
        "category": "04_Survey_Geotech/Geotechnical_Investigation",
        "label": "7. GT Report (310 pages geotechnical)"
    }
]

def download_file(item, index, total):
    fname = item["filename"]
    url = item["url"]
    lbl = item["label"]
    
    core_target = os.path.join(CORE_DIR, fname)
    cat_target = os.path.join(BASE_DIR, item["category"].replace("/", os.sep), fname)
    
    print(f"[{index}/{total}] Fetching: {lbl} ({fname})...")
    
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.rites.com/"
    })
    try:
        with urllib.request.urlopen(req, timeout=45, context=ssl_ctx) as resp:
            data = resp.read()
            
        with open(core_target, "wb") as f:
            f.write(data)
            
        os.makedirs(os.path.dirname(cat_target), exist_ok=True)
        with open(cat_target, "wb") as f:
            f.write(data)
            
        print(f"    [OK] Downloaded {len(data):,} bytes successfully!")
        return True
    except Exception as e:
        print(f"    [FAIL] Failed to download {fname}: {e}")
        return False

def main():
    print("=" * 75)
    print("OIL / RITES DULIAJAN WORKMEN HOUSING - CORE BENCHMARK DATASET DOWNLOADER")
    print("=" * 75)
    os.makedirs(CORE_DIR, exist_ok=True)
    
    success = 0
    for idx, item in enumerate(CORE_FILES, start=1):
        if download_file(item, idx, len(CORE_FILES)):
            success += 1
            
    print("-" * 75)
    print(f"Completed! {success}/{len(CORE_FILES)} files saved to:")
    print(f"  -> {CORE_DIR}")
    print("=" * 75)

if __name__ == "__main__":
    main()

