"""
Skill Registry - 技能註冊中心
"""
from app.skills.base import BaseSkill
from app.skills.daily_grade.check import DailyGradeCheck
from app.skills.daily_grade.register import DailyGradeRegister
from app.skills.daily_grade.analyze import DailyGradeAnalyze
from app.skills.daily_grade.report import DailyGradeReport
from app.skills.semester_grade.register import SemesterGradeRegister
from app.skills.semester_grade.check import SemesterGradeCheck
from app.skills.semester_grade.draft_list import DraftList
from app.skills.system.import_excel import ImportExcel
from app.skills.system.export_excel import ExportExcel
from app.skills.transcript.generate import TranscriptGenerate
from app.skills.ai_enhanced.anomaly_detect import AnomalyDetect
from app.skills.ai_enhanced.class_comparison import ClassComparison
from app.skills.ai_enhanced.makeup_suggestion import MakeupSuggestion

_skills: dict[str, BaseSkill] = {}


def _register(skill: BaseSkill):
    _skills[skill.name] = skill


# 註冊所有技能
_register(DailyGradeCheck())
_register(DailyGradeRegister())
_register(DailyGradeAnalyze())
_register(DailyGradeReport())
_register(SemesterGradeRegister())
_register(SemesterGradeCheck())
_register(DraftList())
_register(ImportExcel())
_register(ExportExcel())
_register(TranscriptGenerate())
_register(AnomalyDetect())
_register(ClassComparison())
_register(MakeupSuggestion())


def get_skill(name: str) -> BaseSkill | None:
    return _skills.get(name)


def get_all_skills() -> list[BaseSkill]:
    return list(_skills.values())


def get_tool_definitions_for_role(role: str) -> list[dict]:
    """取得指定角色可用的工具定義（OpenAI function calling 格式）"""
    tools = []
    for skill in _skills.values():
        if skill.is_available_for_role(role):
            tools.append({
                "type": "function",
                "function": {
                    "name": skill.name,
                    "description": skill.description,
                    "parameters": skill.parameters,
                },
            })
    return tools