from typing import Any

from crewai import Agent

from src.tools.crewai_adapters import PlotTool


def build_vlm_critic(llm: Any) -> Agent:
    return Agent(
        role="VLM Critic",
        goal="Revisar figuras e checar alinhamento com descrições; classificar BUG/NON_BUG.",
        backstory=(
            "Especialista em análise visual usando modelos de visão para validar "
            "qualidade de figuras científicas."
        ),
        verbose=True,
        tools=[PlotTool()],
        llm=llm,
    )
