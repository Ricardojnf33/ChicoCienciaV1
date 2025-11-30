import typer
from typing import Optional
import structlog
import uuid
from pathlib import Path
import json
from src.crews.ai_scientist_v2 import build_crew
from src.processes.ats_process import run_agentic_tree
from src.core.tree import AgenticTree
from src.config.logging_config import configure_logging

app = typer.Typer(help="AI Scientist v2 — CLI")

@app.command()
def init(objective: str, budget: int = 10, out_dir: str = "runs", verbose: bool = False):
    configure_logging(verbose=verbose)
    log = structlog.get_logger()
    run_id = str(uuid.uuid4())[:8]
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    crew = build_crew()
    tree = AgenticTree.new(objective_yaml=objective)
    log.info("init.start", objective=objective, budget=budget, run_id=run_id)
    run_agentic_tree(crew, tree, budget=budget, checkpoint_path=f"{out_dir}/{run_id}.json")
    tree.save_json(f"{out_dir}/{run_id}.json")
    log.info("init.done", run_id=run_id, out=f"{out_dir}/{run_id}.json")
    typer.echo("Run finalizado. Confira a pasta 'experiments/'.")

@app.command()
def resume(run_id: str, out_dir: str = "runs", budget: int = 5, verbose: bool = False):
    configure_logging(verbose=verbose)
    log = structlog.get_logger()
    path = f"{out_dir}/{run_id}.json"
    tree = AgenticTree.load_json(path)
    crew = build_crew()
    log.info("resume.start", run_id=run_id, budget=budget)
    run_agentic_tree(crew, tree, budget=budget, checkpoint_path=path)
    tree.save_json(path)
    log.info("resume.done", run_id=run_id)

@app.command()
def inspect(run_id: str, out_dir: str = "runs", limit: int = 20):
    path = f"{out_dir}/{run_id}.json"
    obj = json.loads(Path(path).read_text())
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
    path = f"{out_dir}/{run_id}.json"
    obj = json.loads(Path(path).read_text())
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

if __name__ == "__main__":
    app()
