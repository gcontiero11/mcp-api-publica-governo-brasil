import httpx
import pytest
import respx

from mcp_camara_pecs.client import CamaraAPIError, CamaraClient, DEFAULT_BASE_URL


@respx.mock
async def test_get_dado_retorna_objeto():
    respx.get(f"{DEFAULT_BASE_URL}/proposicoes/123").mock(
        return_value=httpx.Response(200, json={"dados": {"id": 123, "siglaTipo": "PEC"}})
    )
    async with CamaraClient(backoff_base=0) as client:
        dado = await client.get_dado("/proposicoes/123")
    assert dado["id"] == 123


@respx.mock
async def test_get_all_pagina_unica():
    respx.get(f"{DEFAULT_BASE_URL}/proposicoes").mock(
        return_value=httpx.Response(200, json={"dados": [{"id": 1}, {"id": 2}], "links": []})
    )
    async with CamaraClient(backoff_base=0) as client:
        dados = await client.get_all("/proposicoes", {"siglaTipo": "PEC"}, max_itens=50)
    assert [d["id"] for d in dados] == [1, 2]


@respx.mock
async def test_get_all_pagina_multipla():
    route = respx.get(f"{DEFAULT_BASE_URL}/proposicoes")
    route.side_effect = [
        httpx.Response(200, json={"dados": [{"id": 1}], "links": [{"rel": "next", "href": "x"}]}),
        httpx.Response(200, json={"dados": [{"id": 2}], "links": []}),
    ]
    async with CamaraClient(backoff_base=0) as client:
        dados = await client.get_all("/proposicoes", max_itens=50)
    assert [d["id"] for d in dados] == [1, 2]


@respx.mock
async def test_get_all_respeita_max_itens():
    respx.get(f"{DEFAULT_BASE_URL}/proposicoes").mock(
        return_value=httpx.Response(
            200,
            json={
                "dados": [{"id": i} for i in range(10)],
                "links": [{"rel": "next", "href": "x"}],
            },
        )
    )
    async with CamaraClient(backoff_base=0) as client:
        dados = await client.get_all("/proposicoes", max_itens=3)
    assert len(dados) == 3


@respx.mock
async def test_retry_em_500_depois_sucesso():
    route = respx.get(f"{DEFAULT_BASE_URL}/proposicoes/9")
    route.side_effect = [
        httpx.Response(500),
        httpx.Response(200, json={"dados": {"id": 9}}),
    ]
    async with CamaraClient(backoff_base=0) as client:
        dado = await client.get_dado("/proposicoes/9")
    assert dado["id"] == 9


@respx.mock
async def test_erro_4xx_levanta():
    respx.get(f"{DEFAULT_BASE_URL}/proposicoes/0").mock(
        return_value=httpx.Response(404, text="não encontrado")
    )
    async with CamaraClient(backoff_base=0) as client:
        with pytest.raises(CamaraAPIError):
            await client.get_dado("/proposicoes/0")
