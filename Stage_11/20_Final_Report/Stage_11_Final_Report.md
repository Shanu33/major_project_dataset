# Stage 11 Final Report: Multi-Project Geometry Extraction

## 1. Current Corpus Status
- **Total projects**: 30
- **Usable projects**: 8 (Track A)
- **Projects with usable drawings**: 8
- **Projects with verified geometry**: 1 (Duliajan)
- **Projects with verified BOQ**: 3 (Duliajan, plus partials)
- **Projects with geometry + BOQ**: 1
- **Projects with Element <-> BOQ Mapping**: 1
- **Projects with Material labels**: 1
- **Projects with Labour labels**: 0
- **Projects with Cost labels**: 8 (Project-level abstract only)
- **Projects with Duration labels**: 8 (Project-level abstract only)

## 2. Drawing Extraction Success Rate
- Text-layer extraction (Method A) failed on all 7 unparsed structural drawings. Line-art without embedded text requires Method C (VLM). 

## 3. Critical Statistics
- Total engineering elements extracted: 54 (from 1 project)
- Independent projects represented in ML samples: **1**

## 4. Final Prediction Task Matrix
| Prediction Task | Unit | X Available | Y Available | Projects | Samples | Baseline | ML Eligible |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Concrete Quantity | Element | YES | YES | 1 | 54 | YES | NO (N=1) |
| Steel Quantity | Element | NO | NO | 0 | 0 | NO | DATA ACQUISITION REQUIRED |
| Masonry Quantity | Element | NO | NO | 0 | 0 | NO | DATA ACQUISITION REQUIRED |
| Labour | Element | NO | NO | 0 | 0 | NO | DATA ACQUISITION REQUIRED |
| Cost | Project | NO | YES | 8 | 8 | NO | NEEDS_MORE_DATA |
| Duration | Project | NO | YES | 8 | 8 | NO | NEEDS_MORE_DATA |

## 5. Final Decision Logic
### **DATA ACQUISITION REQUIRED**
The corpus does not currently support multi-project element-level supervised ML. Due to Rule 1 (Never Fabricate) and Rule 7 (Do Not Inflate Dataset Size), the effective dataset size for generalizable ML remains N=1. 

## 6. Exact Data Acquisition Plan
**What exact additional data must be collected to make this system trainable?**
- **Missing Information:** Geometric bounding boxes (L, W, D, Count) for structural elements (Footings, Columns, Slabs).
- **Required Acquisition Method:** Deployment of a Vision-Language Model (VLM) or human quantity surveyors (Method C/D) to parse the structural blueprint PDFs for NIT-Nalanda, EPI-Dhenkanal, and DFCCIL-Sarmatanr.
- **Priority:** Critical. ML Training is mathematically blocked until N >= 5 independent projects are populated with element geometries.

## 7. Recommended Next Technical Step
Do NOT initiate ML Model Training. Halt the pipeline and commission a Vision AI batch process (or manual annotation drive) to transcribe the architectural/structural PDFs into `engineering_elements.csv`.
