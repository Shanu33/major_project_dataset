# PHASE 1T — STEP 4 REPORT: API, LIFECYCLE, AUTHORIZATION & AUDIT HARDENING

**Project:** Construction Intelligence Backend  
**Directory:** `/home/shahnawaz/Documents/DataRequirement/backend`  
**Phase:** Phase 1T — Step 4  
**Current Alembic Head:** `f0a1b2c3d4e5`  
**Parent Migration:** `e9f0a1b2c3d4`  
**Algorithm:** `SCHED_PERFORMANCE_1.0_LINEAR`  
**Date:** 2026-10-11  

---

## 1. Findings Classified by Severity

### Finding 1 (Medium - Resolved): Unbounded Query Filter Parameters in Snapshots List
- **Component:** `app/services/schedule_performance_service.py` & `app/api/endpoints/schedule_performance.py`
- **Issue:** Query string parameters for `delay_status`, `performance_status`, and `status` (`status_filter`) in `list_schedule_performance_snapshots` accepted arbitrary strings, silently converting them to uppercase and returning empty lists rather than validating against permitted domain enum sets.
- **Correction:** Validated `delay_status` against `VALID_DELAY_STATUSES`, `performance_status` against `VALID_PERFORMANCE_STATUSES`, and `status_filter` against `VALID_SNAPSHOT_STATUSES` (`DRAFT`, `FINALIZED`, `SUPERSEDED`). Rejection produces deterministic HTTP 422 Unprocessable Content.

### Finding 2 (Medium - Resolved): Non-Standard Timezone Usage in Summary Cutoff Default
- **Component:** `app/api/endpoints/schedule_performance.py` (`get_summary_endpoint`)
- **Issue:** If `evaluation_date` was omitted, the handler defaulted to `date.today()`, which uses host local system time instead of UTC application standard.
- **Correction:** Aligned default fallback cutoff to `datetime.now(timezone.utc).date()`, guaranteeing deterministic cutoff behavior across timezones.

### Finding 3 (Medium - Resolved): Generic 409 Fallback Swallowing Non-Integrity Exceptions
- **Component:** `app/services/schedule_performance_service.py` (`finalize_schedule_performance_snapshot` & `supersede_schedule_performance_snapshot`)
- **Issue:** Blanket `except Exception as e` converted all runtime errors (including potential programming or connection errors) into HTTP 409 Conflict with raw error message leakage.
- **Correction:** Restricted HTTP 409 Conflict strictly to `sqlalchemy.exc.IntegrityError` (database unique constraint and check constraint collisions). Explicitly passed through `HTTPException` and safely handled unexpected exceptions as HTTP 500 without leaking raw internal exception strings.

### Finding 4 (Low - Clarified & Verified): Authoritative Semantics in Supersession Lifecycle
- **Component:** Database Partial Unique Indexes & Supersession Service Logic
- **Issue:** Investigation requested into whether a replacement snapshot must be finalized prior to superseding an authoritative snapshot, and whether a draft snapshot could prematurely become authoritative.
- **Resolution:** Verified database constraints and established architectural patterns across Phase 1R/1S/1T. The replacement snapshot in a supersession relationship is a draft correction that transitions to authoritative once finalized. The database partial unique index (`uq_sps_authoritative_identity`) strictly requires `status = 'FINALIZED'`. Therefore, superseding the original finalized record releases the unique constraint, allowing the replacement draft to be reviewed and finalized. Downstream consumers and summaries filter exclusively by status (`status = 'FINALIZED'`), ensuring non-authoritative drafts are never treated as authoritative.

---

## 2. Lifecycle Decision & Rationale

