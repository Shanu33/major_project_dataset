#!/usr/bin/env python3
"""
Full Package Synchronizer for DFCCIL Jaipur Staff Quarters.
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
    print("DFCCIL JAIPUR STAFF QUARTERS - FULL REPOSITORY SYNCHRONIZER")
    print("=" * 75)

    if not os.path.exists(MANIFEST_PATH):
        print("Error: Manifest file not found!")
        sys.exit(1)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print(f"Total manifest cataloged records: {len(manifest)}")
    present = 0

    for idx, item in enumerate(manifest, start=1):
        fname = item["filename"]
        cat = item["category"]
        p = os.path.join(BASE_DIR, cat.replace("/", os.sep), fname)
        if os.path.exists(p) and os.path.getsize(p) > 500:
            print(f"[{idx}/{len(manifest)}] [PRESENT] {fname:<55} ({os.path.getsize(p):,} bytes)")
            present += 1
        else:
            print(f"[{idx}/{len(manifest)}] [PENDING] {fname:<55}")

    print("=" * 75)
    print(f"SUMMARY: Present: {present}/{len(manifest)} verified cataloged files.")
    print("=" * 75)

if __name__ == "__main__":
    main()
