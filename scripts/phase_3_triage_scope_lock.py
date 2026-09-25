#!/usr/bin/env python3
"""
Phase 3 — Triage Decision Register & Scope Lock Register
Uses Phase 2 evidence audit results to assign each project to a processing track
and define scope locks for Track A projects.
"""

import csv
from pathlib import Path

ROOT = Path("/home/shahnawaz/Documents/DataRequirement")
OUTPUT_DIR = ROOT / "13_Corpus_Audit"

# Load Phase 2 results
def load_evidence_audit() -> list:
    path = OUTPUT_DIR / "phase_2_primary_evidence_audit.csv"
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

# Load Phase 0 results for additional context
def load_folder_inventory() -> dict:
    path = OUTPUT_DIR / "phase_0_folder_inventory.csv"
    result = {}
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            result[row["folder_name"]] = row
    return result

# Load refinement report for scope suggestions
def load_refinement_report() -> dict:
    path = ROOT / "30_PROJECT_REFINEMENT_REPORT.csv"
    result = {}
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                result[row.get("Project", "").strip()] = row
    return result


def determine_track(audit_row: dict, inv_row: dict) -> tuple:
    """
    Determine the processing track for a project.
    
    Track A — Full Pipeline: ≥1 real arch drawing + ≥1 real struct drawing + ≥1 real BOQ + evidence score ≥ 4
    Track B — Document-First: Real tender/NIT exists but missing drawings or BOQ
    Track C — Benchmark Only: Reference/RERA/markdown-only projects
    Track D — Exclude: Rejected or empty-framework projects
    """
    score = int(audit_row["evidence_score_of_9"])
    has_arch = audit_row["has_real_arch_drawing"] == "True"
    has_struct = audit_row["has_real_struct_drawing"] == "True"
    has_boq = audit_row["has_real_boq"] == "True"
    has_tender = audit_row["has_real_tender_nit"] == "True"
    tier = audit_row["document_quality_tier"]
    folder = audit_row["project_folder"]
    catalog_class = inv_row.get("catalog_classification", "")

    # Special cases
    if "Reject" in catalog_class:
        return "D", "Formally rejected — no public tender documents found"

    # Already-completed pilot projects
    if folder == "OIL-RITES-Duliajan-BQ-Housing":
        return "A_COMPLETE", "Production pilot — complete through Phase 12"
    if folder == "NIT-Nalanda":
        return "A_IN_PROGRESS", "Second pilot — Phase 1 document audit complete, resume from Phase 4"

    # Empty / reference-only projects
    if tier == "EMPTY":
        if "Reference" in catalog_class:
            return "C", "Reference-only project with no primary engineering documents"
        return "D", "Empty framework — no downloadable documents on disk"

    # Track A: Full pipeline candidates
    # Need at minimum: drawings + BOQ evidence + reasonable score
    if has_arch and has_struct and has_boq and score >= 4:
        return "A", "Full pipeline candidate — arch + struct drawings + BOQ available"
    
    if has_arch and has_boq and score >= 4:
        return "A", "Full pipeline candidate — arch drawings + BOQ (struct may be embedded in tender)"

    if has_struct and has_boq and score >= 4:
        return "A", "Full pipeline candidate — struct drawings + BOQ (arch may be embedded in tender)"

    # Track A borderline: comprehensive evidence even if category detection missed some
    if score >= 5:
        return "A", f"Full pipeline candidate — high evidence score ({score}/9)"

    # Track B: Document-first (has tender but missing critical items)
    if has_tender and score >= 1:
        if not has_boq:
            return "B", "Has tender PDF but missing standalone BOQ — BOQ may be embedded in tender volume"
        if not has_arch and not has_struct:
            return "B", "Has tender + BOQ but no separate drawing PDFs — drawings may be in tender volume"
        return "B", f"Has tender but incomplete evidence ({score}/9) — needs deeper document analysis"

    # Track C: Benchmark only
    if "Reference" in catalog_class:
        return "C", "Reference-only benchmark — RERA filings or analytical summaries only"

    # Track B fallback for Silver with some content
    if score >= 1:
        return "B", f"Minimal evidence ({score}/9) — needs document acquisition or deeper extraction"

    return "D", "No usable primary documents identified"


# Known scope locks from existing data
KNOWN_SCOPE_LOCKS = {
    "OIL-RITES-Duliajan-BQ-Housing": {
        "entity_name": "Typical BQ Workmen Housing Tower",
        "storey_profile": "Stilt + 6",
        "plinth_area_sqm": "3419.38",
        "dwelling_units": "24",
        "footprint_m": "30.08 x 16.08",
        "scope_status": "LOCKED",
        "source": "project_metadata.json; selected_tower_inputs.json",
    },
    "NIT-Nalanda": {
        "entity_name": "Faculty Housing Apartment Type 1B Block",
        "storey_profile": "G+2",
        "plinth_area_sqm": "264.67 (ground floor BUA)",
        "dwelling_units": "TBD",
        "footprint_m": "TBD",
        "scope_status": "LOCKED",
        "source": "selected_scope_lock.md",
    },
}

