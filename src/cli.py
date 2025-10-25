import typer
import structlog
import uuid
from pathlib import Path
import json
from src.crews.ai_scientist_v2 import build_crew
from src.processes.ats_process import run_agentic_tree
from src.core.tree import AgenticTree

app = typer.Typer(help="AI Scientist v2 — CLI")

@app.command()
def init(objective: str, budget: int = 10, out_dir: str = "runs"):
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),
    )
    log = structlog.get_logger()
    run_id = str(uuid.uuid4())[:8]
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    crew = build_crew()
    tree = AgenticTree.new(objective_yaml=objective)
    log.info("init.start", objective=objective, budget=budget, run_id=run_id)
    run_agentic_tree(crew, tree, budget=budget)
    tree.save_json(f"{out_dir}/{run_id}.json")
    log.info("init.done", run_id=run_id, out=f"{out_dir}/{run_id}.json")
    typer.echo("Run finalizado. Confira a pasta 'experiments/'.")

@app.command()
def resume(run_id: str, out_dir: str = "runs", budget: int = 5):
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),
    )
    log = structlog.get_logger()
    path = f"{out_dir}/{run_id}.json"
    tree = AgenticTree.load_json(path)
    crew = build_crew()
    log.info("resume.start", run_id=run_id, budget=budget)
    run_agentic_tree(crew, tree, budget=budget)
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

if __name__ == "__main__":
    app()
