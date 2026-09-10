import json
import time
from enum import Enum
from pathlib import Path
from typing import Any

import structlog

from src.config.settings import Settings
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


def _mock_result(tree: AgenticTree, node_id: str) -> Path:
    result_path = tree.artifact_root / node_id / "results.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(
        json.dumps(
            {
                "accuracy": 0.5,
                "_execution": {
                    "mode": ExecutionMode.MOCK.value,
                    "synthetic": True,
                    "network_used": False,
                },
            },
            indent=2,
        )
    )
    return result_path


def _run_live_tasks(crew: Any, node, prompt: str, branching: int, log) -> Path:
    from crewai import Task

    researcher = _agent_by_role(crew, "Researcher")
    coder = _agent_by_role(crew, "Coder")
    runner = _agent_by_role(crew, "Runner")
    expected_dir = Path("experiments") / node.id
    expected_code = expected_dir / "code.py"
    expected_result = expected_dir / "results.json"

    for attempt in range(3):
        tasks = []
        if attempt == 0:
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
                        f"Implementar o plano do nó {node.id} e salvar o código em "
                        f"{expected_code}."
                    ),
                    expected_output="Caminho do arquivo Python criado",
                ),
                Task(
                    agent=runner,
                    description=(
                        f"Executar {expected_code} e salvar as métricas em {expected_result}."
                    ),
                    expected_output="results.json válido e artefatos gerados",
                ),
            ]
        )
        crew.tasks = tasks
        try:
            crew.kickoff()
        except Exception as exc:
            log.warning("ats.kickoff.error", error=str(exc), attempt=attempt + 1)
        if expected_code.is_file() and expected_result.is_file():
            return expected_result
        log.warning("ats.self_healing.retry", node_id=node.id, attempt=attempt + 1)

    raise RuntimeError(
        f"Execução live falhou: artefatos obrigatórios ausentes para o nó {node.id}"
    )


def run_agentic_tree(
    crew: Any,
    tree: AgenticTree,
    budget: int,
    branching: int = 2,
    checkpoint_path: str | None = None,
    *,
    mode: ExecutionMode = ExecutionMode.MOCK,
    sqlite_url: str | None = None,
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

        try:
            if mode is ExecutionMode.MOCK:
                result_path = _mock_result(tree, node.id)
            else:
                result_path = _run_live_tasks(crew, node, prompt, branching, log)
            node.status = ExecStatus.SUCCEEDED
            node.meta.update(
                {
                    "execution_mode": mode.value,
                    "synthetic": mode is ExecutionMode.MOCK,
                    "vlm_evaluated": False,
                }
            )
            tree.update_result(node.id, str(result_path), vlm_ok=False)
        except Exception:
            node.status = ExecStatus.FAILED
            upsert_node(engine, _node_row(node))
            if checkpoint_path:
                tree.save_json(checkpoint_path)
            raise

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
