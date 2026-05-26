"""
成績單 PDF 產生技能
"""
import os
from decimal import Decimal
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.semester_grade import SemesterGrade
from app.models.daily_grade import DailyGradeItem, DailyGrade
from app.models.student import Student, Class
from app.models.subject import ClassSubject, Subject
from app.models.school import Semester

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "exports")
try:
    os.makedirs(EXPORT_DIR, exist_ok=True)
except OSError:
    pass  # Vercel read-only filesystem


class TranscriptGenerate(BaseSkill):
    name = "transcript.generate"
    description = "產生學生成績單 PDF。當使用者要求成績單、PDF、列印成績時使用"
    parameters = {
        "type": "object",
        "properties": {
            "student_id": {"type": "integer", "description": "學生ID（產生單一學生成績單）"},
            "class_id": {"type": "integer", "description": "班級ID（批次產生全班成績單）"},
            "semester_id": {"type": "integer", "description": "學期ID"},
        },
        "required": ["semester_id"],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        from fpdf import FPDF

        semester_id = params["semester_id"]
        student_id = params.get("student_id")
        class_id = params.get("class_id")

        semester = db.query(Semester).filter(Semester.id == semester_id).first()
        if not semester:
            return SkillResult(success=False, message="找不到學期")

        # 決定要產生成績單的學生
        if student_id:
            students = [db.query(Student).filter(Student.id == student_id).first()]
            if not students[0]:
                return SkillResult(success=False, message="找不到學生")
        elif class_id:
            students = db.query(Student).filter(Student.class_id == class_id).order_by(Student.class_number).all()
            if not students:
                return SkillResult(success=False, message="班級內沒有學生")
        else:
            return SkillResult(success=False, message="請指定 student_id 或 class_id")

        generated = []

        for student in students:
            cls = db.query(Class).filter(Class.id == student.class_id).first()
            class_name = cls.name if cls else "?"

            # 取得學生各科成績
            class_subjects = db.query(ClassSubject).filter(ClassSubject.class_id == student.class_id).all()

            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)

            # 標題
            pdf.set_font("Helvetica", "B", 18)
            pdf.cell(0, 12, "Tam Zhen Union School", ln=True, align="C")
            pdf.set_font("Helvetica", "", 14)
            pdf.cell(0, 8, "Student Transcript", ln=True, align="C")
            pdf.ln(5)

            # 學生資訊
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 7, f"Name: {student.name}", ln=True)
            pdf.cell(0, 7, f"Class: {class_name}", ln=True)
            pdf.cell(0, 7, f"Student No: {student.student_no}", ln=True)
            pdf.ln(5)

            # 成績表
            pdf.set_font("Helvetica", "B", 10)
            col_widths = [50, 30, 30, 30, 30]
            headers = ["Subject", "Midterm", "Final", "Daily Avg", "Semester"]
            for i, h in enumerate(headers):
                pdf.cell(col_widths[i], 8, h, border=1, align="C")
            pdf.ln()

            pdf.set_font("Helvetica", "", 10)
            total_score = Decimal("0")
            subject_count = 0

            for cs in class_subjects:
                subj = db.query(Subject).filter(Subject.id == cs.subject_id).first()
                subj_name = subj.name if subj else "?"

                sg = db.query(SemesterGrade).filter(
                    SemesterGrade.student_id == student.id,
                    SemesterGrade.class_subject_id == cs.id,
                    SemesterGrade.semester_id == semester_id,
                ).first()

                midterm = float(sg.midterm_score) if sg and sg.midterm_score else "-"
                final = float(sg.final_score) if sg and sg.final_score else "-"
                semester_score = float(sg.semester_score) if sg and sg.semester_score else "-"

                # 平時成績平均
                daily_grades = (
                    db.query(DailyGrade)
                    .join(DailyGradeItem)
                    .filter(
                        DailyGradeItem.class_subject_id == cs.id,
                        DailyGrade.student_id == student.id,
                    )
                    .all()
                )
                daily_avg = round(sum(float(g.score) for g in daily_grades) / len(daily_grades), 1) if daily_grades else "-"

                pdf.cell(col_widths[0], 7, subj_name, border=1)
                pdf.cell(col_widths[1], 7, str(midterm), border=1, align="C")
                pdf.cell(col_widths[2], 7, str(final), border=1, align="C")
                pdf.cell(col_widths[3], 7, str(daily_avg), border=1, align="C")
                pdf.cell(col_widths[4], 7, str(semester_score), border=1, align="C")
                pdf.ln()

                if semester_score != "-":
                    total_score += Decimal(str(semester_score))
                    subject_count += 1

            # 總分
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(col_widths[0], 7, "Total / Average", border=1)
            pdf.cell(sum(col_widths[1:4]), 7, "", border=1)
            if subject_count > 0:
                avg = float(total_score / subject_count)
                pdf.cell(col_widths[4], 7, f"{avg:.1f}", border=1, align="C")
            else:
                pdf.cell(col_widths[4], 7, "-", border=1, align="C")
            pdf.ln()

            # 儲存
            import uuid
            file_id = str(uuid.uuid4())[:8]
            filename = f"transcript_{student.name}_{file_id}.pdf"
            filepath = os.path.join(EXPORT_DIR, filename)
            pdf.output(filepath)

            generated.append([student.name, filename])

        if len(generated) == 1:
            msg = f"已產生 {generated[0][0]} 的成績單 PDF"
        else:
            msg = f"已產生 {len(generated)} 份成績單 PDF"

        return SkillResult(
            success=True,
            message=msg,
            data={"files": generated},
            data_card={
                "type": "table",
                "title": "成績單 PDF",
                "payload": {
                    "columns": ["學生", "檔案"],
                    "rows": generated,
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return "產生成績單 PDF"