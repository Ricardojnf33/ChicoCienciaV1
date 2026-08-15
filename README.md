# Chico Ciência

**Experimental agentic research Proof of Concept (PoC)**

> [!IMPORTANT]
> This repository is an exploratory engineering prototype. It is **not** a production system, an autonomous scientist, or evidence that the generated experiments produce novel or scientifically valid findings. The most reproducible path currently implemented is the dry-run orchestration flow.

## Purpose

Chico Ciência explores how a multi-agent workflow can organize parts of a machine-learning research cycle: literature retrieval, hypothesis planning, code generation, experiment execution, result scoring, review, and iterative search.

The project combines CrewAI-style agent orchestration with an `AgenticTree` that selects and expands candidate experiment nodes across four stages:

1. `PRELIM`
2. `TUNING`
3. `RESEARCH_GRADE`
4. `ABLATIONS`

## What is implemented

- Specialized agent definitions for management, research, coding, execution, review, data stewardship, ethics, and visual critique.
- Tree selection using a UCT-style policy, node expansion, score propagation, and early stopping.
- CLI commands for `init`, `resume`, `inspect`, and `report`.
- JSON checkpoints and partial SQLite persistence.
- ArXiv and Semantic Scholar clients with fallback behavior.
- Experiment artifact directories containing code, JSON results, figures, and reports.
- Dry-run execution that exercises orchestration without an OpenAI API key.
- Test modules covering dry-run behavior, scoring, tree persistence, and rate limiting.
- Optional Weights & Biases instrumentation for non-dry runs.

## Current validation status

| Area | Current state |
|---|---|
| Python source syntax | Compiles successfully |
| Dry-run path | Implemented; generates synthetic experiment results |
| Tree persistence | Implemented in JSON; SQLite integration is partial |
| CLI `resume` and `inspect` | Implemented |
| External literature clients | Implemented with fallbacks; availability depends on external services |
| Live multi-agent experiment | Experimental; not established as reproducible end to end |
| Scientific validity | Not validated |
| Production readiness | Not production-ready |

## Important limitations

- When `OPENAI_API_KEY` is absent, the workflow creates a synthetic `results.json` with an example accuracy value. These values are orchestration fixtures, not experimental findings.
- In the current real-mode path, a missing result artifact can also trigger a synthetic fallback. A completed run therefore does not by itself prove that a real experiment was executed successfully.
- Visual-critic consistency is currently passed into scoring as a default value; it is not yet a fully verified evaluation signal.
- Generated Python execution is prototype-level and is not a hardened sandbox for untrusted code.
- Reports are lightweight templates and should not be treated as scientific papers.
- No benchmark currently demonstrates scientific novelty, reproducibility, or superiority over a conventional workflow.
- Automated tests exist, but no CI workflow currently publishes their status on each commit.

## Repository structure

```text
src/
  agents/       Agent definitions
  clients/      ArXiv and Semantic Scholar clients
  config/       Settings and logging
  core/         Tree, node, persistence, and scoring logic
  crews/        Crew construction
  processes/    Agentic-tree execution
  prompts/      Stage prompts and progression
  tools/        Datasets, metrics, literature, plotting, and Python execution
experiments/    Generated experiment artifacts
runs/           Saved run checkpoints
reports/        Technical and evaluation reports
tests/          Automated test modules
```

## Requirements

- Python 3.11+
- Poetry
- Optional API keys for live external integrations

## Installation

```bash
poetry install
cp .env.example .env
```

Do not commit API keys. Configure them only in your local `.env` or a secrets manager.

## Run the reproducible dry-run path

Leave `OPENAI_API_KEY` unset and run:

```bash
poetry run python -m src.cli init objective.example.yaml --budget 3
```

The command creates a run checkpoint and synthetic artifacts that can be used to inspect the orchestration flow.

## Other CLI commands

```bash
poetry run python -m src.cli resume <run_id> --budget 3
poetry run python -m src.cli inspect <run_id>
poetry run python -m src.cli report <run_id>
```

## Development priorities

1. Separate synthetic fixtures from real experiment results at the schema level.
2. Fail closed when a live run does not produce the expected artifacts.
3. Add hardened isolation for generated code.
4. Add end-to-end tests and CI with a deterministic mock-LLM path.
5. Validate literature provenance and attach citations to each generated claim.
6. Implement reproducible evaluation datasets, baselines, ablations, and run manifests.
7. Evaluate the system against a conventional non-agentic research workflow.

## License

MIT. See [`LICENSE`](LICENSE).

