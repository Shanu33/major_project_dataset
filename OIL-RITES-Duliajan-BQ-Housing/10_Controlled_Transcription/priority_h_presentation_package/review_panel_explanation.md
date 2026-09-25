# A Practical Explanation for the Civil Engineering Review Panel

**To**: The Respected Members of the Major Project Evaluation Committee  
**From**: Major Project Working Group (Civil Engineering)  
**Subject**: Methodological Framework and Technical Significance of our Research

---

### Dear Committee Members,

When applying artificial intelligence to civil engineering, researchers frequently run into a common failure mode: they treat civil engineering documents like generic text or pictures. They take an architectural drawing, feed it into a Large Language Model alongside a tender Bill of Quantities (BOQ), and ask the model to generate quantities.

As civil engineers, we know this is fundamentally flawed for three practical reasons:
1. **Quantity estimation is deterministic geometry, not probabilistic text prediction.** A building volume does not depend on linguistic likelihood; it depends strictly on $L \times B \times H$ minus physical voids as codified under **IS 1200**.
2. **Real construction projects are multi-document ecosystems.** An estimator cannot measure a structural element from an architectural plan alone. One must reconcile the architectural layout, structural framing plans, rebar schedules, and geotechnical soil reports belonging to the *exact same building*.
3. **Missing data is a real-world reality, not an edge case.** Tender drawings are frequently issued with missing details—such as omitted pile termination depths, conflicting pile cap groupings, or the total absence of a Bar Bending Schedule (BBS). If an automated system guesses these missing values, it introduces catastrophic financial and contractual liabilities.

Our major project was designed from the ground up to solve these fundamental engineering challenges. Below is a concise walkthrough of how we approached this work.

---

### 1. Why We Selected One Complete Tender Package First
Rather than assembling a superficial dataset of 50 random floor plans scraped from internet architectural blogs, we selected **one complete, legally executed Indian public works tender package**:
- **Project**: OIL India Workmen Housing Complex, Duliajan, Assam.
- **Client & PMC**: Oil India Limited and RITES Limited (Tender No. `RITES/NERPO/OIL/BQ-HOUSING/25`, awarded December 2025).
- **Benchmark Unit**: One typical Stilt+6 BQ Residential Housing Tower ($483.60\text{ m}^2$ footprint, 24 dwelling units).

By focusing deeply on this complete tender, we obtained the entire closed-loop document universe: 26 Architectural drawings, 23 Structural drawings, 18 Building Services drawings, the structural Design Basis Report (DBR), Geotechnical Soil Investigation, CPWD Specifications 2019, and official tender award records. This allowed us to model authentic inter-document cross-referencing for the first time.

---

### 2. We Treated Drawings & Specifications Strictly as Inputs
To prevent data contamination, we established a strict ontological boundary:
- **Predictive Inputs**: Architectural drawings (`AR`), Structural drawings (`STR`), Services drawings (`MEP`), DBR notes, and CPWD technical specifications.
- **Blind Ground Truth**: The official tender BOQ, Schedule of Rates (SOR), and contractor CPM schedules.

Under our methodology, the AI is **never allowed to see the BOQ during extraction**. Supplying the BOQ into the extraction prompt is data leakage—it reduces the task to simple optical character recognition (OCR) and gives a false illusion of intelligence. The system must derive its understanding purely from engineering drawings.

---

### 3. We Created Controlled, Relational Registers
Instead of dumping drawing data into an unreadable vector database, we converted the drawing information into structured, human-auditable civil engineering registers:
- **Foundation Register**: Capturing 207 bored cast-in-situ piles and 84 scheduled pile caps.
- **Structural Frame Register**: Capturing 49 vertical load-bearing elements (16 columns, 33 shear walls) and 34 framing beams per floor.
- **Architectural & Finish Registers**: Capturing 10 scheduled door/window types, 5 room archetypes, and floor finishes across all 9 vertical levels.

Every entry in these registers records its exact drawing sheet number, revision date, gridline coordinates, and millimeter dimensions.

---

