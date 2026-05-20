from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel


class SkillResult(BaseModel):
    success: bool
    message: str
    data: Any = None
    data_card: Optional[dict] = None  # type: table/chart/form/transcript
    data_cards: Optional[list[dict]] = None  # multiple cards


class UserContext(BaseModel):
    user_id: int
    name: str
    role: str
    school_id: int

    model_config = {"from_attributes": True}


class BaseSkill(ABC):
    name: str
    description: str
    parameters: dict  # JSON Schema
    required_role: str  # admin / dept_head / teacher

    @abstractmethod
    async def execute(self, params: dict, context: UserContext, db) -> SkillResult:
        ...

    @abstractmethod
    def preview(self, params: dict, context: UserContext) -> str:
        """執行前預覽描述，讓老師確認"""
        ...

    def get_tool_definition(self) -> dict:
        """轉換為 AI function calling tool 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def is_available_for_role(self, role: str) -> bool:
        role_hierarchy = {"teacher": 0, "dept_head": 1, "admin": 2}
        return role_hierarchy.get(role, -1) >= role_hierarchy.get(self.required_role, 99)