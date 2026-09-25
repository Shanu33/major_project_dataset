# Major Project Review Slide Deck: Presentation Notes & Visual Exports

**Project**: Evidence-Controlled Civil Quantity Intelligence (OIL India / RITES Duliajan BQ Housing)  
**Slide Deck File**: `10_Controlled_Transcription/priority_i_slide_deck/major_project_review_deck.pptx`  
**Total Slides**: 12 Widescreen (16:9) Professional Academic Slides  
**Primary Discipline**: Department of Civil Engineering — Major Project Evaluation  

---

### Slide 1: Title and Project Objective
- **Slide Title**: Evidence-Controlled Civil Quantity Intelligence: A Multi-Document Benchmark & Architecture on the OIL India Duliajan BQ Housing Complex
- **Slide Category**: Department of Civil Engineering | Major Project Review
- **Visual Description**: Professional academic title slide featuring an engineered dual-tone navy top bar, structured metadata card, and bulleted scope breakdown summarizing tender identity, benchmark unit, and research objective.
- **Speaker Notes**:
  > "Respected members of the review panel, our major project addresses a fundamental bottleneck in digital construction: the lack of auditable, evidence-controlled data pipelines for quantity estimation. Instead of treating quantity surveying as an ungrounded generative AI task, we developed a rigorous multi-document architecture for the OIL India Duliajan BQ Housing Complex. Our system transcribes architectural and structural drawings, reconciles inter-trade discrepancies, and enforces an engineered refusal guardrail that halts takeoff when drawings lack prerequisite engineering details."

---

### Slide 2: Problem in Construction Quantity Estimation
- **Slide Title**: The Core Problem: AI Hallucination, Leakage, and Lost Provenance
- **Slide Category**: Problem Statement & Literature Gap
- **Visual Description**: Two side-by-side comparison cards in slate gray framing: Left Card highlights "Current Limitations in AI Estimation" (black-box generation and prompt leakage); Right Card highlights "Contractual & Civil Engineering Risks" (unverified heuristics and dispute risks).
- **Speaker Notes**:
  > "Most current AI research in construction estimation suffers from prompt poisoning. Researchers frequently provide both drawings and the final BOQ to the model, claiming high accuracy. In reality, the model simply memorized or copied the BOQ text. Furthermore, when tender drawings omit bar bending schedules or pile depths, generic models hallucinate numbers instead of admitting data is missing. Under IS 1200 and standard Indian public works contracts, an estimate without verifiable provenance is legally and commercially unusable."

---

### Slide 3: Why Project-Level Document Matching Matters
- **Slide Title**: Why Project-Level Document Matching Matters
- **Slide Category**: Methodological Justification
- **Visual Description**: Two structured analytical cards: Left Card details the "Inter-Document Interdependence" across architectural sections, structural framing, and specifications; Right Card details "Authentic Tender Packaging" contrasting closed-loop tender sets with random internet scraping.
- **Speaker Notes**:
  > "In civil engineering practice, an architectural plan only shows walls and room uses; the structural drawing shows column sizes and reinforcement, and the specifications define concrete mixes. If an AI system is trained on random floor plans scraped from the internet, it cannot learn real-world civil engineering. Our pilot captures a complete, closed-loop tender package from RITES and Oil India Limited, preserving all inter-document dependencies exactly as encountered on a live construction project."

---

### Slide 4: Selected Pilot Project and Dataset Corpus
- **Slide Title**: Pilot Benchmark: OIL India Workmen Housing Complex, Duliajan
- **Slide Category**: Pilot Project Baseline
- **Visual Description**: Two informational panels: Left Panel details "Contractual & Structural Context" (RITES tender ID, ₹128.14 Cr contract, Seismic Zone V); Right Panel details "Physical Scope & Drawing Corpus" (Stilt+6 tower, 483.60 m² plinth, 55 sheets across Architecture, Structure, and MEP).
- **Speaker Notes**:
  > "Our benchmark project is an authentic, high-seismic public sector housing development in Assam. We isolated one typical Stilt+6 BQ residential tower as our benchmark unit. It features 207 bored cast-in-situ piles, 49 vertical load-bearing columns and shear walls, 34 framing beams per floor, and 24 identical flats across 6 upper storeys. The drawing corpus comprises 55 audited tender drawing sheets across architecture, structure, and MEP."

---

