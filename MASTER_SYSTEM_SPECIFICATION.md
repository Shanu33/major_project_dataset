# MASTER SYSTEM SPECIFICATION
# Construction Intelligence + Estimation + Resource Planning + Site Monitoring System

---

## 1. Executive Summary

This document specifies the complete architecture for a **Construction Intelligence System** that combines document processing, deterministic engineering calculations, rule-based estimation, resource planning, and daily site monitoring into a unified platform for Indian construction projects.

The system targets two distinct operational modes:
1. **Estimation Mode** (No initial BOQ)
2. **BOQ Validation & Reconciliation Mode** (BOQ provided as ground truth)

**Current Dataset Assessment:** The existing dataset (3 independent projects, 58 elements, effectively 4-5 unique observations) is strictly **insufficient** for any supervised ML training. The system is designed to use deterministic engineering calculations and configurable rule-based norms as its primary estimation engine. Machine learning is architected purely as a **future supplementary capability** that will only be activated when sufficient, diverse, and independent project data accumulates. The core monitoring, evidence, and audit subsystems operate entirely without ML and provide immediate production value.

---

## 2. Dual-Mode Architecture

### Mode A: ESTIMATION MODE
- **Purpose:** Generate a complete project estimate when an official BOQ does not yet exist or is not provided.
- **Inputs:** Architectural/structural drawings, specifications, project/site information, and geotechnical reports.
- **Outputs:** Deterministic engineering quantities, rule-based resource plans, estimated schedules, and estimated costs (where supported by rates).
- **Validation:** Relies on human supervisor review and baseline confirmation.

### Mode B: BOQ VALIDATION / RECONCILIATION MODE
- **Purpose:** Validate contractor/system quantities against an official project BOQ.
- **Inputs:** All Mode A inputs + **Uploaded Official BOQ/Measurement Sheet**.
- **Process:** System compares extracted and deterministically calculated quantities against BOQ line items.
- **Outputs:** Delta reports, discrepancy flags, and explicitly verified Drawing-to-BOQ mappings.
- **ML Benefit:** Confirmed mappings provide reliable observed ground truth (Y) for future ML datasets.

---

## 3. Current Dataset Audit

### 3.1 Data Actually Present in Files

**CRITICAL FINDING: The "58 verified elements" claim requires significant qualification.**

| Project | Elements | Element Types | X Features Available | Y Target Available | Status |
| :--- | ---: | :--- | :--- | :--- | :--- |
| OIL-RITES-Duliajan | 54 | Footing only | L=1.5, W=1.5, D=0.4 (ALL IDENTICAL) | concrete_quantity=0.9 m³ (ALL IDENTICAL) | **Zero variance** |
| NIT-Nalanda | 1 | Pile only | diameter=0.6, L=12.7, W=UNKNOWN | AGGREGATE_BOQ (51259 running metres, NOT element-level) | **Target not element-level** |
| TCIL-Azamgarh | 3 | Building footprint, CC pavement, Kerb stone | Mixed dimensions | 2 of 3 have targets (5.25, 1.35 m³); 1 NEEDS_BOQ_MAPPING | **Partially mapped** |
| **TOTAL** | **58** | | | | |

### 3.2 Critical Data Quality Issues

1. **Duliajan: Zero Feature Variance.** All 54 footings have IDENTICAL dimensions (1.5 × 1.5 × 0.4 m) and IDENTICAL target values (0.9 m³). Statistically, this is **1 unique observation repeated 54 times**, not 54 independent samples. The deterministic formula $V = L \times W \times D$ perfectly explains the target.
2. **NIT-Nalanda: Target Mismatch.** The BOQ quantity is an aggregate across all piles, not the concrete volume of a single pile.
3. **TCIL-Azamgarh: Mixed Granularity.** Only 2 elements have BOQ-mapped concrete targets.

### 3.3 Honest Element Count

| Metric | Actual Unique |
| :--- | ---: |
| Independent projects | 3 |
| Total element rows | 58 |
| Distinct feature vectors | **5** |
| Unique (X,Y) observations | **~4** |

**Conclusion:** The dataset has effectively **4–5 unique data points** across 3 projects. This confirms the ML status is firmly **NOT_TRAINABLE**.

---

## 4. Current ML Feasibility

