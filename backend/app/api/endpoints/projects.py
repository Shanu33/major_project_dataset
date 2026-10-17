from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Project, ProjectMember, User
from app.schemas.schemas import ProjectCreate
from app.api.dependencies import require_contractor, require_project_access, require_admin
from app.services.audit import log_action

router = APIRouter()

@router.post("/")
def create_project(project_in: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(require_contractor)):
    project = Project(name=project_in.name, created_by=current_user.id)
    db.add(project)
    db.flush()
    
    member = ProjectMember(project_id=project.id, user_id=current_user.id)
    db.add(member)
    
    log_action(db, current_user.id, "CREATE_PROJECT", "Project", project.id)
    db.commit()
    return {"id": project.id, "name": project.name}

@router.get("/{project_id}", dependencies=[Depends(require_project_access)])
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"id": project.id, "name": project.name}

@router.post("/{project_id}/members", dependencies=[Depends(require_admin)])
def add_project_member(project_id: str, user_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    member = db.query(ProjectMember).filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id).first()
    if not member:
        member = ProjectMember(project_id=project_id, user_id=user_id)
        db.add(member)
        db.commit()
    return {"status": "ok"}
