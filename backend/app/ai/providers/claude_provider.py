"""
Claude Provider 實作
"""

import json
from typing import AsyncIterator
from anthropic import AsyncAnthropic
from app.ai.provider import AIProvider, AIResponse, StreamChunk
from app.config import settings


class ClaudeProvider(AIProvider):
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self._models = ["claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"]

    def _convert_tools(self, tools: list[dict]) -> list[dict]:
        """將 OpenAI function calling 格式轉為 Claude tool_use 格式"""
        claude_tools = []
        for t in tools:
            func = t.get("function", {})
            claude_tools.append({
                "name": func["name"],
                "description": func.get("description", ""),
                "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
            })
        return claude_tools

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
    ) -> AIResponse:
        model = model or settings.ANTHROPIC_MODEL
        kwargs = {"model": model, "messages": messages, "max_tokens": 4096}
        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        response = await self.client.messages.create(**kwargs)
        result = AIResponse()

        for block in response.content:
            if block.type == "text":
                result.content = block.text
            elif block.type == "tool_use":
                result.tool_call_name = block.name
                result.tool_call_arguments = block.input

        if response.stop_reason == "tool_use":
            result.finish_reason = "tool_calls"
        else:
            result.finish_reason = "stop"

        return result

    async def chat_stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
    ) -> AsyncIterator[StreamChunk]:
        model = model or settings.ANTHROPIC_MODEL
        kwargs = {"model": model, "messages": messages, "max_tokens": 4096}
        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        async with self.client.messages.stream(**kwargs) as stream:
            async for event in stream:
                if event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        yield StreamChunk(content=event.delta.text)
                    elif event.delta.type == "input_json_delta":
                        yield StreamChunk(tool_call_arguments_delta=event.delta.partial_json)
                elif event.type == "message_stop":
                    yield StreamChunk(finish_reason="stop")

    def available_models(self) -> list[str]:
        return self._models

    async def health_check(self) -> bool:
        try:
            await self.client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1,
            )
            return True
        except Exception:
            return False