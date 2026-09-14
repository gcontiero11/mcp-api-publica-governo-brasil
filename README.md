# mcp-camara-pecs

Servidor **MCP (Model Context Protocol)** para consultar **votações e tramitações de PECs** (Propostas de Emenda à Constituição) usando a **API de Dados Abertos da Câmara dos Deputados** (`https://dadosabertos.camara.leg.br/api/v2`).

A API é **pública e não exige chave de autenticação**. Este servidor apenas consome dados abertos já disponíveis a qualquer cidadão.

> Parte do repositório `mcp-api-publica-governo-brasil`. A v1 cobre a **Câmara dos Deputados**; a integração com o **Senado Federal** está planejada (ver `.claude/tasks/feature/`).

## Ferramentas expostas

| Ferramenta | O que faz | Endpoint |
|---|---|---|
| `listar_pecs` | Lista PECs (filtros: ano, número, palavras-chave, datas) | `GET /proposicoes?siglaTipo=PEC` |
| `detalhar_pec` | Dados completos de uma PEC por `id` | `GET /proposicoes/{id}` |
| `listar_autores_pec` | Autores/apresentantes da PEC | `GET /proposicoes/{id}/autores` |
| `listar_tramitacoes_pec` | Histórico de tramitação | `GET /proposicoes/{id}/tramitacoes` |
| `listar_votacoes_pec` | Votações associadas à PEC | `GET /proposicoes/{id}/votacoes` |
| `detalhar_votacao` | Resultado/detalhe de uma votação | `GET /votacoes/{id}` |
| `listar_votos_votacao` | Voto nominal de cada deputado | `GET /votacoes/{id}/votos` |
| `listar_orientacoes_votacao` | Orientação de cada bancada | `GET /votacoes/{id}/orientacoes` |

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .          # produção
pip install -e ".[dev]"   # com dependências de teste
```

## Uso

O servidor roda no transporte **stdio**:

```bash
python -m mcp_camara_pecs
# ou, via console-script:
mcp-camara-pecs
```

### Configuração no Claude Desktop / Cursor

Adicione ao arquivo de configuração de MCP servers (use o caminho absoluto do Python
do seu venv):

```json
{
  "mcpServers": {
    "camara-pecs": {
      "command": "/caminho/para/.venv/bin/python",
      "args": ["-m", "mcp_camara_pecs"]
    }
  }
}
```

## Variáveis de ambiente (opcionais)

- `CAMARA_API_BASE` — sobrescreve a URL base da API.
- `HTTP_TIMEOUT` — timeout das requisições em segundos (padrão: 30).

## Desenvolvimento

```bash
pip install -e ".[dev]"
pytest                    # testes unitários (HTTP mockado, sem rede)
npx @modelcontextprotocol/inspector python -m mcp_camara_pecs   # inspeção manual
```

### Exemplo de fluxo

1. `listar_pecs(ano=2019, keywords="reforma")` → obtenha o `id` da PEC.
2. `detalhar_pec(id)` e `listar_tramitacoes_pec(id)`.
3. `listar_votacoes_pec(id)` → obtenha o `id` da votação.
4. `detalhar_votacao(id)`, `listar_votos_votacao(id)`, `listar_orientacoes_votacao(id)`.

## Licença

MIT.
