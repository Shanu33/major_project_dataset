# Selected Tower Scope Lock Specification

## 1. Selected Unit of Analysis
- **Selected Entity**: Exactly ONE Typical Stilt+6 Residential Workmen Housing Tower (Designation: BQ Workmen Housing Tower Block A-H typical).
- **Project Context**: The overall tender encompasses 8 identical Stilt+6 residential towers (total 192 flats, 27,355 sq.m plinth area). To enable precise, reproducible civil engineering quantity estimation and benchmark validation, this dataset isolates and models **one typical tower** end-to-end.
- **Mathematical Allocation Factor**: Exactly 1/8 (12.500%) of BOQ Item 1.01.

## 2. Tower Configuration & Architectural Scope
- **Building Height**: Stilt Floor (Level 0.00 to +3.00 m) + 6 Residential Floors (+3.00 m to +21.30 m) + Mumty/Lift Machine Room (+21.30 m to +24.00 m). Total architectural height = 24.00 m above plinth.
- **Gross Footprint**: 30.08 m length × 16.08 m width = 483.60 sq.m at stilt and typical floor levels.
- **Plinth / Built-up Area Breakdown**:
  - Stilt Floor (Covered Parking, Ramps, Core, Electrical & LV Shafts): 483.60 sq.m
  - 1st to 6th Typical Residential Floors: 6 floors × 483.60 sq.m = 2,901.60 sq.m
  - Mumty, Staircase Headroom & Overhead Water Tank Floor: 34.18 sq.m
  - **Total Built-up / Plinth Area**: **3,419.38 sq.m** (Matches BOQ Item 1.01: \(8 	imes 3419.38 = 27,355	ext{ sq.m}\)).
- **Unit Typology**: 4 dwelling units per typical floor × 6 residential floors = **24 Dwelling Units** per tower (all Type-2BHK).
  - Plinth area per unit: ~90.00 sq.m.
  - Carpet area per unit: 69.00 sq.m (living/dining, master bedroom, second bedroom, kitchen, 2 toilets, 2 balconies).
  - Common circulation per floor: 123.60 sq.m (central corridor, staircase, 2 lift shafts, service ducts).

## 3. Structural & Foundation Scope
- **Foundation System**:
  - Pile count: **207 piles** direct from Sheet 100.
  - Pile diameter: **600 mm** direct from Sheet 100 and DBR.
  - Pile length/depth: **Assumed 18.0 m** below cut-off level based on DBR / Geotechnical Report recommended range (15–20 m). Tabulated pile schedule is NOT found on tender drawings. Confidence: `ESTIMATED` / `ASSUMPTION_REQUIRED` (not direct).
  - Pile caps: Interconnected by RC plinth tie beams. Preliminary summary lists 84 caps, but Sheet 101 layout shows 54 cap entities and 91 piles remain unaccounted in allocation. Status: `UNRESOLVED_CONTRADICTION` / `ASSUMPTION_REQUIRED`.
- **Superstructure System**: Special Moment Resisting Frame (SMRF) with ductile reinforced concrete structural shear walls designed for Seismic Zone V (\(Z = 0.36\)) in accordance with IS 13920:2016 and IS 456:2000.
  - Columns / Shear Wall Elements: 49 vertical elements (16 framed columns C1-C3 + 33 shear wall legs SW1-SW10).
  - Floor Framing: Cast-in-situ RCC beam grid (spans 3.0 m to 6.2 m) supporting 125 mm two-way RCC floor slabs.
  - Concrete Grade: M30 for all RCC structural elements (piles, pile caps, plinth beams, columns, shear walls, beams, slabs, staircase, OHT); M10 for foundation lean concrete (PCC).
  - Reinforcement: High-yield strength deformed TMT bars Fe 500D / Fe 550D conforming to IS 1786:2008.

## 4. Scope Demarcation: Included vs Excluded

### INCLUDED (Modeled Tower Scope)
1. Bored cast-in-situ RCC piles (600 mm dia), pile caps, and lean concrete under caps.
2. Plinth beams, ground tie beams, and stilt floor grade slab / VDF flooring.
3. Superstructure RCC columns and ductile shear walls from stilt level to terrace/mumty roof.
4. RCC floor beams, landing beams, lintels, and chajjas for all 7 suspended slab levels.
5. RCC two-way suspended floor slabs (1st to 6th floors) and terrace structural slab (125 mm).
6. RCC doglegged staircases (flights, waist slabs, treads, risers, mid-landings).
7. Terrace mumty room, lift machine room slab, and overhead water storage tank (RCC).
8. External 230 mm brick masonry and internal 115 mm brick masonry partitions.
9. Internal cement plaster (12 mm/6 mm), external waterproof plaster (18 mm), and POP punning.
10. Premium acrylic interior emulsion, weather-shield exterior emulsion, and synthetic enamel painting.
11. Vitrified tile flooring (living/bed), anti-skid ceramic tiling (toilets/balconies), and wall tile dado.
12. Kota stone flooring on staircase treads and polished granite counters.
13. Complete door-window assemblies (D1-D3, DW1-DW2, SD1-SD4, W1-W4, V1-V2, MS grills, railings).
14. Terrace elastomeric waterproofing with brick-bat coba protection.

### EXCLUDED (Non-Tower Infrastructure & Ancillary Works)
1. The remaining 7 residential tower blocks (B, C, D, E, F, G, H).
2. Guest House building (G+3 storeys, 1,990 sq.m plinth area).
3. Community Centre building (G+1 storeys, 1,035 sq.m plinth area).
4. Electrical Substation and 11kV/415V Panel Room (Single storey, 368 sq.m plinth area).
5. Two Guard Rooms (70 sq.m) and Main Gate Security Hut (6 sq.m).
6. Sewage Treatment Plant (STP) civil, mechanical, and piping installations.
7. Underground Water Tank (UGT) and central pump house.
8. External site development: 768 m boundary wall (3.6 m height), security gates, cantilever parking sheds.
9. Campus internal and external roads, bituminous pavements, concrete footpaths, storm drains, street lighting, landscaping, and campus services networks.
10. Historical 2020 OIL tender documents (`NIT_CPI4685P21`).
