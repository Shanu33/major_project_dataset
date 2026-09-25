# Priority D — Civil Cross-Register Reconciliation Log

**Project**: OIL/RITES Duliajan BQ Workmen Housing Complex  
**Tender No.**: RITES/NERPO/OIL/BQ-HOUSING/25  
**Scope Unit**: One typical Stilt+6 BQ Workmen Housing residential tower  
**Target Folder**: `10_Controlled_Transcription/`  
**Reconciliation Stage**: Priority D — Civil Cross-Register Reconciliation Cleanup & Verification  
**Stage Status**: `PRIORITY_D_CIVIL_RECONCILIATION_PARTIAL_VERIFIED`  
**Dataset Readiness**: `DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`  

---

## 1. Scope

This document details the cross-register reconciliation and provenance cleanup between foundation, structural framing, architectural layouts, room geometries, finish schedules, and opening deduction records for one typical Stilt+6 BQ residential tower.

The objective of Priority D is to establish a rigorous, transparent geometric correlation across all transcribed registers without generating unvalidated material quantities, upgrading confidence labels, or applying synthetic assumptions.

### Mandatory Dataset Disclaimers:
- **No final material quantities were calculated** (no masonry $m^3$, concrete $m^3$, rebar $MT$, plaster $m^2$, flooring $m^2$, or paint $m^2$).
- **No costs were calculated** (`Cost accuracy: NOT_CALCULATED`).
- **No BOQ validation was performed** (`Quantity accuracy: NOT_CALCULATED`).
- **No labour or duration modelling was performed** (`Labour/Duration: BLOCKED`).
- **No synthetic masonry deduction ratios were used** (the legacy 23% external and 10% internal deduction ratios remain strictly excluded).
- **No 24-flat or tower multiplication was applied** (unit spatial dimensions remain per-flat/per-panel).
- **Dataset Readiness**: The project strictly remains **`DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`**.
- **The project must NOT be marked `READY_FOR_TAKEOFF`**.

---

## 2. Source Registers Reviewed

The following 10 controlled registers and logs were audited and cross-referenced:
1. `controlled_pile_register.csv` (11 rows, Substructure — 207 piles, 600mm dia; founding depth 18m not scheduled on drawing, assumed from DBR range)
2. `controlled_pile_cap_register.csv` (11 rows, Substructure — 84 vs 54 cap contradiction unresolved; 91 piles unallocated under strip caps)
3. `controlled_foundation_register.csv` — **`REGISTER_MISSING`** (Data maintained across pile & pile cap registers)
4. `controlled_column_wall_register.csv` (13 rows, Structural Framing — 16 columns C1-C3, 33 shear walls SW1-SW10 cross-sections and rebar directly visible on Sheet 104; member height is NOT scheduled on Sheet 104 and is `ARCHITECTURAL_SECTION_DERIVED` from Section A-A)
5. `controlled_beam_register.csv` (44 rows, Structural Framing — Plinth beams PB1-PB34, Typical floor beams B1-B34)
6. `controlled_slab_register.csv` (7 rows, Structural Superstructure — Suspended slabs S1-S2 125mm, Grade slabs GS1-GS2)
7. `controlled_stair_oht_register.csv` (7 rows, Structural / Misc — Stair flights visible on Sheet 110; OHT bottom slab 150mm directly scheduled on Sheet 109; OHT wall thickness is `NOT_VISIBLE_ON_SHEET_109` / `ASSUMPTION_REQUIRED` and wall rebar is `NOT_SCHEDULED`)
8. `controlled_opening_register.csv` (15 rows, Architectural — D1-D3, DW1-DW2, SD1-SD4, W1-W4, V1-V2)
9. `controlled_room_register.csv` (14 rows, Architectural — 10 typical unit spaces, 4 core/stilt spaces)
10. `controlled_finish_register.csv` (10 rows, Architectural — Specifications FIN-01 to FIN-10)
11. `controlled_masonry_deduction_register.csv` (15 rows, Architectural — Opening deduction basis; gross/net blank)
12. Audit Logs: `foundation_transcription_log.md`, `structural_frame_transcription_log.md`, `architectural_finishes_transcription_log.md`

---

## 3. Files Created and Verified

Six structured reconciliation matrices and indices are maintained in `10_Controlled_Transcription/`:

1. [`civil_reconciliation_index.csv`](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/10_Controlled_Transcription/civil_reconciliation_index.csv) — Master index of all controlled registers, row counts, and reconciliation statuses.
2. [`floor_scope_reconciliation.csv`](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/10_Controlled_Transcription/floor_scope_reconciliation.csv) — Floor-by-floor scope breakdown from Foundation to OHT level.
3. [`wall_takeoff_reconciliation_matrix.csv`](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/10_Controlled_Transcription/wall_takeoff_reconciliation_matrix.csv) — Wall zone classification, thickness, boundary constraints, and structural interruptions.
4. [`opening_deduction_reconciliation_matrix.csv`](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/10_Controlled_Transcription/opening_deduction_reconciliation_matrix.csv) — Linkage of opening schedule marks to wall types and deduction eligibility.
5. [`finish_area_reconciliation_matrix.csv`](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/10_Controlled_Transcription/finish_area_reconciliation_matrix.csv) — Traceability matrix linking room areas to floor, wall, and ceiling finishes.
6. [`structural_architecture_conflict_log.csv`](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/10_Controlled_Transcription/structural_architecture_conflict_log.csv) — Detailed record of 11 cross-discipline conflicts and missing schedules.
7. [`priority_d_reconciliation_log.md`](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/10_Controlled_Transcription/priority_d_reconciliation_log.md) — This master reconciliation summary document.

