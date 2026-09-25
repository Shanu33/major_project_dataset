# Major Project Roadmap: Next Technical Steps, Dataset Expansion, and Demo Strategy

**Project**: Evidence-Grounded Construction Intelligence  
**Target Repository**: `10_Controlled_Transcription/priority_g_project_summary/`  
**Focus**: Final Year Major Project Execution Strategy & Thesis Defense Preparation  

---

## 1. Immediate Next Technical Step: Building Services (MEP) Baseline

Before expanding across multiple buildings, the typical tower prototype must complete its final discipline:
- **Priority H — Building Services (MEP) Controlled Transcription**:
  - Transcribe directly visible equipment schedules, pipe diameters, fixture counts, electrical distribution boards, and fire protection risers from Sheets `MEP/001` to `MEP/018`.
  - Maintain the same evidence-control rules: record directly visible fixture counts (water closets, washbasins, taps, distribution boards) without estimating total pipe lengths from 2D schematics unless isometric schedules exist.

---

## 2. Post-Award Evidence Recovery Strategy

To unblock the 13 currently blocked trades in the OIL-RITES pilot, the following post-award EPC contractor records should be sought:
1. **Contractor's Approved Bar Bending Schedule (BBS)**: Complete spreadsheet detailing bar marks, diameters, cut lengths, bend shapes, and tonnage per floor.
2. **Approved Pile Borehole / Termination Schedule**: Geotechnical engineer's signed termination depth chart.
3. **Reconciled Foundation General Arrangement**: Drawing resolving the 54 vs 84 pile cap discrepancy and allocating all 207 piles.
4. **Architectural Wall Centerline & Opening Schedule**: Dimensioned wall centerline layout plan deducting structural column/wall block-outs, and opening schedules with count per unit.
5. **Itemized Priced Contract BOQ**: Line-by-line schedule of quantities for one typical tower.

---

## 3. Dataset Expansion Strategy: Multi-Project Generalization

To demonstrate that the proposed architecture is generalizable across different building typologies:
1. **Target 2–3 Additional Projects**:
   - **Project 2**: Institutional / Academic Building (e.g., CPWD / IIT campus block) with framed structure and large clear spans.
   - **Project 3**: Commercial / Office Building with flat slabs or steel composite framing.
   - **Project 4**: Pre-engineered Building (PEB) or industrial shed with steel framing.
2. **Standardized Directory & File Schema**:
   - Apply the exact same 10-folder structure (`00_Project_Control`, `01_Drawing_Registers`, `10_Controlled_Transcription`, etc.) to every new project.
   - Use identical CSV register schemas (`controlled_opening_register.csv`, `controlled_beam_register.csv`, etc.) to enable automated programmatic ingestion.

---

## 4. Cross-Project Benchmarking Framework

Once multiple projects are structured under this ontology:
- **Compare Information Density**: Measure the ratio of directly observed parameters vs assumption-required parameters across different design consultants.
- **Compare Schedule Completeness**: Quantify how often Indian public works tender drawings omit BBS, pile termination depths, or opening counts.
- **Audit Agent Robustness**: Evaluate whether the AI correctly blocks execution when given incomplete drawings across diverse projects, proving that it does not hallucinate.

---

## 5. What to Include in the Final Year Project Report / Thesis

1. **Chapter 1: Introduction & Problem Definition**: The civil engineering estimation problem; limitations of manual takeoff; catastrophic risks of ungrounded LLM hallucinations in construction.
2. **Chapter 2: Literature Review**: Standards of measurement (IS 1200, NRM, POMI); BIM-based QTO vs 2D drawing realities in Indian public works; state of AI in construction estimating.
3. **Chapter 3: Evidence-Controlled System Architecture**: The 11-stage pipeline; ontological separation between AI inputs and ground-truth benchmarks; provenance hierarchy.
4. **Chapter 4: Case Study Implementation (OIL-RITES Housing Complex)**: Pilot scope; document ingestion; controlled transcription of foundation, structural, architectural, and finish trades.
5. **Chapter 5: Cross-Register Reconciliation & Formula Setup**: Vertical profile alignment; core material resolution; formula mapping; input dependency tracking; failure mode registers.
6. **Chapter 6: Proof-of-Method Verification & Sample Execution**: Row-by-row auditable sample execution; enforcement of takeoff blocking guardrails.
7. **Chapter 7: Discussion, Limitations, & Future Work**: What is complete; what is blocked; why academic honesty prevents claiming cost accuracy; roadmap to production.

---

## 6. What to Show in the Project Demo / Defense

Build a clean, interactive Streamlit, Gradio, or web-based demonstration dashboard featuring:
1. **Document Inspector**: View approved drawing sheet with highlighted title block and extracted metadata.
2. **Controlled Register Browser**: Filter transcribed CSV registers by trade, element mark, and provenance tag.
3. **Formula & Dependency Visualizer**: Select a formula (e.g., `FM-MAS-01` Masonry); inspect its formula logic; view active green checks for available inputs and red locks for blocked inputs.
4. **Interactive Sample Calculator**: Click an opening mark (`W1`) or room (`Living / Dining`) to display the live, step-by-step arithmetic trace: $1.20 \times 1.20 = 1.440\text{ m}^2$.
5. **The "Execution Gate" (The Most Impressive Feature)**: Click a button labeled *"Generate Full Tower Takeoff"*; show the system **refusing to calculate**, displaying a detailed explanation of why it is blocked (missing BBS, unsegregated wall centerlines, unscheduled opening counts). Civil engineering professors will appreciate an AI system with the domain knowledge to refuse premature calculations.

---

## 7. What NOT to Claim During Defense

To ensure academic and professional defensibility, **strictly avoid these claims**:
- **Do NOT claim**: "The system achieved 99% cost accuracy." (No itemized tower BOQ exists).
- **Do NOT claim**: "The single tower costs ₹157.25 Crore." (That was a superseded media figure; official complex award was ₹128.14 Cr).
- **Do NOT claim**: "Single tower duration is 15 months." (No single-tower CPM schedule exists; 24 months is the complex contract period).
- **Do NOT claim**: "Full bill of materials is calculated." (Reinforcement, masonry, concrete, and finishes remain blocked).
- **DO claim**: "We built an evidence-controlled ontological framework that extracts verifiable drawing facts, computes deterministic micro-samples, and enforces mathematical guardrails against AI hallucination."

