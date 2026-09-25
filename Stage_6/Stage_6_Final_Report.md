# Stage 6 Final Report: Engineering Ground-Truth & ML Dataset Preparation

## Execution Summary
In accordance with non-negotiable data governance rules, we have reconstructed the ML datasets without fabricating any missing parameters.

## Critical Answers to Required Questions

1. **How many projects were successfully processed?** 30 total (8 Track A).
2. **How many documents were successfully extracted?** Structured metadata extracted for all Track A; binary PDFs were appropriately bypassed rather than hallucinated.
3. **How many BOQ rows were extracted?** 128 rows extracted (primarily from existing CSVs like WB-PWD). The rest are explicitly missing pending OCR.
4. **How many drawings were interpreted?** 0 directly (requires vision OCR/physical inspection); architectural parameters were pulled from existing metadata JSONs.
5. **How many engineering parameters obtained?** Basic footprint/storeys available for 8 projects.
6. **How many values are DIRECT?** Cost/Duration for Track A are DIRECT.
7. **How many are DERIVED?** 0 (Blocked by lack of drawings).
8. **How many are INFERRED?** 0 (Rule: Do not infer quantities).
9. **How many are ASSUMED?** 0 (Rule: No fabrication).
10. **How many remain UNKNOWN?** The vast majority of material and labor quantities.
11. **How many projects have material labels?** 0
12. **How many have labour labels?** 0
13. **How many have cost labels?** 2
14. **How many have duration labels?** 2
15. **Which projects are genuinely ML-ready?** **NONE.** (0 out of 30 have BOTH engineering inputs and verified quantity labels).
16. **Which projects require additional documents?** All Track B projects require complete drawing/BOQ sets.
17. **Which fields have the highest missingness?** `concrete_quantity`, `steel_quantity`, `total_mandays` (100% missingness without PDF extraction).
18. **Which targets have enough project-level samples?** None. Cost and Duration have ~8 samples, which is insufficient for reliable supervised learning.
19. **What data leakage risks exist?** BOQ total amounts and final contract values must be strictly excluded from input feature vectors (`X`). This was verified in Phase 36.
20. **What should be done before model training?** Deploy an advanced Vision-language model or tabular OCR pipeline to extract the locked BOQ tables, and commission physical takeoff from drawing sets. **DO NOT TRAIN MODELS YET.**

## Final Project Classification
Every project currently falls into **DOCUMENT_RECOVERY_REQUIRED** or **PARTIALLY_ML_READY** (only for macro cost/time). No project is fully ML_READY for material/labor estimation.
