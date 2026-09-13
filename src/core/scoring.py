from src.core.contracts import load_result
from src.core.evaluation import EvaluationDecision

def metric_score(results_path: str, primary_metric: str = "accuracy") -> float:
    result = load_result(results_path)
    if result.primary_metric != primary_metric:
        raise ValueError(
            f"Métrica primária divergente: {result.primary_metric!r}, esperada {primary_metric!r}."
        )
    return result.metrics[primary_metric]

def novelty_score(literature_overlap: float = 0.5) -> float:
    # 0 (muito parecido) → 1 (muito novo). Recebe overlap [0..1].
    return max(0.0, min(1.0, 1.0 - literature_overlap))

def robustness_score(replications: int, agreement: float) -> float:
    # acordo = proporção de replicações com resultado semelhante
    return max(0.0, min(1.0, (0.3 * min(replications/5,1.0) + 0.7 * agreement)))

def vlm_consistency_score(vlm_ok: bool) -> float:
    return 1.0 if vlm_ok else 0.4


def evaluation_decision_score(decision: EvaluationDecision | str) -> float:
    normalized = EvaluationDecision(decision)
    return {
        EvaluationDecision.APPROVED: 1.0,
        EvaluationDecision.NEEDS_REVISION: 0.5,
        EvaluationDecision.REJECTED: 0.0,
        EvaluationDecision.NOT_EVALUATED: 0.25,
    }[normalized]

def final_score(
    results_path: str,
    primary_metric: str,
    *,
    literature_overlap: float = 0.5,
    replications: int = 0,
    agreement: float = 0.5,
    reviewer_decision: EvaluationDecision | str = EvaluationDecision.NOT_EVALUATED,
    vlm_decision: EvaluationDecision | str = EvaluationDecision.NOT_EVALUATED,
    vlm_ok: bool | None = None,
) -> float:
    m = metric_score(results_path, primary_metric)
    n = novelty_score(literature_overlap)
    r = robustness_score(replications, agreement)
    reviewer = evaluation_decision_score(reviewer_decision)
    visual = (
        vlm_consistency_score(vlm_ok)
        if vlm_ok is not None
        else evaluation_decision_score(vlm_decision)
    )
    return round(0.40 * m + 0.15 * n + 0.20 * r + 0.15 * reviewer + 0.10 * visual, 4)
