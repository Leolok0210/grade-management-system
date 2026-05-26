"""
針對性成績查詢技能 - 回答特定問題而非輸出完整表格
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.daily_grade import DailyGradeItem, DailyGrade
from app.models.student import Student
from app.models.subject import ClassSubject, Subject
from app.models.student import Class


class DailyGradeQuery(BaseSkill):
    name = "daily_grade.query"
    description = "針對性成績查詢：最高分、最低分、不及格人數、平均分等。當用戶問「誰最高」「誰不及格」「平均分數」等針對性問題時使用"
    parameters = {
        "type": "object",
        "properties": {
            "class_subject_id": {"type": "integer", "description": "班級科目ID"},
            "query_type": {"type": "string", "description": "查詢類型：top/bottom/fail_count/avg/pass_rate"},
            "limit": {"type": "integer", "description": "返回數量（默認5）"},
        },
        "required": ["class_subject_id", "query_type"],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        class_subject_id = params["class_subject_id"]
        query_type = params["query_type"]
        # 支援 fail_count 作為 fail 的別名
        if query_type == "fail_count":
            query_type = "fail"
        limit = params.get("limit", 5)

        # 取得班級科目資訊
        cs = db.query(ClassSubject).filter(ClassSubject.id == class_subject_id).first()
        if not cs:
            return SkillResult(success=False, message="找不到班級科目")

        cls = db.query(Class).filter(Class.id == cs.class_id).first()
        subj = db.query(Subject).filter(Subject.id == cs.subject_id).first()
        cls_name = cls.name if cls else "?"
        subj_name = subj.name if subj else "?"

        # 查詢成績
        grades = db.query(DailyGrade).filter(
            DailyGrade.daily_grade_item_id.in_(
                db.query(DailyGradeItem.id).filter(DailyGradeItem.class_subject_id == class_subject_id)
            )
        ).all()

        if not grades:
            return SkillResult(success=True, message=f"查無 {cls_name} {subj_name} 成績記錄")

        # 按學生分組計算平均分
        student_scores = {}
        for g in grades:
            sid = g.student_id
            if sid not in student_scores:
                student_scores[sid] = []
            student_scores[sid].append(float(g.score))

        student_avgs = []
        for sid, scores in student_scores.items():
            student = db.query(Student).filter(Student.id == sid).first()
            avg = round(sum(scores) / len(scores), 2)
            student_avgs.append({
                "id": sid,
                "name": student.name if student else f"學生{sid}",
                "class_number": student.class_number if student else None,
                "avg": avg,
                "count": len(scores),
                "max": max(scores),
                "min": min(scores),
            })

        # 根據查詢類型返回結果
        if query_type == "top":
            student_avgs.sort(key=lambda x: x["avg"], reverse=True)
            top = student_avgs[:limit]
            answer = f"**{cls_name} {subj_name} 最高分（前{len(top)}名）：**\n"
            for i, s in enumerate(top, 1):
                answer += f"{i}. {s['name']} — 平均 {s['avg']} 分（最高 {s['max']}分，共 {s['count']} 次測驗）\n"

        elif query_type == "bottom":
            student_avgs.sort(key=lambda x: x["avg"])
            bottom = student_avgs[:limit]
            answer = f"**{cls_name} {subj_name} 最低分（前{len(bottom)}名）：**\n"
            for i, s in enumerate(bottom, 1):
                answer += f"{i}. {s['name']} — 平均 {s['avg']} 分（最低 {s['min']}分，共 {s['count']} 次測驗）\n"

        elif query_type == "fail":
            fails = [s for s in student_avgs if s["avg"] < 60]
            fails.sort(key=lambda x: x["avg"])
            if not fails:
                return SkillResult(success=True, message=f"{cls_name} {subj_name} 目前沒有不及格學生（平均分均高於60分）")
            answer = f"**{cls_name} {subj_name} 不及格學生（平均分低於60分，共 {len(fails)} 人）：**\n"
            for s in fails:
                answer += f"- {s['name']} — 平均 {s['avg']} 分\n"

        elif query_type == "avg":
            all_avgs = [s["avg"] for s in student_avgs]
            overall_avg = round(sum(all_avgs) / len(all_avgs), 2)
            answer = f"**{cls_name} {subj_name} 全班平均分：{overall_avg} 分**\n"
            answer += f"（共 {len(student_avgs)} 名學生）"

        elif query_type == "pass_rate":
            pass_count = len([s for s in student_avgs if s["avg"] >= 60])
            pass_rate = round(pass_count / len(student_avgs) * 100, 1)
            answer = f"**{cls_name} {subj_name} 及格率：{pass_rate}%**\n"
            answer += f"（及格 {pass_count} 人 / 全班 {len(student_avgs)} 人）"

        elif query_type == "rank":
            student_avgs.sort(key=lambda x: x["avg"], reverse=True)
            answer = f"**{cls_name} {subj_name} 排名：**\n"
            for i, s in enumerate(student_avgs, 1):
                answer += f"第{i}名：{s['name']} — 平均 {s['avg']} 分\n"

        else:
            answer = f"未知查詢類型：{query_type}"

        return SkillResult(success=True, message=answer)

    def preview(self, params: dict, context: UserContext) -> str:
        return f"查詢成績（{params.get('query_type', '?')}）"