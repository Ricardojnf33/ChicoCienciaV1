import typer
from typing import Optional
from enum import Enum
import structlog
import uuid
from pathlib import Path
import json
from src.core.contracts import (
    RunManifest,
    adapt_legacy_result,
    load_manifest,
    save_manifest,
    write_result,
)
from src.processes.ats_process import ExecutionMode, run_agentic_tree
from src.processes.comparison_process import run_variant_comparison
from src.core.tree import AgenticTree
from src.config.logging_config import configure_logging
from src.config.settings import Settings
from src.core.variants import ExperimentVariant, policy_for

app = typer.Typer(help="AI Scientist v2 — CLI")


class LegacyReduction(str, Enum):
    SCALAR = "scalar"
    MAX = "max"
    MEAN = "mean"


def _run_paths(out_dir: str, run_id: str) -> tuple[Path, Path, Path]:
    run_dir = Path(out_dir) / run_id
    return run_dir, run_dir / "tree.json", run_dir / "manifest.json"


def _existing_tree_path(out_dir: str, run_id: str) -> Path:
    _, current, _ = _run_paths(out_dir, run_id)
    legacy = Path(out_dir) / f"{run_id}.json"
    return current if current.is_file() else legacy


@app.command()
def init(
    objective: str,
    budget: int = 10,
    out_dir: str = "runs",
    mode: ExecutionMode = ExecutionMode.MOCK,
    variant: ExperimentVariant = ExperimentVariant.A,
    branching: int = 2,
    max_depth: int = 4,
    max_branching: int = 3,
    verbose: bool = False,
):
    configure_logging(verbose=verbose)
    log = structlog.get_logger()
    run_id = str(uuid.uuid4())[:8]
    run_dir, tree_path, manifest_path = _run_paths(out_dir, run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    crew = None
    if mode is ExecutionMode.LIVE:
        from src.crews.ai_scientist_v2 import build_crew

        crew = build_crew(Settings())
    artifact_root = run_dir / "artifacts"
    policy = policy_for(variant)
    effective_branching = policy.effective_branching(branching)
    tree = AgenticTree.new(
        objective_yaml=objective,
        artifact_root=str(artifact_root),
        max_depth=max_depth,
        max_branching=max_branching,
    )
    manifest = RunManifest(
        run_id=run_id,
        objective_path=objective,
        primary_metric=tree.primary_metric,
        variant=variant.value,
        budget=budget,
        branching=branching,
        effective_branching=effective_branching,
        max_depth=max_depth,
        automatic_correction=policy.automatic_correction,
    )
    save_manifest(manifest_path, manifest)
    log.info("init.start", objective=objective, budget=budget, run_id=run_id)
    try:
        run_agentic_tree(
            crew,
            tree,
            budget=budget,
            checkpoint_path=str(tree_path),
            mode=mode,
            sqlite_url=f"sqlite:///{run_dir / 'run.db'}",
            manifest=manifest,
            manifest_path=str(manifest_path),
            branching=branching,
            variant=variant,
        )
    except Exception:
        manifest.status = "FAILED"
        save_manifest(manifest_path, manifest)
        raise
    tree.save_json(str(tree_path))
    log.info("init.done", run_id=run_id, out=str(tree_path))
    typer.echo(f"Run finalizado. Artefatos em: {artifact_root}")

@app.command()
def resume(
    run_id: str,
    out_dir: str = "runs",
    budget: int = 5,
    mode: ExecutionMode = ExecutionMode.MOCK,
    variant: Optional[ExperimentVariant] = None,
    verbose: bool = False,
):
    configure_logging(verbose=verbose)
    log = structlog.get_logger()
    run_dir, _, manifest_path = _run_paths(out_dir, run_id)
    tree_path = _existing_tree_path(out_dir, run_id)
    tree = AgenticTree.load_json(str(tree_path))
    if manifest_path.is_file():
        manifest = load_manifest(manifest_path)
    else:
        manifest = RunManifest(
            run_id=run_id,
            objective_path=f"legacy:{tree_path}",
            primary_metric=tree.primary_metric,
        )
        save_manifest(manifest_path, manifest)
    selected_variant = variant or ExperimentVariant(manifest.variant)
    crew = None
    if mode is ExecutionMode.LIVE:
        from src.crews.ai_scientist_v2 import build_crew

        crew = build_crew(Settings())
    log.info("resume.start", run_id=run_id, budget=budget)
    run_agentic_tree(
        crew,
        tree,
        budget=budget,
        checkpoint_path=str(tree_path),
        mode=mode,
        sqlite_url=f"sqlite:///{run_dir / 'run.db'}",
        manifest=manifest,
        manifest_path=str(manifest_path),
        branching=manifest.branching,
        variant=selected_variant,
    )
    tree.save_json(str(tree_path))
    log.info("resume.done", run_id=run_id)


@app.command()
def compare(
    objective: str,
    out_dir: str = "runs/comparisons",
    budget: int = 8,
    mode: ExecutionMode = ExecutionMode.MOCK,
    branching: int = 2,
    max_depth: int = 3,
    max_branching: int = 3,
):
    """Executa B1, A e A0 com objetivo, ferramentas e limites compartilhados."""
    crew_factory = None
    if mode is ExecutionMode.LIVE:
        from src.crews.ai_scientist_v2 import build_crew

        settings = Settings()

        def configured_crew_factory():
            return build_crew(settings)

        crew_factory = configured_crew_factory
    comparison, path = run_variant_comparison(
        objective,
        out_dir,
        budget=budget,
        branching=branching,
        max_depth=max_depth,
        max_branching=max_branching,
        mode=mode,
        crew_factory=crew_factory,
    )
    typer.echo(
        f"Comparação {comparison.campaign_id} concluída. Manifesto: {path}"
    )

@app.command()
def inspect(run_id: str, out_dir: str = "runs", limit: int = 20):
    path = _existing_tree_path(out_dir, run_id)
    obj = json.loads(path.read_text())
    nodes = obj.get("nodes", [])
    frontier = set(obj.get("frontier", []))
    # Ordena por score desc, visits desc
    nodes_sorted = sorted(nodes, key=lambda n: (n.get("score") or 0.0, n.get("visits", 0)), reverse=True)
    header = f"{'id':8}  {'stage':14}  {'score':7}  {'visits':6}  {'status':10}  {'frontier':8}  prompt"
    typer.echo(header)
    typer.echo("-" * len(header))
    for n in nodes_sorted[:limit]:
        line = f"{n['id'][:8]:8}  {str(n['stage']):14}  {str(n.get('score')):7}  {str(n.get('visits',0)):6}  {n.get('status',''):10}  {('yes' if n['id'] in frontier else 'no'):8}  {n.get('prompt','')[:60]}"
        typer.echo(line)
    typer.echo("")
    best = nodes_sorted[0] if nodes_sorted else None
    if best:
        typer.echo(f"Best: id={best['id']} score={best.get('score')} stage={best['stage']}")


@app.command()
def report(run_id: str, out_dir: str = "runs", out_md: Optional[str] = None):
    path = _existing_tree_path(out_dir, run_id)
    obj = json.loads(path.read_text())
    nodes = obj.get("nodes", [])
    nodes_sorted = sorted(nodes, key=lambda n: (n.get("score") or 0.0, n.get("visits", 0)), reverse=True)
    best = nodes_sorted[0] if nodes_sorted else None
    title = obj.get("objective", {}).get("title", f"Run {run_id}")
    lines = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append("## Introdução")
    lines.append("Baseado na consulta de literatura e objetivo fornecidos.")
    lines.append("")
    lines.append("## Método")
    lines.append(f"Datasets: {obj.get('objective', {}).get('datasets', [])}")
    lines.append(f"Métrica primária: {obj.get('primary_metric', 'accuracy')}")
    lines.append("")
    lines.append("## Resultados")
    if best:
        lines.append(f"Melhor nó: `{best['id']}` | score: {best.get('score')} | stage: {best.get('stage')}")
        if best.get("results_path"):
            lines.append(f"Resultados: `{best['results_path']}`")
    else:
        lines.append("Sem nós disponíveis.")
    lines.append("")
    lines.append("## Discussão")
    lines.append("Interpretação dos ganhos e limitações.")
    lines.append("")
    md = "\n".join(lines)
    if out_md is None:
        out_md = f"{out_dir}/{run_id}.md"
    Path(out_md).write_text(md)
    typer.echo(f"Relatório gerado em: {out_md}")


@app.command()
def replay(
    result_path: str,
    primary_metric: str,
    metric_path: str,
    out_path: str = "canonical-results.json",
    node_id: str = "legacy",
    attempt: int = 1,
    reduction: LegacyReduction = LegacyReduction.SCALAR,
):
    """Adapta um resultado histórico sem alterar o arquivo de origem."""
    result = adapt_legacy_result(
        result_path,
        node_id=node_id,
        attempt=attempt,
        mode="replay",
        primary_metric=primary_metric,
        metric_path=metric_path,
        reduction=reduction.value,
    )
    written = write_result(out_path, result)
    typer.echo(f"Resultado canônico de replay: {written}")

if __name__ == "__main__":
    app()
