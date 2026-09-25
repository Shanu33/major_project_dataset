# Estimation Readiness & Evidence Control Report
## OIL/RITES Duliajan Typical Stilt+6 BQ Residential Tower Pilot

- **Project Title**: Construction of Workman Housing Complex (BQ Area) on EPC Mode-II of Contract at OIL Duliajan, Assam
- **Executing Agency**: RITES Limited (Tender Cell-NERPO, Guwahati)
- **Client**: Oil India Limited (OIL), Duliajan, Assam
- **Tender Reference / CPP Tender ID**: `RITES/NERPO/OIL/BQ-HOUSING/25` / `2025_RITES_246752_1`
- **Awarded Contractor**: M/s Badri Rai & Company (Award Record Date: December 2025)
- **Official Contract Award Value**: ₹128.14 Crore (excluding GST)
- **Official Contract Scheduled Duration**: 24 Months (entire campus scope: 8 towers + 4 ancillary facilities + external development)
- **Target Modeling Entity**: Exactly **ONE Typical Stilt+6 BQ Residential Workmen Housing Tower** (1/8th of Macro BOQ Item 1.01)
- **Dataset Status**: `DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`
- **Model Training / Estimation Readiness**: `BLOCKED` (Requires foundation schedule resolution, BBS, and contractor cost/programme records)

---

## Executive Verdict & Audit Integrity Baseline

```text
====================================================================================================
PILOT ESTIMATION READINESS VERDICT: DETERMINISTIC ESTIMATION RESTRICTED TO DIRECT GEOMETRIC PARAMETERS
====================================================================================================
External BOQ Material Validation Coverage: 0.0% (Tender is EPC Mode-II Lump Sum; zero itemized BOQ)
Cost Accuracy:                             NOT CALCULATED (No official tower-specific priced BOQ exists)
Quantity Accuracy:                         NOT CALCULATED (No independent audited quantity bill available)
Macro Scope Consistency:                   PASS (Plinth Area: 3,419.38 sq.m, Units: 24, Storeys: Stilt+6)
Construction Labour Mandays:               NOT CALCULATED (Strictly blocked pending foundation schedule & BBS)
Single Tower Construction Duration:        NOT CALCULATED (Strictly blocked pending single-tower CPM schedule)
Zero-Mixing Protocol:                      ENFORCED (2020 tender NIT_CPI4685P21 strictly quarantined in 99_Unverified)
====================================================================================================
```

This report establishes the engineering evidence boundary for transitioning the OIL/RITES Duliajan BQ residential housing project into an evidence-controlled project-estimation pilot.

In strict adherence to evidence-control governance:
1. **Single Tower Isolation**: Only ONE typical residential tower is modeled (24 units, 3,419.38 sq.m plinth area). The remaining 7 towers, Guest House, Community Centre, Substation, external development, and campus infrastructure are quarantined.
2. **EPC Mode-II Integrity**: Because the tender is an EPC turnkey lump sum contract, **no official itemized construction bill of quantities (BOQ) exists in the public tender**. Preliminary claims of "100% BOQ validation" or "0% quantity error" are formally revoked. Material validation coverage is **0.0%**.
3. **Evidence Tiers Maintained**: Only directly visible drawing dimensions and scheduled counts are designated as `DIRECT / HIGH` and "Ready for Deterministic Estimation". All derived material quantities relying on unverified depths, member averages, synthetic deduction ratios, or parametric intensities are isolated in the "Estimated / Not Training-Ready" group.
4. **No Premature Scheduling or Costing**: Labour mandays and single-tower duration are locked as `NOT_CALCULATED` because foundation cap counts remain contradictory and no bar bending schedule (BBS) exists.

---

## 1. What Can Be Estimated Reliably Now?
### (Ready for Deterministic Estimation Group — 70 Evidenced Parameters)

The following parameters are supported by unambiguous, direct sheet observations from the official tender drawings and project control documents, requiring zero geometric extrapolation:

