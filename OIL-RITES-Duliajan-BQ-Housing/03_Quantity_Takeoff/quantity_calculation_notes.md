# Civil Engineering Quantity Takeoff & Audit Notes

## 1. Executive Summary & Geometry Foundation
This material quantity takeoff models **ONE typical Stilt+6 Residential Workmen Housing Tower** for the OIL/RITES Duliajan Workmen Housing Complex (`Tender Ref: RITES/NERPO/OIL/BQ-HOUSING/25`).

### Truth Disclosure Statement
- **Contract Type**: EPC Mode-II (Lump Sum Component Basis).
- **Official BOQ Status**: The tender price schedule contains **NO itemized construction bill of quantities** for materials.
- **Quantity Validation Coverage**: **0%**.
- **Quantity Accuracy**: **NOT CALCULATED** (no independent itemized BOQ available for selected tower scope).
- **Cost Accuracy**: **NOT CALCULATED** (no official itemized priced BOQ available).
- **Audit Classification**: All material quantities are **drawing-based engineering estimates requiring reconciliation**.
- **Tender Scope Concordance (`scope_consistency_check = PASS`)**:
  - Allocated Tower Plinth Area: **3,419.38 sq.m** (Item 1.01: 27,355 sq.m ÷ 8).
  - Dwelling Units: **24 units** (Type-2BHK, 4 units/floor × 6 floors).
  - Vertical Storey Profile: **Stilt + 6 storeys**.
  - Tower Count: 1 of 8 identical towers.

### Master Reconciled Volume & Weight Totals
- **RCC Concrete Volume (M30)**: **2,617.55 m³** (Substructure: 1,346.55 m³, Superstructure: 1,271.00 m³).
- **PCC Lean Concrete Volume (M10)**: **18.00 m³** (under pile caps and plinth trenches).
- **Total Combined Concrete (RCC + PCC)**: **2,635.55 m³**.
- **Total Reinforcement Steel (Fe 500D)**: **300.85 MT** (Substructure: 128.74 MT, Superstructure: 172.11 MT).
- **Overall Steel / Concrete Ratio**: **114.94 kg/m³** (Superstructure: **135.41 kg/m³**).
- **Steel Intensity**: **87.98 kg/sq.m** of plinth area.
- **Concrete Intensity (RCC)**: **0.766 m³/sq.m** of plinth area (Superstructure: **0.372 m³/sq.m**).

---

## 2. Reconciled Contradictions & Audit Findings

### 2.1 Foundation Pile Caps: 54 Caps vs 84 Caps Contradiction
- **Layout Count (Sheet 101)**: Plan layout indicates **54 cap entities**:
  - PC-1 (1-pile): 8 caps (8 piles) = 11.52 m³
  - PC-2 (2-pile): 24 caps (48 piles) = 69.12 m³
  - PC-3 (3-pile): 12 caps (36 piles) = 48.00 m³
  - PC-4 (4-pile): 6 caps (24 piles) = 43.74 m³
  - PC-W (Strip caps under shear walls): 4 strips = 36.00 m³
  - *Calculated Layout Volume*: **208.38 m³** (accounting for 116 discrete piles + strip caps).
- **Preliminary Takeoff Summary**: Claimed **84 caps** totaling **185.00 m³**.
- **Unresolved Pile Allocation**: The 54 layout caps account for only 116 piles out of the 207 total piles counted on Sheet 100, leaving **91 piles unaccounted for** under strip caps. Four 6.0m strip caps cannot physically accommodate 91 piles (22.75 piles/cap).
- **Audit Classification**: **UNRESOLVED_CONTRADICTION** / **ASSUMPTION_REQUIRED**. Cap depth (1.0m) and pile allocation require official foundation schedule drawings.

