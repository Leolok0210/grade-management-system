"""
多模型路由器 - 根據任務類型選擇最適模型
"""

from typing import Optional

from app.ai.provider import AIProvider, AIResponse, StreamChunk
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.providers.claude_provider import ClaudeProvider
from app.ai.providers.local_provider import LocalProvider
from app.config import settings


# 任務類型 → 首選 provider 映射
TASK_PROVIDER_MAP = {
    "intent_recognition": "openai",   # 低延遲、結構化輸出
    "response_generation": "openai",  # 品質優先
    "anomaly_analysis": "anthropic",  # 推理深度
    "report_generation": "openai",    # 長輸出品質
}


class MultiModelRouter(AIProvider):
    def __init__(self):
        self._providers: dict[str, AIProvider] = {}
        self._init_providers()

    def _init_providers(self):
        if settings.OPENAI_API_KEY:
            self._providers["openai"] = OpenAIProvider()
        if settings.ANTHROPIC_API_KEY:
            self._providers["anthropic"] = ClaudeProvider()
        # Local always available (may fail at runtime)
        self._providers["local"] = LocalProvider()

    def get_provider(self, provider_name: Optional[str] = None) -> AIProvider:
        name = provider_name or settings.DEFAULT_PROVIDER
        if name in self._providers:
            return self._providers[name]
        # Fallback
        for p in self._providers.values():
            return p
        raise RuntimeError("沒有可用的 AI Provider，請設定 API Key")

    def get_provider_for_task(self, task_type: str) -> AIProvider:
        preferred = TASK_PROVIDER_MAP.get(task_type, settings.DEFAULT_PROVIDER)
        if preferred in self._providers:
            return self._providers[preferred]
        return self.get_provider()

    async def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> AIResponse:
        p = self.get_provider(provider)
        return await p.chat(messages, tools, model)

    async def chat_stream(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        p = self.get_provider(provider)
        async for chunk in p.chat_stream(messages, tools, model):
            yield chunk

    def available_models(self) -> list[str]:
        models = []
        for p in self._providers.values():
            models.extend(p.available_models())
        return models

    async def health_check(self) -> bool:
        for p in self._providers.values():
            if await p.health_check():
                return True
        return False