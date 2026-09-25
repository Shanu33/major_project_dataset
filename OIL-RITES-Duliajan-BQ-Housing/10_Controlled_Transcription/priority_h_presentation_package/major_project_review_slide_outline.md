# Major Project Review: Slide-by-Slide Outline

**Project Title**: Evidence-Controlled Civil Quantity Takeoff and Multi-Document Architecture for Construction Intelligence  
**Pilot Project**: OIL India Workmen Housing Complex, Duliajan, Assam (RITES Tender: `RITES/NERPO/OIL/BQ-HOUSING/25`)  
**Target Audience**: Major Project Evaluation Committee / Civil Engineering Examination Panel  
**Estimated Presentation Duration**: 15–20 minutes (+ 10 minutes Q&A)

---

### Slide 1: Title & Project Objective
- **Slide Title**: Evidence-Controlled Construction Quantity Intelligence: A Rigorous Multi-Document Pilot on Oil India BQ Housing
- **Key Message**: Developing an auditable, multi-document dataset and AI-ready framework for construction quantity takeoff that enforces strict evidence provenance and refuses hallucination when drawings lack detail.
- **Bullet Content**:
  - **Research Focus**: Structural and architectural quantity estimation from tender drawings without prompt poisoning.
  - **Pilot Benchmark**: Typical Stilt+6 BQ Residential Housing Tower ($483.60\text{ m}^2$ footprint, 24 dwelling units).
  - **Core Innovation**: Evidence-controlled transcription, cross-register civil reconciliation, and an engineered refusal guardrail when data is missing.
  - **Supervision & Discipline**: Department of Civil Engineering — Major Project Review.
- **Suggested Visual**: High-resolution 3D isometric or elevation render of the Stilt+6 BQ Tower alongside the project folder directory schema.
- **Speaker Note**:
  > "Good morning, respected members of the panel. Today, we present our work on developing an evidence-controlled dataset and architectural framework for AI in civil quantity takeoff. Instead of treating quantity surveying as a black-box text-generation task, our work addresses the foundational civil engineering problem: how to establish a deterministic, auditable link between multi-trade drawings, code specifications, and takeoff formulas while preventing false estimates when drawing evidence is incomplete."

---

### Slide 2: Problem in Construction Quantity Estimation & AI Failures
- **Slide Title**: The AI Quantity Estimation Trap: Hallucination, Leakage, and Lost Provenance
- **Key Message**: Current AI approaches to construction estimation fail in production because they treat estimation as text generation, leading to prompt leakage and ungrounded approximations.
- **Bullet Content**:
  - **The Black-Box Failure**: LLMs produce convincing numbers ($2,400\text{ m}^3$ concrete, $300\text{ MT}$ steel) without tracing back to specific gridlines or schedules.
  - **Data Poisoning**: Feeding tender BOQs directly into prompts creates artificial 100% accuracy, masking the inability to read drawings.
  - **Heuristic Reliance**: Standard tools rely on synthetic percentages (e.g., blanket 10% door deductions) that cause major contractual disputes.
  - **Civil Reality**: Quantity takeoff is deterministic geometry governed by IS 1200, requiring exact dimensions, deduction rules, and schedule cross-checks.
- **Suggested Visual**: Comparison diagram: "Naïve AI (Drawings + BOQ in Prompt $\rightarrow$ Hallucinated Takeoff)" vs "Evidence-Controlled AI (Drawings $\rightarrow$ Controlled Transcription $\rightarrow$ Proof-of-Method $\rightarrow$ Refusal Engine)".
- **Speaker Note**:
  > "In industry and academic research, many attempt to feed drawings and BOQs together into large multimodal models. This causes data leakage—the model simply recites the BOQ rather than understanding building geometry. Furthermore, when drawings lack a bar bending schedule or pile depths, naïve AI hallucinates numbers rather than admitting the data is missing. In civil engineering contracts, an ungrounded estimate leads to arbitration and financial overrun."

---

