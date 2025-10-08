from crewai import Agent
from src.tools.datasets import DatasetTool
from src.tools.python_repl import PythonRunnerTool
from src.tools.plotting import PlotTool

coder = Agent(
    role="Coder",
    goal=("Converter planos em código executável reprodutível, sem copiar templates humanos; "
          "salvar results.json e figuras."),
    verbose=True,
    tools=[DatasetTool(), PythonRunnerTool(), PlotTool()],
)
