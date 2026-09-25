#!/usr/bin/env python3
"""
Core Benchmark Downloader & Verifier for EPI Trimbakeshwar EMRS.
Tender Ref: WRO/CON/EMRS/872/334 | Client: NESTS | Executing Agency: EPI (WRO Mumbai)
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
        "url": "https://epi.gov.in/admin/image/tenders/1709981684_NIT334Rev.pdf",
        "name": "1709981684_NIT334Rev.pdf",
        "min_size": 20000000
    },
    {
        "url": "https://epi.gov.in/admin/image/tenders/1705477492_TenderNotice.pdf",
        "name": "1705477492_TenderNotice.pdf",
        "min_size": 500000
    }
]

def main():
    print("=" * 80)
    print("EPI TRIMBAKESHWAR EMRS - CORE BENCHMARK VERIFIER & DOWNLOADER")
    print("=" * 80)

    for item in CORE_FILES:
        target = os.path.join(CORE_DIR, item["name"])
        if os.path.exists(target) and os.path.getsize(target) >= item["min_size"]:
            print(f"[VERIFIED] Present: {item['name']:<40} ({os.path.getsize(target):,} bytes)")
        else:
            print(f"[FETCHING] Downloading {item['name']} from {item['url']}...")
            try:
                req = urllib.request.Request(item["url"], headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=120, context=ssl_ctx) as resp:
                    data = resp.read()
                with open(target, "wb") as f:
                    f.write(data)
                print(f"[OK] Downloaded {item['name']} ({len(data):,} bytes)")
            except Exception as e:
                print(f"[ERROR] Failed downloading {item['name']}: {e}")

    pdf_files = [f for f in os.listdir(CORE_DIR) if f.endswith(".pdf")]
    print("\nCataloged PDF files in 00_Core_Intelligence_Dataset:")
    for idx, f in enumerate(sorted(pdf_files), start=1):
        sz = os.path.getsize(os.path.join(CORE_DIR, f))
        print(f" [{idx:02d}/{len(pdf_files):02d}] [OK] {f:<55} ({sz:,} bytes)")

    print("=" * 80)
    print("Core dataset verification complete.")
    print("=" * 80)

if __name__ == "__main__":
    main()

