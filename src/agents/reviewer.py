from crewai import Agent
from src.tools.plotting import PlotTool
from src.tools.literature import LiteratureTool

reviewer = Agent(
    role="Reviewer",
    goal=("Avaliar resultados, reportar negativos, verificar coerência com hipóteses e sugerir próximos passos."),
    verbose=True,
    tools=[PlotTool(), LiteratureTool()],
)
