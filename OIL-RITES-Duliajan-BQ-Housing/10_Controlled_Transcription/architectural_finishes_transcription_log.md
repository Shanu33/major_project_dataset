# Architectural and Finishes Controlled Transcription Log (Priority C)

**Project**: OIL/RITES Duliajan BQ Workmen Housing Complex  
**Tender No.**: RITES/NERPO/OIL/BQ-HOUSING/25  
**Scope Unit**: One typical Stilt+6 BQ Workmen Housing residential tower  
**Target Folder**: `10_Controlled_Transcription/`  
**Transcription Stage**: Priority C — Architectural Openings, Room Dimensions, Finishes & Masonry Deduction Logic  
**Status**: `ARCHITECTURAL_FINISHES_TRANSCRIPTION_PARTIAL`  
**Dataset Readiness**: `DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`  

---

## 1. Executive Summary

This log documents the controlled transcription and provenance cleanup of directly visible architectural, room geometric, finish, and opening deduction evidence for one typical Stilt+6 residential housing tower from approved tender drawings:
- `Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf` (Sheets AR/TD/005 to AR/TD/020)
- `Tender_drawing_2_First_Second_Floor_pdf-2025-Aug-28-17-38-57.pdf` (Sheets AR/TD/022, 023, 025)

In strict accordance with Phase-1 audit rules:
- **Evidence vs Derived Geometry Strictly Separated**: Directly observed dimensions (length, width, height, sill, lintel) are strictly categorized as `DIRECT_SHEET_OBSERVATION`. All calculated geometric parameters (opening area $= W \times H$, room floor area $= L \times W$, room perimeter $= 2L + 2W$) are explicitly classified as `DERIVED_BASIC_GEOMETRY`.
- **No Premature Quantities**: No total brickwork masonry volumes ($m^3$), plaster areas ($m^2$), flooring areas ($m^2$), paint areas ($m^2$), or cost estimates are calculated.
- **No Synthetic Deduction Ratios**: Historical assumptions (e.g. 23% external wall / 10% internal wall generic deductions) have been completely removed. In `controlled_masonry_deduction_register.csv`, deduction area is recorded per opening mark based on basic geometry ($W \times H$), while gross wall area, net masonry area, and deduction percentages remain uncalculated.
- **No Pre-multiplication Across Units**: Room dimensions and opening marks are captured per unit/panel. Multipliers of 4 units/floor or 24 flats/tower are deliberately NOT pre-multiplied into material totals.
- **Confidence Restriction**: Provenance values are strictly restricted to `DIRECT_SHEET_OBSERVATION` and `DERIVED_BASIC_GEOMETRY`. Zero `HIGH` confidence labels are assigned to derived quantities.

---

## 2. Drawing Sheets Inspected and Transcribed

