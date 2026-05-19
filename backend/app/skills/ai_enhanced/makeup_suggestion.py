"""
智慧補考建議技能
"""
from decimal import Decimal
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.daily_grade import DailyGradeItem, DailyGrade
from app.models.semester_grade import SemesterGrade
from app.models.student import Student, Class
from app.models.subject import ClassSubject, Subject
from app.models.school import Semester


class MakeupSuggestion(BaseSkill):
    name = "ai.makeup_suggestion"
    description = "自動列出需要補考的學生及建議補考科目。當使用者提到補考、不及格、需要重考時使用"
    parameters = {
        "type": "object",
        "properties": {
            "class_id": {"type": "integer", "description": "班級ID"},
            "semester_id": {"type": "integer", "description": "學期ID"},
            "passing_score": {"type": "number", "description": "及格分數線，預設60"},
        },
        "required": ["class_id", "semester_id"],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        class_id = params["class_id"]
        semester_id = params["semester_id"]
        passing_score = Decimal(str(params.get("passing_score", 60)))

        cls = db.query(Class).filter(Class.id == class_id).first()
        if not cls:
            return SkillResult(success=False, message="找不到班級")

        students = db.query(Student).filter(Student.class_id == class_id).order_by(Student.class_number).all()
        if not students:
            return SkillResult(success=False, message="班級內沒有學生")

        class_subjects = db.query(ClassSubject).filter(ClassSubject.class_id == class_id).all()

        makeup_list = []

        for student in students:
            for cs in class_subjects:
                subj = db.query(Subject).filter(Subject.id == cs.subject_id).first()
                subj_name = subj.name if subj else "?"

                sg = db.query(SemesterGrade).filter(
                    SemesterGrade.student_id == student.id,
                    SemesterGrade.class_subject_id == cs.id,
                    SemesterGrade.semester_id == semester_id,
                ).first()

                if sg and sg.semester_score is not None and sg.semester_score < passing_score:
                    makeup_list.append([student.name, subj_name, float(sg.semester_score), "學期成績"])
                    continue

                daily_grades = (
                    db.query(DailyGrade)
                    .join(DailyGradeItem)
                    .filter(
                        DailyGradeItem.class_subject_id == cs.id,
                        DailyGrade.student_id == student.id,
                    )
                    .all()
                )
                if daily_grades:
                    avg = sum(float(g.score) for g in daily_grades) / len(daily_grades)
                    if Decimal(str(round(avg, 1))) < passing_score:
                        already = any(m[0] == student.name and m[1] == subj_name for m in makeup_list)
                        if not already:
                            makeup_list.append([student.name, subj_name, round(avg, 1), "平時成績"])

        if not makeup_list:
            return SkillResult(success=True, message=f"{cls.name} 所有學生均及格，無需補考")

        students_need = len(set(m[0] for m in makeup_list))
        subjects_need = len(set(m[1] for m in makeup_list))

        return SkillResult(
            success=True,
            message=f"{cls.name} 共 {students_need} 名學生需要補考，涉及 {subjects_need} 個科目",
            data={"students_need": students_need, "subjects_need": subjects_need, "total": len(makeup_list)},
            data_card={
                "type": "table",
                "title": f"{cls.name} 補考建議名單",
                "payload": {
                    "columns": ["學生", "科目", "分數", "成績類型"],
                    "rows": sorted(makeup_list, key=lambda x: (x[0], x[1])),
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return "產生補考建議名單"
