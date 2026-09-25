# Second Pilot Phase 2 — Controlled Ground Floor Architectural and Foundation Transcription Log

**Project**: Development of Permanent Campus (Phase-I) for Nalanda University, at Rajgir, Bihar  
**Tender Package**: Package 1C (Construction and Development of Residential Buildings)  
**NIT Reference**: `NU/ENGG/54/2016-17/Tender: 01 dated 25th March 2017`  
**Selected Scope**: Faculty Housing Apartment Type 1B Block (G+2 Floors)  
**Working Directory**: `C:\Users\shahnawaz khan\OneDrive\Documents\DataRequirement\NIT-Nalanda`  
**Output Directory**: `10_Controlled_Transcription\second_pilot_phase_2_controlled_transcription`  
**Current Phase Status**: **`SECOND_PILOT_PHASE_2_B_CLEANUP_COMPLETE_FOUNDATION_EXECUTION_BLOCKED`**  
**Overall Dataset Readiness**: **`DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`**  
*(The project is strictly NOT `READY_FOR_TAKEOFF`)*

---

## 1. Scope

This Phase 2 transcription captures only directly visible and verifiable geometric parameters from the official tender drawings available for Faculty Housing Apartment Type 1B at Nalanda University:
- **Architectural Scope**: Ground Floor Plan (`a.2.1-type-1b-ground-floor-plan.pdf`), covering clear room dimensions, door schedules, window schedules, and floor level annotations.
- **Structural Foundation Scope**: Pile GA Layout & Details (`1.1-pile-layout-and-details-for-faculty-housing-appt-type-1b-.pdf`), covering gridlines X1-X17 and Y1-Y19, pile layout markers, typical pile diameter (600 mm) as a controlled observation, layout pile count (189) as an audited layout count, and general structural notes.
- **Specification Scope**: Material grades and standards referenced strictly for terminology and labeling (M25 concrete, Fe 500D steel, 50d lap lengths, CPWD / IS 2911 piling norms).

All upper floors (First Floor, Second Floor), vertical elevations, superstructure framing (columns, beams, slabs), rebar schedules, and cost data remain firewalled and excluded. Furthermore, pile linear running metres and pile concrete volume calculations are strictly blocked because pile depth is not confirmed by geotechnical founding criteria.

---

## 2. Source Drawings Used

| Drawing ID | File Path | Sheet No. | Title / Origin | Allowed Use | Blocked Scope |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `DWG_NAL_01` | `04_Architectural_Drawings/01_Faculty_Apartments/Type_1B/a.2.1-type-1b-ground-floor-plan.pdf` | `NUC(1)-FAH - A.2.1` | Faculty Apartment Type 1B - Ground Floor Plan (Vastu Shilpa Consultants, 13/02/2017, Scale 1:100) | Ground floor room dimensions, door/window schedules, plinth level | Full building takeoff, upper-floor inference, wall takeoff |
| `DWG_NAL_02` | `05_Structural_Drawings/01_Faculty_Housing_Apartments/Type_1B/1.1-pile-layout-and-details-for-faculty-housing-appt-type-1b-.pdf` | `NUC- FAH(1B)-S-A.1` | STRUCTURAL GA DRAWING OF PILE LAYOUT & DETAILS (Vinod Shah Consulting Engineers, 07/09/2016, Scale 1:50, 1:25) | Grid coordinates, audited pile count (189), typical pile diameter (600 mm) | Pile running metre takeoff, pile volume takeoff, rebar takeoff, pile cap takeoff |
| `DWG_NAL_03` | `03_Technical_Specifications_Reports/Specifications/Part_I_Civil_Works/nalanda-residential-specifications-part-i-civil-works.pdf` | `SPEC_PART_I` | Package 1C Residential Buildings Specifications - Part I Civil Works (179 pages) | Material grades, terminology, cover specifications | Direct quantity inputs, cost generation |

---

## 3. Files Created & Cleaned

All outputs are saved in [`10_Controlled_Transcription/second_pilot_phase_2_controlled_transcription`](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/NIT-Nalanda/10_Controlled_Transcription/second_pilot_phase_2_controlled_transcription):

