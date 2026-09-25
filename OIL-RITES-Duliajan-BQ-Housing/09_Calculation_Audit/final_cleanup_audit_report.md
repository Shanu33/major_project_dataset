# Final Cleanup Audit Report

**Project**: OIL/RITES Duliajan BQ Workmen Housing Complex  
**Tender**: `RITES/NERPO/OIL/BQ-HOUSING/25`  
**Selected Scope**: One typical Stilt+6 BQ Workmen Housing residential tower  
**Audit Date**: September 2026  
**Audit Type**: Stale claims removal, contradiction cleanup, confidence downgrade  

---

## 1. Summary of Cleanup Actions

| Step | Target | Files Changed | Action |
| :--- | :--- | :--- | :--- |
| 1 | Contract Duration Contradiction | 2 files | Removed stale 36-month duration; set tower duration to NOT_CALCULATED |
| 2 | Drawing Readiness Claims | 2 files | Replaced READY_FOR_TAKEOFF with PARTIAL/LEGIBLE; removed 100% verified claims |
| 3 | Assumption Confidence Labels | 2 files | Downgraded all HIGH/HIGH_CONFIDENCE assumptions to MEDIUM |
| 4 | Rebar Lap/Development Register | 1 file | Replaced HIGH_CONFIDENCE with CODE_DERIVED_ASSUMPTION; added BBS note |
| 5 | Global Misleading Phrase Search | 7 files | Replaced HIGH_CONFIDENCE, stale duration, stale readiness across all files |
| 6 | Labour & Duration Files | 3 files | Marked as NOT_CALCULATED / PRELIMINARY; added disclaimers |

---

## 2. Files Checked (Complete List)

All `.md`, `.csv`, `.json` files in folders `00_Project_Control/` through `09_Calculation_Audit/` plus root-level manifests. Excluded: `scratch/` and `99_Unverified*/` directories.

---

## 3. Stale Claims Found and Corrected

### 3.1 Contract Duration

| File | Stale Claim | Correction |
| :--- | :--- | :--- |
| `project_metadata.json` | `overall_contract_duration_months: 36` | Renamed to `_HISTORICAL_NOTE` with supersession explanation |
| `project_metadata.json` | `independent_construction_duration_months: 15` | Set to `NOT_CALCULATED` with explanation note |
| `file_manifest.json` | `₹157.25 Crore, 36 months` in LoA description | Added SUPERSEDED prefix with official award values |
| `duration_estimate.csv` | 36-month overall + 15-month tower | Overall set to 24 months; tower set to NOT_CALCULATED |
| `duration_validation.md` | CPM model claiming 15-month tower duration | Entire file replaced with NOT CALCULATED disclaimer |
| `labour_estimate.csv` | `450 calendar days (15 months)` total | Changed to NOT_VALIDATED with preliminary warning |

### 3.2 Drawing Readiness

| File | Stale Claim | Correction |
| :--- | :--- | :--- |
| `drawing_extraction_readiness_report.md` | `READY_FOR_TAKEOFF` status | Changed to `PARTIAL - READY_FOR_CONTROLLED_TRANSCRIPTION` |
| `drawing_extraction_readiness_report.md` | `100% verified, complete, and READY_FOR_TAKEOFF` | Changed to `partially verified and ready for controlled transcription` |
| `drawing_extraction_readiness_report.md` | `100% complete bar marks` BBS claim | Clarified as partial/derived BBS only |
| `drawing_extraction_readiness_report.md` | `0 Critical Sheets Missing` | Changed to list critical missing data (pile depth, cap count, BBS) |
| `required_sheet_coverage.csv` | 23 rows with `READY_FOR_TAKEOFF` | All changed to `LEGIBLE_FOR_TRANSCRIPTION` |

### 3.3 Assumption Confidence

| File | Stale Claim | Correction |
| :--- | :--- | :--- |
| `02_Building_Element_Model/assumptions_log.csv` | All 10 assumptions labelled `HIGH` | All downgraded to `MEDIUM` |
| `07_Final_Prototype_Dataset/assumptions_log.csv` | ASM-004 to ASM-009 labelled `HIGH_CONFIDENCE` | All downgraded to `MEDIUM` |

### 3.4 Rebar Confidence

