# PHASE 1T — SCOPE DISCOVERY, DESIGN & IMPLEMENTATION PLAN

**Subsystem:** Construction Schedule Performance, Delay Attribution & Earned Schedule Analytics  
**Parent Migration:** `e9f0a1b2c3d4` (Phase 1S — `RES_PERFORMANCE_1.0`)  
**Proposed Phase 1T Migration:** `f0a1b2c3d4e5`  
**Algorithm Version:** `SCHED_PERFORMANCE_1.0`  
**Current Repository Baseline:** 696 / 696 tests passed  
**Alembic Head:** `e9f0a1b2c3d4`  
**Mode:** Planning & Architecture Audit Only — **NOT IMPLEMENTED YET**

---

## 1. Source of Truth & Context Discovery

### 1.1 Specification Analysis
A comprehensive audit of `/home/shahnawaz/Documents/DataRequirement/MASTER_SYSTEM_SPECIFICATION.md` establishes:
1. **Dual Operational Modes**:
   - Mode A: Estimation Mode (No initial BOQ).
   - Mode B: BOQ Validation & Reconciliation Mode (BOQ provided as ground truth).
2. **Current Machine Learning Reality**:
   - The verified dataset consists of 3 independent projects, 58 elements, and effectively 4–5 unique observations.
   - Status: strictly `NOT_TRAINABLE`.
   - **No Machine Learning or heuristic estimation is permitted in the deterministic engineering calculation path.**
3. **Core Architectural Principles**:
   - Explicit assumptions, deterministic calculations where physical laws apply.
   - Immutability of reporting records (contractor declarations and supervisor verifications co-exist without silent overwriting).
   - Cryptographic hashing (SHA-256) and source provenance tracking.
   - Exact precision (`Decimal`) for physical, financial, and duration quantities.

### 1.2 Subsystem Evolutionary Trajectory
The platform progression demonstrates a rigorous, step-by-step engineering foundation:
- **Phase 1G**: Resource Planning (`ResourcePlan`).
- **Phase 1H**: Deterministic Scheduling & CPM Analysis (`ConstructionSchedule`, `ConstructionActivity`, `ActivityScheduleResult`).
- **Phase 1I**: Site Monitoring & Verification (`MonitoringBaseline`, `DailyProgressReport`, `DailyActivityProgressVerification`).
- **Phase 1J**: BOQ Reconciliation Foundation.
- **Phase 1K**: Deterministic Cost Estimation & Rate Catalog (`CostRate`, `CostCalculation`).
- **Phase 1L**: Site Progress Valuation & Interim Payment Certification (`DailyProgressValuation`, `PeriodProgressCertificate`).
- **Phase 1M**: BOQ Execution Reconciliation & Contract Variations (`BoqExecutionReconciliation`, `ContractVariationOrder`).
- **Phase 1N**: Material Mix Formulation & Theoretical Consumption.
- **Phase 1O**: Contractor Procurement & Material Requirements Planning.
- **Phase 1P**: Material Inventory & Stock Availability.
- **Phase 1Q**: Material Issue & Actual Consumption Reconciliation.
- **Phase 1R**: Material Productivity & Consumption Efficiency (`MaterialPerformanceSnapshot`).
- **Phase 1S**: Resource Productivity & Cost Performance (`ResourcePerformanceSnapshot`, `RES_PERFORMANCE_1.0`).

### 1.3 The Missing Domain Capability: Why Phase 1T is Required
With Phase 1R (Material Efficiency) and Phase 1S (Resource Productivity & Unit Cost Performance) complete:
- The system evaluates **quantities, productivity, and costs**.
- However, construction project performance fundamentally rests on the **Iron Triangle**: **Cost, Quality/Resources, and Time/Schedule**.
- In Phase 1H, deterministic critical path method (CPM) schedules were generated (`early_start`, `early_finish`, `late_start`, `late_finish`, `total_float`).
- In Phase 1I, daily activity progress was verified (`verified_quantity`, execution dates).
- In Phase 1L, progress certificates established cut-off milestone dates.
- **Critical Gap:** The system currently cannot deterministically answer:
  1. *What is the Schedule Performance Index ($SPI$) and Schedule Variance ($\Delta T, SV_t$) of executing activities?*
  2. *Is an activity on the Critical Path delayed, and by exactly how many days?*
  3. *Has an activity consumed its available total float ($TF$), turning into a critical activity?*
  4. *What is the root cause / attribution category of the schedule delay (e.g., `WEATHER_FORCE_MAJEURE`, `CLIENT_DRAWING_REVISION`, `CONTRACTOR_LABOUR_SHORTAGE`, `MATERIAL_STOCKOUT`, `SITE_ACCESS_OBSTRUCTION`)?*
  5. *What is the verified Earned Schedule ($ES$) and estimated completion date based on actual physical velocity?*

