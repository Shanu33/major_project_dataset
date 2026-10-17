# PHASE 1T — STEP 2 CORRECTNESS & HARDENING REPORT

**Subsystem:** Construction Schedule Performance, Earned Schedule & Delay Attribution Analytics  
**Phase:** Phase 1T — Step 2 Hardening & Correctness Fixes  
**Algorithm:** `SCHED_PERFORMANCE_1.0_LINEAR`  
**Current Migration Revision:** `f0a1b2c3d4e5` (head)  
**Parent Migration Revision:** `e9f0a1b2c3d4`  
**Date:** October 11, 2026  
**Final Status:** `APPROVED FOR STEP 3`

---

## 1. Executive Summary

This report documents the final correctness, provenance, and lifecycle hardening pass conducted on Phase 1T Step 2 prior to starting Step 3 API endpoint integration. The objective was to ensure mathematical, relational, and cryptographic invariants are strictly adhered to in the deterministic service and schemas without relying on client assumptions or implicit defaults.

All governing constraints and required audit corrections were verified against the live PostgreSQL database, SQLAlchemy models, Pydantic schemas, and the pytest test suite.

---

## 2. Issues Identified and Corrections Made

### 2.1 Schedule and Baseline Consistency (Ambiguity Elimination)
- **Issue:** Previously, `create_schedule_performance_snapshot` fell back to silently querying the latest calculated schedule for the project if `schedule_id` was not explicitly provided, even when no baseline was provided.
- **Correction:** Removed the silent fallback. The service now requires `schedule_id` to be explicitly provided or cleanly derives it from an explicitly supplied and validated `monitoring_baseline_id`. If neither is supplied, the service immediately raises an `HTTP 422 Unprocessable Content` domain error. When both `schedule_id` and `monitoring_baseline_id` are provided, the service strictly validates that `baseline.schedule_id == schedule_id`, rejecting any mismatch with `HTTP 422`.

### 2.2 Earned Schedule Approximation & Planned Progress Transparency
- **Issue:** CPM schedules model discrete start/finish/float schedules rather than non-linear planned progress curves. The Earned Schedule calculation ($ES = PD \times \frac{\text{Actual\%}}{100}$) assumes linear planned progress across the planned duration.
- **Correction:** Qualified the calculation contract explicitly as `LINEAR_CPM_APPROXIMATION`. Documented the assumption in `provenance_metadata["planned_progress_curve_type"] = "LINEAR_CPM_APPROXIMATION"` and updated the algorithm version to `SCHED_PERFORMANCE_1.0_LINEAR`. Documented that `planned_cumulative_progress_pct` is recorded in the input snapshot for auditability when external S-curves are available.

### 2.3 Verified Progress Precedence & Stable Tie-Breaking
- **Issue:** Multiple supervisor verification records could share the same daily progress report date, leading to arbitrary database sorting if only sorted by `report_date DESC`.
- **Correction:** Enforced deterministic three-tier ordering: `DailyProgressReport.report_date.desc(), DailyActivityProgressVerification.verified_at.desc(), DailyActivityProgressVerification.id.desc()`. Upstream verification IDs are captured in provenance. Overriding verified progress strictly requires an explicit `override_reason` (HTTP 422 if omitted), and the source category is accurately stamped as `SUPERVISOR_VERIFIED`, `MANUAL_OVERRIDE`, or `DIRECT_ENTRY_UNVERIFIED`.

### 2.4 Strict Canonical Hashing
- **Issue:** `_canonical_normalize` previously had a fallback to `str(value)` which could mask non-deterministic object serialization. Furthermore, non-string dictionary keys were not explicitly blocked.
- **Correction:** Refactored `_canonical_normalize` to strictly whitelist supported types: `None`, `bool`, `int`, `Decimal` (exact string), `date`/`datetime` (ISO 8601), `enum`, `str`, `list`/`tuple`, and `dict` (strictly string-keyed). Any non-string dictionary key or unsupported object raises `TypeError`. Added all material snapshot fields, inputs, outputs, delay classifications, and baseline references to `canonical_payload`.

### 2.5 Pure Decimal Float and Slippage Arithmetic
- **Issue:** Fractional delay calculations previously converted `schedule_variance_days` to `float` prior to `math.ceil()`, risking floating-point precision drift.
- **Correction:** Removed binary float conversions. Replaced with pure `Decimal` arithmetic using `to_integral_value(rounding=ROUND_CEILING)`. Residual float calculation contract is explicitly documented as integer calendar days.

### 2.6 Finalization Concurrency & Supersession Lifecycle
- **Issue:** Finalization advisory lock previously locked on `project_id + "_" + snapshot_id`, meaning concurrent draft snapshots for the exact same activity and performance period did not serialize on each other. Supersession also lacked cycle detection.
- **Correction:** Changed the advisory lock key to a stable business identity: `sps_finalize_{project_id}_{activity_id}_{period_start}_{period_end}`. Wrapped finalization and supersession in explicit `try/except` blocks with database rollbacks to prevent aborted transaction leakage. In `supersede_schedule_performance_snapshot`, added check preventing cyclical supersession chains (`replacement.superseded_by == snapshot.id`).

