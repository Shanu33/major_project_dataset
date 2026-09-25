# Major Project Executive Brief: Evidence-Controlled Civil Quantity Intelligence

**Academic Unit**: Department of Civil Engineering | Major Project Technical Review  
**Project Benchmark**: OIL India Workmen Housing Complex, Duliajan, Assam (RITES Tender: `RITES/NERPO/OIL/BQ-HOUSING/25`)  
**Primary Unit of Analysis**: Typical Stilt+6 BQ Residential Housing Tower ($483.60\text{ m}^2$ footprint, 24 units)

---

### 1. Project Title
**Evidence-Controlled Multi-Document Architecture for Construction Quantity Takeoff and Artificial Intelligence Benchmarking**

### 2. Problem Statement
Current generative AI and machine learning applications in construction quantity estimation suffer from three fatal flaws:
1. **Prompt Poisoning & Data Leakage**: Feeding tender BOQs directly into prompts, causing models to parrot answers rather than interpreting architectural and structural drawings.
2. **Ungrounded Hallucination**: Generating plausible-sounding concrete, steel, and masonry quantities when source drawings lack required geometric dimensions or schedules.
3. **Absence of Provenance**: Estimating quantities without an auditable chain linking numbers back to specific drawing sheets, gridlines, and IS 1200 measurement rules.

### 3. Objective
To construct an open, auditable, multi-document dataset and deterministic pipeline that:
- Extracts structural, architectural, and geotechnical parameters under strict evidence-provenance controls.
- Reconciles inter-trade document discrepancies (structural framing vs. architectural finishes).
- Implements an automated refusal guardrail that halts takeoff when prerequisite engineering data is missing, demonstrating a safe, production-grade foundation for construction intelligence.

### 4. Dataset Used
- **Tender Context**: EPC Contract awarded December 2025 by Oil India Limited via PMC RITES Limited (Award Value: ₹128.14 Cr).
- **Core Corpus**: 55 full-size tender drawing sheets: Architectural (26 sheets, `AR/001`–`026`), Structural (23 sheets, `STR/100`–`150`), and Building Services (18 sheets, `MEP/001`–`018`).
- **Technical Baselines**: Design Basis Report (DBR), Geotechnical Soil Investigation Report, CPWD Specifications 2019, and Bureau of Indian Standards codes (IS 1200, IS 456, IS 13920, IS 2911).

### 5. Methodology
- **Ontological Separation**: Strict separation between predictive inputs (Drawings, DBR, Specs) and blind validation targets (BOQ, SOR, CPM Schedule).
- **9-Tier Provenance Hierarchy**: Every parameter is classified from Tier 1 (`DIRECT_SHEET_OBSERVATION`) to Tier 9 (`ENGINEERING_ASSUMPTION_UNVERIFIED`). Zero assumptions are allowed to claim `HIGH_CONFIDENCE`.
- **Heuristic Purging**: Revoked legacy rules-of-thumb (e.g., 23% external and 10% internal wall opening deductions) in favor of explicit door/window schedules.
- **Dependency-Driven Execution**: Takeoff formulas are linked to verified inputs; missing inputs trigger an auditable refusal log rather than an estimate.

### 6. Current Prototype Capability
- **Transcription Layer**: 100% controlled transcription of foundation layout, 49 vertical columns/shear walls, 34 framing beams, 10 opening marks, and 5 room archetypes across 9 vertical building levels.
- **Reconciliation Engine**: Reconciled floor-to-floor heights ($3.05\text{m}$ from Architectural Section A-A vs. structural schedules) and resolved vertical datums from Stilt ($+0.00\text{m}$) to Mumty ($+24.00\text{m}$).
- **Formula Architecture**: 14 standardized IS 1200 measurement formulas mapped into an automated dependency graph.
- **Automated Refusal Engine**: 14 major takeoff work packages successfully intercepted and safely blocked due to missing drawing schedules.

### 7. Sample Result (Proof-of-Method)
- **15 Verified Micro-Calculations**: Executed on isolated architectural elements with verified drawing evidence:
  - *Door D1 Face Area*: $0.800\text{m} \times 2.100\text{m} = 1.680\text{ m}^2$ (Toilet Door, Sheet `AR/TD/005`)
  - *Window W1 Face Area*: $1.200\text{m} \times 1.200\text{m} = 1.440\text{ m}^2$ (Bedroom Window, Sheet `AR/TD/005`)
  - *Living/Dining Carpet Area*: $5.520\text{m} \times 3.970\text{m} = 21.914\text{ m}^2$ | Perimeter: $18.980\text{m}$ (Sheet `AR/TD/005`)
  - *Master Bedroom Carpet Area*: $3.845\text{m} \times 3.220\text{m} = 12.381\text{ m}^2$ | Perimeter: $14.130\text{m}$ (Sheet `AR/TD/005`)
- *Traceability & Consistency*: Formula-recomputed from controlled dimensions, internally consistent with Priority F sample register; zero multipliers applied.

### 8. Current Limitations & Blocked Scopes
- **Full Tower Takeoff**: Strictly **BLOCKED**. Bulk concrete, steel reinforcement, masonry, and finish quantities are withheld.
- **Substructure Incompleteness**: Pile depth ($18\text{m}$) is a geotechnical assumption from DBR text (omitted on Sheet 100); 54 pile caps on plan vs. 84 in schedule remains an unresolved drafting contradiction.
- **Reinforcement Incompleteness**: Zero bar bending schedules (BBS) were issued in the tender package. Steel cut lengths cannot be deterministically verified.
- **Commercial & Schedule Metrics**: Cost accuracy and single-tower construction duration are designated `NOT_CALCULATED` because RITES issued only an aggregate 8-tower BOQ without a single-tower breakdown.

### 9. Next Work
1. **Priority I**: Controlled transcription of 18 Building Services (MEP) drawings (Plumbing, Firefighting, Electrical).
2. **Multi-Project Dataset Expansion**: Ingest 5–10 additional public works (CPWD/PSU) tender sets to form a multi-building benchmark corpus.
3. **Interactive Demonstration Tool**: Package the controlled registers and refusal rules into a web-based audit interface.

### 10. Final Value Proposition
**"In civil engineering AI, the ability to provably refuse an estimate when drawings lack data is far more valuable than an unverified number."**


