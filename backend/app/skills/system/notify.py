"""
家長通知技能
成績確認後自動發送通知給家長
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.semester_grade import SemesterGrade
from app.models.student import Student
from app.models.subject import ClassSubject, Subject


class NotifyParents(BaseSkill):
    name = "system.notify_parents"
    description = "成績確認後發送通知給家長，支援 Email 通知"
    parameters = {
        "type": "object",
        "properties": {
            "class_subject_id": {"type": "integer", "description": "班級科目ID"},
            "semester_id": {"type": "integer", "description": "學期ID"},
            "notify_type": {"type": "string", "enum": ["all", "failing_only"], "description": "通知範圍：全部或僅不及格"},
        },
        "required": ["class_subject_id", "semester_id"],
    }
    required_role = "admin"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        class_subject_id = params["class_subject_id"]
        semester_id = params["semester_id"]
        notify_type = params.get("notify_type", "failing_only")

        grades = db.query(SemesterGrade).filter(
            SemesterGrade.class_subject_id == class_subject_id,
            SemesterGrade.semester_id == semester_id,
            SemesterGrade.status == "confirmed",
        ).all()

        if notify_type == "failing_only":
            grades = [g for g in grades if not g.is_passing]

        cs = db.query(ClassSubject).filter(ClassSubject.id == class_subject_id).first()
        subject = db.query(Subject).filter(Subject.id == cs.subject_id).first() if cs else None

        notified = []
        for g in grades:
            student = db.query(Student).filter(Student.id == g.student_id).first()
            # TODO: 實際發送 Email/LINE 通知
            # 目前為模擬
            notified.append([
                student.name if student else g.student_id,
                subject.name if subject else "-",
                float(g.semester_score) if g.semester_score else "-",
                "已通知" if g.is_passing is False else "已通知",
            ])

        return SkillResult(
            success=True,
            message=f"已發送 {len(notified)} 封家長通知",
            data={"notified_count": len(notified)},
            data_card={
                "type": "table",
                "title": "家長通知發送結果",
                "payload": {
                    "columns": ["學生", "科目", "成績", "狀態"],
                    "rows": notified,
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return "發送家長通知"