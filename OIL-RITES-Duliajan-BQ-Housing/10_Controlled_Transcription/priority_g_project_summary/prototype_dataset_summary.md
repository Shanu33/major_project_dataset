# Prototype Dataset Summary Report: OIL-RITES Duliajan BQ Housing Pilot

**Project Name**: OIL India Residential Housing Complex (Workmen BQ Towers), Duliajan, Assam  
**Tender Reference**: RITES/NERPO/OIL/BQ-HOUSING/25  
**Selected Scope**: One typical Stilt+6 BQ Workmen Housing Residential Tower  
**Target Repository**: `10_Controlled_Transcription/`  
**Stage**: Priority G — Prototype Dataset Summary & Architecture Synthesis  
**Stage Status**: `PRIORITY_G_PROJECT_SUMMARY_COMPLETE`  
**Dataset Readiness**: `DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`  

---

## 1. Executive Statement & Mandatory Disclaimers

> [!IMPORTANT]
> - **This is a controlled prototype dataset, not a full quantity estimate.**
> - **The system strictly separates direct evidence, derived geometry, assumptions, and blocked items.**
> - **BOQ and cost validation were not performed because an itemized official priced BOQ is not available.**
> - **The project is NOT `READY_FOR_TAKEOFF`.**
> - **The current readiness strictly remains `DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`.**

No final material quantities (concrete $m^3$, steel $MT$, brickwork $m^3$, plaster/paint $m^2$), financial costs, labour models, or construction schedules have been generated. All calculations performed in this dataset are limited to verified micro-samples serving as proofs of method.

---

## 2. Project Selection & Context

The OIL/RITES Duliajan BQ Housing project was selected as the flagship pilot dataset for developing an agentic, evidence-grounded construction intelligence platform:
- **Real-World Public Sector Infrastructure**: An actual Oil India Limited (OIL) EPC project engineered by RITES Ltd., reflecting authentic Indian standard practice (IS 456, IS 13920, IS 1893 Seismic Zone V, CPWD specifications).
- **Comprehensive Tender Drawing Repository**: 55 approved tender drawing sheets covering all civil, structural, architectural, and building services trades for the typical housing block.
- **Reproducible Unit Architecture**: Stilt+6 configuration with 4 identical residential flats per floor (24 flats total) and central core, allowing evaluation of spatial repetition and element hierarchy without mixing synthetic datasets.

---

## 3. Document Repository & Available Records

The pilot dataset is grounded exclusively in officially available project records:
1. **Architectural Drawings (26 Sheets)**: Site layout, typical unit plans (`AR/TD/005`), stilt floor (`006`), typical 1st–6th floor (`007`), terrace plan (`008`), mumty & OHT plan (`009`), elevations (`010`, `011`), sections (`012`, `013`), door/window schedules & details (`014`, `015`), and floor/toilet finish layouts (`016` to `025`).
2. **Structural Drawings (11 Tower Sheets)**: Pile layout plan (`STR/TD/100`), pile cap layout (`101`), typical detailing (`102`), column layout (`103`), column reinforcement (`104`), plinth beams (`105`, `106`), floor beams & slabs (`107`, `108`), mumty & water tank bottom (`109`), staircase details (`110`).
3. **Building Services Drawings (18 Sheets)**: Plumbing, sanitary, electrical, and fire protection sheets (`MEP/001` to `MEP/018`).
4. **Engineering Reports & Award Metadata**: Design Basis Report (DBR) excerpts, geotechnical investigation notes, and the official RITES December 2025 tender dealt record confirming contract award to Badri Rai & Co. at ₹128.14 Crore (excl. GST) with a 24-month contract duration.

---

## 4. Completed Dataset Stages

The dataset has progressed through seven rigorous, sequential control stages:
- **Phase 0 — Project Control & Boundary Locking**: Fixed single-tower boundary, locked baseline metadata, eliminated historical contradictions (superseded media ₹157.25 Cr / 36-month claims), and established audit trails.
- **Priority A — Foundation Controlled Transcription**: Transcribed 207 piles (600mm dia) and documented unresolved substructure contradictions (54 visible cap entities vs 84 scheduled caps; 91 piles unallocated).
- **Priority B — Structural Frame Controlled Transcription**: Transcribed columns C1–C3, shear walls SW1–SW10, plinth beams PB1–PB34, typical floor beams B1–B34, suspended slabs S1–S2 (125mm), stairs, and OHT bottom slab (150mm).
- **Priority C — Architectural & Finishes Controlled Transcription**: Transcribed 15 opening types (D1–D3, DW1–DW2, SD1–SD4, W1–W4, V1–V2), 14 room/core dimensions, 10 finish specifications (FIN-01 to FIN-10), and opening deduction geometries.
- **Priority D — Civil Cross-Register Reconciliation**: Established vertical storey profiles (3.05m floor-to-floor), resolved lift shaft as RC shear wall (zero masonry), and logged 11 cross-discipline discrepancies.
- **Priority E — Controlled Quantity Formula Setup**: Defined 18 formula groups, 14 masonry wall zones, 16 concrete formulas, 15 schedule-based rebar formulas, and 17 input dependencies, locking all into `FORMULA_DEFINED_INPUTS_BLOCKED`.
- **Priority F — Controlled Sample Quantity Execution**: Successfully executed 18 auditable micro-samples (5 opening areas, 5 room floor areas, 5 room perimeters, 3 finish traces) with a complete row-by-row audit trail while enforcing takeoff blocks.

---

## 5. What Was Transcribed & Reconciled

