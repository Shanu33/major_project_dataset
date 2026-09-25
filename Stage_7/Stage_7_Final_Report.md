# Stage 7 Final Report: Engineering Ground-Truth Validation

1. **How many projects were actually usable?** 8 Track A projects attempted.
2. **How many have verified BOQs?** 2 (Successful extractions via pdfplumber).
3. **How many have verified architectural data?** 0 directly verified via text.
4. **How many have verified structural data?** 0 directly verified.
5. **How many have verified specifications?** 0 directly verified.
6. **How many have verified cost targets?** 0 verified from PDFs.
7. **How many have verified duration targets?** 0 verified from PDFs.
8. **How many have verified material quantity targets?** 2.
9. **How many have verified labour targets?** 0.
10. **How many have sufficient X features?** 0.
11. **Which existing CSV/JSON files were verified?** N/A (Excluded forced extraction).
12. **Which existing CSV/JSON files were invalid?** N/A.
13. **Which PDF data was successfully extracted?** Partial BOQ tables where borders allowed.
14. **Which PDF data remains inaccessible?** Complex multi-span tables, scanned drawings.
15. **Which drawings were successfully interpreted?** None (Requires Vision AI).
16. **Which engineering quantities were successfully reconstructed?** None.
17. **Which reconstructed quantities agree with BOQ?** N/A.
18. **What are the major data-quality problems?** Missing structured data format.
19. **What is the actual number of trainable samples for each target?** Materials: 2, Cost: 0, Duration: 0.
20. **Is the corpus ready for ML training?** **NO.**
21. **If not, exactly what must be collected/extracted next?** Manual or Vision-based mapping of architectural drawings to BOQ items.
22. **Which projects should be retained?** Track A.
23. **Which projects should be quarantined?** Track B until documents recovered.
24. **Which projects should be completely removed?** Track C/D.
25. **What is the recommended next engineering/data-acquisition step?** Commissioning structural/architectural estimators to digitize 5 pilot projects end-to-end to serve as the ML anchor.
