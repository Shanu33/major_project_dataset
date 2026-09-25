import os, shutil

base_dir = r"c:\Users\shahnawaz khan\OneDrive\Documents\DataRequirement\Paras-Dews-Sector-106-Gurugram"

# Copy primary files to respective technical directories
brochure_src = os.path.join(base_dir, "03_Technical_Specifications_Reports", "Paras_Dews_Master_Brochure_and_Floor_Plans.pdf")
rera_src = os.path.join(base_dir, "01_Tender_NIT_PreBid", "Haryana_RERA_Project_Preview_Form_A_H_1043.html")

shutil.copy2(brochure_src, os.path.join(base_dir, "00_Core_Intelligence_Dataset", "Paras_Dews_Master_Brochure_and_Floor_Plans.pdf"))
shutil.copy2(rera_src, os.path.join(base_dir, "00_Core_Intelligence_Dataset", "Haryana_RERA_Project_Preview_Form_A_H_1043.html"))
shutil.copy2(brochure_src, os.path.join(base_dir, "04_Architectural_Drawings", "Paras_Dews_Master_Brochure_and_Floor_Plans.pdf"))
shutil.copy2(brochure_src, os.path.join(base_dir, "07_Landscape_Infrastructure", "Paras_Dews_Master_Brochure_and_Floor_Plans.pdf"))
shutil.copy2(rera_src, os.path.join(base_dir, "08_Execution_Actuals", "Haryana_RERA_Project_Preview_Form_A_H_1043.html"))

# 1. 00_Core_Intelligence_Dataset/Project_Executive_Summary_and_Data_Extraction.md
f00 = """# Project Executive Summary & Regulatory Intelligence: Paras Dews, Gurugram

## 1. Project Master Identification
- **Project Name:** Paras Dews
- **Promoter / Developer:** Sepset Properties Private Limited / Paras Buildtech India Private Limited
- **Promoter Office:** 11th Floor, Paras Twin Towers, Golf Course Road, Sector-54, Gurugram - 122002, Haryana
- **RERA Registration No.:** `118 OF 2017` / `RERA-GRG-439-2019`
- **RERA Project ID:** 1043 (Haryana Real Estate Regulatory Authority, Panchkula/Gurugram)
- **Project Site Location:** Sector 106, Dwarka Expressway, Daulatabad, Gurugram - 122001, Haryana
- **Plot Area:** **13.762 Acres** (55,693 m2 / 5.57 Hectares)
- **Project Typology:** Private High-Rise Residential Group Housing Complex (6 High-Rise Towers)
- **Tower Heights:** 24 Storeys each (**2 Basements + Ground + 23 Upper Floors**)
- **Total Residential Units:** **724 Homes** across 6 Towers (plus EWS component)
- **Occupancy Certificate (OC) Status:** Formally Issued & Uploaded on **04-August-2023** (Ready-to-Move)

## 2. RERA Official Cost Structure (Form A-H Filing)
- **Total Estimated Project Cost:** **Rs 81,201.06 Lakhs** (Rs 812.01 Crores)
  - **Land Cost:** Rs 19,933.00 Lakhs (Rs 199.33 Crores)
  - **Estimated Cost of Apartment Construction:** Rs 27,256.36 Lakhs (Rs 272.56 Crores)
  - **Estimated Cost of Infrastructure & Site Structures:** Rs 7,200.17 Lakhs (Rs 72.00 Crores)
  - **Other Costs (EDC, IDC, Taxes, Statutory Levies):** Rs 26,811.53 Lakhs (Rs 268.12 Crores)
- **Total Civil & Development Direct Cost:** **Rs 34,456.53 Lakhs** (~Rs 344.57 Crores)

## 3. Tower-by-Tower Unit & Carpet Area Distribution
Verified directly from Haryana RERA Form A-H filings:

| Tower | Total Units | Total Carpet Area (m2) | Booked / Sold Units | Construction Status (At Filing) |
| :--- | :---: | :---: | :---: | :---: |
| **Tower A** | 95 Units | 10,386 m2 | 94 Units | 100% Complete |
| **Tower B** | 196 Units | 20,148 m2 | 196 Units | 100% Complete |
| **Tower C** | 188 Units | 19,326 m2 | 187 Units | 100% Complete |
| **Tower D** | 75 Units | 9,825 m2 | 74 Units | 100% Complete |
| **Tower E** | 102 Units | 8,058 m2 | 67 Units | 95% Complete |
| **Tower F** | 68 Units | 5,372 m2 | 39 Units | 95% Complete |
| **Total** | **724 Units** | **73,115 m2** | **657 Units** | **100% Complete (OC Received 2023)** |
"""

