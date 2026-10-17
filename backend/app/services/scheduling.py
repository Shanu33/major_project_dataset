"""Phase 1H: Deterministic Construction Scheduling Service.

Implements:
- Activity & dependency creation with append-only revisions
- Unit normalization (canonical unit: day)
- Zero and negative duration rejection (strict duration > 0 policy)
- Strong duration provenance validation (USER_PROVIDED, RULE_BASED, DETERMINISTIC)
- ResourcePlan semantic isolation
- Transaction-safe schedule versioning with row locking
- Deterministic Kahn's topological sort and CPM calculations (Decimal arithmetic)
- Complete input snapshot preservation
- Transactional audit logging
"""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import (
    Project,
    EngineeringElement,
    ConstructionActivity,
    ConstructionActivityRevision,
    ActivityDependency,
    ActivityDependencyRevision,
    ConstructionSchedule,
    ActivityScheduleResult,
    Rule,
    RuleBasedEstimation,
    EngineeringCalculation,
    ResourcePlan,
    generate_uuid,
)
from app.schemas.schemas import (
    ActivityCreate,
    DependencyCreate,
    DurationMethodEnum,
    DurationClassificationEnum,
    ActivityTypeEnum,
)
from app.services.audit import log_action


CANONICAL_DURATION_UNIT = "day"
SUPPORTED_DURATION_UNITS = {"day", "days", "d", "hour", "hours", "hr", "h"}
SUPPORTED_LAG_UNITS = {"day", "days", "d", "hour", "hours", "hr", "h"}


def normalize_to_canonical_days(value: Decimal, unit: Optional[str]) -> Decimal:
    """Normalize hours or days to canonical days using exact Decimal arithmetic."""
    if not unit or not unit.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_INPUT: Unit must be specified when value is provided."
        )
    clean_unit = unit.strip().lower()
    if clean_unit in {"day", "days", "d"}:
        return value
    elif clean_unit in {"hour", "hours", "hr", "h"}:
        # 1 day = 24 hours
        return value / Decimal("24")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"INVALID_INPUT: Unsupported unit '{unit}'. Only 'hour' and 'day' are supported."
        )


def validate_duration_provenance(
    db: Session,
    project_id: str,
    duration_value: Optional[Decimal],
    duration_unit: Optional[str],
    duration_method: DurationMethodEnum,
    duration_classification: DurationClassificationEnum,
    metadata_json: Optional[Dict[str, Any]],
) -> None:
    """Enforce explicit provenance rules for activity durations."""
    if duration_value is not None:
        if duration_value <= Decimal("0"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: Activity duration must be greater than zero. Zero and negative durations are prohibited."
            )
        if not duration_unit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: Unit must be specified when duration value is provided."
            )
        clean_unit = duration_unit.strip().lower()
        if clean_unit not in SUPPORTED_DURATION_UNITS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"INVALID_INPUT: Unsupported duration unit '{duration_unit}'."
            )

    meta = metadata_json or {}
    source_type = meta.get("source_type")
    source_id = meta.get("source_id")

    # ResourcePlan semantic isolation check: ResourcePlan cannot become duration
    if source_type in {"RESOURCE_PLAN", "RESOURCE_DEMAND", "RESOURCE"} or (
        source_id and db.query(ResourcePlan).filter(ResourcePlan.id == source_id).first()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_INPUT: ResourcePlan cannot be directly converted to activity duration without an explicit duration rule."
        )

    if duration_method == DurationMethodEnum.USER_PROVIDED:
        if duration_classification not in {
            DurationClassificationEnum.USER_PROVIDED,
            DurationClassificationEnum.ASSUMPTION_BASED,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: USER_PROVIDED duration method must have USER_PROVIDED or ASSUMPTION_BASED classification."
            )
        if source_type and source_type not in {"USER_PROVIDED", "MANUAL", "USER"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: USER_PROVIDED duration method cannot specify non-user source_type."
            )

    elif duration_method == DurationMethodEnum.RULE_BASED:
        if duration_classification not in {
            DurationClassificationEnum.ASSUMPTION_BASED,
            DurationClassificationEnum.CALCULATED,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: RULE_BASED duration method must have ASSUMPTION_BASED or CALCULATED classification."
            )
        if not source_id or not source_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: RULE_BASED duration requires metadata_json with valid source_type and source_id."
            )
        # Verify source_id points to an actual RuleDefinition or RuleBasedEstimation
        rule = db.query(Rule).filter(Rule.id == source_id).first()
        estimation = db.query(RuleBasedEstimation).filter(RuleBasedEstimation.id == source_id).first()
        if not rule and not estimation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: Invalid RULE_BASED duration source. Referenced rule or estimation does not exist."
            )
        if rule and rule.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: Referenced rule definition is inactive."
            )

    elif duration_method == DurationMethodEnum.DETERMINISTIC:
        if duration_classification != DurationClassificationEnum.CALCULATED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: DETERMINISTIC duration method must have CALCULATED classification."
            )
        if not source_id or not source_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: DETERMINISTIC duration requires metadata_json with valid source_type and source_id."
            )
        # Verify source_id points to an actual EngineeringCalculation
        calc = db.query(EngineeringCalculation).filter(EngineeringCalculation.id == source_id).first()
        if not calc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: Invalid DETERMINISTIC duration source. Referenced engineering calculation does not exist."
            )


