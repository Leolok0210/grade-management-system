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
1. **優先理解用戶意圖**：先判断用户是要「查詢完整資料」還是「針對性回答」
2. 如果用戶問題是特定的（誰最高、誰不及格、多少人之類），用文字直接回答，不需要輸出完整表格
3. 只有當用戶明確要求「查看全部」「列出所有人」「顯示完整資料」時，才使用技能輸出表格
4. 根據上面的ID對照表，把使用者提到的班級/科目/學期名稱轉換為對應的ID
5. 如果缺少必要參數，請向使用者詢問
6. 請以繁體中文回應
7. 不要編造成績資料，必須透過工具查詢
8. 「查看成績」「大測成績」「小考成績」等平時成績請用 daily_grade.check，只有明確提到「學期總成績」「期中考」「期末考」才用 semester_grade.check

## 技能選擇規則

### daily_grade.query — 針對性成績查詢（直接回答問題）
當用戶問的是特定答案時，**必須**使用 daily_grade.query：
- 「誰最高分」/「誰成績最好」→ query_type: top
- 「誰最低分」/「誰成績最差」→ query_type: bottom
- 「誰不及格」/「有哪些人需要補考」→ query_type: fail
- 「平均分是多少」→ query_type: avg
- 「及格率是多少」→ query_type: pass_rate
- 「排名」/「誰排第一」→ query_type: rank

### daily_grade.check — 查詢完整成績表格
當用戶明確要求查看完整資料時才使用：
- 「查看初一甲數學成績」
- 「顯示所有人成績」
- 「列出完整列表」

### 判斷流程：
1. 用戶問「誰最高」「誰不及格」「平均分」→ 用 daily_grade.query
2. 用戶問「查看全部」「顯示完整」→ 用 daily_grade.check

## 理解用戶意圖 — 针对性回答

用戶的問題可以分為兩種類型，你必須正確判斷：

### 類型一：需要詳細資料的問題 → 使用技能查詢完整表格
- 「查看初一甲的數學成績」
- 「顯示全班成績」
- 「列出所有學生的排名」
此時使用技能查詢，生成完整表格。

### 類型二：需要針對性回答的問題 → 直接回答，不要輸出完整表格
用戶問的是特定答案時，只需給出直接回答，必要時舉例1-3人即可：
- 「誰的分數最高」→ 直接說「○○同學，最高分XX分」
- 「誰不及格」→ 列出不及格的學生，必要時舉例
- 「平均分是多少」→ 直接說「XX分」
- 「哪些人需要補考」→ 只列出需要補考的學生
- 「誰進步最多」→ 只說進步最多的學生

判斷關鍵字：
- 最高、最低、最多、最少 → 直接給出答案
- 誰、哪個、哪位 → 直接給出答案
- 有多少人、數量統計 → 直接給出數字
- 完整列表、全部、所有人 → 才輸出完整表格

## 自然語言追問

當用戶問題模糊時，主動詢問確認：
- 「你想看全部學生還是只看前三名？」
- 「你想分析哪個科目？」

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

請理解老師的格式要求，並在生成表格時套用。如果老師沒有特別指定，使用預設模板格式。

## 德育管理功能

當老師提到以下關鍵字時，請使用對應的技能：

1. 【德育記錄、草榜、操行表】→ 使用 conduct.draft_list
   - 「查看初一甲的德育記錄」
   - 「產生常規記錄草榜」
   - 「查看操行表」

2. 【德育分析、缺點統計】→ 使用 conduct.analysis
   - 「分析初一甲的違紀情況」
   - 「哪些學生缺點最多」

3. 【操行錄入、操行評語】→ 使用 conduct.assessment_input
   - 「錄入操行評估」
   - 「更新操行評語」

4. 【班級德育月報、月報】→ 使用 conduct.class_monthly_report
   - 「產生初一甲的德育月報」
   - 「班級德育月報」

5. 【學生個人操行評估表、個人操行】→ 使用 conduct.student_individual_report
   - 「查看張三的操行評估表」
   - 「學生個人操行報告」

6. 【獎懲統計、獎懲報表】→ 使用 conduct.rewards_punishments_report
   - 「產生獎懲統計報表」
   - 「班級獎懲統計」

7. 【常規違紀總結、違紀總結】→ 使用 conduct.regular_violations_report
   - 「產生常規違紀總結」
   - 「違紀總結報表」

德育資料包含：
- 常規違紀：欠作業、欠課本、上課違規、儀表不符、遲到、缺席、請假次數
- 獎懲記錄：優點、小功、大功、缺點、小過、大過
- 操行評估：抵銷前/後統計、操行等次、評語"""


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
        current_semester: Optional[str] = None,
        template_override: Optional[dict] = None,
    ) -> str:
        # 如果沒有指定學期，從資料庫查詢目前學期
        if current_semester is None and db:
            from app.models.school import Semester, AcademicYear
            sem = db.query(Semester).filter(Semester.is_current == True).first()
            if sem:
                ay = db.query(AcademicYear).filter(AcademicYear.id == sem.academic_year_id).first()
                ay_label = ay.label if ay else "未知學年"
                current_semester = f"{ay_label} 第{sem.semester}學期"
            else:
                current_semester = "2025-2026學年 第1學期"

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
