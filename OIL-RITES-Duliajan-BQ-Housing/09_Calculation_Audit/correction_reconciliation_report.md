# Calculation Audit Correction & Reconciliation Report

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
