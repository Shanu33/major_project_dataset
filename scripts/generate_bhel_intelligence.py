import os

base_dir = r"c:\Users\shahnawaz khan\OneDrive\Documents\DataRequirement\BHEL-Township-Jagdishpur"

# 1. 00_Core_Intelligence_Dataset/Project_Executive_Summary_and_Data_Extraction.md
f00 = """# Project Executive Summary & Technical Intelligence: BHEL Township Jagdishpur

## 1. Project Master Identification
- **Project Title:** Construction of Multi-Storey Flats of Type-A, B, C, D & CEO Residence & Other Utility Buildings, Services etc. Including Finishing Works for Township at Jagdishpur
- **Tender Enquiry No.:** `BHE/FP/CVL/021` (Master Final Revised Tender); Earlier Stage: `BHE/FP/CVL/012`
- **Architectural & Design Consultancy Tender:** `BHE/FP/CVL/001`
- **Client / Authority:** Bharat Heavy Electricals Limited (BHEL) - Centralised Stamping Unit (CSU) & Fabrication Plant (FP)
- **Location:** BHEL Industrial Area, Jagdishpur, Distt. Sultanpur, Uttar Pradesh - 227817 (80 km SE of Lucknow on Lucknow-Varanasi Highway)
- **Site Area:** 31.6 Acres (adjacent to existing Insulator Plant IP and CSU)
- **Contract Type:** Item Rate Contract (Two-part bidding: Techno-commercial + Price Bid / Reverse Auction)
- **Contract Completion Period:** 24 Calendar Months
- **Defects Liability Period:** 12 Months from completion

## 2. Complete Scope & Building Breakdown
The project comprises the full development of a residential township housing complex with complete civic and recreational infrastructure:

### Residential Buildings Scope (262 Total Units)
1. **CEO Residence:** 2 Premium Executive Bungalows (Milestone 1)
2. **Type-A Flats:** 4 Multi-Storey Blocks = **128 Flats** (32 flats/block, G+8/G+10 floors)
   - 2 Blocks (64 flats) in Milestone 1
   - 2 Blocks (64 flats) in Milestone 2
3. **Type-B Flats:** 1 Multi-Storey Block = **64 Flats** (Milestone 1, G+8/G+10 floors)
4. **Type-C Flats:** 2 Multi-Storey Blocks = **56 Flats** (28 flats/block, G+8/G+10 floors)
   - 1 Block (28 flats) in Milestone 1
   - 1 Block (28 flats) in Milestone 2
5. **Type-D Flats:** 1 Multi-Storey Block = **12 Flats** (Milestone 2, G+8/G+10 floors)
- **Total Residential Tenements:** 260 Multi-Storey Flats + 2 CEO Residences = **262 Residential Units**

### Civic, Utility & Amenity Buildings
- **Transit Hostel:** Multi-room guest/transit accommodation with reception lounge, dining hall, TV lounge
- **Club & Gymnasium Block:** Multi-purpose halls, gymnasium, administration office, pantry, toilets
- **Shopping Center:** Retail market complex for township residents
- **Dispensary Block:** Emergency/M.O. room, registration lobby, minor operation theatre (OT), sterilization room, ward
- **Sub-station & Electrical Center:** Transformer room, 125 kVA DG set installations, switchgear
- **Pump House & Water Supply:** Underground water reservoir, domestic & fire pumps, overhead distribution
- **Sewage Treatment Plant (STP):** Complete biological sewage treatment plant and recycling
- **Security & Enclosure:** Security gate houses, main gates, boundary wall, shifting of LPG godown
"""

with open(os.path.join(base_dir, '00_Core_Intelligence_Dataset', 'Project_Executive_Summary_and_Data_Extraction.md'), 'w', encoding='utf-8') as f:
    f.write(f00)

