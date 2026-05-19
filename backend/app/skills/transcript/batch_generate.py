"""
批次產生成績單技能
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.student import Student, Class
from app.models.semester_grade import SemesterGrade
from app.models.subject import ClassSubject, Subject


class TranscriptBatchGenerate(BaseSkill):
    name = "transcript.batch_generate"
    description = "批次產生全班學生的成績單"
    parameters = {
        "type": "object",
        "properties": {
            "class_id": {"type": "integer", "description": "班級ID"},
            "semester_id": {"type": "integer", "description": "學期ID"},
        },
        "required": ["class_id", "semester_id"],
    }
    required_role = "dept_head"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        students = db.query(Student).filter(Student.class_id == params["class_id"]).all()
        class_ = db.query(Class).filter(Class.id == params["class_id"]).first()

        results = []
        for student in students:
            grades = db.query(SemesterGrade).filter(
                SemesterGrade.student_id == student.id,
                SemesterGrade.semester_id == params["semester_id"],
            ).all()

            total = 0
            count = 0
            for g in grades:
                if g.semester_score:
                    total += float(g.semester_score)
                    count += 1

            avg = round(total / count, 2) if count > 0 else 0
            results.append([student.name, student.student_no, avg, count])

        return SkillResult(
            success=True,
            message=f"已產生 {class_.name if class_ else ''} 共 {len(results)} 位學生的成績單",
            data_card={
                "type": "table",
                "title": f"{class_.name if class_ else ''} 成績單總覽",
                "payload": {
                    "columns": ["姓名", "學號", "總平均", "科目數"],
                    "rows": results,
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return "批次產生成績單"