| Sheet ID | Sheet Title | PDF Page | Discipline | Status | Transcribed Information |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `AR/TD/005` | TYPICAL UNIT PLAN & SCHEDULE OF OPENINGS | Doc1, p. 9 | Architectural | `LEGIBLE_FOR_TRANSCRIPTION` | Clear room dimensions for typical flat (Living/Dining, Master Bed, Bed 2, Study, Kitchen, Toilets, Balconies); opening schedule table (D1-D3, DW1-DW2, SD1-SD4, W1-W4, V1-V2). |
| `AR/TD/006` | TYPICAL STILT FLOOR PLAN | Doc1, p. 10 | Architectural | `LEGIBLE_FOR_TRANSCRIPTION` | Stilt footprint $30.08\text{ m} \times 16.08\text{ m}$, driveway ramps, ELV room $3855 \times 3220\text{ mm}$, fire shafts. |
| `AR/TD/007` | TYPICAL FLOOR PLAN (1ST TO 6TH FLOOR) | Doc1, p. 11 | Architectural | `LEGIBLE_FOR_TRANSCRIPTION` | 4 units per floor layout, central corridor ($3200\text{ mm}$ wide), staircase core, lift lobby with Lift 1 (15-pass) and Lift 2 (MRL). |
| `AR/TD/008` | TYPICAL TERRACE PLAN | Doc1, p. 12 | Architectural | `LEGIBLE_FOR_TRANSCRIPTION` | Terrace floor plate, $225\text{ mm}$ thick & $1200\text{ mm}$ high parapet wall, 1:80 slope, $450 \times 450\text{ mm}$ khurras. |
| `AR/TD/009` | TYPICAL MUMTY LVL PLAN | Doc1, p. 13 | Architectural | `LEGIBLE_FOR_TRANSCRIPTION` | Stair mumty plinth ($34.18\text{ m}^2$), lift machine room, fire water tank ($25,000\text{ L}$ capacity, water depth $2.0\text{ m} + 300\text{ mm}$ freeboard). |
| `AR/TD/010` | TYPICAL ELEVATION (A) | Doc1, p. 14 | Architectural | `LEGIBLE_FOR_TRANSCRIPTION` | Storey height $3.05\text{ m}$ ($3050\text{ mm}$), total building height $24.0\text{ m}$, facade plaster and louvers. |
| `AR/TD/011` | TYPICAL ELEVATION (B) | Doc1, p. 15 | Architectural | `LEGIBLE_FOR_TRANSCRIPTION` | Side elevation, building width $16.08\text{ m}$, balconies, chajjas, architectural bands. |
| `AR/TD/012` | SECTION A-A | Doc1, p. 16 | Architectural | `LEGIBLE_FOR_TRANSCRIPTION` | Longitudinal section: floor-to-floor height $3.05\text{ m}$, slab thickness $125\text{ mm}$, clear ceiling height $2.925\text{ m}$. |
| `AR/TD/013` | SECTION B-B | Doc1, p. 17 | Architectural | `LEGIBLE_FOR_TRANSCRIPTION` | Cross section: central corridor width $3.2\text{ m}$, stair flight width $1.5\text{ m}$, riser $150\text{ mm}$, tread $300\text{ mm}$. |
| `AR/TD/014` | DOOR AND WINDOW SCHEDULES & DETAILS-1 | Doc1, p. 18 | Architectural | `LEGIBLE_FOR_TRANSCRIPTION` | Fabrication sections, frame materials, and shutter specs for D1, D2, D3, DW1, DW2, SD1, SD4, W1, V1. |
| `AR/TD/015` | DOOR AND WINDOW SCHEDULES & DETAILS-2 | Doc1, p. 19 | Architectural | `LEGIBLE_FOR_TRANSCRIPTION` | Fabrication sections and specs for W2, W3, W4, V2, SD2, SD3. |
| `AR/TD/016` | FLOORING LAYOUT STILT FLOOR | Doc1, p. 20 | Architectural | `LEGIBLE_FOR_TRANSCRIPTION` | $60\text{ mm}$ CC paver block for parking/driveway; $25\text{ mm}$ Kota stone (FL-07) for fire control/ELV; $18\text{ mm}$ granite for ramps/steps. |
| `AR/TD/017` | FLOORING LAYOUT TYPICAL FLOOR | Doc1, p. 21 | Architectural | `LEGIBLE_FOR_TRANSCRIPTION` | Polished vitrified tiles ($600 \times 600$) for living/bedrooms; anti-skid vitrified ($600 \times 600$) for balconies/kitchen; anti-skid ceramic ($300 \times 300$) for toilets; $18\text{ mm}$ granite (FL-01) for corridors. |
| `AR/TD/018` | FLOORING LAYOUT TERRACE FLOOR | Doc1, p. 22 | Architectural | `LEGIBLE_FOR_TRANSCRIPTION` | Liquid rubber waterproofing, CC 1:2:4 roof grading concrete, heat-resistant SRI tiles, khurras. |
| `AR/TD/019` | TYPICAL TOILET DETAILS - PLAN & PIPING | Doc1, p. 23 | Architectural | `LEGIBLE_FOR_TRANSCRIPTION` | Anti-skid ceramic floor tile ($300 \times 300$); ceramic wall tiles dado up to false ceiling height; calcium silicate false ceiling. |
| `AR/TD/020` | TYPICAL TOILET DETAILS - SECTIONS | Doc1, p. 24 | Architectural | `LEGIBLE_FOR_TRANSCRIPTION` | Wall tile cladding sections, sunken slab details, drop levels, plumbing chase walls. |
| `AR/TD/022` | TYPICAL STAIRCASE PLAN AT GROUND & TYPICAL | Doc2, p. 1 | Architectural | `LEGIBLE_FOR_TRANSCRIPTION` | Staircase plan: flight width $1500\text{ mm}$, riser $150\text{ mm}$, tread $300\text{ mm}$, threshold steps. |
| `AR/TD/023` | STAIRCASE SECTIONS XX & YY | Doc2, p. 2 | Architectural | `LEGIBLE_FOR_TRANSCRIPTION` | Landing levels, headroom height, floor levels ($+3.45\text{m}$ to $+22.35\text{m}$). |
| `AR/TD/025` | WARDROBE & KITCHEN COUNTER DETAILS | Doc2, p. 4 | Architectural | `LEGIBLE_FOR_TRANSCRIPTION` | Polished granite kitchen countertop with ceramic tile dado above counter; $100\text{ mm}$ high vitrified tile skirting. |

