import os

target_dir = r"c:\Users\shahnawaz khan\OneDrive\Documents\DataRequirement\UP-RERA-Residential-Towers-Floor-Plans"

files = {}

# 00_Core_Intelligence_Dataset
files['00_Core_Intelligence_Dataset/UP_RERA_Multi_Tower_Cross_Project_Compendium.md'] = """# UP RERA Multi-Tower Residential Projects - Cross-Project Compendium & Floor Plan Intelligence

## 1. Executive Summary & Regulatory Authority

The **Uttar Pradesh Real Estate Regulatory Authority (UP RERA)** was established under the **Real Estate (Regulation and Development) Act, 2016** and the **Uttar Pradesh Real Estate (Regulation and Development) Rules, 2016**. UP RERA oversees one of the largest and most dense residential construction markets in India, spanning:
1. **NCR Western Uttar Pradesh:** Gautam Buddha Nagar (NOIDA, Greater Noida, Yamuna Expressway), Ghaziabad, and Meerut.
2. **Central & Eastern Uttar Pradesh:** Lucknow, Kanpur, Agra, Prayagraj, and Varanasi.

### Distinctive Strengths of UP RERA Public Portal
While each state regulatory authority has unique disclosure formats, **UP RERA** is uniquely rich in:
- **Floor Plans of All Types (Sanctioned Architectural PDFs):** High-resolution floor plans for every unit type (2BHK, 3BHK, 4BHK, Penthouses, Shops, and Villas) and typical multi-floor sequences (Floors 1-8, 1-17, 5-20, 1-27).
- **Project Specifications on Promoter Letterhead:** Comprehensive civil, joinery, electrical, sanitary, and structural material specifications officially certified and uploaded by the promoter.
- **Sanctioned Master Layout Plans & Local Authority Approvals:** Formal maps approved by NOIDA, GNIDA, YEIDA, and LDA.
- **Standardized Legal Formats:** Proforma Application Forms, Allotment Letters, and Builder Buyer Agreements (BBA).

---

## 2. Empirical UP RERA Project Cross-Section

The dataset synthesizes verified disclosures across multi-tower high-rise and mid-rise residential developments:

| Project Name | Promoter Entity | Location / Authority | UP RERA Reg. No. / ID | Building Typology & Scope | Key Downloaded Assets |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Himalaya Pride (Phase 3: Tower D)** | Himalaya Realestate Pvt. Ltd. | Tech Zone-IV, Greater Noida West (GNIDA) | `UPRERAPRJ8898` (ID: 8898) | High-Rise Residential Tower D, Plot 2,665 m2, Central Park 9,983.98 m2 | Sanctioned Layout Plan, Floor Plans of All Types (Tower C/D), Proforma Application & Allotment Letters, Registry |
| **Himalaya Pride (Phase 2: Tower C)** | Himalaya Realestate Pvt. Ltd. | Tech Zone-IV, Greater Noida West (GNIDA) | `UPRERAPRJ8888` (ID: 8888) | High-Rise Residential Tower C (G+20+), 2BHK/3BHK Clusters | Sanctioned Floor Plans, Unit Schedules, Technical Specifications |
| **M3M The Cullinan** | Lavish Buildmart Pvt. Ltd. / M3M India | Sector 94, Noida Expressway (NOIDA) | `UPRERAPRJ442214` (Ref: `PRJ9315`) | Ultra-Luxury Multi-Tower High-Rise Complex (G+30+ Floors) | Builder Buyer Agreement (BBA), High-Rise Typical Floor Plans (1-27 Floors), Master Layout Plan |
| **Omaxe Full Moon (Group Housing-1)** | Omaxe Limited | Mathura, Uttar Pradesh | `UPRERAPRJ2218` (ID: 2218) | Integrated Group Housing Scheme | Approved Layout Map, Unit Floor Plans, Civil Specifications |
| **Raj Residency** | Shreeraj Infrahousing Pvt. Ltd. | Barabanki / Lucknow Periphery | `UPRERAPRJ17537` (ID: 17537) | Mid-Rise Residential Enclave | Sanctioned Floor Plans, Project Specifications, Promoter Audited Filings |

---

## 3. Floor Plan Typologies & Spatial Parameters

Analysis of sanctioned "Floor Plans of All Types" reveals standard spatial planning across UP NCR:

1. **2BHK Residential Units:**
   - Carpet Area: **55.0 m2 to 68.0 m2** (592 to 732 sq.ft.).
   - Super Built-Up Area: **850 to 1,100 sq.ft.** (Efficiency ~66% - 70%).
   - Configuration: Living/dining, 2 bedrooms, 2 toilets, kitchen, utility balcony, 2-3 view balconies.
2. **3BHK Residential Units:**
   - Carpet Area: **75.0 m2 to 105.0 m2** (807 to 1,130 sq.ft.).
   - Super Built-Up Area: **1,200 to 1,650 sq.ft.** (Efficiency ~68% - 72%).
   - Configuration: Living/dining, 3 bedrooms, 2-3 toilets, kitchen, utility balcony, extended continuous running balconies.
3. **4BHK & Luxury Units:**
   - Carpet Area: **135.0 m2 to 210.0 m2** (1,453 to 2,260 sq.ft.).
   - Super Built-Up Area: **2,000 to 3,400 sq.ft.** (Efficiency ~70% - 74%).
   - Configuration: Double-height living, 4 bedrooms, 4-5 toilets, powder room, servant quarter with attached toilet.
4. **Typical Floor Plate Sequences:**
   - Low-Rise to Mid-Rise (1-8 Floor Typical Plans)
   - Standard High-Rise (1-17 Floor & 5-20 Floor Typical Plans)
   - Ultra High-Rise Towers (1-27 Floor Typical Plans)
"""

