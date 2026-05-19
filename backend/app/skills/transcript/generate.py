"""
產生學生成績單技能
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.semester_grade import SemesterGrade
from app.models.student import Student
from app.models.subject import ClassSubject, Subject


class TranscriptGenerate(BaseSkill):
    name = "transcript.generate"
    description = "產生單一學生的成績單，包含所有科目學期成績"
    parameters = {
        "type": "object",
        "properties": {
            "student_id": {"type": "integer", "description": "學生ID"},
            "semester_id": {"type": "integer", "description": "學期ID"},
        },
        "required": ["student_id", "semester_id"],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        student = db.query(Student).filter(Student.id == params["student_id"]).first()
        if not student:
            return SkillResult(success=False, message="找不到該學生")

        grades = db.query(SemesterGrade).filter(
            SemesterGrade.student_id == params["student_id"],
            SemesterGrade.semester_id == params["semester_id"],
        ).all()

        if not grades:
            return SkillResult(success=True, message="該學生尚無學期成績")

        rows = []
        total_score = 0
        count = 0
        for g in grades:
            cs = db.query(ClassSubject).filter(ClassSubject.id == g.class_subject_id).first()
            subject = db.query(Subject).filter(Subject.id == cs.subject_id).first() if cs else None
            score = float(g.semester_score) if g.semester_score else "-"
            if isinstance(score, float):
                total_score += score
                count += 1
            rows.append([
                subject.name if subject else "-",
                float(g.daily_avg) if g.daily_avg else "-",
                float(g.midterm_score) if g.midterm_score else "-",
                float(g.final_score) if g.final_score else "-",
                score,
                "及格" if g.is_passing else "不及格" if g.is_passing is not None else "-",
            ])

        overall_avg = round(total_score / count, 2) if count > 0 else "-"

        return SkillResult(
            success=True,
            message=f"已產生 {student.name} 的成績單，總平均 {overall_avg}",
            data={"student_name": student.name, "overall_avg": overall_avg},
            data_card={
                "type": "transcript",
                "title": f"{student.name} 成績單",
                "payload": {
                    "student_name": student.name,
                    "student_no": student.student_no,
                    "overall_avg": overall_avg,
                    "columns": ["科目", "平時平均", "期中考", "期末考", "學期總成績", "及格與否"],
                    "rows": rows,
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return "產生學生成績單"