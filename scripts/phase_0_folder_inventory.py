#!/usr/bin/env python3
"""
Phase 0 — Folder Inventory & File Census
Scans all project directories under DataRequirement and produces phase_0_folder_inventory.csv.
Cross-verifies against construction_intelligence_master_catalog.csv.
"""

import csv
import json
import os
import sys
from pathlib import Path

ROOT = Path("/home/shahnawaz/Documents/DataRequirement")
OUTPUT_DIR = ROOT / "13_Corpus_Audit"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Directories to exclude from project scanning
EXCLUDE_DIRS = {"scripts", "tmp", "Civil-Estimation-Training-Dataset-v1", "__pycache__"}
EXCLUDE_FILES = {"desktop.ini", "README.md", "construction_intelligence_master_catalog.csv",
                 "construction_intelligence_master_catalog.json", "30_PROJECT_REFINEMENT_REPORT.csv"}


def get_file_stats(project_dir: Path) -> dict:
    """Walk a project directory and collect file statistics."""
    total_files = 0
    total_size = 0
    pdf_count = 0
    csv_count = 0
    json_count = 0
    md_count = 0
    html_count = 0
    png_count = 0
    gitkeep_count = 0
    py_count = 0
    ps1_count = 0
    other_count = 0
    max_pdf_size = 0
    max_pdf_name = ""

    for dirpath, dirnames, filenames in os.walk(project_dir):
        for f in filenames:
            fp = Path(dirpath) / f
            try:
                fsize = fp.stat().st_size
            except OSError:
                fsize = 0

            total_files += 1
            total_size += fsize
            ext = fp.suffix.lower()

            if ext == ".pdf":
                pdf_count += 1
                if fsize > max_pdf_size:
                    max_pdf_size = fsize
                    max_pdf_name = f
            elif ext == ".csv":
                csv_count += 1
            elif ext == ".json":
                json_count += 1
            elif ext == ".md":
                md_count += 1
            elif ext == ".html":
                html_count += 1
            elif ext == ".png":
                png_count += 1
            elif ext in (".py",):
                py_count += 1
            elif ext in (".ps1",):
                ps1_count += 1
            elif f == ".gitkeep":
                gitkeep_count += 1
            else:
                other_count += 1

    return {
        "total_files": total_files,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "pdf_count": pdf_count,
        "csv_count": csv_count,
        "json_count": json_count,
        "md_count": md_count,
        "html_count": html_count,
        "png_count": png_count,
        "gitkeep_count": gitkeep_count,
        "py_count": py_count,
        "ps1_count": ps1_count,
        "other_count": other_count,
        "max_pdf_size_mb": round(max_pdf_size / (1024 * 1024), 2),
        "max_pdf_name": max_pdf_name,
    }


def check_key_files(project_dir: Path) -> dict:
    """Check for the presence of key metadata and control files."""
    checks = {}
    checks["has_readme"] = (project_dir / "README.md").exists()
    checks["has_file_manifest_csv"] = (project_dir / "file_manifest.csv").exists()
    checks["has_file_manifest_json"] = (project_dir / "file_manifest.json").exists()

    # Check multiple possible locations for project_metadata.json
    pm_locations = [
        project_dir / "project_metadata.json",
        project_dir / "07_Final_Prototype_Dataset" / "project_metadata.json",
        project_dir / "00_Core_Intelligence_Dataset" / "project_metadata.json",
    ]
    checks["has_project_metadata"] = any(p.exists() for p in pm_locations)

    # Check for selected_tower_inputs.json
    sti_locations = [
        project_dir / "selected_tower_inputs.json",
        project_dir / "07_Final_Prototype_Dataset" / "selected_tower_inputs.json",
    ]
    checks["has_selected_tower_inputs"] = any(p.exists() for p in sti_locations)

    # Check for scope lock
    scope_locations = [
        project_dir / "00_Project_Control" / "selected_scope.md",
        project_dir / "10_Controlled_Transcription" / "second_pilot_phase_1_document_audit" / "selected_scope_lock.md",
    ]
    checks["has_scope_lock"] = any(p.exists() for p in scope_locations)

    # Identify folder pattern
    top_dirs = sorted([d.name for d in project_dir.iterdir() if d.is_dir()])
    standard_dirs = {"00_Core_Intelligence_Dataset", "01_Tender_NIT_PreBid", "02_Cost_BOQ_Makes",
                     "03_Technical_Specifications_Reports", "04_Architectural_Drawings",
                     "05_Structural_Drawings", "06_MEP_Services", "07_Landscape_Infrastructure",
                     "08_Execution_Actuals", "99_Unverified_or_Related_References"}
    has_standard = len(standard_dirs.intersection(set(top_dirs))) >= 8

    # Check for extended pipeline dirs (Duliajan-style)
    extended_dirs = {"09_Calculation_Audit", "10_Controlled_Transcription",
                     "11_Estimation_Readiness", "12_Evidence_Recovery_Package"}
    has_extended = len(extended_dirs.intersection(set(top_dirs))) >= 2

    # Check for dual-track / package-based dirs
    has_descriptive = any(d for d in top_dirs if not d.startswith(("0", "1", "9", "scripts", "scratch", "tmp", ".")))

    if has_extended:
        checks["folder_pattern"] = "extended_pipeline"
    elif has_standard and has_descriptive:
        checks["folder_pattern"] = "hybrid_dual_track"
    elif has_standard:
        checks["folder_pattern"] = "standard_10"
    else:
        checks["folder_pattern"] = "non_standard"

    checks["top_level_dir_count"] = len(top_dirs)

    return checks


