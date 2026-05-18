"""
名列前茅名單技能
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.semester_grade import SemesterGrade
from app.models.student import Student
from app.models.subject import ClassSubject, Subject
from app.models.student import Class


class HonorRollList(BaseSkill):
    name = "grade_check.honor_roll"
    description = "列出各班名列前茅的學生名單，可依班級、科目、學期查詢"
    parameters = {
        "type": "object",
        "properties": {
            "class_id": {"type": "string", "description": "班級ID（可選，不填則全部班級）"},
            "semester_id": {"type": "string", "description": "學期ID"},
            "subject_id": {"type": "string", "description": "科目ID（可選，不填則按總平均排名）"},
            "top_n": {"type": "integer", "description": "取前N名，預設5"},
        },
        "required": ["semester_id"],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        semester_id = params["semester_id"]
        top_n = params.get("top_n", 5)
        class_id = params.get("class_id")
        subject_id = params.get("subject_id")

        # 取得班級列表
        if class_id:
            classes = db.query(Class).filter(Class.id == class_id).all()
        else:
            classes = db.query(Class).filter(Class.school_id == context.school_id).all()

        all_rows = []
        for cls in classes:
            students = db.query(Student).filter(Student.class_id == cls.id).all()
            student_scores = []

            for student in students:
                if subject_id:
                    # 單科排名
                    cs = db.query(ClassSubject).filter(
                        ClassSubject.class_id == cls.id,
                        ClassSubject.subject_id == subject_id,
                        ClassSubject.semester_id == semester_id,
                    ).first()
                    if not cs:
                        continue
                    grade = db.query(SemesterGrade).filter(
                        SemesterGrade.student_id == student.id,
                        SemesterGrade.class_subject_id == cs.id,
                        SemesterGrade.semester_id == semester_id,
                    ).first()
                    score = float(grade.semester_score) if grade and grade.semester_score else None
                else:
                    # 總平均排名
                    grades = db.query(SemesterGrade).filter(
                        SemesterGrade.student_id == student.id,
                        SemesterGrade.semester_id == semester_id,
                        SemesterGrade.semester_score.isnot(None),
                    ).all()
                    scores = [float(g.semester_score) for g in grades]
                    score = round(sum(scores) / len(scores), 2) if scores else None

                if score is not None:
                    student_scores.append((student.name, score))

            # 排序取前N
            student_scores.sort(key=lambda x: x[1], reverse=True)
            for rank, (name, score) in enumerate(student_scores[:top_n], 1):
                all_rows.append([cls.name, rank, name, score])

        if not all_rows:
            return SkillResult(success=True, message="查無成績資料")

        return SkillResult(
            success=True,
            message=f"名列前茅名單（前 {top_n} 名）",
            data_card={
                "type": "table",
                "title": "名列前茅名單",
                "payload": {
                    "columns": ["班級", "名次", "姓名", "分數"],
                    "rows": all_rows,
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return f"列出前 {params.get('top_n', 5)} 名"