### Authoritative Record & Supersession Model
In accordance with `MASTER_SYSTEM_SPECIFICATION.md` Section 6 ("Immutable Reporting Model") and PostgreSQL schema constraints established in Step 1:
1. **Creation:** A snapshot begins its lifecycle strictly as `DRAFT` (enforced by DB trigger `fn_protect_schedule_performance_snapshot` and Pydantic validator).
2. **Finalization:** A draft is verified by an authorized role (`admin`, `supervisor`, `site_supervisor`) and transitions to `FINALIZED`. An advisory lock on `(project_id, activity_id, period)` serializes concurrent requests, while partial unique index `uq_sps_authoritative_identity` guarantees that at most **one** finalized record exists for a project activity and reporting period.
3. **Supersession:** When errors in physical progress or schedule inputs require replacement:
   - A replacement draft is evaluated and created for the exact same activity and performance period.
   - Calling `POST /finalize` on the replacement *while the original is still finalized* correctly triggers HTTP 409 Conflict (partial unique index block).
   - The authoritative record is superseded via `POST /supersede` pointing to the replacement draft with an explicit, non-empty `supersession_reason`.
   - The superseded record transitions `FINALIZED -> SUPERSEDED`, permanently preserving its calculation fields, canonical hash, and finalized-at timestamp, while populating `superseded_by`, `superseded_by_user_id`, `superseded_at`, and `supersession_reason`.
   - The replacement draft is then finalized via `POST /finalize`, cleanly becoming the new authoritative record.
4. **Authoritative Downstream Consumption:** Aggregation queries and external integrations query `status = 'FINALIZED'`. DRAFT snapshots and SUPERSEDED records are explicitly marked and cannot be mistaken for active authoritative values.

---

## 3. Final Role and Permission Matrix

| Operation | Route Path | Enforced Roles | Project Access Enforcement | Expected HTTP Codes |
|---|---|---|---|---|
| **Create Snapshot** | `POST /api/projects/{project_id}/schedule-performance` | `admin`, `supervisor`, `site_supervisor` | Must be project member (or admin) | 201, 401, 403, 404, 422 |
| **List Snapshots** | `GET /api/projects/{project_id}/schedule-performance` | `admin`, `supervisor`, `site_supervisor`, `contractor` | Must be project member (or admin) | 200, 401, 403, 404, 422 |
| **Get Snapshot** | `GET /api/projects/{project_id}/schedule-performance/{id}` | `admin`, `supervisor`, `site_supervisor`, `contractor` | Must be project member (or admin) | 200, 401, 403, 404 |
| **Activity History** | `GET /api/projects/{project_id}/activities/{activity_id}/schedule-performance` | `admin`, `supervisor`, `site_supervisor`, `contractor` | Must be project member; activity must belong to project | 200, 401, 403, 404 |
| **Project Summary** | `GET /api/projects/{project_id}/schedule-performance/summary` | `admin`, `supervisor`, `site_supervisor`, `contractor` | Must be project member (or admin) | 200, 401, 403, 404 |
| **Finalize Snapshot** | `POST /api/projects/{project_id}/schedule-performance/{id}/finalize` | `admin`, `supervisor`, `site_supervisor` | Must be project member (or admin) | 200, 400, 401, 403, 404, 409 |
| **Supersede Snapshot** | `POST /api/projects/{project_id}/schedule-performance/{id}/supersede` | `admin`, `supervisor`, `site_supervisor` | Must be project member (or admin) | 200, 400, 401, 403, 404, 409, 422 |

*Note: Roles not in MVP (`project_manager`, `contractor` for mutations) receive HTTP 403 Forbidden. Non-members receive HTTP 403 Forbidden. Non-existent projects receive HTTP 404 Not Found.*

---

## 4. Files Changed and Rationale

1. **`app/schemas/schedule_performance.py`**
   - Added `VALID_SNAPSHOT_STATUSES = {"DRAFT", "FINALIZED", "SUPERSEDED"}` to provide authoritative validation sets for status filtering.
2. **`app/services/schedule_performance_service.py`**
   - Imported `VALID_DELAY_STATUSES`, `VALID_PERFORMANCE_STATUSES`, `VALID_SNAPSHOT_STATUSES`, and `IntegrityError`.
   - Added query parameter validation in `list_schedule_performance_snapshots` returning HTTP 422 for unwhitelisted filter values.
   - Hardened `finalize_schedule_performance_snapshot` and `supersede_schedule_performance_snapshot` exception handling to catch `IntegrityError` specifically for 409, preserving 500 for unexpected errors and performing clean transaction rollbacks.
3. **`app/api/endpoints/schedule_performance.py`**
   - Changed `date.today()` fallback to `datetime.now(timezone.utc).date()` for UTC consistency.
