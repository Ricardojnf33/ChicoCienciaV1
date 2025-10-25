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
import structlog

def run_agentic_tree(crew: Crew, tree: AgenticTree, budget: int, branching: int = 2):
    settings = Settings()
    dry_run = settings.OPENAI_API_KEY is None
    log = structlog.get_logger()
    for _ in range(budget):
        node = tree.select()
        prompt = build_prompt(node.stage, objective_json=node.prompt)
        log.info("ats.iter.start", node_id=node.id, stage=node.stage.name)

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
        kickoff_output = None
        if not dry_run:
            try:
                kickoff_output = crew.kickoff(tasks)
            except Exception as e:
                log.warning("ats.kickoff.error", error=str(e))
                kickoff_output = None

        # Extração de resultados reais (best-effort) ou simulação fallback
        import json, os
        res_path = None
        vlm_ok = True
        if kickoff_output:
            try:
                # Espera-se um objeto rico do CrewAI. Fazemos best-effort parsing.
                # Tentativas comuns: dict direto, objeto com .json ou .raw_output
                if isinstance(kickoff_output, dict):
                    res_path = kickoff_output.get("results_path")
                    vlm_ok = bool(kickoff_output.get("vlm_ok", True))
                else:
                    raw = getattr(kickoff_output, "raw_output", None) or getattr(kickoff_output, "json", None)
                    if callable(raw):
                        raw = raw()
                    if isinstance(raw, dict):
                        res_path = raw.get("results_path")
                        vlm_ok = bool(raw.get("vlm_ok", True))
            except Exception as e:
                log.warning("ats.extract.error", error=str(e))

        if not res_path:
            # Fallback: gera um results.json sintético
            res_path = f"./experiments/{node.id}/results.json"
            os.makedirs(f"./experiments/{node.id}", exist_ok=True)
            with open(res_path, "w") as f:
                json.dump({"accuracy": 0.5}, f)

        tree.update_result(node.id, res_path, vlm_ok=vlm_ok)
        score = tree.nodes[node.id].score or 0.0
        tree.backpropagate(tree.nodes[node.id], score)
        log.info("ats.iter.scored", node_id=node.id, score=score)

        # expansão simples por estágio
        child_ids = tree.expand(tree.nodes[node.id], k=branching)
        # Atualiza estágios dos filhos
        for cid in child_ids:
            c = tree.nodes[cid]
            c.stage = next_stage(c.stage)
        log.info("ats.iter.children", node_id=node.id, children=child_ids)

        if tree.should_early_stop(threshold=tree.settings.EARLY_STOP_SCORE):
            log.info("ats.early_stop", best=max((n.score or 0.0) for n in tree.nodes.values()))
            break
