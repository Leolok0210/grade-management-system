"""
獎懲統計報表 (Rewards/Punishments Statistics Report)
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.skills.conduct.excel_utils import (
    create_workbook, write_header_row, write_data_row,
    merge_title, save_workbook,
)
from app.models.conduct import RewardPunishment
from app.models.student import Student, Class


class RewardsPunishmentsReport(BaseSkill):
    name = "conduct.rewards_punishments_report"
    description = "產生獎懲統計報表 per-class per-semester student-level reward/punishment breakdown with reasons. 當使用者要求獎懲統計、獎懲報表、產生獎懲統計時使用"
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
        rp_records = rp_query.all()

        student_stats = {sid: {
            "優點": 0, "小功": 0, "大功": 0,
            "缺點": 0, "小過": 0, "大過": 0,
            "reward_reasons": [], "punishment_reasons": [],
        } for sid in student_ids}

        for rp in rp_records:
            stats = student_stats[rp.student_id]
            if rp.reward_type and rp.reward_count:
                stats[rp.reward_type] += rp.reward_count
                if rp.reward_reason:
                    stats["reward_reasons"].append(f"{rp.reward_type}×{rp.reward_count}: {rp.reward_reason}")
            if rp.punishment_type and rp.punishment_count:
                stats[rp.punishment_type] += rp.punishment_count
                if rp.punishment_reason:
                    stats["punishment_reasons"].append(f"{rp.punishment_type}×{rp.punishment_count}: {rp.punishment_reason}")

        columns = ["班內學號", "姓名", "優點", "小功", "大功", "獎勵小計", "缺點", "小過", "大過", "懲罰小計", "獎勵原因", "懲罰原因"]
        rows = []

        for student in students:
            stats = student_stats[student.id]
            reward_sum = stats["優點"] + stats["小功"] + stats["大功"]
            punish_sum = stats["缺點"] + stats["小過"] + stats["大過"]
            rows.append([
                student.class_number,
                student.name,
                stats["優點"], stats["小功"], stats["大功"], reward_sum,
                stats["缺點"], stats["小過"], stats["大過"], punish_sum,
                "; ".join(stats["reward_reasons"][:3]) if stats["reward_reasons"] else "",
                "; ".join(stats["punishment_reasons"][:3]) if stats["punishment_reasons"] else "",
            ])

        wb, ws = create_workbook(f"{cls.name}獎懲統計")
        ws.append([f"{cls.name} 獎懲統計報表"])
        merge_title(ws, 1, f"{cls.name} 獎懲統計報表", 1, len(columns))
        ws.append(columns)
        write_header_row(ws, 2, columns)
        for row_idx, row_data in enumerate(rows, start=3):
            ws.append(row_data)
            write_data_row(ws, row_idx, row_data)

        filename, file_id = save_workbook(wb, f"{cls.name}_獎懲統計")

        return SkillResult(
            success=True,
            message=f"已產生 {cls.name} 獎懲統計報表，共 {len(students)} 名學生",
            data={"filename": filename, "file_id": file_id},
            data_card={
                "type": "table",
                "title": f"{cls.name} 獎懲統計報表",
                "payload": {"columns": columns, "rows": rows},
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return f"產生獎懲統計報表"