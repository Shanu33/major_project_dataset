# Missing Data Impact Analysis

## Overview
The primary missing data across the corpus is machine-readable BOQs and structural framing drawings.

## Impact on ML Models
- **Quantity Model**: Severely impacted. Cannot establish ground-truth labels without BOQ.
- **Cost Model**: Blocked. Item rates are locked in PDFs.
- **Schedule Model**: Impacted. Need BOQ to correlate with duration.