1. [**`controlled_nalanda_drawing_register.csv`**](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/NIT-Nalanda/10_Controlled_Transcription/second_pilot_phase_2_controlled_transcription/controlled_nalanda_drawing_register.csv)  
   Source drawing register defining allowed vs prohibited scopes for each input sheet.
2. [**`controlled_nalanda_room_register.csv`**](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/NIT-Nalanda/10_Controlled_Transcription/second_pilot_phase_2_controlled_transcription/controlled_nalanda_room_register.csv)  
   Transcribed 23 ground-floor rooms/spaces with clear dimensions ($L, W$), derived floor areas, and perimeters.
3. [**`controlled_nalanda_opening_register.csv`**](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/NIT-Nalanda/10_Controlled_Transcription/second_pilot_phase_2_controlled_transcription/controlled_nalanda_opening_register.csv)  
   Transcribed 17 door, window, and ventilator schedule types with clear dimensions, derived face areas, and visible ground-floor counts.
4. [**`controlled_nalanda_grid_register.csv`**](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/NIT-Nalanda/10_Controlled_Transcription/second_pilot_phase_2_controlled_transcription/controlled_nalanda_grid_register.csv)  
   Transcribed 36 structural gridlines (17 X-axis, 19 Y-axis) with exact bay spacings and cumulative coordinates.
5. [**`controlled_nalanda_pile_register.csv`**](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/NIT-Nalanda/10_Controlled_Transcription/second_pilot_phase_2_controlled_transcription/controlled_nalanda_pile_register.csv) *(Cleaned in Phase 2-B)*  
   Controlled pile foundation record (Pile P1, 600 mm diameter as `DIRECT_SHEET_OBSERVATION`, 189 layout count as `DIRECT_LAYOUT_COUNT`, 12.700 m detail dimension classified as `DRAWING_DETAIL_DIMENSION_VISIBLE_BUT_NOT_FOUNDING_DEPTH` and `BLOCKED_FOR_QUANTITY_EXECUTION`).
6. [**`controlled_nalanda_foundation_blocker_register.csv`**](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/NIT-Nalanda/10_Controlled_Transcription/second_pilot_phase_2_controlled_transcription/controlled_nalanda_foundation_blocker_register.csv) *(Updated in Phase 2-B)*  
   Catalog of 9 formal takeoff blockers preventing foundation quantity calculation, explicitly including `PILE_RUNNING_METRE_BLOCKED`.
7. [**`controlled_nalanda_transcription_audit_trail.csv`**](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/NIT-Nalanda/10_Controlled_Transcription/second_pilot_phase_2_controlled_transcription/controlled_nalanda_transcription_audit_trail.csv) *(Cleaned in Phase 2-B)*  
   Line-by-line audit trail containing 164 records linking every direct observation, derived geometry, and blocked execution status to source sheets.
8. [**`phase_2_b_pile_evidence_verification.csv`**](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/NIT-Nalanda/10_Controlled_Transcription/second_pilot_phase_2_controlled_transcription/phase_2_b_pile_evidence_verification.csv) *(New in Phase 2-B)*  
   Exhaustive 12-point pile and foundation evidence verification register.
9. [**`phase_2_b_overclaim_cleanup_log.md`**](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/NIT-Nalanda/10_Controlled_Transcription/second_pilot_phase_2_controlled_transcription/phase_2_b_overclaim_cleanup_log.md) *(New in Phase 2-B)*  
   Synthesis log of all overclaim corrections and risk remediations.
10. [**`phase_2_b_final_guardrail_check.md`**](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/NIT-Nalanda/10_Controlled_Transcription/second_pilot_phase_2_controlled_transcription/phase_2_b_final_guardrail_check.md) *(New in Phase 2-B)*  
    Verification matrix confirming strict compliance with all negative constraints.
11. [**`phase_2_controlled_transcription_log.md`**](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/NIT-Nalanda/10_Controlled_Transcription/second_pilot_phase_2_controlled_transcription/phase_2_controlled_transcription_log.md)  
    This comprehensive Phase 2 synthesis log and governance audit report.

---

## 4. Room Data Transcribed (23 Records)

