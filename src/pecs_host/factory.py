"""Seleção do backend do host a partir de variáveis de ambiente.

Backend padrão: `lmstudio` (endpoint compatível com OpenAI). Use
`PECS_HOST_BACKEND=ollama` para o Ollama nativo.
"""

from __future__ import annotations

import os
from typing import Any, Mapping

from .agent_base import MAX_STEPS, ExecutarTool, LLMAgent

DEFAULT_BACKEND = "lmstudio"
_OPENAI_ALIASES = {"lmstudio", "openai", "lm-studio", "lm_studio"}


def escolher_backend(env: Mapping[str, str] | None = None) -> str:
    """Nome normalizado do backend a partir de `PECS_HOST_BACKEND`."""
    env = env if env is not None else os.environ
    return (env.get("PECS_HOST_BACKEND") or DEFAULT_BACKEND).strip().lower()


def criar_agent(
    tools: list[dict],
    executar_tool: ExecutarTool,
    *,
    backend: str | None = None,
    model: str | None = None,
    client: Any = None,
    max_steps: int = MAX_STEPS,
    env: Mapping[str, str] | None = None,
) -> LLMAgent:
    """Instancia o agente do backend escolhido, lendo config do ambiente."""
    env = env if env is not None else os.environ
    backend = (backend or escolher_backend(env)).strip().lower()

    if backend == "ollama":
        from .ollama_agent import DEFAULT_MODEL, DEFAULT_OLLAMA_HOST, OllamaAgent

        return OllamaAgent(
            tools,
            executar_tool,
            model=model or env.get("PECS_HOST_MODEL", DEFAULT_MODEL),
            host=env.get("OLLAMA_HOST", DEFAULT_OLLAMA_HOST),
            client=client,
            max_steps=max_steps,
        )

    if backend in _OPENAI_ALIASES:
        from .openai_agent import DEFAULT_BASE_URL, DEFAULT_MODEL, OpenAIAgent

        return OpenAIAgent(
            tools,
            executar_tool,
            model=model or env.get("PECS_HOST_MODEL", DEFAULT_MODEL),
            base_url=env.get("PECS_HOST_BASE_URL", DEFAULT_BASE_URL),
            api_key=env.get("PECS_HOST_API_KEY"),
            client=client,
            max_steps=max_steps,
        )

    raise ValueError(
        f"Backend desconhecido: {backend!r}. Use 'lmstudio' (padrão) ou 'ollama'."
    )
