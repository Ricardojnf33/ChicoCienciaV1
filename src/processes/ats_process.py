try:
    from crewai import Task, Crew, Process  # type: ignore
except Exception:
    class Task:  # minimal stub for dry-run
        def __init__(self, agent=None, description: str = ""):
            self.agent = agent
            self.description = description

    class Crew:  # minimal stub for dry-run
        def __init__(self, agents=None, process=None, verbose: bool = False):
            self.agents = agents or []
            self.process = process
            self.verbose = verbose

        def kickoff(self, tasks):
            return None

    class Process:
        hierarchical = "hierarchical"
from src.core.tree import AgenticTree
from src.prompts.stages import build_prompt, next_stage
from src.config.settings import Settings

def run_agentic_tree(crew: Crew, tree: AgenticTree, budget: int, branching: int = 2):
    settings = Settings()
    dry_run = settings.OPENAI_API_KEY is None
    for _ in range(budget):
        node = tree.select()
        prompt = build_prompt(node.stage, objective_json=node.prompt)

        def _agent_by_name(c: Crew, name: str):
            return next(a for a in c.agents if getattr(a, "name", None) == name)

        researcher = _agent_by_name(crew, "researcher")
        coder = _agent_by_name(crew, "coder")
        runner = _agent_by_name(crew, "runner")
        reviewer = _agent_by_name(crew, "reviewer")
        vlm_critic = _agent_by_name(crew, "vlm_critic")

        tasks = [
            Task(agent=researcher, description=f"{prompt}\nGere {branching} hipóteses/planos para o nó {node.id}."),
            Task(agent=coder, description=f"Implementar o melhor plano para o nó {node.id} com reprodutibilidade."),
            Task(agent=runner, description=f"Executar o código do nó {node.id} e salvar artifacts."),
            Task(agent=reviewer, description=f"Avaliar resultados do nó {node.id}, checar validade e gerar report."),
            Task(agent=vlm_critic, description=f"Revisar figuras do nó {node.id} (VLM) e classificar BUG/NON_BUG."),
        ]
        if not dry_run:
            crew.kickoff(tasks)

        # Simulação de resultado e backprop com UCT
        import json, os
        res_path = f"./experiments/{node.id}/results.json"
        os.makedirs(f"./experiments/{node.id}", exist_ok=True)
        with open(res_path, "w") as f:
            json.dump({"accuracy": 0.5}, f)
        tree.update_result(node.id, res_path, vlm_ok=True)
        score = tree.nodes[node.id].score or 0.0
        tree.backpropagate(tree.nodes[node.id], score)

        # expansão simples por estágio
        child_ids = tree.expand(tree.nodes[node.id], k=branching)
        # Atualiza estágios dos filhos
        for cid in child_ids:
            c = tree.nodes[cid]
            c.stage = next_stage(c.stage)

        if tree.should_early_stop(threshold=tree.settings.EARLY_STOP_SCORE):
            break