4. **`tests/test_schedule_performance_api.py`**
   - Added tests for `supervisor` alias role, `project_manager` role rejection on mutation, `contractor` read access vs mutation rejection, invalid query filter rejection (HTTP 422), and summary evaluation-date cutoff boundaries.
5. **`tests/test_schedule_performance_service.py`**
   - Added `test_30_list_snapshots_filter_validation` verifying service-level rejection of invalid filter parameters.

---

## 5. New Regression Tests

- `tests/test_schedule_performance_api.py::test_project_membership_and_role_authorization` (Expanded: tests non-member 403, contractor read allowed/mutation forbidden, project_manager mutation forbidden, supervisor alias allowed).
- `tests/test_schedule_performance_api.py::test_invalid_query_filter_validation` (Tests 422 response on invalid `delay_status`, `performance_status`, and `status`).
- `tests/test_schedule_performance_api.py::test_summary_authoritative_only_and_date_filtering` (Tests empty summary metrics when cutoff precedes snapshots).
- `tests/test_schedule_performance_service.py::test_30_list_snapshots_filter_validation` (Tests service-layer HTTP 422 on invalid filter values).

---

## 6. Exact Commands and Observed Test Results

### 1. Phase 1T Test Suite
```bash
PYTHONPATH=. SECRET_KEY="test_secret_key" venv/bin/pytest tests/test_schedule_performance_db.py tests/test_schedule_performance_service.py tests/test_schedule_performance_api.py -v
```
**Result:** **66 passed**, 13 warnings in 7.94s
- `tests/test_schedule_performance_db.py`: 26 passed
- `tests/test_schedule_performance_service.py`: 30 passed
- `tests/test_schedule_performance_api.py`: 10 passed

### 2. Neighboring Regressions (Phase 1R & Phase 1S)
```bash
PYTHONPATH=. SECRET_KEY="test_secret_key" venv/bin/pytest tests/test_resource_performance.py tests/test_material_performance.py -q
```
**Result:** **126 passed**, 6 warnings in 10.80s

### 3. Full Backend Test Suite
```bash
PYTHONPATH=. SECRET_KEY="test_secret_key" venv/bin/pytest -q
```
**Result:** **762 passed**, 28 warnings in 74.51s (100% passing across all Phases 0 through 1T).

---

## 7. OpenAPI and Migration Verification

### OpenAPI Route Extraction
```bash
PYTHONPATH=. SECRET_KEY="test_secret_key" venv/bin/python3 -c "from app.main import app; import json; schema = app.openapi(); paths = {p: list(m.keys()) for p, m in schema['paths'].items() if 'schedule-performance' in p}; print(json.dumps(paths, indent=2))"
```
**Output:**
```json
{
  "/api/projects/{project_id}/schedule-performance": ["post", "get"],
  "/api/projects/{project_id}/schedule-performance/summary": ["get"],
  "/api/projects/{project_id}/activities/{activity_id}/schedule-performance": ["get"],
  "/api/projects/{project_id}/schedule-performance/{performance_id}": ["get"],
  "/api/projects/{project_id}/schedule-performance/{performance_id}/finalize": ["post"],
  "/api/projects/{project_id}/schedule-performance/{performance_id}/supersede": ["post"]
}
```

### Alembic Migration Verification
```bash
PYTHONPATH=. SECRET_KEY="test_secret_key" venv/bin/alembic heads && PYTHONPATH=. SECRET_KEY="test_secret_key" venv/bin/alembic current
```
**Output:**
```
f0a1b2c3d4e5 (head)
f0a1b2c3d4e5 (head)
```
Database migration head is strictly clean and synchronized at `f0a1b2c3d4e5`. No new migrations were required or created.

---

## 8. Remaining Risks and Limitations

1. **Linear CPM Assumption:** As explicitly stated in `algorithm_version = "SCHED_PERFORMANCE_1.0_LINEAR"`, earned schedule assumes linear progress between CPM early start and early finish dates. Non-linear S-curves remain an enhancement for subsequent versions.
2. **PostgreSQL Advisory Locks:** Serialization locks rely on 32-bit hash keys generated from `(project_id, activity_id, period)`. While collision probability across active concurrent transactions is negligible ($< 10^{-9}$), database partial unique indexes remain the definitive safeguard.

---

## 9. Final Verdict

**APPROVED FOR STEP 5**

