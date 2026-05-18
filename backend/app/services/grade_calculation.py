"""
加權成績計算服務
根據 class_subject 的權重設定，計算學期總成績
"""
from decimal import Decimal
from app.models.subject import ClassSubject
from app.models.semester_grade import SemesterGrade
from app.models.daily_grade import DailyGrade, DailyGradeItem


def calculate_semester_score(grade: SemesterGrade, class_subject: ClassSubject, db) -> Decimal:
    """計算學期總成績 = 平時平均 * daily_weight + 期中 * midterm_weight + 期末 * final_weight"""

    # 計算平時成績加權平均
    daily_avg = grade.daily_avg
    if daily_avg is None:
        # 從 daily_grades 計算
        daily_grades = db.query(DailyGrade).join(DailyGradeItem).filter(
            DailyGradeItem.class_subject_id == class_subject.id,
            DailyGrade.student_id == grade.student_id,
        ).all()

        if daily_grades:
            total_weighted = sum(float(g.score) * float(g.item.weight) for g in daily_grades)
            total_weight = sum(float(g.item.weight) for g in daily_grades)
            daily_avg = Decimal(str(round(total_weighted / total_weight, 2))) if total_weight > 0 else Decimal("0")
            grade.daily_avg = daily_avg

    # 計算學期總成績
    daily_weight = float(class_subject.daily_weight)
    midterm_weight = float(class_subject.midterm_weight)
    final_weight = float(class_subject.final_weight)

    daily_val = float(daily_avg or 0)
    midterm_val = float(grade.midterm_score or 0)
    final_val = float(grade.final_score or 0)

    semester_score = round(
        daily_val * daily_weight + midterm_val * midterm_weight + final_val * final_weight,
        2,
    )

    grade.semester_score = Decimal(str(semester_score))
    grade.is_passing = semester_score >= float(class_subject.passing_score)

    return grade.semester_score