# 01_Tender_NIT_PreBid
files['01_Tender_NIT_PreBid/UPRERA_Statutory_Framework_and_Authority_Approvals.md'] = """# UP RERA Statutory Framework, Municipal Sanctions & Legal Formats

## 1. Statutory Registration Mandate

Governed by Central Act 16 of 2016 and the **Uttar Pradesh Real Estate (Regulation and Development) Rules, 2016**:
- Mandatory registration for projects with land area > 500 m2 or units > 8.
- **Form REG-1 / Project Registration Application:** Disclosure of promoter credentials, encumbrance certificate, sanctioned plans, layout plans, and proforma sales documents.
- **Section 4(2)(l)(D) Escrow Account (70% Rule):** Dedicated project bank account in a scheduled bank where 70% of collections must be deposited for land and construction expenditure.
- **Withdrawal Protocols:** Certified quarterly by Project Architect, Project Structural Engineer, and Chartered Accountant in Practice (Form REG-3).

---

## 2. Industrial & Urban Development Authorities in Uttar Pradesh

Unlike states governed primarily by Municipal Corporations, Western UP high-rise corridors are governed by specialized statutory Industrial Development Authorities:
1. **NOIDA (New Okhla Industrial Development Authority):** Regulating Sectors 1 to 168 under the UP Industrial Area Development Act, 1976.
2. **GNIDA (Greater Noida Industrial Development Authority):** Governing planned industrial, residential, and institutional sectors in Greater Noida and Tech Zones in Greater Noida West.
3. **YEIDA (Yamuna Expressway Industrial Development Authority):** Governing the Jewar International Airport investment corridor.
4. **LDA (Lucknow Development Authority) & GDA (Ghaziabad Development Authority):** Administering urban planning under the UP Urban Planning and Development Act, 1973.

---

## 3. Standardized Legal & Allotment Documentation

UP RERA has pioneered standardized legal instruments uploaded directly by developers:
- **Proforma Application Form:** Standardized buyer application containing registration details, payment schedules, and statutory disclosures.
- **Proforma Allotment Letter:** Issued upon booking, detailing carpet area, common areas, and payment milestones.
- **Builder Buyer Agreement (BBA):** Comprehensive agreement defining carpet area per RERA, defect liability period (5 years under Section 14(3)), handover timelines, and interest rates for delay.
"""

