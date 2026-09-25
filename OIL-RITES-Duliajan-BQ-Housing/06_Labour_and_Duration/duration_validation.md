# Construction Schedule & Duration Validation

## Status: NOT CALCULATED

The construction schedule and duration model for this pilot dataset have **NOT been validated** and are **NOT ready for use**.

### Official Duration Baseline
- **Full Contract Package Duration**: **24 months** per December 2025 RITES tender-dealt record (`status_of_Tender_dealt_Dec_2025_Badri_Rai_Award.pdf`).
- **Prior Figure**: The earlier DBR/media figure of 36 months is superseded by the official award record.
- **Single Tower Duration**: **NOT CALCULATED**. No independent single-tower critical path analysis has been performed or validated.

### Why Duration Modelling Is Not Ready
1. **Unresolved Foundation Contradiction**: The 54-cap vs 84-cap pile cap discrepancy impacts foundation milestone scheduling.
2. **Absence of Official BBS**: Without bar bending schedules, rebar fixing labour mandays cannot be calculated deterministically.
3. **No Validated Productivity Benchmarks**: Gang productivity rates used in the preliminary labour estimate are assumed, not benchmarked to this project.
4. **No Official Construction Programme**: The contractor's approved construction programme / bar chart has not been obtained.

### Preliminary Data (Reference Only — NOT for Model Training)
The files `labour_estimate.csv` and `duration_estimate.csv` in this folder contain preliminary parametric estimates that were generated before the calculation audit. They use assumed productivity rates and an assumed 15-month tower duration that is **NOT validated**.

These files are retained for reference only and must NOT be used for model training, cost estimation, or scheduling decisions.
