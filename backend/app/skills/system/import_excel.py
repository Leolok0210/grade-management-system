"""
Excel 批次匯入技能
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.daily_grade import DailyGradeItem, DailyGrade
from app.models.semester_grade import SemesterGrade
from app.models.student import Student
from app.models.subject import ClassSubject


class ImportExcel(BaseSkill):
    name = "system.import_excel"
    description = "從 Excel 檔案批次匯入成績資料，支援平時成績和學期成績匯入"
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Excel 檔案路徑"},
            "import_type": {"type": "string", "enum": ["daily", "semester"], "description": "匯入類型：平時成績或學期成績"},
            "class_subject_id": {"type": "string", "description": "班級科目ID"},
            "semester_id": {"type": "string", "description": "學期ID"},
            "title": {"type": "string", "description": "成績項目標題（平時成績用）"},
            "grade_type": {"type": "string", "description": "成績類型（平時成績用）"},
        },
        "required": ["file_path", "import_type", "class_subject_id", "semester_id"],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        from openpyxl import load_workbook

        file_path = params["file_path"]
        import_type = params["import_type"]
        class_subject_id = params["class_subject_id"]
        semester_id = params["semester_id"]

        try:
            wb = load_workbook(file_path)
            ws = wb.active
        except Exception as e:
            return SkillResult(success=False, message=f"無法讀取 Excel 檔案: {e}")

        # 取得學生列表
        cs = db.query(ClassSubject).filter(ClassSubject.id == class_subject_id).first()
        if not cs:
            return SkillResult(success=False, message="找不到班級科目設定")

        students = db.query(Student).filter(Student.class_id == cs.class_id).all()
        student_map = {s.student_no: s for s in students}

        imported = []
        errors = []

        if import_type == "daily":
            # 平時成績匯入
            title = params.get("title", ws.title or "匯入成績")
            grade_type = params.get("grade_type", "其他")

            item = DailyGradeItem(
                class_subject_id=class_subject_id,
                title=title,
                grade_type=grade_type,
                date=__import__("datetime").date.today(),
                created_by=context.user_id,
            )
            db.add(item)
            db.flush()

            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or len(row) < 2:
                    continue
                student_no, score = str(row[0]), row[1]
                student = student_map.get(student_no)
                if not student:
                    errors.append(f"找不到學號 {student_no}")
                    continue

                grade = DailyGrade(
                    daily_grade_item_id=item.id,
                    student_id=student.id,
                    score=__import__("decimal").Decimal(str(score)),
                    created_by=context.user_id,
                )
                db.add(grade)
                imported.append([student.name, score])

            db.commit()

        elif import_type == "semester":
            # 學期成績匯入
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or len(row) < 2:
                    continue
                student_no = str(row[0])
                student = student_map.get(student_no)
                if not student:
                    errors.append(f"找不到學號 {student_no}")
                    continue

                score_data = {"student_id": student.id}
                if len(row) >= 2 and row[1]:
                    score_data["midterm_score"] = row[1]
                if len(row) >= 3 and row[2]:
                    score_data["final_score"] = row[2]
                if len(row) >= 4 and row[3]:
                    score_data["semester_score"] = row[3]

                existing = db.query(SemesterGrade).filter(
                    SemesterGrade.student_id == student.id,
                    SemesterGrade.class_subject_id == class_subject_id,
                    SemesterGrade.semester_id == semester_id,
                ).first()

                if existing:
                    for key in ["midterm_score", "final_score", "semester_score"]:
                        if key in score_data:
                            setattr(existing, key, __import__("decimal").Decimal(str(score_data[key])))
                else:
                    sg = SemesterGrade(
                        student_id=student.id,
                        class_subject_id=class_subject_id,
                        semester_id=semester_id,
                        status="draft",
                    )
                    for key in ["midterm_score", "final_score", "semester_score"]:
                        if key in score_data:
                            setattr(sg, key, __import__("decimal").Decimal(str(score_data[key])))
                    db.add(sg)

                imported.append([student.name, score_data.get("semester_score", "-")])

            db.commit()

        msg = f"已匯入 {len(imported)} 筆成績"
        if errors:
            msg += f"，{len(errors)} 筆有誤"

        return SkillResult(
            success=True,
            message=msg,
            data={"imported": len(imported), "errors": len(errors)},
            data_card={
                "type": "table",
                "title": "匯入結果",
                "payload": {
                    "columns": ["學生", "分數"],
                    "rows": imported[:30],
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return f"匯入 {params.get('import_type', '')} 成績"