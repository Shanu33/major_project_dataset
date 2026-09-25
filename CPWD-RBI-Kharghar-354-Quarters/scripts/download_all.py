#!/usr/bin/env python3
"""
Full Package Synchronizer for CPWD / RBI Kharghar 354 Staff Quarters Repository.
Verifies all files across disciplinary folders against file_manifest.json.
"""

import os
import sys
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MANIFEST_PATH = os.path.join(BASE_DIR, "file_manifest.json")

def main():
    print("=" * 75)
    print("CPWD / RBI KHARGHAR 354 STAFF QUARTERS - FULL REPOSITORY SYNCHRONIZER")
    print("=" * 75)

    if not os.path.exists(MANIFEST_PATH):
        print("Error: file_manifest.json not found!")
        sys.exit(1)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print(f"Total cataloged entries: {len(manifest)}")
    present_count = 0

    for idx, item in enumerate(manifest, start=1):
        fname = item["filename"]
        cat_path = item["category"]
        target = os.path.join(BASE_DIR, cat_path.replace("/", os.sep), fname)
        
        if os.path.exists(target) and os.path.getsize(target) > 500:
            print(f"[{idx}/{len(manifest)}] [PRESENT] {fname} ({os.path.getsize(target):,} bytes)")
            present_count += 1
        else:
            print(f"[{idx}/{len(manifest)}] [PENDING] {fname}")

    print("=" * 75)
    print(f"SUMMARY: Present: {present_count}/{len(manifest)} cataloged files ready.")
    print("=" * 75)

if __name__ == "__main__":
    main()
