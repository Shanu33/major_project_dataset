# Priority F — Controlled Sample Quantity Execution Log

**Project**: OIL/RITES Duliajan BQ Workmen Housing Complex  
**Tender No.**: RITES/NERPO/OIL/BQ-HOUSING/25  
**Scope Unit**: One typical Stilt+6 BQ Workmen Housing residential tower  
**Target Folder**: `10_Controlled_Transcription/priority_f_sample_quantity_execution/`  
**Stage**: Priority F — Controlled Sample Quantity Execution (Proof of Method)  
**Status**: `PRIORITY_F_SAMPLE_EXECUTION_COMPLETE_FULL_TAKEOFF_BLOCKED`  
**Dataset Readiness**: `DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`  

---

## 1. Scope

This document records a strictly controlled, limited **proof-of-method sample calculation pass** for the typical Stilt+6 BQ residential housing tower.

The objective of Priority F is to demonstrate that directly observed drawing dimensions can be converted into auditable micro-quantities through basic geometry, while rigorously enforcing mathematical and civil engineering guardrails that prevent premature full-tower takeoff.

### Mandatory Dataset Disclaimers:
- **Only micro-sample quantities were calculated** (individual opening areas, single-room floor areas and perimeters, and reference floor finish traces).
- **No full project quantities were calculated**.
- **No full tower quantities were calculated**.
- **No costs were calculated** (`Cost accuracy: NOT_CALCULATED`).
- **No BOQ validation was performed** (`Quantity accuracy: NOT_CALCULATED`).
- **No labour or duration modelling was performed** (`Labour/Duration: BLOCKED`).
- **No synthetic deduction percentages were used** (the legacy 23% external and 10% internal deduction ratios remain strictly excluded).
- **No 24-flat or tower multiplication was applied** (all calculations are limited to single-unit or single-opening scopes).
- **No RCC, rebar, foundation, OHT wall, masonry, plaster, or external finish final quantity was calculated**.
- **Dataset Readiness**: The project strictly remains **`DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`**.
- **The project must NOT be marked `READY_FOR_TAKEOFF`**.

---

## 2. Source Files Reviewed

The sample calculations and audit trails were executed from the following verified registers:
1. `controlled_opening_register.csv` (15 scheduled opening marks)
2. `controlled_room_register.csv` (14 room/core spaces)
3. `controlled_finish_register.csv` (10 finish specifications FIN-01 to FIN-10)
4. `controlled_masonry_deduction_register.csv` (15 opening deduction geometries)
5. Priority E setup files: `quantity_formula_master_index.csv`, `opening_quantity_formula_map.csv`, `finish_quantity_formula_map.csv`, `formula_input_dependency_register.csv`, `blocked_formula_reason_register.csv`, and `priority_e_formula_setup_log.md`.

---

## 3. Sample Calculations Performed

Three categories of micro-samples were executed across 18 auditable items:

### A. Sample Opening Area Calculations (5 Selected Marks)
- `D1` (Toilet Door): $0.800\text{ m} \times 2.100\text{ m} = \mathbf{1.680\text{ m}^2}$ (`SAMPLE_EXECUTED_TRACEABLE`)
- `W1` (Bedroom Window): $1.200\text{ m} \times 1.200\text{ m} = \mathbf{1.440\text{ m}^2}$ (`SAMPLE_EXECUTED_TRACEABLE`)
- `DW1` (Door-Window Combination): $2.000\text{ m} \times 2.100\text{ m} = \mathbf{4.200\text{ m}^2}$ (`SAMPLE_EXECUTED_TRACEABLE`)
- `V1` (Attached Toilet Ventilator): $0.515\text{ m} \times 0.875\text{ m} = \mathbf{0.451\text{ m}^2}$ ($0.450625\text{ m}^2$) (`SAMPLE_EXECUTED_TRACEABLE`)
- `SD1` (Electrical Shaft Service Door): $0.900\text{ m} \times 2.100\text{ m} = \mathbf{1.890\text{ m}^2}$ (`SAMPLE_EXECUTED_TRACEABLE`)

### B. Sample Room Area and Perimeter Calculations (5 Selected Rooms)
- `Living / Dining`: $5.520\text{ m} \times 3.970\text{ m} = \mathbf{21.914\text{ m}^2}$; Perimeter $= 2 \times (5.520 + 3.970) = \mathbf{18.980\text{ m}}$ (`SAMPLE_EXECUTED_TRACEABLE`)
- `Master Bedroom`: $3.845\text{ m} \times 3.220\text{ m} = \mathbf{12.381\text{ m}^2}$; Perimeter $= 2 \times (3.845 + 3.220) = \mathbf{14.130\text{ m}}$ (`SAMPLE_EXECUTED_TRACEABLE`)
- `Kitchen`: $2.580\text{ m} \times 2.440\text{ m} = \mathbf{6.295\text{ m}^2}$; Perimeter $= 2 \times (2.580 + 2.440) = \mathbf{10.040\text{ m}}$ (`SAMPLE_EXECUTED_TRACEABLE`)
- `Attached Toilet`: $2.700\text{ m} \times 1.400\text{ m} = \mathbf{3.780\text{ m}^2}$; Perimeter $= 2 \times (2.700 + 1.400) = \mathbf{8.200\text{ m}}$ (`SAMPLE_EXECUTED_TRACEABLE`)
- `Living Balcony`: $2.280\text{ m} \times 1.365\text{ m} = \mathbf{3.112\text{ m}^2}$; Perimeter $= 2 \times (2.280 + 1.365) = \mathbf{7.290\text{ m}}$ (`SAMPLE_EXECUTED_TRACEABLE`)