# 2. 01_Tender_NIT_PreBid/Tender_NIT_Key_Terms_and_Eligibility_Criteria.md
f01 = """# Tender Notice & Key Commercial Terms: BHEL Township Jagdishpur

## 1. Notice Inviting Tender (NIT) Parameters
- **Tender Enquiry No:** `BHE/FP/CVL/021` (NIT-Township-Final Revised)
- **Earliest Reference:** `BHE/FP/CVL/012`
- **Cost of Tender Documents:** Rs 1,000/- (Non-refundable)
- **Earnest Money Deposit (EMD):** Rs 2,00,000/- (Rs Two Lakh only) via Demand Draft payable at Jagdishpur/Lucknow
- **Tender Officer:** Sh. Vaibhav Jain, Engineer (Civil-Planning) / Sh. Ramnik Sarbahi, Sr. Manager (Projects), BHEL CSU & FP, Jagdishpur Industrial Area, Sultanpur, UP - 227817

## 2. Prequalification Criteria (Annexure NIT-I)
Contractors must demonstrate proven track record in high-rise buildings / multi-storey apartments / townships within last 7 years:
1. **Value of Completed Works:**
   - One single completed work of value >= **Rs 27.70 Crores** (Rs 2,770 Lakhs), OR
   - Two completed works of value >= **Rs 17.29 Crores** (Rs 1,729 Lakhs) each, OR
   - Three completed works of value >= **Rs 13.84 Crores** (Rs 1,384 Lakhs) each
2. **Financial Turnover:** Minimum average annual financial turnover of **Rs 10.38 Crores** (Rs 1,038 Lakhs) per year over 3 consecutive financial years.
3. **Physical Construction Experience:** Minimum constructed floor area of **12,000 m2** in high-rise/multi-storey buildings within the last 7 years.

## 3. Commercial Conditions
- **Bidding System:** Two-packet system (Part-I Techno-commercial Bid, Part-II Price Schedule / Reverse Auction).
- **Mobilisation Advance:** Up to **5% of contract value**, interest-bearing, secured by Bank Guarantee of 1.2 times advance amount valid initially for 12 months.
- **Contract Nature:** Single turnkey contractor for complete civil, structural, architectural, MEP, and external township infrastructure.
"""

with open(os.path.join(base_dir, '01_Tender_NIT_PreBid', 'Tender_NIT_Key_Terms_and_Eligibility_Criteria.md'), 'w', encoding='utf-8') as f:
    f.write(f01)

# 3. 02_Cost_BOQ_Makes/Cost_Abstract_and_BOQ_Schedule_Intelligence.md
f02 = """# Cost Abstract & BOQ Intelligence: BHEL Township Jagdishpur

## 1. BOQ & Pricing Structure
- **Tender Volume:** Section IV: Bill of Quantities & Price Schedule (TE No. `BHE/FP/CVL/021`).
- **Benchmark / Scribd BOQ Reference:** *Township BOQ With Corrigendum* (Poornima D Gowda / Bhadanis Courseware benchmark, 423198487) covers the comprehensive civil, structural, architectural, and external infrastructure schedule for Jagdishpur Township.
- **Tender Cost Benchmark:** Prequalification single-work criterion of Rs 27.70 Cr reflects an overall project cost scale of Rs 50 - Rs 100 Crores.
- **Unit Rate Analysis Structure (Annexure SCC-IV):**
  1. Salary & Wages of Staff & Workers
  2. Consumables: Gases, Welding Electrodes, P.O.L., Others
  3. Depreciation & Maintenance for Tools & Plants (T&Ps)
  4. Depreciation & Maintenance for Other Items
  5. Establishment & Administrative Expenses of Site
  6. Overheads
  7. Contractor Profit Margin

## 2. Stage-Wise Milestone Billing Basis
Running account bills are linked to physical progress targets across the three major contractual milestones defined in Annexure SCC-III:
- **Milestone 1:** Prorated payment for 2 CEO residences, 2 Type-A blocks (64 flats), 1 Type-C block (28 flats), 1 Type-B block (64 flats), Transit Hostel, Club/Gym, Shopping Center, Dispensary, and primary trunk services.
- **Milestone 2:** Prorated payment for remaining 2 Type-A blocks (64 flats), 1 Type-C block (28 flats), 1 Type-D block (12 flats), final road paving, and landscaping.
- **Milestone 3:** Final bill settlement upon punch point rectification, material reconciliation, scrap hand-back, and final formal handover.
"""

with open(os.path.join(base_dir, '02_Cost_BOQ_Makes', 'Cost_Abstract_and_BOQ_Schedule_Intelligence.md'), 'w', encoding='utf-8') as f:
    f.write(f02)