def create_activity(
    db: Session,
    project_id: str,
    activity_in: ActivityCreate,
    current_user_id: str,
) -> ConstructionActivity:
    """Create a new construction activity and record Revision 1."""
    # Check duplicate activity_code
    existing = db.query(ConstructionActivity).filter(
        ConstructionActivity.project_id == project_id,
        ConstructionActivity.activity_code == activity_in.activity_code,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Activity with code '{activity_in.activity_code}' already exists in this project."
        )

    # Validate engineering element ownership if provided
    if activity_in.engineering_element_id:
        element = db.query(EngineeringElement).filter(
            EngineeringElement.id == activity_in.engineering_element_id,
            EngineeringElement.project_id == project_id,
        ).first()
        if not element:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Engineering element does not exist or does not belong to this project."
            )

    # Validate provenance and duration
    validate_duration_provenance(
        db=db,
        project_id=project_id,
        duration_value=activity_in.duration_value,
        duration_unit=activity_in.duration_unit,
        duration_method=activity_in.duration_method,
        duration_classification=activity_in.duration_classification,
        metadata_json=activity_in.metadata_json,
    )

    activity_id = generate_uuid()
    activity = ConstructionActivity(
        id=activity_id,
        project_id=project_id,
        engineering_element_id=activity_in.engineering_element_id,
        activity_code=activity_in.activity_code,
        activity_name=activity_in.activity_name,
        description=activity_in.description,
        activity_type=activity_in.activity_type.value if hasattr(activity_in.activity_type, "value") else activity_in.activity_type,
        duration_value=activity_in.duration_value,
        duration_unit=activity_in.duration_unit,
        duration_method=activity_in.duration_method.value if hasattr(activity_in.duration_method, "value") else activity_in.duration_method,
        duration_classification=activity_in.duration_classification.value if hasattr(activity_in.duration_classification, "value") else activity_in.duration_classification,
        status="ACTIVE",
        created_by=current_user_id,
        metadata_json=activity_in.metadata_json,
    )
    db.add(activity)

    # Append Revision 1
    revision = ConstructionActivityRevision(
        id=generate_uuid(),
        activity_id=activity_id,
        project_id=project_id,
        revision_number=1,
        activity_code=activity.activity_code,
        activity_name=activity.activity_name,
        description=activity.description,
        activity_type=activity.activity_type,
        engineering_element_id=activity.engineering_element_id,
        duration_value=activity.duration_value,
        duration_unit=activity.duration_unit,
        duration_method=activity.duration_method,
        duration_classification=activity.duration_classification,
        status=activity.status,
        metadata_json=activity.metadata_json,
        created_by=current_user_id,
        revision_note="Initial activity creation",
    )
    db.add(revision)

    log_action(
        db=db,
        user_id=current_user_id,
        action="CREATE_ACTIVITY",
        entity_type="ConstructionActivity",
        entity_id=activity.id,
        reason=f"Created activity {activity.activity_code} (rev 1)",
    )

    db.commit()
    db.refresh(activity)
    return activity


