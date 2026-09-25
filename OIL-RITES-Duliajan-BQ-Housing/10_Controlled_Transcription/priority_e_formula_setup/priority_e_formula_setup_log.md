# Priority E — Controlled Quantity Formula Setup Log

**Project**: OIL/RITES Duliajan BQ Workmen Housing Complex  
**Tender No.**: RITES/NERPO/OIL/BQ-HOUSING/25  
**Scope Unit**: One typical Stilt+6 BQ Workmen Housing residential tower  
**Target Folder**: `10_Controlled_Transcription/priority_e_formula_setup/`  
**Stage**: Priority E — Controlled Quantity Formula Setup  
**Status**: `PRIORITY_E_FORMULA_SETUP_COMPLETE_INPUTS_BLOCKED`  
**Dataset Readiness**: `DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`  

---

## 1. Scope

This log documents the establishment of a controlled, deterministic quantity takeoff formula layer for the typical Stilt+6 residential housing tower.

The objective of Priority E is to define the mathematical and geometric logic for calculating civil, structural, architectural, and finishes quantities, mapping every input parameter to verified drawing registers while establishing explicit blocking gates where source evidence is incomplete or unverified.

### Mandatory Dataset Disclaimers:
- **No final material quantities were calculated** ($0.0\text{ m}^3$ concrete, $0.0\text{ m}^3$ masonry, $0.0\text{ MT}$ steel rebar, $0.0\text{ m}^2$ plaster/paint/flooring).
- **No costs were calculated** (`Cost accuracy: NOT_CALCULATED`).
- **No BOQ validation was performed** (`Quantity accuracy: NOT_CALCULATED`).
- **No labour or duration modelling was performed** (`Labour/Duration: BLOCKED`).
- **No synthetic deduction percentages were used** (the legacy 23% external and 10% internal deduction ratios remain strictly excluded).
- **No 24-flat or tower multiplication was applied** (formulas are mapped parametrically to verified unit records; global multipliers are not executed).
- **OHT wall remains blocked** (wall thickness is `NOT_VISIBLE_ON_SHEET_109` / `ASSUMPTION_REQUIRED`, wall rebar is `NOT_SCHEDULED`, zero quantity calculated).
- **Reinforcement remains blocked without BBS/cut-length/lap evidence** (steel tonnage cannot be calculated from bar schedules without cut-length schedules).
- **Dataset Readiness**: The project strictly remains **`DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`**.
- **The project must NOT be marked `READY_FOR_TAKEOFF`**.

---

## 2. Source Files Reviewed

The formula definitions and dependency maps were constructed after reviewing 20 controlled transcription and reconciliation files:
1. `civil_reconciliation_index.csv`
2. `floor_scope_reconciliation.csv`
3. `wall_takeoff_reconciliation_matrix.csv`
4. `opening_deduction_reconciliation_matrix.csv`
5. `finish_area_reconciliation_matrix.csv`
6. `structural_architecture_conflict_log.csv`
7. `priority_d_reconciliation_log.md`
8. `controlled_opening_register.csv` (15 scheduled opening marks)
9. `controlled_room_register.csv` (14 room/core spaces)
10. `controlled_finish_register.csv` (10 finish specifications FIN-01 to FIN-10)
11. `controlled_masonry_deduction_register.csv` (15 opening deduction geometries)
12. `controlled_column_wall_register.csv` (13 column and shear wall cross-sections)
13. `controlled_beam_register.csv` (44 plinth and typical floor beam schedules)
14. `controlled_slab_register.csv` (7 suspended, grade, and roof slab schedules)
15. `controlled_stair_oht_register.csv` (7 staircase and OHT records; OHT base 150mm visible, wall thickness missing)
16. `controlled_pile_register.csv` (11 pile records; 207 piles 600mm dia, 18m assumed)
17. `controlled_pile_cap_register.csv` (11 cap records; 54 vs 84 cap contradiction)
18. `foundation_transcription_log.md`
19. `structural_frame_transcription_log.md`
20. `architectural_finishes_transcription_log.md`

---

## 3. Formula Files Created

Nine structured formula and dependency files were created in `10_Controlled_Transcription/priority_e_formula_setup/`:

