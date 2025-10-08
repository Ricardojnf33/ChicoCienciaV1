import json, math
from pathlib import Path

def metric_score(results_path: str, primary_metric: str = "accuracy") -> float:
    try:
        data = json.loads(Path(results_path).read_text())
        val = float(data.get(primary_metric, 0.0))
        return max(0.0, min(1.0, val))
    except Exception:
        return 0.0

def novelty_score(literature_overlap: float = 0.5) -> float:
    # 0 (muito parecido) → 1 (muito novo). Recebe overlap [0..1].
    return max(0.0, min(1.0, 1.0 - literature_overlap))

def robustness_score(replications: int, agreement: float) -> float:
    # acordo = proporção de replicações com resultado semelhante
    return max(0.0, min(1.0, (0.3 * min(replications/5,1.0) + 0.7 * agreement)))

def vlm_consistency_score(vlm_ok: bool) -> float:
    return 1.0 if vlm_ok else 0.4

def final_score(results_path: str, primary_metric: str, *, 
                literature_overlap: float = 0.5, replications: int = 0,
                agreement: float = 0.5, vlm_ok: bool = True) -> float:
    m = metric_score(results_path, primary_metric)
    n = novelty_score(literature_overlap)
    r = robustness_score(replications, agreement)
    v = vlm_consistency_score(vlm_ok)
    # pesos ajustáveis
    return round(0.45*m + 0.2*n + 0.25*r + 0.10*v, 4)
