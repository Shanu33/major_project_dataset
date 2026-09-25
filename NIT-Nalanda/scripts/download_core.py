#!/usr/bin/env python3
"""
Download the 7 Core Intelligence Dataset benchmark files for Nalanda University Package 1C.
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
        "filename": "finalnit25-03-17.pdf",
        "url": "https://nalandauniv.edu.in/wp-content/uploads/2019/07/finalnit25-03-17.pdf",
        "category": "01_Tender_NIT_PreBid/02_NIT_Conditions",
        "label": "1. NIT (full conditions)"
    },
    {
        "filename": "05.-boq-schedule-b-combined.pdf",
        "url": "https://nalandauniv.edu.in/wp-content/uploads/2019/07/05.-boq-schedule-b-combined.pdf",
        "category": "02_Cost_BOQ_Makes/02_BOQ_Schedules/Combined_BOQ",
        "label": "2. Combined BOQ (best single BOQ)"
    },
    {
        "filename": "nalanda-residential-specifications-part-i-civil-works.pdf",
        "url": "https://nalandauniv.edu.in/wp-content/uploads/2019/07/nalanda-residential-specifications-part-i-civil-works.pdf",
        "category": "03_Technical_Specifications_Reports/Specifications/Part_I_Civil_Works",
        "label": "3. Specs Part I — Civil"
    },
    {
        "filename": "nalanda-residential-specifications-part-ii-services.pdf",
        "url": "https://nalandauniv.edu.in/wp-content/uploads/2019/07/nalanda-residential-specifications-part-ii-services.pdf",
        "category": "03_Technical_Specifications_Reports/Specifications/Part_II_Services",
        "label": "4. Specs Part II — Services"
    },
    {
        "filename": "02.-ecpt.pdf",
        "url": "https://nalandauniv.edu.in/wp-content/uploads/2019/07/02.-ecpt.pdf",
        "category": "02_Cost_BOQ_Makes/01_Estimated_Cost_ECPT",
        "label": "5. Estimated cost (ECPT)"
    },
    {
        "filename": "a.2.1-type-1b-ground-floor-plan.pdf",
        "url": "https://nalandauniv.edu.in/wp-content/uploads/2019/07/a.2.1-type-1b-ground-floor-plan.pdf",
        "category": "04_Architectural_Drawings/01_Faculty_Apartments/Type_1B",
        "label": "6. Type 1B GF plan"
    },
    {
        "filename": "1.1-pile-layout-and-details-for-faculty-housing-appt-type-1b-.pdf",
        "url": "https://nalandauniv.edu.in/wp-content/uploads/2019/07/1.1-pile-layout-and-details-for-faculty-housing-appt-type-1b-.pdf",
        "category": "05_Structural_Drawings/01_Faculty_Housing_Apartments/Type_1B",
        "label": "7. Type 1B pile layout"
    }
]

def download_file(item, index, total):
    fname = item["filename"]
    url = item["url"]
    lbl = item["label"]
    
    core_target = os.path.join(CORE_DIR, fname)
    cat_target = os.path.join(BASE_DIR, item["category"].replace("/", os.sep), fname)
    
    print(f"[{index}/{total}] Fetching: {lbl} ({fname})...")
    
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    try:
        with urllib.request.urlopen(req, timeout=45, context=ssl_ctx) as resp:
            data = resp.read()
            
        # Write to Core directory
        with open(core_target, "wb") as f:
            f.write(data)
            
        # Also copy to Category directory
        os.makedirs(os.path.dirname(cat_target), exist_ok=True)
        with open(cat_target, "wb") as f:
            f.write(data)
            
        print(f"    [OK] Downloaded {len(data):,} bytes successfully!")
        return True
    except Exception as e:
        print(f"    [FAIL] Failed to download {fname}: {e}")
        return False

def main():
    print("=" * 70)
    print("NALANDA UNIVERSITY PACKAGE 1C - CORE BENCHMARK DATASET DOWNLOADER")
    print("=" * 70)
    os.makedirs(CORE_DIR, exist_ok=True)
    
    success = 0
    for idx, item in enumerate(CORE_FILES, start=1):
        if download_file(item, idx, len(CORE_FILES)):
            success += 1
            
    print("-" * 70)
    print(f"Completed! {success}/{len(CORE_FILES)} files saved to:")
    print(f"  -> {CORE_DIR}")
    print("=" * 70)

if __name__ == "__main__":
    main()

