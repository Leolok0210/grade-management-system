"""
Agent Orchestrator - 意圖識別 → 技能調度 → 回應生成
"""

import json
from typing import Union
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


def _build_context_info(db) -> str:
    """從資料庫讀取班級、科目、學期的 ID 對照表"""
    from app.models.student import Class
    from app.models.subject import Subject, ClassSubject
    from app.models.school import Semester
    from sqlalchemy import text

    lines = ["ID 對照表："]

    # 班級
    classes = db.query(Class).all()
    if classes:
        lines.append("班級：")
        for c in classes:
            lines.append(f"  - {c.name} → class_id={c.id}")

    # 科目
    subjects = db.query(Subject).all()
    if subjects:
        lines.append("科目：")
        for s in subjects:
            lines.append(f"  - {s.name} → subject_id={s.id}")

    # 學期
    semesters = db.query(Semester).all()
    if semesters:
        lines.append("學期：")
        for sem in semesters:
            label = f"第{sem.semester}學期"
            lines.append(f"  - {label} → semester_id={sem.id}")

    # 班級科目
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
        """處理使用者訊息，返回技能執行結果或自然語言回應"""

        tools = get_tool_definitions_for_role(context.role)
        system_prompt = self._build_system_prompt(context, db)

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
        system_prompt = self._build_system_prompt(context, None)

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        async for chunk in self.ai_router.chat_stream(messages=messages, tools=tools):
            yield chunk