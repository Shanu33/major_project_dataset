# Stage 12: Implementation Plan — Visual Extraction Queue Generation

## 1. Objective
Execute **Outcome B** as mandated: Stop auditing the bottleneck and produce the exact visual extraction package required for an external VLM/human engineer. Since the current headless environment lacks native multimodal VLM endpoints, we will programmatically assemble the definitive `19_External_Extraction_Requests` package for all structural and architectural PDFs in the Track A corpus.

## 2. Input
- The 8 prioritized Track A projects.
- The raw structural and architectural PDFs within those project directories.

## 3. Processing Method
1. **Pre-Audit & Prioritization**: Map the current state and list the Track A projects.
2. **Drawing Discovery**: Scan the file system to locate all relevant PDFs. 
3. **Extraction Request Generation**: For every PDF discovered, generate a machine-readable entry in `visual_extraction_queue.csv`. We will specify exactly what geometric elements and dimensions must be extracted per the target schema.
4. **JSON Schema Definition**: Output `visual_extraction_request.json` defining the strict JSON structure the external VLM or human must return. This schema will mandate `source_evidence` references for every dimension to enforce Rule 1 (Never Fabricate) and Rule 5 (Drawing Evidence).
5. **Final Reporting**: Compile the `prediction_task_matrix.csv` reflecting the current state (waiting on the queue) and generate `Stage_12_Final_Report.md`.

## 4. Output
- The 21 requested Stage 12 directories.
- The definitive `visual_extraction_queue.csv` bridging the gap to physical extraction.
- The VLM input JSON schema.
- The final Stage 12 report.

## 5. Validation & Acceptance Criteria
- **Acceptance Condition**: The complete machine-readable extraction queue is generated, explicitly linking every required project and PDF to the target extraction schema.
- **Failure Condition**: Any fabrication of geometric samples to falsely claim Outcome A.

## Execution Sequence
I will author and execute `stage_12_pipeline.py` to recursively crawl the Track A PDF directories, build the page-level VLM requests, and generate the final reports and tracking datasets.

