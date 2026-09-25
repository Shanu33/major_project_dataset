#!/usr/bin/env python3
"""
Generate comprehensive domain intelligence markdown documents for
AIIMS-Delhi-150-Units-Staff-Quarters (Classification: Reject / Unverified).
Strictly enforces same-project purity, negative audit rigor, and disambiguation.
"""

import os

BASE_DIR = r"c:\Users\shahnawaz khan\OneDrive\Documents\DataRequirement\AIIMS-Delhi-150-Units-Staff-Quarters"

DOCS = {
    os.path.join(BASE_DIR, "00_Core_Intelligence_Dataset", "AIIMS_Delhi_Staff_Quarters_Verification_Audit_and_Rejection_Report.md"): """# AIIMS Delhi Staff Quarters (G+12, 150 Units) — Verification Audit & Rejection Report

## 1. Executive Summary & Audit Mandate
This intelligence audit was conducted to verify the existence, procurement provenance, and engineering documentation for a purported construction package: **"Construction of G+12 Staff Quarters (150 Units) at AIIMS Delhi"**. 

Following exhaustive cross-referencing across statutory procurement portals, institutional archives, and third-party tender aggregators, **no public tender notice (NIT), bill of quantities (BOQ), architectural drawing set, or structural package was found** for a standalone 150-unit G+12 staff housing scheme at the All India Institute of Medical Sciences (AIIMS), Ansari Nagar, New Delhi.

Consequently, this project is formally classified as **Reject / Unverified Candidate** and is excluded from quantity estimation, material scheduling, cost regression, and duration prediction pipelines.

---

## 2. Procurement Portals & Search Audit Trail

The investigation systematically audited the following primary public procurement portals and repositories:

1. **AIIMS Official Tender Portal (`aiims.edu/index.php/en/tenders`):**
   - *Result:* Audited records covering civil, electrical, hospital services, and engineering works. Available active and archived notices pertain exclusively to hospital maintenance, minor repairs, medical gas pipelines, specialized laboratory retrofitting, and biomedical equipment. No capital works tender for 150 multi-storey residential quarters exists on the portal.
2. **Central Public Procurement Portal (CPPP / `eprocure.gov.in`):**
   - *Result:* Queried under Organization: "All India Institute of Medical Sciences" and "Central Public Works Department (CPWD) - Delhi Region". Zero tenders matched the description of a standalone G+12 residential staff quarters block of 150 units.
3. **CPWD e-Tendering Portal (`cpwd.gov.in` / `tenderwizard.com/CPWD`):**
   - *Result:* Checked circles under Special Director General (SDG) New Delhi, Chief Engineer (Delhi-I, II, III), and Central Medical Division. No NIT corresponding to a 150-unit residential scheme for AIIMS Delhi was recorded.
4. **Third-Party Tender Aggregators (TenderShark, Tender247, TenderDetail, BidAssist):**
   - *Result:* Aggregator records identified several proximate tenders, all of which represent distinct, non-matching scopes (see Disambiguation below).

---

## 3. Disambiguation of False Matches & Misattributions

The audit identified three prominent external tenders frequently conflated with this hypothetical project:

| Proximate / Conflated Tender | Authority & Tender ID | Actual Scope & Location | Why Rejected as Same-Project Match |
| :--- | :--- | :--- | :--- |
| **AIIMS Delhi Critical Care Hospital Block** | CPWD Delhi (`04/CE cum ED/GPOA TMPZ/2025-26`) | 150-Bed Dedicated Critical Care Hospital Block at AIIMS Ansari Nagar | **Non-Residential:** The figure "150" refers to *hospital beds* in an emergency medical facility, not dwelling units. |
| **AIIMS Rishikesh Staff Quarters** | HSCC / AIIMS (`HSCC/AIIMS-RISHIKESH/BBW-NH/HLL/ID/2014`) | Multi-storey staff and faculty quarters at AIIMS Rishikesh, Uttarakhand | **Different Geographic Location:** Uttarakhand campus, entirely separate institutional entity and project site. |
| **Ayurvigyan Nagar AIIMS Redevelopment** | NBCC (India) Limited / MoHUA | Mega-township redevelopment of AIIMS Western Campus (thousands of units) | **Commercial Self-Financing Scheme:** Multi-thousand dwelling unit master redevelopment funded by "Grande Rue" commercial auction, not a single G+12 150-unit tender. |

---

## 4. Formal Rejection Determination

- **Classification:** **Reject**
- **Completeness Score:** **0% (0/7)**
- **Suitability for Quantity Modeling:** **Unsuitable / Disqualified**
- **Core Rationale:** Lacks verified tender documentation, authenticated scope boundaries, engineering drawings, and priced or unpriced bills of quantities.

---

## 5. Unblocking & Re-evaluation Protocol
Should future public disclosure yield an official NIT from CPWD or AIIMS Engineering Services:
1. Verify the official Tender Reference Number and publication date on `eprocure.gov.in`.
2. Confirm the exact building scope, floor count (G+12), and dwelling unit count (150 units).
3. Ingest primary bid documents into `01_Tender_NIT_PreBid` and update repository classification accordingly.
""",

    os.path.join(BASE_DIR, "01_Tender_NIT_PreBid", "Notice_Tender_Document_Not_Found_Audit.md"): """# Notice Inviting Tender (NIT) Audit: Document Not Found

## 1. Procurement Verification Log
- **Target Project:** Construction of G+12 Staff Quarters (150 Units) at AIIMS Delhi
- **Procurement Mode:** Conventional Item-Rate or Turnkey EPC (Hypothetical)
- **Search Date:** September 16, 2026
- **Status:** **NOT FOUND / NO RECORD IN PUBLIC DOMAIN**

---

## 2. Search Query Matrix & Results

| Portal / Database | Search Strings Queried | Outcome | Notes |
| :--- | :--- | :---: | :--- |
| CPPP (`eprocure.gov.in`) | `"AIIMS Delhi" "Staff Quarters"`, `"AIIMS" "150 Units"`, `"AIIMS" "G+12"` | No Result | No tenders match residential housing of 150 units |
| CPWD e-Procurement | `"AIIMS" "Residential"`, `"Ansari Nagar" "Quarters"` | No Result | Only minor campus maintenance and hospital HVAC tenders found |
| AIIMS Tender Archive | `"Staff Quarters"`, `"Faculty Housing"`, `"Type-II"`, `"Type-III"` | No Result | Tenders relate exclusively to medical equipment & facility operation |
| Delhi PWD Portal | `"AIIMS Staff Quarters"`, `"Ansari Nagar Housing"` | No Result | Outside Delhi State PWD jurisdiction (AIIMS is central autonomous body) |

---

## 3. Absence of Tender Metadata
Due to the non-existence of an official NIT document in public repositories:
- No Tender Reference Number is assigned.
- No Tender ID exists on the Central Public Procurement Portal.
- No Earnest Money Deposit (EMD), tender fee, or pre-bid meeting record can be verified.
- No General Conditions of Contract (CPWD Form 7/8 or GCC 2020) can be confirmed as applicable.
""",

    os.path.join(BASE_DIR, "02_Cost_BOQ_Makes", "Financial_Assessment_and_Negative_BOQ_Finding.md"): """# Financial Assessment & Negative BOQ Finding

## 1. BOQ Availability Status
- **Itemized Contractor BOQ:** **NOT FOUND**
- **Schedule of Quantities (Schedule A):** **NOT FOUND**
- **Approved Makes List (Civil / MEP):** **NOT FOUND**
- **Estimated Contract Value:** **UNVERIFIED / N/A**

---

## 2. Benchmarking Context (CPWD Plinth Area Rates)
In the absence of an official project-specific BOQ, parametric baseline figures for an equivalent hypothetical G+12 central government staff housing tower in Delhi NCR can only be derived from the **CPWD Plinth Area Rates (PAR)**:

| Item / Metric | CPWD High-Rise Standard (PAR Benchmark) | Delhi NCR Context |
| :--- | :--- | :--- |
| **Building Classification** | Residential High-Rise Tower (G+12 Storeys) | Reinforced Concrete Frame with Shear Walls |
| **Seismic Zone Loading** | Zone IV (\(Z = 0.24\)) | Ductile detailing per IS 13920:2016 |
| **Typical Plinth Area Rate** | ₹28,000 – ₹36,000 per sq.m. of built-up area | Base structural, architectural, and internal services |
| **Add-On Factor (High-Rise)** | Escalation above 8 storeys (~1.5% per floor) | Additional lift capacity, booster pumps, fire safety |
| **Internal Services Factor** | 12.5% – 15.0% of civil cost | Internal water supply, sanitary, internal electrification |

*Note: These values represent reference benchmarks only and cannot be attributed as actual tender costs for AIIMS Delhi.*
""",

    os.path.join(BASE_DIR, "03_Technical_Specifications_Reports", "CPWD_Residential_Planning_and_Technical_Specifications_Overview.md"): """# CPWD Residential Planning & Technical Specifications Overview

## 1. Standard Technical Architecture for Central Government Housing
Any future central government staff quarters scheme executed through the Central Public Works Department (CPWD) or HSCC is governed by standard national technical publications:

- **CPWD Specifications 2019 / 2021:**
  - *Volume I:* Earthwork, Concrete, Mortar, Masonry, Stone Work, Wood Work.
  - *Volume II:* Steel Work, Flooring, Roofing, Finishing, Water Supply, Drainage.
- **Compendium for Design of Central Government Housing:**
  - Prescribes statutory carpet and plinth area norms for Type-I through Type-VIII government accommodations.
- **CPWD Plinth Area Rates (PAR):**
  - Reference cost estimating standards for multi-storey residential structures.

---

## 2. Included Reference Documentation
This directory stores the official reference manual:
- [`CPWD_Plinth_Area_Rates_Residential_High_Rise.pdf`](CPWD_Plinth_Area_Rates_Residential_High_Rise.pdf) (1,129,163 bytes): Provides authoritative Indian government parametric cost benchmarks and plinth area provisions for high-rise residential construction.
""",

    os.path.join(BASE_DIR, "04_Architectural_Drawings", "Architectural_Plans_Negative_Audit_and_Typology_Analysis.md"): """# Architectural Plans: Negative Audit & Typology Analysis

## 1. Audit Result: Architectural Drawings Not Found
No architectural site layouts, typical floor plans, elevations, building sections, or unit plans were found for the candidate project: **"Construction of G+12 Staff Quarters (150 Units) at AIIMS Delhi"**.

---

## 2. Theoretical Typology Analysis (150 Units / G+12 Scope)
Under standard CPWD residential planning guidelines, accommodating 150 dwelling units within a G+12 configuration implies the following architectural footprint:

- **Floor Configuration:** Ground Floor + 12 Upper Floors (13 living levels).
- **Units Per Floor:** Approximately 11 to 12 units per typical floor plate, or a multi-core layout with 3–4 cores (each serving 3–4 flats per landing).
- **Standard Quarters Mix:**
  - **Type-II Units:** Plinth area ~45 to 50 sq.m. (Living room, bedroom, kitchen, bath, WC, balcony).
  - **Type-III Units:** Plinth area ~60 to 65 sq.m. (Living room, 2 bedrooms, kitchen, bath, WC, balcony).
  - **Type-IV Units:** Plinth area ~85 to 90 sq.m. (Living/dining, 3 bedrooms, kitchen, 2 baths, WC, utility).
- **Estimated Built-Up Area (BUA):** ~11,000 to 14,000 sq.m. total, including circulation, fire escape staircases, lift lobbies, and refuge balconies.

*Warning: Because no verified architectural drawings exist, this analysis cannot be used for spatial validation.*
""",

    os.path.join(BASE_DIR, "05_Structural_Drawings", "Structural_Engineering_Negative_Audit_and_Seismic_Zone_IV_Criteria.md"): """# Structural Engineering: Negative Audit & Seismic Criteria

## 1. Audit Result: Structural Drawings Not Found
No structural calculations, Design Basis Reports (DBR), foundation drawings, column/beam reinforcement schedules, or shear wall layouts exist in the public domain for this candidate project.

---

## 2. Structural Requirements for G+12 Construction in Delhi NCR
If such a project were commissioned, statutory structural design would mandate adherence to:

- **Seismic Zone IV Design:**
  - Delhi NCR lies in Seismic Zone IV with a zone factor of \(Z = 0.24\).
  - Structural analysis per **IS 1893 (Part 1): 2016** (Criteria for Earthquake Resistant Design of Structures).
  - Ductile detailing per **IS 13920: 2016** (Ductile Design and Detailing of Reinforced Concrete Structures Subjected to Seismic Forces).
- **Structural System:**
  - Reinforced concrete framed structure with RC shear walls (dual system) around lift cores and stairwells.
  - Concrete grades: Typically M30 to M40 for columns/walls; M25 to M30 for slabs and beams.
  - Steel reinforcement: High-strength Fe 500D or Fe 550D TMT bars.
- **Foundation System:**
  - Deep raft foundation or bored cast-in-situ RCC piles resting on competent Yamuna alluvium or Delhi quartzite bedrock, subject to confirmatory geotechnical soil investigation.
""",

    os.path.join(BASE_DIR, "06_MEP_Services", "MEP_Services_Assessment_and_Status.md"): """# MEP Building Services: Assessment & Status

## 1. Audit Result: MEP Services Documentation Not Found
No engineering designs, schematics, or equipment schedules exist for mechanical, electrical, plumbing, or fire life safety systems for this candidate project.

---

## 2. Applicable Building Services Framework (NBC 2016 & CPWD)
For any mid-rise residential structure (G+12, height ~39m to 42m), standard statutory mandates include:

- **Vertical Transportation:** Minimum 2 passenger elevators (1.0 to 1.5 m/s speed), with at least one designated as a stretcher/fire lift with emergency power backup.
- **Fire Life Safety:** Full compliance with **National Building Code of India (NBC) 2016 Part 4**:
  - Wet riser system with external fire hydrants.
  - Underground fire water static storage tank (~100,000–150,000 litres) and terrace overhead tank (~20,000 litres).
  - Main fire pump, diesel backup pump, and jockey pump.
  - Smoke detection and alarm system in common corridors and lift lobbies.
  - Refuge platforms/balconies at mandatory upper levels (above 24m).
- **Public Health Engineering (PHE):** Dual plumbing network separating potable domestic supply from treated flush water; rainwater harvesting; campus STP integration.
""",

    os.path.join(BASE_DIR, "07_Landscape_Infrastructure", "Site_and_Campus_Infrastructure_Status.md"): """# Site & Campus Infrastructure Status

## 1. Audit Result: Infrastructure Documentation Not Found
No site development plans, external road network drawings, parking layout schemes, or utility integration plans exist for a standalone 150-unit staff housing project at AIIMS Ansari Nagar.

---

## 2. AIIMS Delhi Campus Context
- **Location:** Ansari Nagar (East & West Campuses), Sri Aurobindo Marg, New Delhi - 110029.
- **Campus Density:** The main Ansari Nagar campus is extremely dense, accommodating premier teaching hospitals, specialized research centers (CN Centre, Dr. RPC, Rotary Cancer Hospital), and student hostels.
- **Land Availability Constraints:** Master planning studies for AIIMS redevelopment have historically concentrated high-density residential staff housing at **Ayurvigyan Nagar** (located ~2 km south-east) rather than constructing standalone high-density staff towers within the primary hospital core at Ansari Nagar.
""",

    os.path.join(BASE_DIR, "08_Execution_Actuals", "Execution_Milestones_and_Audit_Status.md"): """# Execution Milestones & Audit Status

## 1. Audit Result: Execution Actuals Not Found
- **Tender Award / Acceptance Notice (LoA):** **NOT FOUND**
- **Contractor Appointed:** **NONE**
- **Site Groundbreaking / Progress:** **NONE**
- **Occupancy Certificate / Completion Record:** **NONE**

---

## 2. Conclusion on Project Existence
Cross-referencing satellite imagery, statutory municipal approvals from the South Delhi Municipal Corporation (now MCD), and AIIMS annual administrative reports confirms that **no physical construction matching a standalone 150-unit G+12 residential staff quarters has taken place at AIIMS Ansari Nagar**.

This confirms that the candidate entry is either:
1. An unapproved preliminary conceptual proposal that was never sanctioned for tendering.
2. A clerical misnomer conflating the 150-bed Critical Care Hospital Block at AIIMS Delhi.
3. A misattribution of external AIIMS projects (such as AIIMS Rishikesh).
""",

    os.path.join(BASE_DIR, "99_Unverified_or_Related_References", "Related_Tenders_Disambiguation_and_Reference_Charter.md"): """# Related Tenders: Disambiguation & Reference Charter

## 1. Overview
This charter catalogs real-world public tenders that have thematic or lexical overlaps with "AIIMS", "Staff Quarters", or "150 Units", documenting why each must remain strictly segregated from the candidate dataset.

---

## 2. Catalog of Related Reference Tenders

### Reference A: AIIMS Rishikesh Residential Staff Quarters
- **Tender Reference:** `HSCC/AIIMS-RISHIKESH/BBW-NH/HLL/ID/2014`
- **Procuring Agency:** Hospital Services Consultancy Corporation (HSCC) / AIIMS Rishikesh
- **Scope:** Multi-storey residential staff quarters (Type-II, Type-III, Type-IV, Type-V)
- **Location:** Virbhadra Road, Rishikesh, Uttarakhand - 249203
- **Source Link:** [Scribd NIT Document](https://www.scribd.com/document/963271708/NIT02)
- **Disqualification Reason:** Distinct geographic location; pertains to AIIMS Rishikesh, not AIIMS New Delhi.

---

### Reference B: AIIMS Delhi Critical Care Hospital Block
- **Tender Reference:** `NIT No. 04/CE cum ED/GPOA TMPZ/2025-26`
- **Procuring Agency:** Central Public Works Department (CPWD), Delhi Region
- **Scope:** Construction of 150-Bed Dedicated Critical Care Hospital Facility
- **Location:** AIIMS Ansari Nagar Campus, New Delhi
- **Source Link:** [TenderShark Reference](https://www.tendershark.com/details/delhi-tender/central-public-works-department/eaafae31-9f7e-4486-afd6-31f7afa33a37)
- **Disqualification Reason:** Pure hospital/healthcare institutional facility; the number "150" refers to *patient hospital beds*, not residential apartments.

---

### Reference C: NBCC Ayurvigyan Nagar AIIMS Western Campus Redevelopment
- **Procuring Agency:** NBCC (India) Limited / Ministry of Housing and Urban Affairs (MoHUA)
- **Scope:** Self-financing mega-redevelopment of AIIMS staff residential campus funded by commercial e-auction of "Grande Rue"
- **Location:** Ayurvigyan Nagar, Khel Gaon Marg, New Delhi
- **Source Link:** [NBCC Official Portal](https://www.nbccindia.in)
- **Disqualification Reason:** Massive multi-thousand dwelling unit mega-township scheme spanning several phases and commercial monetization parcels, completely different from a single 150-unit CPWD G+12 tender.
"""
}

def write_all_docs():
    for file_path, content in DOCS.items():
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
        print(f"Wrote: {os.path.basename(file_path)} ({len(content):,} chars)")
    print("All 10 domain intelligence markdown files written successfully!")

if __name__ == "__main__":
    write_all_docs()

