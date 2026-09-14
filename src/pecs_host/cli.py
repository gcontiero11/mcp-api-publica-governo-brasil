"""REPL de terminal do host: pergunta em PT-BR → LLM local (Ollama) → ferramentas MCP."""

from __future__ import annotations

import asyncio
import os

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .mcp_link import MCPLink
from .ollama_agent import DEFAULT_MODEL, OllamaAgent, mcp_tools_para_ollama

_console = Console()


def _fmt_args(args: dict) -> str:
    if not args:
        return ""
    return ", ".join(f"{k}={v!r}" for k, v in args.items())


def _erro_amigavel(exc: Exception) -> str:
    msg = str(exc)
    baixo = msg.lower()
    if any(t in baixo for t in ("connect", "refused", "max retries", "connection")):
        return (
            "[red]Não consegui falar com o Ollama.[/] Verifique se o serviço está no ar "
            "(`ollama serve`) e se o modelo foi baixado (`ollama pull qwen2.5:7b`)."
        )
    if "not found" in baixo or "no such model" in baixo:
        return (
            f"[red]Modelo indisponível:[/] {msg}\n"
            "Baixe com `ollama pull <modelo>` ou troque com `/modelo <nome>`."
        )
    return f"[red]Erro:[/] {msg}"


async def _run() -> None:
    model = os.getenv("PECS_HOST_MODEL", DEFAULT_MODEL)
    _console.print(
        Panel.fit(
            "Busca de PECs da Câmara dos Deputados — LLM local via Ollama\n"
            "Digite sua pergunta em português.\n"
            "Comandos: [bold]/tools[/]  [bold]/modelo <nome>[/]  [bold]/sair[/]",
            title="pecs-host",
            border_style="cyan",
        )
    )

    async with MCPLink() as link:
        tools = await link.listar_tools()
        _console.print(
            f"[dim]Conectado ao servidor MCP · {len(tools)} ferramentas · modelo: {model}[/dim]\n"
        )
        agent = OllamaAgent(mcp_tools_para_ollama(tools), link.chamar_tool, model=model)

        while True:
            try:
                pergunta = _console.input("[bold cyan]você[/] › ").strip()
            except (EOFError, KeyboardInterrupt):
                _console.print("\nAté mais! 👋")
                break

            if not pergunta:
                continue
            if pergunta in ("/sair", "/quit", "/exit"):
                _console.print("Até mais! 👋")
                break
            if pergunta == "/tools":
                for t in tools:
                    desc = (t.description or "").splitlines()[0] if t.description else ""
                    _console.print(f"• [bold]{t.name}[/] — {desc}")
                continue
            if pergunta.startswith("/modelo"):
                partes = pergunta.split(maxsplit=1)
                if len(partes) == 2:
                    agent.model = partes[1].strip()
                    _console.print(f"Modelo agora: [bold]{agent.model}[/]")
                else:
                    _console.print(f"Modelo atual: [bold]{agent.model}[/]")
                continue

            def _mostrar_tool(nome: str, args: dict) -> None:
                _console.print(f"[dim]→ {nome}({_fmt_args(args)})[/dim]")

            _console.print("[dim]pensando…[/dim]")
            try:
                resposta = await agent.perguntar(pergunta, on_tool=_mostrar_tool)
            except Exception as exc:  # noqa: BLE001 - erro é mostrado ao usuário
                _console.print(_erro_amigavel(exc))
                continue

            _console.print(
                Panel(Markdown(resposta or "(resposta vazia)"), title="resposta", border_style="green")
            )


def main() -> None:
    """Ponto de entrada do console-script `pecs-host`."""
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
