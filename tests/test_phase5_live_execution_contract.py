from pathlib import Path
from types import SimpleNamespace

import crewai

from src.processes import ats_process


def test_reset_manager_tools_removes_previous_delegation_state():
    manager = SimpleNamespace(tools=[object()])
    crew = SimpleNamespace(manager_agent=manager)

    ats_process._reset_manager_delegation_tools(crew)

    assert manager.tools == []


def test_extract_python_code_prefers_fenced_program():
    output = SimpleNamespace(
        raw="Explicação\n```python\nprint('ok')\n```\nFim"
    )

    assert ats_process._extract_python_code(output) == "print('ok')\n"


def test_live_attempt_materializes_crew_output_before_runner(tmp_path, monkeypatch):
    monkeypatch.setattr(
        crewai,
        "Task",
        lambda **kwargs: SimpleNamespace(**kwargs),
    )

    class FakeRunner:
        def run_script(self, code_path, **kwargs):
            assert Path(code_path).read_text() == "print('generated')\n"
            return {"returncode": 0, "stdout": "", "stderr": "", "timed_out": False}

    result_path = tmp_path / "canonical.json"

    monkeypatch.setattr(ats_process, "PythonRunnerTool", lambda: FakeRunner())
    monkeypatch.setattr(
        ats_process,
        "canonicalize_attempt",
        lambda *args, **kwargs: result_path,
    )

    manager = SimpleNamespace(tools=["delegation-tool"])
    agents = [
        SimpleNamespace(role="Researcher"),
        SimpleNamespace(role="Coder"),
    ]

    class FakeCrew:
        def __init__(self):
            self.manager_agent = manager
            self.agents = agents
            self.tasks = []

        def kickoff(self):
            assert self.manager_agent.tools == []
            self.manager_agent.tools = ["delegation-tool"]
            return SimpleNamespace(raw="```python\nprint('generated')\n```")

    node = SimpleNamespace(id="node-1", meta={"primary_metric": "accuracy"})

    observed = ats_process._run_live_attempt(
        FakeCrew(),
        node,
        "prompt",
        branching=1,
        attempt_dir=tmp_path,
        attempt=1,
        experiment_seed=11,
    )

    assert observed == result_path
    assert len(list(tmp_path.glob("code.py"))) == 1
