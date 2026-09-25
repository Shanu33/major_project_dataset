#!/usr/bin/env python3
"""
Phase 1 — Document Type Matrix + Phase 2 — Primary Evidence Audit
Combined script that:
1. Classifies every file in every project by document category
2. Performs binary evidence checks per project
3. Generates phase_1_document_type_matrix.csv and phase_2_primary_evidence_audit.csv
"""

import csv
import os
import re
from pathlib import Path

ROOT = Path("/home/shahnawaz/Documents/DataRequirement")
OUTPUT_DIR = ROOT / "13_Corpus_Audit"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EXCLUDE_DIRS = {"scripts", "tmp", "Civil-Estimation-Training-Dataset-v1", "__pycache__", "13_Corpus_Audit"}
EXCLUDE_FILES = {"desktop.ini"}

# Minimum size thresholds (bytes) for "real" documents
MIN_REAL_PDF_SIZE = 100 * 1024  # 100 KB
MIN_SUBSTANTIAL_PDF_SIZE = 5 * 1024 * 1024  # 5 MB
STUB_PDF_MAX_SIZE = 10 * 1024  # 10 KB

# Keywords for classification (case-insensitive)
TENDER_KEYWORDS = [
    "nit", "tender", "notice_inviting", "bid_doc", "gcc", "scc", "corrigendum",
    "prebid", "pre_bid", "contract", "award", "eligibility", "allotment",
    "volume_01", "volume_1", "volume1", "vol_i", "vol_1", "voli",
    "part_a", "part_b", "part_c", "technical_bid",
]
ARCH_KEYWORDS = [
    "architectural", "floor_plan", "site_plan", "elevation", "section",
    "ground_floor", "first_floor", "typical_floor", "unit_plan",
    "ar_td", "arch", "brochure", "layout",
]
STRUCT_KEYWORDS = [
    "structural", "foundation", "pile", "column", "beam", "slab",
    "str_td", "framing", "bbs", "bar_bending", "rebar", "shear_wall",
    "diaphragm",
]
BOQ_KEYWORDS = [
    "boq", "bill_of_quantities", "price_bid", "financial_bid",
    "schedule_b", "item_rate", "rate_schedule", "ecpt",
    "cost_abstract", "estimated_cost",
]
SPEC_KEYWORDS = [
    "specification", "tech_spec", "technical_spec", "dsr",
    "approved_makes", "schedule_of_finishes", "ats",
]
COST_KEYWORDS = [
    "cost", "rate_analysis", "payment", "milestone", "ra_bill",
    "ca_cert", "price", "pricing",
]
SCHEDULE_KEYWORDS = [
    "schedule", "programme", "bar_chart", "cpm", "milestone_schedule",
    "completion", "duration", "work_order", "wo",
]
MEP_KEYWORDS = [
    "electrical", "plumbing", "sanitary", "hvac", "fire",
    "mep", "services", "em_component", "lift",
]
GEOTECH_KEYWORDS = [
    "geotech", "geotechnical", "borehole", "soil", "subsoil",
    "foundation_recommendation",
]
DRAWING_KEYWORDS = [
    "drawing", "drg", "drwg", "dwg", "plan", "section", "detail",
    "tender_drawing",
]


def normalize_name(filename: str) -> str:
    """Normalize filename for keyword matching."""
    name = filename.lower().replace("-", "_").replace(" ", "_")
    name = re.sub(r"[^a-z0-9_.]", "_", name)
    return name