def load_master_catalog() -> dict:
    """Load the master catalog CSV for cross-verification."""
    catalog = {}
    catalog_path = ROOT / "construction_intelligence_master_catalog.csv"
    if catalog_path.exists():
        with open(catalog_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                folder = row.get("folder_name", "").strip()
                if folder:
                    catalog[folder] = {
                        "catalog_id": row.get("id", ""),
                        "catalog_classification": row.get("classification", ""),
                        "catalog_completeness": row.get("completeness_score", ""),
                        "catalog_tender_cost_cr": row.get("tender_cost_cr", ""),
                        "catalog_floors_units": row.get("floors_units", ""),
                    }
    return catalog


def load_refinement_report() -> dict:
    """Load the 30-project refinement report for cross-verification."""
    report = {}
    report_path = ROOT / "30_PROJECT_REFINEMENT_REPORT.csv"
    if report_path.exists():
        with open(report_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                project = row.get("Project", "").strip()
                if project:
                    report[project] = {
                        "refinement_class": row.get("Current class", ""),
                        "refinement_scope": row.get("Selected building scope", ""),
                        "refinement_missing": row.get("Missing critical files", ""),
                        "refinement_confidence": row.get("Verification confidence", ""),
                        "refinement_next_action": row.get("Next action", ""),
                    }
    return report


def main():
    catalog = load_master_catalog()
    refinement = load_refinement_report()

    # Find all project directories
    project_dirs = []
    for entry in sorted(ROOT.iterdir()):
        if entry.is_dir() and entry.name not in EXCLUDE_DIRS:
            project_dirs.append(entry)

    rows = []
    discrepancies = []

    for pdir in project_dirs:
        folder_name = pdir.name
        stats = get_file_stats(pdir)
        checks = check_key_files(pdir)
        cat_info = catalog.get(folder_name, {})
        ref_info = refinement.get(folder_name, {})

        row = {
            "project_id": cat_info.get("catalog_id", "NOT_IN_CATALOG"),
            "folder_name": folder_name,
            "total_files": stats["total_files"],
            "total_size_mb": stats["total_size_mb"],
            "pdf_count": stats["pdf_count"],
            "csv_count": stats["csv_count"],
            "json_count": stats["json_count"],
            "md_count": stats["md_count"],
            "html_count": stats["html_count"],
            "png_count": stats["png_count"],
            "gitkeep_count": stats["gitkeep_count"],
            "max_pdf_size_mb": stats["max_pdf_size_mb"],
            "max_pdf_name": stats["max_pdf_name"],
            "has_readme": checks["has_readme"],
            "has_file_manifest_csv": checks["has_file_manifest_csv"],
            "has_file_manifest_json": checks["has_file_manifest_json"],
            "has_project_metadata": checks["has_project_metadata"],
            "has_selected_tower_inputs": checks["has_selected_tower_inputs"],
            "has_scope_lock": checks["has_scope_lock"],
            "folder_pattern": checks["folder_pattern"],
            "top_level_dir_count": checks["top_level_dir_count"],
            "catalog_classification": cat_info.get("catalog_classification", "NOT_IN_CATALOG"),
            "catalog_completeness": cat_info.get("catalog_completeness", ""),
            "catalog_tender_cost_cr": cat_info.get("catalog_tender_cost_cr", ""),
            "refinement_class": ref_info.get("refinement_class", "NOT_IN_REPORT"),
            "refinement_scope": ref_info.get("refinement_scope", ""),
            "refinement_missing": ref_info.get("refinement_missing", ""),
        }
        rows.append(row)

        # Cross-verification checks
        if folder_name not in catalog:
            discrepancies.append(f"DISCREPANCY: {folder_name} exists on disk but NOT in master catalog")
        if folder_name not in refinement:
            discrepancies.append(f"DISCREPANCY: {folder_name} exists on disk but NOT in refinement report")

        # Check if catalog claims are consistent with actual files
        if cat_info:
            completeness = cat_info.get("catalog_completeness", "")
            if "100%" in completeness and stats["pdf_count"] == 0:
                discrepancies.append(
                    f"DISCREPANCY: {folder_name} — catalog claims 100% completeness but 0 PDFs on disk")
            if "100%" in completeness and stats["max_pdf_size_mb"] < 0.01 and stats["pdf_count"] > 0:
                discrepancies.append(
                    f"DISCREPANCY: {folder_name} — catalog claims 100% but all PDFs are <10 KB (likely stubs)")

    # Write inventory CSV
    output_path = OUTPUT_DIR / "phase_0_folder_inventory.csv"
    fieldnames = list(rows[0].keys()) if rows else []
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Phase 0 inventory written to: {output_path}")
    print(f"   Projects scanned: {len(rows)}")
    print(f"   Total files across corpus: {sum(r['total_files'] for r in rows)}")
    print(f"   Total size: {sum(r['total_size_mb'] for r in rows):.1f} MB")
    print(f"   Total PDFs: {sum(r['pdf_count'] for r in rows)}")
    print(f"   Total CSVs: {sum(r['csv_count'] for r in rows)}")
    print()

    # Print discrepancies
    if discrepancies:
        print(f"⚠️  {len(discrepancies)} cross-verification discrepancies found:")
        for d in discrepancies:
            print(f"   {d}")
    else:
        print("✅ No cross-verification discrepancies found.")

    # Print summary table
    print()
    print("=" * 120)
    print(f"{'Folder':<50} {'Files':>5} {'PDFs':>4} {'CSVs':>4} {'MaxPDF':>8} {'Pattern':<20} {'Catalog Class':<25}")
    print("=" * 120)
    for r in rows:
        print(f"{r['folder_name']:<50} {r['total_files']:>5} {r['pdf_count']:>4} {r['csv_count']:>4} "
              f"{r['max_pdf_size_mb']:>7.1f}M {r['folder_pattern']:<20} {r['catalog_classification']:<25}")


if __name__ == "__main__":
    main()