| File | Stale Claim | Correction |
| :--- | :--- | :--- |
| `rebar_lap_development_length_register.csv` | All 7 rows `HIGH_CONFIDENCE` | Changed to `CODE_DERIVED_ASSUMPTION` with BBS note |
| `rebar_cut_length_calculations.csv` | All 8 rows `HIGH_CONFIDENCE` | Changed to `CODE_DERIVED_ASSUMPTION` |
| `rebar_bar_mark_schedule.csv` | All 23 rows `HIGH_CONFIDENCE` | Changed to `MEDIUM` |
| `baseline_file_inventory.csv` | 2 rows with `HIGH_CONFIDENCE` | Changed to `MEDIUM` |
| `coverage_report.csv` | `HIGH_CONFIDENCE_DRAWING` for openings | Changed to `DIRECT_DRAWING_EVIDENCE` |

### 3.5 Other Corrections

| File | Stale Claim | Correction |
| :--- | :--- | :--- |
| `final_project_audit.md` | `HIGH Confidence` in section heading 4.1 | Changed to `10 Parameters Only` |
| `final_project_audit.md` | AUD-007/008/010 `HIGH confidence` in body text | Clarified as `(originally HIGH confidence, now ESTIMATED)` |
| `dataset_data_dictionary.md` | HIGH_CONFIDENCE described as active tier | Restricted description to 10 parameters only |

---

## 4. Items Retained as Audit Trail

The following matches of flagged phrases were reviewed and intentionally RETAINED because they document what was originally claimed (audit trail):

- `calculation_audit_log.csv` — "Original Claim" column documenting prior `HIGH confidence` and `100% BOQ validated` claims (6 entries)
- `correction_reconciliation_report.md` — Change log noting "downgraded from HIGH confidence" (2 entries)
- `final_project_audit.md` — Discrepancy table "Original Claim" column (7 entries)

These entries are part of the audit record and correctly describe what was found and corrected. They do NOT make active claims.

---

## 5. Remaining HIGH-Confidence Items (Allowed per Rules)

Only these 10 directly-measured drawing parameters retain HIGH status:

| # | Parameter | Value | Source |
| :--- | :--- | :--- | :--- |
| 1 | Plinth Area | 3,419.38 sq.m | BoQ_3 Item 1.01 |
| 2 | Dwelling Units | 24 | AR/TD/002-007 |
| 3 | Storey Profile | Stilt + 6 | AR/TD/010-013 |
| 4 | Gross Footprint | 30.08m × 16.08m = 483.60 sq.m | AR/TD/001, STR/TD/105 |
| 5 | Pile Count | 207 | STR/TD/100 |
| 6 | Pile Diameter | 600mm | STR/TD/100 |
| 7 | Column Count | 16 | STR/TD/104 |
| 8 | Shear Wall Count | 33 | STR/TD/104 |
| 9 | Door Count | 216 | AR/TD/005 |
| 10 | Window/Vent Count | 168 | AR/TD/005 |

No calculated material quantity (concrete, steel, masonry, plaster, flooring) is classified HIGH.

---

## 6. Final Status After Cleanup

| Dimension | Status |
| :--- | :--- |
| **Contract Duration** | Official: 24 months. Historical 36-month figure: SUPERSEDED. Tower duration: NOT_CALCULATED. |
| **Assumptions** | All 10 assumptions: MEDIUM or ESTIMATED. Zero HIGH assumptions. |
| **Drawing Readiness** | PARTIAL - READY_FOR_CONTROLLED_TRANSCRIPTION. Not READY_FOR_TAKEOFF. |
| **Cost Accuracy** | NOT CALCULATED. No cost accuracy percentage reported. |
| **Quantity Validation** | Coverage: 0%. Accuracy: NOT CALCULATED. |
| **Labour Modelling** | NOT CALCULATED. Preliminary estimates retained as reference only. |
| **Duration Modelling** | NOT CALCULATED. No duration model validated. |
| **Dataset Status** | `DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION` |
| **Model Training Readiness** | BLOCKED. Unresolved pile cap contradiction, no BBS, no itemized BOQ. |

---

## 7. Total Files Modified in This Cleanup Pass

1. `07_Final_Prototype_Dataset/project_metadata.json`
2. `file_manifest.json`
3. `01_Drawing_Registers/drawing_extraction_readiness_report.md`
4. `01_Drawing_Registers/required_sheet_coverage.csv`
5. `02_Building_Element_Model/assumptions_log.csv`
6. `07_Final_Prototype_Dataset/assumptions_log.csv`
7. `09_Calculation_Audit/rebar_lap_development_length_register.csv`
8. `09_Calculation_Audit/rebar_cut_length_calculations.csv`
9. `09_Calculation_Audit/rebar_bar_mark_schedule.csv`
10. `09_Calculation_Audit/baseline_file_inventory.csv`
11. `05_Validation/coverage_report.csv`
12. `06_Labour_and_Duration/duration_estimate.csv`
13. `06_Labour_and_Duration/duration_validation.md`
14. `06_Labour_and_Duration/labour_estimate.csv`
15. `07_Final_Prototype_Dataset/dataset_data_dictionary.md`
16. `07_Final_Prototype_Dataset/final_project_audit.md`
17. `09_Calculation_Audit/final_cleanup_audit_report.md` (this file)

