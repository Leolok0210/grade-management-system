"""
AI Provider 抽象層 - 統一介面供多模型切換
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional


@dataclass
class AIResponse:
    content: Optional[str] = None
    tool_call_name: Optional[str] = None
    tool_call_arguments: Optional[dict] = None
    finish_reason: str = "stop"


@dataclass
class StreamChunk:
    content: Optional[str] = None
    tool_call_name: Optional[str] = None
    tool_call_arguments_delta: Optional[str] = None
    finish_reason: Optional[str] = None


class AIProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        model: Optional[str] = None,
    ) -> AIResponse:
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        model: Optional[str] = None,
    ) -> AsyncIterator[StreamChunk]:
        ...

    @abstractmethod
    def available_models(self) -> list[str]:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...