### 2.2 Beam Length: 403.5 m Grid Run vs 420.0 m Legacy Approximation
- **Grid-Derived Length**: Sum of longitudinal grid lines (6 × 30.08m = 180.48m) and transverse grid lines (14 × 16.08m = 225.12m) = **403.50 m per floor**.
- **Legacy Figure**: 420.0 m was an unverified rounded multiplier arbitrarily paired with 0.115 m² section.
- **Reconciliation**: Standardized on **403.50 m per floor** across all schedules.
- **Audit Classification**: **ESTIMATED** (uses assumed weighted average cross-section 0.1197 m²).

### 2.3 Stilt Grade Slab: 438.00 m² Net Area vs 483.60 m² Gross Footprint
- **Gross Footprint**: 30.08 m × 16.08 m = **483.60 sq.m**.
- **Net Interior Slab Area**: Gross area minus column/wall footprints and plumbing voids = **438.00 sq.m**.
- **Volume Reconciled**:
  - Uniform 125mm slab on 438.00 m² net area = **54.75 m³**.
  - The preliminary 60.45 m³ figure was mathematically forced by applying 125mm to gross footprint (483.60 × 0.125 = 60.45 m³) or by assuming an unmeasured 5.70 m³ edge thickening allowance.
- **Audit Classification**: **ASSUMPTION_REQUIRED** for edge thickening allowance.

### 2.4 Suspended Slab: 424.96 m² Net Area vs 428.00 m² Rounded Area & 125mm vs 130mm Thickness
- **Net Floor Slab Area**: Gross footprint (483.60 m²) minus measured core voids (58.64 m² for staircases, lift shafts, and plumbing ducts) = **424.96 sq.m per floor**. (428.00 m² was a rounded figure).
- **Thickness Reconciled**: Sheet 107 schedules base slab S1 as 125 mm and sunken wet-area slab S2 as 150 mm. The 130 mm figure represents an assumed weighted average, not a single sheet schedule.
- **Audit Classification**: **ESTIMATED** (uses assumed weighted average thickness across 6 repeated floors).

---

## 3. Mathematical Takeoff by Engineering Trade

### 3.1 Substructure Works
1. **Bored Cast-in-Situ RCC Piles**:
   - Count: Exactly **207 piles** per tower, directly counted on `STR/TD/HOUSING(G+6)/100` (Sheet 100).
   - Diameter: \(D = 600\text{ mm} = 0.60\text{ m}\). Cross-sectional area \(A = \frac{\pi \times 0.6^2}{4} = 0.28274\text{ m}^2\).
   - Length: Assumed \(L = 18.0\text{ m}\) based on DBR p.35 and Geotechnical Report recommendation of 15–20m (ASM-001).
   - Volume: \(207 \times 0.28274\text{ m}^2 \times 18.0\text{ m} = \mathbf{1,053.49\text{ m}^3}\) (M30) (`ESTIMATED`).
   - Rebar: Assumed 8-T20 cage + T10 spiral ties (\(94.2\text{ kg/m}^3\)) = \(\mathbf{99.24\text{ MT}}\) (`ESTIMATED`).
2. **PCC Lean Concrete (1:5:10)**:
   - Assumed 75mm leveling layer under caps and plinth trenches = \(\mathbf{18.00\text{ m}^3}\) (M10) (`ESTIMATED`).
3. **Plinth Beams (PB1 to PB34)**:
   - Reconciled length = 403.5 m. Weighted average cross section = 0.118 m². Volume = \(\mathbf{47.61\text{ m}^3}\) (M30) (`ESTIMATED`). Steel (assumed 135 kg/m³) = \(\mathbf{6.43\text{ MT}}\) (`ESTIMATED`).

