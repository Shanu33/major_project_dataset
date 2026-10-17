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
