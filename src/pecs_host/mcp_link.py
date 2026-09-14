"""Conexão com o servidor MCP `mcp_camara_pecs` via stdio.

Sobe o servidor como subprocesso (usando o mesmo Python do venv), inicializa a
sessão MCP e expõe métodos simples para listar e chamar ferramentas.
"""

from __future__ import annotations

import json
import os
import sys
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Teto de caracteres do resultado de uma ferramenta devolvido ao LLM. Em CPU, um
# resultado enorme (ex.: ~500 votos nominais) estoura contexto e latência.
MAX_RESULT_CHARS = 6000


class MCPLink:
    """Gerencia o ciclo de vida da conexão MCP como context manager assíncrono."""

    def __init__(self, command: str | None = None, args: list[str] | None = None) -> None:
        self.command = command or sys.executable
        self.args = args or ["-m", "mcp_camara_pecs"]
        self._stack: AsyncExitStack | None = None
        self._devnull: Any = None
        self.session: ClientSession | None = None

    async def __aenter__(self) -> "MCPLink":
        self._stack = AsyncExitStack()
        # Silencia o stderr do servidor para não poluir o CLI.
        self._devnull = open(os.devnull, "w")
        params = StdioServerParameters(command=self.command, args=self.args)
        read, write = await self._stack.enter_async_context(
            stdio_client(params, errlog=self._devnull)
        )
        self.session = await self._stack.enter_async_context(ClientSession(read, write))
        await self.session.initialize()
        return self

    async def __aexit__(self, *_exc: object) -> None:
        if self._stack is not None:
            await self._stack.aclose()
            self._stack = None
            self.session = None
        if self._devnull is not None:
            self._devnull.close()
            self._devnull = None

    async def listar_tools(self) -> list[Any]:
        assert self.session is not None, "sessão não inicializada"
        resp = await self.session.list_tools()
        return list(resp.tools)

    async def chamar_tool(self, nome: str, args: dict[str, Any] | None = None) -> str:
        assert self.session is not None, "sessão não inicializada"
        result = await self.session.call_tool(nome, args or {})
        return _extrair_texto(result)


def _extrair_texto(result: Any) -> str:
    partes: list[str] = []
    for bloco in getattr(result, "content", None) or []:
        texto = getattr(bloco, "text", None)
        if texto:
            partes.append(texto)
    saida = "\n".join(partes).strip()

    if not saida:
        structured = getattr(result, "structuredContent", None)
        if structured is not None:
            saida = json.dumps(structured, ensure_ascii=False)

    if len(saida) > MAX_RESULT_CHARS:
        saida = saida[:MAX_RESULT_CHARS] + "\n…(resultado truncado para caber no contexto)"

    return saida or "(sem conteúdo)"
