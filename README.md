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

- Specialized agent definitions for management, research, coding, review, data stewardship, ethics, and visual critique.
- Tree selection using a UCT-style policy, node expansion, score propagation, and early stopping.
- Structured hypothesis and experiment-plan contracts with distinct, bounded expansion.
- Comparable B1, A, and A0 policies plus a single-command comparison manifest.
- Reviewer and VLM evidence contracts with explicit `NOT_EVALUATED` state.
- CLI commands for `init`, `resume`, `inspect`, and `report`.
- Atomic JSON checkpoints, durable attempt manifests, and a reconstructible SQLite projection.
- ArXiv and Semantic Scholar clients with fallback behavior.
- Experiment artifact directories containing code, JSON results, figures, and reports.
- Dry-run execution that exercises orchestration without an OpenAI API key.
- A fail-closed live runner with network namespace, restricted filesystem, resource limits, sanitized environment, process-group timeout, and independent evidence.
- Test modules covering dry-run behavior, contracts, recovery, runner boundaries, scoring, tree persistence, and global rate limiting.
- Optional Weights & Biases instrumentation for non-dry runs.

## Current validation status

| Area | Current state |
|---|---|
| Python source syntax | Compiles successfully |
| Dry-run path | Implemented; generates synthetic experiment results |
| Tree persistence | Atomic JSON plus idempotent recovery; SQLite is rebuilt as a projection |
| CLI `resume` and `inspect` | Implemented |
| External literature clients | Implemented with fallbacks; availability depends on external services |
| Live multi-agent experiment | Fail-closed runner implemented; compatible sandbox host and end-to-end scientific validation still required |
| Agent evaluation | Explicit and hashed; mock runs remain `NOT_EVALUATED` |
| Scientific validity | Not validated |
| Production readiness | Not production-ready |

## Important limitations

- When `OPENAI_API_KEY` is absent, the workflow creates a synthetic `results.json` with an example accuracy value. These values are orchestration fixtures, not experimental findings.
- Live mode rejects missing, invalid or hash-divergent evidence and never substitutes a synthetic result.
- Reviewer/VLM decisions affect scoring only when represented by their explicit contracts; mock runs record `NOT_EVALUATED` and are not approvals.
- Generated Python runs only when Bubblewrap can isolate network and filesystem. This narrows risk but is not an absolute security guarantee against hostile code or kernel vulnerabilities.
- Reports are lightweight templates and should not be treated as scientific papers.
- No benchmark currently demonstrates scientific novelty, reproducibility, or superiority over a conventional workflow.
- No live LLM experiment or positive sandbox run has yet been recorded for Phase 3; this development host denies user namespaces and the runner correctly fails closed.

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

- Python 3.11 (the lock currently excludes 3.12+)
- Poetry
- Linux `bwrap` and `prlimit` for live generated-code execution
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
poetry run python -m src.cli compare objective.example.yaml --mode mock --budget 8
```

## Development priorities

1. Run the sandbox preflight and smoke test on a compatible Linux host.
2. Materialize B0 and the dataset/seed campaign matrix.
3. Validate literature provenance and attach citations to generated claims.
4. Approve token and monetary caps before any LLM-backed pilot.
5. Execute six pilots before freezing the empirical protocol.
6. Collect the main comparison and prepare the independent reproduction.

## License

MIT. See [`LICENSE`](LICENSE).
