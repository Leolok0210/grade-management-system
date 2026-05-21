"""
Agent Orchestrator - 意圖識別 → 技能調度 → 回應生成（串流版）
"""

import json
import logging
from typing import Union, AsyncIterator, Optional
from dataclasses import dataclass
from app.ai.router import MultiModelRouter
from app.skills.registry import get_skill, get_tool_definitions_for_role
from app.skills.base import SkillResult, UserContext
from app.models.table_format import TableFormatTemplate

logger = logging.getLogger(__name__)


SYSTEM_PROMPT_TEMPLATE = """你是氹仔坊眾學校的成績管理AI助手。使用者是學校老師和教職員。

目前學期：{current_semester}
使用者：{user_name}（{user_role}）

{context_info}

{table_format_info}

重要規則：
1. 當使用者的請求匹配某個技能時，你必須調用對應的 function，不要只用文字回覆
2. 根據上面的ID對照表，把使用者提到的班級/科目/學期名稱轉換為對應的ID
3. 如果缺少必要參數，請向使用者詢問
4. 請以繁體中文回應
5. 不要編造成績資料，必須透過工具查詢
6. 「查看成績」「大測成績」「小考成績」等平時成績請用 daily_grade.check，只有明確提到「學期總成績」「期中考」「期末考」才用 semester_grade.check

## 表格輸出格式要求

當需要輸出成績表格時，請務必包含以下格式：

1. 【欄位結構】：科目、測驗名稱、測驗日期、負責老師、不及格率
2. 【不及格率計算】：不及格人數 / 總人數 * 100%，顯示為百分比（保留兩位小數）
3. 【不及格標準】：分數低於 60.0 分視為「不及格」
4. 【不及格次數統計】：橫向統計該名學生在所有顯示的測驗項目中，有幾次低於 60 分

5. 【視覺標記格式】：
   - 不及格分數（< 60）的儲存格：加上淺紅色背景 <span style="background-color:#ffcccc;">分數</span>
   - 不及格次數（> 0）的儲存格：加深紅色背景，數字加粗斜體 <span style="background-color:#ff9999;"><b><i>次數</i></b></span>
   - 及格次數為 0 的儲存格：保持空白或顯示 0

6. 【學生資料列格式】：學生編號 | 班級 | 姓名 | 學號 | 各科分數... | 不及格次數

7. 【表格抬頭欄位順序】：第一欄為學生識別（學號、班級、姓名），其後依序為各科目/測驗，最後一欄為不及格測驗次數

example output structure:
| 科目 | 中文讀本 | 中文讀本 | 數學 | ... | 不及格 |
| 測驗名稱 | 大測1 | 大測2 | 大測1 | ... | |
| 測驗日期 | 2026-03-09 | 2026-03-30 | 2026-03-05 | ... | |
| 負責老師 | 黃渝丹 | 黃渝丹 | 郭彥俊 | ... | |
| 不及格率 | 25.00% | 21.43% | 32.14% | ... | 次數 |

## 自然語言格式調整

老師可以用自然語言要求調整格式，例如：
- 「不及格用藍色標記」
- 「加入排名欄位」
- 「顯示各科平均分」
- 「不及格率用紅字」

請理解老師的格式要求，並在生成表格時套用。如果老師沒有特別指定，使用預設模板格式。"""


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


def _build_table_format_info(db) -> str:
    """取得可用的表格格式模板"""
    templates = TableFormatTemplate.get_all_active(db)
    if not templates:
        return ""

    lines = ["\n可用表格格式模板："]
    for t in templates:
        style_info = ""
        if t.style_config:
            if t.style_config.get("fail_score_bg"):
                style_info = f" [不及格標記:{t.style_config['fail_score_bg']}]"
            if t.style_config.get("fail_count_bg"):
                style_info += f" [不及格次數:{t.style_config['fail_count_bg']}]"

        default_mark = " (預設)" if t.is_default else ""
        lines.append(f"  - {t.name}{default_mark}：{t.description or ''}{style_info}")

    return "\n".join(lines)


class AgentOrchestrator:
    def __init__(self, ai_router: MultiModelRouter):
        self.ai_router = ai_router

    def _build_system_prompt(
        self,
        context: UserContext,
        db,
        current_semester: str = "2025-2026學年 第2學期",
        template_override: Optional[dict] = None,
    ) -> str:
        context_info = _build_context_info(db) if db else ""
        table_format_info = _build_table_format_info(db) if db else ""

        prompt = SYSTEM_PROMPT_TEMPLATE.format(
            current_semester=current_semester,
            user_name=context.name,
            user_role=context.role,
            context_info=context_info,
            table_format_info=table_format_info,
        )

        # 如果有 template override，附加到 prompt
        if template_override:
            prompt += f"\n\n## 目前使用格式模板：{template_override.get('name', '自訂')}\n"
            prompt += json.dumps(template_override.get("style_config", {}), ensure_ascii=False, indent=2)

        return prompt

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
        logger.info(f"AI response: finish={response.finish_reason}, tool_call={response.tool_call_name}, content={str(response.content)[:200] if response.content else None}")

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
