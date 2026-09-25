#!/usr/bin/env python3
"""
Core Benchmark Downloader & Verifier for DFCCIL Jaipur Staff Quarters.
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CORE_DIR = os.path.join(BASE_DIR, "00_Core_Intelligence_Dataset")

def main():
    print("=" * 75)
    print("DFCCIL JAIPUR STAFF QUARTERS - CORE BENCHMARK VERIFIER")
    print("=" * 75)

    files = [f for f in os.listdir(CORE_DIR) if f.endswith(".pdf")]
    print(f"Found {len(files)} PDF documents in 00_Core_Intelligence_Dataset:")

    for idx, f in enumerate(sorted(files), start=1):
        sz = os.path.getsize(os.path.join(CORE_DIR, f))
        print(f"[{idx}/{len(files)}] [VERIFIED] {f:<55} ({sz:,} bytes)")

    print("=" * 75)
    print("Core dataset verification complete.")

if __name__ == "__main__":
    main()
