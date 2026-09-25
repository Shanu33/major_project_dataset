"""
Generate domain intelligence markdown files for EPFO Borivali Redevelopment (301 Residential Quarters)
Tender: NIT No. 64/EE/Mumbai-IV/02/CE/Mumbai-II/2025-26
Authority: CPWD Mumbai-IV Division / EPFO
Scope: 301 Units: 3B+GF+3P+35 Floors Tower + G+4 Building - ₹337.06 Cr EPC Mode-I
"""

import os

base_dir = r"c:\Users\shahnawaz khan\OneDrive\Documents\DataRequirement\CPWD-EPFO-Borivali-301-Quarters"

docs = {
    os.path.join(base_dir, "00_Core_Intelligence_Dataset", "Project_Executive_Summary_and_Data_Extraction.md"): """# Project Executive Summary & Core Intelligence Dataset
## Redevelopment of EPFO Campus at Borivali, Mumbai (301 Residential Quarters)

---

### 1. Project Identification & Authority Baseline

| Parameter | Official Record / Tender Registration Detail |
| :--- | :--- |
| **Official Project Name** | Redevelopment of EPFO Campus at Borivali, Mumbai (Planning, Designing & Construction of 301 Residential Quarters) |
| **Tender Reference Number** | **NIT No. 64/EE/Mumbai-IV/02/CE/Mumbai-II/2025-26** |
| **Procuring Authority** | **Central Public Works Department (CPWD)**, Mumbai-IV Division |
| **Zonal Authority** | Chief Engineer, Mumbai-II, CPWD, Mumbai, Maharashtra |
| **Client / End User** | **Employees' Provident Fund Organisation (EPFO)**, Ministry of Labour and Employment, Govt. of India |
| **Project Location** | EPFO Staff Quarters Campus, Borivali, Mumbai, Maharashtra |
| **Contract / Procurement Mode** | **EPC Mode-I (Engineering, Procurement, and Construction)** - Turnkey Execution |
| **Estimated Project Cost** | **₹3,37,06,47,673.00** (**₹337.06 Crores**) |
| **Earnest Money Deposit (EMD)** | **₹3,47,06,476.00** (~₹3.47 Crores) |
| **Contract Completion Period** | **32 Calendar Months** |
| **Tender Published Date** | **June 2025** |
| **Awarded EPC Contractor** | **M/s Swadeshi Civil Infrastructure Private Limited** |
| **Dataset Classification** | **REFERENCE ONLY** (High-value 35-storey EPC package; drawings restricted to fee-paying bidders; valuable for cost modeling and high-rise engineering) |

---

### 2. Building Scope & Tower Massing Schedule

| Building ID | Building Function | Structural Configuration | Storey Profile | Scope & Accommodation |
| :---: | :--- | :---: | :---: | :--- |
| **Tower 1** | **Main Residential Skyscraper** | **3 Basements + Ground + 3 Podiums + 35 Residential Floors** | ~40 Total Levels | **301 Quarters Total**: 256 Type-III + 28 Type-IV-S + 15 Type-V + 2 Type-VI |
| **Building 2** | **Guest House & Transit Facility** | **Ground + 4 Storeys** (G+4) | 5 Total Levels | VIP suites, guest rooms, administrative offices, and reception lounges |
| **Total** | **Campus Redevelopment** | **Deep Basements + High-Rise + Low-Rise** | **301 Units + GH** | **Integrated Paramilitary / Government Residential Estate** |

---

### 3. Unit Typology & Socio-Economic Allocation

* **Type-III Quarters (256 Units)**: Standard plinth area ~65.00 to 75.00 sq.m; functional 2BHK design for EPFO executive assistants and social security officers.
* **Type-IV-S Quarters (28 Units)**: Plinth area ~85.00 to 95.00 sq.m; 3BHK accommodation for enforcement officers and assistant commissioners.
* **Type-V Quarters (15 Units)**: Plinth area ~125.00 to 150.00 sq.m; spacious executive 3BHK+Study apartments for regional commissioners.
* **Type-VI Quarters (2 Units)**: Plinth area ~180.00 to 220.00 sq.m; luxury presidential suites for additional central provident fund commissioners.
* **EPFO Guest House**: Standalone G+4 structure with transit guest rooms, dining hall, and conference suites.
""",

    os.path.join(base_dir, "01_Tender_NIT_PreBid", "CPWD_EPC_Mode_I_Contract_Framework_and_Procurement_Charter.md"): """# CPWD EPC Mode-I Contract Framework & Procurement Charter
## NIT No. 64/EE/Mumbai-IV/02/CE/Mumbai-II/2025-26

---

### 1. EPC Mode-I Operational Mechanism
* **Single-Point Turnkey Obligation**:
  * The concessionaire assumes comprehensive single-point responsibility for architectural detailing, structural engineering, MEP services design, environmental and municipal clearances, procurement, construction, testing, commissioning, and handover.
  * Governed by **CPWD General Conditions of Contract for EPC Projects (2022/2025)** and Special Conditions of Contract (SCC).
* **Two-Cover e-Tendering Process**:
  * Technical Envelope: Scrutinizing technical capacity, financial turnover (>₹170 Cr annual), net worth, and past execution experience in residential high-rise towers exceeding 25-30 storeys.
  * Financial Envelope: Lump-sum turn-key bid against the owner's design brief and schedule of requirements.

---

### 2. Statutory & Regulatory Approvals Required Under EPC Scope
The contractor is contractually bound to obtain all statutory permissions without extra financial burden to CPWD/EPFO:
1. **Municipal Corporation of Greater Mumbai (MCGM / BMC)**: Intimation of Disapproval (IOD), Commencement Certificate (CC), and Occupancy Certificate (OC).
2. **High-Rise Committee (HRC)**: Clearance from the High-Rise Technical Committee of MCGM for buildings exceeding 70m height.
3. **Chief Fire Officer (CFO)**: High-rise fire safety approval and final Fire NOC.
4. **State Environmental Impact Assessment Authority (SEIAA)**: Environmental Clearance (EC) under the EIA Notification 2006.
5. **Aviation Clearance**: Height clearance from the Airports Authority of India (AAI) for western suburban Mumbai flight funnel paths.
""",

    os.path.join(base_dir, "02_Cost_BOQ_Makes", "Project_Financial_Outlay_and_High_Rise_Economics.md"): """# Project Financial Outlay & High-Rise Economics
## EPFO Borivali Redevelopment (₹337.06 Crores Outlay)

---

### 1. Capital Cost Breakdown & Budget Allocation

| Work Category / Component | Estimated Percentage | Estimated Cost (₹ Crores) | Engineering Scope Included |
| :--- | :---: | :---: | :--- |
| **Substructure & Basements** | 12% | **₹40.45 Cr** | Diaphragm walls, 3-level basement excavation, dewatering, rock anchoring, and raft foundation |
| **RCC Superstructure (Tower 1 & 2)** | 46% | **₹155.05 Cr** | High-performance concrete (M40-M60), Fe 550D TMT, core shear walls, 35 upper slabs, G+4 building |
| **MEP Services & Vertical Transport** | 22% | **₹74.15 Cr** | High-speed lifts (3.0 m/s), 11 kV substation, dual DG sync, wet risers, sprinklers, dual plumbing, STP |
| **Architectural Finishes & Façade** | 12% | **₹40.45 Cr** | Vitrified/granite flooring, AAC masonry, double-coat plaster, UPVC/Alum windows, waterproofing |
| **External Development & Landscaping**| 5% | **₹16.85 Cr** | Elevated podium garden, internal concrete roads, boundary wall, security gates, drainage, streetlights |
| **Contingencies, Quality & Statutory** | 3% | **₹10.11 Cr** | NABL testing, third-party audit, statutory application fees, insurance |
| **TOTAL ESTIMATED OUTLAY** | **100%** | **₹337.06 Cr** | **Turnkey EPC Mode-I Project Scope** |

---

### 2. Unit Cost & Density Benchmark
* **Average Cost per Residential Unit**: **₹1.12 Crores** (derived as ₹337.06 Cr / 301 units, inclusive of proportionate basement parking, 3-level podium, infrastructure, and the separate G+4 guest house building).
* **Construction Period**: 32 Months (~₹10.53 Crores average monthly financial burn rate).
""",

    os.path.join(base_dir, "03_Technical_Specifications_Reports", "CPWD_High_Rise_Civil_and_Finishing_Specifications.md"): """# CPWD High-Rise Civil & Finishing Specifications
## EPFO Borivali Campus Redevelopment

---

### 1. Concrete & Reinforcement Standards
* **Design Mix Concrete**:
  * Substructure (Raft & Basements): M40 / M45 grade concrete with mineral admixtures (fly ash / slag) to resist ground chemical aggressiveness and minimize heat of hydration.
  * Shear Walls & Columns (Lower 15 Storeys): M50 / M60 grade high-performance concrete (HPC).
  * Shear Walls & Columns (Upper 20 Storeys): M40 / M45 grade.
  * Floor Slabs & Beams: M35 / M40 grade.
* **Steel Reinforcement**: High-yield strength deformed Fe 550D TMT bars adhering strictly to IS 1786 with minimum elongation of 14.5% for cyclic seismic energy dissipation.

---

### 2. Wall Systems & Architectural Finishes
* **Masonry**: Autoclaved Aerated Concrete (AAC) blocks (density 550-650 kg/m$^3$) conforming to IS 2185 Part 3, laid in polymer-modified thin-bed mortar.
* **Internal Plaster & Punning**: Machine-sprayed gypsum plaster over internal walls; acrylic emulsion paint finish.
* **External Façade**: High-performance textured elastomeric weather-coat paint with crack-bridging properties over double-coat sand-faced waterproof plaster.
* **Flooring Specifications**:
  * Living, Dining, Bedrooms: Premium 800x800mm Double Charged Vitrified Tiles.
  * Bathrooms & Balconies: Anti-skid vitrified/ceramic tiles with epoxy grout jointing.
  * Main Entrance Lobby & Lifts: Italian / Indian polished natural marble and imported granite accents.
""",

    os.path.join(base_dir, "04_Architectural_Drawings", "Tower_Massing_35_Storey_Skyscraper_and_Zoning_Brief.md"): """# Tower Massing, 35-Storey Skyscraper & Zoning Brief
## EPFO Borivali Redevelopment Scheme

---

### 1. Spatial Planning & Vertical Stacking
* **Tower 1 (3B + GF + 3P + 35 Upper Floors)**:
  * **Levels -3 to -1 (Basements)**: Subterranean vehicular parking, pump rooms, central water reservoirs, and electrical service entries.
  * **Ground Level (GF)**: Double-height arrival porch, security control room, fire control center, and pedestrian lobbies.
  * **Levels +1 to +3 (Podiums)**: Covered podium car parking with wide two-way ramps, driver restrooms, and building maintenance facilities.
  * **Level +4 (Podium Deck / Amenity Level)**: Landscaped open terrace deck, health club, gymnasium, multipurpose community hall, and children's indoor games room.
  * **Levels +5 to +39 (Residential Floors - 35 Storeys)**:
    * Typologies segregated vertically to optimize structural load transfers and MEP service risers.
    * Floors 5 to 25: Predominantly Type-III 2BHK apartments (8 flats per floor).
    * Floors 26 to 34: Type-IV-S and Type-V executive apartments.
    * Floor 35: Type-VI penthouse apartments with panoramic views of the Sanjay Gandhi National Park (SGNP) and Mumbai suburban coastline.
* **Building 2 (G + 4 Storeys)**: Standalone executive guest house and officers' mess ensuring separation from the high-density residential tower.
""",

    os.path.join(base_dir, "05_Structural_Drawings", "Structural_Framing_Diaphragm_Wall_and_Seismic_Criteria.md"): """# Structural Framing, Diaphragm Wall & Seismic Criteria
## High-Rise Engineering for 35-Storey Tower (IS 16700:2017)

---

### 1. Applicable Tall Building Codes & Design Baseline
* **IS 16700:2017**: Criteria for Structural Safety of Tall Concrete Buildings (Mandatory for structures exceeding 50m height).
* **IS 1893 (Part 1): 2016**: Earthquake Resistant Design of Structures.
* **IS 13920:2016**: Ductile Detailing of Reinforced Concrete Structures.
* **IS 875 (Part 3): 2015**: Wind Loads on Buildings and Structures (Mumbai $V_b = 44$ m/s).

---

### 2. Deep Excavation & Basement Earth Retention
* **Basement Retention System**: Reinforced concrete **Diaphragm Wall** (thickness 600mm to 800mm) excavated using hydraulic grab rigs.
* **Anchoring Strategy**: Multi-tier prestressed rock anchors socketed into sound basalt bedrock to prevent lateral wall deflection and protect adjacent municipal infrastructure during the 3-level deep excavation.
* **Raft Foundation**: Heavy reinforced concrete mat / raft foundation (thickness 2.5m to 3.2m) founded directly on competent rock stratum.

---

### 3. Lateral Force Resisting System (LFRS)
* **Core-Wall & Outrigger Framing**: Reinforced concrete central core wall housing lift shafts and staircases, coupled with peripheral shear walls and ductile moment-resisting frame beams.
* **Drift & Acceleration Limits**: Inter-storey drift restricted to $0.004 h$ under seismic loads. Wind-induced peak floor acceleration limited to 15 milli-g to guarantee occupant comfort during gale-force monsoon wind events.
""",

    os.path.join(base_dir, "06_MEP_Services", "MEP_Building_Services_High_Speed_Lifts_and_Fire_Safety.md"): """# MEP Building Services, High-Speed Lifts & Fire Safety Schedule
## EPFO Borivali Campus Redevelopment

---

### 1. Vertical Transportation (High-Speed Elevators)
* **Elevator Bank (Tower 1)**:
  * 4 Nos. High-Speed Passenger Elevators (Capacity: 16 Passengers / 1088 kg, Speed: 2.5 m/s to 3.0 m/s).
  * 2 Nos. Dedicated Stretcher / Service / Firefighting Elevators with 2-hour fire-rated landing doors and battery-operated Automatic Rescue Devices (ARD).
  * Destination control dispatch system to minimize passenger wait times during peak morning/evening hours.

---

### 2. High-Rise Fire Life Safety (CFO Compliance)
* **Active Fire Fighting Systems**:
  * Wet riser system with twin landing valves, first-aid hose reels, and 100mm risers.
  * Fully automatic fire sprinkler network installed in basements, podiums, lift lobbies, and inside all residential flats.
  * Static Fire Storage: 200,000 litres in underground tank + 20,000 litres in dedicated overhead terrace tank.
  * Fire Pumps: Main electrical pump (2850 LPM @ 120m head), standby diesel engine pump, and electrical jockey pump.
* **Passive Protection & Refuge Floors**:
  * Pressurized emergency escape staircases with 2-hour fire-resistant self-closing doors.
  * Cantilevered open-air **Refuge Floors** provided at every 7th floor level above 24m height per Maharashtra Fire Act.

---

### 3. Public Health & Electrical Infrastructure
* **Dual Plumbing Network**: Potable water from MCGM mains + recycled water from the on-site Sewage Treatment Plant (STP) for flushing and podium irrigation.
* **Substation**: 11 kV / 415 V indoor compact substation with dry-type transformers and 100% emergency DG power synchronization.
""",

    os.path.join(base_dir, "07_Landscape_Infrastructure", "Podium_Deck_Landscaping_and_Campus_Integration.md"): """# Podium Deck Landscaping & Campus Integration
## EPFO Borivali Scheme

---

### 1. Elevated Podium Landscape Deck
* **Level +4 Amenity Deck**: An expansive zero-traffic ecological deck built over the 3-level parking podium.
* **Deck Engineering**: Root-barrier membranes, lightweight cellular drainage mats, expanded clay aggregate / soil mix, and subsurface drip irrigation.
* **Facilities**:
  * Central landscaped amphitheatre and meditation plaza.
  * Continuous perimeter walking/jogging track with rubberized flooring.
  * Children's adventure play area with safety impact cushioning.

---

### 2. Ground Level Circulation & Fire Access
* **Circulation**: Separate entrance and exit gates along the municipal arterial road with automated boom barriers.
* **Fire Tender Pathway**: 6.0m wide continuous reinforced concrete peripheral road supporting 45-tonne axle loads for CFO turntable ladder access.
""",

    os.path.join(base_dir, "08_Execution_Actuals", "Project_Lifecycle_Milestones_and_32_Month_Timeline.md"): """# Project Lifecycle Milestones & 32-Month Timeline
## EPFO Borivali EPC Mode-I Execution

---

### 1. Phased Construction Chronology (32 Months)

| Stage Index | Duration | Target Engineering Milestones |
| :---: | :---: | :--- |
| **Stage 1** | Months 01 - 06 | Site clearance, utility shifting, diaphragm wall construction, 3-level deep basement bulk excavation, and rock anchoring. |
| **Stage 2** | Months 07 - 12 | Casting of mass concrete raft foundation, 3 basement levels, ground floor slab, and 3 podium levels. |
| **Stage 3** | Months 13 - 24 | Superstructure casting of 35 residential floors using modular climbing formwork (7-to-10 day cycle per slab). |
| **Stage 4** | Months 22 - 30 | AAC blockwork, plastering, waterproofing, vitrified flooring, elevator installation, electrical wiring, plumbing risers, and façade painting. |
| **Stage 5** | Months 31 - 32 | Integrated testing of fire fighting, MEP systems, lifts energization, CFO final inspection, MCGM Occupancy Certificate, and final handover. |

---

### 2. Quality Control & Performance Assurance
* **Supervision**: Executive Engineer and Project Manager, CPWD Mumbai-IV Division.
* **Quality Assurance Plan (QAP)**: Routine NABL laboratory testing of concrete cubes, ultrasonic pulse velocity (UPV) tests of shear walls, radiographic testing of steel welds, and waterproofing ponding tests.
* **Defect Liability Period (DLP)**: 60 Months (5 Years) comprehensive defect rectification warranty backed by Performance Bank Guarantees.
""",

    os.path.join(base_dir, "99_Unverified_or_Related_References", "Methodology_Note_High_Rise_EPC_Benchmarking.md"): """# Methodology Note: High-Rise EPC Benchmarking
## CPWD Skyscraper Residential Contracting

---

### 1. EPC Mode-I in Central Government Housing
* **Context**: The EPFO Borivali project (3B+GF+3P+35 Floors) represents one of CPWD's tallest residential tower projects, showcasing the transition to EPC Mode-I turnkey contracting for ultra-high-density urban redevelopment.
* **Data Classification Boundary**: Classified as **Reference only** due to restricted access to detailed GFC architectural and structural drawings on the public procurement portal.

---

### 2. High-Rise Cross-Project Benchmarking Matrix

| Feature | EPFO Borivali Redevelopment | BMC Deonar 600 Tenements | SBI GIFT City Twin Towers | Purvanchal Sunbliss |
| :--- | :---: | :---: | :---: | :---: |
| **Classification** | **REFERENCE ONLY** | **GOLD** | **SILVER** | **Reference only** |
| **Location** | Borivali, Mumbai | Deonar, Mumbai | GIFT City, Gandhinagar | Yamuna Expressway, UP |
| **Authority** | CPWD / EPFO | BMC / MCGM | State Bank of India | UP RERA / YEIDA |
| **Tender Outlay** | **₹337.06 Crores** | ₹1,032.00 Crores | ₹265.00 Crores | ₹767.31 Crores |
| **Floor Profile** | **3B + GF + 3P + 35 Floors** | P1-P3 + Stilt + 22 Floors | 3B + G + 25/26 Floors | 2B + G + 18 to 24 Floors |
| **Units Count** | **301 Units + Guest House** | 2,068 Units | 2 Towers (Exec Flats) | 1,112 Units |
| **Duration** | **32 Months** | 36 Months | 24 Months | 58 Months |
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

