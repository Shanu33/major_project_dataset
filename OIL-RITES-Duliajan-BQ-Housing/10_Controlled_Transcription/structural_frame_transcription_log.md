# Structural Frame Controlled Transcription Log (Priority B)

**Project**: OIL/RITES Duliajan BQ Workmen Housing Complex  
**Tender No.**: RITES/NERPO/OIL/BQ-HOUSING/25  
**Scope Unit**: One typical Stilt+6 BQ Workmen Housing residential tower  
**Target Folder**: `10_Controlled_Transcription/`  
**Transcription Stage**: Priority B — Structural Frame (Superstructure & Foundation Frame)  
**Status**: `STRUCTURAL_FRAME_TRANSCRIPTION_PARTIAL`  
**Dataset Readiness**: `DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`  

---

## 1. Executive Summary

This log documents the controlled transcription of directly visible structural frame evidence from Sheets 103 through 110 of tender drawing package `Tender_drawing_3_TypicalFloor_StructuralHousing_pdf-2025-Aug-28-17-39-16.pdf`.

In strict accordance with Phase-1 audit rules:
- **Evidence Only**: Only directly visible dimensions, member marks, and rebar schedules are transcribed into controlled CSV registers.
- **No Height Assumptions on Schedule Sheets**: Column and shear wall heights are left blank (`height_mm = blank`) in `controlled_column_wall_register.csv` because Sheet 104 does not print storey heights. Member heights must be controlled separately from architectural/elevation drawings before any volume or cut-length calculation.
- **No Unscheduled Wall Assumptions**: Overhead water tank (OHT) RC wall thickness and wall reinforcement are NOT visibly scheduled on Sheet 109. The prior generic 150mm IS 3370 assumption has been completely removed from measured transcription values. The OHT wall row is retained strictly as a missing-evidence control row (`measured_value = NOT_VISIBLE`, `confidence = ASSUMPTION_REQUIRED`, `assumption_flag = YES`).
- **No Synthetic Takeoffs**: No concrete volumes ($m^3$), rebar weights (metric tonnes), or calculated cut-length spreadsheets are produced or claimed as verified.
- **Confidence Restriction**: Only approved provenance values (`DIRECT_SHEET_OBSERVATION`, `ESTIMATED`, `ASSUMPTION_REQUIRED`, `PARTIAL_RECONCILIATION_REQUIRED`) are used. Zero `HIGH` or `HIGH_CONFIDENCE` labels are assigned to derived quantities.
- **Separation of Fact vs Derivation**: The presence of legible structural cross-sections does not constitute an issued Bar Bending Schedule (BBS). Official BBS remains unissued by the engineer.

---

## 2. Drawing Sheets Inspected and Transcribed

| Sheet ID | Sheet Title | PDF Page | Discipline | Status | Transcribed Information |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `STR/TD/HOUSING(G+6)/103` | COLUMN AND SHEAR WALL LAYOUT PLAN | 19 | Structural | `LEGIBLE_FOR_TRANSCRIPTION` | 49 vertical elements: 16 columns (C1: 4, C2: 8, C3: 4) and 33 shear walls (SW1: 12, SW2: 4, SW3: 4, SW4: 4, SW5: 4, core walls SW6-SW10: 5). Member height is not scheduled. |
| `STR/TD/HOUSING(G+6)/104` | COLUMN AND SHEAR WALL REINFORCEMENT DETAILS | 20 | Structural | `LEGIBLE_FOR_TRANSCRIPTION` | Cross-sections, boundary elements, and rebar schedules for C1-C3, SW1-SW5, and combined core wall CW1 (SW6-SW10). Member height is not scheduled. |
| `STR/TD/HOUSING(G+6)/105` | PLINTH BEAM LAYOUT PLAN | 21 | Structural | `LEGIBLE_FOR_TRANSCRIPTION` | Plinth framing grid PB1 to PB34, tie beams TB1-TB2, and grade slab panels GS1 (125mm) and GS2 (150mm). |
| `STR/TD/HOUSING(G+6)/106` | PLINTH BEAM REINFORCEMENT DETAILS | 22 | Structural | `LEGIBLE_FOR_TRANSCRIPTION` | Longitudinal top/bottom rebar, side face bars, and stirrup spacing for PB1 to PB34 and TB1-TB2. |
| `STR/TD/HOUSING(G+6)/107` | BEAM LAYOUT PLAN FOR TYPICAL FLOORS & SLAB SCHEDULE | 23 | Structural | `LEGIBLE_FOR_TRANSCRIPTION` | Floor beams B1 to B34, tie beams TB1-TB2, and two-way suspended slab schedules S1 (125mm) and S2 (125mm). |
| `STR/TD/HOUSING(G+6)/108` | BEAM REINFORCEMENT DETAILS FOR TYPICAL FLOORS | 24 | Structural | `LEGIBLE_FOR_TRANSCRIPTION` | Longitudinal top/bottom rebar, side face bars, and stirrup spacing for B1 to B34 and TB1-TB2 across typical floors 1 to 6. |
| `STR/TD/HOUSING(G+6)/109` | MUMTY LEVEL AND WATER TANK BOTTOM LEVEL PLAN | 25 | Structural | `PARTIAL_RECONCILIATION_REQUIRED` | Mumty beams B1-B2 (230x450), OHT beam B1 (300x600), Mumty slab S1 (125mm), Lift overhead slab S1 (125mm), Water tank base slab S1 (150mm). OHT wall thickness and wall rebar are NOT visible / NOT scheduled. |
| `STR/TD/HOUSING(G+6)/110` | STAIRCASE PLAN & DETAILS - HOUSING BLOCK | 26 | Structural | `LEGIBLE_FOR_TRANSCRIPTION` | Riser R=150mm, Tread T=300mm, Flight Width W=1500mm, Waist slab=150mm, Landing beam 230x450mm, rebar T10-2L@100 c/c. |