def create_dependency(
    db: Session,
    project_id: str,
    predecessor_activity_id: str,
    dependency_in: DependencyCreate,
    current_user_id: str,
) -> ActivityDependency:
    """Create an activity dependency and record Revision 1 with cycle detection."""
    # Check self-dependency
    if predecessor_activity_id == dependency_in.successor_activity_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Self-dependency is prohibited. Activity cannot depend on itself."
        )

    # Validate predecessor activity
    pred = db.query(ConstructionActivity).filter(
        ConstructionActivity.id == predecessor_activity_id,
        ConstructionActivity.project_id == project_id,
    ).first()
    if not pred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Predecessor activity does not exist or does not belong to this project."
        )

    # Validate successor activity
    succ = db.query(ConstructionActivity).filter(
        ConstructionActivity.id == dependency_in.successor_activity_id,
        ConstructionActivity.project_id == project_id,
    ).first()
    if not succ:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Successor activity does not exist or does not belong to this project."
        )

    # Check active status
    if pred.status != "ACTIVE" or succ.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create dependency involving inactive or deprecated activities."
        )

    # Validate lag
    if dependency_in.lag_value < Decimal("0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_INPUT: Negative lag is prohibited."
        )
    if not dependency_in.lag_unit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_INPUT: Unit must be specified for dependency lag."
        )
    clean_unit = dependency_in.lag_unit.strip().lower()
    if clean_unit not in SUPPORTED_LAG_UNITS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"INVALID_INPUT: Unsupported lag unit '{dependency_in.lag_unit}'."
        )

    # Check duplicate dependency
    existing = db.query(ActivityDependency).filter(
        ActivityDependency.project_id == project_id,
        ActivityDependency.predecessor_activity_id == predecessor_activity_id,
        ActivityDependency.successor_activity_id == dependency_in.successor_activity_id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This dependency already exists."
        )

    # Cycle Detection: DFS from successor to predecessor
    # If predecessor is reachable from successor, adding pred -> succ would create a cycle
    all_deps = db.query(ActivityDependency).filter(
        ActivityDependency.project_id == project_id
    ).all()
    graph: Dict[str, List[str]] = {}
    for d in all_deps:
        graph.setdefault(d.predecessor_activity_id, []).append(d.successor_activity_id)

    visited = set()
    stack = [dependency_in.successor_activity_id]
    while stack:
        curr = stack.pop()
        if curr == predecessor_activity_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CIRCULAR_DEPENDENCY: Adding this dependency would create a cycle."
            )
        if curr not in visited:
            visited.add(curr)
            stack.extend(graph.get(curr, []))

    dep_id = generate_uuid()
    dependency = ActivityDependency(
        id=dep_id,
        project_id=project_id,
        predecessor_activity_id=predecessor_activity_id,
        successor_activity_id=dependency_in.successor_activity_id,
        dependency_type=dependency_in.dependency_type.value if hasattr(dependency_in.dependency_type, "value") else dependency_in.dependency_type,
        lag_value=dependency_in.lag_value,
        lag_unit=dependency_in.lag_unit,
        created_by=current_user_id,
        metadata_json=dependency_in.metadata_json,
    )
    db.add(dependency)

    # Append Revision 1
    revision = ActivityDependencyRevision(
        id=generate_uuid(),
        dependency_id=dep_id,
        project_id=project_id,
        revision_number=1,
        predecessor_activity_id=predecessor_activity_id,
        successor_activity_id=dependency_in.successor_activity_id,
        dependency_type=dependency.dependency_type,
        lag_value=dependency.lag_value,
        lag_unit=dependency.lag_unit,
        created_by=current_user_id,
        revision_note="Initial dependency creation",
    )
    db.add(revision)

    log_action(
        db=db,
        user_id=current_user_id,
        action="CREATE_DEPENDENCY",
        entity_type="ActivityDependency",
        entity_id=dependency.id,
        reason=f"Created dependency {predecessor_activity_id} -> {dependency_in.successor_activity_id} (rev 1)",
    )

    db.commit()
    db.refresh(dependency)
    return dependency


