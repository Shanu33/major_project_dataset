#!/usr/bin/env python3
"""
Bulk Downloader for Nalanda University Package 1C Tender Documents (~696 PDFs).
Reads from file_manifest.json and downloads files directly into their structured folders.

Usage:
    python download_all.py                    # Download all files
    python download_all.py --category 01      # Only download category 01 (Tender/NIT)
    python download_all.py --category 04      # Only download Architectural drawings
    python download_all.py --workers 8        # Download using 8 concurrent workers
"""

import os
import sys
import json
import ssl
import argparse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MANIFEST_PATH = os.path.join(BASE_DIR, "file_manifest.json")
CORE_DIR = os.path.join(BASE_DIR, "00_Core_Intelligence_Dataset")

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

def download_item(item, overwrite=False):
    fname = item["filename"]
    url = item["url"]
    cat_rel = item["category_path"]
    
    target_dir = os.path.join(BASE_DIR, cat_rel.replace("/", os.sep))
    target_file = os.path.join(target_dir, fname)
    
    os.makedirs(target_dir, exist_ok=True)
    
    if not overwrite and os.path.exists(target_file) and os.path.getsize(target_file) > 1000:
        return {"status": "SKIPPED", "filename": fname, "size": os.path.getsize(target_file)}
        
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    try:
        with urllib.request.urlopen(req, timeout=45, context=ssl_ctx) as resp:
            data = resp.read()
            
        with open(target_file, "wb") as f:
            f.write(data)
            
        # If it's a core file, also mirror in 00_Core_Intelligence_Dataset
        if item.get("is_core", False):
            os.makedirs(CORE_DIR, exist_ok=True)
            core_file = os.path.join(CORE_DIR, fname)
            with open(core_file, "wb") as f:
                f.write(data)
                
        return {"status": "SUCCESS", "filename": fname, "size": len(data)}
    except Exception as e:
        return {"status": "FAILED", "filename": fname, "error": str(e), "url": url}

def main():
    parser = argparse.ArgumentParser(description="Nalanda University Package 1C Bulk Downloader")
    parser.add_argument("--category", type=str, default="", help="Filter by category prefix (e.g., '01', '04_Architectural', '05')")
    parser.add_argument("--workers", type=int, default=5, help="Number of concurrent download threads (default: 5)")
    parser.add_argument("--overwrite", action="store_true", help="Force overwrite existing downloaded files")
    args = parser.parse_args()

    if not os.path.exists(MANIFEST_PATH):
        print(f"Error: Manifest not found at {MANIFEST_PATH}")
        sys.exit(1)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    if args.category:
        filtered = [item for item in manifest if args.category.lower() in item["category_path"].lower()]
    else:
        filtered = manifest

    total = len(filtered)
    print("=" * 75)
    print(f"NALANDA UNIVERSITY PACKAGE 1C BULK DOWNLOADER")
    print(f"Target files: {total} PDFs | Concurrency: {args.workers} workers | Overwrite: {args.overwrite}")
    if args.category:
        print(f"Category filter: '{args.category}'")
    print("=" * 75)

    downloaded = 0
    skipped = 0
    failed = 0
    failed_items = []

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(download_item, item, args.overwrite): item for item in filtered}
        
        for count, fut in enumerate(as_completed(futures), start=1):
            res = fut.result()
            st = res["status"]
            fn = res["filename"]
            
            if st == "SUCCESS":
                downloaded += 1
                sz_kb = res["size"] / 1024
                print(f"[{count:03d}/{total:03d}] [OK]   {fn:<50} ({sz_kb:,.1f} KB)")
            elif st == "SKIPPED":
                skipped += 1
                print(f"[{count:03d}/{total:03d}] [SKIP] {fn:<50} (Already exists)")
            else:
                failed += 1
                failed_items.append(res)
                print(f"[{count:03d}/{total:03d}] [FAIL] {fn:<50} ERR: {res.get('error')}")

    print("=" * 75)
    print(f"Download Summary: Total: {total} | Success: {downloaded} | Skipped: {skipped} | Failed: {failed}")
    if failed_items:
        print("\nFailed items:")
        for item in failed_items:
            print(f"  - {item['filename']}: {item['error']}")
    print("=" * 75)

if __name__ == "__main__":
    main()