# 4. 03_Technical_Specifications_Reports/Technical_Specifications_and_Finishing_Standards.md
f03 = """# Technical Specifications & Room-by-Room Finishing Schedule

Extracted directly from the official 8-page **Specification Chart (TE: BHE/FP/CVL/021, Pages 106-113)**:

## 1. Residential Units Finishing Standards
### Type-A Flats (128 Units across 4 Blocks)
- **Lounge & Bedrooms:** Vitrified tiles flooring, 4 inch skirting, Oil Bound Distemper (OBD) ceiling/walls, Sal wood door/window frames, Flush doors with one-side teak facing, Painted MS grills, Spectrum texture external finish, 19mm commercial board with 1.0mm mica wardrobes.
- **Kitchen:** Vitrified tiles, OBD, Sal wood frames, Baroda green granite kitchen counter top, overhead 19mm commercial board cabinet with mica.
- **Bath & W.C.:** Grade IV ceramic floor tiles, glazed wall tiles up to 7'-0" height, OBD.
- **Common Areas & Staircase:** Combination of Baroda Green marble and white marble.

### Type-B Flats (64 Units across 1 Block)
- **Lounge & Bedrooms (Bed 1 & Bed 2):** Vitrified tile flooring, 4 inch skirting, OBD on walls/ceiling, Sal wood frames, flush door with teak facing, Spectrum textured external paint, 19mm commercial board wardrobe with 1.0mm mica.
- **Kitchen:** Vitrified tiles, Baroda green granite counter, overhead cabinets.
- **Toilets:** Grade IV floor tiles, wall tiles up to 7'-0" height.
- **Parking:** 30mm thick heavy-duty Kota stone flooring.

### Type-C Flats (56 Units across 2 Blocks)
- **Drawing Room & Lounge:** Vitrified tiles, 4 inch skirting, POP punning on ceiling and walls with cornices/mouldings, plastic emulsion paint, teak wood shutters with glass, PU-polished teak wood framed veneer cabinets.
- **Kitchen:** Vitrified tiles, Lakha red granite counter top, teak wood framed veneer cabinets.
- **Study Room:** Vitrified tiles, overhead cabinet with teak wood frame and etched glass.
- **Toilets:** Grade IV tiles, full height wall dado up to 7'-0", granite counter wash basin.

### Type-D Flats (12 Units across 1 Block)
- **Foyer & Living Room:** Premium vitrified tiles, POP punning with ornate cornices/mouldings, plastic emulsion.
- **Drawing Room & Master Bedroom:** Wooden flooring, 4 inch wooden skirting, plastic emulsion with feature accent wall, teak wood window/door frames, PU-polished veneer wardrobes.
- **Kitchen:** Vitrified tiles, Lakha red granite counter top, modular cabinetry.
- **Toilets:** Grade V floor tiles (15"x15"), jointless wall tiles with handmade decorative borders up to 7'-0" height, granite counter tops.

### Chief Executive (CEO) Residence (2 Bungalows)
- **Entrance Lobby, Dining & Lounge:** Imported Italian Marble / Granite pattern flooring, 4 inch Italian marble skirting, POP punning, plastic emulsion.
- **Drawing Room & Master Bedroom:** Real wooden flooring, 4 inch wooden skirting, plastic emulsion with specialized wall texture, teak wood doors and windows with jali/glass shutters.
- **Kitchen:** Vitrified tiles, jointless tiles with handmade borders, Lakha red granite counters, PU-polished modular cabinetry.
- **Toilets:** Grade V 15"x15" tiles, full height designer dado, granite vanity counters.

## 2. Institutional & Amenity Finishing Standards
- **Transit Hostel:** Vitrified and granite combination in reception/dining/lounges, vitrified in guest bedrooms, Lakha red granite in kitchen, granite staircases.
- **Dispensary Block:** PVC anti-static/hygienic flooring in Minor OT and Sterilization rooms, vitrified tiles in registration lobby and doctor rooms, satin enamel washable wall paint.
- **Club & Gymnasium:** Vitrified tiles with decorative granite border patterns in lobby, halls, and staircase; teak wood doors with glass panels; Spectrum textured external paint.
"""

with open(os.path.join(base_dir, '03_Technical_Specifications_Reports', 'Technical_Specifications_and_Finishing_Standards.md'), 'w', encoding='utf-8') as f:
    f.write(f03)

