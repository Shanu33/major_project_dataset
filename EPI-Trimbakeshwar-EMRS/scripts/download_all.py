#!/usr/bin/env python3
"""
Full Package Synchronizer & Manifest Verifier for EPI Trimbakeshwar EMRS.
Tender Ref: WRO/CON/EMRS/872/334 | Client: NESTS | Executing Agency: EPI
"""

import os
import sys
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MANIFEST_PATH = os.path.join(BASE_DIR, "file_manifest.json")

def main():
    print("=" * 80)
    print("EPI TRIMBAKESHWAR EMRS - FULL REPOSITORY SYNCHRONIZER & INTEGRITY AUDIT")
    print("=" * 80)

    if not os.path.exists(MANIFEST_PATH):
        print("[ERROR] Manifest file not found at:", MANIFEST_PATH)
        sys.exit(1)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print(f"Total manifest cataloged records: {len(manifest)}\n")
    present_count = 0

    for idx, item in enumerate(manifest, start=1):
        fname = item["filename"]
        cat = item["category"]
        p = os.path.join(BASE_DIR, cat.replace("/", os.sep), fname)
        if os.path.exists(p) and os.path.getsize(p) > 200:
            sz = os.path.getsize(p)
            print(f" [{idx:02d}/{len(manifest):02d}] [PRESENT]  {cat:<45} / {fname:<45} ({sz:,} bytes)")
            present_count += 1
        else:
            print(f" [{idx:02d}/{len(manifest):02d}] [MISSING]  {cat:<45} / {fname:<45}")

    print("\n" + "=" * 80)
    print(f"SUMMARY AUDIT: Verified {present_count}/{len(manifest)} cataloged files in repository.")
    print("=" * 80)

if __name__ == "__main__":
    main()

