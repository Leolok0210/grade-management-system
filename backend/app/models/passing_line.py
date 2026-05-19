from decimal import Decimal
from sqlalchemy import String, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PassingLine(Base):
    __tablename__ = "passing_lines"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    passing_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("60.00"))
    makeup_passing_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("60.00"))

    school = relationship("School")
    semester = relationship("Semester")
    subject = relationship("Subject")
