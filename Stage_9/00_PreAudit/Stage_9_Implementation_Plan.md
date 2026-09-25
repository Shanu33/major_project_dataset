# Stage 9: Implementation Plan — Final Engineering Dataset Verification & ML Readiness

## 1. Inspection Scope
- **What will be inspected**: The entirety of the 30-project corpus, with specific scrutiny on the Stage 8 relational datasets (`Datasets A-L`), the Duliajan pilot data (`OIL-RITES-Duliajan-BQ-Housing`), and the Stage 7 OCR outputs.
- **What will be changed**: Nothing in Stages 1–8 will be altered. Stage 9 will exclusively generate new audit logs, trace verifications, and readiness reports inside the `Stage_9/` directory structure.
- **What will not be changed**: Raw documents, existing CSVs from previous stages, and manual transcriptions.

## 2. Planned Scripts to be Executed
We will author and execute `scripts/stage_9_audit.py` which will:
1. **Pre-Audit Engine**: Generate `existing_file_inventory.csv` and map source-to-output traceability.
2. **Sample Verification Engine**: Trace the lineage of the Duliajan Element-Level samples (claimed as "valid" in Stage 8) from `JSON -> Element -> Derivation -> Supervised Sample`.
3. **Leakage & Independence Auditor**: Enforce project-level grouping logic (`GroupKFold`) and verify that 100 footings from 1 project do not falsely inflate `N`.
4. **Engineering Data Modeler**: Formalize the entity relationship mapping (Project -> Building -> Drawing -> Element -> BOQ).
5. **Readiness Scorer**: Populate the final matrix declaring the absolute ML training readiness for Material, Labour, Cost, and Duration.

## 3. Input & Output Files
- **Inputs**: 
  - `/Stage_8/18_Final_Dataset/*.csv`
  - `/13_Corpus_Audit/*.csv`
  - Raw Pilot JSONs (`selected_tower_inputs.json`, `pile_cap_schedule_audit.csv`)
- **Outputs**: 
  - `Stage_9/00_PreAudit/` through `Stage_9/18_Final_Dataset/`
  - The critical `Stage_9_Final_Report.md` (answering the final required questions and providing the mandatory Prediction Task Table).

## 4. Validation Rules
- **Rule of Provenance**: Any sample lacking a traceable source document + page/reference is quarantined.
- **Rule of Origin Differentiation**: Engineering-derived volumes (`L * W * H`) will be strictly separated from observed BOQ quantities. An ML model must not be trained merely to learn basic arithmetic.
- **Rule of Leakage**: BOQ amounts, target-derived quantities, and actual durations will be hard-blocked from entering the `X` feature matrix.

## 5. Stopping Criteria & Acceptance
- **Stopping Criteria**: Execution completes when the `Stage_9_Final_Report.md` is generated, clearly identifying what we have, what we can train, what we cannot train, why, and what specific documents/extraction technologies (e.g., Vision AI) are missing.
- **Acceptance Criteria**: The final dataset MUST pass the test: *Can an independent engineer trace every ML training sample from its X features and Y target back to the original project document and verify that the relationship is engineering-valid and leakage-free?*

## 6. Risks & Expected Bottlenecks
- **Severe Sample Starvation**: Stage 8 proved that only the Duliajan pilot provided structural geometry at the Element Level. Thus, the effective independent project count (`N`) for geometry-to-material ML is 1. We expect the pipeline to definitively conclude `PILOT_ONLY` or `NEEDS_MORE_DATA` for production ML training.

## User Review Required
Please review this implementation plan. Upon your approval, I will execute the final Stage 9 dataset verification script.

