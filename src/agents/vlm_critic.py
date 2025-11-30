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
    from src.tools.crewai_adapters import PlotTool
except ImportError:
    from src.tools.plotting import PlotTool

vlm_critic = Agent(
    role="VLM Critic",
    goal="Revisar figuras e checar alinhamento com descrições; classificar BUG/NON_BUG.",
    backstory="Especialista em análise visual usando modelos de visão para validar qualidade de figuras científicas.",
    verbose=True,
    tools=[PlotTool()],
)
