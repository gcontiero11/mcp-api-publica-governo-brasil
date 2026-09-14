"""Servidor MCP: ferramentas para consultar PECs na API da Câmara dos Deputados.

Expõe ferramentas curadas sobre proposições do tipo PEC, suas tramitações e
suas votações (incluindo votos nominais por deputado e orientação de bancada).

Transporte padrão: stdio (Claude Desktop, Cursor e outros clientes locais).
"""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from . import formatting as fmt
from .client import CamaraClient

mcp = MCPServer("camara-pecs")


@mcp.tool()
async def listar_pecs(
    ano: int | None = None,
    numero: int | None = None,
    keywords: str | None = None,
    data_apresentacao_inicio: str | None = None,
    data_apresentacao_fim: str | None = None,
    ordenar_por: str = "id",
    ordem: str = "DESC",
    max_itens: int = 50,
) -> list[dict[str, Any]]:
    """Lista Propostas de Emenda à Constituição (PECs).

    Use para descobrir PECs e obter o `id` de cada uma (necessário nas demais
    ferramentas). Filtros são opcionais e combináveis.

    Parâmetros:
    - ano: ano de apresentação (ex.: 2023).
    - numero: número da proposição.
    - keywords: termos de busca na ementa/palavras-chave (ex.: "reforma tributária").
    - data_apresentacao_inicio / data_apresentacao_fim: intervalo AAAA-MM-DD.
    - ordenar_por: campo de ordenação ("id", "ano", "numero").
    - ordem: "ASC" ou "DESC".
    - max_itens: teto de resultados retornados (paginação automática).
    """
    params = {
        "siglaTipo": "PEC",
        "ano": ano,
        "numero": numero,
        "keywords": keywords,
        "dataApresentacaoInicio": data_apresentacao_inicio,
        "dataApresentacaoFim": data_apresentacao_fim,
        "ordenarPor": ordenar_por,
        "ordem": ordem,
    }
    async with CamaraClient() as client:
        dados = await client.get_all("/proposicoes", params, max_itens=max_itens)
    return [fmt.resumir_proposicao(p) for p in dados]


@mcp.tool()
async def detalhar_pec(id: int) -> dict[str, Any]:
    """Retorna os dados completos de uma PEC pelo seu `id`.

    Inclui ementa detalhada, palavras-chave e o status/tramitação mais recente.
    Obtenha o `id` com `listar_pecs`.
    """
    async with CamaraClient() as client:
        return await client.get_dado(f"/proposicoes/{id}")


@mcp.tool()
async def listar_autores_pec(id: int) -> list[dict[str, Any]]:
    """Lista os autores/apresentantes de uma PEC (deputados, senadores, órgãos)."""
    async with CamaraClient() as client:
        dados = await client.get_lista(f"/proposicoes/{id}/autores", max_itens=200)
    return [fmt.resumir_autor(a) for a in dados]


@mcp.tool()
async def listar_tramitacoes_pec(
    id: int,
    data_inicio: str | None = None,
    data_fim: str | None = None,
    max_itens: int = 200,
) -> list[dict[str, Any]]:
    """Lista o histórico de tramitação de uma PEC, em ordem cronológica.

    Cada item traz data/hora, órgão, o tipo de tramitação, a situação e o
    despacho. Filtre por intervalo com `data_inicio`/`data_fim` (AAAA-MM-DD).
    """
    params = {"dataInicio": data_inicio, "dataFim": data_fim}
    async with CamaraClient() as client:
        dados = await client.get_lista(
            f"/proposicoes/{id}/tramitacoes", params, max_itens=max_itens
        )
    return [fmt.resumir_tramitacao(t) for t in dados]


@mcp.tool()
async def listar_votacoes_pec(id: int, max_itens: int = 100) -> list[dict[str, Any]]:
    """Lista as votações associadas a uma PEC.

    Retorna o `id` de cada votação (string, ex.: "2611313-34"), necessário para
    `detalhar_votacao`, `listar_votos_votacao` e `listar_orientacoes_votacao`.
    """
    async with CamaraClient() as client:
        dados = await client.get_lista(
            f"/proposicoes/{id}/votacoes", max_itens=max_itens
        )
    return [fmt.resumir_votacao(v) for v in dados]


@mcp.tool()
async def detalhar_votacao(id: str) -> dict[str, Any]:
    """Retorna o detalhe/resultado de uma votação pelo seu `id`.

    Inclui descrição, órgão, se foi aprovada (`aprovacao`) e o placar. Obtenha o
    `id` com `listar_votacoes_pec`.
    """
    async with CamaraClient() as client:
        return await client.get_dado(f"/votacoes/{id}")


@mcp.tool()
async def listar_votos_votacao(id: str, max_itens: int = 600) -> list[dict[str, Any]]:
    """Lista o voto nominal de cada deputado em uma votação.

    Cada item traz o nome do deputado, partido, UF e o `tipoVoto`
    (Sim/Não/Abstenção/Obstrução/Artigo etc.). Só há votos nominais em votações
    por registro eletrônico (votações simbólicas retornam lista vazia).
    """
    async with CamaraClient() as client:
        dados = await client.get_lista(f"/votacoes/{id}/votos", max_itens=max_itens)
    return [fmt.resumir_voto(v) for v in dados]


@mcp.tool()
async def listar_orientacoes_votacao(id: str) -> list[dict[str, Any]]:
    """Lista a orientação de cada bancada/partido em uma votação.

    Mostra como cada liderança orientou seus deputados a votar. Repassado sem
    filtro por ser uma lista curta.
    """
    async with CamaraClient() as client:
        return await client.get_dado(f"/votacoes/{id}/orientacoes")


def main() -> None:
    """Ponto de entrada: inicia o servidor MCP no transporte stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
