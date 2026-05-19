"""
學期成績登記技能
"""
from decimal import Decimal
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.semester_grade import SemesterGrade


class SemesterGradeRegister(BaseSkill):
    name = "semester_grade.register"
    description = "登記學生的學期考試成績（期中考、期末考），或直接輸入學期總成績"
    parameters = {
        "type": "object",
        "properties": {
            "scores": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "student_id": {"type": "integer"},
                        "midterm_score": {"type": "number", "description": "期中考分數"},
                        "final_score": {"type": "number", "description": "期末考分數"},
                        "semester_score": {"type": "number", "description": "學期總成績（直接輸入）"},
                    },
                },
                "description": "學生成績列表",
            },
            "class_subject_id": {"type": "integer", "description": "班級科目ID"},
            "semester_id": {"type": "integer", "description": "學期ID"},
        },
        "required": ["class_subject_id", "semester_id", "scores"],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        class_subject_id = params["class_subject_id"]
        semester_id = params["semester_id"]
        scores = params["scores"]

        created = []
        for s in scores:
            # 檢查是否已有記錄
            existing = db.query(SemesterGrade).filter(
                SemesterGrade.student_id == s["student_id"],
                SemesterGrade.class_subject_id == class_subject_id,
                SemesterGrade.semester_id == semester_id,
            ).first()

            if existing:
                # 更新
                if "midterm_score" in s:
                    existing.midterm_score = Decimal(str(s["midterm_score"]))
                if "final_score" in s:
                    existing.final_score = Decimal(str(s["final_score"]))
                if "semester_score" in s:
                    existing.semester_score = Decimal(str(s["semester_score"]))
                created.append(s)
            else:
                grade = SemesterGrade(
                    student_id=s["student_id"],
                    class_subject_id=class_subject_id,
                    semester_id=semester_id,
                    midterm_score=Decimal(str(s.get("midterm_score", 0))) if "midterm_score" in s else None,
                    final_score=Decimal(str(s.get("final_score", 0))) if "final_score" in s else None,
                    semester_score=Decimal(str(s.get("semester_score", 0))) if "semester_score" in s else None,
                    status="draft",
                )
                db.add(grade)
                created.append(s)

        db.commit()

        return SkillResult(
            success=True,
            message=f"已登記 {len(created)} 筆學期成績",
            data={"count": len(created)},
            data_card={
                "type": "table",
                "title": "學期成績登記結果",
                "payload": {
                    "columns": ["學生ID", "期中考", "期末考", "學期總成績"],
                    "rows": [
                        [s["student_id"], s.get("midterm_score", "-"), s.get("final_score", "-"), s.get("semester_score", "-")]
                        for s in created
                    ],
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return f"將登記 {len(params.get('scores', []))} 筆學期成績"