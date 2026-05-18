"""
Local Provider (Ollama) 實作
"""

import json
from typing import AsyncIterator
import httpx
from app.ai.provider import AIProvider, AIResponse, StreamChunk
from app.config import settings


class LocalProvider(AIProvider):
    def __init__(self):
        self.base_url = settings.LOCAL_MODEL_URL
        self._models = [settings.LOCAL_MODEL_NAME]

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
    ) -> AIResponse:
        model = model or settings.LOCAL_MODEL_NAME
        payload = {"model": model, "messages": messages, "stream": False, "format": "json"}
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = data.get("message", {}).get("content", "")
        result = AIResponse(content=content, finish_reason="stop")

        # Ollama tool calls are embedded in content as JSON
        if tools and content:
            try:
                parsed = json.loads(content)
                if "name" in parsed and "arguments" in parsed:
                    result.tool_call_name = parsed["name"]
                    result.tool_call_arguments = parsed["arguments"]
                    result.content = None
            except json.JSONDecodeError:
                pass

        return result

    async def chat_stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
    ) -> AsyncIterator[StreamChunk]:
        model = model or settings.LOCAL_MODEL_NAME
        payload = {"model": model, "messages": messages, "stream": True}
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as resp:
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield StreamChunk(content=content)
                        if data.get("done"):
                            yield StreamChunk(finish_reason="stop")
                    except json.JSONDecodeError:
                        continue

    def available_models(self) -> list[str]:
        return self._models

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False