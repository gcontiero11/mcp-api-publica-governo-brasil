"""Testes da seleção de backend (fábrica de agentes)."""

from pecs_host.factory import criar_agent, escolher_backend


async def _executar_tool(nome, args):
    return "[]"


def test_backend_default_e_lmstudio():
    assert escolher_backend({}) == "lmstudio"


def test_escolher_backend_respeita_env():
    assert escolher_backend({"PECS_HOST_BACKEND": "ollama"}) == "ollama"


def test_escolher_backend_normaliza():
    assert escolher_backend({"PECS_HOST_BACKEND": " OLLAMA "}) == "ollama"


def test_criar_agent_default_e_openai():
    from pecs_host.openai_agent import OpenAIAgent

    agent = criar_agent([], _executar_tool, client=object(), env={})
    assert isinstance(agent, OpenAIAgent)


def test_criar_agent_ollama_quando_pedido():
    from pecs_host.ollama_agent import OllamaAgent

    agent = criar_agent(
        [], _executar_tool, client=object(), env={"PECS_HOST_BACKEND": "ollama"}
    )
    assert isinstance(agent, OllamaAgent)


def test_criar_agent_backend_desconhecido_erro():
    import pytest

    with pytest.raises(ValueError):
        criar_agent([], _executar_tool, client=object(), env={"PECS_HOST_BACKEND": "xyz"})