# 02_Cost_BOQ_Makes
files['02_Cost_BOQ_Makes/CA_Certified_Project_Costs_and_Macro_Takeoff_Matrix.md'] = """# CA Certified Project Costs, Form REG-3 & Macro Takeoff Matrix

## 1. Project Cost Structure (Form REG-3 Disclosures)

Under UP RERA rules, promoters must submit certified project cost estimates from a Chartered Accountant (Form REG-3):

| Cost Head | Proportion of Total Outlay | Empirical Range (Noida / Gr. Noida) | Empirical Range (Tier-2 UP) |
| :--- | :---: | :---: | :---: |
| **Land Acquisition & Lease Premium** | 25% - 45% | Rs 50 Cr - Rs 300+ Cr | Rs 10 Cr - Rs 40 Cr |
| **Direct Tower Construction Cost** | 35% - 55% | Rs 80 Cr - Rs 450+ Cr | Rs 20 Cr - Rs 90 Cr |
| **Internal Site Infrastructure (IDW)** | 5% - 10% | Rs 10 Cr - Rs 40 Cr | Rs 3 Cr - Rs 12 Cr |
| **Authority Dues (Lease Rent, EDC, IDC)** | 10% - 20% | Rs 20 Cr - Rs 100 Cr | Rs 5 Cr - Rs 20 Cr |
| **Finance, Marketing & Administration** | 5% - 10% | Rs 15 Cr - Rs 60 Cr | Rs 3 Cr - Rs 15 Cr |

---

## 2. Construction Cost Benchmarks in Uttar Pradesh

| Location / Corridor | Building Typology | Storeys | Cost / Sq.Ft. BUA | Cost / Sq.Ft. Carpet |
| :--- | :--- | :--- | :--- | :--- |
| **Noida Expressway (Sec 94, 128, 150)** | Ultra-Luxury (RCC Shear Wall / Mivan) | G+25 to G+35 | Rs 3,800 - Rs 5,500 | Rs 5,500 - Rs 8,000 |
| **Greater Noida West (Noida Extension)** | High-Rise Residential (Tower D type) | G+18 to G+24 | Rs 2,400 - Rs 3,200 | Rs 3,500 - Rs 4,600 |
| **Ghaziabad (Raj Nagar Ext. / Indirapuram)**| Mid-to-High Rise Residential | G+14 to G+20 | Rs 2,200 - Rs 2,900 | Rs 3,200 - Rs 4,200 |
| **Lucknow (Gomti Nagar Ext. / Shaheed Path)**| High-Rise Group Housing | G+14 to G+22 | Rs 2,100 - Rs 2,800 | Rs 3,000 - Rs 4,000 |
| **Tier-2/3 UP (Mathura, Barabanki, Agra)** | Mid-Rise Enclaves | G+4 to G+10 | Rs 1,600 - Rs 2,200 | Rs 2,300 - Rs 3,200 |

---

## 3. Takeoff Utility of UP RERA Floor Plans

Because UP RERA hosts **high-resolution Sanctioned Floor Plans of All Types**, quantity surveyors can perform direct geometric takeoffs:
- **Slab Area (m2):** Direct planimeter measurement of floor plate boundaries.
- **Wall Surface Area (m2):** Measured from interior partition schedules and door/window opening schedules.
- **Flooring & Skirting Quantities (m2 / m):** Room-by-room area extraction from unit floor plans.
"""

# 03_Technical_Specifications_Reports
files['03_Technical_Specifications_Reports/Promoter_Technical_Specifications_Architecture.md'] = """# Promoter Technical Specifications Architecture (UP RERA Filings)

## 1. Structure & Superstructure

- **Structural Framing:** Earthquake-resistant RCC framed structure conforming to **IS 1893:2016 (Seismic Zone IV)** for Noida, Greater Noida, and Ghaziabad; and **Seismic Zone III** for Lucknow and Central UP.
- **Concrete & Reinforcement:** High-performance concrete mix (M25/M30/M35) with Fe-500D / Fe-550D TMT reinforcement bars (Tata Tiscon, SAIL, Jindal Panther).
- **External & Internal Walls:** Autoclaved Aerated Concrete (AAC) blocks (density 600 kg/m3) or high-grade fly ash bricks set in polymer-modified adhesive mortar.

---

## 2. Flooring & Surface Finishes

- **Drawing / Dining / Living Room:** Premium vitrified tiles (800 x 800 mm or 1200 x 600 mm) with matching skirting.
- **Master Bedroom:** Laminated wooden flooring (AC4 grade) or wooden-finish glazed vitrified tiles.
- **Other Bedrooms:** Vitrified tiles (600 x 600 mm).
- **Balconies:** Anti-skid ceramic/terracotta tiles with weather-resistant exterior paint on ceiling soffits.
- **Lift Lobbies & Corridors:** Selected granite or imported marble combination on lift facia; anti-skid vitrified tiles on corridors.
- **Staircases:** Granite or polished Kota stone treads and risers with MS railings.

---

## 3. Kitchen & Bathroom Architecture

- **Kitchen Working Counter:** Polished black granite counter slab with stainless steel single/double bowl sink (Nirali/Franke); ceramic tile dado up to 2.0 ft height above working platform; provision for RO water purifier and exhaust/chimney.
- **Toilets & Bathrooms:** Anti-skid ceramic floor tiles; designer digital ceramic wall tiles up to false ceiling height (7.0 ft); premium wall-hung EWC with concealed dual-flush cistern; single lever CP brass diverters and fixtures (Jaquar, Kohler, Grohe).

---

## 4. Doors, Windows & Electrical Services

- **Main Door:** 8.0 ft high polished hardwood door frame with veneered designer flush shutter, multi-point mortise lock, and brass fittings.
- **Internal Doors:** Hardwood / maranti frame with painted skin-moulded flush shutters.
- **External Windows & Glazing:** Powder-coated / anodized aluminum or UPVC sliding/casement window sections with 5 mm toughened float glass.
- **Electrical Distribution:** Concealed flame-retardant low smoke (FRLS) copper wiring in PVC conduits (Finolex, Havells, Polycab); modular switches (Legrand, Schneider); 100% DG power backup with dual electric meters.
"""