### 4. We Tagged Evidence Quality with a 9-Tier Provenance Hierarchy
In engineering practice, not all numbers carry the same weight. We established an explicit 9-tier provenance hierarchy:
- A column width printed on a drawing is **Direct Evidence** (`DIRECT_SHEET_OBSERVATION`).
- A room carpet area computed from verified bounds is **Derived Geometry** (`DERIVED_BY_BASIC_GEOMETRY`).
- A rebar lap length calculated using $(0.87 \cdot f_y \cdot d) / (4 \cdot \tau_{bd}) = 45.3d$ is **Code-Derived** (`IS_CODE_DERIVED`).
- An assumed pile length is an **Engineering Assumption** (`ESTIMATED`).

**Our Core Rule**: Zero assumptions are ever permitted to claim a `HIGH_CONFIDENCE` tag. Furthermore, we eradicated ungrounded industry rules-of-thumb—such as deducting a blanket 23% for windows and 10% for doors—demanding instead that deductions be calculated from scheduled opening marks.

---

### 5. We Defined Standardized IS 1200 Formulas
We mapped 14 standardized measurement formulas strictly conforming to Bureau of Indian Standards **IS 1200**:
- Concrete measurement by net volume ($L \times B \times H$) excluding rebar volume.
- Brickwork masonry by net volume deducting openings greater than $0.1\text{ m}^2$.
- Internal plastering by net wall surface area with one-face opening deductions.
- Shuttering by contact area between wet concrete and formwork.

Crucially, we wrapped each formula in an **input dependency graph**: a formula cannot evaluate until every required operand has been verified and registered.

---

### 6. We Calculated Only Safe, Verified Sample Quantities (Proof-of-Method)
To prove that our formula engine functions with exact mathematical precision, we executed Priority F: Controlled Sample Quantity Execution.
We calculated **15 isolated micro-sample quantities**:
- 5 door and window face areas (e.g., Toilet Door D1 = $0.800\text{m} \times 2.100\text{m} = 1.680\text{ m}^2$, Bedroom Window W1 = $1.200\text{m} \times 1.200\text{m} = 1.440\text{ m}^2$, Door-Window DW1 = $2.000\text{m} \times 2.100\text{m} = 4.200\text{ m}^2$).
- 5 room carpet areas (e.g., Living/Dining = $5.520\text{m} \times 3.970\text{m} = 21.914\text{ m}^2$, Master Bedroom = $3.845\text{m} \times 3.220\text{m} = 12.381\text{ m}^2$).
- 5 room internal perimeters for skirting and wall plastering baseline (e.g., Living/Dining = $18.980\text{m}$, Master Bedroom = $14.130\text{m}$).

These calculations are formula-recomputed from controlled dimensions and internally consistent with the Priority F sample register. We deliberately refrained from multiplying these by 24 flats or 8 towers to preserve geometric truth.

---

### 7. We Blocked Unsafe Full Takeoff: Refusal is an Engineering Feature
When evaluating full tower quantities, our automated guardrail detected that critical engineering schedules were missing from the tender package:
1. **Pile Depth**: The pile layout drawing omits pile cut-off termination depths (stating only a broad $15\text{–}20\text{m}$ range in the DBR narrative).
2. **Pile Cap Ambiguity**: The foundation plan shows 54 visual cap entities, while the schedule lists 84 caps.
3. **Rebar BBS**: The structural consultant did not issue a Bar Bending Schedule; steel cut lengths and lap staggering cannot be computed deterministically.

Instead of guessing or hallucinating numbers, **our system actively refused takeoff and logged an auditable Request for Information (RFI) report across 14 civil work packages**.

In computer science, a system that halts might be seen as an exception. In civil engineering, **refusing to guess when drawings lack data is the hallmark of competent, ethical engineering**.

---

### 8. The Foundation for a Larger Construction-Intelligence Dataset
Respected panel, our work proves that before generative AI can be deployed on infrastructure projects, the industry must have **structured, evidence-controlled, multi-document datasets**. 

We have successfully created the data architecture, transcription protocols, reconciliation matrices, and refusal guardrails on this complex pilot. This framework is now ready to:
1. Complete Building Services (MEP) transcription across 18 sheets.
2. Ingest 5 to 10 additional public works tender packages (CPWD, NBCC, RITES).
3. Provide the civil engineering community with an open, audit-proof benchmark for digital quantity surveying.

Thank you for your guidance and evaluation of our work.


