# BOQ Data Quality & Contract Structure Audit Log

## 1. Official Tender BOQ Nature
- **Contract Type**: EPC Mode-II (Engineering, Procurement, and Construction on Lump-Sum Component Basis).
- **Price Schedule Document**: `BoQ_3_Plumbing_Sanitary_pdf-2025-Aug-28-17-28-6.pdf` (Items 1.01 to 1.10).
- **Primary Finding**: The official tender price schedule does NOT contain itemized bills of quantities for civil or structural works. There are NO itemized quantities for:
  - Concrete volumes (Piles, caps, columns, beams, slabs).
  - Reinforcement steel weights (diameter-wise or total).
  - Formwork / shuttering contact surface areas.
  - Brickwork / masonry volumes.
  - Plastering, painting, or flooring areas.

## 2. Scope Consistency Ground Truth
The tender BOQ establishes binding macro-level scope parameters:
- **Total Residential Plinth Area**: 27,355.00 sq.m across 8 towers.
- **Single Tower Plinth Area**: 3,419.38 sq.m (27,355 ÷ 8).
- **Dwelling Units per Tower**: 24 units across 6 typical residential floors (4 flats per floor).
- **Building Height Profile**: Stilt + 6 residential floors.

## 3. Ground Truth Integrity Enforcement
- **Zero False Validation Rule**: No quantity generated from drawings may be labeled as "BOQ-validated" or "BOQ ground truth match" for materials.
- **Classification**: All drawing-derived quantities are classified as `DRAWING_BASED_ESTIMATE`. Plinth area and unit count are classified as `SCOPE_CONSISTENCY_CHECK`.
