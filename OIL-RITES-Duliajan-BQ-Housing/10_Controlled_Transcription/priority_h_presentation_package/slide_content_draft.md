# Slide Content Draft: Presentation-Ready Text

*Instructions for Presenter: This document contains clean, formatted text designed for direct copy-pasting into presentation software (Microsoft PowerPoint, Google Slides, or LaTeX Beamer). Keep slide bullet points concise and deliver the detailed context using the speaker explanation paragraphs.*

---

### Slide 1: Title & Project Scope
**Evidence-Controlled Construction Quantity Intelligence**  
*A Multi-Document Benchmark on the OIL India Duliajan BQ Housing Complex*

- **Department**: Civil Engineering — Major Project Review
- **Pilot Scope**: Typical Stilt+6 Residential Housing Tower ($483.60\text{ m}^2$ footprint, 24 units)
- **Tender Context**: RITES / Oil India Limited (Tender No. `RITES/NERPO/OIL/BQ-HOUSING/25`)
- **Core Focus**: Auditable multi-document data extraction with refusal guardrails against AI hallucination

**Speaker Explanation**:  
Respected members of the review panel, our major project addresses a critical bottleneck in digital construction: the lack of auditable, evidence-controlled data pipelines for automated quantity surveying. We have developed a rigorous framework that extracts geometric parameters from full tender drawing sets, cross-reconciles architectural and structural discrepancies, and refuses to calculate quantities when prerequisite drawing evidence is missing.

---

### Slide 2: The Core Problem in Construction Estimation AI
**The AI Estimation Trap: Data Poisoning and Hallucination**

- **Monolithic Black-Boxes**: Standard LLMs predict bulk quantities without tracing back to gridlines or schedules.
- **Prompt Poisoning**: Feeding tender BOQs directly into AI prompts leads to circular reasoning and data leakage.
- **Heuristic Reliance**: Common estimation tools use unverified rules-of-thumb (e.g., blanket 10%–23% opening deductions).
- **Civil Cost of Errors**: In civil contracts, a 5% ungrounded error in concrete or steel triggers contractual disputes and major cost overruns.

**Speaker Explanation**:  
Most existing AI tools in construction estimation attempt to leap directly from raw PDF drawings to final BOQ line items. In doing so, researchers frequently feed the BOQ into the model prompt, which masks the model's inability to interpret drawings. Furthermore, when drawings lack critical information like bar bending schedules or pile lengths, generic models hallucinate plausible-looking numbers. In civil engineering, an estimate without verifiable provenance is legally and commercially unusable.

---

### Slide 3: Why Multi-Document Matching is Essential
**The Multi-Document Reality of Civil Infrastructure**

- **Closed Ecosystem**: Real-world takeoff requires simultaneous correlation across architectural, structural, and technical documents.
- **Inter-Document Dependencies**: A single structural beam requires architectural floor heights, structural framing spans, rebar schedules, and DBR concrete grades.
- **Pitfalls of Random Scraping**: Training AI on disconnected drawings from random projects creates noise and invalidates geometric rules.
- **Pilot Approach**: Deep, closed-loop extraction from a complete, legally executed Indian public works tender package.

**Speaker Explanation**:  
A civil quantity surveyor never works from a single drawing in isolation. To measure a concrete beam or a brick wall, one must cross-reference architectural sections for clear heights, structural plans for spans, reinforcement details for rebar marks, and specifications for material grades. Scraping random floor plans from the internet breaks this geometric chain. Our research focuses on a single, comprehensive tender package to capture every inter-document dependency exactly as encountered in professional practice.

---

### Slide 4: Selected Pilot Project and Dataset Corpus
**Pilot Dataset: OIL India Workmen Housing Complex, Duliajan**

