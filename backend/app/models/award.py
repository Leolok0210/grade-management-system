import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AwardType(Base):
    __tablename__ = "award_types"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id: Mapped[str] = mapped_column(String(36), ForeignKey("schools.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # 學業優良獎/進步獎
    criteria = mapped_column(JSON, nullable=True)

    school = relationship("School")


class StudentAward(Base):
    __tablename__ = "student_awards"
    __table_args__ = (UniqueConstraint("student_id", "award_type_id", "semester_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False)
    award_type_id: Mapped[str] = mapped_column(String(36), ForeignKey("award_types.id"), nullable=False)
    semester_id: Mapped[str] = mapped_column(String(36), ForeignKey("semesters.id"), nullable=False)
    granted_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    comment: Mapped[str] = mapped_column(String(500), nullable=True)

    student = relationship("Student")
    award_type = relationship("AwardType")
    semester = relationship("Semester")
    granter = relationship("User")