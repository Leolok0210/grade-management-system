"""
學年成績檢查技能
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.semester_grade import SemesterGrade
from app.models.school import Semester
from app.models.student import Student, Class
from app.models.subject import ClassSubject, Subject


class YearReview(BaseSkill):
    name = "grade_check.year_review"
    description = "學年成績檢查，比較上下學期成績變化，查看學年總體表現"
    parameters = {
        "type": "object",
        "properties": {
            "academic_year_id": {"type": "integer", "description": "學年ID"},
            "class_id": {"type": "integer", "description": "班級ID（可選）"},
        },
        "required": ["academic_year_id"],
    }
    required_role = "admin"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        semesters = db.query(Semester).filter(
            Semester.academic_year_id == params["academic_year_id"],
        ).order_by(Semester.semester).all()

        if len(semesters) < 2:
            return SkillResult(success=False, message="需要上下學期資料才能進行學年檢查")

        sem1, sem2 = semesters[0], semesters[1]

        classes = db.query(Class).filter(Class.school_id == context.school_id)
        if params.get("class_id"):
            classes = classes.filter(Class.id == params["class_id"])
        classes = classes.all()

        rows = []
        for cls in classes:
            students = db.query(Student).filter(Student.class_id == cls.id).all()
            for student in students:
                sem1_grades = db.query(SemesterGrade).filter(
                    SemesterGrade.student_id == student.id,
                    SemesterGrade.semester_id == sem1.id,
                    SemesterGrade.semester_score.isnot(None),
                ).all()
                sem2_grades = db.query(SemesterGrade).filter(
                    SemesterGrade.student_id == student.id,
                    SemesterGrade.semester_id == sem2.id,
                    SemesterGrade.semester_score.isnot(None),
                ).all()

                sem1_avg = round(sum(float(g.semester_score) for g in sem1_grades) / len(sem1_grades), 2) if sem1_grades else 0
                sem2_avg = round(sum(float(g.semester_score) for g in sem2_grades) / len(sem2_grades), 2) if sem2_grades else 0
                year_avg = round((sem1_avg + sem2_avg) / 2, 2)
                change = round(sem2_avg - sem1_avg, 2)

                if sem1_grades or sem2_grades:
                    rows.append([cls.name, student.name, sem1_avg, sem2_avg, year_avg, f"+{change}" if change > 0 else str(change)])

        rows.sort(key=lambda x: x[4], reverse=True)

        return SkillResult(
            success=True,
            message=f"學年成績檢查完成，共 {len(rows)} 位學生",
            data_card={
                "type": "table",
                "title": "學年成績檢查",
                "payload": {
                    "columns": ["班級", "學生", "上學期平均", "下學期平均", "學年總平均", "變化"],
                    "rows": rows[:50],
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return "學年成績檢查"