---

## 4. What Is Now Reconciled

Through this Priority D pass, the following inter-discipline linkages are verified:
1. **Vertical Storey & Structural Height Provenance**: Storey height ($3.05\text{ m}$ floor-to-floor) from Architectural Sections A-A and B-B is cross-mapped to structural framing. Column cross-sections and rebar are direct Sheet 104 observations, but vertical height is strictly classified as **`ARCHITECTURAL_SECTION_DERIVED`** (not scheduled on Sheet 104). Final column/wall concrete volume and steel cut-lengths remain blocked.
2. **Floor-by-Floor Hierarchy**: Scope established across 11 vertical levels: Foundation, Stilt Floor, 6 Typical Residential Floors (1st to 6th), Terrace Level, Stair Mumty / Headroom, and OHT level.
3. **Lift Core Structural Material Resolution**: The Lift Shaft enclosure is formally resolved as **Reinforced Concrete Shear Wall structure (SW9/SW10 / CW1, 250mm thick)** governed by Structural Sheet 103. Masonry takeoff for lift core is set to zero, eliminating potential double-counting.
4. **Opening Deduction Host Mapping**: All 15 opening marks are mapped to host wall thicknesses ($230\text{ mm}$ external perimeter vs $115\text{ mm}$ internal partitions) and geometric deduction areas ($W \times H$).
5. **Spatial-to-Finish Traceability**: Room categories from `controlled_room_register.csv` are mapped to finish specifications (`FIN-01` to `FIN-10`), establishing clear boundaries between vitrified tiles, granite, ceramic dado, Kota stone, and plaster/paint.
6. **OHT Scope Verification**: Directly visible bottom slab thickness ($150\text{ mm}$) and rebar on Sheet 109 are confirmed. OHT wall thickness is formally marked as `NOT_VISIBLE_ON_SHEET_109` / `ASSUMPTION_REQUIRED`, wall rebar as `NOT_SCHEDULED`, and OHT quantity takeoff as strictly `BLOCKED`. Generic IS 3370 or assumed wall thicknesses are excluded.

---

## 5. What Remains Blocked

The following items are identified as active blockers:
1. **Wall Length Assembly**: Net masonry wall lengths remain uncalculated because wall centerlines have not been segregated from column widths ($300\text{ mm}$) and shear wall panel lengths ($1200\text{ mm}$ to $2800\text{ mm}$).
2. **Variable Clear Wall Heights**: Varying beam depths ($450\text{ mm}$ for secondary beams, $600\text{ mm}$ for main beams) mean clear masonry height varies by bay ($2450\text{ mm}$ under $600\text{ mm}$ beams; $2600\text{ mm}$ under $450\text{ mm}$ beams; $2925\text{ mm}$ under slabs). A uniform wall height cannot be applied.
3. **Opening Counts**: Drawing Sheet `AR/TD/005` schedule omits opening counts per unit and per floor. Automatic multiplier calculation is blocked.
4. **Substructure Foundation Contradictions**:
   - Pile termination depth is unscheduled on Sheet 100 ($18.0\text{ m}$ is derived from DBR range).
   - Pile cap entity count mismatch ($54$ visible layout caps vs $84$ scheduled caps) and $91$ piles unallocated under strip caps.
5. **OHT Wall Details Missing**: Tank wall thickness and water-retaining reinforcement schedule are completely missing from Sheet 109. No OHT concrete volume or rebar weight is calculated.

---

## 6. Why Final Quantity Takeoff Is Still Not Allowed

Final quantity takeoff is prohibited because:
- Multiplying unit room dimensions or opening schedules across the tower without locked wall centerlines would reintroduce uncontrolled parametric errors.
- The absence of an engineer-issued Bar Bending Schedule (BBS) means rebar weights cannot be verified beyond code-based approximations.
- Calculating net wall area without deducting structural column/shear wall block-outs violates IS 1200 (Part III) masonry measurement principles.
- The substructure foundation volume remains ambiguous pending pile cap reconciliation.

---

## 7. What Evidence Is Required Before Quantity Calculation

To advance to deterministic quantity takeoff, the following evidence must be provided:
1. **Wall Centerline General Arrangement**: Dimensioned wall centerline plans deducting column and shear wall blocks.
2. **Bay-by-Bay Beam-Wall Interface Schedule**: Schedule correlating each masonry wall run to the soffit of its supporting/overhead beam.
3. **Official Opening Schedule with Counts**: Complete door/window schedule confirming counts per flat and per floor.
4. **Reconciled Foundation General Arrangement**: Numbered pile cap drawing resolving the 54 vs 84 cap contradiction and allocating all 207 piles.
5. **Approved Pile Borehole Schedule**: Engineer's approved pile termination depths.
6. **OHT Structural Details**: Section drawing showing tank wall thickness, top dome/slab, and reinforcement.

---

## 8. Recommended Priority E Task

**Recommended Next Step**: Once civil reconciliation cleanup is verified, the recommended progression is:
- **Priority E — Building Services (MEP) Controlled Transcription**:  
  Transcribe directly visible evidence from the 18 Building Services drawing sheets (`Tender_drawing_4_Sections_StructuralCommunity_MEP_pdf-2025-Aug-28-17-39-32.pdf`, Sheets `MEP/001` to `MEP/018`) covering plumbing, drainage, sanitary fixtures, electrical distribution, and fire fighting risers.
