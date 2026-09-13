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
try:
    from src.tools.crewai_adapters import DatasetTool, PlotTool
except ImportError:
    from src.tools.datasets import DatasetTool
    from src.tools.plotting import PlotTool

coder = Agent(
    role="Coder",
    goal=("Converter planos em código reprodutível sem executá-lo; salvar code.py e "
          "raw_results.json apenas quando o executor controlado rodar o script."),
    backstory="Desenvolvedor Python experiente em ciência de dados, focado em código limpo e reprodutível.",
    verbose=True,
    tools=[DatasetTool(), PlotTool()],
)