def classify_file(filepath: Path, rel_path: str) -> str:
    """Classify a file by document category."""
    ext = filepath.suffix.lower()
    name = normalize_name(filepath.name)
    parent_dir = normalize_name(filepath.parent.name)
    full_rel = normalize_name(rel_path)
    fsize = 0
    try:
        fsize = filepath.stat().st_size
    except OSError:
        pass

    # Non-document files
    if filepath.name == ".gitkeep":
        return "GITKEEP"
    if ext == ".md":
        # Check if it's a project README vs analytical markdown
        if filepath.name == "README.md":
            return "METADATA"
        return "SYNTH"  # AI-generated analytical markdown
    if ext == ".py":
        return "SCRIPT"
    if ext == ".ps1":
        return "SCRIPT"
    if ext == ".pyc":
        return "SCRIPT"
    if ext == ".pptx":
        return "OTHER"
    if ext == ".png":
        return "IMAGE"
    if ext == ".html":
        return "HTML_STATUTORY"

    # CSV classification
    if ext == ".csv":
        if "file_manifest" in name:
            return "METADATA"
        if "boq" in name or "item_rate" in name:
            return "CAT4_BOQ"
        if "audit" in name or "register" in name or "reconciliation" in name:
            return "AUDIT_DATA"
        if "formula" in name or "calculation" in name:
            return "AUDIT_DATA"
        if "transcription" in name or "schedule" in name:
            return "CONTROLLED_TRANSCRIPTION"
        return "STRUCTURED_DATA"

    # JSON classification
    if ext == ".json":
        if "file_manifest" in name:
            return "METADATA"
        if "project_metadata" in name or "selected_tower" in name:
            return "METADATA"
        return "STRUCTURED_DATA"

    # PDF classification — the most complex part
    if ext == ".pdf":
        # Check for stub/generated PDFs (< 10 KB)
        if fsize < STUB_PDF_MAX_SIZE:
            return "STUB_PDF"

        # Check parent directory for context
        combined = name + " " + parent_dir + " " + full_rel

        # Geotechnical (check first as it's specific)
        if any(kw in combined for kw in GEOTECH_KEYWORDS):
            return "CAT9_GEOTECH"

        # BOQ/Cost (check before tender since BOQs are often within tender volumes)
        if any(kw in combined for kw in BOQ_KEYWORDS):
            return "CAT4_BOQ"

        # Architectural drawings
        if any(kw in combined for kw in ARCH_KEYWORDS) and any(kw in combined for kw in DRAWING_KEYWORDS):
            return "CAT2_ARCH_DRAWING"
        if "04_architectural" in combined:
            return "CAT2_ARCH_DRAWING"

        # Structural drawings
        if any(kw in combined for kw in STRUCT_KEYWORDS) and any(kw in combined for kw in DRAWING_KEYWORDS):
            return "CAT3_STRUCT_DRAWING"
        if "05_structural" in combined and "dbr" not in combined:
            return "CAT3_STRUCT_DRAWING"

        # Technical specifications
        if any(kw in combined for kw in SPEC_KEYWORDS):
            return "CAT5_SPECS"

        # MEP
        if any(kw in combined for kw in MEP_KEYWORDS):
            return "CAT8_MEP"

        # Schedule / Duration / Work orders
        if any(kw in combined for kw in SCHEDULE_KEYWORDS):
            return "CAT7_SCHEDULE"

        # Cost data
        if any(kw in combined for kw in COST_KEYWORDS):
            return "CAT6_COST"

        # Structural (non-drawing: DBR, design basis)
        if any(kw in combined for kw in STRUCT_KEYWORDS):
            return "CAT3_STRUCT_DRAWING"

        # Architectural (non-drawing: brochure, plans)
        if any(kw in combined for kw in ARCH_KEYWORDS):
            return "CAT2_ARCH_DRAWING"

        # Tender/NIT (catch-all for official documents)
        if any(kw in combined for kw in TENDER_KEYWORDS):
            return "CAT1_TENDER"

        # If PDF is in 01_Tender directory
        if "01_tender" in combined:
            return "CAT1_TENDER"
        if "02_cost" in combined:
            return "CAT4_BOQ"
        if "03_technical" in combined:
            return "CAT5_SPECS"
        if "06_mep" in combined:
            return "CAT8_MEP"
        if "07_landscape" in combined:
            return "CAT2_ARCH_DRAWING"
        if "08_execution" in combined:
            return "CAT7_SCHEDULE"
        if "99_unverified" in combined:
            return "CAT_UNVERIFIED"
        if "00_core" in combined:
            return "CAT1_TENDER"

        # Plinth rate reference documents
        if "plinth" in combined and "rate" in combined:
            return "CAT6_COST"

        return "PDF_UNCLASSIFIED"

    return "OTHER"