- **Tender Reference**: `RITES/NERPO/OIL/BQ-HOUSING/25` | Award Value: ₹128.14 Cr (Dec 2025)
- **Geotechnical Context**: Seismic Zone V, Upper Assam alluvium, heavy ductile detailing requirements.
- **Benchmark Unit**: Typical Stilt+6 Residential Tower ($30.08\text{ m} \times 16.08\text{ m}$, 24 flats, $24.0\text{ m}$ height).
- **Corpus Analyzed**: 55 drawing sheets (26 Architectural, 23 Structural, 18 MEP) plus DBR, Tender Notices, and CPWD Specifications.

**Speaker Explanation**:  
Our pilot benchmark is a real-world, high-seismic housing project in Assam, executed under RITES supervision for Oil India Limited. We isolated one typical Stilt+6 BQ residential block as our standardized benchmarking unit. This structure possesses a high-density framing system: 207 cast-in-situ bored piles, 49 vertical columns and shear walls, 34 framing beams per floor, and 24 identical residential units across 6 typical suspended storeys.

---

### Slide 5: Ontological Separation of Inputs and Validation Targets
**Preventing Data Leakage: The Strict Ontological Firewall**

- **Predictive AI Input Domain**: Architectural Drawings (`AR`), Structural Drawings (`STR`), DBR, and CPWD Specifications.
- **Blind Ground-Truth Domain**: Official Tender BOQ, priced Schedule of Rates (SOR), and Contractor CPM Schedules.
- **Zero-Leakage Guarantee**: BOQ item descriptions, rates, and totals are strictly prohibited from extraction prompts.
- **Honest Academic Reporting**: Because RITES issued an aggregate multi-building BOQ without an official single-tower breakdown, cost accuracy is explicitly marked `NOT_CALCULATED`.

**Speaker Explanation**:  
To maintain scientific validity, we enforce a strict ontological separation between what the AI is allowed to see and what is used to evaluate it. The predictive inputs are restricted entirely to design drawings and specifications. Tender BOQs and contractor schedules are placed behind a blind validation firewall. Furthermore, we refuse to present an artificial cost accuracy percentage because doing so without an official, single-tower itemized BOQ would constitute academic dishonesty.

---

### Slide 6: Evidence-Control Methodology & Provenance Hierarchy
**The 9-Tier Evidence Provenance Hierarchy**

- **Tier 1 (`DIRECT_SHEET_OBSERVATION`)**: Directly printed drawing text, callouts, and schedule entries.
- **Tier 2 (`DERIVED_FROM_ARCHITECTURAL_SECTION`)**: Vertical levels and storey heights verified from building sections.
- **Tier 3 (`DERIVED_BY_BASIC_GEOMETRY`)**: Deterministic calculations ($L \times B$, perimeters) from observed dimensions.
- **Tier 4 & 5 (`IS_CODE_DERIVED` / `ESTIMATED`)**: Code formulas ($45.3d$ rebar laps, standard covers) and engineering assumptions.
- **Strict Guardrail**: Zero assumptions are permitted to hold a `HIGH_CONFIDENCE` tag; synthetic rules-of-thumb (23%/10% opening deductions) are completely purged.

**Speaker Explanation**:  
We have established a 9-tier provenance classification system. Every parameter in our registers carries an immutable evidence tag. If a column dimension is printed on Sheet 103, it is Tier 1 direct observation. If an area is multiplied from room bounds, it is Tier 3 derived geometry. Most importantly, we instituted two critical rules: first, no assumption may ever claim 'High Confidence'; second, rule-of-thumb shortcuts—such as deducting a flat 23% for openings—are strictly banned in favor of exact door and window schedule geometry.

---

### Slide 7: Multi-Stage System Architecture
**11-Stage Modular Architecture: From Ingestion to Refusal**

