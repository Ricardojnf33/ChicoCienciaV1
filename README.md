# ChicoCienciaV1 — AI Scientist v2 com CrewAI e Agentic Tree Search

Projeto que orquestra um ciclo de descoberta científica autônoma com **CrewAI**, realizando uma busca em árvore orientada por agentes (Agentic Tree Search) em 4 estágios, combinando LLMs e ferramentas clássicas de ciência de dados. Inclui gerência hierárquica de agentes, integração com literatura (ArXiv e Semantic Scholar), execução de código controlada, geração de artefatos/reports e avaliação com métricas e crítica VLM.

## Visão geral

- **Orquestração**: `CrewAI` com processo hierárquico e agentes especializados: `manager`, `researcher`, `coder`, `runner`, `reviewer`, `vlm_critic`.
- **Busca agentic**: árvore `AgenticTree` com seleção tipo UCT, expansão controlada e backpropagação de pontuações.
- **Estágios**: PRELIM → TUNING → RESEARCH_GRADE → ABLATIONS, com prompts dedicados e progressão automática.
- **Literatura**: clientes reais para ArXiv e Semantic Scholar com fallback seguro.
- **Execução**: ferramenta de execução Python isolada, geração de `results.json` e figuras.
- **Métricas**: composição de score final por métrica primária, novidade, robustez e consistência VLM.

## Estrutura do repositório

```
ChicoCienciaV1/
  src/
    cli.py               # CLI Typer para iniciar/gerir execuções
    crews/               # montagem do Crew (build_crew)
    agents/              # manager, researcher, coder, runner, reviewer, vlm_critic
    processes/           # execução do Agentic Tree Search (ATS)
    prompts/             # templates e progressão de estágios
    core/                # árvore, nós, enums, scoring
    tools/               # datasets, execução python, plotting, métricas, literatura
    clients/             # ArXiv e Semantic Scholar
    config/              # Settings (Pydantic Settings)
  experiments/           # artefatos gerados por nó (criado em runtime)
  runs.db                # SQLite (criado em runtime)
  .env.example           # exemplo de variáveis de ambiente
  objective.example.yaml # exemplo de objetivo/brief
  pyproject.toml         # dependências e toolchain
  README.md
```

## Componentes principais

### Crew e agentes

- `src/crews/ai_scientist_v2.py`: monta o `Crew` em processo hierárquico, verbose on.
- `src/agents/manager.py`: orquestra orçamento/critérios e seleção/expansão de nós; usa `LiteratureTool`.
- `src/agents/researcher.py`: gera hipóteses/planos com suporte de literatura.
- `src/agents/coder.py`: converte planos em código reprodutível; usa `DatasetTool`, `PythonRunnerTool`, `PlotTool`.
- `src/agents/runner.py`: executa scripts em sandbox e captura stdout/stderr.
- `src/agents/reviewer.py`: avalia resultados e sugere próximos passos; tem `PlotTool` e `LiteratureTool`.
- `src/agents/vlm_critic.py`: revisa figuras e classifica BUG/NON_BUG.

### Árvore agentic e ATS

- `src/core/tree.py`:
  - `AgenticTree.new(objective_yaml)`: carrega objetivo YAML, define métrica primária e cria nó raiz.
  - `select()`: seleção por UCT com `UCT_C` e smoothing de visitas.
  - `expand(node, k)`: gera filhos com plano autopreenchido e atualiza fronteira.
  - `update_result(node_id, results_path, vlm_ok)`: computa score final e remove da fronteira.
  - `backpropagate(node, score)`: propaga visitas e valores até a raiz.
  - `should_early_stop(threshold)`: decide parada por melhor score.
- `src/processes/ats_process.py`:
  - Constrói `Task`s para cada agente por nó selecionado e chama `crew.kickoff` quando há `OPENAI_API_KEY`.
  - Simula resultados mínimos em modo dry-run (gera `./experiments/<node_id>/results.json` com `accuracy`).
  - Expande filhos e avança o estágio com `prompts.next_stage`.

### Prompts e estágios

- `src/prompts/stages.py`: templates distintos por estágio e função `build_prompt(stage, objective_json)`.
- Progressão: PRELIM → TUNING → RESEARCH_GRADE → ABLATIONS.

### Ferramentas

