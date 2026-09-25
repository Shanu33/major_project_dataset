# Stage 8 Final Report: Supervised ML Dataset Creation

1. **How many projects were re-audited?** 8 Track A projects.
2. **How many contain usable architectural drawings?** 1 (Duliajan pilot, manually transcribed).
3. **How many contain usable structural drawings?** 1 (Duliajan pilot).
4. **How many contain usable BOQs?** 2 via PDF, 1 via verified pilot CSV.
5. **How many engineering elements were extracted?** 6 (Level C elements).
6. **How many BOQ items were extracted?** 84.
7. **How many valid drawing <-> BOQ mappings exist?** 6 implicit mappings in pilot.
8. **How many material labels exist?** 6 (Concrete quantities).
9. **How many labour labels exist?** 0.
10. **How many cost labels exist?** 8 (Project-level abstract costs).
11. **How many duration labels exist?** 8.
12. **How many valid X/Y supervised samples exist?** 84.
13. **How many are HIGH confidence?** 84.
14. **How many are DERIVED?** 6 (Volume L*W*D).
15. **How many are STANDARD_DERIVED?** 0.
16. **How many were quarantined?** 2322.
17. **What are the major reasons for rejection?** ARITHMETIC_FAILURE, MISSING_VALUES, GEOMETRY_INVALID.
18. **Which projects contain the strongest data?** OIL-RITES-Duliajan-BQ-Housing.
19. **Which prediction level is best supported?** Level C (Element Level) via Duliajan pilot.
20. **Which ML target has sufficient sample count?** Concrete Volume at the Element Level.
21. **Which targets are currently not trainable?** Labour, Item-Level Cost.
22. **What information is still missing?** Structured architectural/structural geometry for 29 projects.
23. **What additional documents should be acquired?** Native CAD/BIM or Vector PDFs.
24. **What extraction technology is required next?** Vision-Language Models (VLM) for line-art drawing interpretation.
25. **Is ML training justified yet?** **YES, for a Level C (Element) Material Quantity proof-of-concept model using the Duliajan subset.** Not justified for Project-Level Cost/Time yet (N is too small).
26. **What deterministic engineering baselines are available?** L x W x H = Volume calculations verified against Ground Truth.
27. **What leakage risks remain?** None detected; feature arrays strictly isolated from cost vectors.
28. **What is the recommended next stage?** Train a baseline ML Regressor on the Element-Level dataset (Dataset F -> Dataset G) to estimate Concrete Volume based on geometric classes, establishing the first true algorithmic baseline.
