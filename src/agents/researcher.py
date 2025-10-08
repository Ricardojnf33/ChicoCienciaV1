from crewai import Agent
from src.tools.literature import LiteratureTool

researcher = Agent(
    role="Researcher",
    goal="Gerar hipóteses e planos experimentais com revisão de literatura e novidade.",
    verbose=True,
    tools=[LiteratureTool()],
)
