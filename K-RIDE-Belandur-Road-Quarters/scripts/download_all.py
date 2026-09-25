#!/usr/bin/env python3
"""
Bulk Downloader for K-RIDE Railway Quarters & Station Infrastructure Documents.
Reads file_manifest.json and synchronizes official volumes.
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
    print("K-RIDE RAILWAY INFRASTRUCTURE - REPOSITORY SYNCHRONIZER")
    print("=" * 75)

    if not os.path.exists(MANIFEST_PATH):
        print("Manifest not found!")
        sys.exit(1)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Only distinct downloadable files
    seen = set()
    downloadables = []
    for item in manifest:
        if item["url"].endswith(".pdf") and item["filename"] not in seen:
            seen.add(item["filename"])
            downloadables.append(item)

    print(f"Unique downloadable tender volumes: {len(downloadables)}")

    for count, item in enumerate(downloadables, start=1):
        fn = item["filename"]
        url = item["url"]
        cat = item["category_path"]
        target = os.path.join(BASE_DIR, cat.replace("/", os.sep), fn)
        os.makedirs(os.path.dirname(target), exist_ok=True)

        if os.path.exists(target) and os.path.getsize(target) > 1000:
            print(f"[{count:02d}/{len(downloadables):02d}] [SKIP] {fn:<50} (Already exists: {os.path.getsize(target):,} bytes)")
        else:
            print(f"[{count:02d}/{len(downloadables):02d}] [FETCH] {fn} from {url}...")
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                with urllib.request.urlopen(req, timeout=50, context=ssl_ctx) as resp:
                    data = resp.read()
                with open(target, "wb") as f:
                    f.write(data)
                print(f"    [OK] Saved {len(data):,} bytes successfully!")
            except Exception as e:
                print(f"    [FAIL] Error downloading {fn}: {e}")

    print("=" * 75)
    print("Synchronized all available tender volumes.")
    print("=" * 75)

if __name__ == "__main__":
    main()

