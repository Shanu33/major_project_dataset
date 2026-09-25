#!/usr/bin/env python3
"""
Downloader & Verifier for KMRL Muttom Staff Quarters Core Benchmark Files.
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

CORE_PDF_URL = "https://kochimetro.org/wp-content/uploads/2015/05/NIT-TENDER-DOCUMENT-STAFF-QUARTERS-AT-MUTTOM.pdf"
CORE_PDF_NAME = "NIT-TENDER-DOCUMENT-STAFF-QUARTERS-AT-MUTTOM.pdf"

def main():
    print("=" * 75)
    print("KMRL MUTTOM STAFF QUARTERS - CORE DATASET VERIFIER")
    print("=" * 75)

    target = os.path.join(CORE_DIR, CORE_PDF_NAME)
    if os.path.exists(target) and os.path.getsize(target) > 1000000:
        print(f"[VERIFIED] Master PDF present: {CORE_PDF_NAME} ({os.path.getsize(target):,} bytes)")
    else:
        print(f"[FETCHING] Downloading master tender PDF from {CORE_PDF_URL}...")
        try:
            req = urllib.request.Request(CORE_PDF_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60, context=ssl_ctx) as resp:
                data = resp.read()
            with open(target, "wb") as f:
                f.write(data)
            print(f"[OK] Downloaded {len(data):,} bytes successfully!")
        except Exception as e:
            print(f"[FAIL] Download failed: {e}")

    files = [f for f in os.listdir(CORE_DIR) if f.endswith(".pdf")]
    print(f"Total verified core PDFs in repository: {len(files)}")
    print("=" * 75)

if __name__ == "__main__":
    main()
