import uuid, random, json, math
from pathlib import Path
from typing import List, Optional
from .node import Node
from .enums import NodeType, Stage
from .scoring import final_score
from src.config.settings import Settings

class AgenticTree:
    def __init__(self, objective: dict, primary_metric: str, artifact_root: str):
        self.objective = objective
        self.primary_metric = primary_metric
        self.artifact_root = Path(artifact_root)
        self.nodes: dict[str, Node] = {}
        self.frontier: list[str] = []
        self.settings = Settings()

    @classmethod
    def new(cls, objective_yaml: str, artifact_root: str = "./experiments"):
        import yaml
        obj = yaml.safe_load(Path(objective_yaml).read_text())
        primary_metric = obj.get("objective", {}).get("primary_metric", "accuracy")
        tree = cls(obj, primary_metric, artifact_root)
        root_id = tree._add_node(
            parent_id=None,
            type=NodeType.HYPOTHESIS,
            stage=Stage.PRELIM,
            prompt=json.dumps(obj["objective"], ensure_ascii=False),
            plan=None
        )
        tree.frontier.append(root_id)
        return tree

    def _add_node(self, parent_id, type, stage, prompt, plan) -> str:
        nid = str(uuid.uuid4())[:8]
        n = Node(id=nid, parent_id=parent_id, type=type, stage=stage, prompt=prompt, plan=plan)
        self.nodes[nid] = n
        return nid

    def select(self) -> Node:
        # UCT seleção entre candidatos da fronteira (ou todos se vazio)
        candidates = [self.nodes[i] for i in self.frontier] if self.frontier else list(self.nodes.values())
        if not candidates:
            raise RuntimeError("No candidates to select")
        total_visits = sum(max(1, n.visits) for n in candidates)
        c = self.settings.UCT_C
        def uct(n: Node) -> float:
            avg = (n.value_sum / n.visits) if n.visits > 0 else 0.0
            explore = c * math.sqrt(math.log(total_visits) / max(1, n.visits))
            return avg + explore
        return max(candidates, key=uct)

    def expand(self, node: Node, k: int = 2) -> list[str]:
        child_ids = []
        for _ in range(k):
            child_ids.append(self._add_node(
                parent_id=node.id,
                type=node.type,  # simplificação: herda tipo; o Manager ajustará no runtime real
                stage=node.stage,
                prompt=node.prompt,
                plan=node.plan or "Auto-generated plan stub."
            ))
        self.frontier.extend(child_ids)
        return child_ids

    def update_result(self, node_id: str, results_path: str, vlm_ok: bool = True):
        n = self.nodes[node_id]
        n.results_path = results_path
        n.score = final_score(results_path, self.primary_metric, vlm_ok=vlm_ok)
        if node_id in self.frontier:
            self.frontier.remove(node_id)

    def backpropagate(self, node: Node, score: float):
        # Atualiza valor e visitas ao longo da cadeia até a raiz
        cur: Optional[Node] = node
        while cur is not None:
            cur.visits += 1
            cur.value_sum += score
            cur.score = max(cur.score or 0.0, score)
            cur = self.nodes.get(cur.parent_id) if cur.parent_id else None

    def should_early_stop(self, threshold: float = 0.72) -> bool:
        best = max((n.score or 0.0) for n in self.nodes.values())
        return best >= threshold
