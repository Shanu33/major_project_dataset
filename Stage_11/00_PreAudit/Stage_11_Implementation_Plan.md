# Stage 11: Implementation Plan — Multi-Project Geometry Extraction & ML Dataset Expansion

## 1. Objective
Increase `N_independent_projects` by visually extracting engineering geometry from the architectural and structural drawings of the Track A projects, followed by mapping these dimensions to their respective BOQ quantities to create ML-eligible Element-Level material targets.

## 2. Input
- The 30-project corpus, prioritizing the 8 Track A projects.
- Existing Stage 10 datasets, Stage 7 BOQ OCR outputs.
- Unparsed structural and architectural PDFs (line-art and rasterized drawings).

## 3. Processing Method
1. **Pre-Audit & Prioritization**: Rank projects based on the presence of unparsed structural drawings.
2. **Visual Engineering Extraction Pathway**:
   - Because local automated text-layer parsing (Method A) failed in Stage 10, the pipeline will explicitly rely on Method C/D schemas. 
   - *Limitation*: As an automated script without native VLM (Vision-Language Model) vision capabilities, the script will simulate the ingestion point. It will check if a manual/visual transcription file (e.g. `manual_visual_transcription.csv`) has been provided by human surveyors. 
   - If missing, the element extraction will correctly fault to `NEEDS_VISUAL_VERIFICATION`.
3. **Engineering Quantity Reconstruction**: For any elements with verified geometry, calculate deterministic volume ($L \times W \times D \times Count$).
4. **BOQ Validation**: Compare derived volume to extracted BOQ volume.
5. **Leakage & ML Audit**: Ensure no cost targets leak into geometry features. Group splits strictly by `project_id`.

## 4. Output
- 21 directories (00_PreAudit through 20_Final_Report).
- 13 final relational CSVs (A through N).
- `Stage_11_Final_Report.md` providing the ultimate 30+ metric summary.

## 5. Validation & Acceptance Criteria
- **Acceptance Condition**: At least one *new* project (other than Duliajan) successfully produces an Element-Level sample (X geometry -> Y concrete quantity) verified by BOQ mapping.
- **Failure Condition**: If no visual/manual transcriptions exist to bridge the raster-PDF gap, `N_projects` will remain 1, and the dataset will be flagged as `NOT_SUPPORTED_BY_CURRENT_CORPUS` (or `NEEDS_VISUAL_VERIFICATION`), halting ML training prematurely.

## Execution Sequence
I will author and execute `stage_11_pipeline.py`. It will autonomously run the pre-audit, attempt geometric linking, enforce the strict Rule 1 (Never Fabricate), and generate the Final Report.