with open(os.path.join(base_dir, "00_Core_Intelligence_Dataset", "Project_Executive_Summary_and_Data_Extraction.md"), "w", encoding="utf-8") as f:
    f.write(f00)

# 2. 01_Tender_NIT_PreBid/RERA_Regulatory_Framework_and_License_Parameters.md
f01 = """# Regulatory Framework & Statutory Approvals: Paras Dews

## 1. Haryana RERA Registration Details
- **Authority:** Haryana Real Estate Regulatory Authority (HARERA)
- **Registration Certificate No.:** `118 OF 2017` / `RERA-GRG-439-2019`
- **Scrutiny Date:** Initially scrutinized on 03-Feb-2020; Extension No. 05 of 2022 approved on 28-Nov-2022.
- **Bank Account for Escrow Deposits:** IndusInd Bank Ltd., Sushant Lok Phase-1, Branch Mohali (A/c No. 25124456100).

## 2. Statutory Clearances & Approvals Log
All major clearances obtained from Haryana state agencies:
1. **DTCP Group Housing License:** License along with schedule of land for 13.762 Acres in Daulatabad, Sector 106, Gurugram.
2. **Road Access Approval:** Obtained from Gurugram Metropolitan Development Authority (GMDA) on 09-05-2022.
3. **Water Supply Connection:** Approval obtained from GMDA on 09-05-2022.
4. **State Environment Impact Assessment Authority (SEIAA):** Environmental Clearance obtained on 18-06-2019.
5. **State Pollution Control Board (HSPCB):** Consent to Establish/Operate obtained on 18-06-2019.
6. **Fire Safety Scheme & NOC:** Obtained from Commissioner Municipal Corporation / Fire Authority on 14-09-2018 (Tower D & EWS Fire NOC re-validated on 28-02-2020).
7. **Airports Authority of India (AAI):** Height clearance renewed up to 05-12-2019.
8. **Occupancy Certificate (OC):** Formally uploaded and certified on **04-August-2023**.
"""

with open(os.path.join(base_dir, "01_Tender_NIT_PreBid", "RERA_Regulatory_Framework_and_License_Parameters.md"), "w", encoding="utf-8") as f:
    f.write(f01)

