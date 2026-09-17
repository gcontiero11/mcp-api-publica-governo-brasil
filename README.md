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

## Host CLI (busca com LLM)

Além do servidor, o projeto traz um **host MCP em terminal** (`pecs-host`): você pergunta
em português, um **LLM** interpreta, chama as ferramentas do servidor **pelo protocolo
MCP** e responde. Dois backends são suportados:

- **LM Studio** (padrão) — qualquer modelo servido pelo endpoint compatível com OpenAI.
- **Ollama** — LLM local nativo, 100% offline (`PECS_HOST_BACKEND=ollama`).

> Modelos com bom suporte a *tool-calling* (Qwen2.5, Llama 3.1 etc.) encadeiam as
> ferramentas de forma mais confiável; modelos muito pequenos podem errar o schema.

### Tutorial passo a passo — LM Studio (Linux · macOS · Windows)

Do zero até a primeira pergunta respondida. Onde o comando muda por sistema, os três
estão indicados.

#### 1. Instalar o LM Studio

Baixe o instalador em **<https://lmstudio.ai>** e instale:

- **Linux** — arquivo `.AppImage`: dê permissão de execução e rode
  (`chmod +x LM-Studio-*.AppImage && ./LM-Studio-*.AppImage`).
- **macOS** — arquivo `.dmg`: arraste o app para *Applications*.
- **Windows** — instalador `.exe`: siga o assistente.

#### 2. Baixar um modelo com suporte a ferramentas

No LM Studio, abra a aba **🔍 Discover/Search**, procure um modelo bom em *tool-calling*
e baixe. Sugestões: **`Qwen2.5 7B Instruct`** (equilíbrio) ou **`Qwen2.5 3B Instruct`**
(mais leve). Evite modelos muito pequenos — eles erram o formato das chamadas de ferramenta.

#### 3. Ligar o servidor local

Abra a aba **Developer** (ícone `>_`), **carregue o modelo** no topo e clique em
**Start Server**. O endpoint padrão é **`http://localhost:1234/v1`**.

#### 4. Descobrir o nome exato do modelo

`PECS_HOST_MODEL` precisa bater com o identificador que o LM Studio expõe (essa é a causa
nº 1 do erro *"model not found"*). Para descobrir:

```bash
# Linux / macOS
curl http://localhost:1234/v1/models
```
```powershell
# Windows (PowerShell)
Invoke-RestMethod http://localhost:1234/v1/models | ConvertTo-Json -Depth 5
```

Anote o valor do campo `"id"` (algo como `qwen2.5-7b-instruct`).

#### 5. Preparar o ambiente Python (>= 3.10)

Recomendado: **pyenv 3.11.13** (evita depender do Python do sistema).

```bash
# Linux / macOS (com pyenv)
pyenv install 3.11.13
pyenv shell 3.11.13
python -m venv .venv
source .venv/bin/activate
```
```powershell
# Windows (PowerShell) — pyenv-win, ou o Python 3.11 do python.org
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### 6. Instalar o projeto

```bash
pip install -e ".[host]"
```

#### 7. Rodar o host

Com o servidor do LM Studio no ar, defina o nome do modelo (passo 4) e rode `pecs-host`.
A sintaxe da variável de ambiente muda por shell:

```bash
# Linux / macOS (bash/zsh)
PECS_HOST_MODEL="qwen2.5-7b-instruct" pecs-host
```
```powershell
# Windows (PowerShell)
$env:PECS_HOST_MODEL = "qwen2.5-7b-instruct"; pecs-host
```
```bat
:: Windows (cmd.exe)
set PECS_HOST_MODEL=qwen2.5-7b-instruct && pecs-host
```

Se o LM Studio estiver em **outra máquina**, acrescente `PECS_HOST_BASE_URL` (ex.:
`http://192.168.0.10:1234/v1`) da mesma forma.

#### 8. Primeira pergunta

No REPL, pergunte à vontade (ex.: *"Liste 3 PECs de 2023"*, *"Quais as votações da PEC
2595897 e como cada bancada orientou?"*). Comandos: `/tools`, `/modelo <nome>`, `/sair`.

#### Problemas comuns

| Sintoma | Causa provável / solução |
|---|---|
| *Não consegui falar com o LM Studio* | Servidor não está ligado (passo 3) ou `PECS_HOST_BASE_URL` errado. Teste o `curl` do passo 4. |
| *model not found* | `PECS_HOST_MODEL` não bate com o `id` do passo 4, ou nenhum modelo carregado. |
| Respostas sem usar ferramentas / loop não conclui | Modelo fraco em *tool-calling*: troque por Qwen2.5/Llama 3.1 com `/modelo <nome>`. |

### Alternativa — Ollama (100% offline)

```bash
curl -fsSL https://ollama.com/install.sh | sh   # instalar (Linux, pode pedir sudo)
ollama pull qwen2.5:7b                           # modelo com suporte a ferramentas
ollama serve &                                   # garantir o serviço no ar
pip install -e ".[host,ollama]"                  # projeto + backend ollama
PECS_HOST_BACKEND=ollama pecs-host               # rodar usando o Ollama
```

### Variáveis de ambiente (host)

- `PECS_HOST_BACKEND` — `lmstudio` (padrão) ou `ollama`.
- `PECS_HOST_MODEL` — nome do modelo (LM Studio: precisa bater com o carregado; Ollama: padrão `qwen2.5:7b`).
- `PECS_HOST_BASE_URL` — endpoint OpenAI-compat do LM Studio (padrão `http://localhost:1234/v1`).
- `PECS_HOST_API_KEY` — chave enviada ao endpoint (padrão `lm-studio`; o LM Studio ignora).
- `OLLAMA_HOST` — endereço do Ollama (padrão `http://localhost:11434`).

## Licença

MIT.