Directly transcribed from Sheet `NUC(1)-FAH - A.2.1`:

| Room ID | Space Name | Clear L (m) | Clear W (m) | Derived Area ($m^2$) | Perimeter ($m$) | Provenance | Notes |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| `RM_GF_01` | Living | 6.360 | 5.100 | 32.436 | 22.920 | `DIRECT_SHEET_OBSERVATION` | Dimension 636 x 510 cm |
| `RM_GF_02` | Dining | 3.500 | 3.760 | 13.160 | 14.520 | `DIRECT_SHEET_OBSERVATION` | Dimension 350 x 376 cm |
| `RM_GF_03` | Foyer | 3.500 | 2.250 | 7.875 | 11.500 | `DIRECT_SHEET_OBSERVATION` | Dimension 350 x 225 cm |
| `RM_GF_04` | Master Bedroom | 3.500 | 4.500 | 15.750 | 16.000 | `DIRECT_SHEET_OBSERVATION` | Dimension 350 x 450 cm |
| `RM_GF_05` | Bedroom | 3.500 | 3.900 | 13.650 | 14.800 | `DIRECT_SHEET_OBSERVATION` | Dimension 350 x 390 cm |
| `RM_GF_06` | Guest Bedroom | 3.730 | 3.900 | 14.547 | 15.260 | `DIRECT_SHEET_OBSERVATION` | Dimension 373 x 390 cm |
| `RM_GF_07` | Study | 3.500 | 3.500 | 12.250 | 14.000 | `DIRECT_SHEET_OBSERVATION` | Dimension 350 x 350 cm |
| `RM_GF_08` | Kitchen | 2.400 | 3.945 | 9.468 | 12.690 | `DIRECT_SHEET_OBSERVATION` | Dimension 240 x 394.5 cm |
| `RM_GF_09` | Store | 2.400 | 1.200 | 2.880 | 7.200 | `DIRECT_SHEET_OBSERVATION` | Dimension 240 x 120 cm |
| `RM_GF_10` | Servants Room | 3.300 | 1.935 | 6.386 | 10.470 | `DIRECT_SHEET_OBSERVATION` | Dimension 330 x 193.5 cm |
| `RM_GF_11` | Dressing | 1.665 | 1.800 | 2.997 | 6.930 | `DIRECT_SHEET_OBSERVATION` | Dimension 166.5 x 180 cm |
| `RM_GF_12` | Toilet (MBR) | 1.550 | 2.470 | 3.829 | 8.040 | `DIRECT_SHEET_OBSERVATION` | Dimension 155 x 247 cm |
| `RM_GF_13` | Toilet (BR) | 1.550 | 2.470 | 3.829 | 8.040 | `DIRECT_SHEET_OBSERVATION` | Dimension 155 x 247 cm |
| `RM_GF_14` | Toilet (Guest BR) | 1.550 | 2.585 | 4.007 | 8.270 | `DIRECT_SHEET_OBSERVATION` | Dimension 155 x 258.5 cm |
| `RM_GF_15` | Toilet (Servant) | 1.985 | 1.250 | 2.481 | 6.470 | `DIRECT_SHEET_OBSERVATION` | Dimension 198.5 x 125 cm |
| `RM_GF_16` | Powder Room | 1.290 | 1.595 | 2.058 | 5.770 | `DIRECT_SHEET_OBSERVATION` | Dimension 129 x 159.5 cm |
| `RM_GF_17` | Verandah (Living) | 8.110 | 1.890 | 15.328 | 20.000 | `DIRECT_SHEET_OBSERVATION` | Dimension 811 x 189 cm |
| `RM_GF_18` | Verandah (Bedrooms)| 3.500 | 2.190 | 7.665 | 11.380 | `DIRECT_SHEET_OBSERVATION` | Dimension 350 x 219 cm |
| `RM_GF_19` | Utility Verandah | 3.300 | 1.615 | 5.330 | 9.830 | `DIRECT_SHEET_OBSERVATION` | Dimension 330 x 161.5 cm |
| `RM_GF_20` | Verandah (Core) | 5.250 | 3.000 | 15.750 | 16.500 | `DIRECT_SHEET_OBSERVATION` | Dimension 525 x 300 cm |
| `RM_GF_21` | Lift Well | 2.550 | 1.900 | 4.845 | 8.900 | `DIRECT_SHEET_OBSERVATION` | Dimension 255 x 190 cm |
| `RM_GF_22` | Fire Shaft | 1.200 | 0.690 | 0.828 | 3.780 | `DIRECT_SHEET_OBSERVATION` | Dimension 120 x 69 cm |
| `RM_GF_23` | ELV Room | 2.780 | 1.550 | 4.309 | 8.660 | `DIRECT_SHEET_OBSERVATION` | Dimension 278 x 155 cm |

