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
    from src.tools.crewai_adapters import LiteratureTool
except ImportError:
    from src.tools.literature import LiteratureTool

researcher = Agent(
    role="Researcher",
    goal="Gerar hipóteses e planos experimentais com revisão de literatura e novidade.",
    backstory="Pesquisador experiente em revisão de literatura científica e formulação de hipóteses testáveis.",
    verbose=True,
    tools=[LiteratureTool()],
)
