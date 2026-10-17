import os

BASE_DIR = '/home/shahnawaz/Documents/DataRequirement/backend'

files = {
    'app/__init__.py': '',
    'app/main.py': '''
from fastapi import FastAPI
from app.api.endpoints import auth, projects, baselines, reports

app = FastAPI(title="Construction Intelligence MVP")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(baselines.router, prefix="/api/projects/{project_id}/baselines", tags=["baselines"])
app.include_router(reports.router, prefix="/api/projects/{project_id}/reports", tags=["reports"])

@app.get("/")
def health_check():
    return {"status": "ok"}
''',
    'app/core/config.py': '''
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    if not SECRET_KEY and os.getenv("TESTING") != "1":
        raise ValueError("SECRET_KEY environment variable MUST be set in production")
    elif not SECRET_KEY:
        SECRET_KEY = "test_secret_key"
        
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    TESTING: bool = os.getenv("TESTING") == "1"
    if TESTING:
        DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg://shahnawaz:password@localhost:5433/construction_intel_test")
    else:
        DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg://shahnawaz:password@localhost:5433/construction_intel")

settings = Settings()
''',
    'app/core/security.py': '''
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
''',
    'app/db/database.py': '''
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
''',
    'app/db/models.py': '''
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON, Index, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)

class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    created_by = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    active_baseline_id = Column(String, ForeignKey("project_baselines.id", use_alter=True, name="fk_active_baseline"), nullable=True)
    baselines = relationship("ProjectBaseline", back_populates="project", foreign_keys="ProjectBaseline.project_id")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")

class ProjectMember(Base):
    __tablename__ = "project_members"
    project_id = Column(String, ForeignKey("projects.id"), primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    project = relationship("Project", back_populates="members")

class ProjectBaseline(Base):
    __tablename__ = "project_baselines"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    revision_number = Column(Integer, default=0)
    frozen_by = Column(String, ForeignKey("users.id"))
    frozen_at = Column(DateTime(timezone=True), server_default=func.now())
    reason_for_revision = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    project = relationship("Project", back_populates="baselines", foreign_keys=[project_id])

    __table_args__ = (
        Index('uq_active_baseline', 'project_id', unique=True, postgresql_where=text("is_active = true")),
    )

class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"))
    filename = Column(String)
    file_path = Column(String)
    file_hash = Column(String)
    uploaded_by = Column(String, ForeignKey("users.id"))
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())

class DailyReport(Base):
    __tablename__ = "daily_reports"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"))
    baseline_id = Column(String, ForeignKey("project_baselines.id"))
    submitted_by = Column(String, ForeignKey("users.id"))
    contractor_declared_work = Column(JSON, nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    is_finalized = Column(Boolean, default=False)
    verification = relationship("ReportVerification", back_populates="report", uselist=False)

class ReportVerification(Base):
    __tablename__ = "report_verifications"
    id = Column(String, primary_key=True, default=generate_uuid)
    daily_report_id = Column(String, ForeignKey("daily_reports.id"))
    verified_by = Column(String, ForeignKey("users.id"))
    supervisor_verified_work = Column(JSON, nullable=False)
    status = Column(String, nullable=False)
    verified_at = Column(DateTime(timezone=True), server_default=func.now())
    report = relationship("DailyReport", back_populates="verification")

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    action = Column(String, nullable=False)
    entity_type = Column(String)
    entity_id = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    reason = Column(String)
''',
    'app/schemas/schemas.py': '''
from pydantic import BaseModel, EmailStr
from typing import Optional, Any, Dict

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserCreateAdmin(BaseModel):
    email: EmailStr
    password: str
    role: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    role: str

class ProjectCreate(BaseModel):
    name: str

class BaselineFreeze(BaseModel):
    reason_for_revision: str = "Initial Baseline"

class DailyReportSubmit(BaseModel):
    contractor_declared_work: Dict[str, Any]

class VerificationSubmit(BaseModel):
    supervisor_verified_work: Dict[str, Any]
    status: str
''',
    'app/api/dependencies.py': '''
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.database import get_db
from app.db.models import User, ProjectMember, Project

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def require_role(roles: list):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Operation not permitted for role")
        return current_user
    return role_checker

require_admin = require_role(["admin"])
require_contractor = require_role(["contractor", "admin"])
require_supervisor = require_role(["supervisor", "admin"])

def require_project_access(project_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == "admin":
        return current_user
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if project.created_by == current_user.id:
        return current_user
        
    member = db.query(ProjectMember).filter(ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not authorized to access this project")
        
    return current_user
''',
    'app/services/audit.py': '''
from sqlalchemy.orm import Session
from app.db.models import AuditLog

def log_action(db: Session, user_id: str, action: str, entity_type: str, entity_id: str, reason: str = ""):
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        reason=reason
    )
    db.add(log)
    # MUST COMMIT in caller to maintain atomicity!
''',
    'app/api/endpoints/auth.py': '''
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.db.database import get_db
from app.db.models import User
from app.schemas.schemas import UserCreate, UserCreateAdmin, UserResponse
from app.core.security import get_password_hash, verify_password, create_access_token
from app.api.dependencies import get_current_user, require_admin
from datetime import timedelta
from app.core.config import settings

router = APIRouter()

@router.post("/register/public", response_model=UserResponse)
def register_public(user_in: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_in.password)
    new_user = User(email=user_in.email, password_hash=hashed_password, role="contractor")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/register/admin", response_model=UserResponse)
def register_admin(user_in: UserCreateAdmin, db: Session = Depends(get_db)):
    if db.query(User).count() > 0:
        raise HTTPException(status_code=403, detail="Admins must be created by existing admins. Bootstrap closed.")
    
    hashed_password = get_password_hash(user_in.password)
    new_user = User(email=user_in.email, password_hash=hashed_password, role="admin")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/users", response_model=UserResponse, dependencies=[Depends(require_admin)])
def create_user_as_admin(user_in: UserCreateAdmin, db: Session = Depends(get_db)):
    if user_in.role not in ["admin", "contractor", "supervisor"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_in.password)
    new_user = User(email=user_in.email, password_hash=hashed_password, role=user_in.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
''',
    'app/api/endpoints/projects.py': '''
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
''',
    'app/api/endpoints/baselines.py': '''
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
''',
    'app/api/endpoints/reports.py': '''
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import DailyReport, ReportVerification, Project, User
from app.schemas.schemas import DailyReportSubmit, VerificationSubmit
from app.api.dependencies import require_contractor, require_supervisor, require_project_access
from app.services.audit import log_action

router = APIRouter()

@router.post("/", dependencies=[Depends(require_project_access)])
def submit_report(project_id: str, report_in: DailyReportSubmit, db: Session = Depends(get_db), current_user: User = Depends(require_contractor)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project.active_baseline_id:
        raise HTTPException(status_code=400, detail="Cannot submit report before baseline freeze")
    
    report = DailyReport(
        project_id=project_id,
        baseline_id=project.active_baseline_id,
        submitted_by=current_user.id,
        contractor_declared_work=report_in.contractor_declared_work,
        is_finalized=True
    )
    db.add(report)
    db.flush()
    log_action(db, current_user.id, "SUBMIT_REPORT", "DailyReport", report.id)
    db.commit()
    return {"id": report.id}

@router.put("/{report_id}", dependencies=[Depends(require_project_access)])
def update_report(project_id: str, report_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_contractor)):
    raise HTTPException(status_code=405, detail="Finalized reports cannot be modified. Submit a new report or add a correction.")

@router.delete("/{report_id}", dependencies=[Depends(require_project_access)])
def delete_report(project_id: str, report_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_contractor)):
    raise HTTPException(status_code=405, detail="Finalized reports cannot be deleted.")

@router.post("/{report_id}/verify", dependencies=[Depends(require_project_access)])
def verify_report(project_id: str, report_id: str, verify_in: VerificationSubmit, db: Session = Depends(get_db), current_user: User = Depends(require_supervisor)):
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    if report.project_id != project_id:
        raise HTTPException(status_code=400, detail="Project/Report mismatch")
    
    if db.query(ReportVerification).filter(ReportVerification.daily_report_id == report_id).first():
        raise HTTPException(status_code=400, detail="Report already verified")
    
    verification = ReportVerification(
        daily_report_id=report_id,
        verified_by=current_user.id,
        supervisor_verified_work=verify_in.supervisor_verified_work,
        status=verify_in.status
    )
    db.add(verification)
    db.flush()
    log_action(db, current_user.id, "VERIFY_REPORT", "ReportVerification", verification.id)
    db.commit()
    return {"id": verification.id, "supervisor_verified_work": verification.supervisor_verified_work, "status": verification.status}
''',
    'tests/conftest.py': '''
import os
os.environ["TESTING"] = "1"
os.environ["SECRET_KEY"] = "test_key_for_ci_cd"
''',
    'tests/test_invariants.py': '''
import pytest
import os
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import engine, get_db
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from alembic.config import Config
from alembic import command

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    alembic_cfg = Config("alembic.ini")
    
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    
    command.upgrade(alembic_cfg, "head")
    
    yield
    
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))

def test_migration_objects_exist(setup_db):
    db = TestingSessionLocal()
    idx = db.execute(text("SELECT indexname FROM pg_indexes WHERE indexname = 'uq_active_baseline'")).scalar()
    assert idx == 'uq_active_baseline', "uq_active_baseline index missing"
    
    trgs = db.execute(text("SELECT tgname FROM pg_trigger WHERE tgname IN ('prevent_update_delete_report_trg', 'prevent_audit_modification_trg')")).scalars().all()
    assert 'prevent_update_delete_report_trg' in trgs, "Report immutability trigger missing"
    assert 'prevent_audit_modification_trg' in trgs, "Audit immutability trigger missing"
    db.close()

def test_role_security_bootstrap(setup_db):
    res = client.post("/api/auth/register/admin", json={"email": "admin1@test.com", "password": "pass", "role": "contractor"})
    assert res.status_code == 200
    assert res.json()["role"] == "admin"
    
    res = client.post("/api/auth/register/admin", json={"email": "admin2@test.com", "password": "pass", "role": "admin"})
    assert res.status_code == 403
    
    res = client.post("/api/auth/register/public", json={"email": "hacker@test.com", "password": "pass"})
    assert res.status_code == 200
    assert res.json()["role"] == "contractor"

def test_auth_and_project_creation(setup_db):
    res_a = client.post("/api/auth/login", data={"username": "admin1@test.com", "password": "pass"})
    admin_token = res_a.json()["access_token"]

    client.post("/api/auth/users", json={"email": "c1@test.com", "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client.post("/api/auth/users", json={"email": "c2@test.com", "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client.post("/api/auth/users", json={"email": "s1@test.com", "password": "p", "role": "supervisor"}, headers={"Authorization": f"Bearer {admin_token}"})
    
    c1_t = client.post("/api/auth/login", data={"username": "c1@test.com", "password": "p"}).json()["access_token"]
    c2_t = client.post("/api/auth/login", data={"username": "c2@test.com", "password": "p"}).json()["access_token"]
    s1_t = client.post("/api/auth/login", data={"username": "s1@test.com", "password": "p"}).json()["access_token"]
    
    res = client.post("/api/projects/", json={"name": "P1"}, headers={"Authorization": f"Bearer {c1_t}"})
    assert res.status_code == 200
    project_id = res.json()["id"]
    
    res = client.get(f"/api/projects/{project_id}", headers={"Authorization": f"Bearer {c2_t}"})
    assert res.status_code == 403
    
    db = TestingSessionLocal()
    s1_id = db.execute(text("SELECT id FROM users WHERE email = 's1@test.com'")).scalar()
    db.close()
    
    res = client.post(f"/api/projects/{project_id}/members?user_id={s1_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    
    res = client.get(f"/api/projects/{project_id}", headers={"Authorization": f"Bearer {s1_t}"})
    assert res.status_code == 200
    
    return project_id, c1_t, s1_t, c2_t, admin_token

def test_baseline_freeze(setup_db):
    project_id, c1_t, s1_t, c2_t, admin_t = test_auth_and_project_creation(setup_db)
    
    res = client.post(f"/api/projects/{project_id}/baselines/freeze", json={}, headers={"Authorization": f"Bearer {c1_t}"})
    assert res.status_code == 403
    
    res = client.post(f"/api/projects/{project_id}/baselines/freeze", json={"reason_for_revision": "Initial"}, headers={"Authorization": f"Bearer {s1_t}"})
    assert res.status_code == 200
    assert res.json()["revision_number"] == 0
    
    res = client.post(f"/api/projects/{project_id}/baselines/freeze", json={"reason_for_revision": "Rev 1"}, headers={"Authorization": f"Bearer {s1_t}"})
    assert res.status_code == 200
    assert res.json()["revision_number"] == 1
    
    db = TestingSessionLocal()
    active_count = db.execute(text(f"SELECT COUNT(*) FROM project_baselines WHERE project_id='{project_id}' AND is_active=true")).scalar()
    db.close()
    assert active_count == 1
    
    return project_id, c1_t, s1_t

def test_report_immutability(setup_db):
    project_id, c1_t, s1_t = test_baseline_freeze(setup_db)
    
    res = client.post(
        f"/api/projects/{project_id}/reports/",
        json={"contractor_declared_work": {"concrete": 10}},
        headers={"Authorization": f"Bearer {c1_t}"}
    )
    assert res.status_code == 200
    report_id = res.json()["id"]
    
    res = client.delete(f"/api/projects/{project_id}/reports/{report_id}", headers={"Authorization": f"Bearer {c1_t}"})
    assert res.status_code == 405
    
    db = TestingSessionLocal()
    try:
        db.execute(text(f"DELETE FROM daily_reports WHERE id='{report_id}'"))
        db.commit()
        pytest.fail("DELETE on daily_reports succeeded, trigger failed!")
    except Exception as e:
        db.rollback()
        assert "Cannot update or delete" in str(e) or "Cannot update or delete a finalized daily report" in str(e)
        
    try:
        db.execute(text(f"UPDATE daily_reports SET is_finalized=false WHERE id='{report_id}'"))
        db.commit()
        pytest.fail("UPDATE on daily_reports succeeded, trigger failed!")
    except Exception as e:
        db.rollback()
        assert "Cannot update or delete" in str(e) or "Cannot update or delete a finalized daily report" in str(e)
    db.close()

def test_audit_log_immutability(setup_db):
    db = TestingSessionLocal()
    
    try:
        db.execute(text("DELETE FROM audit_log"))
        db.commit()
        pytest.fail("DELETE on audit_log succeeded, trigger failed!")
    except Exception as e:
        db.rollback()
        assert "Audit log records" in str(e) or "append-only" in str(e)

    try:
        db.execute(text("UPDATE audit_log SET action='HACKED'"))
        db.commit()
        pytest.fail("UPDATE on audit_log succeeded, trigger failed!")
    except Exception as e:
        db.rollback()
        assert "Audit log records" in str(e) or "append-only" in str(e)
        
    db.close()
'''
}

for filepath, content in files.items():
    with open(os.path.join(BASE_DIR, filepath), 'w') as f:
        f.write(content.strip() + '\n')
