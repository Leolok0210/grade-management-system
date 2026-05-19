from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AwardType(Base):
    __tablename__ = "award_types"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # 學業優良獎/進步獎
    criteria = mapped_column(JSON, nullable=True)

    school = relationship("School")


class StudentAward(Base):
    __tablename__ = "student_awards"
    __table_args__ = (UniqueConstraint("student_id", "award_type_id", "semester_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    award_type_id: Mapped[int] = mapped_column(ForeignKey("award_types.id"), nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False)
    granted_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    comment: Mapped[str] = mapped_column(String(500), nullable=True)

    student = relationship("Student")
    award_type = relationship("AwardType")
    semester = relationship("Semester")
    granter = relationship("User")
