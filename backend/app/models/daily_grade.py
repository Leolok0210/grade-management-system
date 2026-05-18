import uuid
from datetime import datetime
from datetime import date as date_type
from decimal import Decimal
from sqlalchemy import String, Date, ForeignKey, DateTime, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class DailyGradeItem(Base):
    __tablename__ = "daily_grade_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    class_subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("class_subjects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)  # 第三次數學小考
    grade_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 作業/小考/課堂參與/口試/其他
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    max_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("100.00"))
    weight: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("1.00"))
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    class_subject = relationship("ClassSubject")
    creator = relationship("User")
    grades = relationship("DailyGrade", back_populates="item", lazy="selectin")


class DailyGrade(Base):
    __tablename__ = "daily_grades"
    __table_args__ = (UniqueConstraint("daily_grade_item_id", "student_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    daily_grade_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("daily_grade_items.id"), nullable=False)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    comment: Mapped[str] = mapped_column(String(500), nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    item = relationship("DailyGradeItem", back_populates="grades")
    student = relationship("Student")
    creator = relationship("User")