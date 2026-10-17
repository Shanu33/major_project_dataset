from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import (
    User,
    ConstructionActivity,
    ConstructionActivityRevision,
    ActivityDependency,
    ActivityDependencyRevision,
    ConstructionSchedule,
    ActivityScheduleResult,
)
from app.api.dependencies import require_project_access
from app.schemas.schemas import (
    ActivityCreate,
    ActivityResponse,
    ActivityRevisionResponse,
    DependencyCreate,
    DependencyResponse,
    DependencyRevisionResponse,
    ScheduleResponse,
    ActivityScheduleResultResponse,
)
from app.services.scheduling import (
    create_activity,
    create_dependency,
    calculate_cpm_schedule,
)

router = APIRouter()


def build_schedule_response(schedule: ConstructionSchedule) -> ScheduleResponse:
    crit_ids = []
    if schedule.result_summary_json and "critical_path" in schedule.result_summary_json:
        crit_ids = schedule.result_summary_json["critical_path"]
    else:
        crit_ids = [r.activity_id for r in schedule.results if r.is_critical]

    results_dto = [
        ActivityScheduleResultResponse(
            id=r.id,
            schedule_id=r.schedule_id,
            activity_id=r.activity_id,
            activity_code=r.activity.activity_code if r.activity else None,
            activity_name=r.activity.activity_name if r.activity else None,
            es=r.es,
            ef=r.ef,
            ls=r.ls,
            lf=r.lf,
            total_float=r.total_float,
            is_critical=r.is_critical,
            created_at=r.created_at,
        )
        for r in schedule.results
    ]

    return ScheduleResponse(
        id=schedule.id,
        project_id=schedule.project_id,
        schedule_version=schedule.schedule_version,
        calculation_status=schedule.calculation_status,
        project_duration=schedule.project_duration,
        duration_unit=schedule.duration_unit,
        canonical_schedule_unit=schedule.duration_unit,
        calculated_at=schedule.calculated_at,
        calculated_by=schedule.calculated_by,
        algorithm_version=schedule.algorithm_version,
        input_snapshot_json=schedule.input_snapshot_json,
        result_summary_json=schedule.result_summary_json,
        created_at=schedule.created_at,
        critical_path=crit_ids,
        results=results_dto,
    )


