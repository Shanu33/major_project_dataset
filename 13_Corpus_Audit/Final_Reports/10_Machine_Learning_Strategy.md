# Final ML Strategy

## 1. Domain Constraint
Restrict initial models to Indian PSU residential construction only (G+1 to G+25). Do not mix with commercial or private datasets.

## 2. Model Architecture
Use a dual-tower approach:
- **Tower A (Geometry)**: Takes architectural footprint, storeys, and plinth area.
- **Tower B (Specs)**: Takes categorical variables (foundation type, location).
Output heads: Total Cost, Concrete Volume, Steel Tonnage, Labour Mandays.

## 3. Next Steps
Do not begin model training. The immediate next action must be deploying OCR/tabular extraction tools against the Track A BOQ PDFs to unblock the label pipeline.