# 5. 04_Architectural_Drawings/Architectural_Design_Basis_and_Drawings_Catalog.md
f04 = """# Architectural Design Basis & Enclosed Drawings Catalog

## 1. Master Drawing Index (Clause 20.1 of Master Tender BHE/FP/CVL/021)
The master tender references 16 architectural and engineering drawing sheets designated `Drg Nos CSU/FP/01 to 16`:
1. `CSU/FP/01`: Master Township Layout & Site Master Plan (31.6 Acres)
2. `CSU/FP/02`: Block Type-A Architectural Floor Plans (Ground to 8th/10th Floor)
3. `CSU/FP/03`: Block Type-A Elevations & Cross Sections
4. `CSU/FP/04`: Block Type-B Architectural Floor Plans
5. `CSU/FP/05`: Block Type-B Elevations & Sections
6. `CSU/FP/06`: Block Type-C Architectural Floor Plans & Elevations
7. `CSU/FP/07`: Block Type-D Architectural Floor Plans & Elevations
8. `CSU/FP/08`: CEO Residence Architectural Plans, Elevations & Sections
9. `CSU/FP/09`: Transit Hostel Architectural Floor Plans & Elevations
10. `CSU/FP/10`: Club & Gymnasium Architectural Layout
11. `CSU/FP/11`: Shopping Center Architectural Layout & Shop Configurations
12. `CSU/FP/12`: Dispensary Block Medical Layout & OT Specifications
13. `CSU/FP/13`: Sub-station, DG Room & Pump House Utility Layouts
14. `CSU/FP/14`: Security Gate Houses, Boundary Walls & Main Entry Gate
15. `CSU/FP/15`: External Water Supply Distribution & Sewerage Network Plan
16. `CSU/FP/16`: Road Network, Storm Water Drainage & Grading Plan

*Note: In the public master tender PDF (Pages 90-105), sheets are included as indexed reference placeholders. Detailed full-scale GFC drawings and high-resolution CAD files (`Drawing_Part-I_and_II.rar`) are managed via the BHEL eProcurement portal and formally released post-award.*
"""

with open(os.path.join(base_dir, '04_Architectural_Drawings', 'Architectural_Design_Basis_and_Drawings_Catalog.md'), 'w', encoding='utf-8') as f:
    f.write(f04)

# 6. 05_Structural_Drawings/Structural_Design_Basis_and_Piling_Engineering_Notes.md
f05 = """# Structural Design Basis & Geotechnical/Piling Specifications

## 1. Structural Engineering Scheme
- **Structural System:** RCC Framed multi-storey earthquake-resistant structures (G+4 to G+10 storeys).
- **Foundation System:** Under-reamed cast-in-situ bored concrete piles designed to cater to Sultanpur alluvium / silty strata.
- **Plant & Machinery Required on Site (Annexure SCC-I):**
  - **16 Nos.** Cast-in-situ under-reamed piling rigs and testing equipment.
  - **1 No.** PLC-operated automatic concrete batching plant (minimum capacity 30 m3/hr).
  - Concrete pumps (minimum 20 m3/hr, 40m vertical lift) and transit mixers.
  - MS Scaffolding adequate for 8 blocks of G+8 storeys simultaneously.
  - 8 Nos. Winches with building passenger/material hoists.
  - 4 Nos. Reinforcement cutting and bending machines.
  - 1 No. 400 MT cement storage shed.

## 2. Geotechnical Investigation Framework (Tender BHE/FP/CVL/001)
- **Boring Requirement:** 250 Running Meters of 150mm nominal diameter boreholes down to 25m depth below ground level.
- **In-Situ Testing:**
  - Standard Penetration Tests (SPT) at every 3m interval and change of strata.
  - Cyclic Plate Load Tests at 5 critical building footprint locations.
  - Dynamic Cone Penetration Tests (DCPT) using 65mm cone at 20 locations.
- **Soil Laboratory Testing:** Bulk density, moisture, sieve/hydrometer analysis, Atterberg limits, swell pressure, free swell index, triaxial shear, 1D consolidation, Proctor compaction, CBR, dynamic shear modulus, Young's modulus, Poisson's ratio.
- **Vetting Authority:** Final geotechnical report required to be vetted and accepted by **IIT / IT-BHU**.
"""

with open(os.path.join(base_dir, '05_Structural_Drawings', 'Structural_Design_Basis_and_Piling_Engineering_Notes.md'), 'w', encoding='utf-8') as f:
    f.write(f05)

# 7. 06_MEP_Services/MEP_Engineering_Specifications_and_Services_Schedule.md
f06 = """# MEP Engineering Services & Utility Infrastructure Schedule

## 1. Electrical & Power Distribution
- **Sub-Station & Transformers:** Dedicated electrical sub-station building housing high-voltage switchgear and transformers.
- **Backup Power:** 1 No. 125 kVA diesel generator set specified in site equipment alongside permanent township emergency DG installation.
- **Internal Wiring:** Concealed FRLS copper wiring, modular switches, earthing pits across all residential and institutional blocks.
- **External Lighting:** Street lighting, security perimeter illumination, pathway lighting.

## 2. Plumbing, Water Supply & Public Health
- **Source & Storage:** Underground raw and treated water storage reservoirs, hydro-pneumatic / centrifugal pump sets, overhead RCC tanks on each multi-storey block.
- **Internal Piping:** CPVC pipes for internal water distribution, UPVC/CI pipes for soil and waste stacks.
- **Sanitary Fixtures:** Vitrified ceramic sanitaryware, brass/CP fittings, granite washbasin counters.

## 3. Sewerage & Sewage Treatment Plant (STP)
- **Collection Network:** Gravity underground stoneware / RCC pipe sewer network with manholes at regular intervals.
- **Sewage Treatment:** Dedicated biological STP designed to treat domestic effluent to statutory UPPCB disposal and horticultural reuse standards.

## 4. Fire Protection & Life Safety
- **Hydrant System:** External fire hydrant ring main network around all multi-storey blocks.
- **Internal Wet Risers:** Wet risers with landing valves, hose reels, and fire brigade inlet connections.
- **Emergency Access:** Fire tenders vehicular access routes conforming to NBC guidelines.
"""

