"""
及格分數線設定技能
"""
from decimal import Decimal
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.passing_line import PassingLine


class PassingLineSet(BaseSkill):
    name = "semester_grade.passing_line"
    description = "設定學期各科目的及格分數線和補考及格分數線"
    parameters = {
        "type": "object",
        "properties": {
            "school_id": {"type": "string", "description": "學校ID"},
            "semester_id": {"type": "string", "description": "學期ID"},
            "subject_id": {"type": "string", "description": "科目ID"},
            "passing_score": {"type": "number", "description": "及格分數，預設60"},
            "makeup_passing_score": {"type": "number", "description": "補考及格分數，預設60"},
        },
        "required": ["school_id", "semester_id", "subject_id"],
    }
    required_role = "admin"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        existing = db.query(PassingLine).filter(
            PassingLine.school_id == params["school_id"],
            PassingLine.semester_id == params["semester_id"],
            PassingLine.subject_id == params["subject_id"],
        ).first()

        passing = Decimal(str(params.get("passing_score", 60)))
        makeup_passing = Decimal(str(params.get("makeup_passing_score", 60)))

        if existing:
            existing.passing_score = passing
            existing.makeup_passing_score = makeup_passing
        else:
            pl = PassingLine(
                school_id=params["school_id"],
                semester_id=params["semester_id"],
                subject_id=params["subject_id"],
                passing_score=passing,
                makeup_passing_score=makeup_passing,
            )
            db.add(pl)

        db.commit()

        return SkillResult(
            success=True,
            message=f"已設定及格分數線：{passing} 分，補考及格：{makeup_passing} 分",
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return f"設定及格分數線為 {params.get('passing_score', 60)} 分"