---

## 8. Register-Level Follow-up Correction

### Problem Found
After the initial cleanup pass (sections 1–7 above), the three active drawing register files still contained `READY_FOR_TAKEOFF` labels on all in-scope tower rows:

| Register File | READY_FOR_TAKEOFF Rows Before | After |
| :--- | :--- | :--- |
| `architectural_sheet_register.csv` | **22 rows** | **0** |
| `structural_sheet_register.csv` | **11 rows** | **0** |
| `mep_sheet_register.csv` | **12 rows** | **0** |
| `required_sheet_coverage.csv` | **0** (already fixed) | **0** |
| **Total** | **45 rows** | **0** |

### Corrections Applied

1. **`01_Drawing_Registers/architectural_sheet_register.csv`** — All 22 tower rows changed from `READY_FOR_TAKEOFF` to `LEGIBLE_FOR_TRANSCRIPTION`. Finishes/flooring/toilet sheet evidence notes updated to clarify exact quantities require room-wise transcription.

2. **`01_Drawing_Registers/structural_sheet_register.csv`** — All 11 tower rows corrected with differentiated statuses:
   - Sheet 100 (Pile layout) → `LEGIBLE_FOR_TRANSCRIPTION` — pile count and diameter visible; depth assumed from DBR
   - Sheet 101 (Pile cap layout) → `PARTIAL_RECONCILIATION_REQUIRED` — 54 vs 84 cap contradiction unresolved
   - Sheets 102, 103, 104, 106, 108, 110 → `LEGIBLE_FOR_TRANSCRIPTION` — bar marks visible but no official BBS
   - Sheets 105, 107 (Beam/slab layout) → `LEGIBLE_FOR_TRANSCRIPTION` — geometry legible but weighted-average assumptions used
   - Sheet 109 (OHT/tank) → `PARTIAL_RECONCILIATION_REQUIRED` — OHT dimensions assumed from IS 3370

3. **`01_Drawing_Registers/mep_sheet_register.csv`** — All 12 tower rows changed from `READY_FOR_TAKEOFF` to `LEGIBLE_FOR_TRANSCRIPTION`. Evidence notes clarify MEP quantities are outside current civil-structural takeoff scope.

4. **`01_Drawing_Registers/required_sheet_coverage.csv`** — Additional refinements:
   - Pile-cap details row → `PARTIAL_RECONCILIATION_REQUIRED` (54 vs 84 contradiction)
   - Water-tank details row → `PARTIAL_RECONCILIATION_REQUIRED` (OHT dimensions assumed)
   - Pile schedule row → evidence note updated: depth 18m assumed from DBR, not scheduled on drawing

5. **`01_Drawing_Registers/drawing_extraction_readiness_report.md`** — Fixed pile depth overclaim (line 42): depth 18.0m clarified as assumed from DBR range, not directly visible on drawing. Extraction claim (line 39): changed "extracted directly" to "legible; controlled transcription required."

6. **`00_Project_Control/scope_match_audit.csv`** — Corporate disclosure row (Rs 157.25 Cr, 36 months) annotated with SUPERSEDED note.

### Post-Correction Verification

Final scan confirmed:
- **0** active register rows contain `READY_FOR_TAKEOFF`
- **0** active assumption rows contain `HIGH_CONFIDENCE` (excluding audit trail references)
- **0** active duration fields validate 36 months or 15 months as current (all superseded/NOT_CALCULATED)
- Cost accuracy: `NOT_CALCULATED` ✓
- Quantity accuracy: `NOT_CALCULATED` ✓
- Dataset status: `DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION` ✓
- Drawing readiness: `PARTIAL - READY_FOR_CONTROLLED_TRANSCRIPTION` ✓

### Total Additional Files Modified in Register Follow-up
18. `01_Drawing_Registers/architectural_sheet_register.csv`
19. `01_Drawing_Registers/structural_sheet_register.csv`
20. `01_Drawing_Registers/mep_sheet_register.csv`
21. `00_Project_Control/scope_match_audit.csv`