*(Note: Plinth Built-Up Area including core is noted as $264.67\text{ m}^2$ on drawing).*

---

## 5. Opening Data Transcribed (17 Records)

Directly transcribed from Door and Window Schedules on Sheet `NUC(1)-FAH - A.2.1`:

| Opening ID | Tag | Type | Width (m) | Height (m) | Sill (m) | Lintel (m) | Derived Area ($m^2$) | Count (GF) | Notes |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `OPN_GF_01` | `D1` | Flush Door w/ Flymesh | 1.000 | 2.100 | - | 2.100 | 2.100 | 2 | Main entrance & kitchen utility |
| `OPN_GF_02` | `D2` | Flush Door | 0.900 | 2.100 | - | 2.100 | 1.890 | 4 | Bedrooms & Study |
| `OPN_GF_03` | `D3` | Flush Door | 0.750 | 2.100 | - | 2.100 | 1.575 | 5 | Toilets, Store, Powder |
| `OPN_GF_04` | `D4` | Flush Door | 0.900 | 2.100 | - | 2.100 | 1.890 | 1 | Servant Room |
| `OPN_GF_05` | `D5` | M.S Gate | 1.500 | 2.900 | - | 2.900 | 4.350 | 1 | Core entrance security gate |
| `OPN_GF_06` | `DW1` | Door with Window | 3.500 | 3.115 | - | 3.115 | 10.903 | 1 | Master BR to Verandah |
| `OPN_GF_07` | `DW2` | Door with Window | 3.500 | 2.900 | - | 2.900 | 10.150 | 1 | Bedroom to Verandah |
| `OPN_GF_08` | `DW4` | Foldable Door | 6.360 | 2.900 | - | 2.900 | 18.444 | 1 | Living to Front Verandah |
| `OPN_GF_09` | `W1` | Wooden Window | 1.800 | 1.425 | 0.825 | 2.250 | 2.565 | 1 | Guest Bedroom |
| `OPN_GF_10` | `W2` | Wooden Window | 1.200 | 1.425 | 0.825 | 2.250 | 1.710 | 1 | Study |
| `OPN_GF_11` | `W3` | Wooden Window | 2.100 | 1.385 | 0.865 | 2.250 | 2.909 | 1 | Dining |
| `OPN_GF_12` | `W4` | Wooden Window | 1.200 | 2.080 | 0.170 | 2.250 | 2.496 | 1 | Living room side |
| `OPN_GF_13` | `W6` | Wooden Window | 0.600 | 2.080 | 0.170 | 2.250 | 1.248 | 1 | Kitchen |
| `OPN_GF_14` | `W7` | Large Glazed Window | 3.500 | 2.730 | 0.170 | 2.900 | 9.555 | 1 | Living / Core screen |
| `OPN_GF_15` | `W8` | Toilet Ventilator | 0.645 | 1.500 | 1.400 | 2.900 | 0.968 | 3 | High level obscure glazing |
| `OPN_GF_16` | `W9` | Wooden Window | 1.200 | 2.080 | 0.170 | 2.250 | 2.496 | 1 | Servant Room |
| `OPN_GF_17` | `W10`| Fixed Glass Transom | 1.200 | 1.080 | 1.820 | 2.900 | 1.296 | 1 | ELV Room / Core |

---

## 6. Grid Data Transcribed (36 Gridlines)

Directly transcribed from Sheet `NUC- FAH(1B)-S-A.1`:

