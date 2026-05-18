import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class GradeAnomaly(Base):
    __tablename__ = "grade_anomalies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False)
    class_subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("class_subjects.id"), nullable=False)
    semester_id: Mapped[str] = mapped_column(String(36), ForeignKey("semesters.id"), nullable=False)
    anomaly_type: Mapped[str] = mapped_column(String(50), nullable=False)  # sudden_drop / statistical_outlier
    severity: Mapped[str] = mapped_column(String(10), default="low")  # low/medium/high
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student = relationship("Student")
    class_subject = relationship("ClassSubject")
    semester = relationship("Semester")