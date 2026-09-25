# Project Claims, Boundaries, and Limitations

**Document Purpose**: Definitive boundaries guide for project presentation, documentation, and thesis defense.  
**Governing Standard**: Academic honesty, ethical quantity surveying practice, and strict evidence control.

---

### 1. What This Project CAN Claim

The major project research has established, verified, and delivered the following defensible accomplishments:
1. **Multi-Document Tender Corpus Structuring**: Successfully assembled and structured a complete 55-sheet tender package from RITES/Oil India Limited (Architectural, Structural, MEP, DBR, Tender Notices, Award Records, CPWD Specifications) into an open, auditable data environment.
2. **Standardized Provenance Schema (9 Tiers)**: Formulated and implemented a 9-tier evidence provenance hierarchy that categorizes every civil engineering parameter by its derivation method and bans assumptions from claiming `HIGH_CONFIDENCE`.
3. **Multi-Discipline Civil Reconciliation**: Constructed an inter-document reconciliation framework that aligns structural framing layouts with architectural room schedules and elevations across 9 vertical building datums.
4. **Purging of Ungrounded Heuristics**: Successfully identified, audited, and eradicated ungrounded rules-of-thumb (e.g., blanket 23% external and 10% internal wall opening deduction percentages) in favor of deterministic schedule tracking.
5. **IS 1200 Formula Dependency Architecture**: Mapped 14 standardized civil measurement formulas into an automated dependency graph that halts execution whenever prerequisite operands are unverified.
6. **Verified Proof-of-Method Micro-Takeoff**: Demonstrated formula-recomputed micro-takeoff traceable to verified inputs across 15 isolated sample calculations (5 door/window face areas, 5 room carpet areas, 5 room perimeters) directly from approved drawing callouts, internally consistent with Priority F sample registers.
7. **Engineered Refusal & Guardrail System**: Developed an active refusal engine that successfully intercepts and documents 14 blocked civil trades when drawings lack necessary schedules, proving that automated refusal is a vital engineering feature against hallucination.

---

### 2. What This Project CANNOT Claim Yet

To maintain complete academic and professional integrity, the following claims are **STRICTLY PROHIBITED**:
1. **NO Claim of "Full BOQ Automation"**: The system does NOT automatically generate a Bill of Quantities from drawings. It provides an auditable transcription and formula layer.
2. **NO Claim of "Cost Accuracy"**: Cost accuracy is **`NOT_CALCULATED`**. RITES issued an aggregate multi-building tender without an official single-tower BOQ; calculating a fake accuracy percentage against an unverified single-tower estimate is prohibited.
3. **NO Claim of "Full Tower Takeoff"**: Full building material quantities (total concrete, total brickwork, total plaster, total paint, total flooring) are **`NOT_CALCULATED`** and remain strictly blocked.
4. **NO Claim of "Reinforcement Takeoff"**: Total rebar tonnage ($300.85\text{ MT}$ or any other figure) is **`BLOCKED`** because no official Bar Bending Schedule (BBS) was issued by the structural engineer.
5. **NO Claim of "Labour & Duration Prediction"**: Construction duration and gang productivity are **`NOT_VALIDATED`** and **`BLOCKED`**. The contract duration is 24 months (December 2025 award), but single-tower duration has not been modeled.
6. **NO Claim of "End-to-End Model Training Completed"**: No deep neural network or LLM has been fine-tuned or trained on this dataset to predict quantities.
7. **NO Claim of "Takeoff Validation Completed"**: Ground-truth validation has NOT occurred because independent ground truth for a single tower does not exist in the tender documents.

---

### 3. What Has Been Demonstrated

The project has practically demonstrated:
- **Human-Auditable Transcription**: Populated registers for 207 piles, 49 vertical elements (16 columns, 33 shear walls), 34 framing beams, 10 opening marks, and 5 room archetypes with exact drawing coordinates.
- **Inter-Trade Geometric Resolution**: Traced vertical storey heights ($3.05\text{m}$) from Architectural Section A-A (`AR/TD/012`) to supply missing height data for Structural Sheet `STR/TD/104`.
- **Zero-Tolerance Provenance Labeling**: Every value is tagged:
  - Direct callouts $\rightarrow$ `DIRECT_SHEET_OBSERVATION`
  - Calculated areas $\rightarrow$ `DERIVED_BY_BASIC_GEOMETRY`
  - Rebar lap lengths $\rightarrow$ `IS_CODE_DERIVED` (IS 456 formula $45.3d$, capped at `MEDIUM` confidence)
  - Estimated parameters $\rightarrow$ `ESTIMATED` / `MEDIUM` (Never `HIGH_CONFIDENCE`).