### 2.7 Date and Input Validation Boundaries
- **Issue:** Schema allowed `evaluation_date` to precede `performance_period_start`.
- **Correction:** Added model validator in `SchedulePerformanceCreateRequest` enforcing `evaluation_date >= performance_period_start`. Preserved field validators ensuring cumulative progress percentages are bounded between 0% and 100%.

---

## 3. Files Changed and Rationale

1. **`app/schemas/schedule_performance.py`**
   - Added validation ensuring `evaluation_date` is not before `performance_period_start`.
   - Maintained `ConfigDict(extra="forbid")` and validated range `[0.0000, 100.0000]` on progress percentages.

2. **`app/services/schedule_performance_service.py`**
   - Replaced `math.ceil(float(...))` with pure `Decimal` `ROUND_CEILING`.
   - Updated `_canonical_normalize()` with strict type checking and `TypeError` on unsupported objects or non-string dictionary keys.
   - Enforced unambiguous schedule resolution and baseline pairing.
   - Enforced three-tier deterministic sorting for verification tie-breaking.
   - Updated advisory lock in `finalize_schedule_performance_snapshot` to lock on business identity (`project_id`, `activity_id`, `period_start`, `period_end`).
   - Added rollback protection and cycle prevention in `supersede_schedule_performance_snapshot`.

3. **`tests/test_schedule_performance_service.py`**
   - Expanded test suite from 16 to 29 comprehensive tests covering all boundary conditions, deterministic tie-breaking, canonical hash type errors, circular supersession rejection, pure Decimal float precision, and schedule resolution errors.

---

## 4. New Tests Added

- `test_17_schedule_variance_tolerance_boundary_conditions`: Validates exact $\pm 0.5000$ day tolerance band transitions.
- `test_18_supervisor_assessed_status_does_not_override_calculated_delay_status`: Proves human assessment cannot replace calculated status.
- `test_19_baseline_schedule_mismatch_rejection`: Validates rejection of schedule/baseline mismatches.
- `test_20_progress_provenance_and_override_reason_requirement`: Tests verified progress precedence and mandatory `override_reason`.
- `test_21_canonical_hash_strict_typing_and_metadata_sensitivity`: Tests SHA-256 sensitivity to all inputs and metadata.
- `test_22_canonical_hash_rejects_unsupported_types_and_non_string_keys`: Proves `TypeError` on arbitrary objects and non-string keys.
- `test_23_schedule_resolution_without_schedule_or_baseline_fails`: Rejects ambiguous snapshot creation without schedule or baseline.
- `test_24_schedule_derived_from_explicit_baseline_without_schedule_id`: Verifies clean derivation of `schedule_id` from explicit baseline.
- `test_25_evaluation_date_before_performance_period_start_rejected`: Verifies schema rejection when `evaluation_date < performance_period_start`.
- `test_26_progress_percentage_out_of_bounds_rejected`: Verifies rejection of negative and $>100\%$ progress values.
- `test_27_supersession_prevents_cycles_and_invalid_replacement_status`: Verifies cycle prevention and self-supersession blocking.
- `test_28_deterministic_verification_ordering_tie_breaking`: Verifies tie-breaking by `verified_at` and `id` for duplicate report dates.
- `test_29_pure_decimal_ceiling_residual_float_precision`: Verifies precision without binary floating-point drift.

---

## 5. Verification Commands and Observed Outputs

### 5.1 Service Unit & Hardening Tests
```bash
PYTHONPATH=. SECRET_KEY="test_secret_key" venv/bin/pytest tests/test_schedule_performance_service.py
```
**Output:** `29 passed, 4 warnings in 3.19s`

### 5.2 Combined Phase 1T Tests (DB + Service)
```bash
PYTHONPATH=. SECRET_KEY="test_secret_key" venv/bin/pytest tests/test_schedule_performance_db.py tests/test_schedule_performance_service.py
```
**Output:** `55 passed, 4 warnings in 5.01s`

### 5.3 Upstream Regression Tests (Phase 1S & Phase 1R)
```bash
PYTHONPATH=. SECRET_KEY="test_secret_key" venv/bin/pytest tests/test_resource_performance.py tests/test_material_performance.py -q
```
**Output:** `126 passed, 6 warnings in 11.23s`

### 5.4 Full Repository Regression Suite
```bash
PYTHONPATH=. SECRET_KEY="test_secret_key" venv/bin/pytest -q
```
**Output:** `751 passed, 24 warnings in 81.45s (0:01:21)`

### 5.5 Alembic Migration Revision
```bash
SECRET_KEY="test_secret_key" venv/bin/alembic current
```
**Output:** `f0a1b2c3d4e5 (head)`

---

## 6. Unresolved Limitations or Risks

- **Linear CPM Progress Limitation:** Standard CPM networks do not contain non-linear cumulative S-curves. Earned Schedule calculations remain qualified as `LINEAR_CPM_APPROXIMATION` until future phases integrate non-linear baseline planned curves.
- **Tamper Detection vs Truth:** Canonical SHA-256 hashes detect database tampering relative to the persisted hash digest; they do not verify external real-world truth.

---

## 7. Final Verdict

**VERDICT: APPROVED FOR STEP 3**

The Phase 1T Step 2 service and schemas meet all architectural, provenance, mathematical, and concurrency requirements. The system is ready to proceed to Phase 1T Step 3 (API Endpoints & Router Integration).
