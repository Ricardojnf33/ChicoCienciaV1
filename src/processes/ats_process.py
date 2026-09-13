import json
import time
from enum import Enum
from pathlib import Path
from typing import Any

import structlog

from src.config.settings import Settings
from src.core.contracts import (
    AttemptRecord,
    CanonicalResult,
    ExecutionEvidence,
    RunManifest,
    canonicalize_attempt,
    file_sha256,
    save_manifest,
    utc_now,
    write_result,
)
from src.core.enums import ExecStatus
from src.core.persistence import NodeRow, init_db, upsert_node
from src.core.tree import AgenticTree
from src.prompts.stages import build_prompt, next_stage


class ExecutionMode(str, Enum):
    MOCK = "mock"
    LIVE = "live"


def _node_row(node) -> NodeRow:
    return NodeRow(
        id=node.id,
        parent_id=node.parent_id,
        type=node.type.name,
        stage=node.stage.value,
        prompt=node.prompt,
        plan=node.plan,
        code_path=node.code_path,
        results_path=node.results_path,
        figs_paths=json.dumps(node.figs_paths) if node.figs_paths else None,
        score=node.score,
        visits=node.visits,
        value_sum=node.value_sum,
        status=node.status.name,
        meta=json.dumps(node.meta) if node.meta else None,
    )


def _agent_by_role(crew: Any, role: str):
    return next(
        agent
        for agent in crew.agents
        if getattr(agent, "role", "").lower() == role.lower()
    )


def _mock_result(
    attempt_dir: Path,
    *,
    node_id: str,
    attempt: int,
    primary_metric: str,
) -> Path:
    return write_result(
        attempt_dir / "results.json",
        CanonicalResult(
            node_id=node_id,
            attempt=attempt,
            status="SUCCEEDED",
            primary_metric=primary_metric,
            metrics={primary_metric: 0.5},
            execution=ExecutionEvidence(
                mode="mock",
                synthetic=True,
                network_used=False,
                return_code=0,
            ),
        ),
    )


def _run_live_attempt(
    crew: Any,
    node,
    prompt: str,
    branching: int,
    attempt_dir: Path,
    attempt: int,
) -> Path:
    from crewai import Task

    researcher = _agent_by_role(crew, "Researcher")
    coder = _agent_by_role(crew, "Coder")
    runner = _agent_by_role(crew, "Runner")
    expected_code = attempt_dir / "code.py"
    raw_result = attempt_dir / "raw_results.json"
    execution_evidence = attempt_dir / "execution.json"
    tasks = []
    if attempt == 1:
        tasks.append(
            Task(
                agent=researcher,
                description=(
                    f"{prompt}\nGere {branching} hipóteses/planos para o nó {node.id}."
                ),
                expected_output="Lista de hipóteses testáveis com revisão de literatura",
            )
        )
    tasks.extend(
        [
            Task(
                agent=coder,
                description=(
                    f"Implementar o plano do nó {node.id}. Salvar o código em {expected_code} "
                    f"e a métrica primária escalar no topo de {raw_result}."
                ),
                expected_output="Código e raw_results.json nos caminhos declarados",
            ),
            Task(
                agent=runner,
                description=(
                    f"Executar {expected_code}. Salvar em {execution_evidence} um JSON com "
                    "mode='live', synthetic=false, network_used conforme observado e "
                    "return_code inteiro do processo."
                ),
                expected_output="execution.json com o retorno real do processo",
            ),
        ]
    )
    crew.tasks = tasks
    crew.kickoff()
    return canonicalize_attempt(
        attempt_dir,
        node_id=node.id,
        attempt=attempt,
        mode="live",
        primary_metric=node.meta["primary_metric"],
    )


def _save_attempt(
    manifest: RunManifest | None,
    manifest_path: str | None,
    record: AttemptRecord,
) -> None:
    if manifest is None:
        return
    key = (record.node_id, record.attempt)
    for index, current in enumerate(manifest.attempts):
        if (current.node_id, current.attempt) == key:
            manifest.attempts[index] = record
            break
    else:
        manifest.attempts.append(record)
    validated = RunManifest.model_validate(manifest.model_dump())
    manifest.attempts = validated.attempts
    if manifest_path:
        save_manifest(manifest_path, manifest)


