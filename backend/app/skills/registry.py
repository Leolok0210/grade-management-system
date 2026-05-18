from typing import Optional

from app.skills.base import BaseSkill, SkillResult, UserContext  # noqa: F401

_skill_registry: dict[str, BaseSkill] = {}


def register_skill(skill: BaseSkill):
    _skill_registry[skill.name] = skill


def get_skill(name: str) -> Optional[BaseSkill]:
    return _skill_registry.get(name)


def get_all_skills() -> list[BaseSkill]:
    return list(_skill_registry.values())


def get_skills_for_role(role: str) -> list[BaseSkill]:
    return [s for s in get_all_skills() if s.is_available_for_role(role)]


def get_tool_definitions_for_role(role: str) -> list[dict]:
    return [s.get_tool_definition() for s in get_skills_for_role(role)]