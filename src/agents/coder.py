from typing import Any

from crewai import Agent

from src.tools.crewai_adapters import DatasetTool, PlotTool


def build_coder(llm: Any) -> Agent:
    return Agent(
        role="Coder",
        goal=(
            "Entregar código Python reprodutível como texto para o executor controlado. "
            "O script deve gravar raw_results.json quando for executado."
        ),
        backstory=(
            "Desenvolvedor Python experiente em ciência de dados, focado em código "
            "limpo e reprodutível."
        ),
        verbose=True,
        tools=[DatasetTool(), PlotTool()],
        llm=llm,
    )
