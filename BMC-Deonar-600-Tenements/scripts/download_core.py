#!/usr/bin/env python3
"""
Downloader for BMC Deonar 600-Tenements Core Benchmark Files.
Fetches the official master tender bid document, Building 04 architectural drawing pack,
podium infrastructure drawings, and draft MOU from the official MCGM / BMC portals.
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

CORE_DOWNLOADS = [
    {
        "filename": "ETH_7000022191_020922.pdf",
        "url": "https://www.mcgm.gov.in/irj/go/km/docs/documents/Tenders/ETH/ETH_7000022191_020922.pdf",
        "category": "01_Tender_NIT_Eligibility/01_Main_Bid_Document",
        "label": "Master Bid Document (253 Pages Complete)"
    },
    {
        "filename": "ETH_7000022191_DRAWING-4.pdf",
        "url": "https://portal.mcgm.gov.in/irj/go/km/docs/documents/Tenders/ETH/ETH_7000022191_DRAWING-4.pdf",
        "category": "04_Architectural_Drawings_Building_04/01_Full_Drawing_Set_PDF",
        "label": "Building 04 Complete Architectural Drawings (8 Sheets)"
    },
    {
        "filename": "ETH_7000022191_DRAWING-8.pdf",
        "url": "https://portal.mcgm.gov.in/irj/go/km/docs/documents/Tenders/ETH/ETH_7000022191_DRAWING-8.pdf",
        "category": "05_Podium_Site_Infrastructure_Drawings/01_Full_Podium_Drawing_PDF",
        "label": "Podium Levels P1-P3 & Site Master Plan Drawings (8 Sheets)"
    },
    {
        "filename": "ETH_7000022191_11_130922.pdf",
        "url": "https://r3app.mcgm.gov.in/irj/go/km/docs/documents/Tenders/ETH/ETH_7000022191_11_130922.pdf",
        "category": "02_Project_Scope_BUA_Payment/04_Draft_MOU_Format",
        "label": "Official Joint Venture Draft MOU Format"
    }
]

def main():
    print("=" * 75)
    print("BMC DEONAR 600-TENEMENTS - CORE DATASET DOWNLOADER")
    print("=" * 75)
    os.makedirs(CORE_DIR, exist_ok=True)

    for idx, item in enumerate(CORE_DOWNLOADS, start=1):
        fname = item["filename"]
        url = item["url"]
        lbl = item["label"]
        print(f"[{idx}/{len(CORE_DOWNLOADS)}] Fetching {lbl} ({fname})...")

        core_target = os.path.join(CORE_DIR, fname)
        cat_target = os.path.join(BASE_DIR, item["category"].replace("/", os.sep), fname)

        if os.path.exists(core_target) and os.path.getsize(core_target) > 50000:
            print(f"    [SKIP] Already exists in Core Dataset ({os.path.getsize(core_target):,} bytes)")
            continue

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=60, context=ssl_ctx) as resp:
                data = resp.read()
            with open(core_target, "wb") as f:
                f.write(data)
            os.makedirs(os.path.dirname(cat_target), exist_ok=True)
            with open(cat_target, "wb") as f:
                f.write(data)
            print(f"    [OK] Downloaded {len(data):,} bytes successfully!")
        except Exception as e:
            print(f"    [FAIL] Failed to download {fname}: {e}")

    print("-" * 75)
    print("Core dataset verification complete.")

if __name__ == "__main__":
    main()

