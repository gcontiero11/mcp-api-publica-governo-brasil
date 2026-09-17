"""Testes do loop agêntico com backend OpenAI-compatível (LM Studio), MOCKADO."""

import types


def _msg(content=None, tool_calls=None):
    return types.SimpleNamespace(role="assistant", content=content, tool_calls=tool_calls)


def _resp(message):
    return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])


def _tool_call(id, name, arguments):
    fn = types.SimpleNamespace(name=name, arguments=arguments)
    return types.SimpleNamespace(id=id, function=fn)


class FakeOpenAI:
    """Imita `client.chat.completions.create(**kwargs)` do SDK openai."""

    def __init__(self, respostas):
        self._respostas = list(respostas)
        self.calls = []
        self.chat = types.SimpleNamespace(
            completions=types.SimpleNamespace(create=self._create)
        )

    async def _create(self, **kwargs):
        self.calls.append(kwargs)
        return self._respostas.pop(0)


async def test_loop_executa_tool_e_usa_tool_call_id():
    from pecs_host.openai_agent import OpenAIAgent

    respostas = [
        _resp(
            _msg(
                content="",
                tool_calls=[_tool_call("call_1", "listar_pecs", '{"ano": 2023}')],
            )
        ),
        _resp(_msg(content="Encontrei 3 PECs de 2023.")),
    ]
    fake = FakeOpenAI(respostas)
    chamadas = []

    async def executar_tool(nome, args):
        chamadas.append((nome, args))
        return '[{"id": 1, "sigla": "PEC 1/2023"}]'

    agent = OpenAIAgent([], executar_tool, client=fake, model="fake")
    resposta = await agent.perguntar("Liste PECs de 2023")

    assert resposta == "Encontrei 3 PECs de 2023."
    assert chamadas == [("listar_pecs", {"ano": 2023})]
    # A 2a chamada deve conter a msg de resultado da ferramenta com o tool_call_id.
    segunda = fake.calls[1]["messages"]
    assert any(
        isinstance(m, dict)
        and m.get("role") == "tool"
        and m.get("tool_call_id") == "call_1"
        for m in segunda
    )


async def test_loop_sem_tool_retorna_direto():
    from pecs_host.openai_agent import OpenAIAgent

    fake = FakeOpenAI([_resp(_msg(content="Olá!"))])

    async def executar_tool(nome, args):
        raise AssertionError("não deveria chamar ferramenta")

    agent = OpenAIAgent([], executar_tool, client=fake, model="fake")
    assert await agent.perguntar("oi") == "Olá!"


async def test_loop_respeita_max_steps():
    from pecs_host.openai_agent import OpenAIAgent

    resposta_tool = _resp(
        _msg(content="", tool_calls=[_tool_call("c", "listar_pecs", "{}")])
    )
    fake = FakeOpenAI([resposta_tool] * 10)

    async def executar_tool(nome, args):
        return "[]"

    agent = OpenAIAgent([], executar_tool, client=fake, model="fake", max_steps=3)
    resposta = await agent.perguntar("loop infinito?")
    assert "Não consegui concluir" in resposta
    assert len(fake.calls) == 3
