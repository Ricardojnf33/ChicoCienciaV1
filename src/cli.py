import typer
import structlog
import uuid
from pathlib import Path
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
def inspect(run_id: str, out_dir: str = "runs", show_frontier: bool = True):
    path = f"{out_dir}/{run_id}.json"
    data = Path(path).read_text()
    typer.echo(data)

if __name__ == "__main__":
    app()
