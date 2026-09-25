# Final Project Calculation Audit & Integrity Report

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
| **AUD-007** | Grade Slab Area & Thickening | Claimed 483.60 m2 gross x 0.125m = 60.45 m3 (originally HIGH confidence, now ESTIMATED) | Gross footprint is 483.60 m2; net slab area after core deductions is 438.00 m2 (54.75 m3). 60.45 m3 required an unmeasured 5.70 m3 edge thickening. | Uniform slab = 54.75 m3; edge thickening (5.70 m3) marked ASSUMPTION_REQUIRED. | `DOWNGRADED_TO_ASSUMPTION_REQUIRED` |
| **AUD-008** | Suspended Slab Area & Thickness | Claimed 428 m2 / 125mm (originally HIGH confidence, now ESTIMATED) | Exact net slab after deducting measured core shafts is 424.96 m2 (428 m2 was rounded). Thickness 130mm is assumed weighted average (S1 125mm, S2 150mm). | Reconciled to 424.96 m2; thickness 130mm marked assumed weighted average; downgraded to ESTIMATED. | `DOWNGRADED_TO_ESTIMATED` |
| **AUD-009** | Total Concrete Volume Split | Total concrete claimed inconsistently as 2617.55 vs 2635.55 m3 | 2,617.55 m3 is RCC M30 only; 18.00 m3 is PCC M10 lean concrete. Total combined concrete is 2,635.55 m3. | Explicitly separated RCC M30 (2,617.55 m3) and PCC M10 (18.00 m3) across all files. | `CORRECTED` |
| **AUD-010** | Reinforcement BBS Claims | Rebar claimed (originally HIGH confidence) (300.85 MT) | No bar bending schedule exists for piles, caps, beams, or slabs. Generic kg/m3 intensities were used for beams (140), slabs (90), piles (94.2), caps (110). | All rebar downgraded: Columns/walls/stairs to MEDIUM (bar counts scheduled, 50d lap rule used); Piles/caps/beams/slabs to ESTIMATED / ASSUMPTION_REQUIRED. | `DOWNGRADED` |

---

## 4. Audit Classifications: What is Verified, Estimated, Assumption-Based, and Not Validated

### 4.1 What is Verified (Direct Drawing Evidence — 10 Parameters Only)
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
5. **Single Tower Construction Cost**: Not validated against contract. Cost accuracy: NOT CALCULATED. No cost accuracy percentage is reported.

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