# 3. 02_Cost_BOQ_Makes/RERA_Cost_Breakdown_and_Unit_Pricing_Intelligence.md
f02 = """# Cost Breakdown & Unit Pricing Benchmark: Paras Dews

## 1. Regulatory Capital Cost Breakdown (Haryana RERA Form-C)
- **Land Acquisition Cost:** Rs 19,933.00 Lakhs (~Rs 199.33 Crores)
- **Apartment Superstructure Construction:** Rs 27,256.36 Lakhs (~Rs 272.56 Crores)
- **Internal Infrastructure & Common Facilities:** Rs 7,200.17 Lakhs (~Rs 72.00 Crores)
  - Roads & Pavements: Rs 295.30 Lakhs
  - Water Supply Network: Rs 412.18 Lakhs
  - Clubhouse & Community Centre: Rs 446.99 Lakhs
  - Parks & Green Landscaping: Rs 10.00 Lakhs
- **Government Levies, EDC, IDC & Statutory Taxes:** Rs 26,811.53 Lakhs (~Rs 268.12 Crores)
- **Total Project Outlay:** **Rs 81,201.06 Lakhs** (~Rs 812.01 Crores)

## 2. Residential Unit Typology & Market Pricing
- **2BHK Apartments (1,385 sq.ft. Saleable / RERA Carpet ~85-90 m2):**
  - Configuration: 2 Bedrooms + Living/Dining + Kitchen + 2 Toilets + Utility Balcony
  - Sale Price Range: Rs 1.05 - Rs 1.20 Crores
- **3BHK Standard Apartments (1,760 sq.ft. Saleable):**
  - Configuration: 3 Bedrooms + Living/Dining + Kitchen + 3 Toilets + Balconies
  - Sale Price Range: Rs 1.40 - Rs 1.65 Crores
- **3BHK + Servant Room (1,900 sq.ft. Saleable):**
  - Configuration: 3 Bedrooms + Living/Dining + Kitchen + 3 Toilets + Servant Room & Toilet
  - Sale Price Range: Rs 1.25 - Rs 1.55 Crores
- **4BHK + Servant Room (2,350 sq.ft. Saleable):**
  - Configuration: 4 Bedrooms + Family Lounge + Kitchen + 4 Toilets + Servant Quarter
  - Sale Price Range: Rs 1.80 - Rs 2.10 Crores
- **4BHK Penthouses (4,150 sq.ft. Saleable):**
  - Configuration: Duplex Penthouse with private terrace deck, plunge pool space, and panoramic Dwarka Expressway views
  - Sale Price: Up to Rs 4.94 Crores
"""

with open(os.path.join(base_dir, "02_Cost_BOQ_Makes", "RERA_Cost_Breakdown_and_Unit_Pricing_Intelligence.md"), "w", encoding="utf-8") as f:
    f.write(f02)

# 4. 03_Technical_Specifications_Reports/Architectural_Finishes_and_Material_Specifications.md
f03 = """# Architectural Finishes & Engineering Specifications

Extracted from RERA Unit-Wise Specifications & Technical Brochure:

## 1. Living, Dining & Foyer
- **Flooring:** Premium Imported Botticino Italian Marble.
- **Walls:** Plastic emulsion paint over POP punning with cornice details.
- **Ceiling:** Oil Bound Distemper / Plastic emulsion with designer false ceiling perimeters.
- **Doors/Windows:** Hardwood frame with European style polished molded skin doors; UPVC/powder coated aluminum sliding windows with tinted glass.

## 2. Bedrooms & Private Suites
- **Master Bedroom:** Laminated wooden flooring, acrylic emulsion paint, premium modular wardrobe spaces.
- **Other Bedrooms:** Large-format vitrified tiles (600x600mm / 800x800mm), plastic emulsion.
- **Balconies:** Anti-skid ceramic tiles, weather-proof exterior texture paint, MS safety railing.

## 3. Kitchen Specifications
- **Counter Top:** Polished premium granite counter with double-bowl stainless steel sink.
- **Dado:** Ceramic wall tiles up to 2'-0" above the counter.
- **Flooring:** Anti-skid vitrified / ceramic tiles.
- **Fixtures:** Premium CP fittings of Jaquar / Kohler or equivalent make, provision for piped natural gas (PNG) and RO system.

## 4. Bathrooms & Sanitary
- **Dado:** Designer glazed ceramic tiles up to 7'-0" / false ceiling height.
- **Flooring:** Anti-skid ceramic tiles.
- **Fixtures:** Wall-hung European water closets (EWC) with concealed cisterns, granite vanity counters, glass shower partition in master bath.
"""

with open(os.path.join(base_dir, "03_Technical_Specifications_Reports", "Architectural_Finishes_and_Material_Specifications.md"), "w", encoding="utf-8") as f:
    f.write(f03)

