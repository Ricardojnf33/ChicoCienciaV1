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
    from src.tools.crewai_adapters import PythonRunnerTool
    from crewai_tools import FileReadTool, FileWriterTool
except ImportError:
    from src.tools.python_repl import PythonRunnerTool
    # Fallback stubs if crewai_tools missing
    class FileReadTool: pass
    class FileWriterTool: pass

runner = Agent(
    role="Runner",
    goal="Executar scripts em sandbox, capturar stdout/stderr e registrar artefatos.",
    backstory="Especialista em execução segura de código Python em ambientes isolados.",
    verbose=True,
    tools=[PythonRunnerTool(), FileReadTool(), FileWriterTool()],
)
