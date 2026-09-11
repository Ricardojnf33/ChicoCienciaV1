import uuid
import json
import math
from pathlib import Path
from typing import Optional
from .node import Node
from .enums import NodeType, Stage, ExecStatus
from .scoring import final_score
from src.config.settings import Settings
from src.core.atomic_io import atomic_write_text
from src.core.research import ExpansionCandidate, ExperimentPlan, HypothesisSpec
from src.prompts.stages import next_stage

class AgenticTree:
    def __init__(
        self,
        objective: dict,
        primary_metric: str,
        artifact_root: str,
        *,
        max_depth: int | None = None,
        max_branching: int | None = None,
    ):
        self.objective = objective
        self.primary_metric = primary_metric
        self.artifact_root = Path(artifact_root)
        self.nodes: dict[str, Node] = {}
        self.frontier: list[str] = []
        self.settings = Settings()
        self.max_depth = max_depth if max_depth is not None else self.settings.MAX_DEPTH
        self.max_branching = (
            max_branching if max_branching is not None else self.settings.MAX_BRANCHING
        )
        if self.max_depth < 0:
            raise ValueError("max_depth não pode ser negativo")
        if self.max_branching < 1:
            raise ValueError("max_branching deve ser pelo menos 1")

    @classmethod
    def new(
        cls,
        objective_yaml: str,
        artifact_root: str = "./experiments",
        *,
        max_depth: int | None = None,
        max_branching: int | None = None,
    ):
        import yaml
        obj = yaml.safe_load(Path(objective_yaml).read_text())
        primary_metric = obj.get("objective", {}).get("primary_metric", "accuracy")
        tree = cls(
            obj,
            primary_metric,
            artifact_root,
            max_depth=max_depth,
            max_branching=max_branching,
        )
        root_id = tree._add_node(
            parent_id=None,
            type=NodeType.HYPOTHESIS,
            stage=Stage.PRELIM,
            prompt=json.dumps(obj["objective"], ensure_ascii=False),
            plan=None
        )
        tree.frontier.append(root_id)
        return tree

    def _add_node(
        self,
        parent_id,
        type,
        stage,
        prompt,
        plan,
        *,
        depth: int = 0,
        hypothesis: HypothesisSpec | None = None,
        experiment_plan: ExperimentPlan | None = None,
    ) -> str:
        nid = str(uuid.uuid4())[:8]
        n = Node(
            id=nid,
            parent_id=parent_id,
            type=type,
            stage=stage,
            prompt=prompt,
            plan=plan,
            depth=depth,
            hypothesis=hypothesis,
            experiment_plan=experiment_plan,
        )
        self.nodes[nid] = n
        return nid

    def select(self) -> Node:
        candidates = [
            self.nodes[node_id]
            for node_id in self.frontier
            if self.nodes[node_id].status in {ExecStatus.PENDING, ExecStatus.FAILED}
        ]
        if not candidates:
            raise RuntimeError("A busca não possui nós pendentes na fronteira.")
        total_visits = sum(max(1, n.visits) for n in candidates)
        c = self.settings.UCT_C
        def uct(n: Node) -> float:
            avg = (n.value_sum / n.visits) if n.visits > 0 else 0.0
            explore = c * math.sqrt(math.log(total_visits) / max(1, n.visits))
            return avg + explore
        return max(candidates, key=uct)

    def _objective_candidates(self) -> list[ExpansionCandidate]:
        objective = self.objective.get("objective", {})
        statements = objective.get("hypotheses") or [
            f"Avaliar de forma controlada: {objective.get('title', 'objetivo científico')}"
        ]
        candidates = []
        for statement in statements:
            hypothesis = HypothesisSpec.from_statement(statement, self.primary_metric)
            plan = ExperimentPlan.build(
                hypothesis_id=hypothesis.hypothesis_id,
                decision_key=f"{hypothesis.hypothesis_id}.objective-test",
                description=f"Testar a hipótese declarada: {hypothesis.statement}",
                parameters={
                    "dataset": objective.get("dataset"),
                    "primary_metric": self.primary_metric,
                },
            )
            candidates.append(ExpansionCandidate(hypothesis=hypothesis, plan=plan))
        return candidates

    def _derived_candidates(self, node: Node) -> list[ExpansionCandidate]:
        if node.hypothesis is None:
            return []
        target_stage = next_stage(node.stage)
        strategies = {
            Stage.TUNING: [
                ("low-regularization", "Avaliar regularização baixa", {"regularization": "low"}),
                ("reference", "Avaliar configuração de referência", {"regularization": "reference"}),
                ("high-regularization", "Avaliar regularização alta", {"regularization": "high"}),
            ],
            Stage.RESEARCH_GRADE: [
                ("stratified-cv", "Validar com partições estratificadas", {"validation": "stratified-cv"}),
                ("seed-stability", "Medir estabilidade entre seeds", {"validation": "seed-stability"}),
                ("error-analysis", "Executar análise de erros", {"validation": "error-analysis"}),
            ],
            Stage.ABLATIONS: [
                ("remove-change", "Remover a mudança principal", {"ablation": "remove-change"}),
                ("minimal-model", "Comparar com modelo mínimo", {"ablation": "minimal-model"}),
                ("shuffle-control", "Aplicar controle por embaralhamento", {"ablation": "shuffle-control"}),
            ],
        }[target_stage]
        inherited = node.experiment_plan.parameters if node.experiment_plan else {}
        candidates = []
        for key, description, parameters in strategies:
            decision_key = (
                f"{node.hypothesis.hypothesis_id}.d{node.depth + 1}."
                f"{target_stage.name.lower()}.{key}"
            )
            plan = ExperimentPlan.build(
                hypothesis_id=node.hypothesis.hypothesis_id,
                decision_key=decision_key,
                description=description,
                parameters={**inherited, **parameters},
            )
            candidates.append(
                ExpansionCandidate(hypothesis=node.hypothesis, plan=plan)
            )
        return candidates

    def expand(
        self,
        node: Node,
        k: int = 2,
        *,
        candidates: list[ExpansionCandidate] | None = None,
    ) -> list[str]:
        if k < 0:
            raise ValueError("k não pode ser negativo")
        if node.depth >= self.max_depth or k == 0:
            node.meta["terminal_reason"] = "max_depth" if node.depth >= self.max_depth else "no_branching"
            return []
        available = candidates or (
            self._objective_candidates() if node.depth == 0 else self._derived_candidates(node)
        )
        decision_keys = [candidate.plan.decision_key for candidate in available]
        if len(decision_keys) != len(set(decision_keys)):
            raise ValueError("Candidatos de expansão contêm decisões duplicadas.")
        existing = {
            child.experiment_plan.decision_key
            for child in self.nodes.values()
            if child.parent_id == node.id and child.experiment_plan is not None
        }
        selected = [item for item in available if item.plan.decision_key not in existing][
            : min(k, self.max_branching)
        ]
        child_ids = []
        child_stage = next_stage(node.stage)
        type_by_stage = {
            Stage.TUNING: NodeType.HYPERPARAM,
            Stage.RESEARCH_GRADE: NodeType.REPLICATION,
            Stage.ABLATIONS: NodeType.ABLATION,
        }
        for candidate in selected:
            child_ids.append(
                self._add_node(
                    parent_id=node.id,
                    type=type_by_stage[child_stage],
                    stage=child_stage,
                    prompt=candidate.hypothesis.statement,
                    plan=candidate.plan.description,
                    depth=node.depth + 1,
                    hypothesis=candidate.hypothesis,
                    experiment_plan=candidate.plan,
                )
            )
        if node.id in self.frontier:
            self.frontier.remove(node.id)
        self.frontier.extend(child_ids)
        return child_ids

    def update_result(
        self,
        node_id: str,
        results_path: str,
        *,
        reviewer_decision: str = "NOT_EVALUATED",
        vlm_decision: str = "NOT_EVALUATED",
    ):
        n = self.nodes[node_id]
        score = final_score(
            results_path,
            self.primary_metric,
            reviewer_decision=reviewer_decision,
            vlm_decision=vlm_decision,
        )
        n.results_path = results_path
        n.score = score
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
                "depth": n.depth,
                "hypothesis": n.hypothesis.model_dump() if n.hypothesis else None,
                "experiment_plan": (
                    n.experiment_plan.model_dump() if n.experiment_plan else None
                ),
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
            "max_depth": self.max_depth,
            "max_branching": self.max_branching,
            "frontier": list(self.frontier),
            "nodes": [node_to_dict(n) for n in self.nodes.values()],
        }

    def save_json(self, path: str) -> None:
        atomic_write_text(path, json.dumps(self.to_dict(), indent=2, ensure_ascii=False))

    @classmethod
    def from_dict(cls, data: dict) -> "AgenticTree":
        obj = data.get("objective", {})
        primary_metric = data.get("primary_metric", "accuracy")
        artifact_root = data.get("artifact_root", "./experiments")
        tree = cls(
            obj,
            primary_metric,
            artifact_root,
            max_depth=int(data.get("max_depth", Settings().MAX_DEPTH)),
            max_branching=int(data.get("max_branching", Settings().MAX_BRANCHING)),
        )
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
                depth=int(nd.get("depth", 0)),
                hypothesis=(
                    HypothesisSpec.model_validate(nd["hypothesis"])
                    if nd.get("hypothesis")
                    else None
                ),
                experiment_plan=(
                    ExperimentPlan.model_validate(nd["experiment_plan"])
                    if nd.get("experiment_plan")
                    else None
                ),
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
