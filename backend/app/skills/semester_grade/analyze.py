"""
學期成績統計分析技能
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.semester_grade import SemesterGrade
from app.models.student import Student


class SemesterGradeAnalyze(BaseSkill):
    name = "semester_grade.analyze"
    description = "學期成績統計分析，包含平均、分佈、及格率、標準差"
    parameters = {
        "type": "object",
        "properties": {
            "class_subject_id": {"type": "integer", "description": "班級科目ID"},
            "semester_id": {"type": "integer", "description": "學期ID"},
        },
        "required": ["class_subject_id", "semester_id"],
    }
    required_role = "dept_head"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        grades = db.query(SemesterGrade).filter(
            SemesterGrade.class_subject_id == params["class_subject_id"],
            SemesterGrade.semester_id == params["semester_id"],
            SemesterGrade.semester_score.isnot(None),
        ).all()

        if not grades:
            return SkillResult(success=True, message="查無已評分的學期成績")

        scores = [float(g.semester_score) for g in grades]
        avg = round(sum(scores) / len(scores), 2)
        max_s = max(scores)
        min_s = min(scores)
        passing_count = len([s for s in scores if s >= 60])
        passing_rate = round(passing_count / len(scores) * 100, 1)

        variance = sum((s - avg) ** 2 for s in scores) / len(scores)
        std_dev = round(variance ** 0.5, 2)

        # 分佈
        ranges = [(0, 59), (60, 69), (70, 79), (80, 89), (90, 100)]
        dist = {}
        for low, high in ranges:
            dist[f"{low}-{high}"] = len([s for s in scores if low <= s <= high])

        return SkillResult(
            success=True,
            message=f"學期成績分析：平均 {avg}，及格率 {passing_rate}%，標準差 {std_dev}",
            data={
                "average": avg, "max": max_s, "min": min_s,
                "passing_rate": passing_rate, "std_dev": std_dev,
                "distribution": dist, "count": len(scores),
            },
            data_card={
                "type": "table",
                "title": "學期成績統計分析",
                "payload": {
                    "columns": ["指標", "數值"],
                    "rows": [
                        ["人數", len(scores)],
                        ["平均分數", avg],
                        ["最高分", max_s],
                        ["最低分", min_s],
                        ["及格率", f"{passing_rate}%"],
                        ["標準差", std_dev],
                        *[[k, v] for k, v in dist.items()],
                    ],
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return "分析學期成績統計"