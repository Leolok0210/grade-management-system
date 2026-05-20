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


class DraftList(BaseSkill):
    name = "semester_grade.draft_list"
    description = "產生學期成績草榜，包含各科加權總分、排名、不及格標記。當使用者要求產生草榜、成績總表、學期成績單時使用"
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

        # 建立表格
        columns = ["排名", "學生"] + subject_names + ["總分", "不及格數"]
        rows = []
        for rank, (sid, data) in enumerate(ranked, 1):
            row = [rank, data["name"]]
            for subj_name in subject_names:
                score = data["subjects"].get(subj_name)
                if score is not None:
                    cell = score
                    if Decimal(str(score)) < passing_score:
                        cell = f"{score} ✗"
                    row.append(cell)
                else:
                    row.append("-")
            row.append(float(data["total"]))
            row.append(data["fail_count"])
            rows.append(row)

        return SkillResult(
            success=True,
            message=f"已產生 {cls.name} 學期成績草榜，共 {len(ranked)} 名學生",
            data={"class_name": cls.name, "student_count": len(ranked)},
            data_card={
                "type": "table",
                "title": f"{cls.name} 學期成績草榜",
                "payload": {
                    "columns": columns,
                    "rows": rows,
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