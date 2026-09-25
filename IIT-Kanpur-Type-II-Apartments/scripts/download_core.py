#!/usr/bin/env python3
"""
Downloader for IIT Kanpur Type-II Apartments Core Benchmark Files.
Fetches the official 190-page Master Tender Document and syncs to 00_Core_Intelligence_Dataset.
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
        "filename": "Tenderdocument44D3.pdf",
        "url": "https://iitk.ac.in/iwd/file/2025/44-Composite-D3-2024-25/Tenderdocument44D3.pdf",
        "category": "01_Tender_NIT_Eligibility/01_Master_Tender_Document",
        "label": "Master Tender Document (190 Pages)"
    }
]

def main():
    print("=" * 75)
    print("IIT KANPUR TYPE-II APARTMENTS - CORE DATASET DOWNLOADER")
    print("=" * 75)
    os.makedirs(CORE_DIR, exist_ok=True)
    
    for idx, item in enumerate(CORE_DOWNLOADS, start=1):
        fname = item["filename"]
        url = item["url"]
        lbl = item["label"]
        print(f"[{idx}/{len(CORE_DOWNLOADS)}] Fetching {lbl}...")
        
        core_target = os.path.join(CORE_DIR, fname)
        cat_target = os.path.join(BASE_DIR, item["category"].replace("/", os.sep), fname)
        
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=40, context=ssl_ctx) as resp:
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
    print(f"Drawing packages are accessible via Google Drive:")
    print("  -> https://drive.google.com/drive/folders/1-3XgCAKZ4VkDADDHG_qNN9pnY-TEA3lS?usp=sharing")
    print("=" * 75)

if __name__ == "__main__":
    main()