def scan_project(project_dir: Path) -> list:
    """Scan all files in a project and classify them."""
    results = []
    for dirpath, dirnames, filenames in os.walk(project_dir):
        for f in filenames:
            if f in EXCLUDE_FILES:
                continue
            fp = Path(dirpath) / f
            rel = str(fp.relative_to(project_dir))
            try:
                fsize = fp.stat().st_size
            except OSError:
                fsize = 0

            category = classify_file(fp, rel)
            results.append({
                "project_folder": project_dir.name,
                "relative_path": rel,
                "filename": f,
                "extension": fp.suffix.lower(),
                "size_bytes": fsize,
                "size_mb": round(fsize / (1024 * 1024), 3),
                "document_category": category,
                "is_real_pdf": 1 if fp.suffix.lower() == ".pdf" and fsize >= MIN_REAL_PDF_SIZE else 0,
                "is_stub_pdf": 1 if fp.suffix.lower() == ".pdf" and fsize < STUB_PDF_MAX_SIZE else 0,
                "is_substantial_pdf": 1 if fp.suffix.lower() == ".pdf" and fsize >= MIN_SUBSTANTIAL_PDF_SIZE else 0,
            })
    return results


def generate_evidence_audit(all_files: list) -> list:
    """Generate per-project primary evidence audit from classified files."""
    # Group by project
    projects = {}
    for f in all_files:
        pf = f["project_folder"]
        if pf not in projects:
            projects[pf] = []
        projects[pf].append(f)

    audit_rows = []
    for project_name, files in sorted(projects.items()):
        pdfs = [f for f in files if f["extension"] == ".pdf"]
        real_pdfs = [f for f in pdfs if f["is_real_pdf"]]
        stub_pdfs = [f for f in pdfs if f["is_stub_pdf"]]
        substantial_pdfs = [f for f in pdfs if f["is_substantial_pdf"]]

        # Evidence checks
        has_real_tender = any(f["document_category"] == "CAT1_TENDER" and f["is_real_pdf"] for f in files)
        has_real_arch_drawing = any(f["document_category"] == "CAT2_ARCH_DRAWING" and f["is_real_pdf"] for f in files)
        has_real_struct_drawing = any(f["document_category"] == "CAT3_STRUCT_DRAWING" and f["is_real_pdf"] for f in files)
        has_real_boq = any(f["document_category"] in ("CAT4_BOQ",) and (f["is_real_pdf"] or f["extension"] == ".csv") for f in files)
        has_real_specs = any(f["document_category"] == "CAT5_SPECS" and f["is_real_pdf"] for f in files)
        has_cost_data = any(f["document_category"] == "CAT6_COST" and (f["is_real_pdf"] or f["extension"] == ".csv") for f in files)
        has_schedule_data = any(f["document_category"] == "CAT7_SCHEDULE" and (f["is_real_pdf"] or f["extension"] == ".csv") for f in files)
        has_geotech = any(f["document_category"] == "CAT9_GEOTECH" and f["is_real_pdf"] for f in files)
        has_boq_csv = any(f["document_category"] == "CAT4_BOQ" and f["extension"] == ".csv" for f in files)
        has_mep = any(f["document_category"] == "CAT8_MEP" and f["is_real_pdf"] for f in files)

        # Count real unique PDFs (by name, to avoid counting duplicates across directories)
        unique_real_pdf_names = set(f["filename"] for f in real_pdfs)
        unique_stub_pdf_names = set(f["filename"] for f in stub_pdfs)

        # Category counts
        cat_counts = {}
        for f in files:
            cat = f["document_category"]
            if cat not in cat_counts:
                cat_counts[cat] = 0
            cat_counts[cat] += 1

        # Compute evidence score (out of 9)
        evidence_checks = [
            has_real_tender, has_real_arch_drawing, has_real_struct_drawing,
            has_real_boq, has_real_specs, has_cost_data, has_schedule_data,
            has_geotech, has_mep,
        ]
        evidence_score = sum(1 for e in evidence_checks if e)

        # Determine document quality tier
        if evidence_score >= 7:
            doc_quality = "COMPREHENSIVE"
        elif evidence_score >= 5:
            doc_quality = "SUBSTANTIAL"
        elif evidence_score >= 3:
            doc_quality = "PARTIAL"
        elif evidence_score >= 1:
            doc_quality = "MINIMAL"
        else:
            doc_quality = "EMPTY"

        audit_rows.append({
            "project_folder": project_name,
            "total_files": len(files),
            "total_pdfs": len(pdfs),
            "unique_real_pdfs": len(unique_real_pdf_names),
            "unique_stub_pdfs": len(unique_stub_pdf_names),
            "substantial_pdfs_gt_5mb": len(set(f["filename"] for f in substantial_pdfs)),
            "has_real_tender_nit": has_real_tender,
            "has_real_arch_drawing": has_real_arch_drawing,
            "has_real_struct_drawing": has_real_struct_drawing,
            "has_real_boq": has_real_boq,
            "has_real_specs": has_real_specs,
            "has_cost_data": has_cost_data,
            "has_schedule_data": has_schedule_data,
            "has_geotech_report": has_geotech,
            "has_mep_docs": has_mep,
            "has_boq_csv": has_boq_csv,
            "evidence_score_of_9": evidence_score,
            "document_quality_tier": doc_quality,
            "synth_markdown_count": cat_counts.get("SYNTH", 0),
            "audit_data_count": cat_counts.get("AUDIT_DATA", 0) + cat_counts.get("CONTROLLED_TRANSCRIPTION", 0),
        })

    return audit_rows