---

## 3. Controlled Output Registers Status

1. **`controlled_column_wall_register.csv`** (13 element marks, 24 columns):
   - Transcribes 3 column types (`C1`, `C2`, `C3`) and 10 shear wall types (`SW1` to `SW10`).
   - Section length, section width, vertical bar counts, bar diameters, and tie confinement rules are direct Sheet 104 observations.
   - **`height_mm` is blank**: No member heights are printed on Sheet 104. Any assumption of 3050mm storey height belongs to architectural elevation/section analysis and must not be misattributed as a structural reinforcement schedule fact.
   - Official BBS remains unissued; total steel tonnage and concrete volumes are not calculated.

2. **`controlled_beam_register.csv`** (44 beam rows, 24 columns):
   - Transcribes plinth beams (`PB1` to `PB34`, `TB1`, `TB2`), typical floor beams (`B1` to `B34`, `TB1`, `TB2`), and roof/mumty/OHT beams (`B1`, `B2`).
   - Records directly visible web width (230mm, 300mm), overall depth (450mm, 600mm), top longitudinal rebar, bottom longitudinal rebar, side-face reinforcement, and stirrup pitch (70mm, 75mm, 100mm, 150mm c/c).
   - Clear spans are identified as variable by bay; beam run lengths are deliberately NOT pre-multiplied into final concrete volume or rebar tonnage.

3. **`controlled_slab_register.csv`** (7 slab rows, 25 columns):
   - Transcribes Grade Slabs `GS1` (125mm) and `GS2` (150mm) from Sheet 105.
   - Transcribes Typical Floor Slabs `S1` (125mm, T8@125 / T8@150 c/c) and `S2` (125mm, T10@125 / T10@150 c/c) from Sheet 107.
   - Transcribes Mumty Slab `S1` (125mm, T8@150 c/c both ways) and Lift Overhead Slab `S1` (125mm, T8@200 c/c both ways) from Sheet 109.
   - Transcribes Water Tank Bottom Slab `S1` (150mm, T10@125 / T10@150 c/c bottom, T8@125 / T8@150 c/c top) directly from Sheet 109 table.

4. **`controlled_stair_oht_register.csv`** (7 component rows, 24 columns):
   - Transcribes typical staircase flight (`ST-TYP`), landing slab/beam (`ST-LAND`), and plinth flight (`ST-PLINTH`) from Sheet 110.
   - Transcribes water tank bottom slab (`OHT-BASE`), stair mumty roof slab (`MUMTY-SLAB`), and lift overhead slab (`LIFT-SLAB`) from Sheet 109.
   - **OHT RC Wall (`OHT-WALL`) Cleanup**:
     - `tank_wall_thickness_mm`: blank
     - `measured_value`: `NOT_VISIBLE`
     - `extraction_method`: `NOT_VISIBLE_ON_SHEET_109`
     - `confidence`: `ASSUMPTION_REQUIRED`
     - `assumption_flag`: `YES`
     - `notes`: "OHT wall thickness and wall reinforcement are not visibly scheduled on Sheet 109. No wall quantity or wall thickness should be used until structural tank wall schedule is recovered."

---

## 4. Engineering Findings & Clarifications

1. **Water Tank Bottom Slab vs Tank Wall Status**:
   - **OHT Bottom Slab**: Directly transcribed as **`150 mm`** from Sheet 109 schedule table `WATER TANK BOTTOM SLABS SCHEDULE DETAILS`. This corrects the earlier engineering model assumption of 200mm.
   - **OHT RC Wall**: **NOT VISIBLE / NOT SCHEDULED** on Sheet 109. All generic 150mm assumptions have been removed from transcribed values. It remains classified as `ASSUMPTION_REQUIRED` and must not be used for quantity calculation until an official structural tank wall schedule is recovered.

2. **Column and Shear Wall Heights**:
   - Column/wall sections and rebar schedules are directly visible on Sheet 104.
   - Storey height is not scheduled on Sheet 104; `height_mm` is left blank in the column/wall register. Storey height / repeated floor use is not a BBS or final quantity.

3. **Status of Bar Bending Schedule (BBS)**:
   - Official BBS remains **NOT ISSUED** by the structural engineer.
   - Parameters such as bar lap staggering, crank lengths, anchorage lengths ($L_d$), and hook dimensions are unverified code derivations.

4. **Quantities and Guardrails**:
   - Zero concrete volume ($m^3$) or steel tonnage ($\text{MT}$) was calculated.
   - Active `READY_FOR_TAKEOFF` labels = 0.
   - Active `HIGH-confidence` assumption labels = 0.
   - Cost accuracy = `NOT_CALCULATED`.
   - Quantity accuracy = `NOT_CALCULATED`.
   - Labour/duration modelling = `BLOCKED`.
   - Final Priority B transcription status = `STRUCTURAL_FRAME_TRANSCRIPTION_PARTIAL`.
   - Overall dataset readiness = `DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`.
