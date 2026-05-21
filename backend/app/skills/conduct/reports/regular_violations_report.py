"""
常規違紀總結 (Regular Violations Summary)
"""
from openpyxl.styles import Font, Alignment

from app.skills.base import BaseSkill, SkillResult, UserContext
from app.skills.conduct.excel_utils import (
    create_workbook, write_header_row, write_data_row,
    merge_title, save_workbook,
)
from app.models.conduct import RegularViolation
from app.models.student import Student, Class

VIOLATION_TYPES = ["欠作業", "欠課本", "上課違規", "儀表不符", "遲到", "缺席", "請假"]


class RegularViolationsReport(BaseSkill):
    name = "conduct.regular_violations_report"
    description = "產生常規違紀總結 per-class per-semester student-level violation breakdown. 當使用者要求常規違紀總結、違紀總結、產生違紀總結時使用"
    parameters = {
        "type": "object",
        "properties": {
            "class_id": {"type": "integer", "description": "班級ID"},
            "semester_id": {"type": "integer", "description": "學期ID"},
        },
        "required": ["class_id"],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        class_id = params["class_id"]
        semester_id = params.get("semester_id")

        cls = db.query(Class).filter(Class.id == class_id).first()
        if not cls:
            return SkillResult(success=False, message="找不到班級")

        students = db.query(Student).filter(
            Student.class_id == class_id, Student.status == "active"
        ).order_by(Student.class_number).all()
        if not students:
            return SkillResult(success=False, message="班級內沒有學生")

        student_ids = [s.id for s in students]

        rv_query = db.query(RegularViolation).filter(RegularViolation.student_id.in_(student_ids))
        if semester_id:
            rv_query = rv_query.filter(RegularViolation.semester_id == semester_id)
        rv_records = rv_query.all()

        student_violations = {sid: {vt: 0 for vt in VIOLATION_TYPES} for sid in student_ids}
        violation_details = {sid: {vt: [] for vt in VIOLATION_TYPES} for sid in student_ids}

        for rv in rv_records:
            if rv.violation_type in student_violations[rv.student_id]:
                student_violations[rv.student_id][rv.violation_type] += rv.count
                if rv.record_date:
                    violation_details[rv.student_id][rv.violation_type].append(
                        f"{rv.record_date.isoformat()}(×{rv.count})"
                    )

        columns = ["班內學號", "姓名"] + VIOLATION_TYPES + ["總計", "違紀詳情"]
        rows = []

        for student in students:
            viol = student_violations[student.id]
            total = sum(viol.values())
            details_parts = []
            for vt in VIOLATION_TYPES:
                if violation_details[student.id][vt]:
                    details_parts.append(f"{vt}: {', '.join(violation_details[student.id][vt])}")
            details_str = "; ".join(details_parts) if details_parts else ""

            row = [student.class_number, student.name] + [viol[vt] for vt in VIOLATION_TYPES] + [total, details_str]
            rows.append(row)

        wb, ws = create_workbook(f"{cls.name}違紀總結")
        ws.append([f"{cls.name} 常規違紀總結"])
        merge_title(ws, 1, f"{cls.name} 常規違紀總結", 1, len(columns))
        ws.append(columns)
        write_header_row(ws, 2, columns)
        for row_idx, row_data in enumerate(rows, start=3):
            ws.append(row_data)
            write_data_row(ws, row_idx, row_data)
            ws.cell(row=row_idx, column=len(columns)).alignment = Alignment(wrap_text=True)

        filename, file_id = save_workbook(wb, f"{cls.name}_違紀總結")

        return SkillResult(
            success=True,
            message=f"已產生 {cls.name} 常規違紀總結，共 {len(students)} 名學生",
            data={"filename": filename, "file_id": file_id},
            data_card={
                "type": "table",
                "title": f"{cls.name} 常規違紀總結",
                "payload": {"columns": columns, "rows": rows},
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return f"產生常規違紀總結"