import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Boolean, Date, ForeignKey, DateTime, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class SemesterGrade(Base):
    __tablename__ = "semester_grades"
    __table_args__ = (UniqueConstraint("student_id", "class_subject_id", "semester_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False)
    class_subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("class_subjects.id"), nullable=False)
    semester_id: Mapped[str] = mapped_column(String(36), ForeignKey("semesters.id"), nullable=False)
    daily_avg: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)
    midterm_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)
    final_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)
    semester_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)
    is_passing: Mapped[bool] = mapped_column(Boolean, nullable=True)
    status: Mapped[str] = mapped_column(String(10), default="draft")  # draft / confirmed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student = relationship("Student")
    class_subject = relationship("ClassSubject")
    semester = relationship("Semester")


class MakeupExam(Base):
    __tablename__ = "makeup_exams"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False)
    class_subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("class_subjects.id"), nullable=False)
    semester_id: Mapped[str] = mapped_column(String(36), ForeignKey("semesters.id"), nullable=False)
    original_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)
    makeup_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)
    makeup_date: Mapped[date] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(10), default="pending")  # pending/passed/failed/absent
    registered_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student = relationship("Student")
    class_subject = relationship("ClassSubject")
    semester = relationship("Semester")
    registrar = relationship("User")