1. [`quantity_formula_master_index.csv`](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/10_Controlled_Transcription/priority_e_formula_setup/quantity_formula_master_index.csv) — Master index of 18 quantity formula groups across all civil and architectural trades.
2. [`masonry_quantity_formula_map.csv`](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/10_Controlled_Transcription/priority_e_formula_setup/masonry_quantity_formula_map.csv) — 14 wall zone formulas defining gross area, opening deduction, net area, and volume logic.
3. [`concrete_quantity_formula_map.csv`](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/10_Controlled_Transcription/priority_e_formula_setup/concrete_quantity_formula_map.csv) — 16 structural concrete and shuttering contact area formulas.
4. [`reinforcement_quantity_formula_map.csv`](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/10_Controlled_Transcription/priority_e_formula_setup/reinforcement_quantity_formula_map.csv) — 15 schedule-based rebar formulas incorporating unit weight ($d^2/162.2$) and lap/hook requirements.
5. [`finish_quantity_formula_map.csv`](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/10_Controlled_Transcription/priority_e_formula_setup/finish_quantity_formula_map.csv) — 16 finish trade formulas (flooring, skirting, wall dado, false ceiling, internal/external plaster and paint).
6. [`opening_quantity_formula_map.csv`](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/10_Controlled_Transcription/priority_e_formula_setup/opening_quantity_formula_map.csv) — 15 opening dimension, area, and tower count formula definitions.
7. [`foundation_quantity_formula_map.csv`](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/10_Controlled_Transcription/priority_e_formula_setup/foundation_quantity_formula_map.csv) — 8 substructure foundation formulas for piles, pile caps, and tie beams.
8. [`formula_input_dependency_register.csv`](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/10_Controlled_Transcription/priority_e_formula_setup/formula_input_dependency_register.csv) — 17 critical input parameters tracked from source sheets with blocking reasons and required unblocking evidence.
9. [`blocked_formula_reason_register.csv`](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/10_Controlled_Transcription/priority_e_formula_setup/blocked_formula_reason_register.csv) — 12 trade-level risk analyses explaining failure modes if formulas were executed prematurely.

---

## 4. Formula Groups Defined

The master index establishes 18 discrete quantity formula groups:
- `GRP-MAS`: Masonry brickwork volume ($m^3$)
- `GRP-PLAS-INT`: Internal cement plaster area ($m^2$)
- `GRP-PLAS-EXT`: External waterproof plaster area ($m^2$)
- `GRP-PNT-INT`: Internal acrylic emulsion / OBD paint area ($m^2$)
- `GRP-PNT-EXT`: External weather-coat acrylic paint area ($m^2$)
- `GRP-FLR`: Floor finishes (vitrified, ceramic, granite, Kota, paver block) ($m^2$)
- `GRP-SKRT`: Skirting along wall perimeters ($m$)
- `GRP-OPN-DED`: Door, window, and ventilator opening deductions ($m^2$)
- `GRP-CONC-COL-SW`: Reinforced concrete in columns and shear walls ($m^3$)
- `GRP-CONC-BM`: Reinforced concrete in framing beams ($m^3$)
- `GRP-CONC-SLAB`: Reinforced concrete in floor, roof, and grade slabs ($m^3$)
- `GRP-CONC-STR`: Reinforced concrete in staircase flights, steps, and landings ($m^3$)
- `GRP-CONC-OHT-BASE`: Reinforced concrete in water tank bottom slab ($m^3$)
- `GRP-CONC-OHT-WALL`: Reinforced concrete in water tank side walls ($m^3$, **`BLOCKED`**)
- `GRP-FND-PILE`: Bored cast-in-situ concrete piles ($m^3$ / $m$)
- `GRP-FND-CAP`: Reinforced concrete in pile caps ($m^3$)
- `GRP-REBAR`: Reinforcing steel tonnage per trade ($MT$, **`BLOCKED`**)
- `GRP-SHTR`: Formwork and shuttering contact surface areas ($m^2$)

All 18 formula groups are set to `ready_for_execution = NO` and `calculation_status = FORMULA_DEFINED_INPUTS_BLOCKED`.

---

## 5. Inputs Currently Available (Direct Drawing Facts)