Phase 1T bridges **Schedule Baselines (Phase 1H)**, **Site Verifications (Phase 1I)**, **Resource Constraints (Phase 1S)**, and **Contract Deviations (Phase 1M)** into **Schedule Performance & Delay Attribution Analytics**.

---

## 2. Current Repository Baseline Verification

An independent verification of the actual environment confirms:
- **Git Branch:** `master` (working tree clean of uncommitted production regressions; unstaged files in `material_requirement_planning` reflect historical test adjustments).
- **Alembic Revision Head:** `e9f0a1b2c3d4` (Phase 1S Resource Performance).
- **Migration Lineage:** 29 sequential migrations from `1c2bfb65f082` (Initial schema) to `e9f0a1b2c3d4`.
- **Full Test Suite:** **696 / 696 passed** in 78.22 seconds (0 failures, 21 deprecation warnings).
- **Dedicated Phase 1S Suite:** **61 / 61 passed**.
- **Dedicated Phase 1R Suite:** **65 / 65 passed**.
- **Frozen Subsystem Status:** Phases 0 through 1S are strictly frozen.

---

## 3. Phase 1T Architectural Design

### 3.1 Problem Definition
Phase 1T implements deterministic, auditable **Schedule Performance, Earned Schedule ($ES$), and Delay Attribution Analytics** (`SCHED_PERFORMANCE_1.0`).

It answers:
- How much progress was planned to be achieved by date $T$ according to the frozen baseline schedule?
- What is the verified actual progress date achieved ($ES$ / Earned Schedule)?
- What is the schedule variance in time ($\Delta T = ES - AT$)?
- If delayed, what is the impact on total float and project completion?
- Which verified events or site conditions caused the delay, and what is the contractual liability allocation?

### 3.2 Required Functionality
1. **Schedule Performance Evaluation**:
   - Planned Duration ($PD$) vs Actual Duration ($AD$).
   - Planned Start / Finish vs Actual Start / Finish.
   - Schedule Variance in Days:
     $$\Delta_{\text{start}} = \text{Actual Start} - \text{Planned Start}$$
     $$\Delta_{\text{finish}} = \text{Actual Finish} - \text{Planned Finish}$$
   - Earned Schedule ($ES$) metric:
     $$SV_t = ES - AT \quad (\text{Schedule Variance in Time})$$
     $$SPI_t = \frac{ES}{AT} \quad (\text{Schedule Performance Index in Time})$$
2. **Critical Path & Float Consumption**:
   - Initial Total Float ($TF_0$) from Phase 1H.
   - Current Residual Float ($TF_{\text{residual}} = TF_0 - \Delta_{\text{delay}}$).
   - Flag `CRITICAL_PATH_BREACH` when residual float becomes $\le 0$.
3. **Structured Delay Attribution**:
   - Delay categorization:
     - `EXCUSABLE_COMPENSABLE` (Client delay, drawing revision, design change).
     - `EXCUSABLE_NON_COMPENSABLE` (Force majeure, extreme weather, statutory halt).
     - `NON_EXCUSABLE` (Contractor default, labour shortage, equipment breakdown).
     - `CONCURRENT_DELAY` (Overlapping client and contractor delays).
   - Traceable link to daily site report logs (Phase 1I `DailyReport` weather/hindrance entries) or contract variations (Phase 1M `ContractVariationOrder`).
4. **Lifecycle & Immutability**:
   - `DRAFT` $\to$ `FINALIZED` $\to$ `SUPERSEDED`.
   - Once `FINALIZED`, updates and deletes are blocked by PostgreSQL triggers.
   - At most one authoritative finalized snapshot per `(project_id, activity_id, performance_period_start, performance_period_end)`.
5. **Deterministic SHA-256 Hashing**:
   - Canonical hash over inputs and calculated delay metrics.

### 3.3 Explicit Exclusions
- **No Machine Learning or AI duration estimation.** Predictions based on unverified historical curves are forbidden.
- **No Project Management Gantt chart UI / Drag-and-drop tool.** This is a backend audit and analytics calculation engine.
- **No automatic modification of frozen schedules.** Phase 1T evaluates variances against frozen schedules; it does not silently mutate Phase 1H schedules.
- **No automated contractor penalty imposition.** Legal dispute outcomes are decisions made by humans; the system only computes deterministic variance and logs liability flags.

