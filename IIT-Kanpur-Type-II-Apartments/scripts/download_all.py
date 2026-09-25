#!/usr/bin/env python3
"""
Bulk Downloader & Drive Guide for IIT Kanpur Type-II Apartments Tender Package.
Reads file_manifest.json and handles downloading direct files and provides references for Drive assets.
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
    print("IIT KANPUR TYPE-II APARTMENTS - REPOSITORY SYNCHRONIZER")
    print("=" * 75)

    if not os.path.exists(MANIFEST_PATH):
        print("Manifest not found!")
        sys.exit(1)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print(f"Total manifest records: {len(manifest)}")
    
    # Download direct files (from iitk.ac.in)
    direct_files = [x for x in manifest if "iitk.ac.in" in x["url"]]
    drive_files = [x for x in manifest if "drive.google.com" in x["url"]]

    for item in direct_files:
        fn = item["filename"]
        url = item["url"]
        cat = item["category_path"]
        target = os.path.join(BASE_DIR, cat.replace("/", os.sep), fn)
        os.makedirs(os.path.dirname(target), exist_ok=True)

        if os.path.exists(target) and os.path.getsize(target) > 1000:
            print(f"[SKIP] {fn:<40} (Already exists: {os.path.getsize(target):,} bytes)")
        else:
            print(f"[FETCH] {fn} from {url}...")
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                with urllib.request.urlopen(req, timeout=40, context=ssl_ctx) as resp:
                    data = resp.read()
                with open(target, "wb") as f:
                    f.write(data)
                print(f"    [OK] Downloaded {len(data):,} bytes")
            except Exception as e:
                print(f"    [FAIL] Error downloading: {e}")

    print("\n" + "=" * 75)
    print(f"Google Drive Drawings Notice ({len(drive_files)} drawing files):")
    print("All architectural, structural, and electrical drawing sheets are hosted on:")
    print("  -> https://drive.google.com/drive/folders/1-3XgCAKZ4VkDADDHG_qNN9pnY-TEA3lS?usp=sharing")
    print("You can download the zip directly from Google Drive and unpack it into:")
    print(f"  -> {os.path.join(BASE_DIR, '05_Drawings')}")
    print("=" * 75)

if __name__ == "__main__":
    main()

