# Duliajan v2 Verified Estimation-Readiness Audit

## 1. Release Scope and Controlling Sources

This audit report governs the release of the verified estimation-readiness package for exactly **ONE typical Stilt+6 BQ residential tower** (Blocks A–H typical) within the OIL/RITES Workman Housing Complex at Duliajan, Assam.

All findings, parameters, and classifications in this release are derived strictly and exclusively from the following allowed authoritative sources:

1. `07_Final_Prototype_Dataset/project_metadata.json`
2. `07_Final_Prototype_Dataset/selected_tower_inputs.json`
3. `07_Final_Prototype_Dataset/final_project_audit.md`
4. `07_Final_Prototype_Dataset/dataset_data_dictionary.md`
5. `07_Final_Prototype_Dataset/calculated_quantities_high_confidence.csv`
6. `09_Calculation_Audit/source_evidence_register.csv`
7. `09_Calculation_Audit/pile_cap_schedule_audit.csv`
8. `09_Calculation_Audit/formula_ledger.csv`
9. `10_Controlled_Transcription/*.csv`
10. `11_Estimation_Readiness/v2_verified_release/estimation_input_master_v2.csv`
11. `11_Estimation_Readiness/v2_verified_release/opening_schedule_reconciliation.csv`
12. `11_Estimation_Readiness/v2_verified_release/legacy_model_quarantine_register.csv`
13. `11_Estimation_Readiness/v2_verified_release/missing_evidence_request_register_v2.csv`

Any parameter, rate, or figure not explicitly substantiated in these controlling files is strictly excluded from this release.

---

## 2. Verified Project Identity and Scope

The verified project parameters established by official tender and execution records are summarized below:

| Field | Verified Value | Source |
|---|---|---|
| Project Title | Construction of Workman Housing Complex (BQ Area) on EPC Mode-II of Contract at OIL Duliajan, Assam | `project_metadata.json` |
| Client | Oil India Limited (OIL) | `project_metadata.json` |
| Executing Agency | RITES Limited (A Govt. of India Enterprise, Tender Cell-NERPO) | `project_metadata.json` |
| Tender Reference | RITES/NERPO/OIL/BQ-HOUSING/25 (CPP Tender ID: 2025_RITES_246752_1) | `project_metadata.json` |
| Contract Type | EPC Mode-II (Lump Sum Component Basis) | `project_metadata.json` |
| Awarded Contractor | M/s Badri Rai & Company | `project_metadata.json`, `status_of_Tender_dealt_Dec_2025_Badri_Rai_Award.pdf` |
| Project Location | Duliajan, Dibrugarh District, Assam (Seismic Zone V, Z = 0.36; Basic Wind Speed 50 m/s) | `project_metadata.json` |
| Target Model Scope | Exactly ONE Typical Stilt+6 Residential Workmen Housing Tower (Block A–H) | `project_metadata.json`, `selected_tower_inputs.json` |
| Tower Plinth Area | 3,419.38 sq.m (Stilt 483.60 sq.m + 6 Floors × 483.60 sq.m + Mumty 34.18 sq.m) | `project_metadata.json`, `selected_tower_inputs.json`, `final_project_audit.md` |
| Tower Footprint | 30.08 m × 16.08 m = 483.60 sq.m | `selected_tower_inputs.json`, `final_project_audit.md` |
| Dwelling Units | 24 total (Type-2BHK: 4 units/floor × 6 residential floors; carpet area 69.0 sq.m/unit) | `project_metadata.json`, `selected_tower_inputs.json` |
| Whole-Project Contract Award | ₹128.14 crore (excluding GST) | `project_metadata.json`, `final_project_audit.md` |
| Whole-Project Contract Duration | 24 months | `project_metadata.json`, `final_project_audit.md` |

### Explicit Contractual Distinctions
- **₹128.14 crore** is a whole-project EPC contract award figure covering the complete campus scope (8 residential towers, guest house, community centre, electrical substation, guard rooms, boundary wall, and 24,675 sq.m of external site development).
- **₹16.0175 crore** is strictly a rough mathematical 1/8 benchmark (₹128.14 crore ÷ 8 towers).
- **Neither figure is a validated tower construction cost.** Single-tower cost is NOT VALIDATED against official contract billing, and cost accuracy remains NOT CALCULATED.

