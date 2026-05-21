"""
德育管理模型 - 獎懲、違紀、操行評估
"""
from datetime import datetime, date
from sqlalchemy import String, Integer, Text, Float, Boolean, ForeignKey, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class RewardPunishment(Base):
    __tablename__ = "reward_punishments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("academic_years.id"), nullable=False)

    # 獎勵記錄
    reward_type: Mapped[str] = mapped_column(String(20), nullable=True)  # 優點/小功/大功
    reward_count: Mapped[int] = mapped_column(Integer, default=0)
    reward_reason: Mapped[str] = mapped_column(Text, nullable=True)
    reward_date: Mapped[date] = mapped_column(Date, nullable=True)

    # 懲罰記錄
    punishment_type: Mapped[str] = mapped_column(String(20), nullable=True)  # 缺點/小過/大過
    punishment_count: Mapped[int] = mapped_column(Integer, default=0)
    punishment_reason: Mapped[str] = mapped_column(Text, nullable=True)
    punishment_date: Mapped[date] = mapped_column(Date, nullable=True)

    # 狀態
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RegularViolation(Base):
    __tablename__ = "regular_violations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("academic_years.id"), nullable=False)

    # 違規類型：欠作業/欠課本/上課違規/儀表不符/遲到/缺席/請假
    violation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=0)
    date: Mapped[date] = mapped_column(Date, nullable=True)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ConductAssessment(Base):
    __tablename__ = "conduct_assessments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False, unique=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("academic_years.id"), nullable=False)

    # 常規違紀統計（抵銷前）
    欠作業: Mapped[int] = mapped_column(Integer, default=0)
    欠課本: Mapped[int] = mapped_column(Integer, default=0)
    上課違規: Mapped[int] = mapped_column(Integer, default=0)
    儀表不符: Mapped[int] = mapped_column(Integer, default=0)
    遲到: Mapped[int] = mapped_column(Integer, default=0)
    缺席: Mapped[int] = mapped_column(Integer, default=0)
    請假: Mapped[int] = mapped_column(Integer, default=0)

    # 抵銷前統計
    before_1_5_fails: Mapped[int] = mapped_column(Integer, default=0)  # 1-5產生缺點
    before_6_fails: Mapped[int] = mapped_column(Integer, default=0)  # 6產生缺點
    before_special_fails: Mapped[int] = mapped_column(Integer, default=0)  # 非常規缺點
    before_total_fails: Mapped[int] = mapped_column(Integer, default=0)
    before_minor_infractions: Mapped[int] = mapped_column(Integer, default=0)  # 小過
    before_major_infractions: Mapped[int] = mapped_column(Integer, default=0)  # 大過
    before_rewards: Mapped[int] = mapped_column(Integer, default=0)  # 優點
    before_minor_awards: Mapped[int] = mapped_column(Integer, default=0)  # 小功
    before_major_awards: Mapped[int] = mapped_column(Integer, default=0)  # 大功

    # 抵銷後統計
    after_1_5_fails: Mapped[int] = mapped_column(Integer, default=0)
    after_6_fails: Mapped[int] = mapped_column(Integer, default=0)
    after_special_fails: Mapped[int] = mapped_column(Integer, default=0)
    after_total_fails: Mapped[int] = mapped_column(Integer, default=0)
    after_minor_infractions: Mapped[int] = mapped_column(Integer, default=0)
    after_major_infractions: Mapped[int] = mapped_column(Integer, default=0)
    after_rewards: Mapped[int] = mapped_column(Integer, default=0)
    after_minor_awards: Mapped[int] = mapped_column(Integer, default=0)
    after_major_awards: Mapped[int] = mapped_column(Integer, default=0)

    # 其他資訊
    volunteer_hours: Mapped[float] = mapped_column(Float, default=0)
    offset_count: Mapped[str] = mapped_column(String(50), nullable=True)  # 如 '1個缺點'

    # 操行評估
    max_assessment: Mapped[str] = mapped_column(String(10), nullable=True)  # 甲下/甲中/甲上/乙下/乙中/乙上
    previous_assessment: Mapped[str] = mapped_column(String(10), nullable=True)
    current_assessment: Mapped[str] = mapped_column(String(10), nullable=True)
    change: Mapped[str] = mapped_column(String(10), nullable=True)  # ↑/↓/--
    cumulative_fails: Mapped[int] = mapped_column(Integer, default=0)
    comment: Mapped[str] = mapped_column(Text, nullable=True)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)