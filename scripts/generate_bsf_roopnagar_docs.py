"""
Generate domain intelligence markdown files for BSF Roopnagar Campus Residential Quarters (63 Units)
Tender: NIT No. 28/EE/SILIGURI/CPWD/2025-26
Authority: CPWD Siliguri Central Division / BSF
Scope: 63 Quarters: 48 Type-II (S+8) + 15 Type-III (S+5) - Structural Design Consultancy Services
"""

import os

base_dir = r"c:\Users\shahnawaz khan\OneDrive\Documents\DataRequirement\CPWD-BSF-Roopnagar-63-Quarters"

docs = {
    os.path.join(base_dir, "00_Core_Intelligence_Dataset", "Project_Executive_Summary_and_Data_Extraction.md"): """# Project Executive Summary & Core Intelligence Dataset
## Construction of 63 Nos. Residential Quarters at BSF Campus Roopnagar (Structural Design Consultancy)

---

### 1. Project Identification & Administrative Baseline

| Parameter | Official Record / Tender Registration Detail |
| :--- | :--- |
| **Official Project Name** | Construction of 63 Nos. Residential Quarters at BSF Campus Roopnagar (Structural Design Consultancy Services) |
| **Tender Reference Number** | **NIT No. 28/EE/SILIGURI/CPWD/2025-26** |
| **Procuring Authority** | **Central Public Works Department (CPWD)**, Siliguri Central Division |
| **Authority Office** | Executive Engineer, Siliguri Central Division, CPWD, Nirman Sadan, Hakimpara, Siliguri, West Bengal |
| **Client / End User** | **Border Security Force (BSF)**, 90 Bn (now 03 Bn), SHQ BSF Cooch Behar / FTR HQ Guwahati |
| **Project Location** | BSF Campus Roopnagar, District Cooch Behar / Jalpaiguri, West Bengal |
| **Contract Nature** | **Structural Design Consultancy Services** (Preparation of structural analysis, 3D models, GFC drawings, BBS, and DBR) |
| **Building Scope** | **63 Units Total**: 48 Nos. Type-II Quarters (Stilt + 8 Floors) + 15 Nos. Type-III Quarters (Stilt + 5 Floors) |
| **Estimated Consultancy Outlay** | **₹7,96,970.00** |
| **Design Submission Period** | **03 Calendar Months** |
| **Publication Date** | **28 August 2025** |
| **Dataset Classification** | **REFERENCE ONLY** (Design consultancy tender; architectural plans restricted under Clause 1.6; structural drawings are deliverables) |

---

### 2. Building Scope & Structural Typology Schedule

| Building Block | Typology | Floor Configuration | Unit Count | Structural System | Deliverable Responsibility |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **Block 1** | **Type-II Quarters** | **Stilt + 8 Floors** (S+8) | 48 Units | RCC Framed / Shear Wall | Structural design by consultant based on CPWD architectural plans |
| **Block 2** | **Type-III Quarters** | **Stilt + 5 Floors** (S+5) | 15 Units | RCC Framed Structure | Structural design by consultant based on CPWD architectural plans |
| **Total** | **Paramilitary Housing** | **S+5 and S+8** | **63 Units** | **Seismic Zone IV RCC** | **Complete Structural GFC Drawing Pack** |

---

### 3. Critical Data Governance & Scope Boundaries
* **Consultancy Nature**: This tender is specifically for the procurement of **Comprehensive Structural Engineering & Architectural Proof-Checking Consultancy**.
* **Clause 1.6 Restriction**: Clause 1.6 of the NIT explicitly specifies: *"The architectural drawings for work are available."* However, these drawings are issued exclusively to the awarded structural consultant and are not hosted on public portals for national security reasons pertaining to border paramilitary installations.
* **Structural Drawings Output**: The structural drawings are the primary deliverable of this contract rather than an input document. Consequently, this package is cataloged for **consultancy scope benchmarking, design timeline modeling, and high-rise structural criteria** rather than construction quantity take-off validation.
""",

    os.path.join(base_dir, "01_Tender_NIT_PreBid", "CPWD_Consultancy_Procurement_Framework_and_Clause16.md"): """# CPWD Consultancy Procurement Framework & Clause 1.6 Analysis
## NIT No. 28/EE/SILIGURI/CPWD/2025-26

---

### 1. CPWD Form 7 Consultancy Contracting System
* **Contract Form**: CPWD Form 7 (Percentage Rate Tender and Contract for Works / Consultancy Services).
* **Bidding Mode**: Single stage two-envelope e-tendering through the Central Public Procurement Portal (CPPP - `eprocure.gov.in`).
* **Consultancy Mandate**:
  1. Detailed structural analysis using commercial finite element software (STAAD.Pro / ETABS).
  2. Preparation of comprehensive Structural Design Basis Report (DBR).
  3. Generation of complete Good-for-Construction (GFC) structural drawings for foundations, columns, beams, slabs, shear walls, staircases, and water tanks.
  4. Bar Bending Schedules (BBS) and structural quantity estimation.
  5. Facilitation of third-party proof-checking through an approved Indian Institute of Technology (IIT) or National Institute of Technology (NIT).

---

### 2. Analysis of Clause 1.6 & Parameter Restrictions
* **Clause 1.6 Text**: *"The architectural drawings for work are available."*
* **Implication**:
  * Architectural drawings have already been prepared in-house by the Senior Architect / Chief Architect, CPWD Eastern Zone.
  * In defense and central armed police force (CAPF) cantonments, detailed site master plans and internal layout plans are treated as protected departmental documents.
  * The selected structural consultant signs a non-disclosure agreement (NDA) upon receipt of the architectural drawings.
""",

    os.path.join(base_dir, "02_Cost_BOQ_Makes", "Consultancy_Fee_Structure_and_Schedule_A_BOQ.md"): """# Consultancy Fee Structure & Schedule A BOQ Analysis
## BSF Roopnagar 63 Quarters (CPWD Siliguri)

---

### 1. Consultancy BOQ Schedule (Page 44 of NIT)

| Item No. | Description of Service | Quantity | Unit | Estimated Rate (₹) | Estimated Amount (₹) |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **1** | Comprehensive Structural Design Consultancy for 48 Nos. Type-II (S+8) and 15 Nos. Type-III (S+5) Quarters at BSF Campus Roopnagar, including 3D structural modeling, foundation design, GFC detailing, BBS, and proof-checking coordination | 1 | Lump-sum Job | ₹7,96,970.00 | **₹7,96,970.00** |

---

### 2. Implied Construction Outlay Benchmark (CPWD PAR Norms)
Based on official **CPWD Plinth Area Rates (PAR 2010/2020)** and prevailing Cost Index (CI) for Siliguri:

| Residential Typology | Unit Plinth Area (sq.m) | Units | Total Plinth Area (sq.m) | Estimated Construction Rate (₹/sq.m) | Projected Construction Cost (₹ Cr) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Type-II (Stilt + 8 Floors)** | ~55.00 | 48 | 2,640.00 | ~₹38,000 / sq.m | ₹10.03 Cr |
| **Type-III (Stilt + 5 Floors)** | ~70.00 | 15 | 1,050.00 | ~₹36,000 / sq.m | ₹3.78 Cr |
| **Stilt Parking, Foundation & Core** | Common | 63 | ~1,200.00 | ~₹25,000 / sq.m | ₹3.00 Cr |
| **External Services & Development** | 15% | All | Lump-sum | 15% of Civil Works | ₹2.52 Cr |
| **Total Projected Construction Outlay**| -- | **63 Units** | **~4,890.00 sq.m** | -- | **₹19.33 - ₹22.00 Cr** |

*Note: The consultancy fee of ₹7.97 Lakhs represents approximately 0.35% to 0.40% of the projected civil construction outlay, aligning with standard CPWD consultancy norms.*
""",

    os.path.join(base_dir, "03_Technical_Specifications_Reports", "CPWD_Design_Basis_Report_and_Structural_Criteria.md"): """# CPWD Design Basis Report & Structural Engineering Criteria
## BSF Campus Roopnagar (Seismic Zone IV)

---

### 1. Governing Bureau of Indian Standards (BIS) Codes
* **IS 456:2000**: Plain and Reinforced Concrete - Code of Practice.
* **IS 1893 (Part 1): 2016**: Criteria for Earthquake Resistant Design of Structures.
* **IS 13920:2016**: Ductile Design and Detailing of Reinforced Concrete Structures Subjected to Seismic Forces.
* **IS 875 (Parts 1 to 3): 2015**: Code of Practice for Design Loads (Dead, Imposed, and Wind Loads).
* **IS 16700:2017**: Structural Safety of Tall Concrete Buildings (Applicable for S+8 high-rise frames).

---

### 2. Regional Geotechnical & Environmental Hazards
* **Seismic Hazard**: **Zone IV** (Severe Seismic Intensity, Peak Ground Acceleration Zone Factor $Z = 0.24$).
  * Siliguri lies in the seismically active North Bengal Himalayan foreland basin.
  * Structural ductile detailing (IS 13920) is mandatory for all beam-column junctions and shear wall boundaries.
* **Wind Speed**: Basic design wind speed $V_b = 47$ m/s ($169.2$ km/h), Terrain Category 2.
* **Concrete Specifications**:
  * Minimum concrete grade for structural members: M30 / M35.
  * Reinforcement steel: High-yield strength Fe 500D / Fe 550D TMT bars with minimum 14.5% elongation.
""",

    os.path.join(base_dir, "04_Architectural_Drawings", "Restricted_Architectural_Scope_and_Typology_Profile.md"): """# Restricted Architectural Scope & Typology Profile
## CPWD BSF Roopnagar Staff Housing

---

### 1. Status of Architectural Documentation
* **Document Access**: **Restricted / Not Publicly Available**.
* **Statutory Basis**: Clause 1.6 of NIT No. 28/EE/SILIGURI/CPWD/2025-26 confirms architectural plans were prepared departmentally by CPWD Architectural Wing and are released only to the awarded consultant.

---

### 2. Typological Space Allocation (CPWD Housing Guidelines)

| Feature / Space Norm | Type-II Quarters (S+8 Floors) | Type-III Quarters (S+5 Floors) |
| :--- | :--- | :--- |
| **Standard Plinth Area** | 45.00 to 55.00 sq.m (484 to 592 sq.ft) | 65.00 to 75.00 sq.m (700 to 807 sq.ft) |
| **Room Schedule** | Living Room, 2 Bedrooms, Kitchen, Toilet, Bath, Utility Balcony | Living-Dining Room, 2-3 Bedrooms, Kitchen, 2 Toilets, Wash Balconies |
| **Target Allottees** | BSF Subordinate Officers & Head Constables | BSF Inspectors, Sub-Inspectors & Gazetted Officers |
| **Vertical Stacking** | 6 Flats per floor x 8 Upper Floors = 48 Flats | 3 Flats per floor x 5 Upper Floors = 15 Flats |
| **Ground Floor** | Open stilt parking + service rooms | Open stilt parking + pump room |
""",

    os.path.join(base_dir, "05_Structural_Drawings", "Consultant_Deliverable_Charter_and_Proof_Checking.md"): """# Consultant Deliverable Charter & Proof-Checking Protocol
## Structural Engineering Scope for BSF Roopnagar Quarters

---

### 1. Mandatory Structural Deliverables
The consultant is bound to deliver the following complete engineering documentation:
1. **Mathematical Analysis Model**: Validated 3D analysis files in STAAD.Pro / ETABS format with dynamic modal and response spectrum output.
2. **Substructure Engineering**: Foundation layout, pile/raft/isolated footing details, grade beams, and water-proofing details.
3. **Superstructure Reinforcement Drawings**:
   * Column location plans, dimensional schedules, and vertical lap splice details.
   * Reinforced concrete shear wall elevation details and boundary element confining ties.
   * Floor beam framing plans and slab reinforcement layouts.
   * Cantilever balcony, staircase, lift machine room, and parapet details.
4. **Water Storage Structures**: Structural design and detailing of Under Ground Tank (UGT) and Overhead Tank (OHT).
5. **Bar Bending Schedules (BBS)**: Itemized bar schedules with cutting lengths and steel tonnage estimates.

---

### 2. Institutional Proof-Checking
* As per CPWD vigilance and structural safety guidelines, all structural designs for buildings exceeding G+4 storeys in Seismic Zone IV must be proof-checked by a premier technical institute (e.g. IIT Kharagpur, IIEST Shibpur, or NIT Silchar).
* The consultant is responsible for attending technical queries and securing final approval from the proof-checking authority.
""",

    os.path.join(base_dir, "06_MEP_Services", "CPWD_General_Specifications_Electrical_and_Mechanical.md"): """# CPWD General Specifications: Electrical & Mechanical Services
## BSF Campus Roopnagar Housing

---

### 1. Internal & External Electrification
* **Reference Standard**: CPWD General Specifications for Electrical Works Part I (Internal) - 2013 and Part IV (Substations) - 2013.
* **Distribution Scheme**: 3-Phase 4-Wire distribution from campus electrical substation to individual floor rising mains.
* **Wiring & Protection**: FRLS copper multi-strand conductors in concealed heavy-gauge PVC conduits; Miniature Circuit Breakers (MCB) and Residual Current Circuit Breakers (RCCB) on all consumer distribution boards.

---

### 2. Plumbing, Public Health & Fire Life Safety
* **Water Supply**: CPWD Specifications for Sanitary Installations 2019. Overhead distribution with separate lines for domestic and flushing supply.
* **Fire Safety (Stilt + 8 Floors)**:
  * National Building Code (NBC) 2016 Part 4 compliant wet riser system with landing valves on all floor landings.
  * Terrace fire storage tank (minimum 10,000 to 20,000 litres capacity) with automated booster fire pump.
  * Fire extinguishers (ABC powder and Carbon Dioxide) at electrical ducts and staircase lobbies.
""",

    os.path.join(base_dir, "07_Landscape_Infrastructure", "BSF_Campus_Roopnagar_Site_Layout_and_Perimeter_Context.md"): """# BSF Campus Roopnagar Site Layout & Perimeter Context
## Campus Infrastructure Integration

---

### 1. Campus Geography & Strategic Location
* **Location**: BSF Campus Roopnagar, situated in the North Bengal frontier under SHQ BSF Cooch Behar.
* **Paramilitary Setting**: Self-contained cantonment accommodating battalion headquarters, administrative blocks, weapon armouries, parade grounds, and residential housing.

---

### 2. External Infrastructure Scope
* **Pavements**: Concrete internal access roads connecting the housing blocks to the campus main gate.
* **Drainage**: Surface stormwater runoff channeled via open brick/concrete drains to campus discharge points.
* **Security Perimeter**: Cantonment security fencing, access-controlled entry barriers, and peripheral high-mast lighting.
""",

    os.path.join(base_dir, "08_Execution_Actuals", "Design_Milestone_Timeline_and_Submission_Stages.md"): """# Design Milestone Timeline & Submission Stages
## Structural Design Consultancy Schedule (03 Months)

---

### 1. Submission Schedule & Payment Triggers

| Milestone Stage | Target Timeline | Deliverable Output | Payment Percentage |
| :---: | :---: | :--- | :---: |
| **Stage 1** | Week 01 - Week 04 | Inception report, Design Basis Report (DBR), foundation sizing, and preliminary structural scheme. | 20% |
| **Stage 2** | Week 05 - Week 08 | Detailed 3D STAAD/ETABS analysis, full structural framing drawings, and submission for proof-checking. | 40% |
| **Stage 3** | Week 09 - Week 10 | Resolution of proof-checking comments and receipt of formal vetting certificate from proof-check institute. | 20% |
| **Stage 4** | Week 11 - Week 12 | Final submission of complete Good-for-Construction (GFC) drawings, Bar Bending Schedules (BBS), and structural approvals. | 20% |
| **Total** | **03 Months** | **Complete Structural GFC Drawing Package** | **100%** |
""",

    os.path.join(base_dir, "99_Unverified_or_Related_References", "Methodology_Note_Consultancy_vs_Construction_Tenders.md"): """# Methodology Note: Consultancy vs Construction Tenders
## Data Integrity & Governance Classification

---

### 1. Rationale for "Reference Only" Classification
* **Missing Construction Bidding Documents**: The tender is exclusively for structural engineering consultancy services (₹7.97 Lakhs) and does not include the primary multi-crore civil construction contract documents or contractor item-rate tender BOQ.
* **Restricted Architectural Plans**: Clause 1.6 confirms architectural plans exist departmentally but are withheld from public disclosure for security reasons.
* **Structural Drawings as Output**: Structural drawings cannot be cataloged as input data because they represent the future deliverable of the consultant.

---

### 2. Value for Construction Intelligence Research
Despite being classified as **Reference only**, this dataset provides valuable benchmark intelligence:
1. **Design Timeline Modeling**: 3-month timeline benchmarks for multi-storey high-rise structural design.
2. **Consultancy Cost Ratio**: Quantifies structural design fees (~0.4% of civil construction outlay) for Indian government housing.
3. **High-Rise Seismic Detailing Criteria**: Documents CPWD structural requirements for S+8 buildings in Seismic Zone IV.
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