| Prediction Task | Unique X→Y Pairs | ML Feasible? | Recommended Primary Method |
| :--- | ---: | :--- | :--- |
| Concrete quantity (element) | ~4 | **NO** | Deterministic ($V = L \times W \times D$) |
| Steel/rebar quantity | 0 | **NO** | Deterministic (BBS) / Rule-based |
| Labour hours | 0 | **NO** | Rule-based (Productivity norms) |
| Cost estimation | 0 | **NO** | Deterministic (Rate × Quantity) |
| Duration | 0 | **NO** | Deterministic (CPM scheduling) |

**ML Status: NOT_TRAINABLE.**

**Future ML Activation Criteria (Internal Checkpoint):**
A sample size like "20 observations from 5 projects" is merely an internal software checkpoint, **not** a universal statistical guarantee. Actual ML readiness will be evaluated dynamically based on:
1. Strict independent-project count boundaries.
2. Sufficient feature and target variance (preventing Duliajan-style zero-variance collapse).
3. Wide target coverage across multiple element types.
4. Absolute passage of data leakage audits.
5. Demonstrated feasibility of GroupKFold validation showing improvement over deterministic baselines.

---

## 5. User Roles & Personas

**MVP Roles (Strictly Enforced):**
1. **Admin**: System configuration, master data, user management, global audit logs.
2. **Contractor**: Creates projects, uploads documents, reviews estimates, submits daily reports.
3. **Supervisor**: Verifies daily reports, reviews baseline freezes, records actual progress, manages discrepancies.

*(Note: Government Authority, Quantity Surveyor, and Client roles are explicitly deferred to post-MVP.)*

---

## 6. Immutable Reporting Model

The core of the system is the **immutable reporting model**.
- A Contractor's submitted values are permanently recorded.
- A Supervisor's verified/corrected values are permanently recorded.
- **A Supervisor's correction NEVER silently overwrites a Contractor's submission.** Both values exist simultaneously, creating a deliberate discrepancy flag that must be resolved via the audit workflow.

---

## 7. Dual-Mode User Journey & Baseline Freeze

```
STEP 1: Contractor creates project and selects MODE (Estimation vs BOQ Validation)
         ↓
STEP 2: Uploads inputs (Drawings, Specs, Site info. Mode B also requires BOQ)
         ↓
STEP 3: Document Intelligence extracts parameters
         ↓
STEP 4: Engineering Engine runs (Deterministic Calculations & Rule-Based Assumptions)
         ↓
STEP 5: (Mode B Only) Reconciliation engine flags deltas against official BOQ
         ↓
STEP 6: Contractor reviews Estimation/Reconciliation Report
         ↓
STEP 7: System generates Resource Plan and CPM Schedule
         ↓
STEP 8: 🔒 BASELINE FREEZE (Contractor & Supervisor Confirmation)
        [Original baseline is permanently locked. Any future changes require a new Revision]
         ↓
STEP 9: Daily Monitoring Loop Begins (Revision-Aware Plan vs Actual)
```

---

## 8. Input Specification

### Mode A: Estimation Mode Inputs
- **Required:** Structural drawings, Architectural drawings, Project metadata (Type, Location, Start Date).
- **Optional:** Technical specifications, Geotechnical reports.
- **NOT Required:** BOQ.

### Mode B: BOQ Validation Mode Inputs
- **Required:** All Mode A requirements + **Official Priced or Unpriced BOQ (PDF/Excel/CSV)**.

---

## 9. Output Specification & Capabilities

The system does NOT automatically estimate every construction material. Outputs are strictly classified:

### 1. Directly Computable Outputs
*High confidence, mathematically derived.*
- **Concrete volume per element:** $V = L \times W \times D$
- **Brickwork/Blockwork volume:** Wall area $\times$ thickness
- **Plastering/Painting area:** Surface geometry
- **Plan vs Actual delta:** Simple arithmetic difference

### 2. Rule/Standard Dependent Outputs
*Medium confidence, labeled as `ASSUMPTION_BASED`.*
- **Labour hours:** Derived from CPWD productivity norms.
- **Activity duration:** Derived from labour availability and productivity norms.
- **Standard material waste:** Industry standard percentages.

### 3. Document/Specification Dependent Outputs
*Confidence depends entirely on extraction quality.*
- **Concrete Grade / Steel Grade:** Extracted from General Notes.
- **Specialized finishes:** Extracted from architectural specs.

### 4. Unsupported Without Additional Information
*Cannot be reliably estimated from basic geometry.*
- **Complex MEP components:** HVAC ducting, specialized electrical runs.
- **Sub-soil stabilization:** Depends entirely on missing geotechnical data.
- **Temporary works / Formwork complexity:** Unless explicitly modeled.