# Scope suggestions from refinement report + survey data
SCOPE_SUGGESTIONS = {
    "BMC-Deonar-600-Tenements": {
        "entity_name": "Building 04 (Composite High-Rise Tower)",
        "storey_profile": "TBD from drawings",
        "plinth_area_sqm": "TBD",
        "dwelling_units": "TBD",
        "footprint_m": "TBD",
        "scope_status": "SUGGESTED",
        "source": "30_PROJECT_REFINEMENT_REPORT.csv",
    },
    "IIT-Hyderabad-Faculty-Housing": {
        "entity_name": "Faculty Housing Tower (G+12)",
        "storey_profile": "G+12 (Precast)",
        "plinth_area_sqm": "TBD",
        "dwelling_units": "TBD",
        "footprint_m": "TBD",
        "scope_status": "SUGGESTED",
        "source": "30_PROJECT_REFINEMENT_REPORT.csv",
    },
    "SBI-Enclave-Hyderabad": {
        "entity_name": "Residential Tower Block (Officers' Quarters)",
        "storey_profile": "B+G+7",
        "plinth_area_sqm": "TBD",
        "dwelling_units": "134",
        "footprint_m": "TBD",
        "scope_status": "SUGGESTED",
        "source": "30_PROJECT_REFINEMENT_REPORT.csv",
    },
    "EPI-Dhenkanal-ICDS-Staff-Quarters": {
        "entity_name": "E-Type Staff Quarters Building",
        "storey_profile": "Stilt+4 (estimated)",
        "plinth_area_sqm": "TBD",
        "dwelling_units": "TBD",
        "footprint_m": "TBD",
        "scope_status": "SUGGESTED",
        "source": "30_PROJECT_REFINEMENT_REPORT.csv",
    },
    "SBI-GIFT-City-Twin-Towers": {
        "entity_name": "Tower A (Block 41A Luxury High-Rise)",
        "storey_profile": "3B+G+25",
        "plinth_area_sqm": "TBD",
        "dwelling_units": "TBD",
        "footprint_m": "TBD",
        "scope_status": "SUGGESTED",
        "source": "30_PROJECT_REFINEMENT_REPORT.csv",
    },
    "TCIL-NVS-JNV-Azamgarh-Quarters": {
        "entity_name": "Type-II Staff Quarters Block",
        "storey_profile": "G+1",
        "plinth_area_sqm": "TBD",
        "dwelling_units": "8",
        "footprint_m": "TBD",
        "scope_status": "SUGGESTED",
        "source": "30_PROJECT_REFINEMENT_REPORT.csv",
    },
    "SBI-DN-Nagar-Andheri-122-Flats": {
        "entity_name": "Tower 1 (Executive Quarters High-Rise)",
        "storey_profile": "2B+Stilt+17",
        "plinth_area_sqm": "TBD",
        "dwelling_units": "122",
        "footprint_m": "TBD",
        "scope_status": "SUGGESTED",
        "source": "30_PROJECT_REFINEMENT_REPORT.csv",
    },
    "DFCCIL-Sarmatanr-Larabad-Koderma-Quarters": {
        "entity_name": "Staff Quarters Block (one station)",
        "storey_profile": "TBD",
        "plinth_area_sqm": "TBD",
        "dwelling_units": "TBD",
        "footprint_m": "TBD",
        "scope_status": "SUGGESTED",
        "source": "30_PROJECT_REFINEMENT_REPORT.csv",
    },
    "MHDC-PMAY-Khairi-Kamptee-Nagpur": {
        "entity_name": "LIG Tenement Block (one typical block)",
        "storey_profile": "TBD",
        "plinth_area_sqm": "TBD",
        "dwelling_units": "TBD",
        "footprint_m": "TBD",
        "scope_status": "SUGGESTED",
        "source": "30_PROJECT_REFINEMENT_REPORT.csv",
    },
    "BHEL-Township-Jagdishpur": {
        "entity_name": "Type-A Residential Quarters Block",
        "storey_profile": "TBD",
        "plinth_area_sqm": "TBD",
        "dwelling_units": "TBD",
        "footprint_m": "TBD",
        "scope_status": "SUGGESTED",
        "source": "30_PROJECT_REFINEMENT_REPORT.csv",
    },
    "NPCIL-Anuvijay-240-Quarters": {
        "entity_name": "D-Type Residential Quarters Tower (Block 1)",
        "storey_profile": "G+10",
        "plinth_area_sqm": "TBD",
        "dwelling_units": "40",
        "footprint_m": "TBD",
        "scope_status": "SUGGESTED",
        "source": "30_PROJECT_REFINEMENT_REPORT.csv",
    },
    "WB-PWD-Burdwan-Type-I-II-Quarters": {
        "entity_name": "Type-II Quarters Block (2BHK)",
        "storey_profile": "G+2",
        "plinth_area_sqm": "TBD",
        "dwelling_units": "8",
        "footprint_m": "TBD",
        "scope_status": "SUGGESTED",
        "source": "30_PROJECT_REFINEMENT_REPORT.csv",
    },
}