def main():
    # Find all project directories
    project_dirs = []
    for entry in sorted(ROOT.iterdir()):
        if entry.is_dir() and entry.name not in EXCLUDE_DIRS:
            project_dirs.append(entry)

    # Phase 1: Classify every file
    all_files = []
    for pdir in project_dirs:
        files = scan_project(pdir)
        all_files.extend(files)

    # Write Phase 1 document type matrix
    p1_path = OUTPUT_DIR / "phase_1_document_type_matrix.csv"
    if all_files:
        fieldnames = list(all_files[0].keys())
        with open(p1_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_files)

    print(f"✅ Phase 1 document type matrix written to: {p1_path}")
    print(f"   Total files classified: {len(all_files)}")

    # Category distribution
    cat_dist = {}
    for f in all_files:
        cat = f["document_category"]
        if cat not in cat_dist:
            cat_dist[cat] = 0
        cat_dist[cat] += 1

    print("\n   Category distribution:")
    for cat, count in sorted(cat_dist.items(), key=lambda x: -x[1]):
        print(f"     {cat:<30} {count:>4}")

    # Phase 2: Primary evidence audit
    audit_rows = generate_evidence_audit(all_files)

    p2_path = OUTPUT_DIR / "phase_2_primary_evidence_audit.csv"
    if audit_rows:
        fieldnames = list(audit_rows[0].keys())
        with open(p2_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(audit_rows)

    print(f"\n✅ Phase 2 primary evidence audit written to: {p2_path}")
    print(f"   Projects audited: {len(audit_rows)}")

    # Evidence summary
    print("\n" + "=" * 140)
    print(f"{'Project':<50} {'Real PDFs':>9} {'Stub':>4} {'>5MB':>4} {'Score':>5} {'Tier':<15} {'Tender':>6} {'Arch':>5} {'Struct':>6} {'BOQ':>4} {'Spec':>4} {'Cost':>5} {'Sched':>5} {'Geo':>4} {'MEP':>4}")
    print("=" * 140)
    for r in audit_rows:
        yn = lambda v: "YES" if v else "  -"
        print(f"{r['project_folder']:<50} {r['unique_real_pdfs']:>9} {r['unique_stub_pdfs']:>4} "
              f"{r['substantial_pdfs_gt_5mb']:>4} {r['evidence_score_of_9']:>4}/9 {r['document_quality_tier']:<15} "
              f"{yn(r['has_real_tender_nit']):>6} {yn(r['has_real_arch_drawing']):>5} "
              f"{yn(r['has_real_struct_drawing']):>6} {yn(r['has_real_boq']):>4} "
              f"{yn(r['has_real_specs']):>4} {yn(r['has_cost_data']):>5} "
              f"{yn(r['has_schedule_data']):>5} {yn(r['has_geotech_report']):>4} "
              f"{yn(r['has_mep_docs']):>4}")


if __name__ == "__main__":
    main()

