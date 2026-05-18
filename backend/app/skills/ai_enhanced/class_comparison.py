"""
班級科目比較分析技能
同年級不同班級、不同科目成績分佈比較
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.semester_grade import SemesterGrade
from app.models.student import Class
from app.models.subject import ClassSubject, Subject


class ClassComparison(BaseSkill):
    name = "ai.class_comparison"
    description = "比較同年級不同班級的成績分佈，或不同科目的平均分數差異"
    parameters = {
        "type": "object",
        "properties": {
            "semester_id": {"type": "string", "description": "學期ID"},
            "grade_level": {"type": "integer", "description": "年級（1-6）"},
            "subject_id": {"type": "string", "description": "科目ID（可選）"},
        },
        "required": ["semester_id", "grade_level"],
    }
    required_role = "dept_head"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        semester_id = params["semester_id"]
        grade_level = params["grade_level"]
        subject_id = params.get("subject_id")

        classes = db.query(Class).filter(
            Class.school_id == context.school_id,
            Class.grade_level == grade_level,
        ).all()

        rows = []
        for cls in classes:
            cs_list = db.query(ClassSubject).filter(
                ClassSubject.class_id == cls.id,
                ClassSubject.semester_id == semester_id,
            ).all()

            for cs in cs_list:
                if subject_id and cs.subject_id != subject_id:
                    continue
                subject = db.query(Subject).filter(Subject.id == cs.subject_id).first()
                grades = db.query(SemesterGrade).filter(
                    SemesterGrade.class_subject_id == cs.id,
                    SemesterGrade.semester_id == semester_id,
                    SemesterGrade.semester_score.isnot(None),
                ).all()

                if not grades:
                    continue

                scores = [float(g.semester_score) for g in grades]
                avg = round(sum(scores) / len(scores), 2)
                passing = len([s for s in scores if s >= 60])
                passing_rate = round(passing / len(scores) * 100, 1)

                rows.append([cls.name, subject.name if subject else "-", avg, max(scores), min(scores), f"{passing_rate}%", len(scores)])

        if not rows:
            return SkillResult(success=True, message="查無可比較的成績資料")

        return SkillResult(
            success=True,
            message=f"班級科目比較分析完成",
            data_card={
                "type": "table",
                "title": f"{grade_level}年級班級科目比較",
                "payload": {
                    "columns": ["班級", "科目", "平均", "最高", "最低", "及格率", "人數"],
                    "rows": rows,
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return f"比較 {params.get('grade_level', '')} 年級班級成績"