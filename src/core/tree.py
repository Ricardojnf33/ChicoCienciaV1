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

    # --- Persistência simples em JSON ---
    def to_dict(self) -> dict:
        def node_to_dict(n: Node) -> dict:
            return {
                "id": n.id,
                "parent_id": n.parent_id,
                "type": n.type.name,
                "stage": n.stage.name,
                "prompt": n.prompt,
                "plan": n.plan,
                "code_path": n.code_path,
                "results_path": n.results_path,
                "figs_paths": list(n.figs_paths),
                "score": n.score,
                "visits": n.visits,
                "value_sum": n.value_sum,
                "status": n.status.name,
                "meta": n.meta,
            }

        return {
            "objective": self.objective,
            "primary_metric": self.primary_metric,
            "artifact_root": str(self.artifact_root),
            "frontier": list(self.frontier),
            "nodes": [node_to_dict(n) for n in self.nodes.values()],
        }

    def save_json(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False))

    @classmethod
    def from_dict(cls, data: dict) -> "AgenticTree":
        obj = data.get("objective", {})
        primary_metric = data.get("primary_metric", "accuracy")
        artifact_root = data.get("artifact_root", "./experiments")
        tree = cls(obj, primary_metric, artifact_root)
        # Reconstroi nós
        tree.nodes = {}
        for nd in data.get("nodes", []):
            n = Node(
                id=nd["id"],
                parent_id=nd.get("parent_id"),
                type=NodeType[nd["type"]],
                stage=Stage[nd["stage"]],
                prompt=nd.get("prompt", ""),
                plan=nd.get("plan"),
                code_path=nd.get("code_path"),
                results_path=nd.get("results_path"),
                figs_paths=nd.get("figs_paths", []),
                score=nd.get("score"),
                visits=int(nd.get("visits", 0)),
                value_sum=float(nd.get("value_sum", 0.0)),
                status=ExecStatus[nd.get("status", "PENDING")],
                meta=nd.get("meta", {}),
            )
            tree.nodes[n.id] = n
        tree.frontier = list(data.get("frontier", []))
        return tree

    @classmethod
    def load_json(cls, path: str) -> "AgenticTree":
        data = json.loads(Path(path).read_text())
        return cls.from_dict(data)
