# Second Pilot Scope Lock: Faculty Housing Apartment Type 1B

**Project**: Development of Permanent Campus (Phase-I) for Nalanda University, at Rajgir, Bihar  
**Tender Package**: Package 1C (Construction and Development of Residential Buildings)  
**Selected Scope**: Faculty Housing Apartment Type 1B Block (G+2 Floors)  
**Target Repository**: `C:\Users\shahnawaz khan\OneDrive\Documents\DataRequirement\NIT-Nalanda`  
**Output Directory**: `10_Controlled_Transcription/second_pilot_phase_1_document_audit`  
**Stage Status**: `SECOND_PILOT_SCOPE_LOCKED_TYPE_1B`  
**Dataset Readiness**: `DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`  
*(The project is strictly NOT `READY_FOR_TAKEOFF`)*

---

## 1. Project Name
**Development of Permanent Campus (Phase-I) for Nalanda University, at Rajgir, Bihar**  
- **Owner / Client**: Nalanda University, Rajgir, District Nalanda, Bihar – 803116  
- **Architect & Master Planner**: Vastu Shilpa Consultants (Sangath, Ahmedabad – Dr. B.V. Doshi)  
- **Structural Consultant**: Vinod Shah Consulting Engineers Pvt. Ltd.  
- **Services Consultant**: DBHMS Services Consultants  

---

## 2. Package / Tender Identity
- **Tender Reference / NIT No.**: `NU/ENGG/54/2016-17/Tender: 01 dated 25th March 2017`  
- **Package Name**: `Package 1C — Tender for Construction and Development Works of Residential Buildings Parcel of Proposed Permanent Campus (Phase I) for Nalanda University, at Rajgir, Bihar`  
- **Overall Contract Duration**: 24 Calendar Months (as stipulated in Volume 1 NIT conditions)  
- **Tender Type**: Item-rate contract based on CPWD Specifications and Delhi Schedule of Rates (DSR 2014)  

---

## 3. Selected Building Scope
- **Specific Building Unit**: **Faculty Housing Apartment Type 1B Block**  
- **Storey Profile**: **G+2 Floors** (Ground Floor + First Floor + Second Floor)  
- **Built-Up Area (BUA)**: Ground Floor BUA including core is explicitly noted as **$264.67\text{ m}^2$** on Drawing `a.2.1-type-1b-ground-floor-plan.pdf`.  
- **Key Geometric Archetype**: Modular residential apartment block featuring Living, Dining, Master Bedroom, regular Bedrooms, Study, Kitchen, Utility Verandah, Toilets, and Servant Quarter.

---

## 4. Why This Scope Was Selected
1. **Direct Drawing Availability**: Unlike other residential types in the repository whose drawing subfolders currently contain only directory placeholders (`.gitkeep`), Type 1B has an authentic, high-resolution architectural floor plan and structural pile GA drawing.
2. **True Closed-Loop Project Matching**: Both available drawings explicitly cite Nalanda University, Package 1C, Vastu Shilpa Consultants, and the exact designation `Faculty Apartment Type 1B`.
3. **Controlled Geometric Complexity**: The G+2 footprint provides an excellent second-pilot validation testbed to prove that the evidence-control pipeline established on OIL/RITES transfers seamlessly to other institutional public works projects.
4. **Avoidance of Mixed-Project Repositories**: Selecting Type 1B avoids the severe project-level document mismatch identified in `SBI-DN-Nagar-Andheri-122-Flats` (where Pune drawings were filed under an Andheri tender folder).

---

