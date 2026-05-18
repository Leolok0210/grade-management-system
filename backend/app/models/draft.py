import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class DraftGradeList(Base):
    __tablename__ = "draft_grade_lists"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    class_id: Mapped[str] = mapped_column(String(36), ForeignKey("classes.id"), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id"), nullable=False)
    semester_id: Mapped[str] = mapped_column(String(36), ForeignKey("semesters.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(10), default="draft")  # draft/reviewed/finalized
    data = mapped_column(JSON, nullable=False)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    class_ = relationship("Class")
    subject = relationship("Subject")
    semester = relationship("Semester")
    creator = relationship("User")