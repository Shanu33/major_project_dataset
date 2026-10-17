from datetime import date, datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.db.models import User
from app.schemas.schedule_performance import (
    SchedulePerformanceCreateRequest,
    SchedulePerformanceSnapshotResponse,
    SchedulePerformanceSummaryResponse,
    SchedulePerformanceSupersedeRequest,
)
from app.services.schedule_performance_service import (
    create_schedule_performance_snapshot,
    finalize_schedule_performance_snapshot,
    get_schedule_performance_snapshot,
    get_schedule_performance_summary,
    list_schedule_performance_snapshots,
    supersede_schedule_performance_snapshot,
)

router = APIRouter(prefix="/api/projects/{project_id}", tags=["schedule-performance"])


@router.post(
    "/schedule-performance",
    response_model=SchedulePerformanceSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create schedule performance snapshot",
)
def create_snapshot_endpoint(
    project_id: str,
    data: SchedulePerformanceCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_schedule_performance_snapshot(db, project_id, data, current_user)


@router.get(
    "/schedule-performance/summary",
    response_model=SchedulePerformanceSummaryResponse,
    summary="Get aggregated schedule performance summary",
)
def get_summary_endpoint(
    project_id: str,
    evaluation_date: Optional[date] = Query(None, description="Cutoff evaluation date for summary calculation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_date = evaluation_date or datetime.now(timezone.utc).date()
    return get_schedule_performance_summary(db, project_id, target_date, current_user)


@router.get(
    "/activities/{activity_id}/schedule-performance",
    response_model=List[SchedulePerformanceSnapshotResponse],
    summary="Get schedule performance snapshots for an activity",
)
def get_activity_schedule_performance_endpoint(
    project_id: str,
    activity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_schedule_performance_snapshots(
        db,
        project_id,
        current_user,
        activity_id=activity_id,
    )


@router.get(
    "/schedule-performance",
    response_model=List[SchedulePerformanceSnapshotResponse],
    summary="List schedule performance snapshots for a project",
)
def list_snapshots_endpoint(
    project_id: str,
    activity_id: Optional[str] = Query(None),
    schedule_id: Optional[str] = Query(None),
    delay_status: Optional[str] = Query(None),
    performance_status: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_schedule_performance_snapshots(
        db,
        project_id,
        current_user,
        activity_id=activity_id,
        schedule_id=schedule_id,
        delay_status=delay_status,
        performance_status=performance_status,
        status_filter=status_filter,
    )


@router.get(
    "/schedule-performance/{performance_id}",
    response_model=SchedulePerformanceSnapshotResponse,
    summary="Get single schedule performance snapshot",
)
def get_snapshot_endpoint(
    project_id: str,
    performance_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_schedule_performance_snapshot(db, project_id, performance_id, current_user)


@router.post(
    "/schedule-performance/{performance_id}/finalize",
    response_model=SchedulePerformanceSnapshotResponse,
    summary="Finalize schedule performance snapshot",
)
def finalize_snapshot_endpoint(
    project_id: str,
    performance_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return finalize_schedule_performance_snapshot(db, project_id, performance_id, current_user)


@router.post(
    "/schedule-performance/{performance_id}/supersede",
    response_model=SchedulePerformanceSnapshotResponse,
    summary="Supersede finalized schedule performance snapshot",
)
def supersede_snapshot_endpoint(
    project_id: str,
    performance_id: str,
    data: SchedulePerformanceSupersedeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return supersede_schedule_performance_snapshot(
        db,
        project_id,
        performance_id,
        data.supersession_reason,
        data.replacement_snapshot_id,
        current_user,
    )

