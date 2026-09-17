"""Backend agêntico via API compatível com OpenAI (LM Studio, vLLM, /v1 do Ollama…).

Implementa as duas diferenças em relação à base: a chamada
`client.chat.completions.create(...)` e o resultado de ferramenta com
`tool_call_id` (formato OpenAI).
"""

from __future__ import annotations

import os
from typing import Any

from .agent_base import MAX_STEPS, ExecutarTool, LLMAgent, _get

DEFAULT_BASE_URL = os.getenv("PECS_HOST_BASE_URL", "http://localhost:1234/v1")
DEFAULT_MODEL = os.getenv("PECS_HOST_MODEL", "local-model")
DEFAULT_API_KEY = os.getenv("PECS_HOST_API_KEY", "lm-studio")


class OpenAIAgent(LLMAgent):
    """Loop de tool-calling contra um endpoint compatível com OpenAI."""

    def __init__(
        self,
        tools: list[dict],
        executar_tool: ExecutarTool,
        *,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        api_key: str | None = None,
        client: Any = None,
        max_steps: int = MAX_STEPS,
    ) -> None:
        super().__init__(tools, executar_tool, model=model, max_steps=max_steps)
        if client is not None:
            self.client = client
        else:  # importação preguiçosa: testes não precisam do pacote openai
            from openai import AsyncOpenAI

            self.client = AsyncOpenAI(base_url=base_url, api_key=api_key or DEFAULT_API_KEY)

    async def _chamar_llm(self) -> Any:
        kwargs: dict[str, Any] = {"model": self.model, "messages": self.messages}
        if self.tools:
            kwargs["tools"] = self.tools
            kwargs["tool_choice"] = "auto"
        resp = await self.client.chat.completions.create(**kwargs)
        return resp.choices[0].message

    def _resultado_tool(self, tool_call: Any, nome: str, content: str) -> dict:
        return {
            "role": "tool",
            "tool_call_id": _get(tool_call, "id"),
            "content": content,
        }
