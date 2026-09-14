"""Loop agêntico usando um LLM local via Ollama.

Converte as ferramentas MCP para o formato de *tools* do Ollama e roda o ciclo
chat → tool_calls → resultado → chat, até a resposta final.
"""

from __future__ import annotations

import json
import os
from typing import Any, Awaitable, Callable

DEFAULT_MODEL = os.getenv("PECS_HOST_MODEL", "qwen2.5:7b")
DEFAULT_OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MAX_STEPS = 6

SYSTEM_PROMPT = """Você é um assistente que responde perguntas sobre PECs \
(Propostas de Emenda à Constituição) usando dados reais da Câmara dos Deputados \
do Brasil, obtidos exclusivamente pelas ferramentas disponíveis.

Regras:
- Sempre use as ferramentas para buscar os dados; nunca invente números, datas ou nomes.
- Encadeie ferramentas quando necessário. Para chegar a votos ou orientações de bancada:
  1) descubra o id da PEC com `listar_pecs`;
  2) liste as votações dela com `listar_votacoes_pec` (pegue o id da votação);
  3) use `listar_votos_votacao` (voto nominal) ou `listar_orientacoes_votacao`.
- Responda em português, de forma objetiva, citando números, placar e datas quando houver.
- Se as ferramentas não retornarem o dado, diga isso claramente em vez de supor."""

ExecutarTool = Callable[[str, dict], Awaitable[str]]


def _get(obj: Any, key: str, default: Any = None) -> Any:
    """Acessa `key` tanto em dicts (mocks/testes) quanto em objetos do Ollama."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def mcp_tools_para_ollama(tools: list[Any]) -> list[dict]:
    """Converte ferramentas MCP (name/description/inputSchema) p/ o formato Ollama."""
    convertidas: list[dict] = []
    for t in tools:
        convertidas.append(
            {
                "type": "function",
                "function": {
                    "name": _get(t, "name"),
                    "description": _get(t, "description") or "",
                    "parameters": _get(t, "inputSchema")
                    or {"type": "object", "properties": {}},
                },
            }
        )
    return convertidas


class OllamaAgent:
    """Mantém a conversa e executa o loop de tool-calling contra o Ollama."""

    def __init__(
        self,
        tools_ollama: list[dict],
        executar_tool: ExecutarTool,
        *,
        model: str = DEFAULT_MODEL,
        host: str = DEFAULT_OLLAMA_HOST,
        client: Any = None,
        max_steps: int = MAX_STEPS,
    ) -> None:
        self.tools = tools_ollama
        self.executar_tool = executar_tool
        self.model = model
        self.max_steps = max_steps
        if client is not None:
            self.client = client
        else:  # importação preguiçosa: testes não precisam do pacote ollama
            from ollama import AsyncClient

            self.client = AsyncClient(host=host)
        self.messages: list[Any] = [{"role": "system", "content": SYSTEM_PROMPT}]

    async def perguntar(
        self,
        pergunta: str,
        *,
        on_tool: Callable[[str, dict], None] | None = None,
    ) -> str:
        self.messages.append({"role": "user", "content": pergunta})

        for _ in range(self.max_steps):
            resp = await self.client.chat(
                model=self.model, messages=self.messages, tools=self.tools
            )
            msg = _get(resp, "message")
            self.messages.append(msg)

            tool_calls = _get(msg, "tool_calls")
            if not tool_calls:
                return _get(msg, "content") or ""

            for tc in tool_calls:
                fn = _get(tc, "function")
                nome = _get(fn, "name")
                args = _get(fn, "arguments") or {}
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                if on_tool:
                    on_tool(nome, args)
                resultado = await self.executar_tool(nome, args)
                self.messages.append(
                    {"role": "tool", "name": nome, "content": resultado}
                )

        return (
            "Não consegui concluir após várias tentativas de usar as ferramentas. "
            "Tente reformular a pergunta ou usar um modelo maior (ex.: /modelo llama3.1:8b)."
        )
