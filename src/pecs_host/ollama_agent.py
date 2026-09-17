"""Backend agêntico usando um LLM local via Ollama (API nativa).

Implementa as duas diferenças em relação à base: a chamada `client.chat(...)`
e o resultado de ferramenta no formato `{role, name, content}`.
"""

from __future__ import annotations

import os
from typing import Any

from .agent_base import (  # noqa: F401 - reexportados por compatibilidade
    MAX_STEPS,
    SYSTEM_PROMPT,
    ExecutarTool,
    LLMAgent,
    _get,
    mcp_tools_para_llm,
)

DEFAULT_MODEL = os.getenv("PECS_HOST_MODEL", "qwen2.5:7b")
DEFAULT_OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Alias histórico: o formato de tools é o mesmo para Ollama e OpenAI.
mcp_tools_para_ollama = mcp_tools_para_llm


class OllamaAgent(LLMAgent):
    """Loop de tool-calling contra o Ollama (API nativa)."""

    def __init__(
        self,
        tools: list[dict],
        executar_tool: ExecutarTool,
        *,
        model: str = DEFAULT_MODEL,
        host: str = DEFAULT_OLLAMA_HOST,
        client: Any = None,
        max_steps: int = MAX_STEPS,
    ) -> None:
        super().__init__(tools, executar_tool, model=model, max_steps=max_steps)
        if client is not None:
            self.client = client
        else:  # importação preguiçosa: testes não precisam do pacote ollama
            from ollama import AsyncClient

            self.client = AsyncClient(host=host)

    async def _chamar_llm(self) -> Any:
        resp = await self.client.chat(
            model=self.model, messages=self.messages, tools=self.tools
        )
        return _get(resp, "message")

    def _resultado_tool(self, tool_call: Any, nome: str, content: str) -> dict:
        return {"role": "tool", "name": nome, "content": content}
