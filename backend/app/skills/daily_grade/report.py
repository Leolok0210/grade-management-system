"""
平時成績報表技能
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.daily_grade import DailyGradeItem, DailyGrade
from app.models.student import Student


class DailyGradeReport(BaseSkill):
    name = "daily_grade.report"
    description = "產生平時成績報表，包含各學生各項成績明細及加權平均"
    parameters = {
        "type": "object",
        "properties": {
            "class_subject_id": {"type": "string", "description": "班級科目ID"},
            "grade_type": {"type": "string", "description": "成績類型篩選（可選）"},
        },
        "required": ["class_subject_id"],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        class_subject_id = params["class_subject_id"]

        query = db.query(DailyGradeItem).filter(
            DailyGradeItem.class_subject_id == class_subject_id
        )

        if params.get("grade_type"):
            query = query.filter(DailyGradeItem.grade_type == params["grade_type"])

        items = query.order_by(DailyGradeItem.date).all()

        if not items:
            return SkillResult(success=True, message="查無成績項目，無法產生報表")

        # 收集所有學生的成績
        student_grades = {}
        for item in items:
            for g in item.grades:
                student = db.query(Student).filter(Student.id == g.student_id).first()
                name = student.name if student else g.student_id
                student_grades.setdefault(g.student_id, {"name": name, "scores": []})
                student_grades[g.student_id]["scores"].append({
                    "title": item.title,
                    "type": item.grade_type,
                    "score": float(g.score),
                    "max": float(item.max_score),
                    "weight": float(item.weight),
                    "date": item.date.isoformat(),
                })

        # 計算加權平均
        rows = []
        for sid, data in student_grades.items():
            total_weighted = sum(s["score"] * s["weight"] for s in data["scores"])
            total_weight = sum(s["weight"] for s in data["scores"])
            avg = round(total_weighted / total_weight, 2) if total_weight > 0 else 0
            rows.append([data["name"], len(data["scores"]), avg])
            rows.sort(key=lambda x: x[2], reverse=True)

        return SkillResult(
            success=True,
            message=f"已產生平時成績報表，共 {len(rows)} 位學生",
            data={"student_count": len(rows), "item_count": len(items)},
            data_card={
                "type": "table",
                "title": "平時成績報表",
                "payload": {
                    "columns": ["學生", "成績筆數", "加權平均"],
                    "rows": rows,
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return f"產生平時成績報表"