### Slide 3: Why Project-Level Document Matching Matters
- **Slide Title**: Document Matching: The Prerequisite for Reliable Construction Intelligence
- **Key Message**: Construction is not single-document; an estimator must correlate architectural plans, structural schedules, and technical specifications from the same tender package.
- **Bullet Content**:
  - **The Multi-Document Reality**: A single beam requires Architectural elevation (clear height), Structural plan (framing span), Structural schedule (rebar marks), and DBR (concrete grade).
  - **Random Scraping Fails**: Training AI on mismatched drawings and unrelated BOQs teaches noise.
  - **Closed-Loop Package**: This pilot captures the complete tender ecosystem from RITES/OIL India (Drawings, DBR, Tender Notices, Award Records, CPWD Specifications).
  - **Inter-Trade Consistency**: Detecting where architecture and structure conflict before concrete is poured.
- **Suggested Visual**: Multi-document Venn/network diagram showing the intersection of Architectural, Structural, Geotechnical/DBR, and Contractual documents on the BQ Tower.
- **Speaker Note**:
  > "Why did we focus deeply on one complete tender package rather than scraping fifty disconnected drawings from the web? Because real civil engineering takeoff requires inter-document reconciliation. If you take a beam from project A and a column from project B, you destroy the geometric coherence. By capturing the complete tender ecosystem of this OIL India housing complex, we model the exact cross-document dependency that a Senior Quantity Surveyor navigates."

---

### Slide 4: Selected Pilot Project and Dataset Corpus
- **Slide Title**: Pilot Benchmark: OIL India Workmen Housing Complex, Duliajan
- **Key Message**: A real-world, high-seismic Zone V EPC project with comprehensive architectural, structural, and infrastructure documentation.
- **Bullet Content**:
  - **Project Authority**: Oil India Limited (Owner) / RITES Limited (Project Management Consultant).
  - **Tender ID & Value**: `RITES/NERPO/OIL/BQ-HOUSING/25` | Contract Value: ₹128.14 Crore (awarded Dec 2025).
  - **Target Element**: Typical Stilt+6 BQ Residential Housing Tower (Footprint: $30.08\text{ m} \times 16.08\text{ m} = 483.60\text{ m}^2$, Height: $24.0\text{ m}$).
  - **Drawing Corpus Audited**: 55 drawing sheets across Architectural (26), Structural (23), and Services/MEP (18) tender sheets.
- **Suggested Visual**: Floor plan of Sheet `AR/TD/007` alongside structural column layout `STR/TD/103` showing the 4-unit typical floor layout.
- **Speaker Note**:
  > "Our pilot dataset is based on the OIL India Workmen Housing Complex in Duliajan, Assam, designed by RITES. It is a major multi-tower development in Seismic Zone V. We isolated one typical Stilt+6 BQ tower as our primary benchmark unit. This gives us a controlled, highly dense structural frame: 207 piles, 49 vertical columns/shear walls, 34 framing beams per floor, and 24 residential apartments with identical repeating floor plates."

---

### Slide 5: Ontological Separation: AI Inputs vs Ground-Truth Targets
- **Slide Title**: Preventing Data Poisoning: Strict Separation of Inputs and Ground Truth
- **Key Message**: Drawings and specifications are predictive inputs; BOQs, costs, and contractor schedules are strictly reserved as blind ground-truth evaluation targets.
- **Bullet Content**:
  - **Predictive AI Input Domain**: Architectural Drawings (`AR`), Structural Drawings (`STR`), DBR, and CPWD Technical Specifications.
  - **Blind Ground Truth Domain**: Official BOQ schedules, priced rate analyses, and contractor CPM construction schedules.
  - **Zero Leakage Rule**: BOQ descriptions and quantities are never placed in extraction prompts or intermediate registers.
  - **Academic Integrity**: Because this tender provided only an aggregate multi-building Schedule of Quantities without an official single-tower BOQ, cost accuracy is honestly designated as `NOT_CALCULATED`.
- **Suggested Visual**: System ontology diagram highlighting the strict "Firewall" separating Predictive Inputs from Validation Targets.
- **Speaker Note**:
  > "Slide 5 illustrates our core methodological safeguard: the ontological separation between AI inputs and ground truth. In many machine learning papers, models are fed tender BOQs to predict quantities. That is circular reasoning. In our pipeline, the model sees only the drawings and technical specifications. The BOQ and contract costs remain strictly behind a blind evaluation firewall. Furthermore, because RITES issued an aggregate 8-tower tender BOQ without an official single-tower breakdown, we refuse to claim a fake cost accuracy percentage."

