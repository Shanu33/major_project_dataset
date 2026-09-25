# Candidate Update Notes

**Project**: OIL/RITES Duliajan BQ Workmen Housing Complex  
**Tender**: `RITES/NERPO/OIL/BQ-HOUSING/25`  
**Recovery Search Date**: September 17, 2026  

---

## Recovered Official Document Evaluation

### Corrigendum-Reply_to_Queries_pdf-2025-Sep-17-09-35-31.pdf
- **Source**: RITES Official Tender Repository (`https://www.rites.com/Upload/Tender/Corrigendum-Reply_to_Queries_pdf-2025-Sep-17-09-35-31.pdf`)
- **Document Type**: Official Pre-Bid Query Clarification (12 pages, 14 query replies)
- **Project Match Evidence**: Exact match — Tender ID: `2025_RITES_246752_1`, E-Tender No: `RITES/NERPO/OIL/BQ-HOUSING/25`, Work: `Construction of Workman Housing Complex (BQ Area) on EPC mode -II of contract at OIL Duliajan, Assam`
- **What it proves**: 
  1. Tender reference numbers and project identity verified against RITES official records.
  2. Defects Liability Period confirmed as 24 months (Operation & Maintenance obligation).
  3. Crucially confirms EPC Mode-II contractual structure: Clause 1.9 stipulates that the EPC contractor is required to prepare 3D models, walkthroughs, and structural design engineering using ETABS / STAAD PRO, Revit, AutoCAD, Navisworks, and Primavera within 15 days of award.
  4. This provides direct official proof that **detailed structural design, modeling, working drawings, and bar bending schedules are post-award EPC contractor deliverables**, not pre-tender public issues.
- **What current assumption it replaces**: Does not replace material quantity assumptions. Replaces ambiguity about why working drawings/BBS are not in the tender packet.
- **Which quantity rows would change**: NONE. The document contains contractual, commercial, and software compliance replies; it contains no material schedules or rates.
- **Whether confidence can be upgraded**: NO. Material takeoff confidence remains unchanged.
- **Whether BOQ/cost/labour/duration validation becomes possible**: NO. Validation remains blocked.

---

## Candidate Update Template (for Future Recoveries)

When an official document is recovered, record the following before updating any quantity:

```
### [Document Name]
- **Source**: [URL or acquisition path]
- **Document Type**: [Pile schedule / BBS / BOQ / Working drawing / etc.]
- **Project Match Evidence**: [Tender ref, project title, location, client, date]
- **What it proves**: [Specific technical fact with values]
- **What current assumption it replaces**: [Reference to specific row in assumptions_log.csv or quantity file]
- **Which quantity rows would change**: [File path + row numbers]
- **Whether confidence can be upgraded**: [YES/NO + from what to what]
- **Whether BOQ/cost/labour/duration validation becomes possible**: [YES/NO + explanation]
```

---

## Remaining Inaccessible Records

The following documents are **required but not publicly available**:

### 1. Post-Award Working Drawings
- **Type**: Foundation working drawings, pile cap working drawings
- **Why needed**: To resolve pile depth, cap count contradiction, pile allocation
- **Produced by**: RITES structural design team or contractor's EPC design consultant
- **Status**: Internal RITES/contractor document; not published

### 2. Contractor Bar Bending Schedule (BBS)
- **Type**: Official BBS per IS 2502 for all structural elements
- **Why needed**: To replace derived cut-length calculations with engineer-issued schedules
- **Produced by**: Contractor M/s Badri Rai & Company (EPC scope)
- **Status**: Post-award design deliverable; not published

### 3. Approved EPC Design Submissions
- **Type**: STAAD/ETABS model outputs, structural adequacy reports, design review notes
- **Why needed**: To verify structural design parameters and cross-section accuracy
- **Produced by**: Contractor's structural design consultant
- **Status**: Submitted to RITES for proof checking; not published

### 4. Internal Priced BOQ / Rate Analysis
- **Type**: Contractor's itemized cost breakdown with quantities, rates, and amounts
- **Why needed**: To validate tower cost allocation and enable cost accuracy calculation
- **Produced by**: Contractor / RITES Contract Cell
- **Status**: Commercial-in-confidence; not published. May be obtainable via RTI.

### 5. Foundation Schedule
- **Type**: Tabulated pile schedule with founding depth, cut-off level, cage details per pile
- **Why needed**: To confirm pile depth (currently assumed 18m from DBR range)
- **Produced by**: Geotechnical consultant / structural designer
- **Status**: Part of detailed engineering working drawings; not in tender package

### 6. Pile Cap Schedule
- **Type**: Tabulated pile cap marks with dimensions, pile allocation, reinforcement
- **Why needed**: To resolve 54 vs 84 cap contradiction
- **Produced by**: Structural designer
- **Status**: Part of working drawings; not in tender package

### 7. Floor-Wise Finishes Schedule
- **Type**: Room-by-room measured quantity schedule for masonry, plaster, flooring, dado, skirting
- **Why needed**: To replace estimated deductions with controlled room-wise transcription
- **Produced by**: Architect / quantity surveyor
- **Status**: Contractor deliverable under EPC; not in tender package. Schedule_of_Finishes.pdf specifies types not quantities.

---

## Recommended Acquisition Paths

| # | Path | Target Document | Feasibility | Effort |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **RITES PU-Guwahati Tender Cell** | Working drawings, pile schedule, cap schedule | HIGH (official agency) | Formal letter / email request |
| 2 | **Oil India Limited Project Dept, Duliajan** | Foundation schedule, approved EPC submissions | HIGH (client PSU) | Formal project information request |
| 3 | **RTI Application to OIL** | Priced BOQ, cost breakdown, contract schedules | MEDIUM (PSU obligation under RTI Act) | ₹10 fee + 30 days statutory response |
| 4 | **Contractor M/s Badri Rai & Company** | BBS, shop drawings, working drawings | LOW (commercial sensitivity) | Relationship / professional request |
| 5 | **Site visit / execution records** | As-built drawings, pile load test reports | MEDIUM (requires site access) | Physical visit to Duliajan site |
| 6 | **RITES Tender Portal - Archived Downloads** | Tender drawing zip package (if still downloadable) | LOW (typically removed post-award) | Try CPPP archive search with registered login |
| 7 | **Academic / internship contact** | Site execution records, design reports | LOW (informal, uncontrolled) | Professional network |