---

## 3. Evidence Classification Framework

All parameters across the estimation-readiness package are classified into six explicit evidentiary categories:

1. **Direct Source Observation:** Verifiable data points extracted directly from drawings, schedules, project specifications, or official contract award records with explicit physical or textual evidence.
2. **Derived Input:** Quantities calculated directly from verified source dimensions via deterministic mathematical operations (e.g., unit counts multiplied by standard floor areas).
3. **Estimate:** Engineering quantities calculated using assumed typical sections, centerline approximations, or empirical ratios that require full CAD extraction or structural shop schedules for confirmation.
4. **Assumption-Required Input:** Values that depend upon unconfirmed engineering assumptions (e.g., assumed pile termination depth within a reported range, assumed leveling course thickness).
5. **Unresolved Contradiction:** Parameters where two or more authoritative project records present mutually conflicting data that cannot be resolved without written designer clarification.
6. **Quarantined Legacy Calculation:** Historical or preliminary outputs (such as ungrounded labour productivity figures or single-tower duration schedules) that fail evidentiary audit standards and are strictly prohibited from use.

---

## 4. Locked High-Confidence Macro Inputs

In strict alignment with `07_Final_Prototype_Dataset/final_project_audit.md`, exactly **10 macro parameter groups** are locked as direct high-confidence evidence:

1. **Tower plinth area:** 3,419.38 sq.m (Item 1.01 in BoQ_3: 27,355 sq.m total residential plinth area ÷ 8 towers).
2. **Dwelling-unit count:** 24 units total (4 units per floor across 6 residential floors).
3. **Storey profile:** Stilt + 6 floors (plus rooftop stair mumty).
4. **Footprint dimensions:** 30.08 m length × 16.08 m width = 483.60 sq.m gross area.
5. **Pile count:** 207 bored cast-in-situ RCC piles counted on Sheet STR/TD/100 layout plan.
6. **Pile diameter:** 600 mm directly scheduled on Sheet STR/TD/100 notes.
7. **Column count:** 16 columns per typical level (4 C1: 1200×350 mm, 8 C2: 1200×300 mm, 4 C3: 1200×300 mm scheduled on Sheet STR/TD/104).
8. **Shear-wall count:** 33 ductile shear wall legs (12 SW1, 4 SW2, 4 SW3, 4 SW4, 4 SW5, 5 CW scheduled on Sheet STR/TD/104).
9. **Door count:** 216 scheduled flush door assemblies (48 D1, 96 D2, 72 D3 on Sheet AR/TD/005 schedule).
10. **Window/ventilator count:** 168 scheduled units (W1–W4 windows and V1–V2 ventilators on Sheet AR/TD/005 schedule).

> [!IMPORTANT]
> **Governance Note on Master-Register Mapping:**
> The master input register (`estimation_input_master_v2.csv`) contains 12 rows marked `is_one_of_10_locked_high_confidence_macro_parameters = YES`. These 12 rows map directly to the **10 macro groups** listed above because the building footprint geometry is represented across three distinct constituent rows: footprint length (30.08 m), footprint width (16.08 m), and gross footprint area (483.60 sq.m).
>
> These 10 locked groups represent reliable project scope and boundary geometry. **They are not independently validated material quantities.**

---

## 5. Direct Drawing Inputs That Are Not Quantity Ground Truth

Direct observations visible on tender drawings—such as structural dimensions, concrete grade M30 for RCC, lean concrete grade M10 for PCC, reinforcement grades Fe 500D / Fe 550D TMT, member cross-sections, opening schedules, and notes—provide critical engineering criteria.

