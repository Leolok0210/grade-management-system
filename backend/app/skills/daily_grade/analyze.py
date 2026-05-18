"""
平時成績分析技能
"""
from decimal import Decimal
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.daily_grade import DailyGradeItem, DailyGrade
from app.models.student import Student
from sqlalchemy import func


class DailyGradeAnalyze(BaseSkill):
    name = "daily_grade.analyze"
    description = "分析平時成績趨勢，包含平均分數、分數分佈、最高最低分、標準差等統計"
    parameters = {
        "type": "object",
        "properties": {
            "class_subject_id": {"type": "string", "description": "班級科目ID"},
            "grade_type": {"type": "string", "description": "成績類型篩選"},
        },
        "required": ["class_subject_id"],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        class_subject_id = params["class_subject_id"]

        query = db.query(DailyGrade).join(DailyGradeItem).filter(
            DailyGradeItem.class_subject_id == class_subject_id
        )

        if params.get("grade_type"):
            query = query.filter(DailyGradeItem.grade_type == params["grade_type"])

        grades = query.all()

        if not grades:
            return SkillResult(success=True, message="查無成績資料可供分析")

        scores = [float(g.score) for g in grades]
        avg = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)

        # 分數分佈
        ranges = [(0, 59), (60, 69), (70, 79), (80, 89), (90, 100)]
        distribution = {}
        for low, high in ranges:
            count = len([s for s in scores if low <= s <= high])
            distribution[f"{low}-{high}"] = count

        # 各學生平均
        student_avgs = {}
        for g in grades:
            sid = g.student_id
            student_avgs.setdefault(sid, []).append(float(g.score))

        avg_rows = []
        for sid, s_scores in student_avgs.items():
            student = db.query(Student).filter(Student.id == sid).first()
            avg_rows.append([student.name if student else sid, round(sum(s_scores) / len(s_scores), 2), len(s_scores)])

        avg_rows.sort(key=lambda x: x[1], reverse=True)

        # 標準差
        variance = sum((s - avg) ** 2 for s in scores) / len(scores)
        std_dev = round(variance ** 0.5, 2)

        grade_type_desc = params.get("grade_type", "全部")
        return SkillResult(
            success=True,
            message=f"平時成績分析結果（{grade_type_desc}）：平均 {round(avg, 2)} 分，最高 {max_score}，最低 {min_score}，標準差 {std_dev}",
            data={
                "average": round(avg, 2),
                "max": max_score,
                "min": min_score,
                "std_dev": std_dev,
                "distribution": distribution,
                "count": len(scores),
            },
            data_card={
                "type": "table",
                "title": "平時成績分析 - 各學生平均",
                "payload": {
                    "columns": ["學生", "平均分數", "成績筆數"],
                    "rows": avg_rows[:20],  # 最多顯示20人
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return f"分析平時成績（{params.get('grade_type', '全部類型')}）"