"""
平時成績查詢技能
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.daily_grade import DailyGradeItem, DailyGrade
from app.models.student import Student
from sqlalchemy.orm import Session


class DailyGradeCheck(BaseSkill):
    name = "daily_grade.check"
    description = "查詢學生的平時成績，可依班級、科目、學生、成績類型篩選"
    parameters = {
        "type": "object",
        "properties": {
            "class_subject_id": {"type": "string", "description": "班級科目ID"},
            "student_id": {"type": "string", "description": "學生ID（查單一學生）"},
            "grade_type": {"type": "string", "description": "成績類型篩選：作業/小考/課堂參與/口試"},
            "date_from": {"type": "string", "description": "起始日期 YYYY-MM-DD"},
            "date_to": {"type": "string", "description": "結束日期 YYYY-MM-DD"},
        },
        "required": ["class_subject_id"],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        query = db.query(DailyGrade).join(DailyGradeItem)

        if params.get("class_subject_id"):
            query = query.filter(DailyGradeItem.class_subject_id == params["class_subject_id"])

        if params.get("student_id"):
            query = query.filter(DailyGrade.student_id == params["student_id"])

        if params.get("grade_type"):
            query = query.filter(DailyGradeItem.grade_type == params["grade_type"])

        if params.get("date_from"):
            from datetime import date
            query = query.filter(DailyGradeItem.date >= date.fromisoformat(params["date_from"]))

        if params.get("date_to"):
            from datetime import date
            query = query.filter(DailyGradeItem.date <= date.fromisoformat(params["date_to"]))

        grades = query.order_by(DailyGradeItem.date.desc()).all()

        if not grades:
            return SkillResult(success=True, message="查無平時成績記錄")

        rows = []
        for g in grades:
            student = db.query(Student).filter(Student.id == g.student_id).first()
            rows.append([student.name if student else g.student_id, g.item.title, g.item.grade_type, float(g.score), g.item.date.isoformat()])

        return SkillResult(
            success=True,
            message=f"查到 {len(grades)} 筆平時成績",
            data={"count": len(grades)},
            data_card={
                "type": "table",
                "title": "平時成績查詢結果",
                "payload": {
                    "columns": ["學生", "項目", "類型", "分數", "日期"],
                    "rows": rows,
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        filters = []
        if params.get("grade_type"):
            filters.append(params["grade_type"])
        if params.get("student_id"):
            filters.append("指定學生")
        desc = "、".join(filters) if filters else "全部"
        return f"查詢平時成績（{desc}）"