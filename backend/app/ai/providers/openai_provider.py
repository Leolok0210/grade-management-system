"""
OpenAI Provider 實作
"""

from typing import AsyncIterator, Optional
from openai import AsyncOpenAI
from app.ai.provider import AIProvider, AIResponse, StreamChunk
from app.config import settings


class OpenAIProvider(AIProvider):
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )
        self._models = [settings.OPENAI_MODEL]

    async def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        model: Optional[str] = None,
    ) -> AIResponse:
        model = model or settings.OPENAI_MODEL
        kwargs = {"model": model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
            # qwen3.5-plus 不支援 tool_choice，不設定

        try:
            response = await self.client.chat.completions.create(**kwargs)
        except Exception as e:
            # 如果模型不支援 tools，退回純文字模式
            if tools and ("tool" in str(e).lower() or "function" in str(e).lower()):
                kwargs.pop("tools", None)
                response = await self.client.chat.completions.create(**kwargs)
            else:
                raise

        if not hasattr(response, "choices") or not response.choices:
            # 某些模型回傳格式不同，嘗試解析
            content = str(response) if response else ""
            return AIResponse(finish_reason="stop", content=content)

        choice = response.choices[0]

        result = AIResponse(finish_reason=choice.finish_reason or "stop")

        if choice.message.tool_calls:
            tc = choice.message.tool_calls[0]
            result.tool_call_name = tc.function.name
            import json
            try:
                result.tool_call_arguments = json.loads(tc.function.arguments)
            except (json.JSONDecodeError, TypeError):
                result.tool_call_arguments = {}
            result.content = choice.message.content
        else:
            result.content = choice.message.content

        return result

    async def chat_stream(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        model: Optional[str] = None,
    ) -> AsyncIterator[StreamChunk]:
        model = model or settings.OPENAI_MODEL
        kwargs = {"model": model, "messages": messages, "stream": True}
        if tools:
            kwargs["tools"] = tools

        stream = await self.client.chat.completions.create(**kwargs)
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta

            sc = StreamChunk(finish_reason=chunk.choices[0].finish_reason)

            if delta.content:
                sc.content = delta.content

            if delta.tool_calls:
                tc = delta.tool_calls[0]
                if tc.function:
                    if tc.function.name:
                        sc.tool_call_name = tc.function.name
                    if tc.function.arguments:
                        sc.tool_call_arguments_delta = tc.function.arguments

            yield sc

    def available_models(self) -> list[str]:
        return self._models

    async def health_check(self) -> bool:
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False