### 3.4 Data Model & Entity Specifications

```text
Table: schedule_performance_snapshots
--------------------------------------------------------------------------------
id                                   VARCHAR(36) PRIMARY KEY
project_id                           VARCHAR(36) FK projects(id) RESTRICT
activity_id                          VARCHAR(36) FK construction_activities(id) RESTRICT
schedule_id                          VARCHAR(36) FK construction_schedules(id) RESTRICT
monitoring_baseline_id               VARCHAR(36) FK monitoring_baselines(id) SET NULL
performance_period_start             DATE
performance_period_end               DATE
evaluation_date                      DATE NOT NULL

planned_start_date                   DATE
planned_finish_date                  DATE
planned_duration_days                INTEGER
actual_start_date                    DATE
actual_finish_date                   DATE
actual_duration_days                 INTEGER

planned_cumulative_progress_pct      NUMERIC(7, 4)   -- 0.0000 to 100.0000 %
actual_cumulative_progress_pct       NUMERIC(7, 4)   -- 0.0000 to 100.0000 %
earned_schedule_days                 NUMERIC(10, 4)  -- ES in days
actual_time_days                     NUMERIC(10, 4)  -- AT in days

schedule_variance_days               NUMERIC(10, 4)  -- SV_t = ES - AT
schedule_performance_index           NUMERIC(10, 6)  -- SPI_t = ES / AT

baseline_total_float_days            INTEGER
residual_total_float_days            INTEGER
is_critical_path                     BOOLEAN NOT NULL DEFAULT FALSE
critical_path_impact_days            INTEGER

delay_status                         VARCHAR(40) NOT NULL
delay_classification                 VARCHAR(40)     -- EXCUSABLE_COMPENSABLE, EXCUSABLE_NON_COMPENSABLE, NON_EXCUSABLE, CONCURRENT_DELAY, NO_DELAY
delay_root_cause_category            VARCHAR(50)     -- WEATHER, SITE_ACCESS, DRAWING_REVISION, LABOUR, MATERIAL, EQUIPMENT, STATUTORY
delay_justification                  TEXT
delay_evidence_document_id           VARCHAR(36) FK documents(id) SET NULL
contract_variation_id                VARCHAR(36) FK contract_variation_orders(id) SET NULL

performance_status                   VARCHAR(40) NOT NULL
algorithm_version                    VARCHAR(50) NOT NULL DEFAULT 'SCHED_PERFORMANCE_1.0'
input_snapshot_json                  JSONB NOT NULL DEFAULT '{}'
provenance_metadata                  JSONB NOT NULL DEFAULT '{}'
canonical_hash                       VARCHAR(64) NOT NULL

status                               VARCHAR(20) NOT NULL DEFAULT 'DRAFT'
created_by                           VARCHAR(36) FK users(id) RESTRICT
created_at                           TIMESTAMPTZ NOT NULL DEFAULT NOW()
finalized_by                         VARCHAR(36) FK users(id) RESTRICT
finalized_at                         TIMESTAMPTZ
superseded_by                        VARCHAR(36) FK schedule_performance_snapshots(id) SET NULL
superseded_by_user_id                VARCHAR(36) FK users(id) RESTRICT
superseded_at                        TIMESTAMPTZ
supersession_reason                  TEXT
```

#### Database Constraints:
- `ck_sps_status`: `status IN ('DRAFT', 'FINALIZED', 'SUPERSEDED')`
- `ck_sps_delay_status`: `delay_status IN ('ON_SCHEDULE', 'AHEAD_OF_SCHEDULE', 'MINOR_DELAY', 'CRITICAL_DELAY', 'FLOAT_ABSORBED', 'SCHEDULE_BREACH', 'REQUIRES_INPUT')`
- `ck_sps_delay_class`: `delay_classification IS NULL OR delay_classification IN ('EXCUSABLE_COMPENSABLE', 'EXCUSABLE_NON_COMPENSABLE', 'NON_EXCUSABLE', 'CONCURRENT_DELAY', 'NO_DELAY')`
- `ck_sps_period`: `performance_period_start IS NULL OR performance_period_end IS NULL OR performance_period_start <= performance_period_end`
- `ck_sps_dates`: `planned_start_date IS NULL OR planned_finish_date IS NULL OR planned_start_date <= planned_finish_date`
- `uq_sps_authoritative_identity`: Partial unique index on `(project_id, activity_id, COALESCE(performance_period_start, '1970-01-01'), COALESCE(performance_period_end, '1970-01-01'))` where `status = 'FINALIZED'`.
- `trg_protect_schedule_performance_snapshot`: Prohibits updates/deletes on finalized/superseded snapshots, enforcing immutability.