---

## 3. Controlled Output Registers Summary

### 3.1. `controlled_opening_register.csv` (15 rows, 26 columns)
Directly captures all 15 scheduled opening marks across doors, windows, combinations, and ventilators:
- **Doors**:
  - `D1` ($800 \times 2100\text{ mm}$): Single leaf WPC frame & flush door shutter for toilets. Area = $1.68\text{ m}^2$ (`DERIVED_BASIC_GEOMETRY`).
  - `D2` ($1000 \times 2100\text{ mm}$): Single leaf teak wood frame & laminated flush shutter for bedrooms. Area = $2.10\text{ m}^2$ (`DERIVED_BASIC_GEOMETRY`).
  - `D3` ($1050 \times 2100\text{ mm}$): Single leaf teak wood frame for double shutter (flush + wire mesh) for main flat entrance. Area = $2.205\text{ m}^2$ (`DERIVED_BASIC_GEOMETRY`).
- **Door-Window Combinations**:
  - `DW1` ($2000 \times 2100\text{ mm}$): Living balcony opening with double shutter (flush + wire mesh) and casement window. Area = $4.20\text{ m}^2$ (`DERIVED_BASIC_GEOMETRY`).
  - `DW2` ($2295 \times 2100\text{ mm}$): Living balcony opening with casement window. Area = $4.82\text{ m}^2$ (`DERIVED_BASIC_GEOMETRY`).
- **Service Doors**:
  - `SD1` ($900 \times 2100\text{ mm}$, sill $100\text{ mm}$): Double leaf MS door for electrical shaft. Area = $1.89\text{ m}^2$ (`DERIVED_BASIC_GEOMETRY`).
  - `SD2` ($600 \times 2100\text{ mm}$, sill $100\text{ mm}$): Single leaf MS door (2 hr fire rated) for plumbing shaft. Area = $1.26\text{ m}^2$ (`DERIVED_BASIC_GEOMETRY`).
  - `SD3` ($900 \times 2100\text{ mm}$, sill $100\text{ mm}$): MS single leaf door with glass for FHC shaft. Area = $1.89\text{ m}^2$ (`DERIVED_BASIC_GEOMETRY`).
  - `SD4` ($1200 \times 2100\text{ mm}$, sill $100\text{ mm}$): MS double leaf door for plant room / mumty. Area = $2.52\text{ m}^2$ (`DERIVED_BASIC_GEOMETRY`).
- **Windows**:
  - `W1` ($1200 \times 1200\text{ mm}$, sill $900\text{ mm}$): Aluminum sliding cum fixed panels window for bedrooms. Area = $1.44\text{ m}^2$ (`DERIVED_BASIC_GEOMETRY`).
  - `W2` ($1000 \times 1225\text{ mm}$, sill $1225\text{ mm}$): Aluminum sliding window with wire mesh & MS grill for kitchens. Area = $1.225\text{ m}^2$ (`DERIVED_BASIC_GEOMETRY`).
  - `W3` ($2300 \times 1100\text{ mm}$, sill $1000\text{ mm}$): Aluminum sliding window with MS grill for staircase well. Area = $2.53\text{ m}^2$ (`DERIVED_BASIC_GEOMETRY`).
  - `W4` ($1200 \times 1200\text{ mm}$, sill $900\text{ mm}$): Aluminum sliding window with MS grill. Area = $1.44\text{ m}^2$ (`DERIVED_BASIC_GEOMETRY`).