---

### Slide 6: Evidence-Control Methodology & Provenance Hierarchy
- **Slide Title**: Evidence-Control Methodology: 9 Tiers of Engineering Provenance
- **Key Message**: Every parameter is tagged with an explicit provenance level; assumptions are barred from claiming 'High Confidence'.
- **Bullet Content**:
  - **Hierarchy Tiers**:
    1. `DIRECT_SHEET_OBSERVATION` (Exact printed text/callout)
    2. `DERIVED_FROM_ARCHITECTURAL_SECTION` (Vertical geometry from sections)
    3. `DERIVED_BY_BASIC_GEOMETRY` ($L \times B$, perimeters)
    4. `IS_CODE_DERIVED` (Standard lap formulas: $45.3d$, cover)
    5. `ENGINEERING_ASSUMPTION_STANDARDIZED` (Estimated inputs, capped at `MEDIUM` confidence)
  - **Purging Heuristics**: Legacy 23% external and 10% internal wall opening deduction heuristics were completely revoked and replaced with schedule-based geometry.
  - **Confidence Discipline**: Zero assumptions are permitted to hold a `HIGH_CONFIDENCE` tag.
- **Suggested Visual**: Provenance hierarchy pyramid showing Level 1 (`DIRECT_SHEET_OBSERVATION`) at the foundation down to Level 9 (`ENGINEERING_ASSUMPTION_UNVERIFIED`) at the apex.
- **Speaker Note**:
  > "A critical contribution of this project is our 9-level evidence provenance hierarchy. When an engineer reads a column schedule, that is Level 1 direct observation. When we calculate a room area, that is Level 3 derived geometry. But when rebar lap lengths are computed from IS 456, that is code-derived. Crucially, we enforced a strict rule: no assumption may be labeled 'High Confidence'. We also purged the ungrounded rules-of-thumb—like deducting a blanket 23% for window openings—demanding instead that every opening be matched to its door/window mark."

---

### Slide 7: System Architecture: 11-Stage Pipeline
- **Slide Title**: System Architecture: From Raw PDFs to Verified Proof-of-Method
- **Key Message**: A modular, pipeline architecture moving systematically across transcription, reconciliation, formula mapping, and refusal guardrails.
- **Bullet Content**:
  - **Phase 0–2**: Document Ingestion, Inventory Verification, and Drawing Legibility Validation.
  - **Phase 3–5 (Priorities A, B, C)**: Controlled Substructure, Structural Frame, and Architectural Transcription.
  - **Phase 6 (Priority D)**: Civil Cross-Register Reconciliation (Resolving inter-trade geometric clashes).
  - **Phase 7 (Priority E)**: Formula Definition & Dependency Mapping (Setting takeoff formulas without executing unverified data).
  - **Phase 8 (Priority F)**: Sample Proof-of-Method Execution & Automated Guardrail Interception.
- **Suggested Visual**: Comprehensive Mermaid architecture pipeline diagram showing Phase 0 through Phase 10 with colored status badges.
- **Speaker Note**:
  > "Here is our 11-stage system architecture. Rather than attempting a monolithic 'PDF-to-BOQ' transformation, our pipeline breaks down the problem into discrete, auditable layers. Notice Phases 3, 4, and 5 where Foundation, Frame, and Architectural registers are populated independently. In Phase 6, they undergo civil reconciliation. In Phase 7, formulas are linked to registered parameters. If any input is unverified, Phase 8 intercepts the calculation and halts takeoff."

---

