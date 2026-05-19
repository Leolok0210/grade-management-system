"""
平時成績登記技能
"""
from datetime import date
from decimal import Decimal
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.daily_grade import DailyGradeItem, DailyGrade
from app.models.student import Student
from app.models.subject import ClassSubject


class DailyGradeRegister(BaseSkill):
    name = "daily_grade.register"
    description = "登記學生的平時成績，包含作業、小考、課堂參與、口試等"
    parameters = {
        "type": "object",
        "properties": {
            "class_subject_id": {"type": "integer", "description": "班級科目ID"},
            "title": {"type": "string", "description": "成績項目標題，例如「第三次作業」"},
            "grade_type": {
                "type": "string",
                "enum": ["作業", "小考", "課堂參與", "口試", "其他"],
                "description": "成績類型",
            },
            "scores": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "student_id": {"type": "integer"},
                        "score": {"type": "number"},
                    },
                },
                "description": "學生ID與分數列表",
            },
            "date": {"type": "string", "description": "日期，格式 YYYY-MM-DD，預設今天"},
            "max_score": {"type": "number", "description": "滿分，預設100"},
        },
        "required": ["class_subject_id", "title", "grade_type", "scores"],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        class_subject_id = params["class_subject_id"]
        title = params["title"]
        grade_type = params["grade_type"]
        scores = params["scores"]
        grade_date = date.fromisoformat(params["date"]) if params.get("date") else date.today()
        max_score = Decimal(str(params.get("max_score", 100)))

        # 建立 grade item
        item = DailyGradeItem(
            class_subject_id=class_subject_id,
            title=title,
            grade_type=grade_type,
            date=grade_date,
            max_score=max_score,
            created_by=context.user_id,
        )
        db.add(item)
        db.flush()

        # 批次建立成績
        created = []
        for s in scores:
            grade = DailyGrade(
                daily_grade_item_id=item.id,
                student_id=s["student_id"],
                score=Decimal(str(s["score"])),
                created_by=context.user_id,
            )
            db.add(grade)
            created.append(s)

        db.commit()

        return SkillResult(
            success=True,
            message=f"已成功登記 {len(created)} 筆「{title}」{grade_type}成績",
            data={"item_id": item.id, "count": len(created)},
            data_card={
                "type": "table",
                "title": f"{title} - 登記結果",
                "payload": {
                    "columns": ["學生ID", "分數"],
                    "rows": [[s["student_id"], s["score"]] for s in created],
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return f"將登記「{params.get('title', '')}」{params.get('grade_type', '')}成績，共 {len(params.get('scores', []))} 筆"