# 04_Architectural_Drawings
files['04_Architectural_Drawings/Floor_Plans_of_All_Types_and_Sanctioned_Layout_Catalog.md'] = """# Floor Plans of All Types & Sanctioned Layout Catalog (UP RERA Assets)

## 1. The 'Floor Plans of All Types' Mandate

Under UP RERA registration guidelines, promoters are legally required to upload **'Floor Plans of All Types'**, creating a comprehensive catalog of architectural assets:

```text
UP RERA Architectural Asset Hierarchy:
├── 01_Approved_Layout_Plan/           -> Master layout showing towers, setbacks, roads, gates & central green
├── 02_Unit_Floor_Plans_All_Types/     -> Unit-level floor plans:
│   ├── 2BHK_Floor_Plans/              -> Unit layouts (Carpet: 55-68 m2)
│   ├── 3BHK_Floor_Plans/              -> Unit layouts (Carpet: 75-105 m2)
│   ├── 4BHK_Penthouse_Plans/          -> Unit layouts (Carpet: 135-210 m2)
│   └── Commercial_Retail_Plans/       -> Ground-level retail shops and kiosks
├── 03_Typical_Floor_Plans_By_Storey/  -> Tower cluster floor plates:
│   ├── Typical_Floor_Plan_1_to_8/     -> Low-to-mid rise cluster layout
│   ├── Typical_Floor_Plan_1_to_17/    -> Standard high-rise floor plate
│   ├── Typical_Floor_Plan_5_to_20/    -> High-rise upper residential floors
│   └── Typical_Floor_Plan_1_to_27/    -> Ultra high-rise floor plates
└── 04_Block_Wise_Floor_Plans/         -> Block 5 & 5A, Tower C, Tower D cluster sheets
```

---

## 2. Case Benchmark: Himalaya Pride (Plot GH-10B, Tech Zone-IV)

- **Total Plot Area:** 2,665 m2 (Tower D phase) within a composite multi-phase group housing enclave.
- **Central Green Park:** **9,983.98 m2** central landscaped park area ensuring extensive light, ventilation, and green open space.
- **Tower Configuration:** High-Rise Tower D (G+20+ storeys) with dual fire escape staircases, high-speed passenger lifts, and stretcher-capacity emergency lifts.
- **Floor Plan Suite:** `PRJ88988... Tower C - Floor Plans.pdf` and Tower D floor sheets displaying multi-unit clusters with central elevator lobbies and pressurized fire escape stairs.

---

## 3. Case Benchmark: M3M The Cullinan (Sector 94, Noida)

- **Scale:** Ultra-luxury mixed-use development with high-rise residential towers rising up to G+30+ floors.
- **Floor Plate Features:** Expansive floor plans (1-27 Typical Floors) featuring private elevator foyers, panoramic glass curtain walls, wrap-around running balconies, and VRV/VRF air conditioning layouts.
"""

