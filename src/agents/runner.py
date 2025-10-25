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
from src.tools.python_repl import PythonRunnerTool

runner = Agent(
    role="Runner",
    goal="Executar scripts em sandbox, capturar stdout/stderr e registrar artefatos.",
    verbose=True,
    tools=[PythonRunnerTool()],
)
