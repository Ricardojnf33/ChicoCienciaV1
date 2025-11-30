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
    from src.tools.crewai_adapters import DatasetTool, PythonRunnerTool, PlotTool
    from crewai_tools import FileReadTool, FileWriterTool
except ImportError:
    from src.tools.datasets import DatasetTool
    from src.tools.python_repl import PythonRunnerTool
    from src.tools.plotting import PlotTool
    # Fallback stubs if crewai_tools missing (dry run)
    class FileReadTool: pass
    class FileWriterTool: pass

coder = Agent(
    role="Coder",
    goal=("Converter planos em código executável reprodutível, sem copiar templates humanos; "
          "salvar results.json e figuras."),
    backstory="Desenvolvedor Python experiente em ciência de dados, focado em código limpo e reprodutível.",
    verbose=True,
    tools=[DatasetTool(), PythonRunnerTool(), PlotTool(), FileReadTool(), FileWriterTool()],
)