# 5. 04_Architectural_Drawings/Master_Site_Plan_and_Tower_Layout_Catalog.md
f04 = """# Master Site Planning & Architectural Drawings Catalog

## 1. Master Site Planning (13.762 Acres)
- **Zoning:** Group housing residential development comprising 6 high-rise towers positioned around a central landscaped courtyard.
- **Vehicular & Pedestrian Segregation:** Peripheral vehicular ring roadway ensuring a central vehicle-free pedestrian podium and landscaped greens.
- **Clubhouse Complex:** Standalone multi-storey clubhouse with swimming pool, gymnasium, indoor badminton, squash courts, and community banquet hall.

## 2. Approved Architectural Drawings Registered with HARERA
As listed in the official RERA document schedule:
- `Drawing 01`: Complete Set of Approved Building Plans (DTCP Haryana)
- `Drawing 09 & 46`: Section Y-Y and Section X-X, Tower D
- `Drawing 17 & 25`: Community Building Architectural Floor Plans & Elevations
- `Drawing 18 & 52`: Elevation 2-2 and Elevation 1-1, Tower B
- `Drawing 22, 26, 27, 29`: Elevations A, B, C, D, Tower D
- `Drawing 23 & 41`: Ground Floor Plan & Typical Floor Plan, Tower B
- `Drawing 30`: Cross Section X-X, Tower B
- `Drawing 35 & 50`: Elevation 2-2 and Elevation 1-1, Tower A
- `Drawing 43`: Ground & Typical Floor Plan & Area Statement, Tower D
- `Drawing 44`: Penthouse Floor Plan, Tower A
- `Drawing 45`: Section X-X, Tower A
- `Drawing 47`: Terrace Floor Plan, Tower B
- `Drawing 48`: Typical 6th to 23rd Floor Plan & Terrace Plan, Tower A
- `Drawing 61`: Approved Master Site Plan for Group Housing Scheme
"""

with open(os.path.join(base_dir, "04_Architectural_Drawings", "Master_Site_Plan_and_Tower_Layout_Catalog.md"), "w", encoding="utf-8") as f:
    f.write(f04)

# 6. 05_Structural_Drawings/Structural_System_and_Seismic_Design_Notes.md
f05 = """# Structural Engineering System & Seismic Design Notes

## 1. Substructure & Foundation Design
- **Substructure Depth:** 2 Common Basements (car parking, water reservoirs, pump house, STP, sub-station).
- **Foundation System:** Heavy RCC Raft Foundation with peripheral RCC retaining walls and waterproofing membrane system.
- **Excavation & Shoring:** Deep open excavation with soil nail / soldier pile retention during substructure phase.

## 2. Superstructure Framing System
- **Structural System:** Reinforced Cement Concrete (RCC) shear wall and moment-resisting framed structure (2B+G+23 storeys).
- **Seismic Code Compliance:** Designed conforming to IS 1893 (Criteria for Earthquake Resistant Design of Structures) for **Seismic Zone IV** and IS 13920 (Ductile Detailing of Reinforced Concrete Structures).
- **Wind Load Design:** Engineered to resist high-velocity wind pressures conforming to IS 875 (Part 3) for Gurugram region.
- **Fire Safety Standards:** Structural fire resistance rating of 2 hours for primary structural elements conforming to NBC 2016 Part 4.
"""

with open(os.path.join(base_dir, "05_Structural_Drawings", "Structural_System_and_Seismic_Design_Notes.md"), "w", encoding="utf-8") as f:
    f.write(f05)