- **Phases 0–2 (Ingestion & Legibility)**: Document indexing, metadata registration, and drawing sheet inventorying.
- **Phases 3–5 (Controlled Transcription)**: Substructure (A), Structural Frame (B), and Architectural Openings/Rooms (C).
- **Phase 6 (Civil Reconciliation)**: Cross-register alignment resolving structural vs architectural boundary clashes.
- **Phase 7–8 (Formulas & Refusal)**: IS 1200 formula dependency mapping and automated guardrail execution.
- **Phases 9–10 (Evaluation & Expansion)**: Blind ground-truth benchmarking and multi-project dataset scaling.

**Speaker Explanation**:  
Our system architecture avoids black-box pipelines by structuring quantity takeoff into 11 discrete, verifiable stages. In Phases 3 through 5, foundation, structural frame, and architectural elements are transcribed into structured registers. Phase 6 reconciles inter-trade discrepancies, such as verifying column heights against architectural sections. Phase 7 maps IS 1200 formulas to these parameters, and Phase 8 intercepts calculations whenever an input is missing.

---

### Slide 8: Cross-Register Civil Reconciliation
**Resolving Real-World Inter-Trade Discrepancies**

- **Vertical Level Reconciliation**: Reconciles Ground ($+0.00\text{m}$), Plinth ($+0.30\text{m}$), 1st–6th Floors ($+3.00\text{m}$ to $+21.30\text{m}$), and Mumty ($+24.00\text{m}$).
- **Structural vs Architectural Alignment**:
  - Structural Sheet 104 provides 49 vertical members (16 Columns, 33 Shear Walls); architectural plans show simplified partition junctions.
  - Floor-to-floor height ($3.05\text{m}$) resolved from Architectural Section A-A (`AR/012`), not structural layouts.
- **Masonry Boundary Matrix**: Requires deducting framing member widths ($300\text{mm}$/ $400\text{mm}$) and beam soffits from gross room bounds.

**Speaker Explanation**:  
In real-world civil engineering, architectural and structural drawings frequently exhibit drafting misalignments. In our reconciliation layer, we verified the vertical datum across all 9 levels. For example, structural sheet 104 schedules column reinforcement but omits vertical storey heights; our reconciliation layer traced and verified the 3050mm floor height directly from Architectural Section A-A. This proves why isolated drawing extraction fails without inter-trade reconciliation.

---

### Slide 9: Formula Setup and The Refusal Engine
**Automated Guardrails: Why Refusal is an Engineering Feature**

- **Deterministic Formula Mapping**: 14 standard measurement formulas established in strict compliance with IS 1200.
- **Input Dependency Tracking**: Formulas cannot execute unless every operand ($L, B, H, \text{deductions}$) is verified.
- **Automated Refusal Interception**: If an input is unverified or conflicting, the system halts execution and issues an auditable blocker log.
- **Current Operational Status**: Full takeoff is currently blocked across 14 civil trades (Piling, Caps, Framing, Rebar, Masonry, Plaster) due to missing tender schedules.

**Speaker Explanation**:  
In classical software, halting is considered an error. In construction quantity takeoff, producing an estimate when input drawings lack essential data is professional negligence. We mapped 14 standardized IS 1200 formulas into a dependency engine. When the engine attempts to evaluate pile concrete, it identifies that pile lengths are omitted from the drawing. Instead of inventing a number, it halts and logs an explicit refusal record. Refusal is an engineering safety feature.

---

### Slide 10: Verified Proof-of-Method: Sample Calculations
**Auditable Micro-Calculations: 15 Verified Sample Quantities**

- **Strict Scope**: Executed on isolated samples with verified, unambiguous drawing callouts.
- **Opening Face Areas (5 Samples)**:
  - Toilet Door D1: $0.800\text{m} \times 2.100\text{m} = 1.680\text{ m}^2$ | Bedroom Window W1: $1.200\text{m} \times 1.200\text{m} = 1.440\text{ m}^2$
  - Door-Window DW1: $2.000\text{m} \times 2.100\text{m} = 4.200\text{ m}^2$ | Ventilator V1: $0.515\text{m} \times 0.875\text{m} = 0.451\text{ m}^2$
  - Service Door SD1: $0.900\text{m} \times 2.100\text{m} = 1.890\text{ m}^2$
