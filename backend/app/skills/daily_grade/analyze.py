"""
平時成績分析技能 — 統計計算 + AI 串流分析
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.daily_grade import DailyGradeItem, DailyGrade
from app.models.student import Student
from app.models.subject import ClassSubject, Subject
from app.models.student import Class


class DailyGradeAnalyze(BaseSkill):
    name = "daily_grade.analyze"
    description = "分析平時成績，包含學生排名、平均分數、分數分佈、最高最低分、標準差，並由 AI 產出深度分析報告。當使用者提到排名、名次、前幾名、成績分析、成績怎麼樣時使用此技能"
    parameters = {
        "type": "object",
        "properties": {
            "class_subject_id": {"type": "integer", "description": "班級科目ID"},
            "grade_type": {"type": "string", "description": "成績類型篩選"},
        },
        "required": ["class_subject_id"],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        class_subject_id = params["class_subject_id"]

        cs = db.query(ClassSubject).filter(ClassSubject.id == class_subject_id).first()
        if not cs:
            return SkillResult(success=False, message="找不到班級科目設定")

        cls = db.query(Class).filter(Class.id == cs.class_id).first()
        subj = db.query(Subject).filter(Subject.id == cs.subject_id).first()
        cls_name = cls.name if cls else "?"
        subj_name = subj.name if subj else "?"

        query = db.query(DailyGrade).join(DailyGradeItem).filter(
            DailyGradeItem.class_subject_id == class_subject_id
        )

        if params.get("grade_type"):
            query = query.filter(DailyGradeItem.grade_type == params["grade_type"])

        grades = query.all()

        if not grades:
            return SkillResult(success=True, message="查無成績資料可供分析")

        # === 統計計算 ===
        scores = [float(g.score) for g in grades]
        avg = round(sum(scores) / len(scores), 2)
        max_score = max(scores)
        min_score = min(scores)
        variance = sum((s - avg) ** 2 for s in scores) / len(scores)
        std_dev = round(variance ** 0.5, 2)

        # 分數分佈
        ranges = [(0, 59.9, "不及格(0-59)"), (60, 69.9, "及格(60-69)"), (70, 79.9, "中等(70-79)"), (80, 89.9, "良好(80-89)"), (90, 200, "優秀(90+)")]
        distribution = {}
        dist_chart_data = []
        for low, high, label in ranges:
            count = len([s for s in scores if low <= s <= high])
            pct = round(count / len(scores) * 100, 1)
            distribution[label] = f"{count}人({pct}%)"
            dist_chart_data.append({"range": label, "count": count})

        # 及格率
        pass_count = len([s for s in scores if s >= 60])
        pass_rate = round(pass_count / len(scores) * 100, 1)

        # 各學生平均 + 排名
        student_avgs = {}
        for g in grades:
            student_avgs.setdefault(g.student_id, []).append(float(g.score))

        ranked_rows = []
        for sid, s_scores in student_avgs.items():
            student = db.query(Student).filter(Student.id == sid).first()
            s_avg = round(sum(s_scores) / len(s_scores), 2)
            ranked_rows.append([student.name if student else sid, s_avg, len(s_scores)])

        ranked_rows.sort(key=lambda x: x[1], reverse=True)
        final_rows = [[rank, *row] for rank, row in enumerate(ranked_rows, 1)]

        # 各次考試平均
        exam_avgs = []
        items = db.query(DailyGradeItem).filter(
            DailyGradeItem.class_subject_id == class_subject_id
        ).order_by(DailyGradeItem.date).all()
        for item in items:
            item_scores = [float(g.score) for g in item.grades]
            if item_scores:
                exam_avgs.append({
                    "title": item.title,
                    "date": item.date.isoformat(),
                    "avg": round(sum(item_scores) / len(item_scores), 2),
                    "max": max(item_scores),
                    "min": min(item_scores),
                    "pass_rate": round(len([s for s in item_scores if s >= 60]) / len(item_scores) * 100, 1),
                })

        # === 統計摘要（立即返回） ===
        grade_type_desc = params.get("grade_type", "全部")
        summary_line = f"{cls_name} {subj_name}（{grade_type_desc}）：平均 {avg} 分，最高 {max_score}，最低 {min_score}，標準差 {std_dev}，及格率 {pass_rate}%"

        # === AI 分析 prompt（交由 orchestrator 串流推送） ===
        stats_summary = f"""
{cls_name} {subj_name} 平時成績統計數據：

基本統計：
- 總筆數：{len(scores)}
- 平均分：{avg}
- 最高分：{max_score}
- 最低分：{min_score}
- 標準差：{std_dev}
- 及格率：{pass_rate}%

分數分佈：
{chr(10).join(f'- {k}: {v}' for k, v in distribution.items())}

各次考試平均：
{chr(10).join(f'- {e["title"]}({e["date"]})：平均{e["avg"]}，最高{e["max"]}，最低{e["min"]}，及格率{e["pass_rate"]}%' for e in exam_avgs)}

學生排名（前5名）：
{chr(10).join(f'- 第{r[0]}名：{r[1]}，平均{r[2]}分' for r in final_rows[:5])}

學生排名（後5名）：
{chr(10).join(f'- 第{r[0]}名：{r[1]}，平均{r[2]}分' for r in final_rows[-5:])}
"""

        ai_prompt = f"""你是氹仔坊眾學校的成績分析專家。請根據以下統計數據，產出一份深度分析報告。

要求：
1. 用繁體中文
2. 分析整體成績水平（偏高/正常/偏低）
3. 指出分數分佈的特徵（是否兩極分化、是否集中）
4. 分析各次考試的變化趨勢（是否進步/退步）
5. 指出需要關注的學生（低分群、高分群）
6. 給出教學建議（如何幫低分學生、如何維持高分學生）
7. 總結用 3-5 句話

統計數據：
{stats_summary}
"""

        # __STREAM__ 前綴告訴 orchestrator：靜態部分先推送，AI 分析串流推送
        return SkillResult(
            success=True,
            message=f"__STREAM__{summary_line}\n\n",
            data={
                "average": avg,
                "max": max_score,
                "min": min_score,
                "std_dev": std_dev,
                "pass_rate": pass_rate,
                "distribution": distribution,
                "count": len(scores),
                "exam_trends": exam_avgs,
                "_ai_prompt": ai_prompt,
            },
            data_card={
                "type": "table",
                "title": f"{cls_name} {subj_name} 成績排名",
                "payload": {
                    "columns": ["排名", "學生", "平均分數", "成績筆數"],
                    "rows": final_rows,
                },
            },
            data_cards=[
                {
                    "type": "chart",
                    "title": f"{cls_name} {subj_name} 成績分佈",
                    "payload": {
                        "chart_type": "bar",
                        "x_key": "range",
                        "y_key": "count",
                        "data": dist_chart_data,
                        "x_label": "分數區間",
                        "y_label": "人數",
                        "colors": ["#ef4444", "#f59e0b", "#22c55e", "#3b82f6", "#8b5cf6"],
                    },
                },
                {
                    "type": "chart",
                    "title": f"{cls_name} {subj_name} 學生平均排名",
                    "payload": {
                        "chart_type": "bar",
                        "x_key": "name",
                        "y_key": "avg",
                        "data": [
                            {"name": row[1], "avg": row[2]}
                            for row in final_rows
                        ],
                        "x_label": "學生",
                        "y_label": "平均分",
                    },
                },
            ],
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return f"分析平時成績（{params.get('grade_type', '全部類型')}）"
