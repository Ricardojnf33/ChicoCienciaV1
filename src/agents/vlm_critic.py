from crewai import Agent
from src.tools.plotting import PlotTool

vlm_critic = Agent(
    role="VLM Critic",
    goal="Revisar figuras e checar alinhamento com descrições; classificar BUG/NON_BUG.",
    verbose=True,
    tools=[PlotTool()],
)
