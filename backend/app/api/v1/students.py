from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.deps import get_current_user
from app.models.student import Student, Class
from app.models.user import User

router = APIRouter(prefix="/students", tags=["學生管理"])


class StudentResponse(BaseModel):
    id: str
    student_no: str
    name: str
    class_id: str
    status: str

    model_config = {"from_attributes": True}


class ClassResponse(BaseModel):
    id: str
    name: str
    grade_level: int
    class_number: int
    school_id: str

    model_config = {"from_attributes": True}


@router.get("/classes", response_model=list[ClassResponse])
async def list_classes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Class).filter(Class.school_id == current_user.school_id).all()


@router.get("", response_model=list[StudentResponse])
async def list_students(
    class_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Student)
    if class_id:
        query = query.filter(Student.class_id == class_id)
    return query.all()