"""
成績異常偵測技能
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.daily_grade import DailyGradeItem, DailyGrade
from app.models.student import Student
from app.models.subject import ClassSubject, Subject
from app.models.student import Class


class AnomalyDetect(BaseSkill):
    name = "ai.anomaly_detect"
    description = "偵測成績異常的學生，包含分數驟降、異常偏高/偏低（超過2個標準差）。當使用者提到異常、異常偵測、成績有問題時使用"
    parameters = {
        "type": "object",
        "properties": {
            "class_subject_id": {"type": "integer", "description": "班級科目ID"},
            "grade_type": {"type": "string", "description": "成績類型篩選（可選）"},
            "threshold": {"type": "number", "description": "標準差倍數閾值，預設2.0"},
        },
        "required": ["class_subject_id"],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        class_subject_id = params["class_subject_id"]
        threshold = params.get("threshold", 2.0)

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
            return SkillResult(success=True, message="查無成績記錄")

        all_scores = [float(g.score) for g in grades]
        mean = sum(all_scores) / len(all_scores)
        variance = sum((s - mean) ** 2 for s in all_scores) / len(all_scores)
        std_dev = variance ** 0.5

        if std_dev == 0:
            return SkillResult(success=True, message="所有學生分數相同，無異常")

        student_scores = {}
        for g in grades:
            student_scores.setdefault(g.student_id, []).append(float(g.score))

        anomalies = []
        for sid, scores in student_scores.items():
            student = db.query(Student).filter(Student.id == sid).first()
            avg = sum(scores) / len(scores)
            z_score = (avg - mean) / std_dev

            if abs(z_score) > threshold:
                direction = "異常偏高" if z_score > 0 else "異常偏低"
                anomalies.append([student.name if student else str(sid), round(avg, 1), round(z_score, 2), direction, len(scores)])

        sudden_drops = []
        for sid, scores in student_scores.items():
            if len(scores) < 2:
                continue
            student = db.query(Student).filter(Student.id == sid).first()
            sorted_scores = sorted(scores)
            for i in range(len(sorted_scores) - 1):
                drop = sorted_scores[i] - sorted_scores[i + 1]
                if drop > 30:
                    sudden_drops.append([student.name if student else str(sid), sorted_scores[i], sorted_scores[i + 1], f"-{drop}"])

        msg_parts = []
        if anomalies:
            msg_parts.append(f"偵測到 {len(anomalies)} 名異常學生（超過 {threshold} 個標準差）")
        if sudden_drops:
            msg_parts.append(f"{len(sudden_drops)} 筆分數驟降（差距超過30分）")
        if not msg_parts:
            return SkillResult(success=True, message=f"{cls_name} {subj_name} 成績無異常（全班平均 {round(mean,1)}，標準差 {round(std_dev,1)}）")

        all_rows = anomalies
        if sudden_drops:
            all_rows.append(["---", "---", "---", "分數驟降", "---"])
            all_rows.extend(sudden_drops)

        return SkillResult(
            success=True,
            message=f"{cls_name} {subj_name}：{', '.join(msg_parts)}（全班平均 {round(mean,1)}，標準差 {round(std_dev,1)}）",
            data={"anomalies": len(anomalies), "sudden_drops": len(sudden_drops)},
            data_card={
                "type": "table",
                "title": f"{cls_name} {subj_name} 成績異常偵測",
                "payload": {
                    "columns": ["學生", "平均分", "Z分數", "異常類型", "筆數"],
                    "rows": all_rows,
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return "偵測成績異常"
