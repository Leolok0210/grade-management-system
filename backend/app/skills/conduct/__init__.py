"""
德育管理技能 - 獎懲登記、常規記錄、操行評估
"""
from decimal import Decimal
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.conduct import RewardPunishment, RegularViolation, ConductAssessment
from app.models.student import Student, Class


class ConductDraftList(BaseSkill):
    """常規記錄草榜技能"""
    name = "conduct.draft_list"
    description = "產生常規記錄草榜，包含學生的常規違紀統計、獎懲記錄、操行評估。當使用者要求查看德育記錄、草榜、操行表時使用"
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

        students = db.query(Student).filter(Student.class_id == class_id).order_by(Student.class_number).all()
        if not students:
            return SkillResult(success=False, message="班級內沒有學生")

        student_ids = [s.id for s in students]

        # 取得操行評估
        # 取得操行評估 - 不使用 semester_id 過濾，因為 FK 是 academic_year_id
        assessments = {a.student_id: a for a in db.query(ConductAssessment).filter(ConductAssessment.student_id.in_(student_ids)).all()}

        # 建立表格
        columns = ["學號", "姓名", "欠作業", "欠課本", "上課違規", "儀表不符", "遲到", "缺席", "請假",
                   "優點", "小功", "大功", "義工時數", "抵銷後操行", "操行評語"]
        rows = []

        for student in students:
            ca = assessments.get(student.id)

            row = [
                student.class_number,
                student.name,
                ca.fail_homework if ca else 0,
                ca.fail_textbook if ca else 0,
                ca.fail_classroom if ca else 0,
                ca.fail_uniform if ca else 0,
                ca.fail_late if ca else 0,
                ca.fail_absent if ca else 0,
                ca.leave_hours if ca else 0,
                ca.before_rewards if ca else 0,
                ca.before_minor_awards if ca else 0,
                ca.before_major_awards if ca else 0,
                ca.volunteer_hours if ca else 0,
                ca.current_assessment if ca else "-",
                ca.comment if ca and ca.comment else "",
            ]
            rows.append(row)

        return SkillResult(
            success=True,
            message=f"已產生 {cls.name} 常規記錄草榜，共 {len(students)} 名學生",
            data={"class_name": cls.name, "student_count": len(students)},
            data_card={
                "type": "table",
                "title": f"{cls.name} 常規記錄草榜",
                "payload": {
                    "columns": columns,
                    "rows": rows,
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return f"產生常規記錄草榜"


class ConductAnalysis(BaseSkill):
    """常規記錄分析技能"""
    name = "conduct.analysis"
    description = "分析常規記錄，統計違紀情況、產生分析報告。當使用者要求分析德育、查看缺點統計時使用"
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

        students = db.query(Student).filter(Student.class_id == class_id).order_by(Student.class_number).all()
        student_ids = [s.id for s in students]

        assessments = {a.student_id: a for a in db.query(ConductAssessment).filter(ConductAssessment.student_id.in_(student_ids)).all()}

        # 統計分析
        total_students = len(students)
        analysis_data = []

        for student in students:
            ca = assessments.get(student.id)
            if ca:
                total_violations = ca.fail_homework + ca.fail_textbook + ca.fail_classroom + ca.fail_uniform + ca.fail_late + ca.fail_absent
                analysis_data.append({
                    "name": student.name,
                    "class_number": student.class_number,
                    "total_violations": total_violations,
                    "fail_homework": ca.fail_homework,
                    "fail_textbook": ca.fail_textbook,
                    "fail_classroom": ca.fail_classroom,
                    "fail_uniform": ca.fail_uniform,
                    "fail_late": ca.fail_late,
                    "fail_absent": ca.fail_absent,
                    "leave_hours": ca.leave_hours,
                    "current_assessment": ca.current_assessment,
                })

        # 按違紀次數排序
        analysis_data.sort(key=lambda x: x["total_violations"], reverse=True)

        # 各類型統計
        type_stats = {
            "欠作業": sum(a.fail_homework for a in assessments.values()),
            "欠課本": sum(a.fail_textbook for a in assessments.values()),
            "上課違規": sum(a.fail_classroom for a in assessments.values()),
            "儀表不符": sum(a.fail_uniform for a in assessments.values()),
            "遲到": sum(a.fail_late for a in assessments.values()),
            "缺席": sum(a.fail_absent for a in assessments.values()),
        }

        total_violation_count = sum(type_stats.values())

        # 圖表1：違紀分布
        violation_chart = {
            "type": "chart",
            "title": f"{cls.name} 違紀情況統計",
            "payload": {
                "chart_type": "bar",
                "x_key": "name",
                "y_key": "total_violations",
                "data": analysis_data[:10],
                "x_label": "學生",
                "y_label": "違紀次數",
            },
        }

        # 圖表2：各類型統計
        pie_chart = {
            "type": "chart",
            "title": f"{cls.name} 違紀類型分布",
            "payload": {
                "chart_type": "pie",
                "data": [{"name": k, "value": v} for k, v in type_stats.items()],
            },
        }

        # === AI 分析 prompt ===
        stats_summary = f"""
{cls.name} 常規記錄統計數據：

基本統計：
- 總學生數：{total_students}
- 總違紀次數：{total_violation_count}
- 人均違紀：{round(total_violation_count / total_students, 2) if total_students > 0 else 0}

各類型統計：
{chr(10).join(f'- {k}: {v}次' for k, v in type_stats.items())}

違紀前5名：
{chr(10).join(f'- 第{i+1}名：{d["name"]}，共{d["total_violations"]}次（欠作業{d["fail_homework"]}、欠課本{d["fail_textbook"]}）' for i, d in enumerate(analysis_data[:5]))}

違紀為0的學生：{', '.join([d['name'] for d in analysis_data if d['total_violations'] == 0]) or '無'}
"""

        ai_prompt = f"""你是氹仔坊眾學校的德育管理分析專家。請根據以下常規記錄統計數據，產出一份深度分析報告。

要求：
1. 用繁體中文
2. 分析整體違紀情況（是否嚴重/正常/輕微）
3. 指出主要違紀類型（哪些問題最需要關注）
4. 分析特殊案例（個別學生是否需要特別關注）
5. 給出改善建議（如何減少違紀、提升常規表現）
6. 總結用 3-5 句話

統計數據：
{stats_summary}
"""

        summary_line = f"{cls.name} 常規記錄分析完成，共 {total_students} 名學生，總違紀 {total_violation_count} 次"

        return SkillResult(
            success=True,
            message=f"__STREAM__{summary_line}\n\n",
            data={
                "class_name": cls.name,
                "student_count": total_students,
                "total_violations": total_violation_count,
                "type_stats": type_stats,
                "top_violators": analysis_data[:5],
                "_ai_prompt": ai_prompt,
            },
            data_card={
                "type": "table",
                "title": f"{cls.name} 違紀排名",
                "payload": {
                    "columns": ["排名", "姓名", "欠作業", "欠課本", "上課違規", "儀表不符", "遲到", "缺席", "總計"],
                    "rows": [[i+1, d["name"], d["fail_homework"], d["fail_textbook"], d["fail_classroom"], d["fail_uniform"], d["fail_late"], d["fail_absent"], d["total_violations"]] for i, d in enumerate(analysis_data[:15])]
                },
            },
            data_cards=[violation_chart, pie_chart],
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return f"分析常規記錄"


class ConductAssessmentInput(BaseSkill):
    """操行評估輸入技能"""
    name = "conduct.assessment_input"
    description = "輸入或更新學生操行評估資料。當使用者要求錄入操行、修改操行評語時使用"
    parameters = {
        "type": "object",
        "properties": {
            "student_id": {"type": "integer", "description": "學生ID"},
            "semester_id": {"type": "integer", "description": "學期ID"},
            "current_assessment": {"type": "string", "description": "目前操行評估"},
            "comment": {"type": "string", "description": "操行評語"},
        },
        "required": ["student_id", "semester_id"],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        student_id = params["student_id"]
        semester_id = params["semester_id"]

        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return SkillResult(success=False, message="找不到學生")

        existing = db.query(ConductAssessment).filter(
            ConductAssessment.student_id == student_id,
            ConductAssessment.semester_id == semester_id,
        ).first()

        if existing:
            if "current_assessment" in params:
                existing.current_assessment = params["current_assessment"]
            if "comment" in params:
                existing.comment = params["comment"]
            db.commit()
            return SkillResult(
                success=True,
                message=f"已更新 {student.name} 的操行評估",
            )

        ca = ConductAssessment(
            student_id=student_id,
            semester_id=semester_id,
            current_assessment=params.get("current_assessment"),
            comment=params.get("comment"),
            created_by=context.user_id,
        )
        db.add(ca)
        db.commit()

        return SkillResult(
            success=True,
            message=f"已儲存 {student.name} 的操行評估",
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return f"錄入操行評估"