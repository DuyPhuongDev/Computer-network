from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import Users
from service.auth import hash_password, authenticate_user, create_access_token, get_current_user, get_current_user_optional
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["auth"])

# Pydantic models cho request/response
class UserCreate(BaseModel):
    username: str
    full_name: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    status: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class StatusUpdate(BaseModel):
    status: str  # 'online', 'offline', 'invisible'

class GuestRequest(BaseModel):
    username: str
    
# Register endpoint
@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Kiểm tra username đã tồn tại chưa
    existing_user = db.query(Users).filter(Users.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Tạo user mới
    hashed_password = hash_password(user.password)
    db_user = Users(
        username=user.username,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_active=True,
        status="offline"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Login endpoint
@router.post("/login", response_model=Token)
async def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=timedelta(hours=24)
    )
    # set status to online
    user.status = "online"
    db.commit()
    db.refresh(user)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login-guest", response_model=Token)
async def loginGuest(guest: GuestRequest):
    # guest => not need check db => response token
    access_token = create_access_token(
        data={"sub": guest.username}, expires_delta=timedelta(hours=24)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# Get current user
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Users = Depends(get_current_user_optional)):
    return current_user

# Update status
@router.put("/status", response_model=UserResponse)
async def update_status(status_update: StatusUpdate, current_user: Users = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    if status_update.status not in ["online", "offline", "invisible"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    current_user.status = status_update.status
    db.commit()
    db.refresh(current_user)
    return current_user