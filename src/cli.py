import typer
import structlog
from src.crews.ai_scientist_v2 import build_crew
from src.processes.ats_process import run_agentic_tree
from src.core.tree import AgenticTree

app = typer.Typer(help="AI Scientist v2 — CLI")

@app.command()
def init(objective: str, budget: int = 10):
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),
    )
    log = structlog.get_logger()
    crew = build_crew()
    tree = AgenticTree.new(objective_yaml=objective)
    log.info("init.start", objective=objective, budget=budget)
    run_agentic_tree(crew, tree, budget=budget)
    log.info("init.done")
    typer.echo("Run finalizado. Confira a pasta 'experiments/'.")

@app.command()
def resume(run_id: str):
    typer.echo("Resume não implementado no boilerplate.")

@app.command()
def inspect(run_id: str, tree_view: bool = True):
    typer.echo("Inspect não implementado no boilerplate.")

if __name__ == "__main__":
    app()
