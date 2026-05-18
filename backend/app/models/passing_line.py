import uuid
from decimal import Decimal
from sqlalchemy import String, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PassingLine(Base):
    __tablename__ = "passing_lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id: Mapped[str] = mapped_column(String(36), ForeignKey("schools.id"), nullable=False)
    semester_id: Mapped[str] = mapped_column(String(36), ForeignKey("semesters.id"), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id"), nullable=False)
    passing_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("60.00"))
    makeup_passing_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("60.00"))

    school = relationship("School")
    semester = relationship("Semester")
    subject = relationship("Subject")