- **Traceability on Grounded Scope**: Verified that given complete $L, B, H$ inputs, the system computes areas and perimeters that are formula-recomputed from controlled dimensions and internally consistent with the Priority F register.

---

### 4. What Remains Blocked & The 14 Blocked Trades

The following 14 civil work packages are intentionally locked behind our refusal guardrail:
1. **Bored Cast-in-Situ Piling Concrete**: Blocked due to omission of pile termination depth on Sheet 100.
2. **RCC Pile Caps Concrete**: Blocked due to drafting discrepancy: 54 visual caps on layout plan vs. 84 caps in summary schedule.
3. **Plinth Beams Concrete**: Blocked due to reliance on preliminary 403.5m centerline run without floor-specific span deduction.
4. **Superstructure Columns & Shear Walls Concrete**: Blocked due to lack of beam-column joint deduction protocol.
5. **Suspended Floor Beams Concrete**: Blocked due to repeated-floor assumption across levels with potential load variations.
6. **Suspended Floor Slabs Concrete**: Blocked due to unverified sunken slab depressings ($300\text{mm}$ in toilets) and slab cutouts.
7. **Reinforcement Steel (All Trades)**: Blocked due to total lack of engineer-approved Bar Bending Schedules (BBS).
8. **Brick Masonry (External 250mm & Internal 125mm)**: Blocked due to lack of floor-segregated centerlines and opening-to-wall coordinate mapping.
9. **Internal Cement Plaster (12mm)**: Blocked due to missing room-by-room opening deduction aggregation.
10. **External Waterproof Plaster (18mm)**: Blocked due to missing external surface area projection and architectural groove deductions.
11. **Floor Finishes (Vitrified, Ceramic, Kota)**: Blocked due to lack of room-wise door threshold adjustments and skirting height schedules.
12. **Internal & External Painting**: Blocked due to dependency on unresolved plaster and masonry surface areas.
13. **Overhead Water Tank (OHT) Concrete & Waterproofing**: Blocked due to wall ($150\text{mm}$) and base ($200\text{mm}$) thickness being code assumptions rather than scheduled structural details.
14. **Staircase Concrete & Finishes**: Blocked due to incomplete landing beam integration and nosing finish details.

---

### 5. What Evidence is Needed to Unblock Each Scope

To unblock the 14 scopes, the following project records must be procured from the project engineer/client:
- **For Substructure**: Structural RFI response clarifying pile termination depth below cut-off level and reconciled pile cap grouping drawing.
- **For Superstructure Concrete**: 3D framing coordinate model or beam-column joint schedule specifying clear spans between member faces.
- **For Reinforcement**: Contractor-submitted and engineer-approved Bar Bending Schedules (BBS) detailing bar marks, cutting lengths, lap locations, and bend deductions.
- **For Masonry & Finishes**: Architectural wall schedule mapping each individual door, window, and ventilator opening to its specific host wall gridline.
- **For Commercial & Schedule**: Approved Contract Price Breakdown (Schedule of Quantities broken down by building asset) and Contractor's approved baseline CPM construction programme.

---

### 6. Guide for Presenters: How to Avoid Overclaiming

When presenting to the major project examination panel, follow these strict communication rules:

| If Asked About... | DO NOT SAY... | INSTEAD, SAY... |
|---|---|---|
| **Accuracy** | "Our AI achieved 98% quantity accuracy." | "Quantity and cost accuracy are explicitly **`NOT_CALCULATED`** because the tender only provides an aggregate multi-building BOQ without an official single-tower breakdown." |
| **Quantities** | "We calculated that the tower has $2,400\text{ m}^3$ of concrete." | "Full tower takeoff is **`BLOCKED`**. We calculated 15 isolated micro-sample quantities where drawing evidence is 100% verified, while blocking bulk quantities to prevent hallucination." |
| **Reinforcement** | "We estimated 300 metric tonnes of steel." | "Reinforcement steel calculation is **`BLOCKED`** because the tender drawings omit a Bar Bending Schedule (BBS). In professional civil engineering, steel cannot be claimed without cutting lengths." |
| **AI Role** | "Our neural network automatically designed the building and calculated the BOQ." | "AI serves as a structured parser and reconciliation assistant; all calculations are deterministic IS 1200 formulas, and the system actively halts when evidence is incomplete." |
| **Refusal** | "We ran out of time to calculate the rest." | "Halting is an intentional engineering safety feature. Producing numbers when drawings omit depths and schedules is professional negligence; our guardrail halts takeoff and logs an RFI." |


