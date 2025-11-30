try:
    from crewai import Agent
except Exception:
    class Agent:  # minimal stub for dry-run
        def __init__(self, role: str, goal: str, backstory: str | None = None,
                     allow_delegation: bool = False, verbose: bool = False, tools=None, name: str | None = None):
            self.role = role
            self.goal = goal
            self.backstory = backstory
            self.allow_delegation = allow_delegation
            self.verbose = verbose
            self.tools = tools or []
            self.name = name
try:
    from src.tools.crewai_adapters import LiteratureTool
except ImportError:
    from src.tools.literature import LiteratureTool

manager = Agent(
    role="Experiment Progress Manager",
    goal=("Orquestrar descoberta científica em 4 estágios; "
          "definir orçamento e critérios; selecionar/expandir nós."),
    backstory="Gerente metódico, prioriza clareza, reprodutibilidade e ética.",
    allow_delegation=True,
    verbose=True,
    tools=[],  # Manager não pode ter tools em processo hierárquico
)