- `src/tools/literature.py`: integra com Semantic Scholar e ArXiv; tem fallback mock se indisponível.
- `src/tools/datasets.py`: exemplo com `iris` (scikit-learn) e split treinoteste.
- `src/tools/python_repl.py`: executa scripts Python com timeout e captura de logs.
- `src/tools/plotting.py`: salva figura simples e metadata JSON.
- `src/tools/metrics.py`: pipeline simples com `LogisticRegression` e grava `results.json` com `accuracy`.

### Clientes externos

- `src/clients/arxiv_client.py`: consulta ArXiv via `arxiv.Search`.
- `src/clients/semantic_scholar_client.py`: consulta Semantic Scholar via SDK.

### Configuração

- `src/config/settings.py`: carrega variáveis via Pydantic Settings (`.env`), com defaults seguros.
  - Principais: `OPENAI_API_KEY`, `SEMANTIC_SCHOLAR_API_KEY`, `MODEL_TEXT`, `MODEL_VISION`.
  - Parâmetros de busca: `MAX_BRANCHING`, `MAX_DEPTH`, `EARLY_STOP_SCORE`, `UCT_C`.
  - I/O: `DATA_ROOT`, `ARTIFACT_ROOT`, `SQLITE_URL`.

## Requisitos

- Python 3.11+
- Chaves de API (opcional para dry-run; requeridas para uso real dos agentes LLM/VLM):
  - `OPENAI_API_KEY`
  - `SEMANTIC_SCHOLAR_API_KEY`

## Instalação

### Via Poetry

```bash
poetry install
```

### Via pip/uv (alternativa)

```bash
uv pip install -r <(poetry export -f requirements.txt --without-hashes)
```

## Configuração de ambiente

Copie `.env.example` para `.env` e ajuste conforme necessário:

```bash
cp .env.example .env
```

Variáveis relevantes (`.env`):

```
OPENAI_API_KEY="<sua-chave-ou-vazio-para-dry-run>"
SEMANTIC_SCHOLAR_API_KEY="<sua-chave>"
UCT_C=1.414
EARLY_STOP_SCORE=0.72
MODEL_TEXT="gpt-4.1-mini"
MODEL_VISION="gpt-4o-mini"
```

## Uso

### Iniciar uma execução (iniciante)

```bash
python -m src.cli init objective.example.yaml --budget 10
```

O comando:
- constrói o `Crew` (`build_crew`),
- cria a `AgenticTree` a partir do YAML (definindo a métrica primária),
- executa o ciclo ATS por até `budget` iterações (ou até early-stop),
- persiste artefatos em `./experiments/<node_id>/` e resultados em `results.json`.

### Outros comandos

```bash
python -m src.cli resume <run_id>
python -m src.cli inspect <run_id> --tree-view true
```

Observação: `resume` e `inspect` são stubs no boilerplate atual.

## Formato do objective YAML

Um exemplo mínimo está em `objective.example.yaml`. Campos úteis dentro de `objective` incluem `primary_metric` (ex.: `accuracy`). O conteúdo é serializado como prompt inicial para o nó raiz.

## Métrica final (scoring)

`src/core/scoring.py` compõe o score final:

```
final = 0.45*metric(primary) + 0.20*novelty + 0.25*robustness + 0.10*vlm_consistency
```

Parâmetros ajustáveis e heurísticos estão documentados no código e podem ser adaptados ao seu domínio.

## Diretórios e artefatos gerados

- `experiments/<node_id>/results.json`: resultados do nó (ex.: `{ "accuracy": 0.5 }`).
- `experiments/<node_id>/*.png`: figuras salvas pelo `PlotTool` com metadata `*.json`.
- `runs.db`: banco SQLite reservado para persistência futura (não utilizado diretamente neste MVP).

## Desenvolvimento

- Linter: `ruff` (config em `pyproject.toml`).
- Testes: `pytest` (sem testes inclusos no MVP).
- Estilo: Python 3.11, tipagem gradual nas partes principais, foco em clareza.

## Roadmap curto

- Conectar de fato o `crew.kickoff` a tasks dinâmicas por nó, capturando outputs e alimentando `AgenticTree`.
- Persistência completa de nós/execuções em `SQLModel`/`SQLite` (`runs.db`).
- Integração de mais datasets e tarefas (visão/nlp), além de pipelines de métricas.
- Suporte robusto a retomada (`resume`) e inspeção visual (`inspect`).
- Melhorar prompts por estágio e acoplamento de ferramentas contextuais.

## Licença

Defina uma licença adequada (ex.: MIT/Apache-2.0) antes de distribuição pública.

## Créditos

Mantido por `Ricardojnf33`. Inspirado em arquiteturas Agentic Tree Search e orquestração CrewAI.
