from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.database import get_db
from app.db.models import Project, ProjectBaseline, User
from app.schemas.schemas import BaselineFreeze
from app.api.dependencies import require_supervisor, require_project_access
from app.services.audit import log_action

router = APIRouter()

@router.post("/freeze", dependencies=[Depends(require_project_access)])
def freeze_baseline(project_id: str, freeze_in: BaselineFreeze, db: Session = Depends(get_db), current_user: User = Depends(require_supervisor)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    current_active = db.query(ProjectBaseline).filter(ProjectBaseline.project_id == project_id, ProjectBaseline.is_active == True).first()
    
    new_rev = 0
    if current_active:
        current_active.is_active = False
        new_rev = current_active.revision_number + 1
        db.add(current_active)
        
    new_baseline = ProjectBaseline(
        project_id=project_id,
        revision_number=new_rev,
        frozen_by=current_user.id,
        reason_for_revision=freeze_in.reason_for_revision,
        is_active=True
    )
    db.add(new_baseline)
    db.flush()
    
    project.active_baseline_id = new_baseline.id
    log_action(db, current_user.id, "FREEZE_BASELINE", "ProjectBaseline", new_baseline.id, freeze_in.reason_for_revision)
    
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Concurrency conflict: Another baseline is actively being frozen.")

    db.refresh(new_baseline)
    return {"id": new_baseline.id, "revision_number": new_baseline.revision_number}

@router.get("/", dependencies=[Depends(require_project_access)])
def get_baselines(project_id: str, db: Session = Depends(get_db)):
    return [{"id": b.id, "revision_number": b.revision_number, "is_active": b.is_active} for b in db.query(ProjectBaseline).filter(ProjectBaseline.project_id == project_id).all()]
