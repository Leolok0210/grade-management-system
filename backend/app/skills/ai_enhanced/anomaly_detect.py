"""
成績異常偵測技能
偵測成績異常波動，如突然大幅下降、統計異常值等
"""
from datetime import datetime
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.semester_grade import SemesterGrade
from app.models.daily_grade import DailyGrade, DailyGradeItem
from app.models.anomaly import GradeAnomaly
from app.models.student import Student
from app.models.subject import ClassSubject, Subject
from app.models.student import Class


class AnomalyDetect(BaseSkill):
    name = "ai.anomaly_detect"
    description = "偵測成績異常，包含突然大幅下降、統計異常值等，主動提醒教師關注"
    parameters = {
        "type": "object",
        "properties": {
            "class_id": {"type": "integer", "description": "班級ID"},
            "semester_id": {"type": "integer", "description": "學期ID"},
            "threshold": {"type": "number", "description": "下降幅度閾值（分），預設30"},
        },
        "required": ["class_id", "semester_id"],
    }
    required_role = "dept_head"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        class_id = params["class_id"]
        semester_id = params["semester_id"]
        threshold = params.get("threshold", 30)

        students = db.query(Student).filter(Student.class_id == class_id).all()
        anomalies = []

        for student in students:
            # 取得平時成績
            daily_grades = db.query(DailyGrade).join(DailyGradeItem).filter(
                DailyGradeItem.class_subject_id.in_(
                    db.query(ClassSubject.id).filter(
                        ClassSubject.class_id == class_id,
                        ClassSubject.semester_id == semester_id,
                    )
                ),
                DailyGrade.student_id == student.id,
            ).order_by(DailyGradeItem.date).all()

            if len(daily_grades) < 2:
                continue

            # 偵測突然下降
            scores = [float(g.score) for g in daily_grades]
            for i in range(1, len(scores)):
                drop = scores[i - 1] - scores[i]
                if drop >= threshold:
                    anomaly = GradeAnomaly(
                        student_id=student.id,
                        class_subject_id=daily_grades[i].item.class_subject_id,
                        semester_id=semester_id,
                        anomaly_type="sudden_drop",
                        severity="high" if drop >= 40 else "medium" if drop >= 30 else "low",
                        description=f"{student.name} 成績從 {scores[i-1]} 下降至 {scores[i]}（降幅 {drop} 分）",
                    )
                    db.add(anomaly)
                    anomalies.append([student.name, scores[i-1], scores[i], f"-{drop}", "突然下降"])

            # 偵測統計異常值（低於平均2個標準差）
            if len(scores) >= 3:
                avg = sum(scores) / len(scores)
                std = (sum((s - avg) ** 2 for s in scores) / len(scores)) ** 0.5
                for score in scores:
                    if std > 0 and (avg - score) / std > 2:
                        anomaly = GradeAnomaly(
                            student_id=student.id,
                            class_subject_id=daily_grades[0].item.class_subject_id,
                            semester_id=semester_id,
                            anomaly_type="statistical_outlier",
                            severity="medium",
                            description=f"{student.name} 成績 {score} 低於平均 {round(avg,1)} 超過2個標準差",
                        )
                        db.add(anomaly)
                        anomalies.append([student.name, score, round(avg, 1), f"-{round(2*std, 1)}", "統計異常"])

        db.commit()

        if not anomalies:
            return SkillResult(success=True, message="未偵測到成績異常")

        return SkillResult(
            success=True,
            message=f"偵測到 {len(anomalies)} 筆成績異常",
            data={"anomaly_count": len(anomalies)},
            data_card={
                "type": "table",
                "title": "成績異常偵測結果",
                "payload": {
                    "columns": ["學生", "原分數", "異常分數", "變化", "類型"],
                    "rows": anomalies,
                },
            },
        )

    def preview(self, params: dict, context: UserContext) -> str:
        return "偵測成績異常"