# Phase 1 Document Audit & Scope Lock Log: Nalanda Second Pilot

**Project**: Development of Permanent Campus (Phase-I) for Nalanda University, at Rajgir, Bihar  
**Tender Reference**: Package 1C (Residential Buildings Parcel, NIT No: `NU/ENGG/54/2016-17/Tender: 01 dated 25th March 2017`)  
**Selected Pilot Scope**: Faculty Housing Apartment Type 1B Block (G+2 Floors)  
**Location on Disk**: `C:\Users\shahnawaz khan\OneDrive\Documents\DataRequirement\NIT-Nalanda`  
**Output Directory**: `10_Controlled_Transcription/second_pilot_phase_1_document_audit`  
**Current Stage Status**: `SECOND_PILOT_PHASE_1_DOCUMENT_AUDIT_COMPLETE_SCOPE_LOCKED`  
**Overall Dataset Readiness**: `DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`  
*(Project strictly remains NOT `READY_FOR_TAKEOFF`)*

---

## 1. Task Scope & Objectives

Following the successful completion of the first controlled pilot (`OIL-RITES-Duliajan-BQ-Housing`, Priorities A through I-B), this task initiates the replication of the evidence-controlled pipeline on a **second authentic public works project**: **NIT-Nalanda**.

The objective of Phase 1 is strictly limited to:
1. Auditing the project repository to verify that all cataloged files belong to the same project and residential tender package.
2. Establishing the ontological boundary between predictive AI inputs and firewalled ground-truth validation documents.
3. Locking one manageable, verified building unit (`Faculty Housing Apartment Type 1B`).
4. Compiling an exhaustive register of missing drawings and schedules before any transcription or takeoff begins.

---

## 2. Source Files Reviewed

The repository was systematically audited across 7 distinct primary PDF documents:
1. `01_Tender_NIT_PreBid/02_NIT_Conditions/finalnit25-03-17.pdf` (240 pages)
2. `02_Cost_BOQ_Makes/01_Estimated_Cost_ECPT/02.-ecpt.pdf` (1 page)
3. `02_Cost_BOQ_Makes/02_BOQ_Schedules/Combined_BOQ/05.-boq-schedule-b-combined.pdf` (33 pages)
4. `03_Technical_Specifications_Reports/Specifications/Part_I_Civil_Works/nalanda-residential-specifications-part-i-civil-works.pdf` (179 pages)
5. `03_Technical_Specifications_Reports/Specifications/Part_II_Services/nalanda-residential-specifications-part-ii-services.pdf` (280 pages)
6. `04_Architectural_Drawings/01_Faculty_Apartments/Type_1B/a.2.1-type-1b-ground-floor-plan.pdf` (1 page)
7. `05_Structural_Drawings/01_Faculty_Housing_Apartments/Type_1B/1.1-pile-layout-and-details-for-faculty-housing-appt-type-1b-.pdf` (1 page)

---

## 3. Same-Project Matching Conclusion

**Verdict: 100% SAME-PROJECT PACKAGE MATCH CONFIRMED.**
- **Project Identity**: All 7 audited documents uniformly identify *Nalanda University, Rajgir, Bihar*, governed by tender Package 1C (`NU/ENGG/54/2016-17/Tender: 01 dated 25th March 2017`).
- **Architectural & Engineering Integrity**: The drawings and specifications share the exact same professional team: *Vastu Shilpa Consultants (Architects, Ahmedabad)*, *Vinod Shah Consulting Engineers (Structural)*, and *DBHMS (Services)*.
- **Scope Discipline**: Unlike `SBI-DN-Nagar-Andheri-122-Flats` (which was flagged and disqualified due to Hinjewadi, Pune drawings contaminating an Andheri tender folder), all files in `NIT-Nalanda` belong strictly to the Nalanda University permanent campus development.

---

## 4. Selected Building Scope Lock

- **Selected Target Unit**: **Faculty Housing Apartment Type 1B Block**
- **Storey Profile**: G+2 Floors (Ground Floor + 2 Upper Floors)
- **Built-Up Area**: Ground Floor BUA is explicitly dimensioned as **$264.67\text{ m}^2$** on Drawing `a.2.1-type-1b-ground-floor-plan.pdf`.
- **Status**: **`SECOND_PILOT_SCOPE_LOCKED_TYPE_1B`**

---

## 5. Accepted AI Input Documents (5 Documents)

