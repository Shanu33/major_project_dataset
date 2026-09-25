# Slide Deck Final Guardrail & Safety Verification

**Inspected Artifact**: `10_Controlled_Transcription/priority_i_slide_deck/major_project_review_deck_final.pptx`  
**Evaluation Scope**: Text frames, table cells, shape titles, and speaker notes across all 12 slides.  
**Auditor**: Independent Guardrail & Verification Script  

---

## 1. Automated Unsafe Phrase Search Results

An exhaustive programmatic search was executed across all shapes, text frames, table cells, and speaker notes in `major_project_review_deck_final.pptx`. The results are recorded below:

| Prohibited Search Term | Occurrences Found | Verification Status | Action Taken / Compliance Note |
|---|---|---|---|
| `0.00% error` | **0** | **CLEAN** | Completely absent. Replaced with defensible phrasing (`traceable to verified inputs`). |
| `zero variance` | **0** | **CLEAN** | Completely absent. Replaced with `formula-recomputed from controlled dimensions`. |
| `validated accuracy` | **0** | **CLEAN** | Completely absent. No accuracy percentages are claimed. |
| `cost accuracy` (unqualified) | **0** | **CLEAN** | Only appears qualified as `cost accuracy is not calculated`. |
| `quantity accuracy calculated` | **0** | **CLEAN** | Only appears qualified as `quantity accuracy is not calculated`. |
| `fully automated BOQ` | **0** | **CLEAN** | Completely absent. System is framed as an auditable transcription and formula layer. |
| `full tower takeoff` (unqualified)| **0** | **CLEAN** | Only appears qualified as `full takeoff remains blocked where evidence is missing`. |
| `READY_FOR_TAKEOFF` | **0** | **CLEAN** | Zero active affirmative occurrences. Project is strictly NOT ready for takeoff. |
| `HIGH_CONFIDENCE` on assumptions | **0** | **CLEAN** | Zero occurrences on assumptions. Governed by the rule capping assumptions at MEDIUM/ESTIMATED. |
| `reinforcement tonnage calculated`| **0** | **CLEAN** | Completely absent. Rebar takeoff is explicitly documented as blocked due to missing BBS. |
| `labour prediction` | **0** | **CLEAN** | Completely absent. Labour modelling is explicitly blocked. |
| `duration prediction` | **0** | **CLEAN** | Completely absent. Single-tower duration is designated NOT_CALCULATED. |
| `validation completed` | **0** | **CLEAN** | Completely absent. Ground-truth validation was not performed. |
| `failure` (on Slide 9) | **0** | **CLEAN** | Replaced with `Safe Blocking on Missing Evidence`. |
| `accuracy` (on Slide 10) | **0** | **CLEAN** | Zero occurrences on Slide 10 or its speaker notes. |

---

## 2. Priority F Sample Value Verification

The table below confirms the exact mathematical and typographical matching of all sample values on **Slide 10** against the Priority F source of truth (`10_Controlled_Transcription/priority_f_sample_quantity_execution/`):

| Slide 10 Element | Slide 10 Printed Text | Priority F Ground Truth Value | Source Sheet Callout | Match Result |
|---|---|---|---|---|
| **Door D1** | `0.800 m x 2.100 m` $\rightarrow$ `1.680 m2` | `0.800 m x 2.100 m = 1.680 m²` | Sheet `AR/TD/005` Schedule | **EXACT MATCH (100%)** |
| **Window W1** | `1.200 m x 1.200 m` $\rightarrow$ `1.440 m2` | `1.200 m x 1.200 m = 1.440 m²` | Sheet `AR/TD/005` Schedule | **EXACT MATCH (100%)** |
| **Door-Window DW1** | `2.000 m x 2.100 m` $\rightarrow$ `4.200 m2` | `2.000 m x 2.100 m = 4.200 m²` | Sheet `AR/TD/005` Schedule | **EXACT MATCH (100%)** |
| **Living / Dining** | `5.520 m x 3.970 m` $\rightarrow$ `21.914 m2` | `5.520 m x 3.970 m = 21.914 m²` | Sheet `AR/TD/005` Unit Plan | **EXACT MATCH (100%)** |
| **Master Bedroom** | `3.845 m x 3.220 m` $\rightarrow$ `12.381 m2` | `3.845 m x 3.220 m = 12.381 m²` | Sheet `AR/TD/005` Unit Plan | **EXACT MATCH (100%)** |
| **Kitchen** | `2.580 m x 2.440 m` $\rightarrow$ `6.295 m2` | `2.580 m x 2.440 m = 6.295 m²` | Sheet `AR/TD/005` Unit Plan | **EXACT MATCH (100%)** |

*Verification Finding*: Zero unauthorized sample calculations exist. Zero rounding discrepancies detected.

---

## 3. Dataset Readiness Label Verification

- **Repository-Wide Active Readiness Status**: **`DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`**
- **Takeoff Readiness Status**: Strictly **NOT `READY_FOR_TAKEOFF`**.
- **Stage Classification**: `PRIORITY_I_B_SLIDE_DECK_VISUAL_QA_COMPLETE`.
- **Integrity Statement**: The slide deck openly presents that drawing-based takeoff requires cross-register reconciliation and that bulk material takeoff is locked until missing engineering schedules are obtained.

---

## 4. Overclaim and Boundary Check

1. **Full BOQ Automation**: **NOT CLAIMED**. Framed as an auditable multi-document data extraction and formula dependency architecture.
2. **Cost Accuracy**: **NOT CLAIMED**. Cost accuracy is explicitly stated as `not calculated`.
3. **Quantity Accuracy**: **NOT CLAIMED**. Quantity accuracy is explicitly stated as `not calculated`.
4. **Full Tower Takeoff**: **NOT CLAIMED**. 14 work packages are explicitly shown as `INPUTS_BLOCKED` in Slides 7, 9, 10, and 11.
5. **Reinforcement Tonnage**: **NOT CLAIMED**. Rebar takeoff is explicitly marked blocked due to the absence of a Bar Bending Schedule (BBS).
6. **Labour & Duration Prediction**: **NOT CLAIMED**. Single-tower duration is designated `not calculated` and labour models remain blocked.
7. **Model Training Completed**: **NOT CLAIMED**. The project is framed as an auditable benchmark dataset and pipeline, not a trained generative model.

---

## 5. Final Conclusion

The PowerPoint presentation [`major_project_review_deck_final.pptx`](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/10_Controlled_Transcription/priority_i_slide_deck/major_project_review_deck_final.pptx) has passed all visual, structural, and factual safety checks. It satisfies every requirement of academic integrity, civil engineering precision, and anti-hallucination guardrails, and is fully approved for presentation to the major project guide and review panel.

