from crewai import Agent
from src.tools.literature import LiteratureTool

manager = Agent(
    role="Experiment Progress Manager",
    goal=("Orquestrar descoberta científica em 4 estágios; "
          "definir orçamento e critérios; selecionar/expandir nós."),
    backstory="Gerente metódico, prioriza clareza, reprodutibilidade e ética.",
    allow_delegation=True,
    verbose=True,
    tools=[LiteratureTool()],
)