def calculate_cpm_schedule(
    db: Session,
    project_id: str,
    current_user_id: str,
) -> ConstructionSchedule:
    """Calculate CPM construction schedule transactionally with row locking."""
    # 1. Lock project row to prevent concurrent calculation and duplicate versions
    project = db.query(Project).filter(Project.id == project_id).with_for_update().first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )

    # 2. Fetch active activities
    activities = db.query(ConstructionActivity).filter(
        ConstructionActivity.project_id == project_id,
        ConstructionActivity.status == "ACTIVE",
    ).order_by(ConstructionActivity.activity_code.asc(), ConstructionActivity.id.asc()).all()

    if not activities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_INPUT: No active activities in project to schedule."
        )

    # 3. Validate durations and normalize to canonical unit (day)
    normalized_durations: Dict[str, Decimal] = {}
    for act in activities:
        if act.duration_value is None or act.duration_value <= Decimal("0"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"REQUIRES_INPUT: Activity '{act.activity_code}' has missing or non-positive duration."
            )
        norm_dur = normalize_to_canonical_days(Decimal(str(act.duration_value)), act.duration_unit)
        normalized_durations[act.id] = norm_dur

    # 4. Fetch dependencies
    dependencies = db.query(ActivityDependency).filter(
        ActivityDependency.project_id == project_id
    ).order_by(ActivityDependency.created_at.asc()).all()

    normalized_lags: Dict[str, Decimal] = {}
    for dep in dependencies:
        if dep.lag_value < Decimal("0"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INPUT: Negative lag is prohibited."
            )
        norm_lag = normalize_to_canonical_days(Decimal(str(dep.lag_value)), dep.lag_unit)
        normalized_lags[dep.id] = norm_lag

    # Build adjacency lists and in-degree map
    activity_ids = {a.id for a in activities}
    adj: Dict[str, List[tuple]] = {a.id: [] for a in activities}
    rev_adj: Dict[str, List[tuple]] = {a.id: [] for a in activities}
    in_degree: Dict[str, int] = {a.id: 0 for a in activities}

    for dep in dependencies:
        if dep.predecessor_activity_id in activity_ids and dep.successor_activity_id in activity_ids:
            adj[dep.predecessor_activity_id].append((dep.successor_activity_id, dep))
            rev_adj[dep.successor_activity_id].append((dep.predecessor_activity_id, dep))
            in_degree[dep.successor_activity_id] += 1

    # 5. Deterministic Kahn's Topological Sort
    # Zero in-degree queue sorted by (activity_code, id) for repeatable ordering
    act_map = {a.id: a for a in activities}
    zero_in_degree = [a.id for a in activities if in_degree[a.id] == 0]
    zero_in_degree.sort(key=lambda x: (act_map[x].activity_code, act_map[x].id))

    topo_order: List[str] = []
    while zero_in_degree:
        curr_id = zero_in_degree.pop(0)
        topo_order.append(curr_id)

        for succ_id, _ in sorted(adj[curr_id], key=lambda item: (act_map[item[0]].activity_code, act_map[item[0]].id)):
            in_degree[succ_id] -= 1
            if in_degree[succ_id] == 0:
                zero_in_degree.append(succ_id)
                zero_in_degree.sort(key=lambda x: (act_map[x].activity_code, act_map[x].id))

    if len(topo_order) < len(activities):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CIRCULAR_DEPENDENCY: Graph contains circular dependency cycle."
        )

    # 6. CPM Forward Pass (Early Start / Early Finish)
    es: Dict[str, Decimal] = {}
    ef: Dict[str, Decimal] = {}

    for act_id in topo_order:
        dur = normalized_durations[act_id]
        if not rev_adj[act_id]:
            es[act_id] = Decimal("0.000000")
        else:
            max_ef = Decimal("0.000000")
            for pred_id, dep in rev_adj[act_id]:
                lag = normalized_lags[dep.id]
                cand = ef[pred_id] + lag
                if cand > max_ef:
                    max_ef = cand
            es[act_id] = max_ef
        ef[act_id] = es[act_id] + dur

    project_duration = max(ef.values()) if ef else Decimal("0.000000")

    # 7. CPM Backward Pass (Late Start / Late Finish)
    ls: Dict[str, Decimal] = {}
    lf: Dict[str, Decimal] = {}

    for act_id in reversed(topo_order):
        dur = normalized_durations[act_id]
        if not adj[act_id]:
            lf[act_id] = project_duration
        else:
            min_ls = None
            for succ_id, dep in adj[act_id]:
                lag = normalized_lags[dep.id]
                cand = ls[succ_id] - lag
                if min_ls is None or cand < min_ls:
                    min_ls = cand
            lf[act_id] = min_ls
        ls[act_id] = lf[act_id] - dur

    # 8. Floats and Critical Path
    total_float: Dict[str, Decimal] = {}
    is_critical: Dict[str, bool] = {}
    critical_path: List[str] = []

    for act_id in topo_order:
        tf = ls[act_id] - es[act_id]
        # Quantize or round float to 6 decimals for zero comparison
        tf_rounded = tf.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        total_float[act_id] = tf
        crit = (tf_rounded == Decimal("0.000000"))
        is_critical[act_id] = crit
        if crit:
            critical_path.append(act_id)

    # 9. Complete Input Snapshot
    activities_snapshot = [
        {
            "id": a.id,
            "project_id": a.project_id,
            "activity_code": a.activity_code,
            "activity_name": a.activity_name,
            "description": a.description,
            "activity_type": a.activity_type,
            "engineering_element_id": a.engineering_element_id,
            "duration_value": str(a.duration_value) if a.duration_value is not None else None,
            "duration_unit": a.duration_unit,
            "normalized_duration_value": str(normalized_durations[a.id]),
            "normalized_duration_unit": CANONICAL_DURATION_UNIT,
            "duration_method": a.duration_method,
            "duration_classification": a.duration_classification,
            "status": a.status,
            "metadata_json": a.metadata_json,
        }
        for a in activities
    ]

    dependencies_snapshot = [
        {
            "id": d.id,
            "project_id": d.project_id,
            "predecessor_activity_id": d.predecessor_activity_id,
            "successor_activity_id": d.successor_activity_id,
            "dependency_type": d.dependency_type,
            "lag_value": str(d.lag_value),
            "lag_unit": d.lag_unit,
            "normalized_lag_value": str(normalized_lags[d.id]),
            "normalized_lag_unit": CANONICAL_DURATION_UNIT,
            "metadata_json": d.metadata_json,
        }
        for d in dependencies
    ]

    input_snapshot = {
        "algorithm_version": "CPM_1.0_DETERMINISTIC",
        "canonical_schedule_unit": CANONICAL_DURATION_UNIT,
        "activities": activities_snapshot,
        "dependencies": dependencies_snapshot,
    }

    # 10. Version Calculation
    existing_versions = db.query(ConstructionSchedule.schedule_version).filter(
        ConstructionSchedule.project_id == project_id
    ).all()
    max_major = 0
    for (v,) in existing_versions:
        try:
            m = int(float(v))
            if m > max_major:
                max_major = m
        except (ValueError, TypeError):
            pass
    next_version = f"{max_major + 1}.0"

    # 11. Supersede previous active schedules
    db.query(ConstructionSchedule).filter(
        ConstructionSchedule.project_id == project_id,
        ConstructionSchedule.calculation_status == "CALCULATED",
    ).update({"calculation_status": "SUPERSEDED"}, synchronize_session=False)

    # 12. Create ConstructionSchedule record
    schedule_id = generate_uuid()
    schedule = ConstructionSchedule(
        id=schedule_id,
        project_id=project_id,
        schedule_version=next_version,
        calculation_status="CALCULATED",
        project_duration=project_duration,
        duration_unit=CANONICAL_DURATION_UNIT,
        calculated_by=current_user_id,
        algorithm_version="CPM_1.0_DETERMINISTIC",
        input_snapshot_json=input_snapshot,
        result_summary_json={
            "total_activities": len(activities),
            "critical_activities_count": len(critical_path),
            "critical_path": critical_path,
            "project_duration_days": str(project_duration),
        },
    )
    db.add(schedule)

    # 13. Create ActivityScheduleResult records
    for act_id in topo_order:
        res = ActivityScheduleResult(
            id=generate_uuid(),
            schedule_id=schedule_id,
            activity_id=act_id,
            es=es[act_id],
            ef=ef[act_id],
            ls=ls[act_id],
            lf=lf[act_id],
            total_float=total_float[act_id],
            is_critical=is_critical[act_id],
        )
        db.add(res)

    # 14. Transactional Audit Log
    log_action(
        db=db,
        user_id=current_user_id,
        action="CALCULATE_SCHEDULE",
        entity_type="ConstructionSchedule",
        entity_id=schedule.id,
        reason=f"Calculated CPM schedule version {next_version}",
    )

    db.commit()
    db.refresh(schedule)
    return schedule
