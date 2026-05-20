"""
Agent Orchestrator - 意圖識別 → 技能調度 → 回應生成（串流版）
"""

import json
from typing import Union, AsyncIterator
from dataclasses import dataclass
from app.ai.router import MultiModelRouter
from app.skills.registry import get_skill, get_tool_definitions_for_role
from app.skills.base import SkillResult, UserContext


SYSTEM_PROMPT_TEMPLATE = """你是氹仔坊眾學校的成績管理AI助手。使用者是學校老師和教職員。

目前學期：{current_semester}
使用者：{user_name}（{user_role}）

{context_info}

重要規則：
1. 當使用者的請求匹配某個技能時，你必須調用對應的 function，不要只用文字回覆
2. 根據上面的ID對照表，把使用者提到的班級/科目/學期名稱轉換為對應的ID
3. 如果缺少必要參數，請向使用者詢問
4. 請以繁體中文回應
5. 不要編造成績資料，必須透過工具查詢
6. 「查看成績」「大測成績」「小考成績」等平時成績請用 daily_grade.check，只有明確提到「學期總成績」「期中考」「期末考」才用 semester_grade.check"""


@dataclass
class StreamEvent:
    """串流事件 — 統一的事件格式"""
    type: str  # status | data_card | content | done
    data: dict = None

    def to_sse(self) -> str:
        return f"data: {json.dumps({'type': self.type, **(self.data or {})}, ensure_ascii=False)}\n\n"


def _build_context_info(db) -> str:
    """從資料庫讀取班級、科目、學期的 ID 對照表"""
    from app.models.student import Class
    from app.models.subject import Subject, ClassSubject
    from app.models.school import Semester

    lines = ["ID 對照表："]

    classes = db.query(Class).all()
    if classes:
        lines.append("班級：")
        for c in classes:
            lines.append(f"  - {c.name} → class_id={c.id}")

    subjects = db.query(Subject).all()
    if subjects:
        lines.append("科目：")
        for s in subjects:
            lines.append(f"  - {s.name} → subject_id={s.id}")

    semesters = db.query(Semester).all()
    if semesters:
        lines.append("學期：")
        for sem in semesters:
            label = f"第{sem.semester}學期"
            lines.append(f"  - {label} → semester_id={sem.id}")

    class_subjects = db.query(ClassSubject).all()
    if class_subjects:
        lines.append("班級科目（class_subject_id）：")
        for cs in class_subjects:
            cls = db.query(Class).filter(Class.id == cs.class_id).first()
            subj = db.query(Subject).filter(Subject.id == cs.subject_id).first()
            cls_name = cls.name if cls else "?"
            subj_name = subj.name if subj else "?"
            lines.append(f"  - {cls_name} {subj_name} → class_subject_id={cs.id}")

    return "\n".join(lines)


class AgentOrchestrator:
    def __init__(self, ai_router: MultiModelRouter):
        self.ai_router = ai_router

    def _build_system_prompt(self, context: UserContext, db, current_semester: str = "2025-2026學年 第2學期") -> str:
        context_info = _build_context_info(db) if db else ""
        return SYSTEM_PROMPT_TEMPLATE.format(
            current_semester=current_semester,
            user_name=context.name,
            user_role=context.role,
            context_info=context_info,
        )

    async def handle_message(
        self,
        user_message: str,
        conversation_history: list[dict],
        context: UserContext,
        db,
    ) -> Union[SkillResult, str]:
        """處理使用者訊息，返回技能執行結果或自然語言回應（非串流版）"""

        tools = get_tool_definitions_for_role(context.role)
        system_prompt = self._build_system_prompt(context, db)

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        response = await self.ai_router.chat(messages=messages, tools=tools)

        if response.tool_call_name:
            skill = get_skill(response.tool_call_name)
            if skill:
                params = response.tool_call_arguments or {}
                if not skill.is_available_for_role(context.role):
                    return SkillResult(
                        success=False,
                        message=f"權限不足，無法執行「{skill.description}」",
                    )
                return await skill.execute(params, context, db)

        return response.content or "抱歉，我無法理解您的請求。請再描述一次。"

    async def handle_message_stream(
        self,
        user_message: str,
        conversation_history: list[dict],
        context: UserContext,
        db,
    ) -> AsyncIterator[StreamEvent]:
        """串流處理使用者訊息，yield 結構化事件"""

        tools = get_tool_definitions_for_role(context.role)
        system_prompt = self._build_system_prompt(context, db)

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        # Step 1: AI 意圖識別
        yield StreamEvent(type="status", data={"message": "正在理解您的需求..."})

        response = await self.ai_router.chat(messages=messages, tools=tools)

        # Step 2: 有技能調用 → 執行技能
        if response.tool_call_name:
            skill = get_skill(response.tool_call_name)
            if not skill:
                yield StreamEvent(type="content", data={"text": "抱歉，找不到對應的功能。"})
                yield StreamEvent(type="done")
                return

            if not skill.is_available_for_role(context.role):
                yield StreamEvent(type="content", data={"text": "權限不足，無法執行此功能。"})
                yield StreamEvent(type="done")
                return

            params = response.tool_call_arguments or {}
            yield StreamEvent(type="status", data={"message": f"正在執行：{skill.preview(params, context)}"})

            result = await skill.execute(params, context, db)

            # 先推送 data_card（如果有）
            if result.data_card:
                yield StreamEvent(type="data_card", data={"card": result.data_card})
            if result.data_cards:
                for card in result.data_cards:
                    yield StreamEvent(type="data_card", data={"card": card})

            # 推送技能結果的靜態部分
            if result.message:
                # 檢查是否需要 AI 串流分析（analyze 技能）
                if result.message.startswith("__STREAM__"):
                    # 技能要求後續 AI 串流分析
                    static_part = result.message[len("__STREAM__"):]
                    if static_part:
                        yield StreamEvent(type="content", data={"text": static_part})

                    # 取得 AI 分析 prompt（技能存在 data 裡）
                    ai_prompt = result.data.get("_ai_prompt", "") if result.data else ""
                    if ai_prompt:
                        yield StreamEvent(type="status", data={"message": "AI 正在進行深度分析..."})
                        async for chunk in self.ai_router.chat_stream(
                            messages=[{"role": "user", "content": ai_prompt}],
                        ):
                            if chunk.content:
                                yield StreamEvent(type="content", data={"text": chunk.content})
                else:
                    # 一般技能結果，直接推送
                    yield StreamEvent(type="content", data={"text": result.message})

            yield StreamEvent(type="done")
            return

        # Step 3: 純對話 → 串流推送 AI 回應
        async for chunk in self.ai_router.chat_stream(messages=messages, tools=None):
            if chunk.content:
                yield StreamEvent(type="content", data={"text": chunk.content})

        yield StreamEvent(type="done")
