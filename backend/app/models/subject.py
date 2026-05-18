import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Boolean, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id: Mapped[str] = mapped_column(String(36), ForeignKey("schools.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # 國文/數學/英文
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    school = relationship("School")


class ClassSubject(Base):
    __tablename__ = "class_subjects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    class_id: Mapped[str] = mapped_column(String(36), ForeignKey("classes.id"), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id"), nullable=False)
    teacher_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    semester_id: Mapped[str] = mapped_column(String(36), ForeignKey("semesters.id"), nullable=False)
    daily_weight: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0.40"))
    midterm_weight: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0.30"))
    final_weight: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0.30"))
    passing_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("60.00"))

    class_ = relationship("Class")
    subject = relationship("Subject")
    teacher = relationship("User")
    semester = relationship("Semester")