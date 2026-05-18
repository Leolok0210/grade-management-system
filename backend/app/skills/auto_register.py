"""
技能自動註冊 - 啟動時載入所有技能到 Registry
"""
from app.skills.registry import register_skill
from app.skills.daily_grade.register import DailyGradeRegister
from app.skills.daily_grade.check import DailyGradeCheck
from app.skills.daily_grade.analyze import DailyGradeAnalyze
from app.skills.daily_grade.report import DailyGradeReport
from app.skills.semester_grade.register import SemesterGradeRegister
from app.skills.semester_grade.check import SemesterGradeCheck
from app.skills.semester_grade.analyze import SemesterGradeAnalyze
from app.skills.semester_grade.makeup import MakeupExamRegister
from app.skills.semester_grade.draft_list import GradeDraftGenerate
from app.skills.semester_grade.passing_line import PassingLineSet
from app.skills.semester_grade.award import AwardGrant
from app.skills.transcript.generate import TranscriptGenerate
from app.skills.transcript.batch_generate import TranscriptBatchGenerate
from app.skills.grade_check.honor_roll import HonorRollList
from app.skills.grade_check.semester_review import SemesterReview
from app.skills.grade_check.year_review import YearReview
from app.skills.ai_enhanced.anomaly_detect import AnomalyDetect
from app.skills.ai_enhanced.trend_analysis import TrendAnalysis
from app.skills.ai_enhanced.class_comparison import ClassComparison
from app.skills.ai_enhanced.makeup_suggestion import MakeupSuggestion
from app.skills.system.import_excel import ImportExcel
from app.skills.system.export_excel import ExportExcel
from app.skills.system.notify import NotifyParents
from app.skills.system.appeal_handle import AppealHandle


def register_all_skills():
    # 平時成績
    register_skill(DailyGradeRegister())
    register_skill(DailyGradeCheck())
    register_skill(DailyGradeAnalyze())
    register_skill(DailyGradeReport())
    # 學期成績
    register_skill(SemesterGradeRegister())
    register_skill(SemesterGradeCheck())
    register_skill(SemesterGradeAnalyze())
    register_skill(MakeupExamRegister())
    register_skill(GradeDraftGenerate())
    register_skill(PassingLineSet())
    register_skill(AwardGrant())
    # 成績單
    register_skill(TranscriptGenerate())
    register_skill(TranscriptBatchGenerate())
    # 成績檢查
    register_skill(HonorRollList())
    register_skill(SemesterReview())
    register_skill(YearReview())
    # AI 增強
    register_skill(AnomalyDetect())
    register_skill(TrendAnalysis())
    register_skill(ClassComparison())
    register_skill(MakeupSuggestion())
    # 系統
    register_skill(ImportExcel())
    register_skill(ExportExcel())
    register_skill(NotifyParents())
    register_skill(AppealHandle())