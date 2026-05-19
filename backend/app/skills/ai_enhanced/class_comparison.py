"""
班級科目比較技能
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.daily_grade import DailyGradeItem, DailyGrade
from app.models.student import Student, Class
from app.models.subject import ClassSubject, Subject


class ClassComparison(BaseSkill):
    name = "ai.class_comparison"
    description = "比較不同班級的科目成績，包含平均分、最高分、最低分、及格率。當使用者提到班級比較、哪班比較好、對比時使用"
    parameters = {
        "type": "object",
        "properties": {
            "class_subject_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "要比較的班級科目ID列表（至少2個）",
            },
            "grade_type": {"type": "string", "description": "成績類型篩選（可選）"},
        },
        "required": ["class_subject_ids"],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        cs_ids = params["class_subject_ids"]
        if len(cs_ids) < 2:
            return SkillResult(success=False, message="至少需要2個班級科目進行比較")

        results = []
        for cs_id in cs_ids:
            cs = db.query(ClassSubject).filter(ClassSubject.id == cs_id).first()
            if not cs:
                continue

            cls = db.query(Class).filter(Class.id == cs.class_id).first()
            subj = db.query(Subject).filter(Subject.id == cs.subject_id).first()
            label = f"{cls.name if cls else '?'} {subj.name if subj else '?'}"

            query = db.query(DailyGrade).join(DailyGradeItem).filter(
                DailyGradeItem.class_subject_id == cs_id
            )
            if params.get("grade_type"):
                query = query.filter(DailyGradeItem.grade_type == params["grade_type"])

            grades = query.all()
            if not grades:
                results.append({"label": label, "avg": "-", "max": "-", "min": "-", "pass_rate": "-", "count": 0})
                continue

            scores = [float(g.score) for g in grades]
            avg = round(sum(scores) / len(scores), 1)
            max_s = max(scores)
            min_s = min(scores)
            pass_rate = round(sum(1 for s in scores if s >= 60) / len(scores) * 100, 1)

            results.append({
                "label": label,
                "avg": avg,
                "max": max_s,
                "min": min_s,
                "pass_rate": f"{pass_rate}%",
                "count": len(scores),
            })

        columns = ["班級科目", "平均分", "最高分", "最低分", "及格率", "筆數"]
        rows = [[r["label"], r["avg"], r["max"], r["min"], r["pass_rate"], r["count"]] for r in results]

        valid = [r for r in results if r["avg"] != "-"]
        best = max(valid, key=lambda x: x["avg"]) if valid else None
        msg = "、".join(r["label"] for r in results) + " 的成績比較"
        if best:
            msg += f"，{best['label']} 平均最高（{best['avg']}分）"

        return SkillResult(
            success=True,
            message=msg,
            data={"comparison": results},
            data_card={
                "type": "table",
                "title": "班級科目成績比較",
                "payload": {
                    "columns": columns,
                    "rows": rows,
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return "比較班級科目成績"
