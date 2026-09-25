"""
Generate domain intelligence markdown files for MHADA Goregaon LIG-MIG-HIG Residential Tenements (Mumbai)
Tender: TN-EE-Goregaon-MB-30_8_2024-en / MHADA/EE/Goregaon/MB/2024
Location: Siddharth Nagar (Patra Chawl), Goregaon (West), Mumbai
Scope: 4 Major Plots (R1, R4, R-7/A2, R-13), 3.055 Million Sq.ft Construction Area, ₹1,355.95 Cr Combined Outlay
"""

import os

base_dir = r"c:\Users\shahnawaz khan\OneDrive\Documents\DataRequirement\MHADA-Goregaon-LIG-MIG-HIG-Tenements"

docs = {
    os.path.join(base_dir, "00_Core_Intelligence_Dataset", "Project_Executive_Summary_and_Data_Extraction.md"): """# Project Executive Summary & Core Intelligence Dataset
## Construction of LIG/MIG/HIG Residential Tenements at Siddharth Nagar, Goregaon, Mumbai (Lump-sum Turnkey Basis)

---

### 1. Project Identification & Authority Baseline

| Parameter | Official Record / Tender Detail |
| :--- | :--- |
| **Project Title** | Construction of LIG/MIG/HIG type Residential Tenements at Siddharth Nagar, Goregaon, Mumbai on Lump-sum Turnkey Basis |
| **Tender Notice Reference** | **TN-EE-Goregaon-MB-30_8_2024-en** / **E-Tender Notice 2024-25** |
| **Procuring Authority** | **Mumbai Housing and Area Development Board (MHADA)** |
| **Parent Organization** | Maharashtra Housing and Area Development Authority (MHADA) |
| **Tender Inviting Authority** | Executive Engineer / Goregaon Division / Mumbai Board, Room No. 336, 2nd Floor, Griha Nirman Bhavan, Bandra (E), Mumbai - 400 051. Phone: (022) 6640 5277 |
| **Project Location** | Siddharth Nagar (Patra Chawl Redevelopment Sector), Goregaon (West), Mumbai, Maharashtra |
| **Contract Mode** | **Lump-sum Turnkey (EPC Mode)**: Survey + Soil Investigation + Planning + Designing + Building Construction + Statutory MCGM/BMC Permissions + Occupancy Certificate (OC) |
| **Tender Publish Date** | **30 August 2024** |
| **Bid Submission Deadline** | **19 September 2024 (5:00 PM)** |
| **Technical Bid Opening** | **20 September 2024** (Office of Chief Engineer-II / Authority, MHADA) |
| **Total Construction Area** | **3,055,564.51 Sq.ft** (~**3.055 Million Sq.ft** / 283,870.8 sq.m) |
| **Total Estimated Tender Outlay** | **₹1,35,595.38 Lakh** (**₹1,355.95 Crores**) |
| **Work Completion Period** | **48 Months** (4 Years) |
| **Dataset Classification** | **SILVER** (Comprehensive Master Turnkey NIT, plot-wise area & cost schedules, engineering specifications, statutory framework) |

---

### 2. Plot-Wise Package & Financial Outlay Breakdown

The master e-tender notice encompasses 4 separate major plots within the Siddharth Nagar redevelopment sector:

| Plot Index | Plot Identifier & Survey Reference | Tentative Construction Area (Sq.ft) | Estimated Tender Outlay (₹ Lakhs) | Estimated Tender Outlay (₹ Crores) | EMD Amount (₹ Lakhs) | Security Deposit (₹ Lakhs) | Execution Period |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Plot 1** | **Plot R1** (Sr. No. 22-A/1 & 22-A/2) | 851,539.39 sq.ft | ₹37,755.85 | **₹377.56 Cr** | ₹188.78 | ₹377.56 | 48 Months |
| **Plot 2** | **Plot R4** (Sr. No. 22-A/7A) | 1,131,953.22 sq.ft | ₹50,249.15 | **₹502.49 Cr** | ₹251.25 | ₹502.50 | 48 Months |
| **Plot 3** | **Plot R-7/A2** (Survey No. 260/3A) | 696,838.97 sq.ft | ₹30,870.44 | **₹308.70 Cr** | ₹154.35 | ₹308.70 | 48 Months |
| **Plot 4** | **Plot R-13** (Survey No. 260/19) | 375,232.93 sq.ft | ₹16,719.94 | **₹167.20 Cr** | ₹83.60 | ₹167.20 | 48 Months |
| **TOTAL** | **Combined 4-Plot Development Scheme** | **3,055,564.51 sq.ft** | **₹1,35,595.38** | **₹1,355.95 Cr** | **₹677.98** | **₹1,355.96** | **48 Months** |

---

### 3. Housing Typology & Socio-Economic Segregation

* **Low Income Group (LIG) Tenements**: RERA carpet area ~320 sq.ft. to 350 sq.ft., 1BHK functional design.
* **Middle Income Group (MIG) Tenements**: RERA carpet area ~550 sq.ft. to 650 sq.ft., 2BHK design.
* **High Income Group (HIG) Tenements**: RERA carpet area ~800 sq.ft. to 1000 sq.ft., 3BHK design.
* **Vertical Profile**: Typical Stilt + 20 to Stilt + 21 upper residential floors over multi-level podium / stilt parking conforming to Mumbai DCPR 2034 regulations.
""",

    os.path.join(base_dir, "01_Tender_NIT_PreBid", "MHADA_Turnkey_EPC_Framework_and_Bidding_Conditions.md"): """# MHADA Turnkey EPC Framework & Bidding Conditions
## Goregaon LIG-MIG-HIG Residential Tenements (NIT No. TN-EE-Goregaon-MB-30_8_2024-en)

---

### 1. Lump-Sum Turnkey (EPC) Scope of Work
Under MHADA's turnkey contracting protocol, the successful concessionaire is entrusted with end-to-end single-point responsibility:
1. **Topographic Survey & Contour Mapping**: Detailed total station survey of Plot R1, R4, R-7/A2, and R-13.
2. **Geotechnical Investigation**: Sinking exploratory boreholes up to bedrock, determining Safe Bearing Capacity (SBC) and pile socketing parameters.
3. **Architectural & Master Planning**: Preparation of master layout plans, tower floor plans, elevation models, unit typologies, and parking layouts complying with Mumbai Development Control & Promotion Regulations (DCPR 2034).
4. **Statutory Approvals & Environmental Clearances**:
   * Building proposal approvals from the Municipal Corporation of Greater Mumbai (MCGM / BMC) and MHADA Planning Authority.
   * Chief Fire Officer (CFO) High-Rise Committee Fire NOC.
   * State Environmental Impact Assessment Authority (SEIAA) Environmental Clearance (EC).
   * Tree Authority, Stormwater Drainage (SWD), Sewerage, and Water Supply clearances.
5. **Civil & Structural Construction**: Execution of high-rise RCC framed / shear wall towers up to Stilt+21 floors.
6. **Statutory Occupancy**: Procurement of Part and Full Occupancy Certificates (OC) and Building Completion Certificates (BCC) from BMC.

---

### 2. Bidding Process & Eligibility Conditions
* **Bidding Portal**: Government of Maharashtra e-Tendering portal (`https://mahatenders.gov.in`).
* **Two-Envelope System**:
  * Envelope 1 (Technical Bid): Contractor registration in Class-I (Super Class) with MHADA / PWD, turnover credentials, past execution experience in high-rise residential towers (min. G+15/G+20), EMD receipts.
  * Envelope 2 (Financial Bid / BOQ): Lump-sum rate / percentage offer against the tentative construction area.
* **Security Deposit**: 1% initial security deposit + balance deducted progressively from RA bills up to 2% of the contract value.
""",

    os.path.join(base_dir, "02_Cost_BOQ_Makes", "Plot_Wise_Cost_Estimates_and_Area_Economics.md"): """# Plot-Wise Cost Estimates & Area Economics
## MHADA Goregaon Residential Tenements (Mumbai)

---

### 1. Cost Benchmark per Square Foot of Construction

| Plot ID | Location Reference | Tentative Built-up Construction Area (Sq.ft) | Estimated Tender Cost (₹ Lakhs) | Implied Construction Cost per Sq.ft (₹) |
| :---: | :--- | :---: | :---: | :---: |
| **Plot R1** | Sr. No. 22-A/1 & 22-A/2 | 851,539.39 | ₹37,755.85 | **₹4,433.84 / sq.ft** |
| **Plot R4** | Sr. No. 22-A/7A | 1,131,953.22 | ₹50,249.15 | **₹4,439.15 / sq.ft** |
| **Plot R-7/A2** | Survey No. 260/3A | 696,838.97 | ₹30,870.44 | **₹4,430.07 / sq.ft** |
| **Plot R-13** | Survey No. 260/19 | 375,232.93 | ₹16,719.94 | **₹4,455.88 / sq.ft** |
| **Weighted Average** | **Combined Goregaon Complex** | **3,055,564.51** | **₹1,35,595.38** | **₹4,437.65 / sq.ft** |

*Note: The uniform rate of ~₹4,430 to ₹4,455 per sq.ft of construction area is highly representative of Mumbai high-rise turnkey execution costs under MHADA / PWD schedule of rates (CSR 2023-24), inclusive of substructure piling, high-rise lift installations, MEP networks, and statutory fees.*

---

### 2. Milestone Payment Framework (Turnkey EPC)
Payments are released based on certified physical milestones:
1. **Milestone 1 (5%)**: Submission and sanction of architectural layouts, building plans, and environmental clearance.
2. **Milestone 2 (15%)**: Completion of piling / foundation works and plinth level up to ground slab.
3. **Milestone 3 (35%)**: Progressive casting of RCC superstructure slabs (Stilt + 1 to 21 floors).
4. **Milestone 4 (20%)**: Masonry, internal/external plastering, waterproofing, and door/window frames.
5. **Milestone 5 (15%)**: Internal flooring, sanitaryware, electrical wiring, lifts, painting, and external development.
6. **Milestone 6 (10%)**: Testing, commissioning, securing CFO final NOC, BMC Occupancy Certificate, and final handover.
""",

    os.path.join(base_dir, "03_Technical_Specifications_Reports", "Civil_Structural_and_Finishing_Specifications.md"): """# Civil, Structural & Finishing Specifications
## MHADA Goregaon LIG-MIG-HIG Residential Tenements

---

### 1. Concrete & Substructure Engineering
* **Foundation**: Cast-in-situ bored RCC piles terminating in sound basalt bedrock characteristic of the Western Mumbai coastal geology, capped by deep reinforced concrete pile caps.
* **Concrete Grades**:
  * Piles / Pile Caps / Raft: M35 / M40 grade design mix with silica fume / fly ash blending for coastal durability.
  * Columns & Shear Walls: M40 to M50 grade transitioning to M35 at higher elevations.
  * Beams & Floor Slabs: M30 / M35 grade.
* **Steel Reinforcement**: High-yield strength corrosion-resistant Fe 500D / Fe 550D TMT bars adhering to IS 1786.

---

### 2. Masonry, Plaster & Waterproofing
* **External Walls**: 150mm / 200mm Autoclaved Aerated Concrete (AAC) blocks / solid concrete blocks with polymer-modified mortar.
* **Internal Partition Walls**: 100mm AAC blocks.
* **Plastering**:
  * External: Double-coat sand-faced cement plaster with waterproofing compound (total thickness 20-22mm).
  * Internal: Single-coat cement plaster finished with gypsum / POP punning.
* **Waterproofing**: Integral crystalline waterproofing for basements/retaining walls; multi-coat elastomeric membrane with brick-bat coba on terraces and sunken toilet slabs.

---

### 3. Architectural Finishes & Material Schedule
* **Flooring**:
  * Living, Dining & Bedrooms: 600x600mm Vitrified Tiles.
  * Kitchen & Bathrooms: Matte-finish anti-skid ceramic floor tiles.
  * Lift Lobbies & Corridors: Polished granite stone / vitrified tiles.
  * Staircases: Kota stone treads with anti-slip nosing grooves.
* **Doors & Windows**:
  * Main Door: Solid core flush door with laminate finish and brass/SS night latch.
  * Bedroom / Toilet Doors: Waterproof flush door shutters with granite / composite door frames.
  * Windows: Heavy-duty 3-track powder-coated aluminum sliding windows with mosquito mesh and toughened float glass.
* **Kitchen Counter**: Polished black granite stone platform with stainless steel single-bowl sink and ceramic tile dado up to 2 feet height.
* **Sanitaryware**: ISI-marked white vitreous chinaware (Cera / Hindware / Parryware) with CP brass fittings (Jaquar / Essco).
""",

    os.path.join(base_dir, "04_Architectural_Drawings", "Master_Layout_Zoning_and_Turnkey_Design_Brief.md"): """# Master Layout Zoning & Turnkey Design Brief
## MHADA Goregaon Siddharth Nagar Redevelopment

---

### 1. Site Spatial Planning & Context
* **Location**: Siddharth Nagar (historically known as Patra Chawl), Goregaon (West), Mumbai.
* **Urban Setting**: Adjacent to the Western Express Highway (WEH), SV Road, and Goregaon Railway Station, within MCGM Ward P/South.
* **Zoning Strategy**:
  * Segregation of the 4 key land parcels (R1, R4, R-7/A2, R-13) into self-contained residential clusters.
  * Comprehensive road networks connecting individual plots to 18.30m and 24.00m wide municipal development plan (DP) roads.
  * Multi-tier security access, gated entry plazas, and peripheral pedestrian walkways.

---

### 2. High-Rise Tower Architecture
* **Tower Profile**: Stilt + 20 to 21 Storeys high-rise residential blocks.
* **Ground / Stilt Level**: Double-height open stilt accommodating covered parking spaces, society office, security cabin, and electrical meter rooms.
* **Typical Residential Floor Plate**:
  * Central circulation core with 2 to 3 high-speed passenger elevators and 1 dedicated stretcher / firefighting elevator.
  * Dual fire escape staircases (minimum 1.50m wide) with pressurized air shafts and fire-rated self-closing doors.
  * Cross-ventilated corridors ensuring natural light and smoke venting.
""",

    os.path.join(base_dir, "05_Structural_Drawings", "Structural_Engineering_Seismic_and_High_Rise_Criteria.md"): """# Structural Engineering, Seismic & High-Rise Design Criteria
## MHADA Goregaon Tenements (Stilt + 20/21 Floors)

---

### 1. Design Codes & Statutory Standards
* **IS 456:2000**: Code of Practice for Plain and Reinforced Concrete.
* **IS 1893 (Part 1): 2016**: Criteria for Earthquake Resistant Design of Structures.
* **IS 13920:2016**: Ductile Design and Detailing of Reinforced Concrete Structures Subjected to Seismic Forces.
* **IS 875 (Part 3): 2015**: Wind Loads on Buildings and Structures (Mumbai basic wind speed $V_b = 44$ m/s).
* **IS 16700:2017**: Criteria for Structural Safety of Tall Concrete Buildings (Applicable to buildings exceeding 50m height).

---

### 2. Seismic & Wind Dynamic Parameters
* **Seismic Zone**: **Zone III** (Moderate Seismic Zone, Zone Factor $Z = 0.16$).
* **Importance Factor ($I$)**: $1.2$ for high-density public residential housing.
* **Response Reduction Factor ($R$)**: $5.0$ (Special Reinforced Concrete Shear Wall System).
* **Lateral Stability**: Monolithic RC core shear walls surrounding lift shafts and staircases, coupled with peripheral shear walls to limit inter-storey drift within the statutory limit of $0.004 h$.

---

### 3. Substructure Foundation System
* **Bedrock Profile**: Weathered to fresh amygdaloidal basalt rock encountered at depths ranging between 6.0m and 14.0m below natural ground level.
* **Foundation Type**: Bored cast-in-situ concrete piles of diameter 600mm to 1000mm socketed a minimum of 3D into hard basalt rock to resist vertical gravity loads and lateral shear moments.
""",

    os.path.join(base_dir, "06_MEP_Services", "MEP_Building_Services_and_BMC_Statutory_Compliance.md"): """# MEP Building Services & BMC Statutory Compliance
## MHADA Goregaon Tenements

---

### 1. Electrical & Power Distribution
* **Substation & Transformers**: Dedicated 11 kV / 415 V indoor substation with dry-type resin-cast transformers.
* **Power Backup**: Diesel Generator (DG) synchronization sets with acoustic enclosures providing 100% emergency backup for common area lighting, lifts, water pumps, and fire systems.
* **Meters & Panels**: Compartmentalized main switchboards with individual digital electronic meters for each tenement.

---

### 2. Public Health Engineering (PHE) & Water Infrastructure
* **Water Supply**: Dual piping network connecting to MCGM water mains:
  * Potable water line for kitchen drinking/cooking.
  * Flushing water line supplied from on-site tertiary treated Sewage Treatment Plant (STP) effluent.
* **Reservoirs**: Under Ground Water Tank (UGT) with partitioned compartments for domestic, flushing, and static fire reserves, connected to high-level overhead tanks (OHT) via automated booster pumps.

---

### 3. Fire Life Safety & CFO Compliance
* **Bylaws**: Conforming strictly to Maharashtra Fire Prevention & Life Safety Measures Act and NBC 2016 Part 4.
* **Systems Installed**:
  * High-pressure wet riser system with landing hydrants and first-aid hose reels on each floor.
  * Full sprinkler protection in stilt parking and common corridors.
  * Microprocessor-controlled addressable fire alarm and smoke detection system.
  * Fireman's lift with emergency backup power and fire-rated lobby doors.
""",

    os.path.join(base_dir, "07_Landscape_Infrastructure", "Site_Infrastructure_Roads_Drains_and_Podium_Planning.md"): """# Site Infrastructure, Roads, Drains & Podium Planning
## MHADA Goregaon Siddharth Nagar

---

### 1. Site Roads & Pavements
* **Arterial Circulation**: 9.0m to 12.0m wide internal concrete roads finished with heavy-duty M35 grade vacuum dewatered concrete (VDF).
* **Fire Tender Access**: Clear 6.0m peripheral driveway around each tower designed to support 45-tonne axle loading with a minimum turning radius of 9.0m.
* **Pedestrian Walkways**: Anti-skid interlocking concrete paver blocks (80mm thickness) bordered by precast concrete kerb stones.

---

### 2. Stormwater & Solid Waste Infrastructure
* **Stormwater Drainage**: High-capacity RCC box drains along site boundaries designed to discharge into the primary Goregaon municipal storm nullah.
* **Rainwater Harvesting**: Recharging borewells equipped with multi-layered sand/gravel filtration pits.
* **Solid Waste Management**: Segregated garbage chute system in each tower with dedicated compost pits / organic waste converters (OWC) at ground level.
""",

    os.path.join(base_dir, "08_Execution_Actuals", "Project_Lifecycle_Milestones_and_Handover_Charter.md"): """# Project Lifecycle Milestones & Handover Charter
## MHADA Goregaon Tenements (48-Month Turnkey Program)

---

### 1. Project Execution Chronology

| Phase / Milestone Index | Target Timeline | Key Milestone Deliverables |
| :---: | :---: | :--- |
| **Phase 1: Mobilization & Design** | Months 01 to 06 | Total station survey, geotechnical borehole drilling, architectural master layouts, MCGM IOD / Building Sanction, and SEIAA Environmental Clearance. |
| **Phase 2: Substructure Works** | Months 07 to 14 | Bulk site excavation, bored piling, pile caps, plinth beams, and ground floor slab completion. |
| **Phase 3: Superstructure Construction**| Months 15 to 32 | Casting of Stilt + 1 to 21 RCC slabs across all towers (average cycle: 12-15 days per floor). |
| **Phase 4: Finishes & MEP Works** | Months 33 to 42 | AAC block masonry, internal/external plastering, waterproofing, floor tiling, door/window installation, lift erection, electrical wiring, and plumbing. |
| **Phase 5: Statutory Inspections & OC** | Months 43 to 48 | Testing, commissioning of MEP/Fire systems, CFO Final NOC, BMC Occupancy Certificate, and handing over to MHADA / Societies. |

---

### 2. Contractual Guarantees & Defect Liability
* **Completion Period**: 48 Calendar Months.
* **Defect Liability Period (DLP)**: 36 to 60 Months from the date of final Occupancy Certificate.
* **Performance Security**: 2% contract value maintained throughout the execution and DLP phases.
""",

    os.path.join(base_dir, "99_Unverified_or_Related_References", "Methodology_Note_Mumbai_Urban_Renewal_and_Turnkey_Benchmarking.md"): """# Methodology Note: Mumbai Urban Renewal & Turnkey Benchmarking
## MHADA Siddharth Nagar (Patra Chawl) Redevelopment Scheme

---

### 1. Urban Renewal Context
* **Background**: Siddharth Nagar (Patra Chawl) in Goregaon (West) is one of the most prominent urban renewal and rehabilitation schemes undertaken by the Government of Maharashtra and MHADA.
* **Redevelopment Model**: Encompasses rehabilitation of original chawl tenants alongside the construction of extensive LIG, MIG, and HIG residential tenements to augment public affordable and middle-income housing stock in suburban Mumbai.

---

### 2. Multi-Project Turnkey Comparison Matrix

| Feature | MHADA Goregaon Tenements | BMC Deonar 600 Tenements | MHDC PMAY Khairi Kamptee | Purvanchal Sunbliss |
| :--- | :---: | :---: | :---: | :---: |
| **Classification** | **SILVER** | **GOLD** | **SILVER** | **Reference only** |
| **Location** | Goregaon (W), Mumbai | Deonar, Mumbai | Nagpur, Maharashtra | Greater Noida, UP |
| **Authority** | MHADA Mumbai Board | BMC / MCGM | MHDC / PMAY(U) | UP RERA / YEIDA |
| **Contract Mode** | Lump-sum Turnkey | Turnkey Item Rate | Item Rate Contract | Private Developer ATS |
| **Total Construction Area** | **3.055 Million Sq.ft** | 1.85 Million Sq.ft | 1.10 Million Sq.ft | 1.45 Million Sq.ft |
| **Total Outlay** | **₹1,355.95 Crores** | ₹1,032.00 Crores | ₹234.00 Crores | ₹767.31 Crores |
| **Height Profile** | Stilt + 20 to 21 Floors | P+S+22 Floors | G + 14 Floors | 2B + G + 18 to 24 |
| **Completion Period** | 48 Months | 36 Months | 30 Months | 58 Months |
"""
}

def main():
    for path, content in docs.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
        print(f"Wrote: {os.path.basename(path)} ({len(content)} chars)")
    print("All 10 domain intelligence markdown files written successfully!")

if __name__ == "__main__":
    main()

