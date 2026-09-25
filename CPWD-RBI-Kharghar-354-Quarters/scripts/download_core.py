#!/usr/bin/env python3
"""
Downloader & Verifier for CPWD / RBI Kharghar 354 Staff Quarters Core Benchmark Files.
Verifies the 7 core engineering benchmark PDFs in 00_Core_Intelligence_Dataset.
"""

import os
import sys
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CORE_DIR = os.path.join(BASE_DIR, "00_Core_Intelligence_Dataset")
MANIFEST_PATH = os.path.join(BASE_DIR, "file_manifest.json")

def main():
    print("=" * 75)
    print("CPWD / RBI KHARGHAR 354 STAFF QUARTERS - CORE DATASET VERIFIER")
    print("=" * 75)

    if not os.path.exists(MANIFEST_PATH):
        print(f"Error: Manifest not found at {MANIFEST_PATH}")
        sys.exit(1)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    core_items = [x for x in manifest if x.get("is_core")]
    print(f"Total core benchmark records: {len(core_items)}")

    verified = 0
    for idx, item in enumerate(core_items, start=1):
        fname = item["filename"]
        target = os.path.join(CORE_DIR, fname)
        if os.path.exists(target) and os.path.getsize(target) > 500:
            print(f"[{idx}/{len(core_items)}] [VERIFIED] {fname:<55} ({os.path.getsize(target):,} bytes)")
            verified += 1
        else:
            print(f"[{idx}/{len(core_items)}] [MISSING]  {fname:<55}")

    print("-" * 75)
    print(f"Verification Summary: {verified}/{len(core_items)} core files verified successfully.")
    print("=" * 75)

if __name__ == "__main__":
    main()
