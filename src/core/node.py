from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .enums import NodeType, ExecStatus, Stage

@dataclass
class Node:
    id: str
    parent_id: Optional[str]
    type: NodeType
    stage: Stage
    prompt: str
    plan: str | None = None
    code_path: str | None = None
    results_path: str | None = None
    figs_paths: List[str] = field(default_factory=list)
    score: float | None = None
    visits: int = 0
    value_sum: float = 0.0
    status: ExecStatus = ExecStatus.PENDING
    meta: Dict[str, Any] = field(default_factory=dict)
