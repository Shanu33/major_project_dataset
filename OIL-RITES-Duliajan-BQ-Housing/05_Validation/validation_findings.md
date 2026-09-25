# Validation Findings & Engineering Audit Report

## 1. Truth Disclosure: Absence of Official Material BOQ Ground Truth
This project (`RITES/NERPO/OIL/BQ-HOUSING/25`) was tendered as an **EPC Mode-II Lump-Sum Component Contract**. 
The official tender documents contain **no itemized construction bill of quantities** for materials such as concrete volume, reinforcement steel weight, formwork surface area, or masonry quantity for a single tower.

Consequently:
- **Quantity validation coverage: 0%**
- **Quantity accuracy: NOT CALCULATED**
- **Cost accuracy: NOT CALCULATED**
- Reason: No independent itemized BOQ quantities or priced items available for the selected tower scope.
- All reported material quantities represent a **drawing-based engineering estimate** requiring reconciliation.

## 2. Macro Scope Consistency Checks

| Scope Parameter | Model Calculated | Official Tender Allocation | Consistency Status | Traceability Source |
| :--- | :--- | :--- | :--- | :--- |
| **Single Tower Plinth Area** | 3,419.38 sq.m | 3,419.38 sq.m | **PASS** | BoQ_3 Item 1.01 (27,355 sq.m ÷ 8) |
| **Dwelling Units per Tower** | 24 units | 24 units | **PASS** | DBR Section 1 & Architectural Plans |
| **Storey Count** | Stilt + 6 | Stilt + 6 | **PASS** | Tender Drawing Elevations AR/TD/010-013 |
| **Foundation Pile Count** | 207 piles | 207 piles | **PASS** | Direct count on Structural Sheet 100 |

## 3. Structural Benchmarking (Seismic Zone V)
Because independent BOQ material quantities do not exist, the drawing-based estimates were evaluated against standard Indian engineering benchmarks for mid-rise residential buildings in Seismic Zone V (\(Z = 0.36\)):

| Engineering Indicator | Model Result | Zone V Standard Benchmark | Benchmark Status | Remarks |
| :--- | :--- | :--- | :--- | :--- |
| **Superstructure Concrete Intensity** | 0.372 m³/sq.m | 0.35 – 0.40 m³/sq.m | REASONABLE_RANGE | Reflects mid-rise frame with ductile shear walls |
| **Overall Concrete Intensity (RCC)** | 0.766 m³/sq.m | 0.70 – 0.85 m³/sq.m | REASONABLE_RANGE | Driven by 207 deep bored piles (18m assumed depth) |
| **Superstructure Steel Intensity** | 135.41 kg/m³ | 125 – 145 kg/m³ | REASONABLE_RANGE | Captures IS 13920 ductile boundary elements |
| **Overall Steel Intensity** | 87.98 kg/sq.m | 80 – 95 kg/sq.m | REASONABLE_RANGE | Zone V seismic detailing and deep piling steel |
| **Masonry Intensity** | 0.182 m³/sq.m | 0.16 – 0.20 m³/sq.m | REASONABLE_RANGE | External 230mm + internal 115mm brick partitions |
| **Plaster Surface Ratio** | 4.34 m²/sq.m | 3.80 – 4.50 m²/sq.m | REASONABLE_RANGE | Internal wall/ceiling plus external double-coat plaster |

*Note: Benchmark compliance indicates engineering plausibility; it does not constitute official BOQ validation.*

## 4. Commercial Award Baseline
- **Official Award Record**: Awarded to **M/s Badri Rai & Company** as documented in the December 2025 RITES tender-dealt record (`status_of_Tender_dealt_Dec_2025_Badri_Rai_Award.pdf`).
- **Contract Award Value**: **₹128.14 Crore** (excluding GST).
- **Scheduled Completion**: **24 Months**.
- **Pro-Rata Benchmark**: ₹128.14 Crore ÷ 8 = ₹16.0175 Crore per tower (proportional project-level benchmark only; not a validated tower cost).
- **Direct Construction Cost Estimate**: ₹12.50 Crore (Takeoff quantities × estimated market rates, not contract-validated).
- **Cost Accuracy Verdict**: **NOT CALCULATED** (no official itemized priced BOQ available).
