from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.deps import get_current_user
from app.models.subject import Subject
from app.models.user import User

router = APIRouter(prefix="/subjects", tags=["科目管理"])


class SubjectResponse(BaseModel):
    id: str
    name: str
    code: str
    school_id: str

    model_config = {"from_attributes": True}


@router.get("", response_model=list[SubjectResponse])
async def list_subjects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Subject).filter(Subject.school_id == current_user.school_id).all()