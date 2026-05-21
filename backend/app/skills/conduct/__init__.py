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
        query = db.query(ConductAssessment).filter(ConductAssessment.student_id.in_(student_ids))
        if semester_id:
            query = query.filter(ConductAssessment.semester_id == semester_id)
        assessments = {a.student_id: a for a in query.all()}

        # 建立表格
        columns = ["學號", "姓名", "欠作業", "欠課本", "上課違規", "儀表不符", "遲到", "缺席", "請假",
                   "優點", "小功", "大功", "義工時數", "抵銷後操行", "操行評語"]
        rows = []

        for student in students:
            ca = assessments.get(student.id)

            row = [
                student.class_number,
                student.name,
                ca.欠作業 if ca else 0,
                ca.欠課本 if ca else 0,
                ca.上課違規 if ca else 0,
                ca.儀表不符 if ca else 0,
                ca.遲到 if ca else 0,
                ca.缺席 if ca else 0,
                ca.請假 if ca else 0,
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

        query = db.query(ConductAssessment).filter(ConductAssessment.student_id.in_(student_ids))
        if semester_id:
            query = query.filter(ConductAssessment.semester_id == semester_id)
        assessments = {a.student_id: a for a in query.all()}

        # 統計分析
        total_students = len(students)
        analysis_data = []

        for student in students:
            ca = assessments.get(student.id)
            if ca:
                total_violations = ca.欠作業 + ca.欠課本 + ca.上課違規 + ca.儀表不符 + ca.遲到 + ca.缺席
                analysis_data.append({
                    "name": student.name,
                    "class_number": student.class_number,
                    "total_violations": total_violations,
                    "欠作業": ca.欠作業,
                    "欠課本": ca.欠課本,
                    "上課違規": ca.上課違規,
                    "current_assessment": ca.current_assessment,
                })

        # 按違紀次數排序
        analysis_data.sort(key=lambda x: x["total_violations"], reverse=True)

        # 圖表1：違紀分布
        violation_chart = {
            "type": "chart",
            "title": f"{cls.name} 違紀情況統計",
            "payload": {
                "chart_type": "bar",
                "x_key": "name",
                "y_key": "total_violations",
                "data": analysis_data[:10],  # 前10名
                "x_label": "學生",
                "y_label": "違紀次數",
            },
        }

        # 圖表2：各類型統計
        type_stats = {
            "欠作業": sum(a.欠作業 for a in assessments.values()),
            "欠課本": sum(a.欠課本 for a in assessments.values()),
            "上課違規": sum(a.上課違規 for a in assessments.values()),
            "儀表不符": sum(a.儀表不符 for a in assessments.values()),
            "遲到": sum(a.遲到 for a in assessments.values()),
            "缺席": sum(a.缺席 for a in assessments.values()),
        }

        pie_chart = {
            "type": "chart",
            "title": f"{cls.name} 違紀類型分布",
            "payload": {
                "chart_type": "pie",
                "data": [{"name": k, "value": v} for k, v in type_stats.items()],
            },
        }

        return SkillResult(
            success=True,
            message=f"已完成 {cls.name} 常規記錄分析",
            data={"class_name": cls.name, "student_count": total_students},
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