# 7. 06_MEP_Services/MEP_Building_Services_and_Utility_Schedule.md
f06 = """# MEP Engineering Services & Common Infrastructure

## 1. Electrical & Power Backup
- **Power Incomer:** Dual incomer sub-station receiving high-tension power from DHBVN / GMDA grid.
- **100% Power Backup:** Heavy-duty acoustic enclosed diesel generator sets providing automated 100% power backup for all common services, lifts, and residential apartments.
- **Wiring & Switching:** Fire-retardant low-smoke (FRLS) multi-strand copper wiring with modular switches and MCB/ELCB distribution boards.

## 2. Plumbing & Public Health Engineering
- **Dual Water Supply Network:** Dual pipeline system supplying municipal treated potable water for domestic use and recycled STP water for flushing and horticulture.
- **Sewage Treatment Plant (STP):** Tertiary-level biological sewage treatment facility installed in basement/ground utility zone.
- **Rainwater Harvesting:** Recharge pits with de-silting chambers installed along site perimeter conforming to CGWA norms.

## 3. Fire Protection & Vertical Transportation
- **Fire Fighting:** Dedicated fire water storage tank, main electric pump, diesel standby pump, jockey pump, external yard hydrants, wet risers in all staircases, and automatic fire sprinkler heads.
- **Elevators:** High-speed automatic passenger elevators and separate stretcher/service elevators per tower with ARD (Automatic Rescue Device) and intercom.
"""

with open(os.path.join(base_dir, "06_MEP_Services", "MEP_Building_Services_and_Utility_Schedule.md"), "w", encoding="utf-8") as f:
    f.write(f06)

# 8. 07_Landscape_Infrastructure/Site_Master_Planning_and_Clubhouse_Amenities.md
f07 = """# Landscape Architecture & Community Amenities Schedule

## 1. Site Infrastructure & Open Spaces
- **Gross Land Area:** 13.762 Acres with large central open green expanse.
- **Peripheral Roadway:** 295.30 Lakhs spent on wide concrete/asphalt circulation roads with street lighting, storm water RCC drainage, and pedestrian sidewalks.
- **Landscaping Greenery:** Central gardens, themed flower beds, jogging tracks, children's play park, and reflexology pathways.

## 2. The Club Dews (Clubhouse & Amenities)
- **Expenditure:** Rs 446.99 Lakhs spent on dedicated community recreation center.
- **Sports & Fitness:**
  - Full-size outdoor swimming pool and separate toddlers' splash pool.
  - Fully equipped modern gymnasium with cardio and strength training sections.
  - Indoor badminton court and squash court.
  - Outdoor tennis court and half basketball court.
- **Social & Leisure Spaces:**
  - Multi-purpose banquet and party hall for residents.
  - Billiards, table tennis, and cards room.
  - Daily convenience shopping retail arcade within premises.
  - Dedicated senior citizen gazebos and meditation pavilions.
"""

with open(os.path.join(base_dir, "07_Landscape_Infrastructure", "Site_Master_Planning_and_Clubhouse_Amenities.md"), "w", encoding="utf-8") as f:
    f.write(f07)

# 9. 08_Execution_Actuals/Project_Completion_and_Occupancy_Certificate_Charter.md
f08 = """# Project Completion, Delivery Tracking & Occupancy Certificate Charter

## 1. Project Execution Timeline
- **Launch / RERA Registration Date:** 28 August 2017 (HARERA Reg. No. 118 of 2017).
- **Physical Progress Milestones:**
  - Towers A, B, C, D completed (100% physical execution achieved).
  - Towers E and F completed (95% to 100% achieved).
- **Occupancy Certificate (OC):** Formally granted by DTCP Haryana and uploaded to Haryana RERA on **04-August-2023**.
- **Current Status:** Fully completed, delivered, and operational (Ready-to-Move with active residents).

## 2. Utility & Service Investment Accounting
As audited and registered with Haryana RERA:
- Total investment in project as of final filing: **Rs 7,942.67 Lakhs** (Rs 79.43 Cr) incremental capital outlay against remaining works.
- Booked allottees: 657 units booked out of 724 total units (over 90% sales absorption).
- Balance recovery due from allottees upon possession handover: Rs 577.30 Lakhs.
- Project delivered without default or incomplete civil works.
"""

with open(os.path.join(base_dir, "08_Execution_Actuals", "Project_Completion_and_Occupancy_Certificate_Charter.md"), "w", encoding="utf-8") as f:
    f.write(f08)

print("Successfully generated all 9 domain intelligence markdown documents for Paras Dews!")

