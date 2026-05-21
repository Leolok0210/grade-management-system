"""
學期成績草榜產生技能
"""
from decimal import Decimal
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.semester_grade import SemesterGrade
from app.models.daily_grade import DailyGradeItem, DailyGrade
from app.models.student import Student, Class
from app.models.subject import ClassSubject, Subject
from app.models.school import Semester
from app.models.table_format import TableFormatTemplate


class DraftList(BaseSkill):
    name = "semester_grade.draft_list"
    description = "產生學期成績草榜，包含各科加權總分、排名、不及格標記。當使用者要求產生草榜、成績總表、學期成績單時使用"
    parameters = {
        "type": "object",
        "properties": {
            "class_id": {"type": "integer", "description": "班級ID"},
            "semester_id": {"type": "integer", "description": "學期ID"},
            "passing_score": {"type": "number", "description": "及格分數線，預設60"},
            "template_name": {"type": "string", "description": "表格格式模板名稱（可選）"},
        },
        "required": ["class_id", "semester_id"],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        class_id = params["class_id"]
        semester_id = params["semester_id"]
        passing_score = Decimal(str(params.get("passing_score", 60)))

        # 取得格式模板
        template = None
        template_name = params.get("template_name")
        if template_name:
            template = db.query(TableFormatTemplate).filter(
                TableFormatTemplate.name == template_name,
                TableFormatTemplate.is_active == True,
            ).first()
        if not template:
            template = TableFormatTemplate.get_default_template("draft_list", db)

        # 讀取模板樣式設定
        style_config = template.style_config if template else {}
        fail_score_bg = style_config.get("fail_score_bg", "#ffcccc")
        fail_count_bg = style_config.get("fail_count_bg", "#ff9999")

        cls = db.query(Class).filter(Class.id == class_id).first()
        if not cls:
            return SkillResult(success=False, message="找不到班級")

        semester = db.query(Semester).filter(Semester.id == semester_id).first()
        if not semester:
            return SkillResult(success=False, message="找不到學期")

        # 取得班級所有學生
        students = db.query(Student).filter(Student.class_id == class_id).order_by(Student.class_number).all()
        if not students:
            return SkillResult(success=False, message="班級內沒有學生")

        # 取得班級所有科目
        class_subjects = db.query(ClassSubject).filter(ClassSubject.class_id == class_id).all()
        if not class_subjects:
            return SkillResult(success=False, message="班級沒有設定科目")

        # 計算每位學生的各科成績
        student_scores = {}  # student_id -> {subject_name: score, total_weighted: Decimal, fail_count: int}
        subject_names = []

        for cs in class_subjects:
            subj = db.query(Subject).filter(Subject.id == cs.subject_id).first()
            subj_name = subj.name if subj else "?"
            subject_names.append(subj_name)

            for student in students:
                if student.id not in student_scores:
                    student_scores[student.id] = {"name": student.name, "subjects": {}, "total": Decimal("0"), "fail_count": 0}

                # 先查學期成績
                sg = db.query(SemesterGrade).filter(
                    SemesterGrade.student_id == student.id,
                    SemesterGrade.class_subject_id == cs.id,
                    SemesterGrade.semester_id == semester_id,
                ).first()

                if sg and sg.semester_score is not None:
                    score = float(sg.semester_score)
                elif sg and sg.midterm_score is not None:
                    # 只有期中成績，用期中分數
                    score = float(sg.midterm_score)
                else:
                    # 沒有學期成績，從平時成績計算加權平均
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
                        score = round(avg, 1)
                    else:
                        score = None

                student_scores[student.id]["subjects"][subj_name] = score
                if score is not None:
                    student_scores[student.id]["total"] += Decimal(str(score))
                    if Decimal(str(score)) < passing_score:
                        student_scores[student.id]["fail_count"] += 1

        # 排名（按總分）
        ranked = sorted(
            [(sid, data) for sid, data in student_scores.items()],
            key=lambda x: x[1]["total"],
            reverse=True,
        )

        # 建立表格 - 符合格式要求的欄位結構
        columns = ["學生編號|班級|姓名|學號"]
        for subj_name in subject_names:
            columns.append(subj_name)
        columns.append("不及格測驗")
        rows = []
        for rank, (sid, data) in enumerate(ranked, 1):
            student = next((s for s in students if s.id == sid), None)
            student_no = student.student_no if student else "?"
            class_number = student.class_number if student else "?"

            # 第一欄：學生識別
            row = [f"{student_no}|初一甲|{data['name']}|{class_number}"]

            # 各科分數
            for subj_name in subject_names:
                score = data["subjects"].get(subj_name)
                if score is not None:
                    if Decimal(str(score)) < passing_score:
                        cell = f"<span style=\"background-color:{fail_score_bg};\">{score}</span>"
                    else:
                        cell = f"{score}"
                    row.append(cell)
                else:
                    row.append("-")

            # 不及格次數
            fail_count = data["fail_count"]
            if fail_count > 0:
                count_cell = f"<span style=\"background-color:{fail_count_bg};\"><b><i>{fail_count}</i></b></span>"
            else:
                count_cell = "0"
            row.append(count_cell)
            rows.append(row)

        return SkillResult(
            success=True,
            message=f"已產生 {cls.name} 學期成績草榜，共 {len(ranked)} 名學生" + (f"（使用模板：{template.name}）" if template else ""),
            data={
                "class_name": cls.name,
                "student_count": len(ranked),
                "template_used": template.name if template else "預設",
            },
            data_card={
                "type": "table",
                "title": f"{cls.name} 學期成績草榜",
                "payload": {
                    "columns": columns,
                    "rows": rows,
                    "style_config": style_config,
                },
            },
            data_cards=[
                {
                    "type": "chart",
                    "title": f"{cls.name} 學期總分排名",
                    "payload": {
                        "chart_type": "bar",
                        "x_key": "name",
                        "y_key": "total",
                        "data": [
                            {"name": data["name"], "total": float(data["total"])}
                            for _, data in ranked
                        ],
                        "x_label": "學生",
                        "y_label": "總分",
                    },
                },
            ],
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return f"產生學期成績草榜"