- **Ventilators**:
  - `V1` ($515 \times 875\text{ mm}$, sill $1225\text{ mm}$): Aluminum fixed frosted glass panel with exhaust fan for attached toilet. Area = $0.451\text{ m}^2$ (`DERIVED_BASIC_GEOMETRY`).
  - `V2` ($615 \times 875\text{ mm}$, sill $1225\text{ mm}$): Aluminum fixed frosted glass panel with exhaust fan for common toilet. Area = $0.538\text{ m}^2$ (`DERIVED_BASIC_GEOMETRY`).

### 3.2. `controlled_room_register.csv` (14 rows, 24 columns)
Directly captures clear room dimensions for typical flat units and core spaces:
- `Living / Dining`: $3970 \times 5520\text{ mm}$ (Floor Area = $21.91\text{ m}^2$, Perimeter = $18.98\text{ m}$ — `DERIVED_BASIC_GEOMETRY`)
- `Master Bedroom`: $3845 \times 3220\text{ mm}$ (Floor Area = $12.38\text{ m}^2$, Perimeter = $14.13\text{ m}$ — `DERIVED_BASIC_GEOMETRY`)
- `Bedroom 2`: $3845 \times 3070\text{ mm}$ (Floor Area = $11.80\text{ m}^2$, Perimeter = $13.83\text{ m}$ — `DERIVED_BASIC_GEOMETRY`)
- `Study Room`: $2440 \times 2640\text{ mm}$ (Floor Area = $6.44\text{ m}^2$, Perimeter = $10.16\text{ m}$ — `DERIVED_BASIC_GEOMETRY`)
- `Kitchen`: $2440 \times 2580\text{ mm}$ (Floor Area = $6.30\text{ m}^2$, Perimeter = $10.04\text{ m}$ — `DERIVED_BASIC_GEOMETRY`)
- `Attached Toilet`: $2700 \times 1400\text{ mm}$ (Floor Area = $3.78\text{ m}^2$, Perimeter = $8.20\text{ m}$ — `DERIVED_BASIC_GEOMETRY`)
- `Common Toilet`: $1345 \times 2400\text{ mm}$ (Floor Area = $3.23\text{ m}^2$, Perimeter = $7.49\text{ m}$ — `DERIVED_BASIC_GEOMETRY`)
- `Living Balcony`: $2280 \times 1365\text{ mm}$ (Floor Area = $3.11\text{ m}^2$, Perimeter = $7.29\text{ m}$ — `DERIVED_BASIC_GEOMETRY`)
- `Bedroom 1 Balcony`: $1200 \times 2000\text{ mm}$ (Floor Area = $2.40\text{ m}^2$, Perimeter = $6.40\text{ m}$ — `DERIVED_BASIC_GEOMETRY`)
- `Bedroom 2 Balcony`: $1200 \times 2000\text{ mm}$ (Floor Area = $2.40\text{ m}^2$, Perimeter = $6.40\text{ m}$ — `DERIVED_BASIC_GEOMETRY`)
- `Central Corridor`: $3200\text{ mm}$ clear width (`DIRECT_SHEET_OBSERVATION`)
- `Staircase Core`: Flight width $1500\text{ mm}$, riser $150\text{ mm}$, tread $300\text{ mm}$ (`DIRECT_SHEET_OBSERVATION`)
- `Lift Core`: 15-passenger lift & MRL stretcher lift shafts (`DIRECT_SHEET_OBSERVATION`)
- `Stilt ELV Room`: $3855 \times 3220\text{ mm}$ (Floor Area = $12.41\text{ m}^2$, Perimeter = $14.15\text{ m}$ — `DERIVED_BASIC_GEOMETRY`)

