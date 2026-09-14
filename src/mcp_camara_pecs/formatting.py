"""Reduz o JSON verboso da API da Câmara a campos úteis para o LLM.

Aplicado sobretudo a endpoints de LISTA (que podem trazer muitos itens). Os
endpoints de DETALHE (objeto único) são repassados sem filtro para não arriscar
descartar campos úteis.
"""

from __future__ import annotations

from typing import Any


def _sigla(p: dict[str, Any]) -> str | None:
    tipo = p.get("siglaTipo")
    numero = p.get("numero")
    ano = p.get("ano")
    if tipo and numero and ano:
        return f"{tipo} {numero}/{ano}"
    return tipo


def resumir_proposicao(p: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": p.get("id"),
        "sigla": _sigla(p),
        "ementa": p.get("ementa"),
        "dataApresentacao": p.get("dataApresentacao"),
        "uri": p.get("uri"),
    }


def resumir_tramitacao(t: dict[str, Any]) -> dict[str, Any]:
    return {
        "sequencia": t.get("sequencia"),
        "dataHora": t.get("dataHora"),
        "siglaOrgao": t.get("siglaOrgao"),
        "descricaoTramitacao": t.get("descricaoTramitacao"),
        "descricaoSituacao": t.get("descricaoSituacao"),
        "despacho": t.get("despacho"),
    }


def resumir_votacao(v: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": v.get("id"),
        "data": v.get("data"),
        "descricao": v.get("descricao"),
        "siglaOrgao": v.get("siglaOrgao"),
        "aprovacao": v.get("aprovacao"),
    }


def resumir_voto(v: dict[str, Any]) -> dict[str, Any]:
    deputado = v.get("deputado_") or {}
    return {
        "deputado": deputado.get("nome"),
        "partido": deputado.get("siglaPartido"),
        "uf": deputado.get("siglaUf"),
        "idDeputado": deputado.get("id"),
        "tipoVoto": v.get("tipoVoto"),
        "dataRegistroVoto": v.get("dataRegistroVoto"),
    }


def resumir_autor(a: dict[str, Any]) -> dict[str, Any]:
    return {
        "nome": a.get("nome"),
        "tipo": a.get("tipo"),
        "proponente": a.get("proponente"),
        "ordemAssinatura": a.get("ordemAssinatura"),
        "uri": a.get("uri"),
    }