# 1. Activities
@router.post("/activities", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
def create_project_activity(
    project_id: str,
    activity_in: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    activity = create_activity(
        db=db,
        project_id=project_id,
        activity_in=activity_in,
        current_user_id=current_user.id,
    )
    return activity


@router.get("/activities", response_model=List[ActivityResponse], status_code=status.HTTP_200_OK)
def list_project_activities(
    project_id: str,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    query = db.query(ConstructionActivity).filter(ConstructionActivity.project_id == project_id)
    if status_filter:
        query = query.filter(ConstructionActivity.status == status_filter)
    return query.order_by(ConstructionActivity.activity_code.asc()).all()


@router.get("/activities/{activity_id}", response_model=ActivityResponse, status_code=status.HTTP_200_OK)
def get_activity_detail(
    project_id: str,
    activity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    activity = db.query(ConstructionActivity).filter(
        ConstructionActivity.id == activity_id,
        ConstructionActivity.project_id == project_id,
    ).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found in this project."
        )
    return activity


@router.get("/activities/{activity_id}/revisions", response_model=List[ActivityRevisionResponse], status_code=status.HTTP_200_OK)
def list_activity_revisions(
    project_id: str,
    activity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    activity = db.query(ConstructionActivity).filter(
        ConstructionActivity.id == activity_id,
        ConstructionActivity.project_id == project_id,
    ).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found in this project."
        )
    return db.query(ConstructionActivityRevision).filter(
        ConstructionActivityRevision.activity_id == activity_id,
    ).order_by(ConstructionActivityRevision.revision_number.asc()).all()


# 2. Dependencies
@router.post("/activities/{activity_id}/dependencies", response_model=DependencyResponse, status_code=status.HTTP_201_CREATED)
def create_activity_dependency(
    project_id: str,
    activity_id: str,
    dependency_in: DependencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    dep = create_dependency(
        db=db,
        project_id=project_id,
        predecessor_activity_id=activity_id,
        dependency_in=dependency_in,
        current_user_id=current_user.id,
    )
    return DependencyResponse(
        id=dep.id,
        project_id=dep.project_id,
        predecessor_activity_id=dep.predecessor_activity_id,
        successor_activity_id=dep.successor_activity_id,
        predecessor_code=dep.predecessor.activity_code if dep.predecessor else None,
        successor_code=dep.successor.activity_code if dep.successor else None,
        dependency_type=dep.dependency_type,
        lag_value=dep.lag_value,
        lag_unit=dep.lag_unit,
        created_by=dep.created_by,
        created_at=dep.created_at,
        metadata_json=dep.metadata_json,
    )


@router.get("/dependencies", response_model=List[DependencyResponse], status_code=status.HTTP_200_OK)
def list_project_dependencies(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    deps = db.query(ActivityDependency).filter(
        ActivityDependency.project_id == project_id
    ).all()
    return [
        DependencyResponse(
            id=d.id,
            project_id=d.project_id,
            predecessor_activity_id=d.predecessor_activity_id,
            successor_activity_id=d.successor_activity_id,
            predecessor_code=d.predecessor.activity_code if d.predecessor else None,
            successor_code=d.successor.activity_code if d.successor else None,
            dependency_type=d.dependency_type,
            lag_value=d.lag_value,
            lag_unit=d.lag_unit,
            created_by=d.created_by,
            created_at=d.created_at,
            metadata_json=d.metadata_json,
        )
        for d in deps
    ]


@router.get("/dependencies/{dependency_id}/revisions", response_model=List[DependencyRevisionResponse], status_code=status.HTTP_200_OK)
def list_dependency_revisions(
    project_id: str,
    dependency_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    dep = db.query(ActivityDependency).filter(
        ActivityDependency.id == dependency_id,
        ActivityDependency.project_id == project_id,
    ).first()
    if not dep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dependency not found in this project."
        )
    return db.query(ActivityDependencyRevision).filter(
        ActivityDependencyRevision.dependency_id == dependency_id,
    ).order_by(ActivityDependencyRevision.revision_number.asc()).all()


# 3. Schedule Calculations
@router.post("/schedules/calculate", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def calculate_schedule(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    schedule = calculate_cpm_schedule(
        db=db,
        project_id=project_id,
        current_user_id=current_user.id,
    )
    return build_schedule_response(schedule)


@router.get("/schedules", response_model=List[ScheduleResponse], status_code=status.HTTP_200_OK)
def list_project_schedules(
    project_id: str,
    calculation_status: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    query = db.query(ConstructionSchedule).filter(ConstructionSchedule.project_id == project_id)
    if calculation_status:
        query = query.filter(ConstructionSchedule.calculation_status == calculation_status)
    schedules = query.order_by(ConstructionSchedule.created_at.desc()).all()
    return [build_schedule_response(s) for s in schedules]


@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse, status_code=status.HTTP_200_OK)
def get_schedule_detail(
    project_id: str,
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    schedule = db.query(ConstructionSchedule).filter(
        ConstructionSchedule.id == schedule_id,
        ConstructionSchedule.project_id == project_id,
    ).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found in this project."
        )
    return build_schedule_response(schedule)


@router.get("/schedules/{schedule_id}/results", response_model=List[ActivityScheduleResultResponse], status_code=status.HTTP_200_OK)
def get_schedule_results(
    project_id: str,
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access),
):
    schedule = db.query(ConstructionSchedule).filter(
        ConstructionSchedule.id == schedule_id,
        ConstructionSchedule.project_id == project_id,
    ).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found in this project."
        )

    results = db.query(ActivityScheduleResult).filter(
        ActivityScheduleResult.schedule_id == schedule_id
    ).order_by(ActivityScheduleResult.es.asc()).all()

    return [
        ActivityScheduleResultResponse(
            id=r.id,
            schedule_id=r.schedule_id,
            activity_id=r.activity_id,
            activity_code=r.activity.activity_code if r.activity else None,
            activity_name=r.activity.activity_name if r.activity else None,
            es=r.es,
            ef=r.ef,
            ls=r.ls,
            lf=r.lf,
            total_float=r.total_float,
            is_critical=r.is_critical,
            created_at=r.created_at,
        )
        for r in results
    ]
