try:
    from crewai import Agent
except Exception:
    class Agent:  # minimal stub for dry-run
        def __init__(self, role: str, goal: str, verbose: bool = False, tools=None, name: str | None = None):
            self.role = role
            self.goal = goal
            self.verbose = verbose
            self.tools = tools or []
            self.name = name
from src.tools.plotting import PlotTool
from src.tools.literature import LiteratureTool

reviewer = Agent(
    role="Reviewer",
    goal=("Avaliar resultados, reportar negativos, verificar coerência com hipóteses e sugerir próximos passos."),
    verbose=True,
    tools=[PlotTool(), LiteratureTool()],
)
