import os
import sys
import csv
import json

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"c:\Users\shahnawaz khan\OneDrive\Documents\DataRequirement\OIL-RITES-Duliajan-BQ-Housing"

def write_csv(rel_path, headers, rows):
    full_path = os.path.join(BASE_DIR, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"Updated {rel_path} ({os.path.getsize(full_path)} bytes)")

def write_text(rel_path, content):
    full_path = os.path.join(BASE_DIR, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Updated {rel_path} ({os.path.getsize(full_path)} bytes)")

# ==============================================================================
# STEP 1 & 2: CORRECT AWARD BASELINE & REMOVE UNSUPPORTED COST VALIDATION
# ==============================================================================

def step1_and_step2():
    # 1. Update project_metadata.json
    meta_path = os.path.join(BASE_DIR, "07_Final_Prototype_Dataset", "project_metadata.json")
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    meta["contract_award_value_inr"] = 1281400000
    meta["contract_award_value_text"] = "₹128.14 Crore (excluding GST)"
    meta["contract_award_contractor"] = "M/s Badri Rai & Company"
    meta["contract_award_record_date"] = "December 2025"
    meta["contract_scheduled_duration_months"] = 24
    meta["award_baseline_source"] = "status_of_Tender_dealt_Dec_2025_Badri_Rai_Award.pdf"
    meta["award_baseline_notes"] = "Awarded to M/s Badri Rai & Company for ₹128.14 Crore (excluding GST) with 24 months duration. Pro-rata 1/8th tower division (₹16.0175 Cr) is a rough project-level proportional benchmark only, NOT a validated tower cost. Earlier figures of ₹113.06 Cr and ₹157.25 Cr are superseded/excluded."
    meta["cost_validation"] = {
        "cost_accuracy": "NOT CALCULATED",
        "reason": "no official itemized priced BOQ available for the selected tower scope"
    }
    meta["quantity_validation"] = {
        "quantity_validation_coverage": "0%",
        "quantity_accuracy": "NOT CALCULATED",
        "reason": "no independent itemized BOQ quantities available for selected tower scope",
        "scope_consistency_check": "PASS"
    }
    meta["data_integrity"]["dataset_status"] = "DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION"
    meta["data_integrity"]["drawing_coverage_percentage"] = 83.9
    meta["data_integrity"]["external_boq_material_coverage_percentage"] = 0.0
    meta["data_integrity"]["macro_scope_concordance_percentage"] = 100.0

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("Updated 07_Final_Prototype_Dataset/project_metadata.json")

    # 2. Update 05_Validation/cost_validation_results.csv
    cost_headers = [
        "Cost Parameter", "Full Project Value", "Single Tower Benchmark Allocation", "Unit",
        "Validation Status", "Confidence", "Use for Model Validation", "Reason / Audit Finding"
    ]
    cost_rows = [
        [
            "Total Contract Award Baseline", "1281400000", "160175000", "INR",
            "NOT_VALIDATED", "LOW", "NO",
            "Contract awarded to M/s Badri Rai & Company for ₹128.14 Cr (excl GST) per Dec 2025 tender dealt record. Pro-rata 1/8th allocation (₹16.0175 Cr) is a rough project-level benchmark only, not validated tower cost."
        ],
        [
            "Estimated Civil & Structural Base Cost", "-", "81500000", "INR",
            "NOT_VALIDATED", "LOW", "NO",
            "Derived from CPWD DSR market rates applied to drawing takeoffs. No itemized official BOQ/rate/amount available for selected tower scope."
        ],
        [
            "Estimated MEP & Services Base Cost", "-", "24500000", "INR",
            "NOT_VALIDATED", "LOW", "NO",
            "Assumed 30% rule of thumb. No itemized official BOQ/rate/amount available for selected tower scope."
        ],
        [
            "Estimated Finishes & Architectural Base Cost", "-", "19000000", "INR",
            "NOT_VALIDATED", "LOW", "NO",
            "Assumed market finishing rates. No itemized official BOQ/rate/amount available for selected tower scope."
        ],
        [
            "Single Tower Estimated Direct Cost", "-", "125000000", "INR",
            "NOT_VALIDATED", "LOW", "NO",
            "Engineering takeoff synthesis (~₹36,556/sq.m plinth area). No official priced BOQ available for selected tower scope."
        ],
        [
            "Cost Accuracy Summary", "-", "-", "-",
            "NOT_CALCULATED", "LOW", "NO",
            "Cost accuracy: NOT CALCULATED. Reason: no official itemized priced BOQ available for the selected tower scope."
        ]
    ]
    write_csv("05_Validation/cost_validation_results.csv", cost_headers, cost_rows)

    # 3. Update 09_Calculation_Audit/scope_and_validation_statement.md
    scope_val_stmt = """# Scope & Validation Truth Disclosure Statement

## 1. Primary Contractual Finding: Absence of Official Itemized Construction BOQ
The tender for the **Construction of Workman Housing Complex (BQ Area) at OIL Duliajan, Assam** (`Tender Ref: RITES/NERPO/OIL/BQ-HOUSING/25`) was issued under **EPC Mode-II (Lump Sum Component Basis)**.

The official tender documents contain **NO itemized Bill of Quantities (BOQ)** providing:
- Concrete volume breakdowns (m³) for piles, pile caps, columns, beams, or slabs.
- Reinforcement steel weights (MT) by bar diameter or member mark.
- Formwork contact areas (m²).
- Masonry volumes (m³) or finishing surface areas (m²).
- Unit item rates (₹/m³, ₹/kg, ₹/m²) or element-wise contract amounts.

## 2. Prohibition of Fictitious Validation Claims
1. **Material Quantities**: No calculated physical quantity in this dataset is externally BOQ-validated. All material quantities represent **drawing-based engineering estimates** subject to calculation-audit and confidence classification.
2. **Cost Accuracy**: Cost accuracy is **NOT CALCULATED**. There is no itemized official priced BOQ for the selected tower scope.
3. **Quantity Accuracy**: Quantity accuracy is **NOT CALCULATED**. Quantity validation coverage against independent official material BOQ is **0%**.
4. **Scope Consistency Checks**: The master EPC schedule (`BoQ_3_Plumbing_Sanitary_pdf-2025-Aug-28-17-28-6.pdf`, Item 1.01) provides official ground truth solely for macro project scope parameters:
   - 8 Identical Residential Towers = 27,355.00 sq.m plinth area.
   - Allocated Single Tower Plinth Area = **3,419.38 sq.m** (`scope_consistency_check = PASS`).
   - Dwelling Units per Tower = **24 units** (Type-2BHK, 4 flats/floor × 6 floors) (`scope_consistency_check = PASS`).
   - Height Profile = **Stilt + 6 storeys** (`scope_consistency_check = PASS`).

## 3. Official Tender Award Baseline
- **Award Authority Record**: Documented in `08_Execution_Actuals/status_of_Tender_dealt_Dec_2025_Badri_Rai_Award.pdf` (RITES Tender Cell-NERPO, December 2025).
- **Successful Contractor**: **M/s Badri Rai & Company**.
- **Contract Award Value**: **₹128.14 Crore** (excluding GST).
- **Scheduled Completion Period**: **24 Months**.
- **Proportional Benchmark Note**: Dividing ₹128.14 Crore by 8 (₹16.0175 Crore per tower) represents only a rough project-level proportional benchmark and must **NOT** be treated as a validated single tower contract cost.
- **Superseded / Excluded Figures**: The preliminary figure of ₹113.06 Crore is superseded by the official award record, and the March/April 2025 media report figure of ₹157.25 Crore is completely excluded.
"""
    write_text("09_Calculation_Audit/scope_and_validation_statement.md", scope_val_stmt)

    # 4. Update 05_Validation/validation_findings.md
    val_findings = """# Validation Findings & Engineering Audit Report

## 1. Truth Disclosure: Absence of Official Material BOQ Ground Truth
This project (`RITES/NERPO/OIL/BQ-HOUSING/25`) was tendered as an **EPC Mode-II Lump-Sum Component Contract**. 
The official tender documents contain **no itemized construction bill of quantities** for materials such as concrete volume, reinforcement steel weight, formwork surface area, or masonry quantity for a single tower.

Consequently:
- **Quantity validation coverage: 0%**
- **Quantity accuracy: NOT CALCULATED**
- **Cost accuracy: NOT CALCULATED**
- Reason: No independent itemized BOQ quantities or priced items available for the selected tower scope.
- All reported material quantities represent a **drawing-based engineering estimate** requiring reconciliation.

## 2. Macro Scope Consistency Checks

| Scope Parameter | Model Calculated | Official Tender Allocation | Consistency Status | Traceability Source |
| :--- | :--- | :--- | :--- | :--- |
| **Single Tower Plinth Area** | 3,419.38 sq.m | 3,419.38 sq.m | **PASS** | BoQ_3 Item 1.01 (27,355 sq.m ÷ 8) |
| **Dwelling Units per Tower** | 24 units | 24 units | **PASS** | DBR Section 1 & Architectural Plans |
| **Storey Count** | Stilt + 6 | Stilt + 6 | **PASS** | Tender Drawing Elevations AR/TD/010-013 |
| **Foundation Pile Count** | 207 piles | 207 piles | **PASS** | Direct count on Structural Sheet 100 |

## 3. Structural Benchmarking (Seismic Zone V)
Because independent BOQ material quantities do not exist, the drawing-based estimates were evaluated against standard Indian engineering benchmarks for mid-rise residential buildings in Seismic Zone V (\(Z = 0.36\)):

| Engineering Indicator | Model Result | Zone V Standard Benchmark | Benchmark Status | Remarks |
| :--- | :--- | :--- | :--- | :--- |
| **Superstructure Concrete Intensity** | 0.372 m³/sq.m | 0.35 – 0.40 m³/sq.m | REASONABLE_RANGE | Reflects mid-rise frame with ductile shear walls |
| **Overall Concrete Intensity (RCC)** | 0.766 m³/sq.m | 0.70 – 0.85 m³/sq.m | REASONABLE_RANGE | Driven by 207 deep bored piles (18m assumed depth) |
| **Superstructure Steel Intensity** | 135.41 kg/m³ | 125 – 145 kg/m³ | REASONABLE_RANGE | Captures IS 13920 ductile boundary elements |
| **Overall Steel Intensity** | 87.98 kg/sq.m | 80 – 95 kg/sq.m | REASONABLE_RANGE | Zone V seismic detailing and deep piling steel |
| **Masonry Intensity** | 0.182 m³/sq.m | 0.16 – 0.20 m³/sq.m | REASONABLE_RANGE | External 230mm + internal 115mm brick partitions |
| **Plaster Surface Ratio** | 4.34 m²/sq.m | 3.80 – 4.50 m²/sq.m | REASONABLE_RANGE | Internal wall/ceiling plus external double-coat plaster |

*Note: Benchmark compliance indicates engineering plausibility; it does not constitute official BOQ validation.*

## 4. Commercial Award Baseline
- **Official Award Record**: Awarded to **M/s Badri Rai & Company** as documented in the December 2025 RITES tender-dealt record (`status_of_Tender_dealt_Dec_2025_Badri_Rai_Award.pdf`).
- **Contract Award Value**: **₹128.14 Crore** (excluding GST).
- **Scheduled Completion**: **24 Months**.
- **Pro-Rata Benchmark**: ₹128.14 Crore ÷ 8 = ₹16.0175 Crore per tower (proportional project-level benchmark only; not a validated tower cost).
- **Direct Construction Cost Estimate**: ₹12.50 Crore (Takeoff quantities × estimated market rates, not contract-validated).
- **Cost Accuracy Verdict**: **NOT CALCULATED** (no official itemized priced BOQ available).
"""
    write_text("05_Validation/validation_findings.md", val_findings)

# ==============================================================================
# STEP 3 & 4: RECLASSIFY QUANTITY CONFIDENCE & RECONCILE CONTRADICTIONS
# ==============================================================================

def step3_and_step4():
    # 1. Update 09_Calculation_Audit/beam_length_schedule.csv
    beam_headers = [
        "Level / Floor", "Beam Mark", "Section b x D (mm)", "Number of Spans", "Reconciled Length per Level (m)",
        "Cross-Section Area (sq.m)", "Net Volume (m3)", "Concrete Grade", "Drawing Reference",
        "Confidence Status", "Contradiction & Audit Reconciliation Notes"
    ]
    beam_rows = [
        [
            "Plinth Level", "PB1 to PB34", "230x450 / 230x600 / 300x600", 108, "403.50", "0.1180", "47.61", "M30",
            "STR/TD/HOUSING(G+6)/105", "ESTIMATED",
            "Reconciled to 403.5m based on grid run lines (6 longitudinal of 30.08m + 14 transverse of 16.08m). Legacy 420m was an unverified rounded estimate. Section is weighted average; downgraded from HIGH to ESTIMATED."
        ],
        [
            "Floors 1 to 6", "B1 to B34 (Typical)", "230x450 / 230x600 / 300x600", 648, "2421.00 (403.5m x 6)", "0.1197", "289.80", "M30",
            "STR/TD/HOUSING(G+6)/107", "ESTIMATED",
            "Reconciled to 403.5m per floor x 6 floors. Cross section 0.1197 m2 is an assumed average; uses 6-floor repetition. Downgraded from HIGH to ESTIMATED."
        ],
        [
            "Terrace Level", "TB1 to TB34", "230x450 / 230x600", 108, "403.50", "0.1197", "48.30", "M30",
            "STR/TD/HOUSING(G+6)/108", "ESTIMATED",
            "Reconciled to 403.5m grid run. Section is assumed average. Downgraded from HIGH to ESTIMATED."
        ]
    ]
    write_csv("09_Calculation_Audit/beam_length_schedule.csv", beam_headers, beam_rows)

    # 2. Update 09_Calculation_Audit/slab_area_schedule.csv
    slab_headers = [
        "Level / Floor", "Slab Type / Mark", "Scheduled Thickness (mm)", "Assumed Weighted Thickness (mm)",
        "Gross Footprint Area (sq.m)", "Measured Core Deductions (sq.m)", "Reconciled Net Slab Area (sq.m)",
        "Concrete Volume (m3)", "Concrete Grade", "Drawing Reference", "Confidence Status", "Contradiction & Reconciliation Notes"
    ]
    slab_rows = [
        [
            "Stilt Floor", "Grade Slab GS1/GS2", "125", "125", "483.60", "45.60", "438.00",
            "54.75", "M30", "STR/TD/HOUSING(G+6)/105", "ASSUMPTION_REQUIRED",
            "Reconciled: Gross footprint = 483.60 m2 (30.08m x 16.08m); Net slab area = 438.00 m2 after deducting columns/walls/ducts. At 125mm uniform thickness, volume = 54.75 m3. Prior claim of 60.45 m3 required an unmeasured 5.70 m3 edge thickening allowance."
        ],
        [
            "Floors 1 to 6", "Suspended Slab S1/S2", "125 (S1) / 150 (S2)", "130 (weighted avg)", "2901.60 (483.60 x 6)", "351.84 (58.64 x 6)", "2549.76 (424.96 x 6)",
            "331.47", "M30", "STR/TD/HOUSING(G+6)/107", "ESTIMATED",
            "Reconciled: Net interior slab is 424.96 m2 per floor (deducting 58.64 m2 core shafts). 428 m2 was a rounded estimate. Thickness 130mm is an assumed weighted average (S1 125mm, S2 sunken 150mm), not single schedule. Downgraded to ESTIMATED."
        ],
        [
            "Terrace Floor", "Terrace Slab S1", "125", "130 (with screed/slope)", "483.60", "58.64", "424.96",
            "55.24", "M30", "STR/TD/HOUSING(G+6)/108", "ESTIMATED",
            "Reconciled to 424.96 m2 net slab. Assumed 130mm average thickness. Downgraded to ESTIMATED."
        ],
        [
            "Balconies & Chajjas", "Cantilever Projections", "100-125", "110", "182.00", "0.00", "182.00",
            "20.02", "M30", "STR/TD/HOUSING(G+6)/107", "ESTIMATED",
            "Exterior shading projections across 7 levels. Derived without individual piece schedule. Downgraded to ESTIMATED."
        ]
    ]
    write_csv("09_Calculation_Audit/slab_area_schedule.csv", slab_headers, slab_rows)

    # 3. Update 09_Calculation_Audit/pile_cap_schedule_audit.csv (STEP 5)
    cap_headers = [
        "Cap Type", "Cap Configuration", "Pile Count per Cap", "Count in Plan Layout", "Reported Summary Count",
        "Length (m)", "Width (m)", "Assumed Depth (m)", "Concrete Grade", "Volume per Cap (m3)",
        "Calculated Total Volume (m3)", "Drawing Reference", "Confidence Status", "Contradiction & Reconciliation Analysis"
    ]
    cap_rows = [
        [
            "PC-1", "1-Pile Cap / Pedestal", 1, 8, "Unreconciled", "1.20", "1.20", "1.00", "M30", "1.44", "11.52",
            "STR/TD/HOUSING(G+6)/101", "ASSUMPTION_REQUIRED",
            "Layout count = 8 caps (8 piles). Thickness 1.0m is engineering assumption (ASM-002); no depth scheduled on drawing."
        ],
        [
            "PC-2", "2-Pile Cap", 2, 24, "Unreconciled", "2.40", "1.20", "1.00", "M30", "2.88", "69.12",
            "STR/TD/HOUSING(G+6)/101", "ASSUMPTION_REQUIRED",
            "Layout count = 24 caps (48 piles). Thickness 1.0m is engineering assumption (ASM-002)."
        ],
        [
            "PC-3", "3-Pile Cap (Triangular)", 3, 12, "Unreconciled", "2.70", "2.10", "1.00", "M30", "4.00", "48.00",
            "STR/TD/HOUSING(G+6)/101", "ASSUMPTION_REQUIRED",
            "Layout count = 12 caps (36 piles). Thickness 1.0m is engineering assumption (ASM-002)."
        ],
        [
            "PC-4", "4-Pile Cap", 4, 6, "Unreconciled", "2.70", "2.70", "1.00", "M30", "7.29", "43.74",
            "STR/TD/HOUSING(G+6)/101", "ASSUMPTION_REQUIRED",
            "Layout count = 6 caps (24 piles). Thickness 1.0m is engineering assumption (ASM-002)."
        ],
        [
            "PC-W", "Continuous Strip Caps under Shear Walls", "Variable (91 piles unaccounted)", 4, "Unreconciled", "6.00", "1.50", "1.00", "M30", "9.00", "36.00",
            "STR/TD/HOUSING(G+6)/101", "ASSUMPTION_REQUIRED",
            "Discrete caps 1-4 account for only 116 piles (8+48+36+24). Remaining 91 piles out of 207 total piles fall under strip caps, but 4 strip caps of 6m cannot physically host 91 piles (22.75 piles/cap)."
        ],
        [
            "TOTAL_CAPS_AUDIT", "Full Foundation Cap System", 207, 54, 84, "Various", "Various", "1.00", "M30", "Various", "185.00 to 208.38",
            "STR/TD/HOUSING(G+6)/101", "UNRESOLVED_CONTRADICTION",
            "CRITICAL CONTRADICTION: Plan layout shows 54 cap entities totaling 208.38 m3, whereas preliminary takeoff summary claimed 84 caps totaling 185.00 m3. Pile allocation leaves 91 piles unresolved. Marked UNRESOLVED_CONTRADICTION / ASSUMPTION_REQUIRED."
        ]
    ]
    write_csv("09_Calculation_Audit/pile_cap_schedule_audit.csv", cap_headers, cap_rows)

    # 4. Update 09_Calculation_Audit/pile_schedule_audit.csv
    pile_headers = [
        "Element ID", "Element Type", "Total Pile Count", "Diameter (mm)", "Cross-Section Area (sq.m)",
        "Assumed Length (m)", "Total Bore Length (m)", "Concrete Grade", "Estimated Concrete Volume (m3)",
        "Drawing Reference", "DBR Reference", "Confidence Status", "Contradiction & Reconciliation Notes"
    ]
    pile_rows = [
        [
            "PILE-001", "Bored Cast-in-situ RCC Pile", 207, 600, "0.28274",
            "18.00", "3726.00", "M30", "1053.49",
            "STR/TD/HOUSING(G+6)/100", "DBR p.35 & GT Report Section 4", "ESTIMATED",
            "Total 207 piles directly counted on foundation layout plan (Sheet 100). Pile termination depth is NOT scheduled on drawing; derived from DBR recommended range of 15-20m (adopted 18m average, ASM-001). Rebar cage not scheduled. Classified as ESTIMATED."
        ]
    ]
    write_csv("09_Calculation_Audit/pile_schedule_audit.csv", pile_headers, pile_rows)

    # 5. Update 09_Calculation_Audit/formula_ledger.csv
    ledger_headers = [
        "Element ID", "Structural / Architectural Element", "Sub-Element", "Formula / Math Expression",
        "Quantity Value", "Unit", "Drawing Reference", "Sheet ID", "Confidence Classification", "Audit Reconciliation Status"
    ]
    ledger_rows = [
        ["CONC-001", "Substructure", "PCC Lean Concrete (1:5:10)", "240.0 sqm cap footprint x 0.075m thickness", "18.00", "m3", "STR/TD/HOUSING(G+6)/101", "Sheet 101", "ESTIMATED", "Assumed 75mm thickness (ASM-003)"],
        ["CONC-002", "Substructure", "Bored RCC Piles (207 nos)", "207 piles * (pi/4 * 0.6^2) * 18.00m length", "1053.49", "m3", "STR/TD/HOUSING(G+6)/100", "Sheet 100", "ESTIMATED", "207 piles verified on Sheet 100; 18m depth assumed from DBR (ASM-001)"],
        ["CONC-003", "Substructure", "RCC Pile Caps", "UNRESOLVED: 54 caps layout (208.38 m3) vs 84 caps summary (185.00 m3)", "185.00", "m3", "STR/TD/HOUSING(G+6)/101", "Sheet 101", "ASSUMPTION_REQUIRED", "Unresolved cap count discrepancy; thickness 1.0m assumed (ASM-002)"],
        ["CONC-004", "Substructure", "Plinth Beams (PB1 to PB34)", "403.5m reconciled length * 0.118 m2 weighted section", "47.61", "m3", "STR/TD/HOUSING(G+6)/105", "Sheet 105", "ESTIMATED", "Reconciled to 403.5m grid run; weighted section assumed"],
        ["CONC-005", "Substructure", "Stilt Grade Slab (GS1/GS2)", "438.0 sqm net area * 0.125m (+5.7m3 unmeasured thickening)", "60.45", "m3", "STR/TD/HOUSING(G+6)/105", "Sheet 105", "ASSUMPTION_REQUIRED", "Uniform slab = 54.75 m3; 60.45 m3 requires assumed 5.7 m3 edge thickening"],
        ["CONC-006", "Superstructure", "Columns C1 (1200x350)", "28 members (4/flr x 7) * 1.20 * 0.35 * 3.00m clear ht", "35.28", "m3", "STR/TD/HOUSING(G+6)/104", "Sheet 104", "MEDIUM", "Cross section directly scheduled; 3.0m floor height assumed repeated"],
        ["CONC-007", "Superstructure", "Columns C2 (1200x300)", "56 members (8/flr x 7) * 1.20 * 0.30 * 3.00m clear ht", "60.48", "m3", "STR/TD/HOUSING(G+6)/104", "Sheet 104", "MEDIUM", "Cross section directly scheduled; 3.0m floor height assumed repeated"],
        ["CONC-008", "Superstructure", "Columns C3 (1200x300)", "28 members (4/flr x 7) * 1.20 * 0.30 * 3.00m clear ht", "30.24", "m3", "STR/TD/HOUSING(G+6)/104", "Sheet 104", "MEDIUM", "Cross section directly scheduled; 3.0m floor height assumed repeated"],
        ["CONC-009", "Superstructure", "Shear Walls SW1 (1260x230)", "84 members (12/flr x 7) * 1.26 * 0.23 * 3.00m clear ht", "73.03", "m3", "STR/TD/HOUSING(G+6)/104", "Sheet 104", "MEDIUM", "Cross section directly scheduled; 3.0m floor height assumed repeated"],
        ["CONC-010", "Superstructure", "Shear Walls SW2 (1500x230)", "28 members (4/flr x 7) * 1.50 * 0.23 * 3.00m clear ht", "28.98", "m3", "STR/TD/HOUSING(G+6)/104", "Sheet 104", "MEDIUM", "Cross section directly scheduled; 3.0m floor height assumed repeated"],
        ["CONC-011", "Superstructure", "Shear Walls SW3 (1380x230)", "28 members (4/flr x 7) * 1.38 * 0.23 * 3.00m clear ht", "26.66", "m3", "STR/TD/HOUSING(G+6)/104", "Sheet 104", "MEDIUM", "Cross section directly scheduled; 3.0m floor height assumed repeated"],
        ["CONC-012", "Superstructure", "Shear Walls SW4 (2925x230)", "28 members (4/flr x 7) * 2.925 * 0.23 * 3.00m clear ht", "56.51", "m3", "STR/TD/HOUSING(G+6)/104", "Sheet 104", "MEDIUM", "Cross section directly scheduled; 3.0m floor height assumed repeated"],
        ["CONC-013", "Superstructure", "Shear Walls SW5 (5030x230)", "28 members (4/flr x 7) * 5.030 * 0.23 * 3.00m clear ht", "97.18", "m3", "STR/TD/HOUSING(G+6)/104", "Sheet 104", "MEDIUM", "Cross section directly scheduled; 3.0m floor height assumed repeated"],
        ["CONC-014", "Superstructure", "Core Shear Walls SW6-SW10", "35 members (5/flr x 7) * 13.89m run * 0.23 * 3.00m ht", "67.09", "m3", "STR/TD/HOUSING(G+6)/104", "Sheet 104", "MEDIUM", "Run length directly scheduled; 3.0m floor height assumed repeated"],
        ["CONC-015", "Superstructure", "Mumty Columns & Pedestals", "8 columns * 0.30 * 0.30 * 2.70m + pedestals", "6.74", "m3", "STR/TD/HOUSING(G+6)/109", "Sheet 109", "MEDIUM", "Dimensions scheduled; minor pedestal volume estimated"],
        ["CONC-016", "Superstructure", "Floor Beams (Floors 1 to 6)", "6 floors * 403.5m reconciled length * 0.1197 m2 section", "289.80", "m3", "STR/TD/HOUSING(G+6)/107", "Sheet 107", "ESTIMATED", "Reconciled to 403.5m grid run; weighted section assumed"],
        ["CONC-017", "Superstructure", "Terrace Beams TB1-TB34", "1 floor * 403.5m reconciled length * 0.1197 m2 section", "48.30", "m3", "STR/TD/HOUSING(G+6)/108", "Sheet 108", "ESTIMATED", "Reconciled to 403.5m grid run; weighted section assumed"],
        ["CONC-018", "Superstructure", "Suspended Floor Slabs (F1-F6)", "6 floors * 424.96 sqm net area * 0.130m weighted thickness", "331.47", "m3", "STR/TD/HOUSING(G+6)/107", "Sheet 107", "ESTIMATED", "Reconciled to 424.96 m2 net slab; 130mm weighted thickness assumed"],
        ["CONC-019", "Superstructure", "Terrace Slab & Mumty Roof", "424.96 sqm net area * 0.130m weighted thickness", "55.24", "m3", "STR/TD/HOUSING(G+6)/108", "Sheet 108", "ESTIMATED", "Reconciled to 424.96 m2 net slab; 130mm thickness assumed"],
        ["CONC-020", "Superstructure", "Balconies & Chajjas", "182.0 sqm projected area * 0.110m avg thickness", "20.02", "m3", "STR/TD/HOUSING(G+6)/107", "Sheet 107", "ESTIMATED", "Derived without individual piece schedule"],
        ["CONC-021", "Superstructure", "Doglegged Staircase Cores (2)", "28 flights * 0.95 m3 per flight (waist + steps + landings)", "26.60", "m3", "STR/TD/HOUSING(G+6)/110", "Sheet 110", "MEDIUM", "Flight geometry scheduled; repeated flight multiplier used"],
        ["CONC-022", "Superstructure", "Mumty Walls & Parapet", "35.20m perimeter * 0.15m * 1.90m height", "10.03", "m3", "STR/TD/HOUSING(G+6)/109", "Sheet 109", "MEDIUM", "Mumty enclosure dimensions directly scheduled"],
        ["CONC-023", "Superstructure", "Overhead Water Tank (OHT)", "Twin compartment tank geometry (walls 150mm base 200mm)", "16.50", "m3", "STR/TD/HOUSING(G+6)/109", "Sheet 109", "ASSUMPTION_REQUIRED", "No structural schedule for tank walls/base; estimated (ASM-010)"]
    ]
    write_csv("09_Calculation_Audit/formula_ledger.csv", ledger_headers, ledger_rows)

# ==============================================================================
# STEP 6 & 7: REBAR / BBS CONTROL & QUANTITY VALIDATION RESULTS
# ==============================================================================

def step6_and_step7():
    # 1. Update 03_Quantity_Takeoff/reinforcement_takeoff.csv
    rebar_headers = [
        "Element ID", "Structural Element", "T8 (kg)", "T10 (kg)", "T12 (kg)", "T16 (kg)",
        "T20 (kg)", "T25 (kg)", "T32 (kg)", "Total Steel (kg)", "Total Steel (MT)",
        "Steel Intensity (kg/m3)", "Drawing Reference", "Confidence Classification", "Audit Reconciliation Notes"
    ]
    rebar_rows = [
        ["REBAR-001", "Bored RCC Piles (207 nos)", 0, 23628, 0, 45611, 30000, 0, 0, 99239, 99.24, 94.20, "STR/TD/HOUSING(G+6)/100", "ESTIMATED", "Pile depth (18m) and 8-T20 cage are assumed (ASM-001/002); no BBS on drawing sheet."],
        ["REBAR-002", "Pile Caps (84 caps summary vs 54 layout)", 0, 0, 3580, 5567, 11203, 0, 0, 20350, 20.35, 110.00, "STR/TD/HOUSING(G+6)/101", "ASSUMPTION_REQUIRED", "Unresolved cap count contradiction (54 vs 84); assumed 110 kg/m3 intensity without BBS."],
        ["REBAR-003", "Plinth Beams (PB1 to PB34)", 1945, 0, 0, 0, 4474, 8, 0, 6427, 6.43, 135.00, "STR/TD/HOUSING(G+6)/105", "ESTIMATED", "Assumed 135 kg/m3 intensity across 403.5m grid length; no bar cut schedule."],
        ["REBAR-004", "Stilt Grade Slab (GS1-GS2)", 2666, 0, 0, 0, 0, 0, 0, 2666, 2.67, 44.10, "STR/TD/HOUSING(G+6)/105", "ESTIMATED", "T8@150 mesh scheduled on Sheet 105; lap and edge allowances estimated."],
        ["REBAR-005", "Columns C1 (14-T32 + 8-T25)", 0, 1764, 0, 0, 0, 6774, 17142, 25680, 25.68, 727.89, "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Bar count (14-T32+8-T25) directly scheduled on Sheet 104; 3.0m floor ht and 50d lap rule used across 7 levels."],
        ["REBAR-006", "Columns C2 (22-T25)", 0, 3024, 0, 0, 0, 15422, 0, 18446, 18.45, 304.99, "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Bar count (22-T25) directly scheduled on Sheet 104; 3.0m floor ht and 50d lap rule used across 7 levels."],
        ["REBAR-007", "Columns C3 (22-T20)", 0, 1512, 0, 0, 6768, 0, 0, 8280, 8.28, 273.81, "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Bar count (22-T20) directly scheduled on Sheet 104; 3.0m floor ht and 50d lap rule used across 7 levels."],
        ["REBAR-008", "Shear Walls SW1 to SW5", 9290, 0, 9051, 8041, 0, 0, 0, 26382, 26.38, 93.42, "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Boundary elements and web mesh scheduled on Sheet 104; vertical cut lengths assume 3.0m clear ht."],
        ["REBAR-009", "Core Walls SW6 to SW10", 1721, 0, 2020, 0, 0, 0, 0, 3741, 3.74, 55.76, "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Duct/lift core reinforcement scheduled on Sheet 104; 3.0m floor ht assumed."],
        ["REBAR-010", "Mumty Columns & Pedestals", 0, 115, 0, 467, 0, 0, 0, 582, 0.58, 86.35, "STR/TD/HOUSING(G+6)/109", "MEDIUM", "Columns detailed on Sheet 109."],
        ["REBAR-011", "Floor Beams (Floors 1-6 + Terrace)", 13886, 0, 5639, 0, 15575, 12234, 0, 47334, 47.33, 140.00, "STR/TD/HOUSING(G+6)/107-108", "ESTIMATED", "Assumed 140 kg/m3 intensity across 7 levels x 403.5m length; no sheet-wise BBS."],
        ["REBAR-012", "Suspended Slabs & Chajjas (7 levels)", 25680, 11005, 0, 0, 0, 0, 0, 36685, 36.69, 89.17, "STR/TD/HOUSING(G+6)/107", "ESTIMATED", "Slab schedules S1/S2 T8@125/150 c/c on Sheet 107; assumed 89.17 kg/m3 intensity."],
        ["REBAR-013", "Doglegged Staircases (2 cores)", 0, 1244, 1671, 0, 0, 0, 0, 2915, 2.92, 109.59, "STR/TD/HOUSING(G+6)/110", "MEDIUM", "Flight reinforcement detailed on Sheet 110; 28 flights repeated."],
        ["REBAR-014", "Mumty & Tank Slabs & OHT Walls", 172, 740, 1066, 0, 0, 0, 0, 1978, 1.98, 119.88, "STR/TD/HOUSING(G+6)/109", "ASSUMPTION_REQUIRED", "OHT reinforcement estimated (ASM-010); no structural drawing schedule."]
    ]
    write_csv("03_Quantity_Takeoff/reinforcement_takeoff.csv", rebar_headers, rebar_rows)

    # 2. Update 09_Calculation_Audit/rebar_weight_summary.csv
    rebar_summary_headers = [
        "Diameter (mm)", "Unit Weight (kg/m)", "Total Length (m)", "Total Weight (kg)",
        "Weight (MT)", "Percentage of Total (%)", "Confidence Classification", "Primary Structural Elements", "BBS Audit Finding"
    ]
    rebar_summary_rows = [
        [8, 0.395, 107316.0, 42390.0, 42.39, 14.09, "ESTIMATED", "Slab mesh (S1/S2/GS1), beam shear stirrups, shear wall horizontal ties", "Mesh spacing scheduled; exact cut lengths and hook deductions require shop BBS"],
        [10, 0.617, 32852.0, 20270.0, 20.27, 6.74, "MEDIUM_AND_ESTIMATED", "Column ties (C1-C3), staircase distribution, pile helical spirals (estimated)", "Ties scheduled; pile spirals estimated (ASM-001/002)"],
        [12, 0.888, 33671.0, 29900.0, 29.90, 9.94, "MEDIUM", "Shear wall web verticals, stair waist slab main, beam side-face", "Directly scheduled on Sheet 104 and Sheet 110; repeated across 7 levels"],
        [16, 1.578, 62389.0, 98450.0, 98.45, 32.72, "ESTIMATED_AND_MEDIUM", "Bored pile cage verticals (estimated), wall boundary elements, beam main bars", "Pile cage is estimated (ASM-001/002); wall boundaries scheduled"],
        [20, 2.466, 25628.0, 63200.0, 63.20, 21.01, "ESTIMATED_AND_MEDIUM", "Bored pile cage verticals (estimated), C3 column verticals, beam bottom bars", "C3 scheduled on Sheet 104; piles and beams estimated"],
        [25, 3.853, 7656.0, 29500.0, 29.50, 9.81, "MEDIUM", "C1 & C2 column verticals, beam top support extra bars", "Bar counts directly scheduled on Sheet 104"],
        [32, 6.313, 2715.0, 17143.0, 17.14, 5.70, "MEDIUM", "C1 column corner and outer face verticals (14-T32 per column)", "Bar count directly scheduled on Sheet 104; mechanical couplers/laps required"]
    ]
    write_csv("09_Calculation_Audit/rebar_weight_summary.csv", rebar_summary_headers, rebar_summary_rows)

    # 3. Update 05_Validation/quantity_validation_results.csv (STEP 7)
    qval_headers = [
        "Scope / Parameter Description", "Calculated Takeoff", "Official BOQ Ground Truth", "Unit",
        "Scope Consistency Check", "Validation Status", "Quantity Accuracy", "Reason / Audit Remarks"
    ]
    qval_rows = [
        ["Tower Plinth Area", "3419.38", "3419.38", "sq.m", "PASS", "SCOPE_CONSISTENCY_CHECK", "N/A", "Concordant with BoQ_3 Item 1.01 (27355 sqm / 8)."],
        ["Total Dwelling Units", "24", "24", "units", "PASS", "SCOPE_CONSISTENCY_CHECK", "N/A", "4 units/floor x 6 residential floors (192 units / 8)."],
        ["Number of Storeys", "Stilt + 6", "Stilt + 6", "storeys", "PASS", "SCOPE_CONSISTENCY_CHECK", "N/A", "Verified from architectural elevations and tender scope."],
        ["Total Number of Towers", "1 (out of 8)", "1 (out of 8)", "nos", "PASS", "SCOPE_CONSISTENCY_CHECK", "N/A", "Isolated single typical tower model."],
        ["Foundation Bored Piles Count", "207", "Not in BOQ", "piles", "PASS", "DRAWING_VERIFIED_COUNT", "N/A", "Direct count from structural sheet 100; pile length/depth not in BOQ."],
        ["Vertical Structural Members Count", "49", "Not in BOQ", "members", "PASS", "DRAWING_VERIFIED_COUNT", "N/A", "16 columns (C1-C3) + 33 shear walls (SW1-SW10) directly counted on Sheet 104."],
        ["Scheduled Door Openings Count", "216", "Not in BOQ", "nos", "PASS", "DRAWING_VERIFIED_COUNT", "N/A", "Scheduled on Sheet 005 (48 D1, 96 D2, 72 D3)."],
        ["Scheduled Window/Vent Openings", "168", "Not in BOQ", "nos", "PASS", "DRAWING_VERIFIED_COUNT", "N/A", "Scheduled on Sheet 005 (W1-W4, V1-V2)."],
        ["RCC Concrete Volume (M30)", "2617.55", "No BOQ Line Item", "m3", "N/A", "NOT_VALIDATED", "NOT_CALCULATED", "No independent itemized BOQ quantities available for selected tower scope."],
        ["PCC Lean Concrete (M10)", "18.00", "No BOQ Line Item", "m3", "N/A", "NOT_VALIDATED", "NOT_CALCULATED", "No independent itemized BOQ quantities available for selected tower scope."],
        ["Reinforcement Steel (Fe 500D)", "300.85", "No BOQ Line Item", "MT", "N/A", "NOT_VALIDATED", "NOT_CALCULATED", "No independent itemized BOQ quantities available for selected tower scope."],
        ["Brick Masonry Volume", "623.65", "No BOQ Line Item", "m3", "N/A", "NOT_VALIDATED", "NOT_CALCULATED", "No independent itemized BOQ quantities available for selected tower scope."],
        ["Cement Plaster Surface Area", "14850.00", "No BOQ Line Item", "sq.m", "N/A", "NOT_VALIDATED", "NOT_CALCULATED", "No independent itemized BOQ quantities available for selected tower scope."],
        ["Overall Material Validation Summary", "-", "-", "-", "N/A", "Quantity validation coverage: 0%", "NOT_CALCULATED", "Reason: no independent itemized BOQ quantities available for selected tower scope."]
    ]
    write_csv("05_Validation/quantity_validation_results.csv", qval_headers, qval_rows)

    # 4. Update 05_Validation/coverage_report.csv
    cov_headers = [
        "Scope Domain", "Drawing Coverage Ratio (%)", "Independent BOQ Material Coverage (%)",
        "Scope Consistency Check", "Audit Classification", "Domain Audit Findings"
    ]
    cov_rows = [
        ["Macro Scope & Geometry", "100.0%", "100.0% (Item 1.01)", "PASS", "SCOPE_CONSISTENCY_CHECK", "Plinth area (3419.38 sqm), unit count (24), and storey count (Stilt+6) concordant with tender scope."],
        ["Foundation (Piles & Caps)", "60.0%", "0.0%", "PARTIAL", "ASSUMPTION_REQUIRED", "207 piles counted, but depth (18m) and cap thickness (1.0m) are assumed; cap count contradictory (54 vs 84)."],
        ["Superstructure Frame (Columns & Walls)", "95.0%", "0.0%", "N/A", "MEDIUM_CONFIDENCE_DRAWING", "All 49 columns/shear walls detailed on Sheet 104; height assumes repeated 3.0m clear floors."],
        ["Floor Framing & Slabs", "75.0%", "0.0%", "N/A", "ESTIMATED_DRAWING", "Beams use average cross-sections and 403.5m grid runs; slabs use assumed 130mm weighted thickness."],
        ["Staircase & Roof Enclosures", "80.0%", "0.0%", "N/A", "MEDIUM_AND_ESTIMATED", "Staircases and mumty detailed; OHT wall/slab thickness estimated without structural schedule."],
        ["Masonry & Finishes", "70.0%", "0.0%", "N/A", "ESTIMATED_DRAWING", "Masonry and plaster rely on gross opening deduction percentages without floor-wise room schedules."],
        ["Scheduled Openings", "100.0%", "0.0%", "PASS", "HIGH_CONFIDENCE_DRAWING", "All 384 door and window assemblies directly transcribed from Sheet 005 schedule."],
        ["Overall Selected Tower Scope", "83.9%", "0.0%", "PARTIAL", "DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION", "Quantity validation coverage: 0%. Quantity accuracy: NOT CALCULATED. No itemized BOQ available."]
    ]
    write_csv("05_Validation/coverage_report.csv", cov_headers, cov_rows)

# ==============================================================================
# STEP 8 & 9: FINAL PROJECT AUDIT & CORRECTION RECONCILIATION REPORT
# ==============================================================================

def step8_and_step9():
    # 1. Update 07_Final_Prototype_Dataset/calculated_quantities_high_confidence.csv
    high_headers = [
        "Parameter ID", "Scope Category", "Parameter Description", "Verified Quantity", "Unit",
        "Drawing Reference", "Sheet ID", "Drawing Revision", "Confidence Classification", "Audit Verification Basis"
    ]
    high_rows = [
        ["HC-001", "Project Scope", "Single Tower Allocated Plinth Area", "3419.38", "sq.m", "BoQ_3 Item 1.01 & AR/TD/001", "Sheet 001", "R0", "HIGH", "Calculated from 30.08m x 16.08m footprint + mumty (34.18 m2); matches BoQ_3 Item 1.01 (27,355 / 8)."],
        ["HC-002", "Project Scope", "Dwelling Units Count per Tower", "24", "units", "AR/TD/002-007 & DBR Section 1", "Sheets 002-007", "R0", "HIGH", "Direct architectural plan count: 4 units/floor x 6 residential floors."],
        ["HC-003", "Project Scope", "Storey Profile Count", "7 (Stilt + 6)", "storeys", "AR/TD/010-013", "Sheets 010-013", "R0", "HIGH", "Direct architectural elevation count: Stilt floor + 6 residential floors."],
        ["HC-004", "Building Geometry", "Gross Tower Footprint Dimensions", "30.08 x 16.08 (483.60)", "m (sq.m)", "AR/TD/001 & STR/TD/105", "Sheet 001 / 105", "R0", "HIGH", "Directly printed structural grid dimensions (Grid 1-10: 30.08m, Grid A-F: 16.08m)."],
        ["HC-005", "Substructure", "Foundation Bored Piles Count", "207", "piles", "STR/TD/HOUSING(G+6)/100", "Sheet 100", "R0", "HIGH", "Direct visual count of individual pile symbols on foundation layout plan."],
        ["HC-006", "Substructure", "Bored Pile Diameter", "600", "mm", "STR/TD/HOUSING(G+6)/100 & DBR p.35", "Sheet 100", "R0", "HIGH", "Directly scheduled on Sheet 100 title block notes and DBR Section 3."],
        ["HC-007", "Superstructure", "Framed Columns Count", "16", "columns", "STR/TD/HOUSING(G+6)/104", "Sheet 104", "R0", "HIGH", "Direct schedule count: 4 C1 (1200x350), 8 C2 (1200x300), 4 C3 (1200x300)."],
        ["HC-008", "Superstructure", "Ductile Shear Walls Count", "33", "wall legs", "STR/TD/HOUSING(G+6)/104", "Sheet 104", "R0", "HIGH", "Direct schedule count: 12 SW1, 4 SW2, 4 SW3, 4 SW4, 4 SW5, 5 CW (SW6-SW10)."],
        ["HC-009", "Openings", "Scheduled Flush Door Units", "216", "nos", "AR/TD/005 Door Schedule", "Sheet 005", "R0", "HIGH", "Direct schedule count: 48 D1 (1000x2100), 96 D2 (900x2100), 72 D3 (750x2100)."],
        ["HC-010", "Openings", "Scheduled Window & Ventilator Units", "168", "nos", "AR/TD/005 Window Schedule", "Sheet 005", "R0", "HIGH", "Direct schedule count: W1-W4 (120 nos) + V1-V2 (48 nos)."]
    ]
    write_csv("07_Final_Prototype_Dataset/calculated_quantities_high_confidence.csv", high_headers, high_rows)

    # 2. Update 07_Final_Prototype_Dataset/calculated_quantities_estimated.csv
    est_headers = [
        "Quantity ID", "Trade Category", "Element Description", "Estimated Value", "Unit",
        "Concrete Grade", "Steel Grade", "Governing Assumption", "Drawing Reference", "Confidence Classification", "Audit Downgrade Rationale"
    ]
    est_rows = [
        ["EST-001", "Substructure", "Bored RCC Piles Concrete", "1053.49", "m3", "M30", "-", "ASM-001 (18m depth)", "STR/TD/100 & DBR p.35", "ESTIMATED", "207 piles counted; depth 18m is derived from DBR range 15-20m, not on drawing."],
        ["EST-002", "Substructure", "Bored RCC Piles Reinforcement Steel", "99.24", "MT", "-", "Fe 500D", "ASM-001/002 (8-T20 cage)", "STR/TD/100 & DBR p.35", "ESTIMATED", "Assumed 8-T20 cage and 18m length (94.2 kg/m3 intensity); no sheet-wise BBS."],
        ["EST-003", "Superstructure", "Columns C1-C3 Concrete", "126.00", "m3", "M30", "-", "Assumed 3.0m clear ht x 7 levels", "STR/TD/104", "MEDIUM", "Sections scheduled on Sheet 104; uses repeated floor height assumption."],
        ["EST-004", "Superstructure", "Columns C1-C3 Reinforcement Steel", "52.41", "MT", "-", "Fe 500D", "Scheduled bars + 50d lap rule", "STR/TD/104", "MEDIUM", "Bar counts scheduled (14-T32+8-T25, 22-T25, 22-T20); cut lengths use 3.0m floor ht."],
        ["EST-005", "Superstructure", "Shear Walls SW1-SW10 Concrete", "349.45", "m3", "M30", "-", "Assumed 3.0m clear ht x 7 levels", "STR/TD/104", "MEDIUM", "Cross sections scheduled on Sheet 104; uses repeated floor height assumption."],
        ["EST-006", "Superstructure", "Shear Walls SW1-SW10 Steel", "30.12", "MT", "-", "Fe 500D", "Scheduled cages + web mesh", "STR/TD/104", "MEDIUM", "Boundary bars and web mesh scheduled on Sheet 104; cut lengths assume 3.0m ht."],
        ["EST-007", "Substructure", "Plinth Beams PB1-PB34 Concrete", "47.61", "m3", "M30", "-", "Reconciled 403.5m length", "STR/TD/105", "ESTIMATED", "Uses 403.5m grid run and weighted section 0.118 m2; no individual member schedule."],
        ["EST-008", "Substructure", "Plinth Beams Reinforcement Steel", "6.43", "MT", "-", "Fe 500D", "Assumed 135 kg/m3 intensity", "STR/TD/105", "ESTIMATED", "Uses preliminary steel intensity rule of thumb; no sheet-wise BBS."],
        ["EST-009", "Superstructure", "Floor Beams B1-B34 (Floors 1-6) Concrete", "289.80", "m3", "M30", "-", "Reconciled 403.5m x 6 levels", "STR/TD/107", "ESTIMATED", "Uses 403.5m grid run, 0.1197 m2 weighted section, and 6 repeated floors."],
        ["EST-010", "Superstructure", "Terrace Beams TB1-TB34 Concrete", "48.30", "m3", "M30", "-", "Reconciled 403.5m length", "STR/TD/108", "ESTIMATED", "Uses 403.5m grid run and 0.1197 m2 weighted section."],
        ["EST-011", "Superstructure", "Floor & Terrace Beams Reinforcement", "47.33", "MT", "-", "Fe 500D", "Assumed 140 kg/m3 intensity", "STR/TD/107-108", "ESTIMATED", "Uses preliminary steel intensity rule of thumb across 7 levels; no shop BBS."],
        ["EST-012", "Superstructure", "Suspended Floor Slabs (Floors 1-6) Concrete", "331.47", "m3", "M30", "-", "Reconciled 424.96 m2 net slab", "STR/TD/107", "ESTIMATED", "Uses 424.96 m2 net slab (483.60 - 58.64 core voids) x 6 x 130mm weighted thickness."],
        ["EST-013", "Superstructure", "Terrace Roof Slab Concrete", "55.24", "m3", "M30", "-", "Reconciled 424.96 m2 net slab", "STR/TD/108", "ESTIMATED", "Uses 424.96 m2 net slab x 130mm weighted thickness."],
        ["EST-014", "Superstructure", "Suspended Slabs Reinforcement Steel", "36.69", "MT", "-", "Fe 500D", "Assumed 89.17 kg/m3 intensity", "STR/TD/107", "ESTIMATED", "Slab schedules S1/S2 T8@125/150 c/c; cut lengths use preliminary intensity."],
        ["EST-015", "Superstructure", "Balconies & Chajjas Concrete", "20.02", "m3", "M30", "-", "Projected area across 7 levels", "STR/TD/107", "ESTIMATED", "Derived without individual piece schedule."],
        ["EST-016", "Superstructure", "Doglegged Staircase Cores Concrete", "26.60", "m3", "M30", "-", "28 flights x 0.95 m3/flight", "STR/TD/110", "MEDIUM", "Flight geometry scheduled on Sheet 110; 28 flights repeated across 7 levels."],
        ["EST-017", "Superstructure", "Doglegged Staircases Reinforcement Steel", "2.92", "MT", "-", "Fe 500D", "Direct flight schedule", "STR/TD/110", "MEDIUM", "Flight rebar scheduled on Sheet 110; repeated across 28 flights."],
        ["EST-018", "Superstructure", "Mumty Structure Concrete", "16.77", "m3", "M30", "-", "Dimensions scheduled", "STR/TD/109", "MEDIUM", "Mumty columns (6.74 m3) + walls/roof (10.03 m3)."],
        ["EST-019", "Superstructure", "Mumty Reinforcement Steel", "1.29", "MT", "-", "Fe 500D", "Scheduled rebar", "STR/TD/109", "MEDIUM", "Columns (0.58 MT) + wall/roof links (0.71 MT)."],
        ["EST-020", "Substructure", "PCC Lean Concrete (1:5:10)", "18.00", "m3", "M10", "-", "ASM-003 (75mm thickness)", "STR/TD/101", "ESTIMATED", "Assumed 75mm leveling layer under caps and plinth trenches."],
        ["EST-021", "Masonry", "External 230mm & Internal 115mm Brickwork", "623.65", "m3", "-", "-", "ASM-007/008 (assumed deductions)", "AR/TD/005-012", "ESTIMATED", "External (216.80 m3) + Internal (406.85 m3); uses assumed opening deduction ratios."],
        ["EST-022", "Finishes", "Internal 12mm & External 18mm Cement Plaster", "14850.00", "sq.m", "-", "-", "ASM-009 (surface ratio)", "AR/TD/006-013", "ESTIMATED", "Internal (11,450 sq.m) + External (3,400 sq.m); uses gross surface area ratio."],
        ["EST-023", "Finishes", "Tile & Stone Flooring (Vitrified, Ceramic, Kota)", "2700.00", "sq.m", "-", "-", "Carpet area approximations", "AR/TD/005-007, 110", "ESTIMATED", "Vitrified (1,848 sq.m) + Ceramic (372 sq.m) + Kota stone (480 sq.m)."],
        ["EST-024", "Finishes", "Internal & External Painting Surface", "14850.00", "sq.m", "-", "-", "Plaster surface equivalence", "Tender Specifications", "ESTIMATED", "Estimated indirectly from gross plaster area."]
    ]
    write_csv("07_Final_Prototype_Dataset/calculated_quantities_estimated.csv", est_headers, est_rows)

    # 3. Update 07_Final_Prototype_Dataset/calculated_quantities_unsupported.csv
    unsup_headers = [
        "Quantity ID", "Trade Category", "Element Description", "Preliminary Value", "Unit",
        "Nature of Unresolved Contradiction / Missing Data", "Required Resolution Action"
    ]
    unsup_rows = [
        [
            "UNS-001", "Substructure", "RCC Pile Caps Concrete Volume", "185.00 to 208.38", "m3",
            "CRITICAL CONTRADICTION: Plan layout (Sheet 101) shows 54 cap entities (208.38 m3), but preliminary takeoff summary claimed 84 caps (185.00 m3). Cap depth 1.0m is unverified on drawings. Pile allocation leaves 91 piles unaccounted for under strip caps.",
            "Requires obtaining official foundation schedule or detailed shop drawings to reconcile exact cap counts, dimensions, depths, and pile groupings."
        ],
        [
            "UNS-002", "Substructure", "RCC Pile Caps Reinforcement Steel", "20.35", "MT",
            "UNSUPPORTED INTENSITY: Uses unverified 110 kg/m3 preliminary intensity applied to unreconciled cap concrete volume. No bar bending schedule exists on Sheet 101.",
            "Requires structural engineering BBS for pile caps with bar marks, spacing, and anchorage details."
        ],
        [
            "UNS-003", "Substructure", "Stilt Grade Slab Edge Thickening Allowance", "5.70", "m3",
            "UNMEASURED ADJUSTMENT: Uniform 125mm slab across 438 m2 net area yields 54.75 m3. Prior claim of 60.45 m3 relied on an arbitrary 5.70 m3 edge thickening allowance.",
            "Requires sheet-wise transcription of perimeter haunches and grade beam thickening details."
        ],
        [
            "UNS-004", "Superstructure", "Overhead Water Tank (OHT) Concrete & Steel", "16.50 m3 / 1.98 MT", "m3 / MT",
            "UNSCHEDULED ELEMENT: Tank wall (150mm) and base (200mm) thicknesses are assumed based on general engineering practice (ASM-010). No structural drawing sheet schedule exists.",
            "Requires structural detail drawing for rooftop water retaining structures."
        ],
        [
            "UNS-005", "Finishes", "Suspended False Ceiling Works", "0.00", "sq.m",
            "EXCLUDED TRADE: Typical workmen residential flats have bare painted RCC slab; false ceiling is neither scheduled nor specified.",
            "Retain as excluded unless client issues a variation order for common corridors."
        ],
        [
            "UNS-006", "Substructure", "Soil Improvement Pressure Grouting", "0.00", "m3",
            "EXCLUDED TRADE: Geotechnical report mandates bored piles bearing into dense stratum; no pressure grouting required.",
            "Retain as excluded."
        ],
        [
            "UNS-007", "Facade", "Structural Glazing & Curtain Walling", "0.00", "sq.m",
            "EXCLUDED TRADE: Architectural elevations confirm standard punched aluminum sliding windows.",
            "Retain as excluded."
        ],
        [
            "UNS-008", "Interiors", "Custom Wood Wall Paneling & Joinery", "0.00", "sq.m",
            "EXCLUDED TRADE: Standard residential workmen flats provide bare plaster walls.",
            "Retain as excluded."
        ]
    ]
    write_csv("07_Final_Prototype_Dataset/calculated_quantities_unsupported.csv", unsup_headers, unsup_rows)

    # 4. Update 09_Calculation_Audit/calculation_audit_log.csv
    log_headers = [
        "Audit ID", "Element / Topic", "Original Preliminary Claim", "Audit Finding & Evidence",
        "Reconciliation & Correction Made", "Revised Status", "Governing Standard / Traceability"
    ]
    log_rows = [
        ["AUD-001", "Contract Award Baseline", "Award claimed at ₹113.06 Cr (and ₹157.25 Cr media)", "Official RITES status (Dec 2025) confirms award to M/s Badri Rai & Company for ₹128.14 Cr (excl GST) with 24 months duration.", "Corrected award value to ₹128.14 Cr across all files. Pro-rata 1/8th allocation (₹16.02 Cr) labeled rough benchmark only.", "CORRECTED", "status_of_Tender_dealt_Dec_2025_Badri_Rai_Award.pdf"],
        ["AUD-002", "Cost Validation Claims", "Cost accuracy validated within 9.8% of contract award", "No itemized official BOQ/rate/amount available for selected tower. Market rates and rule-of-thumb MEP costs were used.", "Cost accuracy set to NOT CALCULATED. All cost rows marked NOT_VALIDATED, confidence LOW, use_for_model_validation NO.", "CORRECTED", "Tender EPC Mode-II Conditions"],
        ["AUD-003", "Quantity Validation Claims", "Quantities claimed as 100% BOQ validated (0.00% error)", "Tender is EPC Mode-II Lump-Sum with area-based schedule; contains ZERO itemized material quantities.", "Quantity validation coverage set to 0%. Quantity accuracy set to NOT CALCULATED. Plinth area and units retained as scope checks.", "CORRECTED", "BoQ_3_Plumbing_Sanitary Item 1.01"],
        ["AUD-004", "Foundation Pile Cap Count", "Claimed 84 caps (185.00 m3)", "CRITICAL CONTRADICTION: Sheet 101 layout plan shows 54 cap entities (208.38 m3). Piles accounted for by 54 caps leave 91 piles unresolved under strip caps.", "Pile cap concrete marked UNRESOLVED_CONTRADICTION / ASSUMPTION_REQUIRED. Removed from high-confidence totals.", "UNRESOLVED_CONTRADICTION", "STR/TD/HOUSING(G+6)/101"],
        ["AUD-005", "Bored RCC Pile Depth", "1,053.49 m3 Concrete claimed HIGH confidence", "207 piles counted on Sheet 100, but pile depth is NOT scheduled on drawing. Depth 18m is derived from DBR range 15-20m.", "Downgraded from HIGH to ESTIMATED (ASM-001).", "DOWNGRADED_TO_ESTIMATED", "STR/TD/100 & DBR p.35"],
        ["AUD-006", "Beam Length & Cross Section", "Beams claimed HIGH confidence; 403.5m vs 420m contradiction", "420m was an unverified rounded estimate; 403.5m is grid-derived. Cross-sections (0.1197 m2) are assumed averages; 6 floors repeated.", "Reconciled to 403.5m grid run; downgraded from HIGH to ESTIMATED.", "DOWNGRADED_TO_ESTIMATED", "STR/TD/105-108"],
        ["AUD-007", "Grade Slab Area & Thickening", "Claimed 483.60 m2 gross x 0.125m = 60.45 m3 HIGH confidence", "Gross footprint is 483.60 m2; net slab area after core deductions is 438.00 m2 (54.75 m3). 60.45 m3 required an unmeasured 5.70 m3 edge thickening.", "Uniform slab = 54.75 m3; edge thickening (5.70 m3) marked ASSUMPTION_REQUIRED.", "DOWNGRADED_TO_ASSUMPTION_REQUIRED", "STR/TD/105"],
        ["AUD-008", "Suspended Slab Area & Thickness", "Claimed 428 m2 / 125mm HIGH confidence", "Exact net slab after deducting measured core shafts is 424.96 m2 (428 m2 was rounded). Thickness 130mm is assumed weighted average (S1 125mm, S2 150mm).", "Reconciled to 424.96 m2; thickness 130mm marked assumed weighted average; downgraded to ESTIMATED.", "DOWNGRADED_TO_ESTIMATED", "STR/TD/107"],
        ["AUD-009", "Total Concrete Volume Split", "Total concrete claimed inconsistently as 2617.55 vs 2635.55 m3", "2,617.55 m3 is RCC M30 only; 18.00 m3 is PCC M10 lean concrete. Total combined concrete is 2,635.55 m3.", "Explicitly separated RCC M30 (2,617.55 m3) and PCC M10 (18.00 m3) across all files.", "CORRECTED", "Structural Sheets 100-110"],
        ["AUD-010", "Reinforcement BBS Claims", "Rebar claimed HIGH confidence (300.85 MT)", "No bar bending schedule exists for piles, caps, beams, or slabs. Generic kg/m3 intensities were used for beams (140), slabs (90), piles (94.2), caps (110).", "All rebar downgraded: Columns/walls/stairs to MEDIUM (bar counts scheduled, 50d lap rule used); Piles/caps/beams/slabs to ESTIMATED / ASSUMPTION_REQUIRED.", "DOWNGRADED", "STR/TD/100-110"]
    ]
    write_csv("09_Calculation_Audit/calculation_audit_log.csv", log_headers, log_rows)

    # 5. Rewrite 07_Final_Prototype_Dataset/final_project_audit.md (STEP 8)
    final_audit_md = """# Final Project Calculation Audit & Integrity Report

## Executive Verdict

```text
Dataset status: DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION
External BOQ Material Validation: 0.0% (No item-wise BOQ in EPC Mode-II tender)
Cost Accuracy: NOT CALCULATED (No official itemized priced BOQ available for selected tower scope)
Quantity Accuracy: NOT CALCULATED (No independent itemized BOQ quantities available)
Macro Scope Consistency Check: PASS (Plinth Area: 3,419.38 sq.m, Units: 24, Storeys: Stilt + 6)
Tender Award Baseline: M/s Badri Rai & Company (RITES Status Dec 2025: ₹128.14 Crore excluding GST, 24 Months)
Model Training Readiness: BLOCKED (Requires reconciliation of contradictory foundation schedules and shop BBS)
```

---

## 1. Project Integrity & Baseline Corrections

- **Official Tender Reference**: `RITES/NERPO/OIL/BQ-HOUSING/25`
- **Client**: Oil India Limited (OIL)
- **Project Management Agency**: RITES Limited (Tender Cell-NERPO)
- **Project Title**: Construction of Workman Housing Complex (BQ Area) on EPC Mode-II at OIL Duliajan, Assam
- **Contractor**: **M/s Badri Rai & Company**
- **Contract Award Value**: **₹128.14 Crore** (excluding GST)
- **Scheduled Completion Period**: **24 Months**
- **Document Source**: `08_Execution_Actuals/status_of_Tender_dealt_Dec_2025_Badri_Rai_Award.pdf`
- **Award Baseline Correction**: All prior references to ₹113.06 Crore (preliminary status) and ₹157.25 Crore (corporate media announcement) have been **superseded and corrected**.
- **Proportional Benchmark Notice**: Dividing ₹128.14 Crore by 8 towers (₹16.0175 Crore per tower) represents strictly a rough project-level proportional benchmark and must **NOT** be treated as an official validated tower cost.
- **Zero-Mixing Protocol**: Historical 2020 OIL tender package (`NIT_CPI4685P21`) remains quarantined in `99_Unverified_or_Related_References` and completely excluded.

---

## 2. Calculation Audit vs. BOQ Validation Statement

This project was tendered on an **EPC Mode-II Lump-Sum Component Basis**. The official tender documents contain **no itemized construction bill of quantities** for materials.

Consequently:
1. **Material quantities are drawing-based estimates, NOT externally BOQ-validated quantities.**
2. **Quantity validation coverage: 0%**.
3. **Quantity accuracy: NOT CALCULATED**.
4. **Cost accuracy: NOT CALCULATED**.
5. Prior preliminary claims of "100% validation" or "0% quantity error" on concrete, steel, or finishes were improper and have been **revoked**.
6. The official EPC schedule (`BoQ_3_Plumbing_Sanitary_pdf-2025-Aug-28-17-28-6.pdf`, Item 1.01) provides binding ground truth **solely for macro scope parameters**:
   - Tower Plinth Area: **3,419.38 sq.m** (27,355 sq.m ÷ 8) -> **scope_consistency_check = PASS**.
   - Dwelling Units: **24 units** (192 units ÷ 8) -> **scope_consistency_check = PASS**.
   - Vertical Profile: **Stilt + 6 storeys** -> **scope_consistency_check = PASS**.

---

## 3. Discrepancy Log & Audit Findings

| Audit ID | Element / Trade | Original Claim | Audit Finding | Correction Made | Revised Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AUD-001** | Contract Award Cost | ₹113.06 Cr / ₹157.25 Cr | Official RITES tender dealt record (Dec 2025) confirms award to M/s Badri Rai & Co. at ₹128.14 Cr (excl GST), 24 months. | Award value updated to ₹128.14 Cr across all files. Pro-rata benchmark noted as ₹16.02 Cr. | `CORRECTED` |
| **AUD-002** | Cost Validation Claims | Cost validated within 9.8% margin | No itemized priced BOQ exists for selected tower. Market rates and rule-of-thumb MEP costs were used. | Cost accuracy set to NOT CALCULATED. All cost rows marked NOT_VALIDATED, confidence LOW. | `CORRECTED` |
| **AUD-003** | Quantity Validation Claims | 100% BOQ Validated (0.00% error) | Tender is EPC Mode-II Lump-Sum with area-based pricing; contains ZERO itemized material quantities. | Quantity validation coverage set to 0%. Quantity accuracy set to NOT CALCULATED. Scope checks retained. | `CORRECTED` |
| **AUD-004** | Foundation Pile Cap Count | Claimed 84 caps (185.00 m3) | CRITICAL CONTRADICTION: Sheet 101 layout plan shows 54 cap entities (208.38 m3). Piles accounted for by 54 caps leave 91 piles unresolved under strip caps. | Pile cap concrete marked UNRESOLVED_CONTRADICTION / ASSUMPTION_REQUIRED. Removed from high-confidence totals. | `UNRESOLVED_CONTRADICTION` |
| **AUD-005** | Bored RCC Pile Depth | 1,053.49 m3 Concrete claimed HIGH confidence | 207 piles counted on Sheet 100, but pile depth is NOT scheduled on drawing. Depth 18m is derived from DBR range 15-20m. | Downgraded from HIGH to ESTIMATED (ASM-001). | `DOWNGRADED_TO_ESTIMATED` |
| **AUD-006** | Beam Length & Cross Section | Beams claimed HIGH confidence; 403.5m vs 420m contradiction | 420m was an unverified rounded estimate; 403.5m is grid-derived. Cross-sections (0.1197 m2) are assumed averages; 6 floors repeated. | Reconciled to 403.5m grid run; downgraded from HIGH to ESTIMATED. | `DOWNGRADED_TO_ESTIMATED` |
| **AUD-007** | Grade Slab Area & Thickening | Claimed 483.60 m2 gross x 0.125m = 60.45 m3 HIGH confidence | Gross footprint is 483.60 m2; net slab area after core deductions is 438.00 m2 (54.75 m3). 60.45 m3 required an unmeasured 5.70 m3 edge thickening. | Uniform slab = 54.75 m3; edge thickening (5.70 m3) marked ASSUMPTION_REQUIRED. | `DOWNGRADED_TO_ASSUMPTION_REQUIRED` |
| **AUD-008** | Suspended Slab Area & Thickness | Claimed 428 m2 / 125mm HIGH confidence | Exact net slab after deducting measured core shafts is 424.96 m2 (428 m2 was rounded). Thickness 130mm is assumed weighted average (S1 125mm, S2 150mm). | Reconciled to 424.96 m2; thickness 130mm marked assumed weighted average; downgraded to ESTIMATED. | `DOWNGRADED_TO_ESTIMATED` |
| **AUD-009** | Total Concrete Volume Split | Total concrete claimed inconsistently as 2617.55 vs 2635.55 m3 | 2,617.55 m3 is RCC M30 only; 18.00 m3 is PCC M10 lean concrete. Total combined concrete is 2,635.55 m3. | Explicitly separated RCC M30 (2,617.55 m3) and PCC M10 (18.00 m3) across all files. | `CORRECTED` |
| **AUD-010** | Reinforcement BBS Claims | Rebar claimed HIGH confidence (300.85 MT) | No bar bending schedule exists for piles, caps, beams, or slabs. Generic kg/m3 intensities were used for beams (140), slabs (90), piles (94.2), caps (110). | All rebar downgraded: Columns/walls/stairs to MEDIUM (bar counts scheduled, 50d lap rule used); Piles/caps/beams/slabs to ESTIMATED / ASSUMPTION_REQUIRED. | `DOWNGRADED` |

---

## 4. Audit Classifications: What is Verified, Estimated, Assumption-Based, and Not Validated

### 4.1 What is Verified (Direct Drawing Evidence - HIGH Confidence)
1. **Tower Plinth Area**: 3,419.38 sq.m (Footprint 30.08m × 16.08m + Mumty 34.18 m²; BoQ_3 Item 1.01).
2. **Dwelling Units**: Exactly 24 units across 6 floors (Sheets AR/TD/002-007).
3. **Storey Profile**: Stilt + 6 storeys + Mumty/OHT (Sheets AR/TD/010-013).
4. **Gross Footprint**: 30.08 m length × 16.08 m width = 483.60 sq.m (Sheets AR/TD/001 & STR/TD/105).
5. **Foundation Bored Piles Count**: Exactly 207 piles directly counted on Sheet 100 layout plan.
6. **Pile Diameter**: 600 mm directly scheduled on Sheet 100 notes.
7. **Vertical Framed Columns Count**: 16 columns (4 C1, 8 C2, 4 C3) directly scheduled on Sheet 104.
8. **Ductile Shear Walls Count**: 33 wall legs (12 SW1, 4 SW2, 4 SW3, 4 SW4, 4 SW5, 5 CW) scheduled on Sheet 104.
9. **Scheduled Door Assemblies**: 216 units (48 D1, 96 D2, 72 D3) on Sheet 005 schedule.
10. **Scheduled Window & Ventilator Assemblies**: 168 units (W1-W4, V1-V2) on Sheet 005 schedule.

### 4.2 What is Estimated (Drawing-Based with Controlled Derivations - MEDIUM to ESTIMATED)
1. **Superstructure Columns & Shear Walls Concrete**: 475.45 m³ (M30) [Sheet 104 cross-sections directly visible; clear height 3.0m assumed across 7 levels].
2. **Superstructure Columns & Shear Walls Reinforcement**: 82.53 MT [Bar counts directly scheduled on Sheet 104; cut lengths assume 3.0m floor height and 50d lap rule].
3. **Bored RCC Piles Concrete**: 1,053.49 m³ [207 piles counted; depth 18m assumed from DBR range 15-20m, ASM-001].
4. **Bored Piles Reinforcement Steel**: 99.24 MT [Assumed 8-T20 cage full depth per DBR/IS 2911, ASM-001/002].
5. **Beams Concrete (Plinth, Typical, Terrace)**: 385.71 m³ [Reconciled 403.5m grid run length per floor; weighted average cross-sections].
6. **Beams Reinforcement Steel**: 53.76 MT [Assumed steel intensity 135–140 kg/m³].
7. **Suspended Slabs Concrete (Floors 1-6 + Terrace)**: 386.71 m³ [Reconciled 424.96 m² net slab; assumed 130mm weighted average thickness].
8. **Suspended Slabs Reinforcement Steel**: 36.69 MT [Assumed 89.17 kg/m³ steel intensity].
9. **Doglegged Staircase Concrete & Steel**: 26.60 m³ / 2.92 MT [Flight geometry scheduled on Sheet 110; 28 flights repeated].
10. **PCC Lean Concrete (M10)**: 18.00 m³ [Assumed 75mm leveling layer, ASM-003].
11. **Brick Masonry**: 623.65 m³ [Assumed opening deduction ratios: 23% external, 10% internal, ASM-007/008].
12. **Cement Plaster**: 14,850.00 sq.m [Gross surface area ratio, ASM-009].
13. **Tile & Stone Flooring**: 2,700.00 sq.m [Carpet area approximations].

### 4.3 What is Assumption-Based / Contradictory (ASSUMPTION_REQUIRED / UNRESOLVED)
1. **RCC Pile Caps Concrete & Steel**: 185.00 m³ vs 208.38 m³ / 20.35 MT [CRITICAL CONTRADICTION: 54 caps on layout plan vs 84 caps in preliminary summary; 91 piles unaccounted for under strip caps; cap depth 1.0m assumed without sheet schedule, ASM-002].
2. **Stilt Grade Slab Thickening Allowance**: 5.70 m³ [Uniform slab = 54.75 m³; prior 60.45 m³ required an unmeasured 5.70 m³ edge thickening].
3. **Overhead Water Tank (OHT) Concrete & Steel**: 16.50 m³ / 1.98 MT [Assumed 150mm walls / 200mm base thickness without structural sheet schedule, ASM-010].
4. **Beam Run Length Approximation**: Legacy 420m vs reconciled 403.5m.

### 4.4 What is Not Validated
1. **Concrete Volumes**: 0% BOQ validation coverage. No itemized concrete BOQ exists.
2. **Reinforcement Steel**: 0% BOQ validation coverage. No itemized rebar BOQ exists.
3. **Formwork / Shuttering**: 0% BOQ validation coverage. No itemized formwork BOQ exists.
4. **Finishes & Masonry**: 0% BOQ validation coverage. No itemized architectural BOQ exists.
5. **Single Tower Construction Cost**: Not validated against contract. Cost accuracy: NOT CALCULATED.

---

## 5. Model Training Readiness & Blockers

```text
CAN THIS PILOT MOVE TO LABOUR / DURATION MODELLING YET?
VERDICT: NO. BLOCKED.
```

### Why It Cannot Move to Labour/Duration Modeling Yet
1. **Unresolved Foundation Contradiction**: The 54-cap vs 84-cap discrepancy directly impacts foundation concrete volume (a variance of 23.38 m³) and excavation/shuttering mandays. Modeling duration on an unresolved foundation schedule will produce invalid milestone schedules.
2. **Absence of Bar Bending Schedule (BBS)**: Steel reinforcement represents 300.85 MT of material. Without bar cut lengths, hook details, and lap staggering locations, rebar fixing labour (bar benders/mandays) cannot be calculated deterministically.
3. **Beam and Slab Cross-Section Averaging**: Beam lengths (403.5m) and cross-sections (0.1197 m²) are weighted averages rather than member-by-member schedules. This prevents reliable formwork and cycle-time calculation per floor.
4. **No Itemized Cost / Rate Benchmark**: Without an official itemized price schedule, productivity-to-cost linkage cannot be validated.

---

## 6. Exact Missing Documents Required

To unblock the dataset and transition it to a fully validated training state, the following official project records must be obtained:

1. **Tabulated Foundation & Pile Schedule**:
   - Structural drawing sheet showing pile termination depth, founding stratum, cut-off level, and pile reinforcement cage detailing.
2. **Tabulated Pile Cap Schedule**:
   - Structural drawing sheet specifying dimensions (length, width, depth) for each cap mark (PC-1 to PC-W) and exact pile allocation.
3. **Bar Bending Schedules (BBS)**:
   - Official reinforcement schedules for columns (C1-C3), shear walls (SW1-SW10), floor beams (B1-B34), and suspended slabs (S1-S2).
4. **Floor-Wise Room Finishes Schedule**:
   - Architectural schedule detailing floor-by-floor room dimensions, door/window deduction schedules, and exact plaster/flooring areas.
5. **Contractor's Approved Detailed Project Report (DPR) / Itemized EPC Cost Breakdown**:
   - Badri Rai & Company's approved contract price breakdown or rate analysis for the 8 residential towers.
"""
    write_text("07_Final_Prototype_Dataset/final_project_audit.md", final_audit_md)

    # 6. Create 09_Calculation_Audit/correction_reconciliation_report.md (STEP 9)
    report_md = """# Calculation Audit Correction & Reconciliation Report

## 1. Executive Summary
- **Project**: OIL/RITES Duliajan BQ Workmen Housing Complex
- **Folder**: `OIL-RITES-Duliajan-BQ-Housing`
- **Tender Reference**: `RITES/NERPO/OIL/BQ-HOUSING/25`
- **Selected Model Scope**: One typical Stilt+6 BQ Workmen Housing residential tower (one of 8 identical towers)
- **Audit Mandate**: Correct, reconcile, and downgrade unsupported claims; remove fictitious BOQ validation claims; enforce defensible civil engineering intelligence standards.

---

## 2. Corrected Award and Baseline Information
- **Contract Award File**: `08_Execution_Actuals/status_of_Tender_dealt_Dec_2025_Badri_Rai_Award.pdf`
- **Successful Contractor**: **M/s Badri Rai & Company**
- **Official Contract Award Value**: **₹128.14 Crore** (excluding GST)
- **Contract Scheduled Duration**: **24 Months**
- **Tender Status Date**: **December 2025** (RITES Tender Cell-NERPO)
- **Superseded Preliminary Figure**: ₹113.06 Crore (preliminary tender dealt status) has been corrected across all files.
- **Excluded Media Figure**: ₹157.25 Crore (corporate announcement from April 2025) is strictly excluded.
- **Proportional Benchmark Treatment**: ₹128.14 Crore ÷ 8 = ₹16.0175 Crore per tower is explicitly labeled as a **rough project-level proportional benchmark only**, NOT an official validated tower cost.

---

## 3. Removed or Downgraded Cost Claims
1. **Removed Claims**: All claims that single-tower construction cost was "validated within a 9.8% margin" against contract award have been **completely removed**.
2. **Cost Accuracy Status**:
   ```text
   Cost accuracy: NOT CALCULATED
   Reason: no official itemized priced BOQ available for the selected tower scope.
   ```
3. **Table Reclassification**: In `05_Validation/cost_validation_results.csv`, all rows based on CPWD DSR market rates, assumed MEP percentages (30%), and finishes estimates are marked:
   - `validation_status = NOT_VALIDATED`
   - `confidence = LOW`
   - `use_for_model_validation = NO`
   - `reason = No itemized official BOQ/rate/amount available for selected tower scope`

---

## 4. Downgraded Quantity Rows & Reclassified Confidence Tiers

In accordance with strict audit rules, every quantity relying on average lengths, average cross-sections, repeated floor assumptions, assumed depths, or preliminary steel intensities was downgraded:

| Quantity Item | Original Classification | Revised Classification | Reason for Downgrade |
| :--- | :--- | :--- | :--- |
| **Bored RCC Piles Concrete** (1,053.49 m³) | HIGH | **ESTIMATED** | 207 piles counted, but depth 18m is derived from DBR range 15-20m (ASM-001); not scheduled on drawing. |
| **Bored RCC Piles Steel** (99.24 MT) | HIGH | **ESTIMATED** | Assumed 18m cage length and 8-T20 cage (94.2 kg/m³ intensity, ASM-001/002); no sheet BBS. |
| **Superstructure Columns Concrete** (126.00 m³) | HIGH | **MEDIUM** | Sections scheduled on Sheet 104; height assumes repeated 3.0m clear floors across 7 levels. |
| **Superstructure Columns Steel** (52.41 MT) | HIGH | **MEDIUM** | Bar counts scheduled on Sheet 104; vertical cut lengths use assumed 3.0m height and 50d lap rule. |
| **Shear Walls Concrete** (349.45 m³) | HIGH | **MEDIUM** | Sections scheduled on Sheet 104; height assumes repeated 3.0m clear floors across 7 levels. |
| **Shear Walls Steel** (30.12 MT) | HIGH | **MEDIUM** | Boundary cages and web mesh scheduled; cut lengths assume 3.0m clear height. |
| **Plinth Beams Concrete** (47.61 m³) | HIGH | **ESTIMATED** | Reconciled 403.5m grid run; uses weighted average section 0.118 m² without individual schedule. |
| **Plinth Beams Steel** (6.43 MT) | HIGH | **ESTIMATED** | Uses preliminary 135 kg/m³ steel intensity; no shop BBS. |
| **Floor Beams Concrete** (289.80 m³) | HIGH | **ESTIMATED** | Reconciled 403.5m length, 0.1197 m² weighted section, and 6 repeated floors. |
| **Floor Beams Steel** (47.33 MT) | HIGH | **ESTIMATED** | Uses preliminary 140 kg/m³ steel intensity across 7 levels; no shop BBS. |
| **Suspended Slabs Concrete** (386.71 m³) | HIGH | **ESTIMATED** | Reconciled 424.96 m² net slab; uses assumed 130mm weighted thickness across repeated floors. |
| **Suspended Slabs Steel** (36.69 MT) | HIGH | **ESTIMATED** | Uses preliminary 89.17 kg/m³ steel intensity; no bar-by-bar cut schedule. |
| **RCC Pile Caps Concrete** (185.00 / 208.38 m³) | HIGH | **ASSUMPTION_REQUIRED** | Unresolved contradiction: 54 caps in plan vs 84 caps in summary; assumed 1.0m thickness. |
| **RCC Pile Caps Steel** (20.35 MT) | HIGH | **ASSUMPTION_REQUIRED** | Assumed 110 kg/m³ intensity applied to unreconciled cap concrete volume. |
| **Stilt Grade Slab Thickening** (5.70 m³) | HIGH | **ASSUMPTION_REQUIRED** | Uniform 125mm slab = 54.75 m³; 60.45 m³ required an unmeasured 5.70 m³ thickening allowance. |
| **Overhead Water Tank Concrete & Steel** | HIGH | **ASSUMPTION_REQUIRED** | Wall (150mm) and base (200mm) thicknesses assumed (ASM-010); no structural drawing schedule. |
| **Brick Masonry** (623.65 m³) | HIGH | **ESTIMATED** | Uses assumed gross opening deduction ratios (23% external, 10% internal) without room schedules. |
| **Cement Plaster** (14,850.00 m²) | HIGH | **ESTIMATED** | Calculated from gross surface area ratios without room-by-room perimeter schedules. |
| **Tile & Stone Flooring** (2,700.00 m²) | HIGH | **ESTIMATED** | Uses carpet area approximations without unit-by-unit flat schedules. |

---

## 5. Reconciled Contradictions

1. **Beam Length (403.5 m vs 420 m per floor)**:
   - *Finding*: 403.5 m is derived from grid lines on Sheet 105 (6 longitudinal lines of 30.08m + 14 transverse lines of 16.08m). 420 m was an unverified rounded legacy figure.
   - *Reconciliation*: Standardized on 403.5 m per floor across all schedules; documented 420 m as superseded.
2. **Grade Slab Area (438.00 m² vs 483.60 m²)**:
   - *Finding*: 483.60 m² is the gross footprint (30.08m × 16.08m). 438.00 m² is the net slab area after core deductions. Uniform 125mm slab yields 54.75 m³.
   - *Reconciliation*: Net slab area is 438.00 m² (54.75 m³). The 60.45 m³ figure required an unmeasured 5.70 m³ edge thickening allowance (`ASSUMPTION_REQUIRED`).
3. **Suspended Slab Area (424.96 m² vs 428.00 m²)**:
   - *Finding*: 424.96 m² is the exact deduction based on measured core voids (58.64 m²). 428.00 m² was a rounded figure.
   - *Reconciliation*: Reconciled to 424.96 m² net suspended slab per floor.
4. **Slab Thickness (125 mm vs 130 mm)**:
   - *Finding*: Sheet 107 schedules S1 as 125 mm base slab and S2 as 150 mm sunken slab. 130 mm is an assumed weighted average.
   - *Reconciliation*: Clarified base slab is 125 mm; 130 mm is an assumed weighted average.
5. **Total Concrete Volume Split (2,617.55 m³ vs 2,635.55 m³)**:
   - *Finding*: 2,617.55 m³ is RCC M30 only. 18.00 m³ is PCC M10 lean concrete.
   - *Reconciliation*: Reconciled as: RCC M30 = 2,617.55 m³; PCC M10 = 18.00 m³; Combined Concrete = 2,635.55 m³.
6. **Foundation Pile Cap Count (54 caps vs 84 caps)**:
   - *Finding*: Plan layout on Sheet 101 shows 54 cap entities totaling 208.38 m³, while preliminary takeoff claimed 84 caps totaling 185.00 m³. Furthermore, 54 caps account for only 116 piles, leaving 91 piles unaccounted for under strip caps.
   - *Reconciliation*: Marked as **UNRESOLVED_CONTRADICTION** / **ASSUMPTION_REQUIRED**. Excluded from high-confidence totals.

---

## 6. Files Changed in This Audit Pass

1. `07_Final_Prototype_Dataset/project_metadata.json` (Award value updated to ₹128.14 Cr; status set to REQUIRES_RECONCILIATION; validation accuracy set to NOT CALCULATED)
2. `05_Validation/cost_validation_results.csv` (Cost rows marked NOT_VALIDATED, confidence LOW, accuracy NOT CALCULATED)
3. `05_Validation/quantity_validation_results.csv` (Validation coverage 0%, accuracy NOT CALCULATED, scope checks PASS)
4. `05_Validation/coverage_report.csv` (Material coverage 0%, scope check PASS)
5. `05_Validation/validation_findings.md` (Truth disclosure rewritten; award updated to ₹128.14 Cr)
6. `09_Calculation_Audit/scope_and_validation_statement.md` (Award updated to ₹128.14 Cr; truth disclosure updated)
7. `09_Calculation_Audit/calculation_audit_log.csv` (10 discrepancies tracked and reconciled)
8. `09_Calculation_Audit/beam_length_schedule.csv` (Reconciled to 403.5m; downgraded to ESTIMATED)
9. `09_Calculation_Audit/slab_area_schedule.csv` (Reconciled 438m2 net, 424.96m2 net, 130mm weighted avg; downgraded to ESTIMATED)
10. `09_Calculation_Audit/pile_cap_schedule_audit.csv` (54 vs 84 cap contradiction documented; marked ASSUMPTION_REQUIRED)
11. `09_Calculation_Audit/pile_schedule_audit.csv` (Depth 18m documented as DBR assumption; downgraded to ESTIMATED)
12. `09_Calculation_Audit/formula_ledger.csv` (Confidence tags downgraded; formulas and reconciled dimensions updated)
13. `09_Calculation_Audit/rebar_weight_summary.csv` (Confidence tiers downgraded; BBS audit findings added)
14. `03_Quantity_Takeoff/reinforcement_takeoff.csv` (All rebar downgraded from HIGH confidence)
15. `07_Final_Prototype_Dataset/calculated_quantities_high_confidence.csv` (Restricted to 10 verified parameters: plinth area, unit count, storey count, footprint, pile count, vertical member count, door/window counts)
16. `07_Final_Prototype_Dataset/calculated_quantities_estimated.csv` (24 drawing-derived estimated/medium quantities)
17. `07_Final_Prototype_Dataset/calculated_quantities_unsupported.csv` (8 unresolved / assumption-required items)
18. `07_Final_Prototype_Dataset/final_project_audit.md` (Executive verdict: DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION)
19. `09_Calculation_Audit/correction_reconciliation_report.md` (This document)

---

## 7. Remaining Blockers & Final Readiness Status

```text
Final Dataset Readiness Status: DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION
Model Training / Execution Phase Readiness: BLOCKED
```

### Remaining Blockers:
1. **Foundation Cap Layout Reconciliation**: Reconciling the 54 vs 84 pile cap discrepancy and obtaining tabulated cap depths/reinforcement.
2. **Shop Bar Bending Schedules (BBS)**: Replacing rule-of-thumb steel intensities (140 kg/m³, 90 kg/m³, 135 kg/m³, 94.2 kg/m³) with bar-by-bar cut length schedules.
3. **Room-by-Room Finishes Schedules**: Transcribing individual room wall perimeters and door/window deductions instead of applying gross surface ratios.
4. **Priced Tower BOQ**: Obtaining Badri Rai & Company's approved detailed rate breakdown for the residential towers.
"""
    write_text("09_Calculation_Audit/correction_reconciliation_report.md", report_md)

if __name__ == "__main__":
    step1_and_step2()
    step3_and_step4()
    step6_and_step7()
    step8_and_step9()
    print("All steps completed successfully.")