- **Room Carpet Areas & Perimeters (10 Samples)**:
  - Living/Dining: $5.520\text{m} \times 3.970\text{m} = 21.914\text{ m}^2$ ($P = 18.980\text{m}$)
  - Master Bedroom: $3.845\text{m} \times 3.220\text{m} = 12.381\text{ m}^2$ ($P = 14.130\text{m}$)
  - Kitchen: $2.580\text{m} \times 2.440\text{m} = 6.295\text{ m}^2$ ($P = 10.040\text{m}$)
  - Attached Toilet: $2.700\text{m} \times 1.400\text{m} = 3.780\text{ m}^2$ ($P = 8.200\text{m}$)
  - Living Balcony: $2.280\text{m} \times 1.365\text{m} = 3.112\text{ m}^2$ ($P = 7.290\text{m}$)
- **Traceability**: Formula-recomputed from controlled dimensions on Sheet `AR/TD/005`, internally consistent with Priority F sample register.

**Speaker Explanation**:  
On this slide, we present our proof-of-method. Where drawings provide complete and verified dimensions, the system executes deterministic geometry that is formula-recomputed from controlled dimensions. We calculated 5 door and window face areas, 5 room carpet areas, and 5 room perimeters directly from Sheet AR/TD/005. Each result exposes the underlying formula, input dimensions, and drawing sheet. We deliberately avoided multiplying these across 24 flats, because typical flats have shaft and plumbing variations that require floor-wise verification.

---

### Slide 11: Transparent Project Limitations
**What is Blocked & What Evidence is Needed to Unblock**

- **Foundation Substructure**: Blocked due to pile length omission (DBR range $15\text{–}20\text{m}$ only) and 54 visual caps vs 84 scheduled caps conflict.
- **Reinforcement (All Trades)**: Blocked due to the total absence of an approved Bar Bending Schedule (BBS) for piles, caps, beams, and slabs.
- **Masonry & Finishes**: Blocked due to lack of floor-by-floor wall centerline lengths and opening-to-wall mapping.
- **Tender Commercials**: Single-tower cost and duration are `NOT_CALCULATED` due to the lack of an official single-tower BOQ and contractor schedule.

**Speaker Explanation**:  
We maintain complete transparency regarding our limitations. Full building takeoff cannot be performed on tender drawings alone. Tender drawings are schematic design representations; they are not construction shop drawings. Without an engineer-issued Bar Bending Schedule, any steel takeoff is an educated guess. Without an RFI resolving whether there are 54 or 84 pile caps, foundation concrete cannot be locked. Acknowledging these gaps is what makes our framework robust and trustworthy.

---

### Slide 12: Future Roadmap & Major Project Conclusion
**Conclusions, Academic Roadmap, and Immediate Next Steps**

- **Immediate Next Step (Priority I)**: Building Services (MEP) Controlled Transcription (18 Sheets: Plumbing, Drainage, Fire, Electrical).
- **Dataset Scaling**: Expand the evidence-controlled methodology across 5 to 10 diverse public sector (CPWD/PSU) tender packages.
- **Interactive Tooling**: Deploy a lightweight, open-source Streamlit/FastAPI interface showcasing the refusal guardrail and provenance tracker.
- **Final Takeaway**: Reliable construction intelligence requires data provenance, document reconciliation, and hallucination control before generative AI can be trusted.

**Speaker Explanation**:  
In conclusion, this project demonstrates that automated quantity surveying is not an LLM prompting problem—it is an information architecture and civil engineering problem. We have built an auditable, evidence-controlled pipeline that protects against hallucination, enforces IS 1200 measurement standards, and provides a benchmark dataset for construction intelligence. Our immediate next step is transcribing the 18 MEP sheets, followed by multi-project scaling. Thank you, and we welcome the panel's feedback.


