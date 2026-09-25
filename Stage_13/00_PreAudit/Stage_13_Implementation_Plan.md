# Stage 13: Implementation Plan — Multi-Project Visual Acquisition

## 1. Objective
Ingest the visual extractions specified by the Stage 12 `visual_extraction_queue.csv` and `visual_extraction_request.json` to extract engineering elements across multiple independent projects. If successful, construct the Level C (Geometry -> BOQ target) multi-project supervised dataset.

## 2. Input
- `Stage_12/19_External_Extraction_Requests/visual_extraction_queue.csv`
- Processed VLM/Human JSON outputs based on the schema (if provided by external systems).
- Duliajan Pilot data (Reference).

## 3. Processing Method
1. **Pre-Audit & Queue Ingestion**: Read the Stage 12 queue to identify target drawings.
2. **Visual Extraction Verification**: Scan the environment for completed VLM JSON responses.
3. **Condition Routing**:
   - If JSON responses exist: Execute geometric validation, BOQ mapping, and construct Datasets A-N. (Condition A).
   - If JSON responses DO NOT exist: Strictly enforce Rule 1 (Never Fabricate) and Rule 32 (No Artificial Data Augmentation). The script will trigger **Condition B** (VISUAL ACQUISITION FAILURE).
4. **Dataset Assembly**: Populate the 21 required Stage 13 directories.
5. **Final Reporting**: Generate `prediction_task_matrix.csv` and `Stage_13_Final_Report.md` precisely answering all 26 required questions.

## 4. Output
- The 21 Stage 13 directories.
- Relational datasets (A through N) containing only verified/provenance-backed data.
- The Final Report and Prediction Matrix.

## 5. Validation & Acceptance Criteria
- **Acceptance Condition**: The pipeline correctly evaluates the presence of external visual data without inventing or assuming dimensions.
- **Stop Condition**: If external visual data is absent, the pipeline will definitively stop at Condition B as instructed, providing the exact acquisition specification without creating further audit loops.

## Execution Sequence
I will author and execute `scripts/stage_13_pipeline.py`. It will read the Stage 12 queue, evaluate the availability of visual extraction outputs, and generate the final outputs accordingly.