with open(os.path.join(base_dir, '06_MEP_Services', 'MEP_Engineering_Specifications_and_Services_Schedule.md'), 'w', encoding='utf-8') as f:
    f.write(f06)

# 8. 07_Landscape_Infrastructure/Site_Development_and_External_Infrastructure_Schedule.md
f07 = """# Site Development, Landscaping & Township Amenities Schedule

## 1. Civil Site Works (31.6 Acre Site)
- **Topographic & Grid Survey:** Establishing reference bench mark pillars (15 Nos.) and grid reference pillars (50 Nos.).
- **Site Grading:** Earth filling, leveling, and compaction across township contours.
- **Roadways & Paving:** Heavy-duty CC paving and asphalt bitumen carriage roads, pedestrian walkways, kerb stones, storm water RCC box/trapezoidal surface drains.
- **Perimeter & Security:** Boundary wall with security fencing, main entrance gate complex with security guard room and boom barriers.
- **Relocation Work:** Safe dismantling and shifting of the existing LPG gas godown to designated industrial zone.

## 2. Community & Civic Infrastructure
- **Club & Gymnasium:** Indoor recreation, badminton/gym hall, community social space.
- **Shopping Complex:** Daily provisions retail shops, convenience stores.
- **Dispensary:** First-aid, medical consultation, minor treatment, and recovery ward.
- **Transit Accommodation:** Multi-occupancy transit hostel for visiting BHEL executives and engineers.
- **Landscaping:** Horticultural planting, lawns, avenue plantations, children play equipment.
"""

with open(os.path.join(base_dir, '07_Landscape_Infrastructure', 'Site_Development_and_External_Infrastructure_Schedule.md'), 'w', encoding='utf-8') as f:
    f.write(f07)

# 9. 08_Execution_Actuals/Construction_Milestones_and_Execution_Charter.md
f08 = """# Construction Milestones & Execution Tracking Charter

## 1. Mandatory Contractual Milestones (Annexure SCC-III)
Total Contract Period: **24 Calendar Months** from issuance of Letter of Intent (LOI).

| Milestone | Target Duration | Scope of Handover | Intermediate Critical Path Targets |
| :--- | :---: | :--- | :--- |
| **Milestone 1** | **14 Months** | - 2 Nos. CEO Residences<br>- 2 Blocks Type-A Flats (64 units)<br>- 1 Block Type-C Flats (28 units)<br>- 1 Block Type-B Flats (64 units)<br>- Transit Hostel<br>- Club & Gymnasium Block<br>- Shopping Center<br>- Dispensary Block | Trunk water supply, primary electrical sub-station energization, access roads, sewerage connections, external fire network ready for initial occupancy. |
| **Milestone 2** | **20 Months** | - 2 Blocks Type-A Flats (64 units)<br>- 1 Block Type-C Flats (28 units)<br>- 1 Block Type-D Flats (12 units) | Balance residential blocks fully finished; complete external services, final asphalt/paving layer on roads, complete site landscaping. |
| **Milestone 3** | **24 Months** | - Full Project Handover | Punch point rectifications, material reconciliation, return of BHEL steel scrap, site clearing, demobilization, and issuance of virtual completion certificate. |

## 2. Quality Control & Site Laboratory
Contractor must establish an on-site accredited testing laboratory equipped with:
- 2000 kN Automatic Compression Testing Machine (ACTM)
- 60 Nos. concrete cube moulds (150mm) and 6 Nos. mortar cube moulds (70mm)
- Slump cones, sieve shakers, Vicat apparatus, core cutter test apparatus, rapid moisture meter
- Total Station (1 No.) and 1-second accuracy Theodolites (2 Nos.)
"""

with open(os.path.join(base_dir, '08_Execution_Actuals', 'Construction_Milestones_and_Execution_Charter.md'), 'w', encoding='utf-8') as f:
    f.write(f08)

print('Successfully generated all 9 domain intelligence markdown documents!')