- **X-Axis Grids (17 Gridlines)**:
  - Spacings (m): X1-X2 (3.665), X2-X3 (1.960), X3-X4 (3.960), X4-X5 (2.860), X5-X6 (1.750), X6-X7 (2.010), X7-X8 (3.960), X8-X9 (3.010), X9-X10 (2.700), X10-X11 (3.960), X11-X12 (2.010), X12-X13 (1.750), X13-X14 (2.860), X14-X15 (3.960), X15-X16 (1.960), X16-X17 (3.665).
  - Total transverse dimension between extreme gridlines X1 and X17: **$46.040\text{ m}$**.
- **Y-Axis Grids (19 Gridlines)**:
  - Spacings (m): Y1-Y2 (0.900), Y2-Y3 (0.565), Y3-Y4 (0.600), Y4-Y5 (0.845), Y5-Y6 (0.145), Y6-Y7 (0.160), Y7-Y8 (1.065), Y8-Y9 (0.945), Y9-Y10 (1.200), Y10-Y11 (1.960), Y11-Y12 (0.300), Y12-Y13 (1.245), Y13-Y14 (0.415), Y14-Y15 (1.685), Y15-Y16 (0.600), Y16-Y17 (0.440), Y17-Y18 (0.920), Y18-Y19 (0.760).
  - Additional edge offsets: $2.700\text{ m}$ below Y1, $3.000\text{ m}$ above Y19. Total longitudinal grid extent: **$14.750\text{ m}$** (overall building envelope ~ $19.890\text{ m}$).

---

## 7. Pile / Foundation Data Transcribed & Cleaned

Directly transcribed and audited from Sheet `NUC- FAH(1B)-S-A.1`:

- **Pile Type**: Bored Cast-In-Situ Reinforced Concrete Pile (`P1`) (`DIRECT_SHEET_OBSERVATION`).
- **Pile Diameter**: **$600\text{ mm}$** ($0.600\text{ m}$), scheduled directly on `TYPICAL DETAIL OF PILE (P1)` (`600Φ`) and `SECTION X-X` (`600 DIA`) (`DIRECT_SHEET_OBSERVATION`).
- **Total Pile Count**: **189 piles** counted across the entire GA layout (`DIRECT_LAYOUT_COUNT`).
- **Pile Detail Dimension Status**: **$12.700\text{ m}$** is dimensioned on the typical detail with a break line, but is classified strictly as **`DRAWING_DETAIL_DIMENSION_VISIBLE_BUT_NOT_FOUNDING_DEPTH`**. It is NOT confirmed as an executable pile founding depth because geotechnical borehole logs, strata profiles, and termination criteria are missing.
- **Pile Quantity Execution**: **STRICTLY BLOCKED**. Pile running metres and pile concrete volume must NOT be calculated.
- **Concrete Grade**: M25 (per general notes: "ALL CONCRETE MIX M25 UNLESS OTHERWISE SPECIFIED") (`DIRECT_SHEET_OBSERVATION`).
- **Steel Grade**: Fe 500D TMT bars (per general notes: "INDICATES TMT STEEL (Fe 500D) OF YIELD STRENGTH 500 N/mm²") (`DIRECT_SHEET_OBSERVATION`).
- **Clear Concrete Cover**: Piles: $50\text{ mm}$; Pile Cap: $60\text{ mm}$; Grade Beam: $30\text{ mm}$; Footings: $50\text{ mm}$; Columns & Pedestals: $40\text{ mm}$ (`DIRECT_SHEET_OBSERVATION`).
- **Lap Length**: 50 times bar diameter ($50d$) (`DIRECT_SHEET_OBSERVATION`).
- **Lean Concrete**: 100 mm thick Lean Con. (1:4:8) under foundation beam/slab (`DIRECT_SHEET_OBSERVATION`).
- **Missing Foundation Schedules**:
  - Longitudinal steel bar diameter, bar count, spiral tie diameter, and pitch are completely omitted (Section X-X shows plain concrete with no rebar).
  - Pile cap schedule (dimensions, thickness, individual markings) is omitted.
  - Grade beam framing layout is omitted.

---

## 8. Derived Geometry