### C. Sample Finish Area Traces (Single-Room Reference Only)
- `Living / Dining` (FIN-01 Polished Vitrified Tile): Single room basis $= \mathbf{21.914\text{ m}^2}$ (`REFERENCE_ONLY`, `BLOCKED_FULL_TAKEOFF`)
- `Kitchen` (FIN-03 Anti-skid Vitrified Tile): Single room basis $= \mathbf{6.295\text{ m}^2}$ (`REFERENCE_ONLY`, `BLOCKED_FULL_TAKEOFF`)
- `Attached Toilet` (FIN-04 Ceramic Floor Tile): Single room basis $= \mathbf{3.780\text{ m}^2}$ (`REFERENCE_ONLY`, `BLOCKED_FULL_TAKEOFF`)

---

## 4. Why These Samples Were Allowed

These calculations were approved for proof-of-method execution because:
1. **Direct Input Visibility**: Every input parameter (width, height, clear length, clear width) is visibly printed on approved tender sheet `AR/TD/005`.
2. **Deterministic Geometric Operations**: The calculations involve strictly 2D rectangle geometry ($W \times H$, $L \times W$, $2(L+W)$) without assumptions, interpolations, or code derivations.
3. **Absence of Aggregation**: Each sample represents a single opening unit or a single room inside one residential flat, without relying on floor counts, tower multipliers, or deduction percentages.

---

## 5. What Was Not Calculated

The following categories were strictly withheld:
- **Zero Masonry Quantities**: No gross wall area, net wall area, or brickwork volume ($m^3$) was computed.
- **Zero Structural Concrete Quantities**: No column, shear wall, beam, slab, or staircase concrete volume ($m^3$) was computed.
- **Zero Reinforcement Steel Tonnage**: No rebar weight ($MT$) was calculated.
- **Zero Substructure Quantities**: No pile concrete volume, pile rebar, or pile cap volume was computed.
- **Zero OHT Wall Quantities**: OHT wall volume remains $0.0\text{ m}^3$ (wall thickness is missing from Sheet 109).
- **Zero Finishes Takeoff**: No multi-room plaster, external paint, or flooring takeoffs were generated.
- **Zero Costs & Valuations**: No currency amounts or tender rates were applied.

---

## 6. Why Full Takeoff Is Still Blocked

Full takeoff cannot proceed because:
1. **Unresolved Structural Block-outs**: Masonry wall lengths cannot be derived from room perimeters without subtracting column widths ($300\text{ mm}$) and shear wall panels ($1260\text{ mm}$ to $5030\text{ mm}$).
2. **Variable Clear Beam Heights**: Varying beam drops ($450\text{ mm}$ vs $600\text{ mm}$) create variable clear wall heights ($2450\text{ mm}$ to $2925\text{ mm}$) that prevent uniform height modeling.
3. **Unscheduled Opening Counts**: Sheet `AR/TD/005` schedule provides dimensions but omits counts per flat and per floor.
4. **Missing Official BBS**: Reinforcement cut lengths, lap locations, and hooks are missing from structural sheets.
5. **Foundation Contradictions**: Contradiction between 54 visible layout cap entities and 84 scheduled caps, with 91 piles unallocated under strip caps.
6. **Missing OHT Wall Detail**: Tank wall thickness is `NOT_VISIBLE_ON_SHEET_109` / `ASSUMPTION_REQUIRED`.

---

## 7. Confirmation of Guardrails

| Guardrail Parameter | Verified State | Enforced Action |
| :--- | :---: | :--- |
| `READY_FOR_TAKEOFF` Labels | **0 Active** | Prevented certification of unverified takeoff |
| `HIGH_CONFIDENCE` Assumption Labels | **0 Active** | Only direct observations and basic geometry allowed |
| Synthetic Deduction Percentages (23% / 10%) | **0 Active** | Fully excluded from all matrices |
| Tower-Level Multipliers (24 Flats / 6 Floors) | **0 Applied** | All calculations confined to single-unit scopes |
| Cost Accuracy Reporting | **NOT_CALCULATED** | Precluded reporting against non-existent BOQ ground truth |
| Quantity Accuracy Reporting | **NOT_CALCULATED** | Precluded reporting against non-existent ground truth |
| Labour / Duration Modelling | **BLOCKED** | Retained strictly as blocked dependency |

---

## 8. Recommended Next Step

**Recommended Next Step**: **Priority G — Building Services (MEP) Controlled Transcription & Equipment Register Setup**.  
Transcribe directly visible equipment schedules, pipe runs, fixture counts, electrical distribution boards, and fire protection risers from the 18 Building Services drawing sheets (`Tender_drawing_4_Sections_StructuralCommunity_MEP_pdf-2025-Aug-28-17-39-32.pdf`, Sheets `MEP/001` to `MEP/018`) to complete all discipline-level transcriptions.