The following parameters are controlled and available for formula execution:
1. **Opening Geometry**: Width, height, sill, and lintel for all 15 scheduled marks (`D1`-`D3`, `DW1`-`DW2`, `SD1`-`SD4`, `W1`-`W4`, `V1`-`V2`).
2. **Room Clear Dimensions**: Clear length, clear width, floor area, and perimeter for 10 typical flat rooms and stilt ELV room.
3. **Finish Specifications**: Material specifications, thicknesses, and trades (`FIN-01` to `FIN-10`).
4. **Column & Shear Wall Cross-Sections**: Dimensions for columns ($C1\text{ }1200 \times 350$, $C2\text{ }1200 \times 300$, $C3\text{ }1200 \times 300$) and shear walls ($SW1\text{–}SW10\text{ }230\text{ mm}$ thick) with longitudinal bar schedules.
5. **Beam Framing Cross-Sections**: Web width and total depth for plinth beams `PB1`–`PB34` and floor beams `B1`–`B34` ($230 \times 450\text{ mm}$ and $230 \times 600\text{ mm}$).
6. **Slab Thickness**: Suspended slabs ($125\text{ mm}$), grade slabs ($125\text{ mm}$), and mumty slab ($125\text{ mm}$).
7. **Staircase Geometry**: Flight width ($1500\text{ mm}$), riser ($150\text{ mm}$), tread ($300\text{ mm}$), and waist slab ($150\text{ mm}$).
8. **OHT Bottom Slab Thickness**: Directly visible on Sheet 109 as $150\text{ mm}$ with scheduled bottom and top rebar.
9. **Pile Layout**: 207 bored cast-in-situ piles of $600\text{ mm}$ diameter.

---

## 6. Inputs Still Blocked (Prerequisites Required to Execute)

The following inputs are unverified or absent from the source drawings, preventing execution:
1. **Wall Centerline Runs**: Net wall lengths after deducting structural column and shear wall widths are not scheduled.
2. **Bay-by-Bay Clear Wall Heights**: Varying beam depths ($450\text{ mm}$ vs $600\text{ mm}$) create variable clear wall heights ($2450\text{ mm}$ to $2925\text{ mm}$) that cannot be averaged.
3. **Opening Counts per Flat/Floor**: Sheet `AR/TD/005` schedule omits opening count columns.
4. **Verified Floor Repetition Multiplier**: Tower-level aggregation cannot be run without verified floor repetition control.
5. **Column/Shear-Wall Vertical Height**: Member height is not scheduled on Sheet 104; current $3050\text{ mm}$ value is `ARCHITECTURAL_SECTION_DERIVED` from Section A-A.
6. **Official Bar Bending Schedule (BBS)**: Cut lengths, lap splices, hooks, and bending schedules are missing across all trades. Steel tonnage cannot be calculated.
7. **OHT Wall Thickness & Rebar**: Completely missing from Sheet 109. No wall thickness or reinforcement schedule exists.
8. **Pile Founding Depth**: Depth is not scheduled on Sheet 100 ($18.0\text{ m}$ is derived from DBR range).
9. **Pile Cap Entity Reconciliation**: Contradiction between 54 visible layout cap entities and 84 scheduled caps, with 91 piles unallocated under strip caps.
10. **Gross Facade Elevation Surface Areas**: 4-face elevation surface areas minus openings and architectural band projections have not been compiled.

---

## 7. Why Formulas Were Not Executed

Executing these formulas now would violate Phase-1 civil engineering integrity rules:
- Calculating masonry volume using gross wall runs would double-count column concrete zones, inflating brickwork by 15–20%.
- Calculating rebar tonnage without a BBS would require assuming lap lengths and hooks, producing arbitrary steel quantities.
- Calculating pile concrete based on an assumed $18\text{ m}$ depth would create up to 25% substructure variance.
- Calculating OHT wall volume would require inventing a wall thickness not present on the structural drawing.
- Scaling quantities across 24 flats or 6 floors without verified repetition gates would compound unverified dimensions.

Therefore, all formulas are strictly locked in status **`FORMULA_DEFINED_INPUTS_BLOCKED`**.

---

## 8. Why Project Is Still Not READY_FOR_TAKEOFF

The project cannot be certified as `READY_FOR_TAKEOFF` because:
- Crucial structural schedules (BBS, pile depths, OHT wall details) remain missing from the tender drawings.
- An unresolved foundation contradiction (54 vs 84 caps) exists in the substructure drawings.
- No itemized priced/unpriced tower BOQ exists to measure takeoff accuracy.
- Readiness remains strictly: **`DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`**.

---

## 9. Recommended Priority F Task

**Recommended Next Step**: **Priority F — Building Services (MEP) Controlled Transcription & Register Setup**.  
Transcribe directly visible equipment schedules, pipe runs, fixture counts, electrical distribution boards, and fire protection risers from the 18 Building Services drawing sheets (`Tender_drawing_4_Sections_StructuralCommunity_MEP_pdf-2025-Aug-28-17-39-32.pdf`, Sheets `MEP/001` to `MEP/018`) to establish the MEP baseline before any multi-trade quantity takeoff is considered.