### Slide 5: AI Input vs Ground-Truth Concept
- **Slide Title**: Ontological Separation: Predictive Inputs vs Ground-Truth Targets
- **Slide Category**: System Ontology & Anti-Contamination
- **Visual Description**: An ontological boundary diagram with two high-contrast panels: Left Panel in soft indigo border encapsulates "Predictive AI Inputs (Visible: Drawings, DBR, Specs)"; Right Panel in soft red border encapsulates "Blind Ground-Truth Targets (Firewalled: BOQ, SOR, CPM Schedule)". A bottom banner emphasizes the zero-leakage principle and justifies `Cost accuracy: NOT_CALCULATED`.
- **Speaker Notes**:
  > "Slide 5 illustrates our core methodological safeguard: the ontological firewall. We strictly separate predictive AI inputs from blind evaluation targets. The AI model only receives design drawings and specifications. The tender BOQ and contract costs remain strictly behind a blind evaluation firewall. Furthermore, because RITES issued an aggregate 8-tower BOQ without an official single-tower breakdown, we maintain cost accuracy as NOT_CALCULATED to preserve academic integrity."

---

### Slide 6: Evidence-Control Methodology
- **Slide Title**: Evidence-Control Methodology: The 9-Tier Provenance Hierarchy
- **Slide Category**: Provenance & Governance Framework
- **Visual Description**: Dual-column governance cards: Left Card presents the "9-Tier Provenance Ladder" (Tier 1 Direct Sheet Observation down to Tier 5 Standardized Assumptions) and highlights the rule banning `HIGH_CONFIDENCE` on assumptions; Right Card outlines "Governance & Heuristic Purging" detailing the removal of synthetic 23%/10% deduction rules.
- **Speaker Notes**:
  > "In quantity surveying, not all numbers have the same authority. We established a 9-tier provenance hierarchy. When an engineer reads a column schedule, that is direct sheet observation. When room bounds are multiplied, that is derived geometry. Crucially, we enforced a strict rule: no assumption may be tagged as High Confidence. We also completely eliminated legacy ungrounded heuristics—such as blanket 23% and 10% wall deductions—insisting that every deduction map to scheduled opening marks."

---

### Slide 7: System Architecture Pipeline
- **Slide Title**: System Architecture: 11-Stage Pipeline from Ingestion to Refusal
- **Slide Category**: Software & Engineering Architecture
- **Visual Description**: Horizontal 5-stage process pipeline containing rounded modular containers: (1) Phases 0-2: Ingestion & Audit; (2) Phases 3-5: Controlled Transcription; (3) Phase 6: Civil Reconciliation; (4) Phase 7: Formula Mapping; (5) Phase 8: Refusal Guardrail. An overarching bottom summary card explains the modular decoupling of transcription from formula evaluation.
- **Speaker Notes**:
  > "Here is our 11-stage system architecture. Rather than an ungrounded black-box script, we structure quantity takeoff into discrete, verifiable phases. Phases 3 through 5 extract Foundation, Structural Frame, and Architecture into separate registers. Phase 6 performs cross-register reconciliation. Phase 7 maps IS 1200 measurement rules to input dependencies. Phase 8 executes sample calculations while intercepting and blocking unsafe takeoff."

---

### Slide 8: Controlled Transcription and Reconciliation Workflow
- **Slide Title**: Controlled Transcription & Civil Cross-Register Reconciliation
- **Slide Category**: Multi-Discipline Engineering Workflow
- **Visual Description**: A 3-column comparative workflow schematic displaying (1) Architectural Registers (`controlled_opening_register.csv`, `controlled_room_register.csv`, etc.); (2) Structural Registers (`controlled_foundation_register.csv`, `controlled_column_wall_register.csv`, etc.); and (3) Civil Reconciliation Layer (`floor_scope_reconciliation.csv`, vertical datum resolution, and conflict logs).
- **Speaker Notes**:
  > "Slide 8 shows our reconciliation layer in action. In real projects, architectural and structural drawings frequently exhibit drafting misalignments. We constructed a floor scope reconciliation matrix reconciling all 9 building levels. For example, Sheet 104 does not print column heights; our reconciliation layer proved that the 3050mm floor height derives from Architectural Section A-A. This proves why isolated drawing extraction fails without cross-register reconciliation."

---

