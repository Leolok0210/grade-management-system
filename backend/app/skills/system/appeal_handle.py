"""
成績申訴處理技能
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.appeal import GradeAppeal
from app.models.student import Student


class AppealHandle(BaseSkill):
    name = "system.appeal_handle"
    description = "處理成績申訴，審核或駁回學生的成績異議"
    parameters = {
        "type": "object",
        "properties": {
            "appeal_id": {"type": "string", "description": "申訴ID"},
            "action": {"type": "string", "enum": ["approve", "reject"], "description": "審核動作"},
            "review_comment": {"type": "string", "description": "審核意見"},
        },
        "required": ["appeal_id", "action"],
    }
    required_role = "dept_head"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        appeal = db.query(GradeAppeal).filter(GradeAppeal.id == params["appeal_id"]).first()
        if not appeal:
            return SkillResult(success=False, message="找不到該申訴記錄")

        action = params["action"]
        if action == "approve":
            appeal.status = "approved"
            msg = "申訴已核准"
        else:
            appeal.status = "rejected"
            msg = "申訴已駁回"

        appeal.reviewed_by = context.user_id
        appeal.review_comment = params.get("review_comment", "")
        db.commit()

        student = db.query(Student).filter(Student.id == appeal.student_id).first()

        return SkillResult(
            success=True,
            message=f"{student.name if student else ''} 的成績申訴{msg}",
        )

    def preview(self, params: dict, context: UserContext) -> str:
        action = "核准" if params.get("action") == "approve" else "駁回"
        return f"{action}成績申訴"