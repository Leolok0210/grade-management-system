"""
學期成績檢查技能
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.semester_grade import SemesterGrade
from app.models.student import Student
from app.models.subject import ClassSubject, Subject
from app.models.student import Class


class SemesterReview(BaseSkill):
    name = "grade_check.semester_review"
    description = "學期成績總檢，查看各班各科及格率、不及格人數等統計"
    parameters = {
        "type": "object",
        "properties": {
            "semester_id": {"type": "integer", "description": "學期ID"},
            "class_id": {"type": "integer", "description": "班級ID（可選）"},
        },
        "required": ["semester_id"],
    }
    required_role = "dept_head"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        semester_id = params["semester_id"]

        classes = db.query(Class).filter(Class.school_id == context.school_id)
        if params.get("class_id"):
            classes = classes.filter(Class.id == params["class_id"])
        classes = classes.all()

        rows = []
        for cls in classes:
            class_subjects = db.query(ClassSubject).filter(
                ClassSubject.class_id == cls.id,
                ClassSubject.semester_id == semester_id,
            ).all()

            for cs in class_subjects:
                subject = db.query(Subject).filter(Subject.id == cs.subject_id).first()
                grades = db.query(SemesterGrade).filter(
                    SemesterGrade.class_subject_id == cs.id,
                    SemesterGrade.semester_id == semester_id,
                    SemesterGrade.semester_score.isnot(None),
                ).all()

                if not grades:
                    continue

                total = len(grades)
                passing = len([g for g in grades if g.is_passing])
                failing = total - passing
                avg = round(sum(float(g.semester_score) for g in grades) / total, 2)
                passing_rate = round(passing / total * 100, 1)

                rows.append([cls.name, subject.name if subject else "-", total, passing, failing, f"{passing_rate}%", avg])

        if not rows:
            return SkillResult(success=True, message="查無學期成績資料")

        return SkillResult(
            success=True,
            message=f"學期成績總檢完成，共 {len(rows)} 個班級科目",
            data_card={
                "type": "table",
                "title": "學期成績總檢",
                "payload": {
                    "columns": ["班級", "科目", "人數", "及格", "不及格", "及格率", "平均"],
                    "rows": rows,
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return "學期成績總檢"