### 3.2 Superstructure Works
1. **Vertical Frame (Columns & Shear Walls)**:
   - **Columns C1** (4 nos, \(1200\times 350\)): \(1.68\text{ m}^2 \times 21.0\text{ m} = \mathbf{35.28\text{ m}^3}\). Steel: 14-T32 + 8-T25 = \(\mathbf{25.68\text{ MT}}\) (`MEDIUM`).
   - **Columns C2** (8 nos, \(1200\times 300\)): \(2.88\text{ m}^2 \times 21.0\text{ m} = \mathbf{60.48\text{ m}^3}\). Steel: 22-T25 = \(\mathbf{18.45\text{ MT}}\) (`MEDIUM`).
   - **Columns C3** (4 nos, \(1200\times 300\)): \(1.44\text{ m}^2 \times 21.0\text{ m} = \mathbf{30.24\text{ m}^3}\). Steel: 22-T20 = \(\mathbf{8.28\text{ MT}}\) (`MEDIUM`).
   - **Shear Walls SW1 to SW5** (28 wall legs, \(230\text{ mm}\) thick): \(13.57\text{ m}^2 \times 21.0\text{ m} = \mathbf{282.36\text{ m}^3}\). Steel = \(\mathbf{26.38\text{ MT}}\) (`MEDIUM`).
   - **Core Shear Walls SW6 to SW10** (13.89m run, \(230\text{ mm}\) thick): \(3.19\text{ m}^2 \times 21.0\text{ m} = \mathbf{67.09\text{ m}^3}\). Steel = \(\mathbf{3.74\text{ MT}}\) (`MEDIUM`).
   - **Mumty Columns & Pedestals**: \(\mathbf{6.74\text{ m}^3}\). Steel = \(\mathbf{0.58\text{ MT}}\) (`MEDIUM`).
2. **Floor & Terrace Beams**:
   - Reconciled length = 403.5 m per level × 7 levels = 2,824.5 m. Weighted cross section = 0.1197 m².
   - Volume = \(\mathbf{338.10\text{ m}^3}\) (M30) (`ESTIMATED`). Steel (assumed 140 kg/m³) = \(\mathbf{47.33\text{ MT}}\) (`ESTIMATED`).
3. **Floor & Terrace Slabs**:
   - Reconciled net slab area = 424.96 m² per level. Assumed 130mm weighted thickness.
   - Floors 1-6 = \(424.96 \times 0.130 \times 6 = \mathbf{331.47\text{ m}^3}\). Terrace = \(\mathbf{55.24\text{ m}^3}\).
   - Balconies & Chajjas = \(\mathbf{20.02\text{ m}^3}\). Total Slabs = \(\mathbf{406.73\text{ m}^3}\) (`ESTIMATED`). Steel = \(\mathbf{36.69\text{ MT}}\) (`ESTIMATED`).
4. **Staircases & Overhead Water Tank**:
   - Staircases (2 doglegged cores, 28 flights) = \(\mathbf{26.60\text{ m}^3}\). Steel = \(\mathbf{2.92\text{ MT}}\) (`MEDIUM`).
   - Overhead Water Tank (OHT) = \(\mathbf{16.50\text{ m}^3}\). Steel = \(\mathbf{1.98\text{ MT}}\) (`ASSUMPTION_REQUIRED`).

### 3.3 Masonry, Finishes & Openings
- **Brick Masonry**: External 230mm (\(216.80\text{ m}^3\)) + Internal 115mm (\(406.85\text{ m}^3\)) = \(\mathbf{623.65\text{ m}^3}\) (`ESTIMATED`).
- **Cement Plaster**: Internal 12mm (\(11,450\text{ m}^2\)) + External 18mm (\(3,400\text{ m}^2\)) = \(\mathbf{14,850\text{ m}^2}\) (`ESTIMATED`).
- **Flooring & Tiling**: Vitrified (\(1,848\text{ m}^2\)) + Ceramic (\(372\text{ m}^2\)) + Kota Stone (\(480\text{ m}^2\)) = \(\mathbf{2,700\text{ m}^2}\) (`ESTIMATED`).
- **Scheduled Openings**: 216 Flush Doors + 168 Windows/Ventilators = **384 scheduled assemblies** (`HIGH`).
