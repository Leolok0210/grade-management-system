"""
補考登記技能
"""
from datetime import date
from decimal import Decimal
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.semester_grade import MakeupExam, SemesterGrade
from app.models.student import Student


class MakeupExamRegister(BaseSkill):
    name = "semester_grade.makeup_register"
    description = "為不及格學生登記補考，可指定補考日期和分數"
    parameters = {
        "type": "object",
        "properties": {
            "registrations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "student_id": {"type": "integer"},
                        "class_subject_id": {"type": "string"},
                        "semester_id": {"type": "string"},
                        "original_score": {"type": "number"},
                        "makeup_date": {"type": "string", "description": "補考日期 YYYY-MM-DD"},
                    },
                },
            },
        },
        "required": ["registrations"],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        registrations = params["registrations"]
        created = []

        for r in registrations:
            makeup = MakeupExam(
                student_id=r["student_id"],
                class_subject_id=r["class_subject_id"],
                semester_id=r["semester_id"],
                original_score=Decimal(str(r.get("original_score", 0))),
                makeup_date=date.fromisoformat(r["makeup_date"]) if r.get("makeup_date") else None,
                registered_by=context.user_id,
            )
            db.add(makeup)
            created.append(r)

        db.commit()

        rows = []
        for r in created:
            student = db.query(Student).filter(Student.id == r["student_id"]).first()
            rows.append([student.name if student else r["student_id"], r.get("original_score", "-"), r.get("makeup_date", "待定")])

        return SkillResult(
            success=True,
            message=f"已登記 {len(created)} 位學生補考",
            data_card={
                "type": "table",
                "title": "補考登記結果",
                "payload": {
                    "columns": ["學生", "原始分數", "補考日期"],
                    "rows": rows,
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return f"將登記 {len(params.get('registrations', []))} 位學生補考"