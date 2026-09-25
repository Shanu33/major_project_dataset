# Evidence Control Methodology: Ontological Provenance and Guardrails

**Platform**: Evidence-Grounded Construction Intelligence  
**Target Repository**: `10_Controlled_Transcription/priority_g_project_summary/`  
**Standard Compliance**: IS 1200 (Methods of Measurement of Building and Civil Engineering Works)  

---

## 1. Epistemic Provenance Hierarchy

In standard engineering practice, data integrity relies on knowing exactly **where a number came from** and **how much interpretation was required** to obtain it. This platform defines nine formal provenance and lifecycle states:

### 1. `DIRECT_SHEET_OBSERVATION`
- **Definition**: A dimension, element mark, material specification, or schedule entry that is visibly and unambiguously printed on an approved drawing sheet or document table.
- **Examples**: Column mark `C1`, section size $1200 \times 350\text{ mm}$, beam mark `PB1`, opening dimension $1200 \times 1200\text{ mm}$, clear room span $3970 \times 5520\text{ mm}$, finish spec `FIN-01`.
- **Allowed Use**: Full factual baseline; eligible for deterministic reference.

### 2. `DERIVED_BASIC_GEOMETRY`
- **Definition**: A mathematical parameter calculated purely from direct sheet observations using standard 2D Euclidean formulas ($W \times H$, $L \times W$, $2(L+W)$) without introducing engineering assumptions or empirical factors.
- **Examples**: Window `W1` opening area ($1.20 \times 1.20 = 1.440\text{ m}^2$); Living Room floor area ($5.52 \times 3.97 = 21.914\text{ m}^2$).
- **Allowed Use**: Isolated single-unit calculations; auditable proof-of-method samples.

### 3. `ARCHITECTURAL_SECTION_DERIVED`
- **Definition**: A vertical dimension or storey height that is extracted from architectural sections or exterior elevations because it is absent from structural framing drawings.
- **Examples**: Column/wall storey height ($3050\text{ mm}$ from Section A-A `AR/TD/012`, because Sheet 104 does not print vertical column elevations).
- **Allowed Use**: Spatial coordination and preliminary ceiling clearance checks.
- **Restriction**: Blocked from generating structural concrete volumes or rebar lap splice cut-lengths until structurally confirmed.

### 4. `ASSUMPTION_REQUIRED`
- **Definition**: An essential engineering parameter that is not printed on any approved drawing sheet and must be inferred from technical standards, design briefs, or standard practice.
- **Examples**: Average pile depth ($18.0\text{ m}$ derived from DBR range $15\text{–}20\text{ m}$); pile cap average depth ($1.0\text{ m}$).
- **Restriction**: Confidence must be capped at `ESTIMATED` or `MEDIUM`. **Zero active `HIGH_CONFIDENCE` labels are permitted.**

### 5. `MISSING`
- **Definition**: A required input parameter, schedule, or sheet that is completely absent from the drawing repository.
- **Examples**: Bar Bending Schedule (BBS); pile borehole depth chart; OHT wall thickness schedule; opening counts on Sheet 005.

### 6. `BLOCKED`
- **Definition**: An engineering work package, trade takeoff, or calculation step that cannot be executed without risking unconstrained hallucination or compounding error due to missing inputs.
- **Examples**: Full masonry takeoff (blocked by unsegregated wall centerlines); full rebar takeoff (blocked by missing BBS).

### 7. `FORMULA_DEFINED_INPUTS_BLOCKED`
- **Definition**: A formula whose mathematical structure is fully defined and linked to source registers, but whose execution is deliberately disabled because prerequisite inputs remain unverified.
- **Examples**: All 18 formula groups in Priority E.

### 8. `SAMPLE_EXECUTED_TRACEABLE`
- **Definition**: An isolated micro-sample calculation executed on verified direct inputs, accompanied by a complete row-by-row audit trail.
- **Examples**: The 18 sample calculations in Priority F.

### 9. `BLOCKED_FULL_TAKEOFF`
- **Definition**: A formal guardrail state asserting that while individual sample components may be understood, scaling to multi-unit, floor-level, or tower-level takeoff is strictly prohibited.

---

## 2. Why Legacy Assumptions Were Completely Excluded

Earlier iterations of the model relied on common estimating heuristics that were found to violate audit standards:

### A. The 23% External and 10% Internal Masonry Deduction Heuristics
- **Legacy Practice**: Estimators sometimes assume opening deductions equal approximately 23% of gross external wall area and 10% of internal partition area.
- **Why Excluded**: Under IS 1200 (Part III), masonry must be measured by calculating gross wall area minus the exact measured deduction of every individual opening exceeding $0.1\text{ m}^2$. Using arbitrary percentage deductions creates ungrounded estimates (up to 15–20% error) and conceals structural penetrations.
- **Enforced Rule**: All percentage deductions were stripped from the dataset. In `controlled_masonry_deduction_register.csv`, deduction area is recorded strictly per opening mark based on $W \times H$, leaving percentage columns blank.

### B. Prohibition of `HIGH_CONFIDENCE` for Assumptions
- **The Principle**: In a rigorous data ontology, **an assumption can never be HIGH confidence**.
- By definition, if a value requires an assumption (such as average pile depth or assumed rebar intensity), it is an estimate subject to variance. Labeling an assumption as `HIGH` creates a false illusion of certainty in downstream automated models.
- **Enforced Rule**: Active `HIGH_CONFIDENCE` assumption labels across the entire project repository were downgraded to `MEDIUM` or `ESTIMATED`, bringing active `HIGH_CONFIDENCE` assumption labels to exactly **0**.

---

## 3. Why the Project Is NOT `READY_FOR_TAKEOFF`

The certification `READY_FOR_TAKEOFF` implies that an automated agent can immediately run an end-to-end bill of materials without human intervention. In this project, certifying takeoff readiness would be premature and incorrect:
1. **Structural Schedule Gaps**: Structural Sheet 104 omits vertical column elevations and lap splice schedules; Sheet 109 omits OHT wall thickness and rebar.
2. **Substructure Contradiction**: Sheet 101 contains an unresolved contradiction between 54 visible layout cap entities and 84 scheduled caps, with 91 piles unallocated under strip caps.
3. **Missing BBS**: No engineer-approved cut-length schedules exist.
4. **Enforced Status**: Dataset readiness strictly remains **`DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`**.

