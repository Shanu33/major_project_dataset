# AI Input vs. Ground Truth Separation Note
## Civil Engineering Intelligence Pilot: OIL/RITES Duliajan BQ Housing

**Folder**: `10_Controlled_Transcription/`  
**Date**: September 17, 2026  
**Status**: Critical Architecture Rule for Phase-1 Pilot  

---

## 1. Document Separation Framework

In any machine learning or automated civil engineering intelligence system, there is a fundamental distinction between **Input Documents** (what the model reads to extract and estimate) and **Ground Truth Documents** (what the predictions are validated against).

```
┌─────────────────────────────────────────────────────────────┐
│                   AI INPUT DOCUMENTS                        │
│  (Available in tender repository — 23 unique PDFs)          │
│                                                             │
│  - Architectural Drawings (Plans, Sections, Elevations)     │
│  - Structural Drawings (Framing Plans, Schedules, Details)  │
│  - Design Basis Report (DBR)                                │
│  - Geotechnical Investigation Report (310 pages)            │
│  - Technical Specifications Volume (CPWD / IS Codes)        │
│  - Schedule of Finishes & Door/Window Schedules             │
│  - Master EPC Scope of Work & Topographic Surveys           │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             CONTROLLED EXTRACTION & TAKEOFF                 │
│  (Human transcription / Computer vision / Formula ledger)   │
│                                                             │
│  - Exact geometric measurements from drawings               │
│  - Scheduled reinforcement diameters and counts             │
│  - Room dimensions and opening deduction registers          │
│  - Formulated physical quantity estimates                   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             GROUND TRUTH / VALIDATION DOCUMENTS             │
│  (MISSING / PROPRIETARY / POST-AWARD INTERNAL RECORDS)      │
│                                                             │
│  - Owner-Approved Itemized Bill of Quantities (BOQ)         │
│  - Contractor Priced BOQ with Item Rate Analysis            │
│  - Approved Bar Bending Schedules (BBS per IS 2502)         │
│  - Approved Baseline Construction Programme (Primavera)     │
│  - Contractor Monthly Progress Reports & Measurement Books  │
│  - Final As-Built Drawings & Handover Records               │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Current Status in This Pilot Project

| Document Class | Current Status | Impact on Intelligence System |
| :--- | :--- | :--- |
| **AI Input Documents** | **PRESENT & VERIFIED (100%)** | The complete pre-award tender package (23 unique PDFs) is available. Geometric layouts, member marks, and specification criteria are fully accessible. |
| **Ground Truth Documents** | **ABSENT / NOT PUBLIC (0%)** | Under EPC Mode-II (Turnkey Component Basis), the owner never generated an itemized material BOQ. Official BBS, working drawings, and rate analyses are post-award contractor deliverables. |

---

## 3. Methodological Implications

### What This Pilot CAN Defensibly Claim:
1. **Document Understanding**: Parsing and linking complex Indian public-works tender documentation across disciplines (Architecture, Structure, Geotech, DBR).
2. **Controlled Takeoff Preparation**: Transcribing drawing geometry into normalized, auditable tabular schemas (`10_Controlled_Transcription/`).
3. **Traceable Engineering Takeoffs**: Computing physical concrete volumes, rebar tonnages, and wall areas with 100% transparent formulas and explicit assumption tags.
4. **Contradiction Detection**: Identifying and isolating technical discrepancies in tender packages (e.g. 54 vs. 84 pile caps, unverified 18m pile depth).

### What This Pilot CANNOT Claim:
1. **Cost Accuracy Validation**: **Cannot be claimed.** No itemized priced BOQ exists to measure cost accuracy against.
2. **Quantity Accuracy Validation**: **Cannot be claimed.** No independent audited bill of materials exists.
3. **Labour & Duration Benchmarking**: **Cannot be claimed.** No contractor daily logs or approved baseline CPM schedules are available.

---

## 4. Conclusion for Pilot Dataset v1

This pilot dataset serves as a rigorous benchmark for **drawing extraction, engineering takeoff transparency, and error detection**. It must **never** report fabricated validation percentages or pretend that proprietary post-award contractor records exist in public tender repositories.

