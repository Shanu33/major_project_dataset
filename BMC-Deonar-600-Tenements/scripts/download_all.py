#!/usr/bin/env python3
"""
Bulk Downloader & Synchronizer for BMC Deonar 600-Tenements Tender Package.
Reads file_manifest.json and handles downloading all project files and verifying completeness.
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
CORE_DIR = os.path.join(BASE_DIR, "00_Core_Intelligence_Dataset")

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

def main():
    print("=" * 75)
    print("BMC DEONAR 600-TENEMENTS - COMPLETE PACKAGE SYNCHRONIZER")
    print("=" * 75)

    if not os.path.exists(MANIFEST_PATH):
        print(f"Manifest not found at: {MANIFEST_PATH}")
        sys.exit(1)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print(f"Total manifest records: {len(manifest)}")
    
    downloaded_count = 0
    already_present = 0
    failed_count = 0

    for idx, item in enumerate(manifest, start=1):
        fname = item["filename"]
        url = item["url"]
        cat_path = item["category_path"]
        target_path = os.path.join(BASE_DIR, cat_path.replace("/", os.sep), fname)
        core_target = os.path.join(CORE_DIR, fname)
        
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        if os.path.exists(target_path) and os.path.getsize(target_path) > 1000:
            print(f"[{idx}/{len(manifest)}] [PRESENT] {fname} ({os.path.getsize(target_path):,} bytes)")
            already_present += 1
            if item.get("is_core") and not os.path.exists(core_target):
                with open(target_path, "rb") as sf, open(core_target, "wb") as df:
                    df.write(sf.read())
            continue

        print(f"[{idx}/{len(manifest)}] [DOWNLOADING] {fname}...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=60, context=ssl_ctx) as resp:
                data = resp.read()
            with open(target_path, "wb") as f:
                f.write(data)
            if item.get("is_core"):
                with open(core_target, "wb") as f:
                    f.write(data)
            print(f"    [OK] Downloaded {len(data):,} bytes successfully.")
            downloaded_count += 1
        except Exception as e:
            print(f"    [FAIL] Failed to download {fname}: {e}")
            failed_count += 1

    print("=" * 75)
    print(f"SUMMARY: Present: {already_present} | Downloaded: {downloaded_count} | Failed: {failed_count}")
    print("=" * 75)

if __name__ == "__main__":
    main()

