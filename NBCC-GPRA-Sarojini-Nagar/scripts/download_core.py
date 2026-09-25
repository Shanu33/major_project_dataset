#!/usr/bin/env python3
"""
Downloader & Portal Mapper for NBCC GPRA Sarojini Nagar Benchmark Files.
Fetches accessible NIT documents and provides verified links for full Volume packs.
"""

import os
import sys
import json
import ssl
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CORE_DIR = os.path.join(BASE_DIR, "00_Core_Intelligence_Dataset")

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

CORE_ITEMS = [
    {
        "filename": "Tendernotice_1_Pkg_III_Commercial_C.pdf",
        "url": "https://eprocure.gov.in/epublish/app?component=$DirectLink&page=FrontEndViewTender&service=direct&sp=S6lXrtT/fvpG4Tx8e8i2Dtw==",
        "label": "Package III Commercial C Master NIT (₹229.91 Cr)"
    },
    {
        "filename": "Package_VI_Type_V_800Nos_NIT.pdf",
        "url": "https://eprocure.gov.in/epublish/app?page=FrontEndTenderDetailsExternal&service=page&tnid=1086023",
        "label": "Package VI 800 Nos Type-V Residential NIT (₹946.16 Cr)"
    }
]

def main():
    print("=" * 75)
    print("NBCC GPRA SAROJINI NAGAR - CORE DATASET DOWNLOADER & PORTAL MAPPER")
    print("=" * 75)
    os.makedirs(CORE_DIR, exist_ok=True)
    
    for idx, item in enumerate(CORE_ITEMS, start=1):
        fn = item["filename"]
        url = item["url"]
        lbl = item["label"]
        print(f"[{idx}/{len(CORE_ITEMS)}] Checking: {lbl}...")
        
        target = os.path.join(CORE_DIR, fn)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=30, context=ssl_ctx) as resp:
                data = resp.read()
            with open(target, "wb") as f:
                f.write(data)
            print(f"    [OK] Downloaded {len(data):,} bytes successfully!")
        except Exception as e:
            print(f"    [NOTICE] Portal session requirement: {e}")
            print(f"    Direct Portal URL: {url}")

    print("-" * 75)
    print("Full Volumes (I to VIII, ~199 MB RAR) are accessed via:")
    print("  -> Central Public Procurement Portal: https://eprocure.gov.in/")
    print("  -> NBCC RailTel e-Tendering Portal:   https://nbcc.enivida.com/")
    print("=" * 75)

if __name__ == "__main__":
    main()

