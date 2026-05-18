import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class GradeAppeal(Base):
    __tablename__ = "grade_appeals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False)
    class_subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("class_subjects.id"), nullable=False)
    semester_id: Mapped[str] = mapped_column(String(36), ForeignKey("semesters.id"), nullable=False)
    reason: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(10), default="submitted")  # submitted/reviewing/approved/rejected
    reviewed_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    review_comment: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student = relationship("Student")
    class_subject = relationship("ClassSubject")
    semester = relationship("Semester")
    reviewer = relationship("User")