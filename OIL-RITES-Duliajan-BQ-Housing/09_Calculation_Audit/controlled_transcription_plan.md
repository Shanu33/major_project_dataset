# Controlled Transcription Plan (Pre-Modelling Protocol)
## OIL/RITES Duliajan BQ Workmen Housing (Typical Tower Pilot)

**Project**: OIL/RITES Duliajan BQ Workmen Housing Complex  
**Tender Reference**: `RITES/NERPO/OIL/BQ-HOUSING/25`  
**Phase Objective**: Convert legible drawing geometry, schedules, and annotations into line-by-line traceable tabular registers before running any automated quantity takeoff or intelligence models.  
**Destination Folder**: `10_Controlled_Transcription/`  

---

## 1. Operating Rules & Transcription Principles

1. **Direct Visibility Only**: Transcribe only what is printed on the sheet (dimensions, callouts, text blocks, schedule rows). Do not interpolate unstated dimensions or invent bar cut lengths.
2. **Evidence Linking on Every Row**: Every single record must cite:
   - `source_pdf`
   - `sheet_id`
   - `sheet_title`
   - `page_number`
   - `revision`
   - `extraction_method` (`MANUAL_VISUAL_TRANSCRIPTION`)
3. **Explicit Assumption Flagging**: If any value relies on an assumed standard parameter (e.g. pile depth 18m, cap thickness 1.0m, OHT walls 150mm), set `assumption_flag = TRUE` and record the rationale.
4. **No Premature Quantities**: Transcribe raw geometric parameters (lengths, breadths, depths, counts, diameters, bar marks). Do not pre-multiply into final steel tonnages or concrete m3 in this phase.

---

## 2. Execution Phases & Priority Order

```
[Priority A: Foundation] ➔ [Priority B: Structural Frame] ➔ [Priority C: Architectural Finishes]
```

### Priority A — Foundation Elements (Target: Resolve Substructure Blockers)

#### Step A.1: Sheet 100 Transcription (Bored RCC Piles)
- **Source Sheet**: `RITES/BLD/STR/TD/HOUSING(G+6)/100` (`Tender_drawing_3`, Page 16)
- **Sheet Title**: `PILE LAYOUT PLAN`
- **Scope to Transcribe**:
  - Transcribe all 207 individual pile coordinates (Grid intersection: A–M numeric and 1–12 alpha).
  - Pile diameter (600 mm).
  - Pile group assignment (P1, P2, P3, P4, strip cap cluster).
  - Drawing notes on founding level, cut-off level, and socketing criteria.
- **Output File**: `10_Controlled_Transcription/controlled_pile_register.csv`

#### Step A.2: Sheet 101 Transcription (Pile Caps & Ground Tie Layout)
- **Source Sheet**: `RITES/BLD/STR/TD/HOUSING(G+6)/101` (`Tender_drawing_3`, Page 17)
- **Sheet Title**: `PILE CAP LAYOUT PLAN AND REINFORCEMENT DETAILS`
- **Scope to Transcribe**:
  - Count and map every physical cap outline entity (resolve the 54 drawn entities vs. 84 summary count).
  - Cap marks (PC1, PC2, PC3, PC4, combined strip caps).
  - Plan dimensions: length, width, and indicated depth.
  - Number of piles enclosed per cap.
  - Reinforcement details (bottom mesh, top mesh, side links, embedment).
- **Output File**: `10_Controlled_Transcription/controlled_pile_cap_register.csv`

---

### Priority B — Superstructure Structural Frame (Target: Member-by-Member Schedules)

#### Step B.1: Sheets 103 & 104 Transcription (Columns & Shear Walls)
- **Source Sheets**: 
  - `RITES/BLD/STR/TD/HOUSING(G+6)/103` (`Tender_drawing_3`, Page 19 — Layout)
  - `RITES/BLD/STR/TD/HOUSING(G+6)/104` (`Tender_drawing_3`, Page 20 — Reinforcement Details)
- **Scope to Transcribe**:
  - 16 framed columns: C1 (1200×350), C2 (1200×300), C3 (1200×300) with exact vertical rebar bar marks and ties.
  - 33 shear walls: SW1–SW5 and Core Walls SW6–SW10 (CW1) with boundary element detailing.
  - Vertical lift heights per floor level (Stilt to Terrace).
- **Output File**: `10_Controlled_Transcription/controlled_column_wall_register.csv`

#### Step B.2: Sheets 105 & 106 Transcription (Plinth Beams)
- **Source Sheets**: 
  - `RITES/BLD/STR/TD/HOUSING(G+6)/105` (`Tender_drawing_3`, Page 21 — Plinth Framing)
  - `RITES/BLD/STR/TD/HOUSING(G+6)/106` (`Tender_drawing_3`, Page 22 — Reinforcement Details)