### 3.5 API Endpoints Design
All endpoints project-scoped under `/api/projects/{project_id}/schedule-performance`:
- `POST /`: Create draft schedule performance snapshot. (Roles: `ADMIN`, `SUPERVISOR`).
- `GET /`: List schedule performance snapshots for project (filterable by `activity_id`, `status`, `delay_status`). (Roles: `ADMIN`, `SUPERVISOR`, `CONTRACTOR` read-only).
- `GET /{snapshot_id}`: Retrieve detailed snapshot with full provenance and attribution lineage.
- `POST /{snapshot_id}/finalize`: Transition `DRAFT` to `FINALIZED`. (Roles: `ADMIN`, `SUPERVISOR`).
- `POST /{snapshot_id}/supersede`: Supersede authoritative snapshot with replacement. (Roles: `ADMIN`, `SUPERVISOR`).
- `GET /summary`: Aggregated project schedule health summary (overall project $SPI_t$, total critical path slip, top delay causes).

---

## 4. Protection of Frozen Boundaries

- **Zero modifications** to historical migrations (`1c2bfb65f082` through `e9f0a1b2c3d4`).
- **Zero changes** to existing Phase 0–1S service contracts, schemas, or database tables.
- **Additive changes only**:
  1. New migration `alembic/versions/f0a1b2c3d4e5_phase_1t_schedule_performance.py` revising `e9f0a1b2c3d4`.
  2. New model `SchedulePerformanceSnapshot` in `app/db/models.py`.
  3. New schemas in `app/schemas/schedule_performance.py`.
  4. New service in `app/services/schedule_performance_service.py`.
  5. New router in `app/api/endpoints/schedule_performance.py` registered in `app/main.py`.
  6. Dedicated test suite in `tests/test_schedule_performance.py`.

---

## 5. Test & Verification Plan

1. **Deterministic Schedule Calculations**:
   - Exact days calculation for $PD$, $AD$, $\Delta_{\text{start}}$, $\Delta_{\text{finish}}$.
   - Earned Schedule ($ES$), $SV_t$, and $SPI_t$ validation using standard formulas.
   - Float consumption: test positive float absorption and transition to negative float.
2. **Missing Operands & Edge Cases**:
   - Activities not yet started $\to$ handled cleanly without false zero delays.
   - Missing daily verifications $\to$ status defaults to `REQUIRES_INPUT`.
3. **Delay Attribution & Evidence**:
   - Verification of delay classification mapping (`EXCUSABLE_COMPENSABLE`, etc.).
   - Linkage to weather events and contract variations verified.
4. **Lifecycle & Immutability**:
   - Creation returns `DRAFT`.
   - Finalization locks snapshot. Direct SQL `UPDATE` and `DELETE` rejected by database triggers.
   - Supersession requires valid reason and maintains pointer integrity.
5. **Partial Unique Index & Concurrency**:
   - Concurrency tests: duplicate finalization for same activity/period yields HTTP 409.
6. **Authorization & Multi-Tenancy**:
   - Project isolation strictly enforced (cross-project access returns 403/404).
   - Contractor restricted to read-only access (mutations rejected with 403).
7. **Migration Roundtrip**:
   - Clean downgrade to `e9f0a1b2c3d4` and upgrade back to head.
8. **Full Regression**:
   - All 696 existing tests must continue to pass (target $\ge 750$ tests passing).

---

## 6. Stop Gate & Final Recommendation

### Evidence Summary
1. Master specification audited: no unverified ML in core engineering path; deterministic principles upheld.
2. Repository baseline verified: 696/696 tests passed, Alembic head at `e9f0a1b2c3d4`.
3. Working tree clean of uncommitted production regressions.
4. Phase 1T scope strictly defined to solve the schedule variance, earned schedule, and delay attribution gap without ERP/UI creep.

### Verdict
```
================================================================================
VERDICT: READY FOR PHASE 1T IMPLEMENTATION
TARGET SUBSYSTEM: Construction Schedule Performance, Delay Attribution & Earned Schedule Analytics
MIGRATION REVISES: e9f0a1b2c3d4 (Phase 1S Head)
ALGORITHM: SCHED_PERFORMANCE_1.0
STATUS: SCOPE LOCKED & ARCHITECTURE APPROVED — READY FOR IMPLEMENTATION
================================================================================
```

