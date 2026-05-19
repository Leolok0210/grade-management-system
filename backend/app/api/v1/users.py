from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.deps import get_current_user, require_role
from app.models.user import User
from app.auth.jwt import hash_password

router = APIRouter(prefix="/users", tags=["使用者管理"])


class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    role: str  # admin / dept_head / teacher
    school_id: int


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    username: str
    name: str
    role: str
    school_id: int
    is_active: bool

    model_config = {"from_attributes": True}


@router.get("", response_model=list[UserResponse])
async def list_users(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return db.query(User).filter(User.school_id == current_user.school_id).all()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="使用者名稱已存在")

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        name=data.name,
        role=data.role,
        school_id=data.school_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user