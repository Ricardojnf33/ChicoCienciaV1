from crewai import Agent
from src.tools.python_repl import PythonRunnerTool

runner = Agent(
    role="Runner",
    goal="Executar scripts em sandbox, capturar stdout/stderr e registrar artefatos.",
    verbose=True,
    tools=[PythonRunnerTool()],
)
