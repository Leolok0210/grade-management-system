"""
成績草榜產生技能
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.draft import DraftGradeList
from app.models.semester_grade import SemesterGrade
from app.models.student import Student


class GradeDraftGenerate(BaseSkill):
    name = "semester_grade.draft_list"
    description = "產生成績草榜，列出班級科目所有學生的學期成績，供教務處審核"
    parameters = {
        "type": "object",
        "properties": {
            "class_id": {"type": "integer", "description": "班級ID"},
            "subject_id": {"type": "integer", "description": "科目ID"},
            "semester_id": {"type": "integer", "description": "學期ID"},
        },
        "required": ["class_id", "subject_id", "semester_id"],
    }
    required_role = "dept_head"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        from app.models.subject import ClassSubject

        # 找到 class_subject
        cs = db.query(ClassSubject).filter(
            ClassSubject.class_id == params["class_id"],
            ClassSubject.subject_id == params["subject_id"],
            ClassSubject.semester_id == params["semester_id"],
        ).first()

        if not cs:
            return SkillResult(success=False, message="找不到對應的班級科目設定")

        # 取得所有學期成績
        grades = db.query(SemesterGrade).filter(
            SemesterGrade.class_subject_id == cs.id,
            SemesterGrade.semester_id == params["semester_id"],
        ).all()

        # 取得學生列表
        students = db.query(Student).filter(Student.class_id == params["class_id"]).all()

        # 組合草榜資料
        draft_data = []
        rows = []
        for student in students:
            grade = next((g for g in grades if g.student_id == student.id), None)
            entry = {
                "student_id": student.id,
                "student_no": student.student_no,
                "name": student.name,
                "daily_avg": float(grade.daily_avg) if grade and grade.daily_avg else None,
                "midterm_score": float(grade.midterm_score) if grade and grade.midterm_score else None,
                "final_score": float(grade.final_score) if grade and grade.final_score else None,
                "semester_score": float(grade.semester_score) if grade and grade.semester_score else None,
                "is_passing": grade.is_passing if grade else None,
            }
            draft_data.append(entry)
            rows.append([
                student.name, student.student_no,
                entry["daily_avg"] or "-",
                entry["midterm_score"] or "-",
                entry["final_score"] or "-",
                entry["semester_score"] or "-",
                "及格" if entry["is_passing"] else "不及格" if entry["is_passing"] is not None else "-",
            ])

        # 儲存草榜
        draft = DraftGradeList(
            class_id=params["class_id"],
            subject_id=params["subject_id"],
            semester_id=params["semester_id"],
            status="draft",
            data=draft_data,
            created_by=context.user_id,
        )
        db.add(draft)
        db.commit()

        return SkillResult(
            success=True,
            message=f"已產生成績草榜，共 {len(draft_data)} 位學生",
            data={"draft_id": draft.id, "count": len(draft_data)},
            data_card={
                "type": "table",
                "title": "成績草榜",
                "payload": {
                    "columns": ["姓名", "學號", "平時平均", "期中考", "期末考", "學期總成績", "及格與否"],
                    "rows": rows,
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return "產生成績草榜"