def run_agentic_tree(
    crew: Any,
    tree: AgenticTree,
    budget: int,
    branching: int = 2,
    checkpoint_path: str | None = None,
    *,
    mode: ExecutionMode = ExecutionMode.MOCK,
    sqlite_url: str | None = None,
    manifest: RunManifest | None = None,
    manifest_path: str | None = None,
) -> None:
    settings = Settings()
    mode = ExecutionMode(mode)
    if mode is ExecutionMode.LIVE and crew is None:
        raise ValueError("O modo live requer uma Crew configurada.")
    if mode is ExecutionMode.LIVE and not (settings.OPENAI_API_KEY or "").strip():
        raise ValueError("O modo live requer OPENAI_API_KEY não vazia.")

    log = structlog.get_logger()
    log.info("ats.start", mode=mode.value, budget=budget)
    engine = init_db(sqlite_url or settings.SQLITE_URL)
    if manifest is not None:
        manifest.status = "RUNNING"
        if manifest_path:
            save_manifest(manifest_path, manifest)

    wandb_run = False
    if settings.WANDB_ON and mode is ExecutionMode.LIVE:
        import wandb

        wandb.init(
            project=settings.WANDB_PROJECT,
            config={
                "budget": budget,
                "branching": branching,
                "model_text": settings.MODEL_TEXT,
                "model_vision": settings.MODEL_VISION,
                "objective": tree.objective.get("objective", {}).get("title", "Unknown"),
            },
        )
        wandb_run = True

    for iteration in range(budget):
        iteration_start = time.time()
        node = tree.select()
        node.status = ExecStatus.RUNNING
        upsert_node(engine, _node_row(node))
        prompt = build_prompt(node.stage, objective_json=node.prompt)
        log.info(
            "ats.iter.start",
            iteration=iteration + 1,
            node_id=node.id,
            stage=node.stage.name,
        )

        node.meta["primary_metric"] = tree.primary_metric
        max_attempts = 1 if mode is ExecutionMode.MOCK else 3
        result_path = None
        for attempt in range(1, max_attempts + 1):
            attempt_dir = tree.artifact_root / node.id / f"attempt-{attempt}"
            attempt_dir.mkdir(parents=True, exist_ok=True)
            started_at = utc_now()
            _save_attempt(
                manifest,
                manifest_path,
                AttemptRecord(
                    node_id=node.id,
                    attempt=attempt,
                    mode=mode.value,
                    status="RUNNING",
                    directory=str(attempt_dir),
                    started_at=started_at,
                ),
            )
            try:
                if mode is ExecutionMode.MOCK:
                    result_path = _mock_result(
                        attempt_dir,
                        node_id=node.id,
                        attempt=attempt,
                        primary_metric=tree.primary_metric,
                    )
                else:
                    result_path = _run_live_attempt(
                        crew,
                        node,
                        prompt,
                        branching,
                        attempt_dir,
                        attempt,
                    )
                _save_attempt(
                    manifest,
                    manifest_path,
                    AttemptRecord(
                        node_id=node.id,
                        attempt=attempt,
                        mode=mode.value,
                        status="SUCCEEDED",
                        directory=str(attempt_dir),
                        result_path=str(result_path),
                        result_sha256=file_sha256(result_path),
                        started_at=started_at,
                        finished_at=utc_now(),
                    ),
                )
                break
            except Exception as exc:
                _save_attempt(
                    manifest,
                    manifest_path,
                    AttemptRecord(
                        node_id=node.id,
                        attempt=attempt,
                        mode=mode.value,
                        status="FAILED",
                        directory=str(attempt_dir),
                        error=str(exc),
                        started_at=started_at,
                        finished_at=utc_now(),
                    ),
                )
                log.warning(
                    "ats.attempt.failed",
                    node_id=node.id,
                    attempt=attempt,
                    error=str(exc),
                )
                if attempt == max_attempts:
                    node.status = ExecStatus.FAILED
                    upsert_node(engine, _node_row(node))
                    if checkpoint_path:
                        tree.save_json(checkpoint_path)
                    if manifest is not None:
                        manifest.status = "FAILED"
                        if manifest_path:
                            save_manifest(manifest_path, manifest)
                    raise

        if result_path is None:
            raise RuntimeError("Tentativa terminou sem resultado validado.")
        node.status = ExecStatus.SUCCEEDED
        node.meta.update(
            {
                "execution_mode": mode.value,
                "synthetic": mode is ExecutionMode.MOCK,
                "vlm_evaluated": False,
            }
        )
        tree.update_result(node.id, str(result_path), vlm_ok=False)

        score = tree.nodes[node.id].score or 0.0
        tree.backpropagate(tree.nodes[node.id], score)
        upsert_node(engine, _node_row(tree.nodes[node.id]))

        child_ids = tree.expand(tree.nodes[node.id], k=branching)
        for child_id in child_ids:
            child = tree.nodes[child_id]
            child.stage = next_stage(child.stage)
            upsert_node(engine, _node_row(child))

        if checkpoint_path:
            tree.save_json(checkpoint_path)
            log.info("ats.checkpoint.saved", path=checkpoint_path)

        duration = time.time() - iteration_start
        log.info("ats.iter.scored", node_id=node.id, score=score, duration=duration)
        if wandb_run:
            import wandb

            wandb.log(
                {
                    "iteration": iteration + 1,
                    "node_id": node.id,
                    "score": score,
                    "duration": duration,
                }
            )
        if tree.should_early_stop(threshold=tree.settings.EARLY_STOP_SCORE):
            log.info("ats.early_stop", score=score)
            break

    if wandb_run:
        import wandb

        wandb.finish()
    if manifest is not None:
        manifest.status = "SUCCEEDED"
        if manifest_path:
            save_manifest(manifest_path, manifest)
