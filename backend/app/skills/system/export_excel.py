"""
匯出 Excel 報表技能
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.semester_grade import SemesterGrade
from app.models.daily_grade import DailyGrade, DailyGradeItem
from app.models.student import Student
from app.models.subject import ClassSubject, Subject


class ExportExcel(BaseSkill):
    name = "system.export_excel"
    description = "匯出成績資料為 Excel 報表，支援平時成績和學期成績匯出"
    parameters = {
        "type": "object",
        "properties": {
            "export_type": {"type": "string", "enum": ["daily", "semester"], "description": "匯出類型"},
            "class_subject_id": {"type": "string", "description": "班級科目ID"},
            "semester_id": {"type": "string", "description": "學期ID"},
            "output_path": {"type": "string", "description": "輸出檔案路徑"},
        },
        "required": ["export_type", "class_subject_id", "semester_id", "output_path"],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        from openpyxl import Workbook

        export_type = params["export_type"]
        class_subject_id = params["class_subject_id"]
        output_path = params["output_path"]

        cs = db.query(ClassSubject).filter(ClassSubject.id == class_subject_id).first()
        subject = db.query(Subject).filter(Subject.id == cs.subject_id).first() if cs else None
        students = db.query(Student).filter(Student.class_id == cs.class_id).all() if cs else []

        wb = Workbook()
        ws = wb.active
        ws.title = f"{subject.name if subject else '成績'}報表"

        if export_type == "daily":
            ws.append(["學號", "姓名", "項目", "類型", "分數", "日期"])

            items = db.query(DailyGradeItem).filter(
                DailyGradeItem.class_subject_id == class_subject_id,
            ).all()

            for item in items:
                for g in item.grades:
                    student = next((s for s in students if s.id == g.student_id), None)
                    ws.append([
                        student.student_no if student else "",
                        student.name if student else "",
                        item.title,
                        item.grade_type,
                        float(g.score),
                        item.date.isoformat(),
                    ])

        elif export_type == "semester":
            ws.append(["學號", "姓名", "平時平均", "期中考", "期末考", "學期總成績", "及格與否"])

            grades = db.query(SemesterGrade).filter(
                SemesterGrade.class_subject_id == class_subject_id,
                SemesterGrade.semester_id == params["semester_id"],
            ).all()

            for g in grades:
                student = next((s for s in students if s.id == g.student_id), None)
                ws.append([
                    student.student_no if student else "",
                    student.name if student else "",
                    float(g.daily_avg) if g.daily_avg else "",
                    float(g.midterm_score) if g.midterm_score else "",
                    float(g.final_score) if g.final_score else "",
                    float(g.semester_score) if g.semester_score else "",
                    "及格" if g.is_passing else "不及格" if g.is_passing is not None else "",
                ])

        wb.save(output_path)

        return SkillResult(
            success=True,
            message=f"已匯出報表至 {output_path}",
            data={"file_path": output_path},
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return f"匯出 {params.get('export_type', '')} 成績報表"