These files are approved as predictive inputs to understand project geometry, materials, and contract terms:
1. `finalnit25-03-17.pdf`: Contractual and site terms.
2. `nalanda-residential-specifications-part-i-civil-works.pdf`: Civil technical specifications and IS 1200 measurement rules.
3. `nalanda-residential-specifications-part-ii-services.pdf`: Building services specifications.
4. `a.2.1-type-1b-ground-floor-plan.pdf`: Ground floor room layouts and door/window schedules for Type 1B.
5. `1.1-pile-layout-and-details-for-faculty-housing-appt-type-1b-.pdf`: Bored pile foundation arrangement for Type 1B.

---

## 6. Ground-Truth Validation-Only Documents (Firewalled)

These files are strictly firewalled and barred from AI prompts:
1. `02.-ecpt.pdf` (1 page): Combined abstract estimated cost put to tender.
2. `05.-boq-schedule-b-combined.pdf` (33 pages): Combined itemized Schedule B BOQ.

> [!CAUTION]
> Feeding Schedule B into extraction prompts constitutes prompt poisoning and circular reasoning. The BOQ will serve strictly as a blind post-takeoff benchmark after independent formula evaluation.

---

## 7. Rejected or Review-Required Documents

- **Combined BOQ Allocation (`05.-boq-schedule-b-combined.pdf`)**: **REVIEW REQUIRED**. The BOQ aggregates quantities across the entire residential campus (8 Faculty Bungalows, VC Bungalow, Type 1B, Type 2A, Type 2B, Staff Apartments, Hostels). It cannot be used to validate single-building Type 1B takeoff without an official building-by-building allocation schedule.
- **Unverified Repository Folders**: Folders for Hostels, Type 2A, and Married Students currently contain only empty `.gitkeep` directory structures. They are excluded from the current scope.

---

## 8. Critical Missing Evidence (15 Registered Items)

As documented in `missing_evidence_register.csv`, the repository currently lacks:
1. 1st and 2nd Floor architectural plans for Type 1B.
2. Architectural elevations (Front, Rear, Sides).
3. Architectural sections (A-A, B-B, C-C, D-D) defining vertical storey heights.
4. Superstructure structural drawings (columns, framing beams, slabs).
5. Bar Bending Schedules (BBS) for all structural trades.
6. Pile termination depth schedule (omitted from Sheet 1.1).
7. Standalone geotechnical borehole report for the Type 1B parcel.
8. Building-wise BOQ allocation schedule.

---

## 9. Why Quantity Takeoff is Strictly Blocked

Full quantity takeoff is strictly **BLOCKED** because:
1. **Vertical Geometry is Unscheduled**: Tender drawings present only the ground floor plan; floor-to-floor heights, beam depths, and slab thicknesses are omitted due to missing architectural sections and structural framing drawings.
2. **Substructure Depths are Incomplete**: Pile layout Sheet 1.1 displays pile coordinates but omits pile depth below cut-off.
3. **Absence of Bar Bending Schedules**: Rebar tonnage cannot be determined without cutting lengths, lap staggering, and hook details.
4. **BOQ Aggregation**: Schedule B combines quantities across multiple building types; estimating quantities without single-building ground truth prevents validation.

---

## 10. Mandatory Dataset Disclaimers

- **No quantities were calculated** ($0.0\text{ m}^3$ concrete, $0.0\text{ m}^3$ masonry, $0.0\text{ MT}$ steel, $0.0\text{ m}^2$ finishes).
- **No costs were calculated** (`Cost accuracy: NOT_CALCULATED`).
- **No BOQ validation was performed** (`Quantity accuracy: NOT_CALCULATED`).
- **No labour or duration modelling was performed** (`Labour/Duration: BLOCKED`).
- **BOQ and ECPT were NOT used as AI inputs**.
- **Dataset Readiness**: The project strictly remains **`DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`**.
- **The project is strictly NOT `READY_FOR_TAKEOFF`**.

---

## 11. Recommended Phase 2 Task

**Recommended Next Step**: **Second Pilot Phase 2 — Controlled Ground Floor Architectural & Foundation Transcription**.  
Proceed with controlled, evidence-tagged transcription of directly visible parameters on the two available Type 1B drawings:
- Extract ground floor room dimensions, door schedules, and window schedules from Sheet `NUC(1)-FAH - A.2.1`.
- Extract pile counts, pile diameter, and grid coordinates from Sheet `NUC- FAH(1B)-S-A.1`.
- Tag all parameters with their exact 9-tier provenance and halt execution on all missing vertical and superstructure elements.

