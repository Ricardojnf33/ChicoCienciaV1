from typing import Any

from crewai import Agent

from src.tools.crewai_adapters import DatasetTool, PlotTool


def build_coder(llm: Any) -> Agent:
    return Agent(
        role="Coder",
        goal=(
            "Converter planos em código reprodutível sem executá-lo; salvar code.py e "
            "raw_results.json apenas quando o executor controlado rodar o script."
        ),
        backstory=(
            "Desenvolvedor Python experiente em ciência de dados, focado em código "
            "limpo e reprodutível."
        ),
        verbose=True,
        tools=[DatasetTool(), PlotTool()],
        llm=llm,
    )
