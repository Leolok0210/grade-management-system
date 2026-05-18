"""
AI Provider 抽象層 - 統一介面供多模型切換
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator


@dataclass
class AIResponse:
    content: str | None = None
    tool_call_name: str | None = None
    tool_call_arguments: dict | None = None
    finish_reason: str = "stop"


@dataclass
class StreamChunk:
    content: str | None = None
    tool_call_name: str | None = None
    tool_call_arguments_delta: str | None = None
    finish_reason: str | None = None


class AIProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
    ) -> AIResponse:
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
    ) -> AsyncIterator[StreamChunk]:
        ...

    @abstractmethod
    def available_models(self) -> list[str]:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...