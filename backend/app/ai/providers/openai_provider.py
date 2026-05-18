"""
OpenAI Provider 實作
"""

from typing import AsyncIterator
from openai import AsyncOpenAI
from app.ai.provider import AIProvider, AIResponse, StreamChunk
from app.config import settings


class OpenAIProvider(AIProvider):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._models = ["gpt-4o-mini", "gpt-4o"]

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
    ) -> AIResponse:
        model = model or settings.OPENAI_MODEL
        kwargs = {"model": model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        result = AIResponse(finish_reason=choice.finish_reason or "stop")

        if choice.message.tool_calls:
            tc = choice.message.tool_calls[0]
            result.tool_call_name = tc.function.name
            import json
            result.tool_call_arguments = json.loads(tc.function.arguments)
            result.content = choice.message.content
        else:
            result.content = choice.message.content

        return result

    async def chat_stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
    ) -> AsyncIterator[StreamChunk]:
        model = model or settings.OPENAI_MODEL
        kwargs = {"model": model, "messages": messages, "stream": True}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

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