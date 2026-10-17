from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


VALID_DELAY_STATUSES = {
    "ON_SCHEDULE",
    "AHEAD_OF_SCHEDULE",
    "MINOR_DELAY",
    "CRITICAL_DELAY",
    "FLOAT_ABSORBED",
    "SCHEDULE_BREACH",
    "REQUIRES_INPUT",
}

VALID_SNAPSHOT_STATUSES = {
    "DRAFT",
    "FINALIZED",
    "SUPERSEDED",
}

VALID_DELAY_CLASSIFICATIONS = {
    "EXCUSABLE_COMPENSABLE",
    "EXCUSABLE_NON_COMPENSABLE",
    "NON_EXCUSABLE",
    "CONCURRENT_DELAY",
    "NO_DELAY",
}

VALID_DELAY_ROOT_CAUSES = {
    "WEATHER",
    "SITE_ACCESS",
    "DRAWING_REVISION",
    "LABOUR",
    "MATERIAL",
    "EQUIPMENT",
    "STATUTORY",
    "FORCE_MAJEURE",
    "DESIGN_CHANGE",
    "CLIENT_DELAY",
    "CONTRACTOR_DEFAULT",
    "OTHER",
}

VALID_PERFORMANCE_STATUSES = {
    "ON_TRACK",
    "SCHEDULE_VARIANCE_WITHIN_TOLERANCE",
    "CRITICAL_DELAY",
    "SCHEDULE_BREACH",
    "REQUIRES_INPUT",
    "DATA_MISMATCH",
}


