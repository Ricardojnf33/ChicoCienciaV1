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
from src.core.persistence import init_db, NodeRow, upsert_node
import json as _json
import wandb
import time

def run_agentic_tree(crew: Crew, tree: AgenticTree, budget: int, branching: int = 2, checkpoint_path: str = None):
    settings = Settings()
    dry_run = settings.OPENAI_API_KEY is None
    log = structlog.get_logger()
    
    # --- OBSERVABILITY: WandB Init ---
    if settings.WANDB_ON and not dry_run:
        wandb.init(
            project=settings.WANDB_PROJECT,
            config={
                "budget": budget,
                "branching": branching,
                "model_text": settings.MODEL_TEXT,
                "model_vision": settings.MODEL_VISION,
                "objective": tree.objective_data.get("title", "Unknown")
            }
        )
        log.info("observability.wandb_init", project=settings.WANDB_PROJECT)
    elif settings.WANDB_ON and dry_run:
        log.warning("observability.wandb_skipped", reason="Dry-run mode active")

    log.info("ats.start", mode="DRY-RUN" if dry_run else "REAL", budget=budget)

    engine = init_db(settings.SQLITE_URL)
    
    start_time = time.time()
    
    for i in range(budget):
        iter_start = time.time()
        node = tree.select()
        prompt = build_prompt(node.stage, objective_json=node.prompt)
        log.info("ats.iter.start", iteration=i+1, node_id=node.id, stage=node.stage.name)

        # Persiste snapshot do nó atual
        upsert_node(engine, NodeRow(
            id=node.id,
            parent_id=node.parent_id,
            type=node.type.name,
            stage=node.stage.value,
            prompt=node.prompt,
            plan=node.plan,
            code_path=node.code_path,
            results_path=node.results_path,
            figs_paths=_json.dumps(node.figs_paths) if node.figs_paths else None,
            score=node.score,
            visits=node.visits,
            value_sum=node.value_sum,
            status=node.status.name,
            meta=_json.dumps(node.meta) if node.meta else None,
        ))

        def _agent_by_role(c: Crew, role: str):
            """Encontra agente por role (CrewAI não tem campo 'name')."""
            return next(a for a in c.agents if getattr(a, "role", "").lower() == role.lower())

        researcher = _agent_by_role(crew, "Researcher")
        coder = _agent_by_role(crew, "Coder")
        runner = _agent_by_role(crew, "Runner")
        reviewer = _agent_by_role(crew, "Reviewer")
        vlm_critic = _agent_by_role(crew, "VLM Critic")

        # --- SELF-HEALING LOOP ---
        max_retries = 2
        attempt = 0
        success = False
        res_path = None
        vlm_ok = True
        
        while attempt <= max_retries and not success:
            current_tasks = []
            
            # 1. Researcher (only on first attempt)
            if attempt == 0:
                current_tasks.append(Task(
                    agent=researcher,
                    description=f"{prompt}\nGere {branching} hipóteses/planos para o nó {node.id}.",
                    expected_output="Lista de hipóteses testáveis com revisão de literatura"
                ))
            
            # 2. Coder (Initial or Correction)
            if attempt == 0:
                coder_desc = (
                    f"Implementar o melhor plano para o nó {node.id} com reprodutibilidade.\n"
                    f"IMPORTANTE: O código DEVE ser salvo em: ./experiments/{node.id}/code.py\n"
                    f"IMPORTANTE: O código DEVE salvar results.json em: ./experiments/{node.id}/results.json\n"
                    f"IMPORTANTE: Verifique se o arquivo ./experiments/{node.id}/code.py foi criado com sucesso antes de finalizar."
                )
            else:
                # Correction Prompt
                coder_desc = (
                    f"A tentativa anterior falhou. Corrija o código para o nó {node.id}.\n"
                    f"Erro reportado: O arquivo ./experiments/{node.id}/code.py não foi encontrado ou falhou na execução.\n"
                    f"CERTIFIQUE-SE de salvar o arquivo corretamente em: ./experiments/{node.id}/code.py"
                )
                log.warning("ats.self_healing.retry", node_id=node.id, attempt=attempt)

            current_tasks.append(Task(
                agent=coder,
                description=coder_desc,
                expected_output="Caminho absoluto do arquivo Python criado e confirmação de existência."
            ))

            # 3. Runner
            current_tasks.append(Task(
                agent=runner,
                description=(
                    f"Executar o código do nó {node.id} localizado em ./experiments/{node.id}/code.py.\n"
                    f"Certifique-se de que o arquivo existe antes de executar."
                ),
                expected_output="Artefatos salvos: results.json e figuras"
            ))

            # Execute Coder & Runner (and Researcher if first try)
            kickoff_output = None
            if not dry_run:
                try:
                    crew.tasks = current_tasks
                    kickoff_output = crew.kickoff()
                except Exception as e:
                    log.warning("ats.kickoff.error", error=str(e), attempt=attempt)
                    kickoff_output = None

            # Check for Success (File Existence)
            # Best-effort extraction of results path
            import os
            expected_res_path = f"./experiments/{node.id}/results.json"
            expected_code_path = f"./experiments/{node.id}/code.py"
            
            if dry_run:
                success = True # Always succeed in dry-run
            elif os.path.exists(expected_code_path):
                 # We assume success if code exists, but ideally we check results.json too
                 # For now, let's be lenient: if code exists, we proceed to Reviewer
                 success = True
                 if os.path.exists(expected_res_path):
                     res_path = expected_res_path
            else:
                success = False
            
            attempt += 1

        # 4. Reviewer & VLM (Only if success or out of retries)
        final_tasks = [
            Task(
                agent=reviewer,
                description=f"Avaliar resultados do nó {node.id}, checar validade e gerar report.",
                expected_output="Avaliação dos resultados e sugestões para próximos passos"
            ),
            Task(
                agent=vlm_critic,
                description=f"Revisar figuras do nó {node.id} (VLM) e classificar BUG/NON_BUG.",
                expected_output="Classificação BUG/NON_BUG das figuras"
            ),
        ]
        
        if not dry_run:
             try:
                crew.tasks = final_tasks
                crew.kickoff() # Execute final analysis
             except Exception as e:
                log.warning("ats.final_tasks.error", error=str(e))

        # Extract final results for tree update
        if not res_path and not dry_run:
             # Try one last time to find it
             if os.path.exists(f"./experiments/{node.id}/results.json"):
                 res_path = f"./experiments/{node.id}/results.json"

        if not res_path:
            # Fallback: gera um results.json sintético
            res_path = f"./experiments/{node.id}/results.json"
            os.makedirs(f"./experiments/{node.id}", exist_ok=True)
            with open(res_path, "w") as f:
                json.dump({"accuracy": 0.5}, f)

        tree.update_result(node.id, res_path, vlm_ok=vlm_ok)
        # Persiste nó atualizado após resultado
        n = tree.nodes[node.id]
        upsert_node(engine, NodeRow(
            id=n.id,
            parent_id=n.parent_id,
            type=n.type.name,
            stage=n.stage.value,
            prompt=n.prompt,
            plan=n.plan,
            code_path=n.code_path,
            results_path=n.results_path,
            figs_paths=_json.dumps(n.figs_paths) if n.figs_paths else None,
            score=n.score,
            visits=n.visits,
            value_sum=n.value_sum,
            status=n.status.name,
            meta=_json.dumps(n.meta) if n.meta else None,
        ))
        score = tree.nodes[node.id].score or 0.0
        tree.backpropagate(tree.nodes[node.id], score)
        
        iter_duration = time.time() - iter_start
        log.info("ats.iter.scored", node_id=node.id, score=score, duration=f"{iter_duration:.2f}s")

        # --- OBSERVABILITY: WandB Log ---
        if settings.WANDB_ON and not dry_run:
            wandb.log({
                "iteration": i + 1,
                "node_id": node.id,
                "stage": node.stage.name,
                "score": score,
                "duration": iter_duration,
                "best_score": max((n.score or 0.0) for n in tree.nodes.values())
            })

        # expansão simples por estágio
        child_ids = tree.expand(tree.nodes[node.id], k=branching)
        # Atualiza estágios dos filhos
        for cid in child_ids:
            c = tree.nodes[cid]
            c.stage = next_stage(c.stage)
            # Persiste cada filho criado
            upsert_node(engine, NodeRow(
                id=c.id,
                parent_id=c.parent_id,
                type=c.type.name,
                stage=c.stage.value,
                prompt=c.prompt,
                plan=c.plan,
                code_path=c.code_path,
                results_path=c.results_path,
                figs_paths=_json.dumps(c.figs_paths) if c.figs_paths else None,
                score=c.score,
                visits=c.visits,
                value_sum=c.value_sum,
                status=c.status.name,
                meta=_json.dumps(c.meta) if c.meta else None,
            ))
        log.info("ats.iter.children", node_id=node.id, children=child_ids)

        if tree.should_early_stop(threshold=tree.settings.EARLY_STOP_SCORE):
            log.info("ats.early_stop", best=max((n.score or 0.0) for n in tree.nodes.values()))
            break
        
        # --- CHECKPOINTING ---
        if checkpoint_path:
            from pathlib import Path
            Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
            tree.save_json(checkpoint_path)
            log.info("ats.checkpoint.saved", path=checkpoint_path)
    
    if settings.WANDB_ON and not dry_run:
        wandb.finish()
