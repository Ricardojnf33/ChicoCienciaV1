from typing import Any

from crewai import Agent

from src.tools.crewai_adapters import LiteratureTool


def build_researcher(llm: Any) -> Agent:
    return Agent(
        role="Researcher",
        goal="Gerar hipóteses e planos experimentais com revisão de literatura e novidade.",
        backstory=(
            "Pesquisador experiente em revisão de literatura científica e formulação "
            "de hipóteses testáveis."
        ),
        verbose=True,
        tools=[LiteratureTool()],
        llm=llm,
    )