## 5. Accepted AI Input Documents
The following 5 documents are formally accepted as predictive AI inputs:
1. `01_Tender_NIT_PreBid/02_NIT_Conditions/finalnit25-03-17.pdf` (240 pages): Contractual terms, tender scope, and site data.
2. `03_Technical_Specifications_Reports/Specifications/Part_I_Civil_Works/nalanda-residential-specifications-part-i-civil-works.pdf` (179 pages): Civil technical specifications, materials, concrete mixes, and IS 1200 measurement rules.
3. `03_Technical_Specifications_Reports/Specifications/Part_II_Services/nalanda-residential-specifications-part-ii-services.pdf` (280 pages): MEP technical specifications, sanitary fixture types, and electrical provisions.
4. `04_Architectural_Drawings/01_Faculty_Apartments/Type_1B/a.2.1-type-1b-ground-floor-plan.pdf` (1 page): Ground floor layout, door/window schedules, room dimensions, and gridlines X1-X17 / Y1-Y19.
5. `05_Structural_Drawings/01_Faculty_Housing_Apartments/Type_1B/1.1-pile-layout-and-details-for-faculty-housing-appt-type-1b-.pdf` (1 page): Bored cast-in-situ pile foundation layout and coordination details.

---

## 6. Accepted Ground-Truth Validation-Only Documents
The following 2 documents are accepted exclusively as **blind ground-truth validation targets**:
1. `02_Cost_BOQ_Makes/01_Estimated_Cost_ECPT/02.-ecpt.pdf` (1 page): Combined abstract estimated cost put to tender.
2. `02_Cost_BOQ_Makes/02_BOQ_Schedules/Combined_BOQ/05.-boq-schedule-b-combined.pdf` (33 pages): Itemized tender Schedule B.

> [!IMPORTANT]
> **Strict Firewall Principle**: BOQ and ECPT files are firewalled and strictly prohibited from entering AI prompt contexts during extraction. They serve exclusively as post-takeoff benchmark targets. Because the BOQ aggregates all Package 1C residential buildings without a single-block breakdown, direct single-building cost validation is currently impossible.

---

## 7. Documents Requiring Review
- **Combined Schedule B BOQ Allocation**: `05.-boq-schedule-b-combined.pdf` lumps quantities across 8 Faculty Bungalows, VC Bungalow, Type 1B, Type 2A, Type 2B, Staff Apartments, and Hostels. A formal building-wise BOQ allocation schedule is required before ground-truth validation can be conducted.
- **Tender Corrigenda & Addenda**: Review whether any pre-bid bulletins or addenda were issued affecting Package 1C between March 2017 and tender award.

---

## 8. Missing Evidence (Pre-Requisites for Full Takeoff)
The following essential drawings and schedules are currently **MISSING** from the repository for Type 1B:
1. **Upper Floor Plans**: 1st Floor and 2nd Floor architectural plans are missing.
2. **Elevations & Sections**: Architectural cross-sections and elevations defining floor-to-floor heights, beam soffits, and sill/lintel heights are missing.
3. **Superstructure Structural Drawings**: Column schedules, beam framing layouts, and slab reinforcement details are missing.
4. **Bar Bending Schedule (BBS)**: No rebar cutting or bending schedules exist for piles, caps, columns, beams, or slabs.
5. **Pile Depth & Soil Profile**: Pile termination depths below cut-off are not scheduled on Sheet 1.1; borehole logs for the Type 1B plot are missing.

---

## 9. What is Strictly NOT Allowed Yet
- **DO NOT calculate material quantities** (concrete, steel, masonry, plaster, paint, flooring).
- **DO NOT calculate costs or budgets**.
- **DO NOT perform BOQ validation** against Schedule B.
- **DO NOT perform labour or duration modelling**.
- **DO NOT create full takeoff files**.
- **DO NOT mark the project `READY_FOR_TAKEOFF`**.

---

## 10. Mandatory Governance Disclaimers

1. **This is a second-pilot controlled dataset audit, NOT a full quantity takeoff.**
2. **BOQ and ECPT documents are validation and benchmark targets, NOT AI inputs for generating quantities.**
3. **No quantities were calculated.**
4. **No costs were calculated.**
5. **No BOQ validation was performed.**
6. **The project strictly remains `DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION` and is NOT `READY_FOR_TAKEOFF`.**

---

## 11. Final Phase 1 Status

**`SECOND_PILOT_SCOPE_LOCKED_TYPE_1B`**

