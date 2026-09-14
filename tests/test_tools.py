import httpx
import respx

from mcp_camara_pecs import server
from mcp_camara_pecs.client import DEFAULT_BASE_URL


@respx.mock
async def test_listar_pecs_formata():
    respx.get(f"{DEFAULT_BASE_URL}/proposicoes").mock(
        return_value=httpx.Response(
            200,
            json={
                "dados": [
                    {
                        "id": 1,
                        "siglaTipo": "PEC",
                        "numero": 45,
                        "ano": 2019,
                        "ementa": "Reforma",
                        "dataApresentacao": "2019-04-03",
                        "uri": "u",
                    }
                ],
                "links": [],
            },
        )
    )
    resultado = await server.listar_pecs(ano=2019)
    assert resultado == [
        {
            "id": 1,
            "sigla": "PEC 45/2019",
            "ementa": "Reforma",
            "dataApresentacao": "2019-04-03",
            "uri": "u",
        }
    ]


@respx.mock
async def test_listar_votos_formata():
    respx.get(f"{DEFAULT_BASE_URL}/votacoes/2611313-34/votos").mock(
        return_value=httpx.Response(
            200,
            json={
                "dados": [
                    {
                        "tipoVoto": "Sim",
                        "dataRegistroVoto": "2023-01-01T10:00",
                        "deputado_": {
                            "id": 7,
                            "nome": "Fulano",
                            "siglaPartido": "XPTO",
                            "siglaUf": "SP",
                        },
                    }
                ],
                "links": [],
            },
        )
    )
    resultado = await server.listar_votos_votacao("2611313-34")
    assert resultado[0]["deputado"] == "Fulano"
    assert resultado[0]["tipoVoto"] == "Sim"
    assert resultado[0]["uf"] == "SP"


@respx.mock
async def test_detalhar_votacao_passthrough():
    respx.get(f"{DEFAULT_BASE_URL}/votacoes/abc").mock(
        return_value=httpx.Response(200, json={"dados": {"id": "abc", "aprovacao": 1}})
    )
    resultado = await server.detalhar_votacao("abc")
    assert resultado == {"id": "abc", "aprovacao": 1}
