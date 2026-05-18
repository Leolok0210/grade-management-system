"""
Agent Orchestrator - 意圖識別 → 技能調度 → 回應生成
"""

import json
from app.ai.router import MultiModelRouter
from app.skills.registry import get_skill, get_tool_definitions_for_role
from app.skills.base import SkillResult, UserContext


SYSTEM_PROMPT_TEMPLATE = """你是一個國中成績管理系統的AI助手。你的任務是分析使用者的輸入，
判斷他們想要執行哪個功能（技能），並提取相關參數。

可用技能列表：
{skills_description}

目前學期：{current_semester}
使用者身份：{user_name}（{user_role}）

請以繁體中文回應。如果使用者請求匹配某個技能，請調用對應的 function。
如果無法匹配任何技能，請用自然語言回覆使用者。
如果缺少必要參數，請向使用者詢問。"""


class AgentOrchestrator:
    def __init__(self, ai_router: MultiModelRouter):
        self.ai_router = ai_router

    def _build_system_prompt(self, context: UserContext, current_semester: str = "114學年度上學期") -> str:
        skills = get_tool_definitions_for_role(context.role)
        skills_desc = "\n".join(
            f"- {t['function']['name']}: {t['function']['description']}"
            for t in skills
        )
        return SYSTEM_PROMPT_TEMPLATE.format(
            skills_description=skills_desc,
            current_semester=current_semester,
            user_name=context.name,
            user_role=context.role,
        )

    async def handle_message(
        self,
        user_message: str,
        conversation_history: list[dict],
        context: UserContext,
        db,
    ) -> SkillResult | str:
        """處理使用者訊息，返回技能執行結果或自然語言回應"""

        tools = get_tool_definitions_for_role(context.role)
        system_prompt = self._build_system_prompt(context)

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        # 呼叫 AI 識別意圖
        response = await self.ai_router.chat(messages=messages, tools=tools)

        # 有技能調用
        if response.tool_call_name:
            skill = get_skill(response.tool_call_name)
            if skill:
                params = response.tool_call_arguments or {}
                # 檢查權限
                if not skill.is_available_for_role(context.role):
                    return SkillResult(
                        success=False,
                        message=f"權限不足，無法執行「{skill.description}」",
                    )
                # 執行技能
                return await skill.execute(params, context, db)

        # 純對話回應
        return response.content or "抱歉，我無法理解您的請求。請再描述一次。"

    async def handle_message_stream(
        self,
        user_message: str,
        conversation_history: list[dict],
        context: UserContext,
    ):
        """串流回應版本（用於 SSE）"""
        tools = get_tool_definitions_for_role(context.role)
        system_prompt = self._build_system_prompt(context)

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        async for chunk in self.ai_router.chat_stream(messages=messages, tools=tools):
            yield chunk