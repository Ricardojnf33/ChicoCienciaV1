# AI Scientist v2 — Boilerplate (Python + CrewAI)

Este boilerplate recria um sistema de **descoberta científica autônoma** inspirado no mind-map v2,
usando **CrewAI** para orquestração, um **Agentic Tree Search** com 4 estágios e
componentes Reviewer (LLM) + VLM Critic.

## Estrutura

```
ai-scientist-v2/
  src/
    config/            # settings pydantic
    core/              # árvore, nós, scoring, persistência
    agents/            # manager, researcher, coder, runner, reviewer, vlm, etc
    tools/             # datasets, plotting, runner, metrics, literatura
    processes/         # ATS e estágios
    crews/             # montagem do Crew
    cli.py             # CLI Typer
  experiments/         # artefatos dos nós
  runs.db              # SQLite (gerado em runtime)
  .env.example
  objective.example.yaml
```

## Requisitos

- Python 3.11+
- Chaves de API (modelos LLM e VLM) no `.env`.

## Instalação (exemplos)

- **Poetry**:
  ```bash
  poetry install
  poetry run python -m src.cli init objective.example.yaml --budget 10
  ```

- **uv**:
  ```bash
  uv pip install -r <(poetry export -f requirements.txt --without-hashes)
  python -m src.cli init objective.example.yaml --budget 10
  ```

## Novidades do MVP

- Integração de literatura com clientes reais: ArXiv e Semantic Scholar, com fallback.
- Seleção UCT na árvore agentic, com `visits` e `value_sum` e backpropagação até a raiz.
- Templates de prompts por estágio (Prelim, Tuning, Research-Grade, Ablations) e uso no fluxo ATS.
- Persistência SQLModel estendida com métricas de busca e utilitários de export.

### Configuração

Defina variáveis no `.env`:

```
SEMANTIC_SCHOLAR_API_KEY="<sua-chave>"
UCT_C=1.414
EARLY_STOP_SCORE=0.72
```

### Uso

```bash
python -m src.cli init objective.example.yaml --budget 10
```

Os resultados ficam em `experiments/<node_id>/results.json` e as escolhas de nós são feitas via UCT.
