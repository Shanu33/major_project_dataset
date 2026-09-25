# Live Demonstration Script: Evidence-Controlled Quantity Takeoff

**Demo Title**: Live Demonstration of Multi-Document Controlled Transcription, Deterministic Micro-Takeoff, and Refusal Guardrails  
**Target Duration**: 5–7 Minutes  
**Presenter**: Major Project Candidate  
**Environment**: Visual Studio Code / Terminal / Local File Explorer  
**Working Directory**: `C:\Users\shahnawaz khan\OneDrive\Documents\DataRequirement\OIL-RITES-Duliajan-BQ-Housing`

---

### Step 1: Project Repository & Document Architecture (Time: 0:00 – 0:45)

**Action on Screen**:
- Open the project folder in VS Code or File Explorer.
- Expand folders:
  - `00_Project_Control/`
  - `01_Drawing_Registers/`
  - `10_Controlled_Transcription/`
- Highlight the 55 tender drawing PDFs located in the drawing folders.

**Exact Speaking Script**:
> *"Respected panel members, I will now walk you through a live demonstration of our evidence-controlled civil quantity intelligence pipeline. On my screen is the pilot repository for the OIL India Workmen Housing Complex in Duliajan, managed by RITES. Notice our directory structure: raw input drawings, Design Basis Reports, and CPWD specifications are strictly segregated in Phase 0 and 1. All controlled outputs are located inside folder `10_Controlled_Transcription`. We do not perform monolithic black-box estimation; every stage is an auditable, human-readable CSV or Markdown artifact."*

---

### Step 2: Controlled Transcription Registers (Time: 0:45 – 1:30)

**Action on Screen**:
- Open `10_Controlled_Transcription/controlled_column_wall_register.csv`.
- Scroll across columns: `element_id`, `element_type`, `grid_location`, `width_mm`, `depth_mm`, `main_rebar_summary`, `extraction_method`, `confidence`.
- Point cursor to row for Column `C1` and Shear Wall `SW1`.

**Exact Speaking Script**:
> *"Next, let us examine our controlled transcription layer. Here is `controlled_column_wall_register.csv`. You can see all 49 vertical load-bearing members—16 columns and 33 shear walls—transcribed from Structural Drawing Sheet 104. Look closely at Column C1: it captures the exact dimension, 300mm by 900mm, with 14 numbers of 32mm bars and 8 numbers of 25mm bars. Notice that every row records the exact source sheet and extraction method. There is no guessing; if a parameter is visible on the sheet, it is transcribed with its exact coordinate location."*

---

### Step 3: Evidence Tags & Provenance Control (Time: 1:30 – 2:15)

**Action on Screen**:
- In `controlled_column_wall_register.csv`, highlight the column `extraction_method` and `confidence`.
- Show how `height_mm` is marked:
  - Value: `3050`
  - Extraction Method: `DERIVED_FROM_ARCHITECTURAL_SECTION`
  - Confidence: `MEDIUM` (or `DERIVED_GEOMETRY`)
- Open `10_Controlled_Transcription/civil_reconciliation_index.csv`.

**Exact Speaking Script**:
> *"Now, let us examine our evidence provenance tags. Notice the storey height for Column C1: it is 3050mm, but its extraction method is explicitly tagged as `DERIVED_FROM_ARCHITECTURAL_SECTION`. Why? Because the structural drawing, Sheet 104, does not print column heights. It only details rebar schedules. An ungrounded AI would claim it read the height from Sheet 104. Our system traces the height back to Architectural Section A-A on Sheet 012. Furthermore, in accordance with our project rules, this parameter is classified as `MEDIUM` confidence because it is derived across disciplines. Under our rules, zero assumptions are permitted to claim 'High Confidence'."*

---

### Step 4: Formula Setup & Dependency Mapping (Time: 2:15 – 3:00)

**Action on Screen**:
- Open `10_Controlled_Transcription/priority_e_formula_setup/formula_input_dependency_register.csv`.
- Highlight rows for:
  - `FORMULA-CONC-001` (Pile Concrete)
  - `FORMULA-MAS-001` (Brick Masonry)
  - `FORMULA-STL-001` (Reinforcement Steel)
- Show column `execution_readiness_status` displaying `INPUTS_BLOCKED`.

**Exact Speaking Script**:
> *"Here in folder `priority_e_formula_setup`, we open `formula_input_dependency_register.csv`. We have mapped 14 standardized civil engineering measurement formulas conforming strictly to IS 1200. But notice the status column on the far right: for every single bulk quantity formula, the status is `INPUTS_BLOCKED`. Each formula explicitly maps its prerequisite inputs. For example, the pile concrete formula requires pile diameter, pile count, and pile cut-off depth. Because the pile depth is not scheduled on the drawing, the formula is locked and barred from execution."*