---

## 10. Deterministic Engineering Layer

### 10.1 Concrete Mix Logic
The system **does not** hard-code nominal ratios (e.g., 1:1.5:3) as universal engineering truth.
1. **IF** a project-approved design mix document is uploaded $\to$ System uses exact design mix ratios.
2. **ELSE** $\to$ System uses configurable standard assumptions based on grade (e.g., CPWD nominal mix) and permanently labels the output as `ASSUMPTION_BASED`.

### 10.2 Reinforcement Steel Logic
1. **IF** Bar Bending Schedule (BBS) is available $\to$ **Calculated** (Length $\times$ Unit Weight).
2. **ELSE IF** sufficient structural detailing/sections are readable $\to$ **Derived** via direct bar counting.
3. **ELSE IF** only element geometry is known $\to$ **Assumption-Based** (Estimated via configurable steel intensity ratios, e.g., 100 kg/m³).
4. **ELSE** $\to$ **Cannot reliably estimate**.

---

## 11. Revision-Aware Baseline Freeze

Once an estimation and schedule are approved, the **Baseline Freeze** occurs.
- The original planned quantities, costs, and durations are locked.
- If scope changes or errors are found during execution, a **Revision** is created.
- The Plan vs Actual dashboard evaluates against the *Active Revision*, but the *Original Baseline* is preserved forever.
- Revisions track: Who changed it, When it changed, and Why (Reason code).

---

## 12. Daily Monitoring & Discrepancy Detection

### Plan vs Actual Dashboard
The dashboard compares:
- Original Baseline vs Active Revision vs Actual Execution.

### Discrepancy Workflow
```
Contractor reports:  Completed Volume = 15 m³
Supervisor verifies: Completed Volume = 12 m³
                     ─────────────────────────────
System records:      Discrepancy = 3 m³ (STATUS = DISPUTED)
                     Both values preserved immutably.
```

---

## 13. ML Layer (Future Capability)

ML is **NOT currently trained, accurate, or deployable**. It is a future mechanism for estimating parameters where deterministic formulas fail (e.g., true waste percentages, complex productivity factors).

- **Always compare against:** Deterministic engineering baseline. If ML cannot beat the deterministic formula or a simple rule-based norm, it is not deployed.
- **Uncertainty:** Any future ML output must be explicitly labeled `EXPERIMENTAL_ML` with its specific assumptions listed.

---

## 14. Database Architecture (Key Updates for Revisions)

```sql
-- Project Baselines
CREATE TABLE project_baselines (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    revision_number INTEGER DEFAULT 0,
    frozen_by UUID REFERENCES users(id),
    frozen_at TIMESTAMP DEFAULT NOW(),
    reason_for_revision TEXT,
    is_active BOOLEAN DEFAULT true
);

-- Material Plans (Revision Aware)
CREATE TABLE material_plans (
    id UUID PRIMARY KEY,
    baseline_id UUID REFERENCES project_baselines(id),
    material_name VARCHAR NOT NULL,
    planned_quantity FLOAT,
    estimation_method ENUM('calculated','derived','assumption_based','user_provided')
);

-- Daily Reports (Immutable)
CREATE TABLE daily_reports (
    id UUID PRIMARY KEY,
    project_id UUID,
    submitted_by UUID REFERENCES users(id),
    contractor_declared_work JSONB,  -- Never overwritten
    submitted_at TIMESTAMP
);

-- Report Verification (Immutable)
CREATE TABLE report_verifications (
    id UUID PRIMARY KEY,
    daily_report_id UUID REFERENCES daily_reports(id),
    verified_by UUID REFERENCES users(id),
    supervisor_verified_work JSONB,  -- Stored alongside contractor data
    status ENUM('approved','rejected','disputed'),
    verified_at TIMESTAMP
);
```

---

## 15. Testing & Validation Strategy

| Test Type | Scope |
| :--- | :--- |
| **Unit tests** | Deterministic formulas, volume math, revision locking |
| **Integration** | Immutable reporting logic (ensure Supervisor cannot overwrite Contractor) |
| **Validation** | Feature-target leakage checks |

---

## 16. FINAL ARCHITECTURAL PRINCIPLES

The system architecture is governed by these uncompromising principles:

1. **Document Intelligence** (Extraction of explicit textual/visual facts)
2. **+ Deterministic Engineering** (Calculation using universal physical laws)
3. **+ Rule-Based Estimation** (Configurable norms, explicitly labeled as assumptions)
4. **+ Optional Future ML** (Strictly supplementary, deployed only if it beats baselines)
5. **+ Resource Planning** (Deterministic CPM scheduling and gang calculation)
6. **+ Baseline Freeze** (Revision-aware locking of project plans)
7. **+ Daily Monitoring** (Tracking actuals against active baselines)
8. **+ Supervisor Verification** (Independent oversight of site reports)
9. **+ Evidence** (Cryptographically hashed visual/documentary proof)
10. **+ Immutable Audit Trail** (Preservation of all historical states without silent overwrites)
11. **+ Human Decision Authority** (The system supports decisions; humans authorize them)

---

## 17. PHASE 1K: DETERMINISTIC COST ESTIMATION & RATE-BASED VALUATION

### 17.1 Purpose & Mathematical Formula
Deterministic, auditable cost calculation:
$$\text{total\_cost} = \text{quantity\_value} \times \text{rate\_value}$$

Evaluated using exact `Decimal` precision quantized to 6 decimal places (`0.000001`).

### 17.2 Architecture & Data Model
- **`cost_rates`**: Rate catalog supporting global schedules (`project_id IS NULL`) and project-specific rates (`project_id IS NOT NULL`).
  - Source Types: `OFFICIAL_SCHEDULE`, `PROJECT_SPECIFIC`, `USER_PROVIDED`, `ASSUMPTION_BASED`.
  - Lifecycle: `DRAFT -> CONFIRMED -> SUPERSEDED`.
  - Versioning: `replaces_rate_id` atomically supersedes previous versions upon confirmation.
  - Logical Identity: Partial unique indexes guarantee at most one active confirmed rate per `(project_id, rate_code)` or `rate_code` (global).
- **`cost_calculations`**: Immutable valuation snapshots.
  - Quantity Bases:
    - `BOQ_STATED`: Stated quantities from confirmed BOQ line items.
    - `ENGINEERING_CALCULATED`: Calculated quantities from engineering calculations.
    - `VERIFIED_RECONCILED`: Reconciled quantities from verified supervisor reconciliations with explicit decision models (`ACCEPT_MATCH`, `ACCEPT_CALCULATED`, `ACCEPT_BOQ`).
  - Lifecycle: `CALCULATED -> SUPERSEDED`.
  - Logical Identity: Partial unique indexes guarantee 1:1 active calculation identity per source entity.

### 17.3 Database-Level Invariants
1. `ck_cost_rates_rate_val_nonneg`, `ck_cost_calc_qty_val_nonneg`, `ck_cost_calc_rate_val_nonneg`, `ck_cost_calc_total_cost_nonneg`: Non-negative math.
2. `ck_cost_rates_status`, `ck_cost_calc_status`, `ck_cost_rates_source_type`, `ck_cost_calc_qty_basis`: Explicit enumeration constraints.
3. `ck_cost_rates_confirmed_fields`: Confirmed rates require non-null `confirmed_by` and `confirmed_at`.
4. `ck_cost_calc_basis_sources`: Mutually exclusive quantity source references matching specified basis.
5. `trg_validate_cost_rate_source`: Prohibits global rates referencing project documents; ensures document/evidence project isolation.
6. `trg_protect_cost_rate`: Blocks deletion of confirmed/superseded rates; blocks mutation of contractual fields once confirmed.
7. `trg_validate_cost_calc_cross_project`: Blocks cross-project quantity sources, enforces rate snapshot consistency and currency matching.
8. `trg_protect_cost_calculation`: Prohibits deletion; allows only `CALCULATED -> SUPERSEDED`; locks all mathematical and provenance attributes.

### 17.4 API Catalog
- `POST /api/projects/{project_id}/cost-rates`: Declare project draft rate.
- `POST /api/cost-rates`: Declare global draft rate.
- `PATCH /api/cost-rates/{rate_id}/confirm`: Confirm draft rate (supervisor/admin).
- `DELETE /api/cost-rates/{rate_id}`: Delete draft rate.
- `GET /api/projects/{project_id}/cost-rates`: List rates available to project.
- `GET /api/cost-rates`: List rates across global catalog.
- `POST /api/projects/{project_id}/cost-calculations`: Execute deterministic calculation.
- `GET /api/projects/{project_id}/cost-calculations`: List project cost calculations.
- `GET /api/projects/{project_id}/cost-summary`: Aggregated cost totals and comparable valuation delta.

---

*Document updated: 2026-10-05*
*Status: PHASE 1K COMPLETE — READY TO FREEZE*

