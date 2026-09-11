from typing import Any

from crewai import Agent

from src.tools.crewai_adapters import LiteratureTool, PlotTool


def build_reviewer(llm: Any) -> Agent:
    return Agent(
        role="Reviewer",
        goal=(
            "Avaliar resultados, reportar negativos, verificar coerência com hipóteses "
            "e sugerir próximos passos."
        ),
        backstory=(
            "Revisor científico rigoroso com experiência em validação de resultados "
            "experimentais."
        ),
        verbose=True,
        tools=[PlotTool(), LiteratureTool()],
        llm=llm,
    )