However, direct drawing callouts **cannot validate** material quantity takeoffs:
- Stating concrete grade M30 does not validate total cubic meters of concrete.
- Specifying rebar grade Fe 500D / Fe 550D does not validate structural steel tonnage.
- Specifying 230 mm external brick masonry in CM 1:6 and 115 mm internal brick masonry in CM 1:4 does not validate net masonry volumes without CAD wall-centerline extraction and door/window opening deductions.
- Listing opening schedules does not validate formwork shuttering, plaster, or paint areas.
- None of these direct drawing specifications validate site labour hours, single-tower duration, or single-tower cost.

---

## 6. Opening-Schedule Reconciliation

The opening dimensions in this release are strictly governed by `11_Estimation_Readiness/v2_verified_release/opening_schedule_reconciliation.csv`, which reconciles the conflicting figures found in older prototype records:

- **D1 (Toilet Flush Door):** Corrected to **800 × 2100 mm** ($1.680\text{ sq.m}$) per Sheet AR/TD/005 (replaces the older inverted record of 1000 × 2100 mm).
- **D2 (Bedroom & Internal Door):** Corrected to **1000 × 2100 mm** ($2.100\text{ sq.m}$) per Sheet AR/TD/005 (replaces the older record of 900 × 2100 mm).
- **D3 (Main Entrance Door):** Corrected to **1050 × 2100 mm** ($2.205\text{ sq.m}$) per Sheet AR/TD/005 (replaces the older record of 750 × 2100 mm).

In addition, the v2 reconciliation cataloged specialized assemblies previously omitted from door summaries (DW1 balcony combo: 2000 × 2100 mm; DW2 alternate balcony combo: 2295 × 2100 mm; SD1 electrical shaft door: 900 × 2100 mm; SD2 plumbing shaft door: 600 × 2100 mm per schedule with 2000 mm detail variance noted; SD3 fire hose cabinet door: 900 × 2100 mm; SD4 mumty door: 1200 × 2100 mm) as well as concordant windows (W1–W4) and ventilators (V1–V2).

> [!NOTE]
> These corrections replace only the conflicting opening dimensions in older prototype files. **This dimensional correction does not validate masonry quantities**, because net wall takeoff requires verified CAD wall-centerline runs, floor-by-floor lintel schedules, and structural member deductions.

---

## 7. Blocked Estimation Outputs

The table below details all downstream estimation outputs whose release is currently blocked due to missing records or evidentiary contradictions:

| Output | Status | Why Blocked |
|---|---|---|
| Pile concrete and reinforcement | BLOCKED | 207 piles counted, but depth is not scheduled on drawings; relies on an assumed 18 m pile depth (derived from DBR range 15–20 m, ASM-001); reinforcement cage detailing and cut-off levels are missing. |
| Pile-cap concrete and reinforcement | BLOCKED | Critical unresolved contradiction between 54 cap entities visible on Sheet STR/TD/101 layout plan and 84 caps reported in preliminary summaries; 91 piles remain unallocated under continuous strip caps; cap thickness schedule missing. The 54-cap-entity observation is sourced from Sheet STR/TD/101; Sheet STR/TD/100 remains the governing source for the 207-pile count and 600 mm pile diameter. |
| Beam/slab quantities | BLOCKED | Member-wise beam/slab schedule absence; relies on gross centerline run (403.5 m) and assumed weighted average thickness (130 mm); beam-column joints and slab ribs not deduplicated. |
| Total concrete | BLOCKED | Substructure and superstructure quantities rely on unverified depth assumptions, unresolved cap contradictions, and average member sections; item-wise material BOQ validation coverage is strictly 0%. |
| Total steel | BLOCKED | Absence of contractor Bar Bending Schedule (BBS); all rebar weights rely on assumed parametric steel intensities (e.g., 89.17 to 140 kg/m³) or formula approximations (50d lap rule). |
| Masonry and finishes | BLOCKED | Lacks dimensioned wall-centerline layout plan and room finish schedule; relies on gross room perimeters and synthetic opening deduction ratios (ASM-007: 23%, ASM-008: 10%). |
| Single-tower cost | BLOCKED | Missing itemized EPC cost breakdown or priced BOQ for single tower; ₹128.14 crore is a whole-project award; ₹16.0175 crore is only a rough 1/8 mathematical benchmark; 0% BOQ validation. |
| Labour mandays | BLOCKED | Quarantined legacy calculation (11,298 mandays); ungrounded parametric gang productivity ratios without contractor muster rolls or site productivity logs. |
| Single-tower duration | BLOCKED | Single-tower duration is NOT CALCULATED; the 24-month contract duration applies strictly to the complete 8-tower complex plus campus scope; no single-tower critical path method (CPM) schedule exists. |