- **Scope to Transcribe**:
  - Plinth beams PB1 to PB34 and tie beams TB1–TB2.
  - Span length between column/wall faces (clear span).
  - Web dimensions (width × overall depth).
  - Main top bars, bottom bars, extra top bars at supports, and stirrup spacing zones.
- **Output File**: `10_Controlled_Transcription/controlled_beam_register.csv` (Plinth subset)

#### Step B.3: Sheets 107 & 108 Transcription (Floor Beams & Slabs)
- **Source Sheets**: 
  - `RITES/BLD/STR/TD/HOUSING(G+6)/107` (`Tender_drawing_3`, Page 23 — Typical Framing & Slab Schedule)
  - `RITES/BLD/STR/TD/HOUSING(G+6)/108` (`Tender_drawing_3`, Page 24 — Typical Beam Reinforcement)
- **Scope to Transcribe**:
  - Floor beams B1 to B34 per typical floor level.
  - Floor slabs S1, S2, and balcony slabs: panel dimensions, boundary conditions (two-way/one-way), slab thickness (125 mm), and top/bottom mesh spacing.
- **Output Files**:
  - `10_Controlled_Transcription/controlled_beam_register.csv` (Floor beam subset)
  - `10_Controlled_Transcription/controlled_slab_register.csv`

#### Step B.4: Sheets 109 & 110 Transcription (Staircase, Mumty & OHT)
- **Source Sheets**:
  - `RITES/BLD/STR/TD/HOUSING(G+6)/109` (`Tender_drawing_3`, Page 25 — Mumty & Tank Level)
  - `RITES/BLD/STR/TD/HOUSING(G+6)/110` (`Tender_drawing_3`, Page 26 — Staircase Details)
- **Scope to Transcribe**:
  - Staircase: flight width (1.50 m), tread (300 mm), riser (150 mm), waist slab (150 mm), landing beams.
  - Mumty: roof slab (125 mm), framing beams.
  - OHT: footprint dimensions, capacity (40 kL), verified vs. assumed wall/base thickness.
- **Output File**: `10_Controlled_Transcription/controlled_stair_oht_register.csv`

---

### Priority C — Architectural Quantities (Target: Room-by-Room Quantities)

#### Step C.1: Sheet 005 Transcription (Openings & Schedules)
- **Source Sheet**: `RITES/BLD/AR/TD/005` (`Tender_drawing_5`, Page 5)
- **Scope to Transcribe**:
  - Door schedule: D1, D2, D3, DW1, DW2, SD1–SD4 (width, height, count per floor, material, frame specification).
  - Window & ventilator schedule: W1–W4, V1–V2 (width, height, sill level, lintel level, count).
- **Output File**: `10_Controlled_Transcription/controlled_opening_register.csv`

#### Step C.2: Sheets 006 & 007 Transcription (Floor Plans & Room Geometry)
- **Source Sheets**: `RITES/BLD/AR/TD/006`, `007` (`Tender_drawing_1` & `2`)
- **Scope to Transcribe**:
  - Room schedule: Living/Dining, Bedroom 1, Bedroom 2, Kitchen, Toilet 1, Toilet 2, Balconies, Corridor.
  - Internal clear room dimensions (L × W) and floor-to-ceiling heights.
  - Wall perimeter per room (for skirting and plaster calculation).
- **Output File**: `10_Controlled_Transcription/controlled_room_register.csv`

#### Step C.3: Sheets 016, 017, 018 Transcription (Finishes Schedule)
- **Source Sheets**: `RITES/BLD/AR/TD/016`, `017`, `018` (`Schedule_of_Finishes`)
- **Scope to Transcribe**:
  - Floor finish specifications mapped room-by-room (Vitrified, Anti-skid ceramic, Kota, VDF).
  - Wall dado heights (toilets 2100 mm, kitchen 600 mm above counter).
  - Ceiling finishes and painting specifications.
- **Output File**: `10_Controlled_Transcription/controlled_finish_register.csv`

#### Step C.4: Wall Deductions Calculation Table
- **Scope to Transcribe**:
  - Room-by-room and external wall-by-wall opening deductions mapping exact door/window IDs to wall segments.
- **Output File**: `10_Controlled_Transcription/controlled_masonry_deduction_register.csv`

---

## 3. Verification Protocol for Completed Registers

Upon completion of each controlled transcription file:
1. Re-verify row count against sheet schedule total.
2. Cross-check sum of room areas against official plinth area (3,419.38 sq.m).
3. Confirm `confidence` is assigned strictly per provenance (`DIRECT_SHEET_OBSERVATION`, `MEDIUM`, `ESTIMATED`, `ASSUMPTION_REQUIRED`).
4. Keep the register version-controlled in `10_Controlled_Transcription/`.

