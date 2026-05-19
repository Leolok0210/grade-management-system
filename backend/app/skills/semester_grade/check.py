"""
學期成績查詢技能
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.semester_grade import SemesterGrade
from app.models.student import Student


class SemesterGradeCheck(BaseSkill):
    name = "semester_grade.check"
    description = "查詢學生的學期總成績（期中、期末、學期加權總分），僅在使用者明確提到「學期總成績」「期中考」「期末考」時使用。一般的大測、小考、作業成績請用 daily_grade.check"
    parameters = {
        "type": "object",
        "properties": {
            "class_subject_id": {"type": "integer", "description": "班級科目ID"},
            "semester_id": {"type": "integer", "description": "學期ID"},
            "student_id": {"type": "integer", "description": "學生ID"},
            "status": {"type": "string", "enum": ["draft", "confirmed"], "description": "成績狀態"},
        },
        "required": ["class_subject_id", "semester_id"],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        query = db.query(SemesterGrade).filter(
            SemesterGrade.class_subject_id == params["class_subject_id"],
            SemesterGrade.semester_id == params["semester_id"],
        )

        if params.get("student_id"):
            query = query.filter(SemesterGrade.student_id == params["student_id"])
        if params.get("status"):
            query = query.filter(SemesterGrade.status == params["status"])

        grades = query.all()

        if not grades:
            return SkillResult(success=True, message="查無學期成績記錄")

        rows = []
        for g in grades:
            student = db.query(Student).filter(Student.id == g.student_id).first()
            rows.append([
                student.name if student else g.student_id,
                float(g.daily_avg) if g.daily_avg else "-",
                float(g.midterm_score) if g.midterm_score else "-",
                float(g.final_score) if g.final_score else "-",
                float(g.semester_score) if g.semester_score else "-",
                "及格" if g.is_passing else "不及格" if g.is_passing is not None else "-",
                g.status,
            ])

        return SkillResult(
            success=True,
            message=f"查到 {len(grades)} 筆學期成績",
            data_card={
                "type": "table",
                "title": "學期成績查詢結果",
                "payload": {
                    "columns": ["學生", "平時平均", "期中考", "期末考", "學期總成績", "及格與否", "狀態"],
                    "rows": rows,
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return "查詢學期成績"