class SchedulePerformanceCreateRequest(BaseModel):
    """
    Request payload to evaluate and create a draft schedule performance snapshot.
    Prohibits callers from setting authoritative lifecycle metadata, calculated IDs, or hashes.
    """
    activity_id: str
    schedule_id: Optional[str] = None
    monitoring_baseline_id: Optional[str] = None
    performance_period_start: Optional[date] = None
    performance_period_end: Optional[date] = None
    evaluation_date: date

    # Progress metrics:
    # planned_cumulative_progress_pct can be provided if an external S-curve is used, otherwise defaults to linear.
    planned_cumulative_progress_pct: Optional[Decimal] = None
    # actual_cumulative_progress_pct is a manual/direct entry (if no supervisor verification exists, or if overriding).
    # If overriding an existing supervisor verification, override_reason must be provided.
    actual_cumulative_progress_pct: Optional[Decimal] = None
    override_reason: Optional[str] = None

    # Directly supplied date metrics (if overriding CPM activity schedule results)
    planned_start_date: Optional[date] = None
    planned_finish_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_finish_date: Optional[date] = None

    # Baseline float override if not loaded from schedule CPM
    baseline_total_float_days: Optional[int] = None
    is_critical_path: Optional[bool] = False

    # Evidentiary and attribution assessment (Human supervisor assessment, recorded separately from calculated status)
    supervisor_assessed_delay_status: Optional[str] = None
    delay_classification: Optional[str] = None
    delay_root_cause_category: Optional[str] = None
    delay_justification: Optional[str] = None
    delay_evidence_document_id: Optional[str] = None
    contract_variation_id: Optional[str] = None

    # Explicit lifecycle state (must always be DRAFT on creation)
    status: Optional[str] = "DRAFT"

    model_config = ConfigDict(extra="forbid")

    @field_validator("status")
    def validate_status(cls, v: Optional[str]) -> str:
        if v is not None and v != "DRAFT":
            raise ValueError("Snapshots must always be created in DRAFT status. Cannot specify status='FINALIZED' or 'SUPERSEDED'.")
        return "DRAFT"

    @field_validator("supervisor_assessed_delay_status")
    def validate_supervisor_assessed_delay_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().upper()
            if clean not in VALID_DELAY_STATUSES:
                raise ValueError(f"supervisor_assessed_delay_status must be one of: {sorted(list(VALID_DELAY_STATUSES))}")
            return clean
        return v

    @field_validator("delay_classification")
    def validate_delay_classification(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().upper()
            if clean not in VALID_DELAY_CLASSIFICATIONS:
                raise ValueError(f"delay_classification must be one of: {sorted(list(VALID_DELAY_CLASSIFICATIONS))}")
            return clean
        return v

    @field_validator("delay_root_cause_category")
    def validate_delay_root_cause_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().upper()
            if clean not in VALID_DELAY_ROOT_CAUSES:
                raise ValueError(f"delay_root_cause_category must be one of: {sorted(list(VALID_DELAY_ROOT_CAUSES))}")
            return clean
        return v

    @field_validator("planned_cumulative_progress_pct")
    def validate_planned_pct(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            if v < Decimal("0.0000") or v > Decimal("100.0000"):
                raise ValueError("planned_cumulative_progress_pct must be between 0.0000 and 100.0000")
        return v

    @field_validator("actual_cumulative_progress_pct")
    def validate_actual_pct(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            if v < Decimal("0.0000") or v > Decimal("100.0000"):
                raise ValueError("actual_cumulative_progress_pct must be between 0.0000 and 100.0000")
        return v

    @model_validator(mode="after")
    def validate_date_intervals(self) -> "SchedulePerformanceCreateRequest":
        # Check performance period order
        if self.performance_period_start and self.performance_period_end:
            if self.performance_period_start > self.performance_period_end:
                raise ValueError("performance_period_start cannot be after performance_period_end")

        # Check evaluation date is not before performance period start
        if self.performance_period_start and self.evaluation_date < self.performance_period_start:
            raise ValueError(
                f"evaluation_date ({self.evaluation_date}) cannot be before performance_period_start ({self.performance_period_start})"
            )

        # Check planned dates order
        if self.planned_start_date and self.planned_finish_date:
            if self.planned_start_date > self.planned_finish_date:
                raise ValueError("planned_start_date cannot be after planned_finish_date")

        # Check actual dates order
        if self.actual_start_date and self.actual_finish_date:
            if self.actual_start_date > self.actual_finish_date:
                raise ValueError("actual_start_date cannot be after actual_finish_date")

        return self


class SchedulePerformanceSupersedeRequest(BaseModel):
    """
    Request payload to supersede an authoritative finalized snapshot with a replacement snapshot.
    """
    supersession_reason: str
    replacement_snapshot_id: str

    model_config = ConfigDict(extra="forbid")

    @field_validator("supersession_reason")
    def validate_reason(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("supersession_reason cannot be empty.")
        return s

    @field_validator("replacement_snapshot_id")
    def validate_replacement_id(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("replacement_snapshot_id cannot be empty.")
        return s


class SchedulePerformanceSnapshotResponse(BaseModel):
    """
    Full response representation of a schedule performance snapshot.
    """
    id: str
    project_id: str
    activity_id: str
    schedule_id: str
    monitoring_baseline_id: Optional[str] = None
    performance_period_start: Optional[date] = None
    performance_period_end: Optional[date] = None
    evaluation_date: date

    planned_start_date: Optional[date] = None
    planned_finish_date: Optional[date] = None
    planned_duration_days: Optional[int] = None
    actual_start_date: Optional[date] = None
    actual_finish_date: Optional[date] = None
    actual_duration_days: Optional[int] = None

    planned_cumulative_progress_pct: Optional[Decimal] = None
    actual_cumulative_progress_pct: Optional[Decimal] = None
    earned_schedule_days: Optional[Decimal] = None
    actual_time_days: Optional[Decimal] = None

    schedule_variance_days: Optional[Decimal] = None
    schedule_performance_index: Optional[Decimal] = None

    baseline_total_float_days: Optional[int] = None
    residual_total_float_days: Optional[int] = None
    is_critical_path: bool
    critical_path_impact_days: Optional[int] = None

    delay_status: str
    delay_classification: Optional[str] = None
    delay_root_cause_category: Optional[str] = None
    delay_justification: Optional[str] = None
    delay_evidence_document_id: Optional[str] = None
    contract_variation_id: Optional[str] = None

    performance_status: str
    algorithm_version: str
    input_snapshot_json: Dict[str, Any]
    provenance_metadata: Dict[str, Any]
    canonical_hash: str

    status: str
    created_by: str
    created_at: datetime
    finalized_by: Optional[str] = None
    finalized_at: Optional[datetime] = None
    superseded_by: Optional[str] = None
    superseded_by_user_id: Optional[str] = None
    superseded_at: Optional[datetime] = None
    supersession_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SchedulePerformanceSummaryResponse(BaseModel):
    """
    Aggregated schedule performance analytics for a project.
    """
    project_id: str
    evaluation_date: date
    total_snapshots: int
    mean_schedule_performance_index: Optional[Decimal] = None
    total_schedule_variance_days: Optional[Decimal] = None
    critical_path_delayed_activities_count: int
    delay_status_distribution: Dict[str, int]
    delay_root_cause_distribution: Dict[str, int]
    performance_status_distribution: Dict[str, int]
    snapshots: List[SchedulePerformanceSnapshotResponse]

    model_config = ConfigDict(from_attributes=True)
