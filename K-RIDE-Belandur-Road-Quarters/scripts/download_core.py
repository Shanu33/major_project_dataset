#!/usr/bin/env python3
"""
Downloader for K-RIDE Core Benchmark Files.
Downloads the Belandur Road Station & Facilities Bid Document and the Hosur Staff Quarters Tender Document.
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
        "filename": "Tender-Document-Belandur-Road-Baiyyappanahalli-Station-Building.pdf",
        "url": "https://kride.in/wp-content/uploads/2021/02/Tender-Document-Belandur-Road-Baiyyappanahalli-Station-Building.pdf",
        "category": "01_Tender_NIT_Bidding_Docs/01_Belandur_Road_Station_Tender_Volume",
        "label": "Belandur Road Station & Facilities Complete Bid Volume (313 Pages)"
    },
    {
        "filename": "HSRA-Staff-Quarters-Tender-Document.pdf",
        "url": "https://kride.in/wp-content/uploads/2021/03/HSRA-Staff-Quarters-Tender-Document.pdf",
        "category": "06_Related_Railway_Quarters_HSRA/01_Hosur_Staff_Quarters_Tender_Volume",
        "label": "Hosur Staff Quarters Type-II & Type-III Complete Tender Volume"
    }
]

def main():
    print("=" * 75)
    print("K-RIDE RAILWAY RESIDENTIAL & STATION INFRASTRUCTURE - CORE DOWNLOADER")
    print("=" * 75)
    os.makedirs(CORE_DIR, exist_ok=True)
    
    for idx, item in enumerate(CORE_DOWNLOADS, start=1):
        fname = item["filename"]
        url = item["url"]
        lbl = item["label"]
        print(f"[{idx}/{len(CORE_DOWNLOADS)}] Fetching: {lbl}...")
        
        core_target = os.path.join(CORE_DIR, fname)
        cat_target = os.path.join(BASE_DIR, item["category"].replace("/", os.sep), fname)
        
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=45, context=ssl_ctx) as resp:
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
    print("Core benchmark documents synchronized.")
    print("=" * 75)

if __name__ == "__main__":
    main()

