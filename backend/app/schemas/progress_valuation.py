"""Phase 1L: Site Progress Valuation & Certified Progress Foundation Schemas."""
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class ActivityRateMappingCreate(BaseModel):
    activity_id: str
    cost_rate_id: str


class ActivityRateMappingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    activity_id: str
    cost_rate_id: str
    rate_value: Decimal
    rate_unit: str
    rate_version: str
    currency: str
    status: str
    effective_from: datetime
    effective_to: Optional[datetime] = None
    created_by: str
    created_at: datetime


class DailyReportValuationRequest(BaseModel):
    daily_progress_report_id: str


class DailyProgressValuationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    verification_id: str
    activity_rate_mapping_id: str
    contractor_claimed_quantity: Decimal
    supervisor_certified_quantity: Decimal
    quantity_unit: str
    unit_conversion_factor: Decimal
    applied_rate_value: Decimal
    applied_rate_unit: str
    currency: str
    contractor_claimed_value: Decimal
    certified_progress_value: Decimal
    discrepancy_quantity: Decimal
    disputed_valuation_exposure: Decimal
    certified_certificate_id: Optional[str] = None
    valuation_status: str
    created_at: datetime


class DailyReportValuationResponse(BaseModel):
    daily_progress_report_id: str
    valuations_count: int
    total_claimed_value: Decimal
    total_certified_value: Decimal
    total_disputed_exposure: Decimal
    currency: str
    valuations: List[DailyProgressValuationResponse] = []


class PeriodCertificateCreate(BaseModel):
    certificate_number: str
    period_start_date: date
    period_cut_off_date: date


class PeriodCertificateItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    certificate_id: str
    valuation_id: str
    activity_id: str
    claimed_quantity: Decimal
    certified_quantity: Decimal
    quantity_unit: str
    unit_conversion_factor: Decimal
    applied_rate: Decimal
    applied_rate_unit: str
    currency: str
    claimed_amount: Decimal
    certified_amount: Decimal
    discrepancy_quantity: Decimal
    disputed_exposure: Decimal
    created_at: datetime


class PeriodCertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    certificate_number: str
    certificate_type: str
    monitoring_baseline_id: str
    baseline_schedule_id: str
    baseline_schedule_version: str
    baseline_schedule_algorithm_version: str
    baseline_start_date: date
    period_start_date: date
    period_cut_off_date: date
    certificate_status: str
    currency: str
    period_claimed_value: Decimal
    period_certified_value: Decimal
    period_disputed_exposure: Decimal
    cumulative_claimed_value: Decimal
    cumulative_certified_value: Decimal
    cumulative_disputed_exposure: Decimal
    item_count: int
    valuation_snapshot_hash: str
    algorithm_version: str
    certified_by: Optional[str] = None
    certified_at: Optional[datetime] = None
    superseded_by: Optional[str] = None
    superseded_at: Optional[datetime] = None
    supersession_reason: Optional[str] = None
    created_at: datetime
    items: Optional[List[PeriodCertificateItemResponse]] = None


class PeriodCertificateSupersedeRequest(BaseModel):
    reason: str


class FinancialProgressSummaryResponse(BaseModel):
    project_id: str
    currency: str
    cumulative_earned_value: Decimal
    cumulative_claimed_value: Decimal
    cumulative_disputed_exposure: Decimal
    planned_valuation_status: str = "PLANNED_VALUATION_NOT_AVAILABLE"
    cumulative_planned_value: Optional[Decimal] = None
    schedule_variance_cost: Optional[Decimal] = None