### Slide 8: Controlled Transcription & Civil Reconciliation Workflow
- **Slide Title**: Cross-Register Reconciliation: Aligning Structure and Architecture
- **Key Message**: Architectural and structural drawings often conflict; our reconciliation matrix resolves scope boundaries before formulas are evaluated.
- **Bullet Content**:
  - **Level Baseline**: Reconciled Ground Level ($+0.00\text{m}$), Plinth ($+0.30\text{m}$), First Floor ($+3.00\text{m}$), Terrace ($+21.30\text{m}$), Mumty ($+24.00\text{m}$).
  - **Conflict Identification**:
    - Structural drawings call for 33 Shear Walls and 16 Columns; architectural floor plans show simplified partition layouts.
    - Floor-to-floor height ($3.05\text{m}$) verified from Architectural Section A-A (`AR/012`), not structural layout (`STR/104`).
  - **Wall Takeoff Matrix**: Masonry lengths must be deducted by column widths and beam soffits, not estimated from gross room bounds.
- **Suggested Visual**: Excerpt of `civil_reconciliation_index.csv` and `floor_scope_reconciliation.csv` with a side-by-side drawing overlay.
- **Speaker Note**:
  > "Slide 8 demonstrates our civil reconciliation layer. In real projects, structural drawings show the load-bearing skeleton, while architectural drawings show the finishes and partitions. We constructed a floor scope reconciliation matrix reconciling all 9 vertical levels. For instance, Sheet 104 does not print column heights; our reconciliation layer proved that the 3050mm floor-to-floor height derives from Architectural Section A-A. This proves the necessity of multi-document cross-referencing."

---

### Slide 9: Formula Setup and Engineered Refusal Logic
- **Slide Title**: Formula Setup & Engineered Refusal: Why Refusal is a Feature, Not a Failure
- **Key Message**: When required engineering inputs are missing from tender drawings, a trustworthy system must block takeoff rather than fabricate numbers.
- **Bullet Content**:
  - **Deterministic Formula Mapping**: 14 standard formulas defined conforming to IS 1200 (Concrete, Masonry, Shuttering, Finishes).
  - **The Input Dependency Register**: Every formula requires verified inputs ($L, B, H, \text{deductions}, \text{BBS}$).
  - **Interception Mechanism**: If any required input has status `BLOCKED` or `UNRESOLVED`, the execution engine flags `TAKEOFF_BLOCKED`.
  - **14 Blocked Work Packages**: Full takeoff is currently blocked across Piling, Pile Caps, Framing Concrete, Rebar, Masonry, and Plastering due to missing tender details.
- **Suggested Visual**: Logic flowchart: "Formula $\rightarrow$ Dependency Check $\rightarrow$ Missing Input Detected? $\rightarrow$ YES $\rightarrow$ Generate Blocked Reason Audit Entry & Halt Takeoff".
- **Speaker Note**:
  > "This is perhaps the most significant civil engineering takeaway of our work: Slide 9 shows our refusal engine. In machine learning, a system that halts is often called a failure. In civil engineering estimation, a system that produces a quantity when the drawing lacks data is negligent. We mapped 14 standard IS 1200 formulas. When the engine attempts to calculate pile concrete, it discovers that pile depth is omitted from Sheet 100. Instead of guessing 18 meters, it issues an auditable refusal log."

---

### Slide 10: Verified Proof-of-Method: Sample Quantity Takeoff
- **Slide Title**: Proof-of-Method: 15 Deterministic Micro-Calculations Verified
- **Key Message**: Demonstrating mathematical precision on elements where 100% of geometric parameters are directly observed from approved drawings.
- **Bullet Content**:
  - **Scope**: Executed strictly on isolated samples without multiplying across floors or flats.
  - **Sample Opening Areas (5 Items)**:
    - Toilet Door D1 ($0.800 \times 2.100\text{m} = 1.680\text{ m}^2$) | Bedroom Window W1 ($1.200 \times 1.200\text{m} = 1.440\text{ m}^2$)
    - Door-Window DW1 ($2.000 \times 2.100\text{m} = 4.200\text{ m}^2$) | Ventilator V1 ($0.515 \times 0.875\text{m} = 0.451\text{ m}^2$)
    - Service Door SD1 ($0.900 \times 2.100\text{m} = 1.890\text{ m}^2$)
  - **Sample Room Carpet Areas & Perimeters (10 Items)**:
    - Living/Dining ($5.520 \times 3.970\text{m} = 21.914\text{ m}^2$, $P = 18.980\text{m}$)
    - Master Bedroom ($3.845 \times 3.220\text{m} = 12.381\text{ m}^2$, $P = 14.130\text{m}$)
    - Kitchen ($2.580 \times 2.440\text{m} = 6.295\text{ m}^2$, $P = 10.040\text{m}$)
    - Attached Toilet ($2.700 \times 1.400\text{m} = 3.780\text{ m}^2$, $P = 8.200\text{m}$)
    - Living Balcony ($2.280 \times 1.365\text{m} = 3.112\text{ m}^2$, $P = 7.290\text{m}$)
  - **Evidence Provenance**: 100% traceable to verified inputs on Sheet `AR/TD/005` and formula-recomputed from controlled dimensions.
