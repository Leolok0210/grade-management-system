"""
歷史趨勢分析技能
跨學期/跨年級成績趨勢視覺化
"""
from app.skills.base import BaseSkill, SkillResult, UserContext
from app.models.semester_grade import SemesterGrade
from app.models.school import Semester, AcademicYear
from app.models.student import Student, Class
from app.models.subject import ClassSubject, Subject


class TrendAnalysis(BaseSkill):
    name = "ai.trend_analysis"
    description = "分析學生或班級的歷史成績趨勢，跨學期比較變化"
    parameters = {
        "type": "object",
        "properties": {
            "student_id": {"type": "string", "description": "學生ID（分析單一學生趨勢）"},
            "class_id": {"type": "string", "description": "班級ID（分析班級趨勢）"},
            "subject_id": {"type": "string", "description": "科目ID"},
        },
        "required": [],
    }
    required_role = "teacher"

    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        student_id = params.get("student_id")
        class_id = params.get("class_id")
        subject_id = params.get("subject_id")

        if student_id:
            # 單一學生趨勢
            student = db.query(Student).filter(Student.id == student_id).first()
            grades = db.query(SemesterGrade).filter(
                SemesterGrade.student_id == student_id,
                SemesterGrade.semester_score.isnot(None),
            ).all()

            rows = []
            for g in grades:
                cs = db.query(ClassSubject).filter(ClassSubject.id == g.class_subject_id).first()
                subject = db.query(Subject).filter(Subject.id == cs.subject_id).first() if cs else None
                semester = db.query(Semester).filter(Semester.id == g.semester_id).first() if cs else None
                ay = db.query(AcademicYear).filter(AcademicYear.id == semester.academic_year_id).first() if semester else None
                label = f"{ay.label}第{semester.semester}學期" if ay and semester else g.semester_id
                rows.append([label, subject.name if subject else "-", float(g.semester_score)])

            return SkillResult(
                success=True,
                message=f"{student.name if student else ''} 成績趨勢分析",
                data_card={
                    "type": "table",
                    "title": f"{student.name if student else ''} 成績趨勢",
                    "payload": {
                        "columns": ["學期", "科目", "分數"],
                        "rows": rows,
                    },
                },
            )

        elif class_id:
            # 班級趨勢
            semesters = db.query(Semester).join(AcademicYear).filter(
                AcademicYear.school_id == context.school_id,
            ).order_by(Semester.semester).all()

            rows = []
            for sem in semesters:
                cs_list = db.query(ClassSubject).filter(
                    ClassSubject.class_id == class_id,
                    ClassSubject.semester_id == sem.id,
                ).all()

                for cs in cs_list:
                    if subject_id and cs.subject_id != subject_id:
                        continue
                    subject = db.query(Subject).filter(Subject.id == cs.subject_id).first()
                    grades = db.query(SemesterGrade).filter(
                        SemesterGrade.class_subject_id == cs.id,
                        SemesterGrade.semester_id == sem.id,
                        SemesterGrade.semester_score.isnot(None),
                    ).all()
                    avg = round(sum(float(g.semester_score) for g in grades) / len(grades), 2) if grades else 0
                    ay = db.query(AcademicYear).filter(AcademicYear.id == sem.academic_year_id).first()
                    label = f"{ay.label}第{sem.semester}學期" if ay else sem.id
                    rows.append([label, subject.name if subject else "-", avg, len(grades)])

            return SkillResult(
                success=True,
                message="班級成績趨勢分析",
                data_card={
                    "type": "table",
                    "title": "班級成績趨勢",
                    "payload": {
                        "columns": ["學期", "科目", "平均分數", "人數"],
                        "rows": rows,
                    },
                },
            )

        return SkillResult(success=False, message="請指定學生ID或班級ID")

    def preview(self, params: dict, context: UserContext) -> str:
        return "分析成績趨勢"