### 1.1 Building Boundary & Spatial Allocations
- **Tower Footprint Geometry**: Directly dimensioned as **30.08 m length × 16.08 m width** on Architectural Ground Plan ([AR/TD/006, p. 10](file:///home/shahnawaz/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf#page=10)) and Structural Plinth Plan ([STR/TD/105, p. 21](file:///home/shahnawaz/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/04_Architectural_Drawings/Tender_drawing_3_TypicalFloor_StructuralHousing_pdf-2025-Aug-28-17-39-16.pdf#page=21)), yielding an exact gross footprint of **483.60 sq.m**.
- **Allocated Plinth Area**: Directly scheduled in EPC Schedule ([BoQ_3, Item 1.01](file:///home/shahnawaz/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/02_Cost_BOQ_Makes/BoQ_3_Plumbing_Sanitary_pdf-2025-Aug-28-17-28-6.pdf#page=1)) as exactly 1/8th of 27,355.0 sq.m = **3,419.38 sq.m**. This matches drawing [AR/TD/001 (p. 4)](file:///home/shahnawaz/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf#page=4) area schedule: `(7 storeys * 483.60 sq.m) + 34.18 sq.m (Mumty) = 3,419.38 sq.m`.
- **Dwelling Unit Counts & Areas**: Architectural plans ([AR/TD/002-007](file:///home/shahnawaz/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf#page=5)) establish **4 units per floor** across 6 residential floors = **24 units** (Type-2BHK). Unit title blocks on [AR/TD/005 (p. 9)](file:///home/shahnawaz/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf#page=9) directly record **Carpet Area = 69.00 sq.m** and **Unit Plinth Area = 90.00 sq.m**.
- **Storey Profile & Architectural Heights**: Architectural elevations and Section A-A ([AR/TD/010-013, pp. 14-17](file:///home/shahnawaz/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf#page=14)) directly dimension:
  - Stilt Floor Clear Height: **3.00 m** (+0.00m to +3.00m)
  - Typical Floor-to-Floor Height: **3.05 m** (+3.00m to +21.30m)
  - Terrace Mumty Clear Height: **2.70 m** (+21.30m to +24.00m)
  - Overall Architectural Building Height: **24.00 m**

### 1.2 Substructure Elements Directly Evidenced
- **Bored Pile Count & Diameter**: Sheet [STR/TD/100 (p. 16)](file:///home/shahnawaz/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/04_Architectural_Drawings/Tender_drawing_3_TypicalFloor_StructuralHousing_pdf-2025-Aug-28-17-39-16.pdf#page=16) layout plan contains exactly **207 bored pile markers ('P')**. Pile diameter is directly scheduled on drawing callouts, Section A-A, and General Notes as **600 mm diameter**.
- **Bored Pile Longitudinal & Confining Reinforcement**: Sheet 100 typical elevation and Section A-A directly schedule **10-T20 vertical bars**, **T8 @ 125 mm c/c** seismic confining ties for the top 9.0 m, **T8 @ 150 mm c/c** ties for the lower zone, and **T16 @ 1500 mm c/c master rings**. Safe axial bearing capacity is directly stated in General Note 16 as **68 MT/pile**.

### 1.3 Superstructure Columns & Shear Walls Directly Evidenced
- **Vertical Framing Counts**: Sheets [STR/TD/103 & 104 (p. 20)](file:///home/shahnawaz/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/04_Architectural_Drawings/Tender_drawing_3_TypicalFloor_StructuralHousing_pdf-2025-Aug-28-17-39-16.pdf#page=20) directly tabulate **16 framed columns** and **33 shear wall legs** per floor.
- **Column Cross-Sections & Scheduled Main Steel**:
  - **C1 (4 nos/floor)**: 1200 mm x 350 mm; main rebar **14-T32 + 8-T25** (22 bars total).
  - **C2 (8 nos/floor)**: 1200 mm x 300 mm; main rebar **22-T25** (22 bars total).
  - **C3 (4 nos/floor)**: 1200 mm x 300 mm; main rebar **22-T20** (22 bars total).
- **Shear Wall Cross-Sections & Scheduled Main Steel**:
  - **SW1 (12 nos/floor)**: 1260 mm x 230 mm; main rebar **12-T12 + 4-T12** (16-T12 total).
  - **SW2 (4 nos/floor)**: 1500 mm x 230 mm; main rebar **12-T16 + 6-T12** (18 bars total).
  - **SW3 (4 nos/floor)**: 1380 mm x 230 mm; main rebar **12-T16 + 6-T12** (18 bars total).
  - **SW4 (4 nos/floor)**: 2925 mm x 230 mm; main rebar **24-T12 + 12-T12** (36-T12 total).
  - **SW5 (4 nos/floor)**: 5030 mm x 230 mm; main rebar **32-T12 + 24-T12 + 14-T12** (70-T12 total).
  - **Core Walls SW6-SW10 (1 core = 5 segments/floor)**: Combined elevator/stair shaft walls, thickness **230 mm**, lengths 2510 mm, 2880 mm, 3110 mm, 2780 mm, 2610 mm, with scheduled boundary reinforcement (28 to 38 bars T12).

### 1.4 Scheduled Openings & Directly Scheduled Dimensions
- **Flush Door Assemblies (216 units total)**: Sheet [AR/TD/005 (p. 9)](file:///home/shahnawaz/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf#page=9) Schedule of Openings:
  - **D1 (48 nos)**: 800 mm x 2100 mm (Toilet flush door with WPC frame/shutter)
  - **D2 (96 nos)**: 1000 mm x 2100 mm (Bedroom/internal flush door with teak wood frame)
  - **D3 (72 nos)**: 1050 mm x 2100 mm (Main entrance door with wire mesh double shutter)
- **Window & Ventilator Assemblies (168 units total)**: Sheet [AR/TD/005 (p. 9)](file:///home/shahnawaz/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf#page=9) Schedule of Openings:
  - **W1 (48 nos)**: 1200 mm x 1200 mm (Sill 900 mm, Lintel 2100 mm)
  - **W2 (24 nos)**: 1000 mm x 1225 mm (Sill 1225 mm, Lintel 2450 mm)
  - **W3 (24 nos)**: 2300 mm x 1100 mm (Sill 1000 mm, Lintel 2100 mm)
  - **W4 (24 nos)**: 1200 mm x 1200 mm (Sill 900 mm, Lintel 2100 mm)
  - **V1 (24 nos)**: 515 mm x 875 mm (Sill 1225 mm, Lintel 2100 mm)
  - **V2 (24 nos)**: 615 mm x 875 mm (Sill 1225 mm, Lintel 2100 mm)
- **Directly Scheduled Slabs & Stairs**:
  - Two-way floor slabs S1 & S2: **125 mm thickness** scheduled on Sheet [STR/TD/107 (p. 23)](file:///home/shahnawaz/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/04_Architectural_Drawings/Tender_drawing_3_TypicalFloor_StructuralHousing_pdf-2025-Aug-28-17-39-16.pdf#page=23).
  - Doglegged staircase flights: **Flight width 1,500 mm, Riser 150 mm, Tread 300 mm, Waist slab 150 mm** directly dimensioned on Sheet [STR/TD/110 (p. 26)](file:///home/shahnawaz/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/04_Architectural_Drawings/Tender_drawing_3_TypicalFloor_StructuralHousing_pdf-2025-Aug-28-17-39-16.pdf#page=26).
- **Direct Material & Design Criteria**: RCC Grade **M30** (characteristic cube compressive strength 30 N/sq.mm at 28 days), Rebar Grade **Fe 550D / Fe 500D**, Lean Concrete **M10 (1:5:10)**, **Seismic Zone V (Z=0.36)**, and **Basic Wind Speed 50 m/s** per DBR Section 3 and drawing notes.

---

## 2. What Cannot Be Estimated Reliably Yet?
### (Estimated / Not Training-Ready Group — 45 Blocked Parameters)

All material volume aggregations, tonnages, cost allocations, and timelines fall into this group because they depend on unevidenced engineering assumptions, unreconciled drawings, or missing shop records:

| Trade Category | Parameter Description | Current Adopted Value | Confidence Tier | Why It Cannot Be Estimated Reliably |
| :--- | :--- | :--- | :--- | :--- |
| **Piling** | Bored RCC Pile Depth | 18.0 m | `ESTIMATED` | Not tabulated on Sheet 100. Relies on DBR recommended range (15m to 20m, ASM-001). Divergence changes concrete volume by up to ±25%. |
| **Piling** | Piles Concrete Volume | 1,053.49 m3 | `ESTIMATED` | 207 * (pi/4 * 0.6^2) * 18m. Directly inherits pile depth unreliability; cut-off levels unscheduled. |
| **Piling** | Piles Reinforcement Steel | 99.24 MT | `ESTIMATED` | Uses parametric intensity (94.2 kg/m3) and assumed 18m cage length. No official BBS issued. |
| **Foundation** | Pile Cap Count & Boundaries | 54 vs 84 caps | `UNRESOLVED_CONTRADICTION` | CRITICAL CONTRADICTION: Sheet 101 layout identifies 54 cap entities (208.38 m3), but preliminary summary claims 84 caps (185.00 m3). 91 piles remain unallocated under strip caps. |
| **Foundation** | Pile Cap Thickness | 0.75m vs 1.0m | `ASSUMPTION_REQUIRED` | Historical model assumed 1.0m (ASM-003); Sheet 101 marks "750 THK PC". Tabulated schedule per cap type is missing. |
| **Foundation** | Pile Cap Concrete Volume | 185.00 to 208.38 m3 | `UNRESOLVED_CONTRADICTION` | Range discrepancy of 23.38 m3 cannot be reconciled without approved foundation GA drawing. |
| **Foundation** | Pile Cap Rebar Steel | 20.35 MT | `ASSUMPTION_REQUIRED` | Arbitrary 110 kg/m3 intensity applied to unreconciled cap volume. Official BBS missing. |
| **Substructure** | PCC Lean Concrete | 18.00 m3 | `ESTIMATED` | Assumed 75mm leveling layer under caps (ASM-003). Thickness not scheduled on foundation sheets. |
| **Substructure** | Plinth Beams (PB1-PB34) Conc. | 47.61 m3 | `ESTIMATED` | Gross grid centerline (403.5m) includes column nodes; weighted section 0.118 m2 used without bay-by-bay clear spans. |
| **Substructure** | Plinth Beams Steel | 6.43 MT | `ESTIMATED` | Assumed 135 kg/m3 intensity (ASM-005). Official BBS missing. |
| **Substructure** | Stilt Grade Slab Concrete | 60.45 m3 | `ASSUMPTION_REQUIRED` | Uniform 125mm slab on 438 sq.m net area is 54.75 m3; 60.45 m3 requires an unmeasured 5.70 m3 perimeter edge thickening. |
| **Framing** | Columns C1-C3 Concrete | 126.00 m3 | `MEDIUM` | Clear height 3.0m assumed repeated across 7 levels; member height not on Sheet 104; beam-column joint deduplication unexecuted. |
| **Framing** | Columns C1-C3 Steel | 52.41 MT | `MEDIUM` | Bar counts scheduled, but cut lengths assume 3.0m height and 50d lap rule. Official BBS missing. |
| **Framing** | Shear Walls SW1-SW10 Conc. | 349.45 m3 | `MEDIUM` | Clear height 3.0m assumed repeated across 7 levels; joint intersections with slabs/beams not deduplicated. |
| **Framing** | Shear Walls SW1-SW10 Steel | 30.12 MT | `MEDIUM` | Boundary zone rebar scheduled, but web mesh and link cut lengths assume 3.0m height. Official BBS missing. |
| **Framing** | Floor Beams B1-B34 (F1-F6) Conc.| 289.80 m3 | `ESTIMATED` | Relies on 403.5m gross centerline and 0.1197 m2 weighted average section across 6 floors without column node deductions. |
| **Framing** | Terrace Beams TB1-TB34 Conc. | 48.30 m3 | `ESTIMATED` | Relies on 403.5m gross centerline and 0.1197 m2 weighted average section. |
| **Framing** | Floor & Terrace Beams Steel | 47.33 MT | `ESTIMATED` | Assumed 140 kg/m3 intensity across 7 levels (ASM-005). Official BBS missing. |
| **Framing** | Suspended Slabs (F1-F6) Conc. | 331.47 m3 | `ESTIMATED` | Reconciled 424.96 sq.m net slab, but relies on 130mm assumed weighted thickness; beam web ribs (230mm) not deducted. |
| **Framing** | Terrace Roof Slab Conc. | 55.24 m3 | `ESTIMATED` | Reconciled 424.96 sq.m net slab with 130mm assumed thickness. Panel-by-panel structural schedule missing. |
| **Framing** | Suspended Slabs Steel | 36.69 MT | `ESTIMATED` | Assumed 89.17 kg/m3 intensity (ASM-006). Official panel BBS missing. |
| **Framing** | Balconies & Chajjas Concrete | 20.02 m3 | `ESTIMATED` | Estimated from 182.0 sq.m projected area without individual piece schedule. |
| **Framing** | Rooftop OHT Concrete & Steel | 16.50 m3 / 1.98 MT | `ASSUMPTION_REQUIRED` | Tank wall thickness NOT visible on Sheet 109; wall rebar NOT scheduled; relies on assumed IS 3370 code rules (ASM-010). |
| **Masonry** | External 230mm Brickwork | 216.80 m3 | `ESTIMATED` | Relies on synthetic 23% opening deduction ratio (ASM-007); column block-outs not subtracted from perimeter run. |
| **Masonry** | Internal 115mm Brickwork | 406.85 m3 | `ESTIMATED` | Relies on synthetic 10% opening deduction ratio (ASM-008); bay-by-bay beam drops not accounted for. |
| **Masonry** | Total Brick Masonry Volume | 623.65 m3 | `ESTIMATED` | Synthetic ratios overestimate brickwork by 15-20% by double-counting concrete columns and beam zones. |
| **Finishes** | Total Cement Plaster Area | 14,850.00 sq.m | `ESTIMATED` | Gross surface area ratio (ASM-009). 4-face exterior elevation envelope and beam soffit drop schedules missing. |
| **Finishes** | Total Flooring & Skirting Area| 2,700.00 sq.m | `ESTIMATED` | Carpet area approximations. Corridor bay lengths and floor-wise repetition controls missing. |
| **Total Civil** | Total RCC M30 Concrete Volume | 2,617.55 m3 | `ESTIMATED` | Drawing-based takeoff estimate (0.766 m3/sq.m plinth). **0% BOQ validation coverage.** |
| **Total Civil** | Total Reinforcement Steel | 300.85 MT | `ESTIMATED` | Drawing-based takeoff estimate (87.98 kg/sq.m plinth). **0% BOQ validation coverage; no shop BBS.** |
| **Commercial** | Single Tower Cost Benchmark | ₹16.0175 Crore | `ESTIMATED` | Rough project-level 1/8th pro-rata division of ₹128.14 Cr contract award. **Cost accuracy: NOT CALCULATED.** |
| **Schedule** | Single Tower Construction Duration| NOT_CALCULATED | `ASSUMPTION_REQUIRED` | Overall contract is 24 months for 8 towers + campus infrastructure. Single-tower CPM schedule uncalculated. |
| **Productivity** | Construction Labour Mandays | NOT_CALCULATED | `ASSUMPTION_REQUIRED` | Strictly blocked pending foundation schedule resolution, BBS, and contractor site productivity logs. |

---

## 3. Which Inputs Are Direct versus Assumed?
### (Comparative Provenance Matrix)

To eliminate any ambiguity regarding input provenance, the table below maps each core engineering discipline between direct drawing evidence and unevidenced assumptions:

| Discipline / Domain | DIRECT DRAWING EVIDENCE (HIGH) | ASSUMED / INFERRED INPUTS (ESTIMATED) |
| :--- | :--- | :--- |
| **1. Substructure Piling** | • Pile count: Exactly 207 piles<br>• Pile diameter: 600 mm<br>• Longitudinal rebar: 10-T20 bars<br>• Ties: T8@125 (top 9m), T8@150 (mid)<br>• Master ring: T16@1500 c/c | • Pile depth: 18.0m (DBR range 15-20m)<br>• Pile cage length: 18.0m full depth<br>• Pile concrete: 1,053.49 m3<br>• Pile steel: 99.24 MT (94.2 kg/m3)<br>• Cut-off elevation: Unscheduled |
| **2. Foundation Caps** | • Cap concrete grade: M30<br>• Cap rebar grade: Fe 550D<br>• Clear cover: 75 mm<br>• Bottom rebar: T25@100 c/c<br>• Top rebar: T25@150 c/c | • Cap count: 54 layout vs 84 summary<br>• Cap thickness: 750mm vs 1,000mm<br>• Cap concrete: 185.00 to 208.38 m3<br>• Cap steel: 20.35 MT (110 kg/m3)<br>• 91 piles under strip caps unallocated |
| **3. Columns & Shear Walls** | • Column count: 16 per floor<br>• Shear wall count: 33 legs per floor<br>• Cross-sections: C1-C3, SW1-SW10 dims<br>• Bar marks: C1-C3, SW1-SW10 bar counts<br>• Concrete grade: M30; Rebar: Fe 500D | • Member clear height: 3.0m assumed (derived from architectural section)<br>• Rebar cut length: 50d lap rule used<br>• Total column/wall concrete: 475.45 m3<br>• Total column/wall steel: 82.53 MT |
| **4. Framing Beams** | • Framing layouts: PB, B, TB grids<br>• Beam section callouts: 230x450-600mm<br>• Beam concrete grade: M30 | • Beam centerline: 403.5m gross run<br>• Beam cross-section: 0.1197 m2 average<br>• Beam concrete: 385.71 m3<br>• Beam steel: 53.76 MT (135-140 kg/m3) |
| **5. Slabs & Stairs** | • Slab thickness: S1/S2 = 125 mm<br>• Slab rebar spacing: T8/T10@125/150 c/c<br>• Stair flight: 1500w / 150r / 300t<br>• Stair waist slab: 150 mm | • Net slab area: 424.96 sq.m net<br>• Weighted slab thickness: 130 mm<br>• Slab concrete: 386.71 m3<br>• Slab steel: 36.69 MT (89.17 kg/m3) |
| **6. Architectural Enclosure** | • Door sizes: D1, D2, D3 scheduled<br>• Window sizes: W1-W4, V1-V2 scheduled<br>• Unit plans & room layouts | • External masonry: 23% deduction ratio<br>• Internal masonry: 10% deduction ratio<br>• Masonry volume: 623.65 m3<br>• Plaster surface: 14,850 sq.m (ratio)<br>• Flooring area: 2,700 sq.m (ratio) |
| **7. Commercial & Schedule** | • Contract award: ₹128.14 Cr (Badri Rai)<br>• Contract duration: 24 Months<br>• Scope allocation: 1/8th of Item 1.01 | • Tower pro-rata cost: ₹16.0175 Cr<br>• Single tower cost: NOT VALIDATED<br>• Single tower duration: NOT CALCULATED<br>• Labour mandays: NOT CALCULATED |

---

## 4. Why Labour, Duration, and Cost Validation Remain Blocked

The pilot strictly refuses to generate ungrounded synthetic estimates for labour, project schedule, or cost accuracy. Four structural blockers govern this restriction:

### 4.1 Unresolved Foundation Contradiction
- **The Physical Conflict**: Sheet [STR/TD/101](file:///home/shahnawaz/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/04_Architectural_Drawings/Tender_drawing_3_TypicalFloor_StructuralHousing_pdf-2025-Aug-28-17-39-16.pdf#page=17) layout plan delineates 54 combined and strip pile cap entities totaling 208.38 m3. In contrast, the preliminary takeoff summary tabulated 84 discrete caps totaling 185.00 m3. Crucially, discrete caps (PC-1 to PC-4) account for only 116 piles; the remaining 91 piles fall under continuous strip caps along shear wall lines, where cap boundaries and pile counts are entirely unreconciled.
- **Impact on Duration & Labour**: Foundation construction sits on the initial critical path. An unreconciled variance of 23.38 m3 of concrete, combined with indeterminate excavation pit boundaries, variable shuttering contact areas, and unallocated pile heads, prevents calculating foundation excavation, rebar tying, and concrete pour cycle times. Generating a CPM schedule on an unresolved foundation produces a fictional critical path.

### 4.2 Complete Absence of Bar Bending Schedules (BBS)
- **The Engineering Gap**: The local tender repository contains pre-tender structural design sheets, but **zero contractor bar bending schedules**. Rebar quantities currently stand at 300.85 MT, derived entirely from parametric intensities (89.17 kg/m3 for slabs, 140 kg/m3 for beams, 94.2 kg/m3 for piles).
- **Impact on Labour**: In reinforced concrete construction, steel reinforcement fixing represents 35% to 45% of structural labour mandays. Under IS 2502 and IS 13920 (Seismic Zone V ductile detailing), labour productivity depends directly on the number of bar cuts, the complexity of 135-degree seismic hooks, mechanical couplers versus lap splices, and column cage prefabrication. Applying arbitrary gang productivities to crude parametric tonnages produces errors exceeding ±30% in bar bender mandays.

### 4.3 Monolithic Beam-Slab-Column Joint Duplication
- **The Geometry Gap**: Current beam concrete (385.71 m3) is derived from gross grid run lengths (403.5 m per floor), which include the 49 vertical column and shear wall nodes. Similarly, suspended slab concrete (386.71 m3) applies a uniform 130mm thickness across 424.96 sq.m without deducting the 230mm beam web ribs that frame into the slab monolithically.
- **Impact on Cycle Times**: Floor cycle times depend on exact formwork contact area (shuttering area) and pour volume. Double-counting concrete at joints and neglecting beam soffit drops prevents assembling realistic floor pour schedules, table formwork cycling, or concrete pump placement rates.

### 4.4 EPC Turnkey Mode-II Contract Structure (Zero Itemized Cost Ground Truth)
- **The Commercial Reality**: The project was awarded under EPC Mode-II Lump-Sum Component Basis. The client (OIL) and project manager (RITES) tendered the project on a lump sum area basis (Item 1.01: 27,355 sq.m @ lumpsum rate). The tender contains **no bill of quantities with itemized rates for concrete, steel, formwork, or finishes**.
- **Why Cost Accuracy = NOT CALCULATED**: Without an engineer's approved priced BOQ or contractor work package breakdown, there is no external cost baseline against which to calculate variance or accuracy. Dividing the ₹128.14 Crore contract award by 8 towers to produce ₹16.0175 Crore is strictly an arithmetic pro-rata benchmark; it does not account for contractor site overheads, plant mobilization, margin, or common infrastructure, and cannot be claimed as a validated single-tower cost.

---

## 5. What Is the Next Highest-Value Document to Obtain?

To systematically unblock this pilot and achieve deterministic takeoff, duration, and cost validation, the next highest-value document to acquire is:

### Top Strategic Target:
> ### **1. Approved Contractor Bar Bending Schedule (BBS) & Structural Shop Drawings**
> **Document Origin**: M/s Badri Rai & Company (Approved Structural Fabricator / RITES Supervising Engineer)  
> **Direct Yield**:
> - Replaces **300.85 MT** of parametric steel estimates with exact cut lengths, hook deductions, and bar weights.
> - Unblocks **rebar fixing labour mandays** (the single largest manual labour trade).
> - Eliminates the primary blocker preventing automated structural machine learning models from training on real rebar geometry.

### Immediate Secondary Target:
> ### **2. Tabulated Foundation Pile & Pile Cap General Arrangement Working Drawing**
> **Document Origin**: EPC Design Consultant / RITES NERPO Guwahati  
> **Direct Yield**:
> - Reconciles the **54 vs 84 pile cap contradiction**, establishing definitive cap depths and boundary coordinates for the 91 piles under strip caps.
> - Establishes confirmed **pile termination depths** from actual borehole drilling logs, replacing the 18m DBR assumption.
> - Unblocks **substructure concrete (1,346.55 m3)** and foundation critical-path duration modeling.

### Tertiary Commercial Target:
> ### **3. Approved EPC Contract Work Package Cost Breakdown (Typical Tower Item 1.01)**
> **Document Origin**: Oil India Limited / RITES Tender Cell / Badri Rai & Co.  
> **Direct Yield**:
> - Establishes official trade-wise cost ground truth, unblocking **Cost Accuracy** from `NOT_CALCULATED` to audited percentage validation.

---

## 6. Deliverables Index & Next Phase Architecture

All outputs generated in this estimation readiness phase are isolated in `11_Estimation_Readiness/` and leave all original source files strictly untouched:

1. **`11_Estimation_Readiness/estimation_input_master.csv`**:
   - Machine-readable master parameter register containing **115 total parameters**.
   - **70 parameters** in `READY_FOR_DETERMINISTIC_ESTIMATION` (Confidence: `DIRECT / HIGH`; validation: `VERIFIED_DIRECT_DRAWING_EVIDENCE`).
   - **45 parameters** in `ESTIMATED_NOT_TRAINING_READY` (Confidence: `ESTIMATED`, `MEDIUM`, `ASSUMPTION_REQUIRED`, `UNRESOLVED_CONTRADICTION`).
   - Full provenance tracking: every single parameter retains its source document, sheet ID, PDF page number, extraction method, formula/derivation, assumption ID, validation status, and blocking issue.
2. **`11_Estimation_Readiness/missing_evidence_request_register.csv`**:
   - Formally structured RFI register listing **8 critical evidence requests** (`REQ-001` to `REQ-008`) prioritized by blocker severity, detailing target drawing numbers, issuing authorities, and technical unblocking criteria.
3. **`11_Estimation_Readiness/estimation_readiness_report.md`**:
   - This comprehensive governance and technical audit report.

```text
====================================================================================================
FINAL GOVERNANCE DECLARATION:
The OIL/RITES Duliajan Typical BQ Residential Tower Pilot is strictly bounded, 
evidenced at the direct drawing parameter level, and properly quarantined against premature 
labour, duration, or cost modeling until contractor post-award engineering records are recovered.
====================================================================================================
```