### Slide 9: Formula Setup and Blocked Execution Logic
- **Slide Title**: Formula Setup & Engineered Refusal: Why Halting is an Engineering Feature
- **Slide Category**: Dependency Engine & Guardrails
- **Visual Description**: Top section features a 4-step decision flowchart (Step 1: Formula Definition $\rightarrow$ Step 2: Dependency Check $\rightarrow$ Step 3: Guardrail Interception $\rightarrow$ Step 4: Refusal Log). Bottom section features dual analytical cards detailing IS 1200 formula compliance and the engineering necessity of refusing ungrounded estimates.
- **Speaker Notes**:
  > "Slide 9 highlights our refusal engine. In computer science, when a program halts, it is often viewed as an error. But in civil engineering quantity surveying, halting when drawings lack critical data is the hallmark of professional competence. We mapped 14 standardized IS 1200 formulas into a dependency engine. When the engine attempts to evaluate pile concrete, it discovers that pile lengths are omitted from Sheet 100. Instead of guessing 18 meters, it halts and logs an explicit refusal record."

---

### Slide 10: Traceable Sample Quantity Results
- **Slide Title**: Traceable Sample Quantity Results: Proof-of-Method
- **Slide Category**: Mathematical Verification
- **Visual Description**: A structured engineering data table featuring 6 verified rows:
  - D1 (Toilet Door: $0.800\text{m} \times 2.100\text{m} = 1.680\text{ m}^2$)
  - W1 (Bedroom Window: $1.200\text{m} \times 1.200\text{m} = 1.440\text{ m}^2$)
  - DW1 (Door-Window Combo: $2.000\text{m} \times 2.100\text{m} = 4.200\text{ m}^2$)
  - Living/Dining (Carpet Area: $5.520\text{m} \times 3.970\text{m} = 21.914\text{ m}^2$)
  - Master Bedroom (Carpet Area: $3.845\text{m} \times 3.220\text{m} = 12.381\text{ m}^2$)
  - Kitchen (Carpet Area: $2.580\text{m} \times 2.440\text{m} = 6.295\text{ m}^2$)  
  Accompanied by a bottom boundary certification confirming single-element scope, zero multiplier scaling, and blocked bulk takeoff.
- **Speaker Notes**:
  > "On Slide 10, we present our traceable sample quantity results. Where drawings provide verified geometric dimensions, our formula engine executes deterministic geometry with complete fidelity. For Toilet Door D1, 0.800m by 2.100m gives exactly 1.680 square meters. For Window W1, 1.200m by 1.200m yields 1.440 square meters. For the Living/Dining room, 5.520m by 3.970m yields 21.914 square meters. Notice that we deliberately did not multiply these by 24 flats—because typical flats have shaft and plumbing variations that require floor-wise verification."

---

### Slide 11: Limitations and Blocked Scopes
- **Slide Title**: Project Limitations & Explicitly Blocked Scopes
- **Slide Category**: Risk Management & Scope Boundaries
- **Visual Description**: A red-accented audit table detailing 5 major blocked packages (Piling Concrete, Pile Caps, Reinforcement Steel, Brick Masonry, Cost & Duration) mapped against Specific Missing Inputs, Estimation Risks, and Required Unblocking Actions. Bottom panel reinforces the academic integrity pledge.
- **Speaker Notes**:
  > "Slide 11 details our project limitations and the 14 blocked scopes. We maintain complete transparency regarding what cannot be calculated with current tender drawings. Full building takeoff cannot be performed on tender drawings alone. Tender drawings are schematic representations; they are not construction shop drawings. Without an engineer-approved Bar Bending Schedule, steel reinforcement cannot be computed deterministically. Acknowledging these gaps is what makes our framework robust and trustworthy."

---

### Slide 12: Next Steps and Future Scope
- **Slide Title**: Future Roadmap: Scaling from Pilot to Multi-Project Benchmark
- **Slide Category**: Research Expansion & Conclusions
- **Visual Description**: Dual strategic panels: Left Panel details "Immediate & Mid-Term Milestones" (Priority J Building Services MEP transcription, scaling across 5-10 PSU tender sets); Right Panel details "Tooling & Research Vision" (interactive audit interface and the defining value proposition).
- **Speaker Notes**:
  > "To conclude: this major project demonstrates that the primary challenge in construction AI is not generating numbers—it is data provenance, document reconciliation, and hallucination control. We have built a verified pilot pipeline that handles complex tender drawings, enforces IS 1200 measurement principles, and blocks unsafe takeoff. Our immediate next step is transcribing the 18 MEP sheets, followed by multi-project scaling. Thank you, and we welcome your questions."


