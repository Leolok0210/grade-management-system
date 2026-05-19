from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class GradeAnomaly(Base):
    __tablename__ = "grade_anomalies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    class_subject_id: Mapped[int] = mapped_column(ForeignKey("class_subjects.id"), nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False)
    anomaly_type: Mapped[str] = mapped_column(String(50), nullable=False)  # sudden_drop / statistical_outlier
    severity: Mapped[str] = mapped_column(String(10), default="low")  # low/medium/high
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student = relationship("Student")
    class_subject = relationship("ClassSubject")
    semester = relationship("Semester")
