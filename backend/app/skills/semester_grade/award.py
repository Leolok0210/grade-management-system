"""
學年獎項授予技能
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.award import AwardType, StudentAward
from app.models.student import Student


class AwardGrant(BaseSkill):
    name = "semester_grade.award_grant"
    description = "授予學生學年獎項，如學業優良獎、進步獎等"
    parameters = {
        "type": "object",
        "properties": {
            "awards": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "student_id": {"type": "integer"},
                        "award_type_id": {"type": "integer", "description": "獎項類型ID"},
                        "semester_id": {"type": "string"},
                        "comment": {"type": "string", "description": "備註"},
                    },
                },
            },
        },
        "required": ["awards"],
    }
    required_role = "admin"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        awards = params["awards"]
        created = []

        for a in awards:
            # 檢查是否已授予
            existing = db.query(StudentAward).filter(
                StudentAward.student_id == a["student_id"],
                StudentAward.award_type_id == a["award_type_id"],
                StudentAward.semester_id == a["semester_id"],
            ).first()

            if existing:
                continue

            sa = StudentAward(
                student_id=a["student_id"],
                award_type_id=a["award_type_id"],
                semester_id=a["semester_id"],
                granted_by=context.user_id,
                comment=a.get("comment"),
            )
            db.add(sa)
            created.append(a)

        db.commit()

        rows = []
        for a in created:
            student = db.query(Student).filter(Student.id == a["student_id"]).first()
            award_type = db.query(AwardType).filter(AwardType.id == a["award_type_id"]).first()
            rows.append([
                student.name if student else a["student_id"],
                award_type.name if award_type else a["award_type_id"],
                a.get("comment", ""),
            ])

        return SkillResult(
            success=True,
            message=f"已授予 {len(created)} 個獎項",
            data_card={
                "type": "table",
                "title": "獎項授予結果",
                "payload": {
                    "columns": ["學生", "獎項", "備註"],
                    "rows": rows,
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return f"將授予 {len(params.get('awards', []))} 個獎項"