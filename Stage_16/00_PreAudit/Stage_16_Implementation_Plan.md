# Stage 16 Implementation Plan: Multi-Project Visual Ground-Truth Expansion

## 1. Current Dataset State
*   **Total Corpus Projects**: 30
*   **Independent Projects with Verified ML Samples**: 2 (OIL-RITES-Duliajan, NIT-Nalanda)
*   **Verified Elements**: 55 (54 Footings, 1 Pile)
*   **Current ML Status**: `NEEDS_MORE_PROJECTS` (N < 5)

## 2. Remaining Candidate Projects (Extraction Priority)
To reach $N \ge 5$, we will target the remaining Track A projects:
1.  **EPI-Dhenkanal-ICDS-Staff-Quarters**: Has `volume02.pdf` (drawings) and `Volume3.pdf` (BOQ).
2.  **DFCCIL-Sarmatanr-Larabad-Koderma-Quarters**: Standard railway quarters.
3.  **MHDC-PMAY-Khairi-Kamptee-Nagpur**: LIG tenement blocks.
4.  **SBI-GIFT-City-Twin-Towers**: Commercial high-rise, 162-page BOQ.
5.  **SBI-DN-Nagar-Andheri-122-Flats**: Tender drawings exist.
6.  **TCIL-NVS-JNV-Azamgarh-Quarters**: Quarters floor plans and BOQ exist.

## 3. Visual Extraction Methodology
1.  **Rendering**: Execute `stage_16_render.py` to convert structural and BOQ PDF pages into high-resolution PNGs in `Stage_16/03_Rendered_Drawings/`.
2.  **Visual Agent Processing**: Use multimodal LLM capability (`view_file`) to inspect the PNGs, identify engineering elements (e.g., Footings, Columns, Piles), and extract explicit dimensions ($L, W, D$, Diameter).
3.  **BOQ Mapping**: Visually or textually locate the corresponding BOQ line item, extract the observed target quantity (Y), and map it to the extracted element (X).

## 4. Validation & Provenance Rules
*   **Never Fabricate**: Missing dimensions = `UNKNOWN`. Missing counts = `UNKNOWN`.
*   **Arithmetic Validation**: Reconstruct geometric volume deterministically ($L \times W \times D$) and compare with BOQ quantities.
*   **Provenance Trace**: Every sample must record `project_id`, `source_document`, `page_number`, `element_id`, and `origin` (`DIRECT`/`DERIVED`).

## 5. Leakage & Independence Rules
*   **Leakage Prevention**: Do not include target variables (BOQ quantities, amounts, final costs) inside the Feature Matrix ($X$).
*   **Project Independence**: Elements are grouped strictly by `project_id`. 100 elements from 1 project = 1 independent sample grouping.

## 6. Stopping & ML-Readiness Criteria
*   **Success (Condition A)**: $N\_projects \ge 5$ containing fully verified X/Y pairs.
*   **Halt (Condition B)**: All remaining Track A candidates attempted, but unreadable drawings, missing BOQs, or external blockers prevent reaching $N = 5$.
*   **Final Delivery**: Produce relational tables, validation logs, and the `Stage_16_Final_Report.md`.