### 3.3. `controlled_finish_register.csv` (10 rows, 24 columns)
Directly transcribes finish specifications per room category from floor finish layouts and detail sheets (`DIRECT_SHEET_OBSERVATION`):
1. `Living / Dining / Bedrooms / Study`: Polished vitrified tiles ($600 \times 600\text{ mm}$), $100\text{ mm}$ matching skirting, internal plaster + acrylic emulsion paint.
2. `Balconies`: Matt / anti-skid vitrified tiles ($600 \times 600\text{ mm}$), $100\text{ mm}$ matching skirting, external waterproof plaster + weather-proof paint.
3. `Kitchen`: Matt / anti-skid vitrified tiles ($600 \times 600\text{ mm}$), granite counter with ceramic tile wall dado ($600\text{ mm}$ above counter).
4. `Toilets`: Rectified anti-skid ceramic tiles ($300 \times 300\text{ mm}$), ceramic wall tiles dado up to false ceiling height (minimum $2100\text{ mm}$), calcium silicate false ceiling.
5. `Corridor / Lift Lobby`: $18\text{ mm}$ thick polished granite flooring (`FL-01`) with $100\text{ mm}$ granite skirting, plaster + synthetic enamel / plastic emulsion.
6. `Main Staircase`: $18\text{ mm}$ thick polished granite with anti-skid grooves on treads, $100\text{ mm}$ granite skirting along stringers.
7. `Stilt Parking / Driveway`: $60\text{ mm}$ thick cement concrete paver blocks with tactile tiles ($300 \times 300\text{ mm}$) or VDF concrete.
8. `Stilt Service Rooms (ELV / Fire Control)`: $25\text{ mm}$ thick Kota stone flooring (`FL-07`) with $100\text{ mm}$ Kota skirting.
9. `Terrace Roof`: Liquid rubber waterproofing, CC 1:2:4 grading concrete for 1:80 slope, heat-resistant SRI tiles, $450 \times 450\text{ mm}$ rainwater khurras.
10. `External Facade`: Two-coat external cement plaster ($18\text{ mm}$) with acrylic exterior emulsion paint.

### 3.4. `controlled_masonry_deduction_register.csv` (15 rows, 25 columns)
Captures the deduction geometry basis for all scheduled openings across external ($230\text{ mm}$) and internal ($115\text{ mm}$) brickwork (`DERIVED_BASIC_GEOMETRY` for opening area):
- External $230\text{ mm}$ wall deductions: `W1` ($1.44\text{ m}^2$), `W2` ($1.225\text{ m}^2$), `W3` ($2.53\text{ m}^2$), `W4` ($1.44\text{ m}^2$), `DW1` ($4.20\text{ m}^2$), `DW2` ($4.82\text{ m}^2$), `V1` ($0.451\text{ m}^2$), `V2` ($0.538\text{ m}^2$).
- Internal $115\text{ mm}$ / $230\text{ mm}$ wall deductions: `D1` ($1.68\text{ m}^2$), `D2` ($2.10\text{ m}^2$), `D3` ($2.205\text{ m}^2$), `SD1` ($1.89\text{ m}^2$), `SD2` ($1.26\text{ m}^2$), `SD3` ($1.89\text{ m}^2$), `SD4` ($2.52\text{ m}^2$).
- `gross_wall_area_sqm`, `net_masonry_area_sqm`, and `deduction_percentage` are deliberately left blank.
- Final masonry volume ($m^3$) remains uncalculated until full wall runs and heights are reconciled floor-wise.

---

## 4. Provenance Cleanup & Separation Confirmation

In this cleanup pass:
- **Priority C Status**: Remains **`ARCHITECTURAL_FINISHES_TRANSCRIPTION_PARTIAL`**.
- **Clear Provenance Separation**: Direct sheet observations (dimensions, marks, materials) and derived geometry (opening areas, room floor areas, perimeters) have been unambiguously separated.
- **Derived Values Explicitly Labeled**: Opening areas, room areas, and perimeters are explicitly designated as `DERIVED_BASIC_GEOMETRY`. Notes affirm they are geometric products ($W \times H$ or $L \times W$), not separate printed values.
- **No Final Quantities Calculated**: No total brickwork masonry volumes ($m^3$), plaster areas ($m^2$), flooring areas ($m^2$), paint areas ($m^2$), or costs were calculated.
- **No Cost Validation Performed**: Cost figures remain completely unmodeled (`Cost accuracy: NOT_CALCULATED`).
- **No Synthetic Deduction Ratios Used**: All legacy parametric deduction assumptions (23% external, 10% internal) are completely absent.
- **No 24-Unit Tower Multiplier Applied**: Unit dimensions and areas remain strictly per-flat/per-panel; no global multiplication was performed.
- **Active Guardrail Labels**:
  - Active `READY_FOR_TAKEOFF` labels: **0**
  - Active `HIGH_CONFIDENCE` assumption labels: **0**
  - Labour / Duration Modelling: **`BLOCKED`**
  - Quantity Accuracy: **`NOT_CALCULATED`**
  - Dataset Readiness: **`DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`**
