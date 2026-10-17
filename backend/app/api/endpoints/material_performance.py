from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.db.models import User
from app.schemas.material_performance import (
    MaterialPerformanceCreateRequest,
    MaterialPerformanceSnapshotResponse,
    MaterialPerformanceSummaryResponse,
    MaterialPerformanceSupersedeRequest,
)
from app.services.material_performance_service import (
    create_material_performance_snapshot,
    finalize_material_performance_snapshot,
    get_material_performance_snapshot,
    get_material_performance_summary,
    list_material_performance_snapshots,
    supersede_material_performance_snapshot,
)

router = APIRouter()


@router.post(
    "/projects/{project_id}/material-performance",
    response_model=MaterialPerformanceSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create material performance snapshot",
)
def create_performance_snapshot_endpoint(
    project_id: str,
    data: MaterialPerformanceCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_material_performance_snapshot(db, project_id, data, current_user)


@router.get(
    "/projects/{project_id}/material-performance",
    response_model=List[MaterialPerformanceSnapshotResponse],
    summary="List material performance snapshots",
)
def list_performance_snapshots_endpoint(
    project_id: str,
    activity_id: Optional[str] = Query(None),
    material_item_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    performance_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_material_performance_snapshots(
        db,
        project_id,
        current_user,
        activity_id=activity_id,
        material_item_id=material_item_id,
        status_filter=status_filter,
        performance_status=performance_status,
    )


@router.get(
    "/projects/{project_id}/material-performance/summary",
    response_model=MaterialPerformanceSummaryResponse,
    summary="Get aggregated material performance summary",
)
def get_performance_summary_endpoint(
    project_id: str,
    activity_id: Optional[str] = Query(None),
    material_item_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_material_performance_summary(
        db,
        project_id,
        current_user,
        activity_id=activity_id,
        material_item_id=material_item_id,
    )


@router.get(
    "/projects/{project_id}/material-performance/activity/{activity_id}",
    response_model=List[MaterialPerformanceSnapshotResponse],
    summary="Get performance snapshots for an activity",
)
def get_activity_performance_snapshots_endpoint(
    project_id: str,
    activity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_material_performance_snapshots(
        db,
        project_id,
        current_user,
        activity_id=activity_id,
    )


@router.get(
    "/projects/{project_id}/material-performance/material/{material_item_id}",
    response_model=List[MaterialPerformanceSnapshotResponse],
    summary="Get performance snapshots for a material",
)
def get_material_performance_snapshots_endpoint(
    project_id: str,
    material_item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_material_performance_snapshots(
        db,
        project_id,
        current_user,
        material_item_id=material_item_id,
    )


@router.get(
    "/projects/{project_id}/material-performance/{performance_id}",
    response_model=MaterialPerformanceSnapshotResponse,
    summary="Get single material performance snapshot",
)
def get_performance_snapshot_endpoint(
    project_id: str,
    performance_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_material_performance_snapshot(
        db,
        project_id,
        performance_id,
        current_user,
    )


@router.post(
    "/projects/{project_id}/material-performance/{performance_id}/finalize",
    response_model=MaterialPerformanceSnapshotResponse,
    summary="Finalize material performance snapshot",
)
def finalize_performance_snapshot_endpoint(
    project_id: str,
    performance_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return finalize_material_performance_snapshot(
        db,
        project_id,
        performance_id,
        current_user,
    )


@router.post(
    "/projects/{project_id}/material-performance/{performance_id}/supersede",
    response_model=MaterialPerformanceSnapshotResponse,
    summary="Supersede material performance snapshot",
)
def supersede_performance_snapshot_endpoint(
    project_id: str,
    performance_id: str,
    payload: MaterialPerformanceSupersedeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return supersede_material_performance_snapshot(
        db,
        project_id,
        performance_id,
        payload.supersession_reason,
        current_user,
        replacement_snapshot_id=payload.replacement_snapshot_id,
    )

