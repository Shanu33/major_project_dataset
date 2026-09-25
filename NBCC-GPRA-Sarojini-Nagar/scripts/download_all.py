#!/usr/bin/env python3
"""
Repository Synchronizer & Portal Mapper for NBCC GPRA Sarojini Nagar Mega Packages.
Reads file_manifest.json and manages downloaded files and portal links across all packages.
"""

import os
import sys
import json
import ssl
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MANIFEST_PATH = os.path.join(BASE_DIR, "file_manifest.json")

def main():
    print("=" * 75)
    print("NBCC GPRA SAROJINI NAGAR - REPOSITORY SYNCHRONIZER & PORTAL DIRECTORY")
    print("=" * 75)

    if not os.path.exists(MANIFEST_PATH):
        print("Manifest file not found!")
        sys.exit(1)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print(f"Total cataloged project documents: {len(manifest)}")
    for count, item in enumerate(manifest, start=1):
        fn = item["filename"]
        cat = item["category_path"]
        desc = item["description"]
        print(f"[{count:02d}/{len(manifest):02d}] {cat:<45} -> {fn}")

    print("\n" + "=" * 75)
    print("PROCUREMENT PORTAL AUTHENTICATION & DOWNLOAD NOTICE:")
    print("NBCC contracts (Package III, VI, V-A, V-B, VII-A/B) use encrypted multi-part RAR archives.")
    print("To download the full 199 MB tender volume pack:")
    print("  1. Log in to https://eprocure.gov.in/ or https://nbcc.enivida.com/")
    print("  2. Search by Tender ID (e.g. 2021_NBCC_581502_1 or 2025_NBCC_821574_1)")
    print("  3. Download Tender_Docs.rar and extract into the respective package folder.")
    print("=" * 75)

if __name__ == "__main__":
    main()