---

## 8. Legacy Labour and Duration Quarantine

All historical labour and duration estimates have been subjected to formal quarantine under `11_Estimation_Readiness/v2_verified_release/legacy_model_quarantine_register.csv`:

- **Quarantine of `labour_estimate.csv`:** The legacy calculation in `06_Labour_and_Duration/labour_estimate.csv` totaling **11,298 mandays** is formally quarantined (`LEGACY_UNVALIDATED`).
- **Prohibition on Use:** The preliminary figure of 11,298 mandays is only a quarantined legacy calculation. It **may not be used** for machine learning training, ground truth validation, productivity benchmarking, cost estimation, or schedule generation.
- **Contract Duration Boundary:** The **24 months** completion period is valid only as a contractual fact for the complete 8-tower EPC package and campus infrastructure.
- **Single-Tower Duration:** Independent construction duration for a single tower is **NOT CALCULATED**. No critical path model or construction logic network has been evaluated.

---

## 9. Priority Evidence Recovery Plan

To systematically resolve blocked outputs, eight Requests for Information (RFIs) are established in `11_Estimation_Readiness/v2_verified_release/missing_evidence_request_register_v2.csv`, strictly adhering to the prioritized order below:

### Priority 1: Mandatory Prerequisites for Deterministic Quantity Modeling
- **`REQ-V2-001` (Pile Schedule & Founding/Termination Levels):** Approved pile termination depth, founding stratum reduced level, cut-off elevation, and pile cage detailing for each of the 207 bored cast-in-situ piles.
- **`REQ-V2-002` (Pile-Cap GA & Schedule):** Approved foundation general arrangement resolving the 54 layout entities visible on Sheet STR/TD/101 versus 84 summary caps contradiction, establishing boundary dimensions (L × W × D) and allocating all 91 strip-cap piles.
- **`REQ-V2-003` (Contractor BBS / Shop Drawings):** Approved Bar Bending Schedule (BBS) and structural shop drawings per IS 2502 detailing bar marks, cut lengths, bending schedules, and lap staggering for all structural members.

### Priority 2: Prerequisites for Superstructure and Architectural Finishing Takeoff
- **`REQ-V2-004` (Beam and Slab Schedules):** Member-wise schedules with clear spans, cross-sections, and panel-by-panel slab layouts to eliminate beam-column joint deduplication errors.
- **`REQ-V2-005` (Wall-Centreline and Finish Schedule):** Dimensioned architectural working drawings with wall centerlines, column block-outs, lintel/sill levels, and room-by-room finish specifications.
- **`REQ-V2-006` (Approved Baseline Programme):** Contractor approved baseline construction master programme (Primavera P6 / MS Project) showing single-tower activity logic, structural cycle times, and crew allocations.
- **`REQ-V2-007` (OHT Detailing):** Rooftop Overhead Water Tank structural detailing, wall thicknesses, base slab sections, and IS 3370 reinforcement schedules.

### Priority 3: Commercial & Contractual Pricing Reconciliation
- **`REQ-V2-008` (Itemized EPC Cost Breakdown):** Approved trade-wise and component billing break-up for a single typical residential tower within the ₹128.14 crore EPC contract award.

---

## 10. Final Readiness Verdict

The Duliajan v2 release is a governed engineering-input baseline. It is useful for provenance-controlled extraction and future deterministic takeoff after missing engineering records are obtained. It is not a validated material-estimation, cost-estimation, labour-estimation, duration-estimation, or ML-training dataset.

---

### QA confirmation
- prohibited-value scan: PASS
- authoritative-source-only audit: PASS
- no original tender/drawing files modified: PASS
