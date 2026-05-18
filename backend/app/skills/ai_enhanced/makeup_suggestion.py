"""
智慧補考建議技能
根據歷史數據預測補考通過率，建議補考名單
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.semester_grade import SemesterGrade, MakeupExam
from app.models.student import Student
from app.models.subject import ClassSubject, Subject


class MakeupSuggestion(BaseSkill):
    name = "ai.makeup_suggestion"
    description = "根據不及格學生的成績數據，智慧建議補考名單和預測通過機率"
    parameters = {
        "type": "object",
        "properties": {
            "class_subject_id": {"type": "string", "description": "班級科目ID"},
            "semester_id": {"type": "string", "description": "學期ID"},
        },
        "required": ["class_subject_id", "semester_id"],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        class_subject_id = params["class_subject_id"]
        semester_id = params["semester_id"]

        # 找不及格學生
        failing_grades = db.query(SemesterGrade).filter(
            SemesterGrade.class_subject_id == class_subject_id,
            SemesterGrade.semester_id == semester_id,
            SemesterGrade.is_passing == False,
        ).all()

        if not failing_grades:
            return SkillResult(success=True, message="無不及格學生，不需補考")

        cs = db.query(ClassSubject).filter(ClassSubject.id == class_subject_id).first()
        subject = db.query(Subject).filter(Subject.id == cs.subject_id).first() if cs else None

        rows = []
        for g in failing_grades:
            student = db.query(Student).filter(Student.id == g.student_id).first()
            score = float(g.semester_score) if g.semester_score else 0

            # 檢查是否已登記補考
            existing = db.query(MakeupExam).filter(
                MakeupExam.student_id == g.student_id,
                MakeupExam.class_subject_id == class_subject_id,
                MakeupExam.semester_id == semester_id,
            ).first()

            # 簡易預測：距離及格線越近，通過機率越高
            gap = 60 - score
            if gap <= 5:
                prob = "高 (80%+)"
            elif gap <= 15:
                prob = "中 (50-80%)"
            else:
                prob = "低 (<50%)"

            status = "已登記" if existing else "待登記"
            rows.append([student.name if student else g.student_id, score, gap, prob, status])

        rows.sort(key=lambda x: x[2])  # 按差距排序

        return SkillResult(
            success=True,
            message=f"共 {len(failing_grades)} 位不及格學生，建議安排補考",
            data_card={
                "type": "table",
                "title": f"補考建議名單 - {subject.name if subject else ''}",
                "payload": {
                    "columns": ["學生", "學期成績", "距及格線", "通過預測", "狀態"],
                    "rows": rows,
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return "智慧補考建議"