# 05_Structural_Drawings
files['05_Structural_Drawings/Seismic_Zone_IV_Structural_Paradigms_UP_NCR.md'] = """# Seismic Zone IV Structural Paradigms & Foundation Engineering in UP NCR

## 1. Seismic Zone IV Classification (Western UP Corridors)

Noida, Greater Noida, and Ghaziabad are situated in **Seismic Zone IV** (High Damage Risk Zone):
- **Seismic Zone Factor (Z):** 0.24 (IS 1893:2016 Part 1).
- **Importance Factor (I):** 1.20 for high-occupancy residential group housing towers.
- **Response Reduction Factor (R):** 5.0 for ductile shear wall and special RC moment-resisting frame (SMRF) systems.
- **Basic Wind Speed (Vb):** 47 m/s (169.2 km/h) per IS 875 Part 3.

---

## 2. Structural Superstructure Architecture

- **Shear Wall Monolithic Construction:** Most modern high-rise towers (G+18 to G+30) in Noida and Greater Noida utilize monolithic aluminum formwork (Mivan) casting shear walls and slabs simultaneously, providing superior lateral stiffness and earthquake resistance.
- **Core Wall Systems:** Elevator and staircase shafts function as central cantilever shear cores resisting up to 75% - 85% of total seismic base shear.
- **Ductile Detailing:** High-yield deformed Fe-500D/550D rebar detailed strictly per **IS 13920:2016** with 135-degree seismic hooks and close-spaced stirrup confinement.

---

## 3. Geotechnical & Foundation Engineering (Yamuna-Hindon Floodplain)

- **Subsurface Conditions:** Deep alluvial silt and fine-to-medium sand deposits typical of the Yamuna and Hindon river floodplains.
- **Foundation Types:**
  - Solid RC Raft Foundations (depth 1.8 m to 2.5 m) on ground-improved strata for towers up to G+15.
  - Piled-Raft Foundations with bored cast-in-situ concrete piles (diameter 600 mm to 900 mm, length 20 m to 30 m) for high-rise towers (G+20 to G+30).
"""

# 06_MEP_Services
files['06_MEP_Services/High_Rise_MEP_and_Fire_Safety_Standards_UP.md'] = """# High-Rise MEP Services & Fire Safety Standards (NBC 2016 Part 4 & UP Fire Services)

## 1. Fire Life Safety Systems in High-Rise Residential Towers

Governed by the **National Building Code of India (NBC 2016 Part 4)** and **Uttar Pradesh Fire Services**:
1. **Fire Refuge Floors:**
   - Dedicated fire refuge floors or cantilever refuge balconies mandatory every 7 floors above 24 m height (typically at 8th, 15th, and 22nd floor levels).
2. **Pressurization & Escape Routes:**
   - Dual fire escape staircases with 2-hour fire-rated doors.
   - Mechanical pressurization fans maintaining 25-50 Pa positive pressure in stairwells and lift lobbies to prevent toxic smoke infiltration.
3. **Suppression Systems:**
   - Automatic wet sprinklers across all apartments, common lobbies, and multi-level basements.
   - Wet risers (150 mm dia) with twin landing hydrants and 30 m hose reel drums on every floor.
   - Dedicated fire water storage: 200,000 to 300,000 liters in underground reservoir (UGR) + 25,000 to 50,000 liters in overhead tank (OHT).

---

## 2. Plumbing & Dual Water Supply Networks

- **Water Demand:** 135 LPCD designed per NBC 2016.
- **Dual Pipe Reticulation:**
  - Potable Domestic Supply: Treated municipal water from authority bulk main.
  - Flushing Supply: Recycled water from on-site Sewage Treatment Plant (STP) using MBBR/SBR technology with tertiary filtration.
- **Rainwater Harvesting:** Recharge pits with desilting chambers strategically placed across site per CGWA and UP Ground Water Department norms.

---

## 3. Power Distribution & Emergency Backup

- **Grid Feed:** 33 kV or 11 kV dedicated feeder from UPPCL / NPCL (Noida Power Company Limited).
- **Substation:** Step-down dry-type transformers (11 kV / 433 V) with vacuum circuit breakers (VCB).
- **Backup Generation:** 100% automated Diesel Generator (DG) backup with Auto Mains Failure (AMF) synchronizing panels meeting CPCB-IV emission standards.
"""

# 07_Landscape_Infrastructure
files['07_Landscape_Infrastructure/Master_Layout_Zoning_and_Open_Space_Norms.md'] = """# Master Layout Zoning, Open Space & Infrastructure Norms (NOIDA / GNIDA Regulations)

## 1. Planning Regulations & Ground Coverage

Under NOIDA and Greater Noida Industrial Development Authority Group Housing Building Regulations:
- **Maximum Ground Coverage:** Restricted to **30% to 35%** of gross plot area, ensuring **65% to 70% open green space**.
- **Floor Area Ratio (FAR):** Base FAR **2.75 to 3.50**, purchasable FAR up to **4.00+** along major expressway transit corridors.
- **Peripheral Setbacks:** Minimum 15 m to 24 m front setbacks; minimum 12 m peripheral clear motorable road for emergency fire appliance movement.

---

## 2. Central Green Park & Podium Amenities

- **Mandatory Central Park:** Group housing schemes must provide large centralized green open spaces (e.g., **9,983.98 m2 central park** in Himalaya Pride).
- **Vehicular Segregation:** Non-vehicular podium decks featuring landscaped lawns, jogging tracks, children's play zones, and water features, while vehicular traffic is diverted directly to basement ramps.
- **Parking Norms:** 1.5 to 2.0 Equivalent Car Spaces (ECS) per residential unit provided across 2-3 levels of underground basements.
"""

