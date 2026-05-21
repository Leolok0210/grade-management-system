"""
班級德育月報 (Class Monthly Conduct Report)
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.skills.conduct.excel_utils import (
    create_workbook, write_header_row, write_data_row,
    merge_title, save_workbook,
)
from app.models.conduct import RewardPunishment, RegularViolation, ConductAssessment
from app.models.student import Student, Class

VIOLATION_TYPES = ["欠作業", "欠課本", "上課違規", "儀表不符", "遲到", "缺席", "請假"]
GRADE_COLS = ["甲上", "甲中", "甲下", "乙上", "乙中", "乙下", "丙上", "丙中", "丁"]


class ClassMonthlyReport(BaseSkill):
    name = "conduct.class_monthly_report"
    description = "產生班級德育月報，包含獎勵統計、懲罰統計、違紀統計、操行評級分布。當使用者要求產生班級德育月報、月報、德育月報時使用"
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

        rp_query = db.query(RewardPunishment).filter(RewardPunishment.student_id.in_(student_ids))
        if semester_id:
            rp_query = rp_query.filter(RewardPunishment.semester_id == semester_id)
        reward_punishments = rp_query.all()

        rv_query = db.query(RegularViolation).filter(RegularViolation.student_id.in_(student_ids))
        if semester_id:
            rv_query = rv_query.filter(RegularViolation.semester_id == semester_id)
        regular_violations = rv_query.all()

        ca_query = db.query(ConductAssessment).filter(ConductAssessment.student_id.in_(student_ids))
        if semester_id:
            ca_query = ca_query.filter(ConductAssessment.semester_id == semester_id)
        assessments = {a.student_id: a for a in ca_query.all()}

        total_rewards = {"優點": 0, "小功": 0, "大功": 0}
        total_punishments = {"缺點": 0, "小過": 0, "大過": 0}
        total_violations = {vt: 0 for vt in VIOLATION_TYPES}

        for rp in reward_punishments:
            if rp.reward_type in total_rewards and rp.reward_count:
                total_rewards[rp.reward_type] += rp.reward_count
            if rp.punishment_type in total_punishments and rp.punishment_count:
                total_punishments[rp.punishment_type] += rp.punishment_count

        for rv in regular_violations:
            if rv.violation_type in total_violations:
                total_violations[rv.violation_type] += rv.count

        assessment_distribution = {}
        for ca in assessments.values():
            grade = ca.current_assessment or "未評"
            assessment_distribution[grade] = assessment_distribution.get(grade, 0) + 1

        reward_total = sum(total_rewards.values())
        punish_total = sum(total_punishments.values())
        violate_total = sum(total_violations.values())
        grade_row = [assessment_distribution.get(g, 0) for g in GRADE_COLS]

        columns = [
            "優點", "小功", "大功", "獎勵小計",
            "缺點", "小過", "大過", "懲罰小計",
            "欠作業", "欠課本", "上課違規", "儀表不符", "遲到", "缺席", "請假", "違紀小計",
            *GRADE_COLS,
        ]
        rows = [[
            total_rewards["優點"], total_rewards["小功"], total_rewards["大功"], reward_total,
            total_punishments["缺點"], total_punishments["小過"], total_punishments["大過"], punish_total,
            total_violations["欠作業"], total_violations["欠課本"], total_violations["上課違規"],
            total_violations["儀表不符"], total_violations["遲到"], total_violations["缺席"], total_violations["請假"], violate_total,
            *grade_row,
        ]]

        wb, ws = create_workbook(f"{cls.name}德育月報")
        ws.append([f"{cls.name} 德育月報"])
        merge_title(ws, 1, f"{cls.name} 德育月報", 1, len(columns))
        ws.append(columns)
        write_header_row(ws, 2, columns)
        write_data_row(ws, 3, rows[0])

        filename, file_id = save_workbook(wb, f"{cls.name}_德育月報")

        return SkillResult(
            success=True,
            message=f"已產生 {cls.name} 德育月報，共 {len(students)} 名學生",
            data={"filename": filename, "file_id": file_id},
            data_card={
                "type": "table",
                "title": f"{cls.name} 德育月報",
                "payload": {"columns": columns, "rows": rows},
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return f"產生班級德育月報"