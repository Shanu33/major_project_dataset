import os

BASE_DIR = '/home/shahnawaz/Documents/DataRequirement/backend'

files = {
    'app/__init__.py': '',
    'app/main.py': '''
from fastapi import FastAPI
from app.db.database import engine, Base
from app.api.endpoints import auth, projects, baselines, reports
from contextlib import asynccontextmanager

Base.metadata.create_all(bind=engine)

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
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./mvp.db")

settings = Settings()
''',
    'app/core/security.py': '''
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
from passlib.hash import sha256_crypt

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
''',
    'app/db/database.py': '''
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from app.core.config import settings

TESTING = os.getenv("TESTING", "0") == "1"
if TESTING:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
else:
    SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

connect_args = {"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

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
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, JSON, Enum
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
    active_baseline_id = Column(String, ForeignKey("project_baselines.id"), nullable=True)
    baselines = relationship("ProjectBaseline", back_populates="project", foreign_keys="ProjectBaseline.project_id")

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
    role: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    role: str
    class Config:
        from_attributes = True

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
from app.db.models import User

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
            raise HTTPException(status_code=403, detail="Operation not permitted")
        return current_user
    return role_checker

def require_admin(current_user: User = Depends(require_role(["admin"]))):
    return current_user

def require_contractor(current_user: User = Depends(require_role(["contractor", "admin"]))):
    return current_user

def require_supervisor(current_user: User = Depends(require_role(["supervisor", "admin"]))):
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
    db.commit()
''',
    'app/api/endpoints/auth.py': '''
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.db.database import get_db
from app.db.models import User
from app.schemas.schemas import UserCreate, UserResponse
from app.core.security import get_password_hash, verify_password, create_access_token
from datetime import timedelta
from app.core.config import settings

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_in.email).first()
    if db_user:
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
from app.db.models import Project, User
from app.schemas.schemas import ProjectCreate
from app.api.dependencies import get_current_user, require_contractor
from app.services.audit import log_action

router = APIRouter()

@router.post("/")
def create_project(project_in: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(require_contractor)):
    project = Project(name=project_in.name, created_by=current_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    log_action(db, current_user.id, "CREATE_PROJECT", "Project", project.id)
    return project

@router.get("/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
''',
    'app/api/endpoints/baselines.py': '''
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Project, ProjectBaseline, User
from app.schemas.schemas import BaselineFreeze
from app.api.dependencies import require_contractor, require_supervisor
from app.services.audit import log_action

router = APIRouter()

@router.post("/freeze")
def freeze_baseline(project_id: str, freeze_in: BaselineFreeze, db: Session = Depends(get_db), current_user: User = Depends(require_supervisor)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    current_active = db.query(ProjectBaseline).filter(ProjectBaseline.project_id == project_id, ProjectBaseline.is_active == True).first()
    
    new_rev = 0
    if current_active:
        current_active.is_active = False
        new_rev = current_active.revision_number + 1
    
    new_baseline = ProjectBaseline(
        project_id=project_id,
        revision_number=new_rev,
        frozen_by=current_user.id,
        reason_for_revision=freeze_in.reason_for_revision,
        is_active=True
    )
    db.add(new_baseline)
    db.commit()
    db.refresh(new_baseline)
    
    project.active_baseline_id = new_baseline.id
    db.commit()
    
    log_action(db, current_user.id, "FREEZE_BASELINE", "ProjectBaseline", new_baseline.id, freeze_in.reason_for_revision)
    return new_baseline

@router.get("/")
def get_baselines(project_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_contractor)):
    return db.query(ProjectBaseline).filter(ProjectBaseline.project_id == project_id).all()
''',
    'app/api/endpoints/reports.py': '''
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import DailyReport, ReportVerification, Project, User
from app.schemas.schemas import DailyReportSubmit, VerificationSubmit
from app.api.dependencies import require_contractor, require_supervisor
from app.services.audit import log_action

router = APIRouter()

@router.post("/")
def submit_report(project_id: str, report_in: DailyReportSubmit, db: Session = Depends(get_db), current_user: User = Depends(require_contractor)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
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
    db.commit()
    db.refresh(report)
    log_action(db, current_user.id, "SUBMIT_REPORT", "DailyReport", report.id)
    return report

@router.put("/{report_id}")
def update_report(project_id: str, report_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_contractor)):
    raise HTTPException(status_code=405, detail="Finalized reports cannot be modified. Submit a new report or add a correction.")

@router.delete("/{report_id}")
def delete_report(project_id: str, report_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_contractor)):
    raise HTTPException(status_code=405, detail="Finalized reports cannot be deleted.")

@router.post("/{report_id}/verify")
def verify_report(project_id: str, report_id: str, verify_in: VerificationSubmit, db: Session = Depends(get_db), current_user: User = Depends(require_supervisor)):
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if db.query(ReportVerification).filter(ReportVerification.daily_report_id == report_id).first():
        raise HTTPException(status_code=400, detail="Report already verified")
    
    verification = ReportVerification(
        daily_report_id=report_id,
        verified_by=current_user.id,
        supervisor_verified_work=verify_in.supervisor_verified_work,
        status=verify_in.status
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)
    log_action(db, current_user.id, "VERIFY_REPORT", "ReportVerification", verification.id)
    return verification
''',
    'tests/conftest.py': '''
import os
os.environ["TESTING"] = "1"
''',
    'tests/test_invariants.py': '''
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import Base, engine, get_db
from sqlalchemy.orm import sessionmaker

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
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_auth_and_project_creation(setup_db):
    client.post("/api/auth/register", json={"email": "contractor@test.com", "password": "pass", "role": "contractor"})
    client.post("/api/auth/register", json={"email": "super@test.com", "password": "pass", "role": "supervisor"})
    
    res = client.post("/api/auth/login", data={"username": "contractor@test.com", "password": "pass"})
    c_token = res.json()["access_token"]
    
    res = client.post("/api/auth/login", data={"username": "super@test.com", "password": "pass"})
    s_token = res.json()["access_token"]
    
    res = client.post("/api/projects/", json={"name": "Test Project"}, headers={"Authorization": f"Bearer {c_token}"})
    assert res.status_code == 200
    project_id = res.json()["id"]
    
    return project_id, c_token, s_token

def test_baseline_freeze(setup_db):
    project_id, c_token, s_token = test_auth_and_project_creation(setup_db)
    
    res = client.post(f"/api/projects/{project_id}/baselines/freeze", json={"reason_for_revision": "Initial"}, headers={"Authorization": f"Bearer {s_token}"})
    assert res.status_code == 200
    assert res.json()["revision_number"] == 0
    
    res = client.post(f"/api/projects/{project_id}/baselines/freeze", json={"reason_for_revision": "Revision 1"}, headers={"Authorization": f"Bearer {s_token}"})
    assert res.status_code == 200
    assert res.json()["revision_number"] == 1
    
    res = client.get(f"/api/projects/{project_id}/baselines/", headers={"Authorization": f"Bearer {c_token}"})
    baselines = res.json()
    assert len(baselines) == 2
    assert baselines[0]["is_active"] == False
    assert baselines[1]["is_active"] == True
    
    return project_id, c_token, s_token

def test_immutability_and_daily_reports(setup_db):
    project_id, c_token, s_token = test_baseline_freeze(setup_db)
    
    res = client.post(
        f"/api/projects/{project_id}/reports/",
        json={"contractor_declared_work": {"concrete": 10}},
        headers={"Authorization": f"Bearer {c_token}"}
    )
    assert res.status_code == 200
    report_id = res.json()["id"]
    
    res = client.put(
        f"/api/projects/{project_id}/reports/{report_id}",
        json={"contractor_declared_work": {"concrete": 12}},
        headers={"Authorization": f"Bearer {c_token}"}
    )
    assert res.status_code == 405
    
    res = client.delete(
        f"/api/projects/{project_id}/reports/{report_id}",
        headers={"Authorization": f"Bearer {c_token}"}
    )
    assert res.status_code == 405
    
    res = client.post(
        f"/api/projects/{project_id}/reports/{report_id}/verify",
        json={"supervisor_verified_work": {"concrete": 8}, "status": "disputed"},
        headers={"Authorization": f"Bearer {s_token}"}
    )
    assert res.status_code == 200
    assert res.json()["supervisor_verified_work"] == {"concrete": 8}
    assert res.json()["status"] == "disputed"
'''
}

for filepath, content in files.items():
    os.makedirs(os.path.dirname(os.path.join(BASE_DIR, filepath)), exist_ok=True)
    with open(os.path.join(BASE_DIR, filepath), 'w') as f:
        f.write(content.strip() + '\
')

print("Backend scaffolding created successfully.")