- **Suggested Visual**: Split screen showing Sheet `AR/TD/005` schedule table and the corresponding verified calculation rows in `sample_quantity_results_summary.csv`.
- **Speaker Note**:
  > "On Slide 10, we present our proof-of-method. Where drawings provide 100% complete and verified geometric evidence, the system calculates exact, auditable quantities. We calculated 5 door/window face areas, 5 room carpet areas, and 5 room perimeters directly from Sheet AR/TD/005, formula-recomputed from controlled dimensions. Every step exposes the formula, operand values, units, and source sheet. Notice that we deliberately did not multiply these by 24 flats—because typical flats have mirrorings and shaft offsets that require floor-by-floor verification."

---

### Slide 11: Explicit Limitations & Blocked Project Scopes
- **Slide Title**: Project Limitations & The 14 Blocked Scopes
- **Key Message**: Transparently exposing what cannot be calculated with current tender drawings to preserve academic and professional integrity.
- **Bullet Content**:
  - **Substructure Blocked**: Pile depth is only a DBR range ($15\text{–}20\text{m}$); Pile cap layout shows 54 visual entities vs 84 in the summary table.
  - **Reinforcement Blocked**: No official Bar Bending Schedule (BBS) exists for piles, caps, beams, or slabs; cut lengths cannot be fabricated.
  - **Masonry Blocked**: Centerline lengths are not segregated by floor; opening deduction locations are not mapped to specific wall panels.
  - **Commercial & Scheduling Blocked**: No contractor CPM schedule; single-tower cost cannot be derived without an official itemized BOQ.
- **Suggested Visual**: Red-flagged audit summary table highlighting the top 5 blockers and required engineering unblocking documents.
- **Speaker Note**:
  > "Respected committee, Slide 11 details our project limitations. We explicitly refuse to claim a full tower takeoff. Why? Because the structural tender drawings do not include an engineer-approved bar bending schedule. The pile layout plan exhibits an unresolved discrepancy: 54 pile cap entities are drawn on the plan, but the schedule lists 84 caps. Until the structural consultant issues a formal RFI clarification, calculating foundation concrete is unsafe."

---

### Slide 12: Next Steps & Academic Expansion
- **Slide Title**: Conclusion & Research Roadmap: Scaling to Multi-Project Benchmark
- **Key Message**: Having established an airtight methodology on one complex pilot, the framework is ready for MEP transcription and multi-building expansion.
- **Bullet Content**:
  - **Immediate Next Step (Priority I)**: Building Services (MEP) Controlled Transcription (18 Sheets: Plumbing, Firefighting, Electrical).
  - **Phase 2 Expansion**: Scale the methodology across 5–10 diverse CPWD/PSU tender packages (Healthcare, Educational, Industrial).
  - **Automated Tooling**: Wrap the controlled registers and refusal rules into an open-source Streamlit/FastAPI interactive audit tool.
  - **Final Value Proposition**: Converting unstructured construction drawings into deterministic, evidence-controlled, and audit-proof AI training data.
- **Suggested Visual**: Roadmap timeline chart showing Completed Stages (A–H), Immediate Next (MEP), and Future Expansion (5–10 Tenders & Web Demo).
- **Speaker Note**:
  > "To conclude: this major project demonstrates that the primary challenge in construction AI is not generating numbers—it is data provenance, document reconciliation, and hallucination control. We have built a verified pilot pipeline that handles complex tender drawings and enforces civil engineering principles. Our immediate next step is transcribing the 18 MEP sheets, followed by expanding this dataset across 10 PSU tender packages. Thank you, and we welcome your questions."


