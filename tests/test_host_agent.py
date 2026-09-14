"""Testes do loop agêntico do host, com Ollama e ferramentas MOCKADOS (sem rede)."""

import pytest

from pecs_host.ollama_agent import OllamaAgent, mcp_tools_para_ollama


class FakeTool:
    def __init__(self, name, description, inputSchema):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema


class FakeOllama:
    """Devolve respostas pré-programadas e registra as chamadas de chat."""

    def __init__(self, respostas):
        self._respostas = list(respostas)
        self.calls = []

    async def chat(self, model, messages, tools):
        self.calls.append({"model": model, "messages": list(messages), "tools": tools})
        return self._respostas.pop(0)


def test_conversao_tools_para_ollama():
    tools = [
        FakeTool(
            "listar_pecs",
            "Lista PECs",
            {"type": "object", "properties": {"ano": {"type": "integer"}}},
        )
    ]
    out = mcp_tools_para_ollama(tools)
    assert out[0]["type"] == "function"
    assert out[0]["function"]["name"] == "listar_pecs"
    assert out[0]["function"]["parameters"]["properties"]["ano"]["type"] == "integer"


def test_conversao_tool_sem_schema_usa_default():
    tools = [FakeTool("x", None, None)]
    out = mcp_tools_para_ollama(tools)
    assert out[0]["function"]["parameters"] == {"type": "object", "properties": {}}


async def test_loop_executa_tool_e_retorna_final():
    respostas = [
        {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"function": {"name": "listar_pecs", "arguments": {"ano": 2023}}}
                ],
            }
        },
        {"message": {"role": "assistant", "content": "Encontrei 3 PECs de 2023."}},
    ]
    fake = FakeOllama(respostas)
    chamadas = []

    async def executar_tool(nome, args):
        chamadas.append((nome, args))
        return '[{"id": 1, "sigla": "PEC 1/2023"}]'

    agent = OllamaAgent([], executar_tool, client=fake, model="fake")
    resposta = await agent.perguntar("Liste PECs de 2023")

    assert resposta == "Encontrei 3 PECs de 2023."
    assert chamadas == [("listar_pecs", {"ano": 2023})]
    # A 2a chamada ao chat deve conter a mensagem de resultado da ferramenta.
    assert any(
        m.get("role") == "tool" and m.get("name") == "listar_pecs"
        for m in fake.calls[1]["messages"]
    )


async def test_loop_argumentos_como_string_json():
    respostas = [
        {
            "message": {
                "tool_calls": [
                    {"function": {"name": "detalhar_pec", "arguments": '{"id": 99}'}}
                ]
            }
        },
        {"message": {"content": "PEC 99 detalhada."}},
    ]
    fake = FakeOllama(respostas)
    chamadas = []

    async def executar_tool(nome, args):
        chamadas.append((nome, args))
        return "{}"

    agent = OllamaAgent([], executar_tool, client=fake, model="fake")
    resposta = await agent.perguntar("detalhe a PEC 99")
    assert resposta == "PEC 99 detalhada."
    assert chamadas == [("detalhar_pec", {"id": 99})]


async def test_loop_sem_tool_retorna_direto():
    fake = FakeOllama([{"message": {"role": "assistant", "content": "Olá!"}}])

    async def executar_tool(nome, args):
        raise AssertionError("não deveria chamar ferramenta")

    agent = OllamaAgent([], executar_tool, client=fake, model="fake")
    resposta = await agent.perguntar("oi")
    assert resposta == "Olá!"


async def test_loop_respeita_max_steps():
    # Sempre pede tool -> nunca conclui; deve parar em max_steps com mensagem.
    resposta_tool = {
        "message": {"tool_calls": [{"function": {"name": "listar_pecs", "arguments": {}}}]}
    }
    fake = FakeOllama([resposta_tool] * 10)

    async def executar_tool(nome, args):
        return "[]"

    agent = OllamaAgent([], executar_tool, client=fake, model="fake", max_steps=3)
    resposta = await agent.perguntar("loop infinito?")
    assert "Não consegui concluir" in resposta
    assert len(fake.calls) == 3