---

### Step 5: Verified Sample Micro-Calculations (Time: 3:00 – 3:50)

**Action on Screen**:
- Open `10_Controlled_Transcription/priority_f_sample_quantity_execution/sample_opening_area_calculations.csv`.
- Highlight Toilet Door `D1` ($0.800\text{m} \times 2.100\text{m} = 1.680\text{ m}^2$) and Bedroom Window `W1` ($1.200\text{m} \times 1.200\text{m} = 1.440\text{ m}^2$).
- Open `10_Controlled_Transcription/priority_f_sample_quantity_execution/sample_room_area_calculations.csv`.
- Highlight Living/Dining Room ($5.520\text{m} \times 3.970\text{m} = 21.914\text{ m}^2$, $P = 18.980\text{m}$).

**Exact Speaking Script**:
> *"To prove that our formula engine functions with mathematical precision when evidence is complete, we ran Priority F: Controlled Sample Execution. On screen are the results: 5 door and window face areas, and 5 room carpet areas and perimeters. For Toilet Door D1, width is 0.800m, height is 2.100m, resulting in exactly 1.680 square meters. For Window W1, 1.200m by 1.200m gives 1.440 square meters. For the Living/Dining room on Sheet AR/TD/005, dimensions are 5.520m by 3.970m, yielding exactly 21.914 square meters with a perimeter of 18.980m. These calculations are formula-recomputed from controlled dimensions and internally consistent with our Priority F sample register. Notice what we did not do: we did not multiply these by 24 flats or 8 towers. We preserve the integrity of the single observed element."*

---

### Step 6: The Refusal Engine in Action (Time: 3:50 – 4:40)

**Action on Screen**:
- Open `10_Controlled_Transcription/priority_f_sample_quantity_execution/blocked_full_takeoff_guardrail.csv`.
- Point out the 14 blocked trades: Piling Concrete, Pile Caps, Columns Concrete, Framing Rebar, Brickwork, Plastering.
- Show column `blocker_summary` and `prerequisite_drawing_or_decision_needed`.

**Exact Speaking Script**:
> *"Now, what happens if an automated agent attempts to calculate the full tower concrete or reinforcement? Look at `blocked_full_takeoff_guardrail.csv`. Our automated guardrail intercepts the execution. It flags 14 blocked trades. Look at Trade 1, Piling: 'Depth unrecorded on Sheet 100; DBR specifies 15m to 20m range only. Takeoff blocked until pile termination schedule is issued.' Look at Trade 2, Pile Caps: 'Plan layout shows 54 cap entities while schedule shows 84 caps. Blocked until RFI clarification.' And look at Trade 6, Reinforcement: 'Zero bar bending schedules issued. Steel cut-length calculation blocked.' The engine refuses to execute."*

---

### Step 7: Why Refusal is a Feature, Not a Failure (Time: 4:40 – 5:30)

**Action on Screen**:
- Switch to `10_Controlled_Transcription/priority_g_project_summary/ai_input_vs_ground_truth_explanation.md` or display Slide 9.
- Highlight the contrast between 'Naïve AI Hallucination' and 'Engineered Civil Refusal'.

**Exact Speaking Script**:
> *"In computer science, when a program halts, it is often seen as an exception. But in civil engineering quantity surveying, halting when drawings lack critical data is the hallmark of professional competence. If an estimator guesses a 18-meter pile depth and the actual depth turns out to be 15 meters, that is a 20% variance across 207 piles—amounting to hundreds of cubic meters of wasted concrete and serious legal claims. Our system treats refusal as an active engineering feature. It protects the client and contractor by generating an actionable RFI register rather than an ungrounded estimate."*

---

### Step 8: Academic Conclusion & Future Scope (Time: 5:30 – 6:15)

**Action on Screen**:
- Open `10_Controlled_Transcription/priority_h_presentation_package/one_page_project_brief.md`.
- Conclude by pointing to the Final Value Proposition at the bottom of the brief.

**Exact Speaking Script**:
> *"To conclude this live demonstration: we have shown an auditable, multi-document architecture that extracts civil parameters with strict evidence provenance, reconciles inter-trade discrepancies, executes verified micro-takeoffs, and safely blocks takeoff when drawings are incomplete. Our immediate next step is transcribing the 18 MEP sheets to complete building services, followed by scaling this framework across 10 PSU tender packages. Thank you, and I am now ready to take the panel's questions."*


