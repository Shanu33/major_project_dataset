from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.db.models import User
from app.schemas.resource_performance import (
    ResourcePerformanceCreateRequest,
    ResourcePerformanceSnapshotResponse,
    ResourcePerformanceSummaryResponse,
    ResourcePerformanceSupersedeRequest,
)
from app.services.resource_performance_service import (
    create_resource_performance_snapshot,
    finalize_resource_performance_snapshot,
    get_resource_performance_snapshot,
    get_resource_performance_summary,
    list_resource_performance_snapshots,
    supersede_resource_performance_snapshot,
)

router = APIRouter(prefix="/api/projects/{project_id}/resource-performance", tags=["resource-performance"])


@router.post("", response_model=ResourcePerformanceSnapshotResponse, status_code=status.HTTP_201_CREATED)
def create_snapshot(
    project_id: str,
    data: ResourcePerformanceCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_resource_performance_snapshot(db, project_id, data, current_user)


@router.get("/summary", response_model=ResourcePerformanceSummaryResponse)
def get_summary(
    project_id: str,
    activity_id: Optional[str] = Query(None),
    resource_category: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_resource_performance_summary(
        db, project_id, current_user, activity_id, resource_category, resource_id
    )


@router.get("/activity/{activity_id}", response_model=List[ResourcePerformanceSnapshotResponse])
def list_by_activity(
    project_id: str,
    activity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_resource_performance_snapshots(db, project_id, current_user, activity_id=activity_id)


@router.get("", response_model=List[ResourcePerformanceSnapshotResponse])
def list_snapshots(
    project_id: str,
    activity_id: Optional[str] = Query(None),
    resource_category: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    material_item_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    performance_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_resource_performance_snapshots(
        db,
        project_id,
        current_user,
        activity_id=activity_id,
        resource_category=resource_category,
        resource_id=resource_id,
        material_item_id=material_item_id,
        status_filter=status_filter,
        performance_status=performance_status,
    )


@router.get("/{performance_id}", response_model=ResourcePerformanceSnapshotResponse)
def get_snapshot(
    project_id: str,
    performance_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_resource_performance_snapshot(db, project_id, performance_id, current_user)


@router.post("/{performance_id}/finalize", response_model=ResourcePerformanceSnapshotResponse)
def finalize_snapshot(
    project_id: str,
    performance_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return finalize_resource_performance_snapshot(db, project_id, performance_id, current_user)


@router.post("/{performance_id}/supersede", response_model=ResourcePerformanceSnapshotResponse)
def supersede_snapshot(
    project_id: str,
    performance_id: str,
    payload: ResourcePerformanceSupersedeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return supersede_resource_performance_snapshot(
        db,
        project_id,
        performance_id,
        payload.supersession_reason,
        current_user,
        replacement_snapshot_id=payload.replacement_snapshot_id,
    )
