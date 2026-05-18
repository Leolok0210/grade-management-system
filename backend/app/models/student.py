import uuid
from datetime import datetime
from sqlalchemy import String, SmallInteger, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Class(Base):
    __tablename__ = "classes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id: Mapped[str] = mapped_column(String(36), ForeignKey("schools.id"), nullable=False)
    campus_id: Mapped[str] = mapped_column(String(36), ForeignKey("campuses.id"), nullable=True)
    academic_year_id: Mapped[str] = mapped_column(String(36), ForeignKey("academic_years.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # 三年二班
    grade_level: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1-6
    class_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    homeroom_teacher_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    school = relationship("School")
    campus = relationship("Campus")
    academic_year = relationship("AcademicYear")
    homeroom_teacher = relationship("User")
    students = relationship("Student", back_populates="class_", lazy="selectin")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    class_id: Mapped[str] = mapped_column(String(36), ForeignKey("classes.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(10), default="active")  # active/transferred/graduated/dropped
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    class_ = relationship("Class", back_populates="students")