def main():
    audit_data = load_evidence_audit()
    inventory = load_folder_inventory()
    refinement = load_refinement_report()

    # Generate triage decisions
    triage_rows = []
    for row in audit_data:
        folder = row["project_folder"]
        inv = inventory.get(folder, {})
        ref = refinement.get(folder, {})

        track, reason = determine_track(row, inv)

        triage_rows.append({
            "project_folder": folder,
            "project_id": inv.get("project_id", ""),
            "assigned_track": track,
            "triage_reason": reason,
            "evidence_score": row["evidence_score_of_9"],
            "document_quality_tier": row["document_quality_tier"],
            "catalog_classification": inv.get("catalog_classification", ""),
            "refinement_class": ref.get("Current class", inv.get("refinement_class", "")),
            "refinement_scope": ref.get("Selected building scope", inv.get("refinement_scope", "")),
            "refinement_next_action": ref.get("Next action", inv.get("refinement_next_action", "")),
        })

    # Write triage register
    triage_path = OUTPUT_DIR / "phase_3_triage_decision_register.csv"
    fieldnames = list(triage_rows[0].keys())
    with open(triage_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(triage_rows)

    # Generate scope lock register (Track A projects only)
    scope_rows = []
    track_a_projects = [r for r in triage_rows if r["assigned_track"].startswith("A")]

    for proj in track_a_projects:
        folder = proj["project_folder"]
        known = KNOWN_SCOPE_LOCKS.get(folder, {})
        suggested = SCOPE_SUGGESTIONS.get(folder, {})
        scope = known or suggested

        scope_rows.append({
            "project_folder": folder,
            "project_id": proj["project_id"],
            "assigned_track": proj["assigned_track"],
            "entity_name": scope.get("entity_name", "TBD — requires drawing review"),
            "storey_profile": scope.get("storey_profile", "TBD"),
            "plinth_area_sqm": scope.get("plinth_area_sqm", "TBD"),
            "dwelling_units": scope.get("dwelling_units", "TBD"),
            "footprint_m": scope.get("footprint_m", "TBD"),
            "scope_status": scope.get("scope_status", "NOT_LOCKED"),
            "source": scope.get("source", ""),
            "notes": "",
        })

    scope_path = OUTPUT_DIR / "phase_3_scope_lock_register.csv"
    if scope_rows:
        fieldnames = list(scope_rows[0].keys())
        with open(scope_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(scope_rows)

    # Print summary
    print(f"✅ Phase 3 triage register written to: {triage_path}")
    print(f"✅ Phase 3 scope lock register written to: {scope_path}")
    print()

    # Track distribution
    track_dist = {}
    for r in triage_rows:
        t = r["assigned_track"]
        if t not in track_dist:
            track_dist[t] = []
        track_dist[t].append(r["project_folder"])

    print("=" * 100)
    print("TRIAGE SUMMARY")
    print("=" * 100)
    for track in sorted(track_dist.keys()):
        projects = track_dist[track]
        track_labels = {
            "A_COMPLETE": "Track A — COMPLETE (production pilot done)",
            "A_IN_PROGRESS": "Track A — IN PROGRESS (audit started)",
            "A": "Track A — FULL PIPELINE (new)",
            "B": "Track B — DOCUMENT-FIRST (needs extraction/acquisition)",
            "C": "Track C — BENCHMARK ONLY (reference data)",
            "D": "Track D — EXCLUDE (rejected/empty)",
        }
        label = track_labels.get(track, f"Track {track}")
        print(f"\n{label} ({len(projects)} projects):")
        for p in projects:
            print(f"  • {p}")

    print(f"\n\nSCOPE LOCK REGISTER ({len(scope_rows)} Track A projects):")
    print("-" * 100)
    for s in scope_rows:
        status_icon = {"LOCKED": "🔒", "SUGGESTED": "📋", "NOT_LOCKED": "❓"}.get(s["scope_status"], "?")
        print(f"  {status_icon} {s['project_folder']}")
        print(f"     Entity: {s['entity_name']}")
        print(f"     Storeys: {s['storey_profile']}  |  Plinth: {s['plinth_area_sqm']} m²  |  Units: {s['dwelling_units']}")
        print(f"     Status: {s['scope_status']}  |  Source: {s['source']}")
        print()


if __name__ == "__main__":
    main()

