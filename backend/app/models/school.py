import uuid
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class School(Base):
    __tablename__ = "schools"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    campuses = relationship("Campus", back_populates="school", lazy="selectin")
    academic_years = relationship("AcademicYear", back_populates="school", lazy="selectin")


class Campus(Base):
    __tablename__ = "campuses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id: Mapped[str] = mapped_column(String(36), ForeignKey("schools.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    school = relationship("School", back_populates="campuses")


class AcademicYear(Base):
    __tablename__ = "academic_years"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id: Mapped[str] = mapped_column(String(36), ForeignKey("schools.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(20), nullable=False)  # 114學年度
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)

    school = relationship("School", back_populates="academic_years")
    semesters = relationship("Semester", back_populates="academic_year", lazy="selectin")


class Semester(Base):
    __tablename__ = "semesters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    academic_year_id: Mapped[str] = mapped_column(String(36), ForeignKey("academic_years.id"), nullable=False)
    semester: Mapped[int] = mapped_column(nullable=False)  # 1 or 2
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)

    academic_year = relationship("AcademicYear", back_populates="semesters")