### A. Transcribed Registers (10 Core Files)
1. `controlled_pile_register.csv` (11 rows)
2. `controlled_pile_cap_register.csv` (11 rows)
3. `controlled_column_wall_register.csv` (13 rows)
4. `controlled_beam_register.csv` (44 rows)
5. `controlled_slab_register.csv` (7 rows)
6. `controlled_stair_oht_register.csv` (7 rows)
7. `controlled_opening_register.csv` (15 rows)
8. `controlled_room_register.csv` (14 rows)
9. `controlled_finish_register.csv` (10 rows)
10. `controlled_masonry_deduction_register.csv` (15 rows)

### B. Reconciled Linkages
- **Vertical Storey & Structural Height**: Architectural floor-to-floor height ($3.05\text{ m}$) from Sections A-A and B-B mapped across structural framing; member height strictly categorized as `ARCHITECTURAL_SECTION_DERIVED` (not on Sheet 104).
- **Core Wall Resolution**: Lift shaft enclosure formally established as reinforced concrete shear wall structure (`SW9`/`SW10` / `CW1`, 250mm thick) governed by Sheet 103; masonry takeoff set to zero to prevent double-counting.
- **Opening Deductions**: Every scheduled opening mark linked to host wall thickness ($230\text{ mm}$ external perimeter vs $115\text{ mm}$ internal partitions) and geometric deduction area ($W \times H$).
- **Spatial Finish Mapping**: Room dimensions traced directly to finish codes (`FIN-01` to `FIN-10`).
- **OHT Bottom Slab**: Directly observed as $150\text{ mm}$ with scheduled rebar on Sheet 109; OHT wall thickness marked missing.

---

## 6. Sample Calculations Safely Executed (Proof of Method)

All calculations are strictly isolated to single-unit scopes:
- **Opening Unit Areas**:
  - `D1` (Toilet Door, $0.800 \times 2.100\text{ m}$): $\mathbf{1.680\text{ m}^2}$
  - `W1` (Bedroom Window, $1.200 \times 1.200\text{ m}$): $\mathbf{1.440\text{ m}^2}$
  - `DW1` (Balcony Opening, $2.000 \times 2.100\text{ m}$): $\mathbf{4.200\text{ m}^2}$
  - `V1` (Toilet Ventilator, $0.515 \times 0.875\text{ m}$): $\mathbf{0.451\text{ m}^2}$
  - `SD1` (Service Door, $0.900 \times 2.100\text{ m}$): $\mathbf{1.890\text{ m}^2}$
- **Room Floor Areas & Perimeters (Single Flat Basis)**:
  - `Living / Dining` ($5.520 \times 3.970\text{ m}$): Floor Area $= \mathbf{21.914\text{ m}^2}$; Perimeter $= \mathbf{18.980\text{ m}}$
  - `Master Bedroom` ($3.845 \times 3.220\text{ m}$): Floor Area $= \mathbf{12.381\text{ m}^2}$; Perimeter $= \mathbf{14.130\text{ m}}$
  - `Kitchen` ($2.580 \times 2.440\text{ m}$): Floor Area $= \mathbf{6.295\text{ m}^2}$; Perimeter $= \mathbf{10.040\text{ m}}$
  - `Attached Toilet` ($2.700 \times 1.400\text{ m}$): Floor Area $= \mathbf{3.780\text{ m}^2}$; Perimeter $= \mathbf{8.200\text{ m}}$
  - `Living Balcony` ($2.280 \times 1.365\text{ m}$): Floor Area $= \mathbf{3.112\text{ m}^2}$; Perimeter $= \mathbf{7.290\text{ m}}$
- **Finish Traces**: Traced verified room areas to `FIN-01`, `FIN-03`, `FIN-04` for single rooms without executing multi-room aggregation.

---

## 7. What Remains Blocked & Why

Full quantity takeoff across all major trades remains strictly blocked due to missing drawing evidence:
1. **Masonry Brickwork ($m^3$)**: Blocked pending wall centerline layout plan that subtracts column faces ($300\text{ mm}$) and shear wall panels ($1260\text{ mm}$ to $5030\text{ mm}$), and reconciles bay-by-bay clear wall heights under variable beam drops ($450\text{ mm}$ vs $600\text{ mm}$).
2. **Structural Concrete ($m^3$)**: Blocked pending structural column elevation schedule, net slab panel coordinates (excluding beam web widths), and beam-column joint deduplication.
3. **Reinforcement Steel ($MT$)**: Strictly blocked across all trades due to the absence of an engineer-approved Bar Bending Schedule (BBS) specifying cut lengths, lap positions, and hook geometry.
4. **Substructure Foundation Concrete & Rebar**: Blocked due to the 54 vs 84 pile cap entity contradiction, 91 unallocated piles under strip caps, and unscheduled pile termination depths.
5. **Overhead Water Tank (OHT) Walls**: Blocked because tank wall thickness is `NOT_VISIBLE_ON_SHEET_109` and wall rebar is `NOT_SCHEDULED`.
6. **Finishes Takeoff ($m^2$)**: Multi-unit flooring, plaster, and paint blocked pending opening counts per unit and elevation surface envelope compilation.
7. **Cost Validation & BOQ Comparison**: Blocked because no itemized priced or unpriced BOQ exists for a single typical housing tower.

---

## 8. Final Readiness Status

**`DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`**  
*(Active `READY_FOR_TAKEOFF` labels: **0** | Active `HIGH_CONFIDENCE` assumption labels: **0**)*

