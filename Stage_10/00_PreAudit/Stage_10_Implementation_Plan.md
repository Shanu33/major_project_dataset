# Stage 10: Implementation Plan — Multi-Project ML Dataset Expansion

## 1. Objective
Solve the critical bottleneck identified in Stage 9 (N=1 independent project for geometric elements) by systematically discovering, extracting, and cross-validating architectural/structural geometry from the entire 30-project corpus, mapping it to BOQ ground truths.

## 2. Pre-Audit & Prioritization
We will prioritize the 8 Track A projects, specifically ordering them based on Stage 7 BOQ extraction success:
1. `OIL-RITES-Duliajan-BQ-Housing` (Baseline pilot)
2. `NIT-Nalanda` (High-potential)
3. `EPI-Dhenkanal` 
4. `SBI-GIFT-City`
5. `SBI-DN-Nagar`
6. `TCIL-NVS-JNV`
7. `DFCCIL-Sarmatanr`
8. `MHDC-PMAY`

## 3. Drawing Visual Extraction (Methods A, B, C)
Since local execution lacks an interactive Vision-Language Model API (Method C), we will deploy **Method A (Vector PDF analysis)** via a comprehensive Python script using `PyMuPDF`. 
- **The Heuristic**: The script will iterate through every PDF marked as a "Drawing". It will extract the text layer. We will apply strict RegEx heuristics looking for standardized structural notation (e.g., `C1 300x450`, `Footing F1 1500x1500x450`).
- **The Limitation**: If the drawing is a scanned raster or vector line-art *without* searchable text, Method A will legitimately fail, and Rule 1 dictates we must mark it `UNKNOWN`. We will **NOT** fabricate labels to inflate dataset size.

## 4. Engineering Reconstruction & BOQ Mapping
Any successfully extracted geometric elements (e.g., a footing's L, W, D) will:
1. Have their volume deterministically calculated ($Volume = L \times W \times D$).
2. Be mapped against the project's extracted BOQ using category heuristics (e.g., "RCC in foundation").
3. Be strictly audited for Data Leakage (Target $Y$ will never populate Feature $X$).

## 5. ML Eligibility & Cross-Project Assembly
The pipeline will enforce `GroupKFold` grouping logic. 54 elements from 1 project will be mathematically constrained to `N=1`. 
The `cross_project_sample_matrix.csv` will be the definitive output, proving exactly how many independent projects achieved the `X -> Y` linkage.

## 6. Execution Protocol
I will author and execute `stage_10_pipeline.py`. It will autonomously run phases 1 through 23 as outlined in the objective. It will output the 23 requested folders and the `Stage_10_Final_Report.md`.