Only basic geometric derivations were performed:
1. **Room Clear Floor Area**: $\text{Area} = \text{Length} \times \text{Width}$ ($m^2$).
2. **Room Perimeter**: $\text{Perimeter} = 2 \times (\text{Length} + \text{Width})$ ($m$).
3. **Opening Area**: $\text{Face Area} = \text{Width} \times \text{Height}$ ($m^2$).
4. **Cumulative Grid Positions**: Cumulative summation of observed bay center-to-center distances along X and Y axes.

*No plaster deductions, no masonry volumes, no pile running metres, no pile concrete volumes, no structural concrete quantities, and no rebar tonnages were derived.*

---

## 9. Missing Evidence Register

The following items remain missing from the repository:
1. **Upper Floor Architectural Plans**: 1st Floor and 2nd Floor plans are missing.
2. **Architectural Building Sections & Elevations**: Cross-sections showing floor-to-floor heights, lintel levels, and beam depths are missing.
3. **Superstructure Structural Framing Plans**: Column schedules, beam layouts, and slab reinforcement drawings are missing.
4. **Pile Reinforcement & Bar Bending Schedule (BBS)**: Rebar details for pile P1 are missing.
5. **Pile Cap Schedule & GA Details**: Cap geometry, grouping, and rebar are missing.
6. **Geotechnical Soil Investigation Report**: Plot-specific borehole logs and bedrock socketing criteria are missing.
7. **Building-Wise BOQ Breakdown**: Schedule B aggregates all Package 1C residential units without a single-building allocation for Type 1B.

---

## 10. Why Full Takeoff & Foundation Execution Remain Blocked

Full takeoff and foundation quantity execution are strictly blocked because:
1. Pile depth is unconfirmed; multiplying 189 piles by the 12.700 m schematic detail dimension produces an unvalidated quantity without geotechnical borehole verification.
2. Superstructure framing is absent; calculating column, beam, or slab quantities would require 100% blind hallucination.
3. Foundation reinforcement and pile cap dimensions are absent; calculating pile steel or foundation RCC would require arbitrary assumptions.
4. Upper floor floor-to-floor heights and layouts are absent; multiplying ground floor dimensions across upper storeys violates CPWD measurement rules.
5. BOQ Schedule B is bundled across the entire residential parcel; single-building benchmarking cannot be performed.

---

## 11. Mandatory Guardrail Confirmations

The following guardrails were strictly enforced during Phase 2 and Phase 2-B:
- [x] **No final quantities were calculated** ($0.0\text{ m}^3$ concrete, $0.0\text{ MT}$ steel, $0.0\text{ m}^3$ masonry).
- [x] **No costs were calculated** (`Cost accuracy: NOT_CALCULATED`).
- [x] **No BOQ validation was performed** (`Quantity accuracy: NOT_CALCULATED`).
- [x] **No labour/duration modelling was performed** (`Labour/Duration: BLOCKED`).
- [x] **BOQ and ECPT documents were NOT used as AI inputs** (strictly firewalled).
- [x] **No upper-floor multiplication was applied** (all data tagged `GROUND_FLOOR_ONLY`).
- [x] **No full building takeoff was performed**.
- [x] **No pile running metres were calculated** (`PILE_RUNNING_METRE_BLOCKED`).
- [x] **No pile concrete volume was calculated**.
- [x] **No reinforcement tonnage was calculated**.
- [x] **The project remains `DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`**.
- [x] **The project is strictly NOT `READY_FOR_TAKEOFF`**.

---

## 12. Recommended Phase 3 Task

**Recommended Next Step**: **Second Pilot Phase 3 — Formula Setup and Blocked Dependency Mapping**.
- Set up mathematical formula templates and dependency maps for directly verified ground-floor architectural items (e.g. room floor areas, floor skirting, internal wall perimeters, and opening deductions).
- Define structural foundation formula templates with explicit blocker tags on pile running metres, pile concrete volume, and reinforcement steel.
- Maintain explicit blockades on all upper-floor, superstructure RCC, and BOQ validation formulas.
- Do NOT perform sample execution of pile running metres or foundation concrete quantities.
