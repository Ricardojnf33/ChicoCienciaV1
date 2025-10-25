try:
    from crewai import Crew, Process
except Exception:
    class Crew:  # minimal stub for dry-run
        def __init__(self, agents=None, process=None, verbose: bool = False):
            self.agents = agents or []
            self.process = process
            self.verbose = verbose

        def kickoff(self, tasks):
            return None

    class Process:
        hierarchical = "hierarchical"
from src.agents.manager import manager
from src.agents.researcher import researcher
from src.agents.coder import coder
from src.agents.runner import runner
from src.agents.reviewer import reviewer
from src.agents.vlm_critic import vlm_critic

manager.name = "manager"
researcher.name = "researcher"
coder.name = "coder"
runner.name = "runner"
reviewer.name = "reviewer"
vlm_critic.name = "vlm_critic"

def build_crew() -> Crew:
    crew = Crew(
        agents=[manager, researcher, coder, runner, reviewer, vlm_critic],
        process=Process.hierarchical,
        verbose=True,
    )
    return crew
