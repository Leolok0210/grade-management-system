"""
Conduct report skills.
"""
from app.skills.conduct.reports.class_monthly_report import ClassMonthlyReport
from app.skills.conduct.reports.student_individual_report import StudentIndividualReport
from app.skills.conduct.reports.rewards_punishments_report import RewardsPunishmentsReport
from app.skills.conduct.reports.regular_violations_report import RegularViolationsReport

__all__ = [
    "ClassMonthlyReport",
    "StudentIndividualReport",
    "RewardsPunishmentsReport",
    "RegularViolationsReport",
]