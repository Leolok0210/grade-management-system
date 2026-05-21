"""
學期成績草榜產生技能 - 完整格式版本
包含：科目、測驗名稱、測驗日期、負責老師、不及格率
"""
from decimal import Decimal
from datetime import date
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.semester_grade import SemesterGrade
from app.models.daily_grade import DailyGradeItem, DailyGrade
from app.models.student import Student, Class
from app.models.subject import ClassSubject, Subject
from app.models.school import Semester
from app.models.table_format import TableFormatTemplate
from app.models.user import User as UserModel


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

        student_ids = [s.id for s in students]

        # 取得班級所有考試項目（daily_grade_items）
        class_subjects = db.query(ClassSubject).filter(ClassSubject.class_id == class_id).all()
        if not class_subjects:
            return SkillResult(success=False, message="班級沒有設定科目")

        # 收集所有考試項目及成績
        exam_items = []  # [(exam_item_id, subject_name, title, date, teacher_name, fail_rate)]

        for cs in class_subjects:
            subj = db.query(Subject).filter(Subject.id == cs.subject_id).first()
            subj_name = subj.name if subj else "?"

            # 取得這個科目的所有考試項目
            items = db.query(DailyGradeItem).filter(DailyGradeItem.class_subject_id == cs.id).order_by(DailyGradeItem.date).all()

            for item in items:
                teacher = db.query(UserModel).filter(UserModel.id == item.created_by).first()
                teacher_name = teacher.name if teacher else "-"

                # 計算這個考試的不及格率
                grades = db.query(DailyGrade).filter(
                    DailyGrade.daily_grade_item_id == item.id,
                    DailyGrade.student_id.in_(student_ids)
                ).all()

                if grades:
                    total = len(grades)
                    fails = sum(1 for g in grades if Decimal(str(g.score)) < passing_score)
                    fail_rate = round(fails / total * 100, 2)
                else:
                    fail_rate = 0.0

                exam_items.append({
                    "id": item.id,
                    "subject_name": subj_name,
                    "title": item.title,
                    "date": item.date.isoformat() if item.date else "",
                    "teacher_name": teacher_name,
                    "fail_rate": fail_rate,
                    "class_subject_id": cs.id,
                })

        # 建立學生成績資料
        student_scores = {}  # student_id -> {scores: {exam_item_id: score}, fail_count: int}
        for student in students:
            student_scores[student.id] = {
                "name": student.name,
                "student_no": student.student_no,
                "class_number": student.class_number,
                "scores": {},
                "fail_count": 0,
            }

        # 填充成績
        for exam in exam_items:
            grades = db.query(DailyGrade).filter(
                DailyGrade.daily_grade_item_id == exam["id"],
                DailyGrade.student_id.in_(student_ids)
            ).all()

            for g in grades:
                score = float(g.score)
                student_scores[g.student_id]["scores"][exam["id"]] = round(score, 1)
                if Decimal(str(score)) < passing_score:
                    student_scores[g.student_id]["fail_count"] += 1

        # 排名（按總分）
        ranked = sorted(
            [(sid, data) for sid, data in student_scores.items()],
            key=lambda x: sum(x[1]["scores"].values()) if x[1]["scores"] else 0,
            reverse=True,
        )

        # 建立表格
        # 表頭欄位：第一欄空白，之後每個考試一欄（包含科目）
        header1 = ["", "", "", "", ""]  # 排名、學生編號、班級、姓名、學號
        header2 = ["排名", "學生編號", "班級", "姓名", "學號"]  # 第二行
        header3 = []  # 測驗名稱
        header4 = []  # 測驗日期
        header5 = []  # 負責老師
        header6 = []  # 不及格率

        columns = ["排名", "學生編號", "班級", "姓名", "學號"]
        for exam in exam_items:
            columns.append(exam["subject_name"])
            header3.append(exam["title"])
            header4.append(exam["date"])
            header5.append(exam["teacher_name"])
            header6.append(f"{exam['fail_rate']:.2f}%")

        columns.append("不及格測驗")
        header3.append("")
        header4.append("")
        header5.append("")
        header6.append("次數")

        # 建立學生資料列
        rows = []
        for idx, (sid, data) in enumerate(ranked):
            row = [
                idx + 1,  # 排名
                data["student_no"] or "",
                cls.name,
                data["name"],
                str(data["class_number"]) if data["class_number"] else "",
            ]

            for exam in exam_items:
                score = data["scores"].get(exam["id"])
                if score is not None:
                    if Decimal(str(score)) < passing_score:
                        cell = f"<span style=\"background-color:{fail_score_bg};\">{score}</span>"
                    else:
                        cell = str(score)
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
            message=f"已產生 {cls.name} 學期成績草榜，共 {len(ranked)} 名學生，{len(exam_items)} 個考試項目" + (f"（使用模板：{template.name}）" if template else ""),
            data={
                "class_name": cls.name,
                "student_count": len(ranked),
                "exam_count": len(exam_items),
                "template_used": template.name if template else "預設",
            },
            data_card={
                "type": "table",
                "title": f"{cls.name} 學期成績草榜",
                "payload": {
                    "columns": columns,
                    "rows": rows,
                    "headers": {
                        "測驗名稱": header3,
                        "測驗日期": header4,
                        "負責老師": header5,
                        "不及格率": header6,
                    },
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
                            {"rank": idx + 1, "name": data["name"], "student_no": data["student_no"], "total": float(sum(data["scores"].values()))}
                            for idx, (_, data) in enumerate(ranked)
                        ],
                        "x_label": "學生",
                        "y_label": "總分",
                    },
                },
                {
                    "type": "chart",
                    "title": f"{cls.name} 不及格次數分布",
                    "payload": {
                        "chart_type": "bar",
                        "x_key": "name",
                        "y_key": "fail_count",
                        "data": [
                            {"name": data["name"], "fail_count": data["fail_count"]}
                            for _, data in ranked
                        ],
                        "x_label": "學生",
                        "y_label": "不及格次數",
                    },
                },
            ],
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return f"產生學期成績草榜"