from dataclasses import dataclass
from src.core.enums import Stage


@dataclass
class StageTemplates:
    prelim_hypothesis: str = (
        "Você é um pesquisador gerando hipóteses iniciais. Dado o objetivo, proponha 2-3 hipóteses testáveis,"
        " cada uma com um plano sucinto (dataset, métrica primária, análise e figura esperada)."
    )
    tuning_plan: str = (
        "Você é um experimentador ajustando hiperparâmetros para melhorar a métrica primária."
        " Proponha variações (até 3) com justificativa e passos reprodutíveis."
    )
    research_grade: str = (
        "Você é um pesquisador preparando um experimento de nível publicável."
        " Defina protocolo rigoroso, controles, riscos e critérios de exclusão."
    )
    ablations: str = (
        "Você fará ablações. Que componentes remover/alterar para confirmar contribuição?"
        " Defina 2-3 ablações e resultados esperados."
    )


def build_prompt(stage: Stage, objective_json: str) -> str:
    t = StageTemplates()
    if stage == Stage.PRELIM:
        return f"{t.prelim_hypothesis}\nOBJETIVO: {objective_json}"
    if stage == Stage.TUNING:
        return f"{t.tuning_plan}\nOBJETIVO: {objective_json}"
    if stage == Stage.RESEARCH_GRADE:
        return f"{t.research_grade}\nOBJETIVO: {objective_json}"
    if stage == Stage.ABLATIONS:
        return f"{t.ablations}\nOBJETIVO: {objective_json}"
    return objective_json


def next_stage(current: Stage) -> Stage:
    if current == Stage.PRELIM:
        return Stage.TUNING
    if current == Stage.TUNING:
        return Stage.RESEARCH_GRADE
    if current == Stage.RESEARCH_GRADE:
        return Stage.ABLATIONS
    return Stage.ABLATIONS