# 08_Execution_Actuals
files['08_Execution_Actuals/Project_Status_Monitoring_and_QPR_Protocols.md'] = """# UP RERA Project Lifecycle Tracking, QPR Submissions & OC Protocols

## 1. Statutory Monitoring Workflow

Under Section 11(1)(b) of Central RERA and UP RERA Rules:
1. **Quarterly Progress Reports (QPR):** Promoters must upload quarterly updates detailing percentage completion of tower foundations, superstructure slabs, internal finishing, and external services.
2. **Tri-Partite Professional Certification:**
   - **Architect Certificate:** Percentage physical progress of each tower.
   - **Structural Engineer Certificate:** Structural stability and code compliance.
   - **Chartered Accountant Certificate (Form REG-3):** Audit of 70% Escrow Account withdrawals against actual construction costs incurred.

---

## 2. Occupancy Certificate (OC) & Handover Process

1. **Joint Authority Inspection:** Physical site inspection conducted by Planning, Fire, Health, and Engineering departments of NOIDA / GNIDA / LDA.
2. **Statutory NOC Clearances:** Final Fire Safety NOC, Lift Safety Certificate from Electrical Inspector, Environmental Clearance compliance, and Municipal Water/Sewer connection certificate.
3. **Grant of Occupancy Certificate (OC):** Formal authority clearance enabling execution of sub-lease / conveyance deeds and physical key handover to allottees.
"""

# 99_Unverified_or_Related_References
files['99_Unverified_or_Related_References/RERA_Disclosures_National_Synergy_Note.md'] = """# National RERA Benchmark Triad: Haryana, West Bengal & Uttar Pradesh

## 1. The Tri-State Private Residential Benchmark Matrix

In building an AI-ready construction intelligence repository, private residential projects across Haryana, West Bengal, and Uttar Pradesh form a complete and mutually reinforcing dataset:

| Dimension / Capability | Haryana RERA (HARERA) | West Bengal RERA (WBRERA) | Uttar Pradesh RERA (UP RERA) | Tri-State Synthesis |
| :--- | :--- | :--- | :--- | :--- |
| **Financial Calibration** | 5 Stars: **Form A-H Tables:** Line-item Land, Apt Construction, Infra, EDC/IDC. | 3 Stars: **Audited BS:** Declared total project outlays. | 4 Stars: **Form REG-3:** CA certified project costs. | **HARERA & UP RERA** calibrate macro construction costs per m2. |
| **Floor Plan Assets** | 2 Stars: Marketing brochures only. | 4 Stars: Sanctioned Typical & Refuge Plans. | 5 Stars: **Floor Plans of All Types:** 2BHK, 3BHK, 4BHK, typical 1-8, 1-17, 1-27 floors. | **UP RERA** provides the most exhaustive unit & floor plate catalog. |
| **Technical Specifications** | 3 Stars: Declared in Form A-H. | 3 Stars: Structural specs in select filings. | 5 Stars: **Certified Letterhead Specs:** Civil, joinery, sanitary, electrical, structural. | **UP RERA** provides promoter-certified material specifications. |
| **Structural Drawings** | 1 Star: Not publicly accessible. | 4 Stars: **TKD Series:** Pile, column, beam-slab framing. | 2 Stars: Layout plans only. | **WBRERA** provides structural engineering sheets. |

---

## 2. Final Dataset Classification: **Reference only (Borderline SILVER)**

- **Classification:** **Reference only**
- **Borderline SILVER Justification:** Private residential developments do not offer public competitive tender BOQs. However, **UP RERA's comprehensive repository of sanctioned Floor Plans of All Types, typical multi-floor sequences (1-8, 1-17, 5-20, 1-27), sanctioned master layout maps, and certified technical specifications** provides direct geometric and material inputs for architectural quantity takeoffs.
"""

for rel_path, content in files.items():
    full_path = os.path.join(target_dir, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print(f'Generated: {rel_path}')

print('All UP RERA intelligence files successfully created.')

