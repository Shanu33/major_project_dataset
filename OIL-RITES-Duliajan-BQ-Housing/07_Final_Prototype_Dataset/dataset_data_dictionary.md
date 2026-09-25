# Prototype Dataset Data Dictionary

## 1. Directory Structure Overview
```text
OIL-RITES-Duliajan-BQ-Housing/
├── 00_Project_Control/          # Project identity, selected scope lock, document registers, and audit
├── 01_Drawing_Registers/        # Complete architectural, structural, and MEP drawing sheet metadata
├── 02_Building_Element_Model/   # Parameterized geometry, architectural, structural, and finishes models
├── 03_Quantity_Takeoff/         # Comprehensive civil, concrete, rebar, masonry, finishes, and opening takeoffs
├── 04_BOQ_Ground_Truth/         # Official BOQ extractions, scope filter, tower allocation, and quality log
├── 05_Validation/               # Scope consistency checks, benchmark comparisons, and cost audit
├── 06_Labour_and_Duration/      # Labour productivity, manday estimates, CPM sequence, and duration analysis
├── 07_Final_Prototype_Dataset/  # Clean, self-contained, segregated prototype dataset release package
└── 09_Calculation_Audit/        # Calculation audit baseline, formula ledger, schedules, and evidence registers
```

## 2. File Manifest & Schema Description

### 2.1 Metadata & Input Specifications
- **`project_metadata.json`**: Official project parameters including tender references, client, executing agency, geographic coordinates, seismic parameters, contract award baseline (Badri Rai & Co., Dec 2025: ₹128.14 Crore excl. GST, 24 months), and scope demarcations.
- **`selected_tower_inputs.json`**: Fully resolved engineering input parameters for the isolated typical Stilt+6 residential tower (dimensions, unit areas, structural systems, materials).

### 2.2 Takeoff & Ground Truth Tables
- **`calculated_quantities_high_confidence.csv`**: Quantities restricted to 10 parameters with direct, unambiguous drawing evidence (plinth area, unit count, storey profile, footprint, pile count, pile diameter, column count, shear wall count, door count, window/vent count). No calculated material quantities (concrete, steel, masonry) are in this tier.
- **`calculated_quantities_estimated.csv`**: Quantities where key geometric parameters (e.g. assumed pile depth 18m from DBR range, assumed pile cap depth 1.0m, unresolved 54 vs 84 cap count, OHT details) required engineering assumptions.
- **`calculated_quantities_unsupported.csv`**: Elements with no sheet-level schedules or specifications (false ceiling, specialized wall panelling).
- **`calculated_quantities.csv`**: Master consolidated material quantities across core civil and architectural trades.
- **`boq_ground_truth.csv`**: Official extractions from the master EPC pricing schedule (BoQ_3), showing project scope and exact 1/8th mathematical allocation of macro scope parameters to the typical tower.
- **`validated_items.csv`**: Audit table recording scope consistency checks against official tender allocations and benchmark checks against Indian standard ranges.
- **`excluded_items.csv`**: Comprehensive register of non-tower items (7 identical towers, Guest House, Community Centre, Substation, STP, UGT, boundary walls, and historical 2020 files) with exclusion rationales.
- **`assumptions_log.csv`**: Formalized register of engineering assumptions, citations, standard references, and sensitivity ratings.

### 2.3 Calculation Audit Registers (`09_Calculation_Audit/`)
- **`baseline_file_inventory.csv`**: Audit of all 22 baseline files with status (`RETAINED`, `CORRECTED`, `SUPERSEDED`).
- **`formula_ledger.csv`**: Mathematical equations replacing generic text with exact formulas for all element takeoffs.
- **`source_evidence_register.csv`**: Direct mapping of all takeoff inputs to drawing sheets, callouts, and PDF page numbers.
- **`calculation_audit_log.csv`**: Discrepancy tracking of original claims, audit findings, and revised classifications.
- **`pile_schedule_audit.csv`**: Audit of 207 bored cast-in-situ piles with depth derivation from DBR/Geotech reports.
- **`pile_cap_schedule_audit.csv`**: Records the unresolved pile cap contradiction: preliminary 84-cap summary vs 54 counted cap entities / unresolved pile allocation. It is not a validated cap schedule.
- **`column_wall_height_schedule.csv`**: Detailed height and volume schedule for C1-C3 and SW1-SW10 across 7 levels.
- **`beam_length_schedule.csv`**: Detailed span and cross-section schedule for plinth, typical floor, and terrace beams.
- **`slab_area_schedule.csv`**: Net slab area and volume schedule excluding vertical shaft voids.
- **`staircase_oht_schedule.csv`**: Concrete volume and rebar schedules for doglegged stairs, mumty, and water tank.
- **`rebar_bar_mark_schedule.csv`**: Element-by-element bar mark schedule detailing diameter, counts, cut lengths, and weights.
- **`rebar_cut_length_calculations.csv`**: Cut length derivations incorporating clear spans, anchorage, and bend deductions.
- **`rebar_lap_development_length_register.csv`**: Tension and compression development lengths and lap requirements per IS 456 / IS 13920.
- **`rebar_weight_summary.csv`**: Diameter-wise weight summary segregated by confidence tier.
- **`architectural_quantity_readiness.csv`**: Assessment of masonry, plaster, flooring, and opening quantities.

### 2.4 Field Naming Standards
- `Quantity ID` / `Element ID` / `Item ID`: Unique alphanumeric identifier tracking each element across models.
- `Takeoff Result` / `Takeoff Value`: Unrounded calculated physical quantity derived from drawings.
- `Unit`: Standard SI / Indian engineering units (`m`, `sq.m`, `m3`, `MT`, `kg`, `nos`).
- `Concrete Grade`: Design characteristic compressive strength at 28 days (`M10`, `M30`).
- `Steel Grade`: Yield strength specification (`Fe 500D`, `Fe 550D`).
- `Confidence Classification`: Rigorous classification of data provenance. Only 10 directly-measured drawing parameters qualify as `HIGH` (renamed from `HIGH_CONFIDENCE`). Derived quantities are classified as `MEDIUM`, `ESTIMATED`, or `ASSUMPTION_REQUIRED`. No assumption may be classified HIGH.
