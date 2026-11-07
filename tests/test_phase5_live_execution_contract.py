from pathlib import Path
from types import SimpleNamespace

import crewai
import pytest

from src.core.contracts import ContractError, RunManifest, load_manifest
from src.core.llm_budget import BudgetExceeded, LLMBudgetLedger
from src.core.tree import AgenticTree
from src.core.variants import ExperimentVariant, policy_for
from src.processes import ats_process


AGENT_LIMIT_OUTPUT = "Agent stopped due to iteration limit or time limit."


@pytest.fixture
def make_crew(monkeypatch):
    monkeypatch.setattr(crewai, "Task", lambda **kwargs: SimpleNamespace(**kwargs))

    def build(*responses):
        outputs = iter(responses)
        manager = SimpleNamespace(tools=["delegation-tool"])

        def kickoff():
            assert manager.tools == []
            manager.tools = ["delegation-tool"]
            return SimpleNamespace(raw=next(outputs))

        return SimpleNamespace(
            manager_agent=manager,
            agents=[SimpleNamespace(role=role) for role in ("Researcher", "Coder")],
            tasks=[],
            kickoff=kickoff,
        )

    return build


def test_reset_manager_tools_removes_previous_delegation_state():
    manager = SimpleNamespace(tools=[object()])
    crew = SimpleNamespace(manager_agent=manager)

    ats_process._reset_manager_delegation_tools(crew)

    assert manager.tools == []


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "",
        "print('raw Python is not the task contract')",
        AGENT_LIMIT_OUTPUT,
        "```python\n" + AGENT_LIMIT_OUTPUT + "\n```",
        "Explicação\n```python\nprint('ok')\n```",
        "```\nprint('missing language')\n```",
        "```python\n\n```",
        "```python\nprint(\n```",
        "```python\nprint(1)\n```\n```python\nprint(2)\n```",
    ],
)
def test_live_attempt_refuses_invalid_generation_before_write_and_run(
    raw, tmp_path, monkeypatch, make_crew
):
    monkeypatch.setattr(
        ats_process, "PythonRunnerTool", lambda: pytest.fail("runner acionado")
    )
    node = SimpleNamespace(id="node-1", meta={"primary_metric": "accuracy"})

    with pytest.raises(ContractError, match="GENERATION_(INVALID|LIMIT_REACHED)"):
        ats_process._run_live_attempt(
            make_crew(raw), node, "prompt", 1, tmp_path, 1, 11
        )

    assert not list(tmp_path.iterdir())


def test_live_attempt_materializes_crew_output_before_runner(
    tmp_path, monkeypatch, make_crew
):
    generated = "if True:\r\n    print('generated')\r\n"
    result_path = tmp_path / "canonical.json"

    class FakeRunner:
        def run_script(self, code_path, **kwargs):
            assert Path(code_path).read_bytes() == generated.encode("utf-8")
            return {"returncode": 0, "stdout": "", "stderr": "", "timed_out": False}

    monkeypatch.setattr(ats_process, "PythonRunnerTool", FakeRunner)
    monkeypatch.setattr(ats_process, "canonicalize_attempt", lambda *a, **kw: result_path)

    node = SimpleNamespace(id="node-1", meta={"primary_metric": "accuracy"})

    observed = ats_process._run_live_attempt(
        make_crew(f"```python\r\n{generated}```"), node, "prompt", 1, tmp_path, 1, 11
    )

    assert observed == result_path
    assert list(tmp_path.iterdir()) == [tmp_path / "code.py"]


@pytest.mark.parametrize(
    ("variant", "expected_attempts"),
    [(ExperimentVariant.B1, 3), (ExperimentVariant.A, 3), (ExperimentVariant.A0, 1)],
)
def test_generation_failure_is_recorded_and_resume_respects_attempt_limit(
    variant, expected_attempts, tmp_path, monkeypatch, make_crew
):
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-key-no-network")
    monkeypatch.setattr(ats_process, "_sync_llm_budget", lambda *args: None)
    monkeypatch.setattr(
        ats_process, "PythonRunnerTool", lambda: pytest.fail("runner acionado")
    )
    objective = tmp_path / "objective.yaml"
    objective.write_text("objective:\n  title: Fixture\n  primary_metric: accuracy\n")
    tree = AgenticTree.new(str(objective), artifact_root=str(tmp_path / "artifacts"))
    tree_path = str(tmp_path / "tree.json")
    manifest_path = str(tmp_path / "manifest.json")
    db_url = f"sqlite:///{tmp_path / 'runs.db'}"
    policy = policy_for(variant)
    manifest = RunManifest(
        run_id="fixture",
        objective_path=str(objective),
        primary_metric="accuracy",
        variant=variant.value,
        effective_branching=policy.effective_branching(2),
        automatic_correction=policy.automatic_correction,
    )
    run_options = {
        "mode": ats_process.ExecutionMode.LIVE,
        "budget": 1,
        "variant": variant,
        "manifest_path": manifest_path,
        "checkpoint_path": tree_path,
        "sqlite_url": db_url,
    }

    with pytest.raises(ContractError, match="GENERATION_LIMIT_REACHED"):
        ats_process.run_agentic_tree(
            crew=make_crew(*[AGENT_LIMIT_OUTPUT] * expected_attempts),
            tree=tree,
            manifest=manifest,
            **run_options,
        )

    saved = load_manifest(manifest_path)
    assert saved.status == "FAILED"
    assert [attempt.attempt for attempt in saved.attempts] == list(range(1, expected_attempts + 1))
    assert all(
        attempt.status == "FAILED"
        and attempt.error.startswith("GENERATION_LIMIT_REACHED:")
        and AGENT_LIMIT_OUTPUT not in attempt.error
        and attempt.result_path is None
        and not list(Path(attempt.directory).iterdir())
        for attempt in saved.attempts
    )

    with pytest.raises(RuntimeError, match="esgotou o limite"):
        ats_process.run_agentic_tree(
            crew=make_crew(), tree=AgenticTree.load_json(tree_path), manifest=saved, **run_options
        )
    assert load_manifest(manifest_path).attempts == saved.attempts


def test_live_budget_stop_prevents_new_attempts_and_preserves_usage(
    tmp_path, monkeypatch, make_crew
):
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-key-no-network")
    monkeypatch.setattr(
        ats_process, "PythonRunnerTool", lambda: pytest.fail("runner acionado")
    )
    objective = tmp_path / "objective.yaml"
    objective.write_text("objective:\n  title: Fixture\n  primary_metric: accuracy\n")
    tree = AgenticTree.new(str(objective), artifact_root=str(tmp_path / "artifacts"))
    tree_path = str(tmp_path / "tree.json")
    manifest_path = str(tmp_path / "manifest.json")
    ledger_options = {
        "model": "gpt-4o-mini-2024-07-18",
        "token_limit": 100,
        "cost_limit_usd": 0.03,
        "call_limit": 24,
        "max_output_tokens_per_call": 20,
        "input_per_million_usd": 0.15,
        "cached_input_per_million_usd": 0.075,
        "output_per_million_usd": 0.60,
        "journal_path": tmp_path / "llm-budget.json",
    }
    ledger = LLMBudgetLedger(**ledger_options)
    ledger.reserve("previous", input_tokens=50)
    ledger.complete("previous", input_tokens=50, output_tokens=10)
    crew = make_crew(AGENT_LIMIT_OUTPUT)
    crew._chico_llm_budget = ledger
    kickoff = crew.kickoff

    def stop_after_rejected_reservation():
        with pytest.raises(BudgetExceeded, match="antes do transporte"):
            ledger.reserve("rejected", input_tokens=30)
        return kickoff()

    crew.kickoff = stop_after_rejected_reservation
    manifest = RunManifest(
        run_id="budget-fixture", objective_path=str(objective), primary_metric="accuracy"
    )
    options = {
        "budget": 1,
        "checkpoint_path": tree_path,
        "manifest_path": manifest_path,
        "mode": ats_process.ExecutionMode.LIVE,
        "sqlite_url": f"sqlite:///{tmp_path / 'runs.db'}",
    }
    with pytest.raises(ContractError, match="GENERATION_LIMIT_REACHED"):
        ats_process.run_agentic_tree(crew, tree, manifest=manifest, **options)

    saved = load_manifest(manifest_path)
    assert saved.status == "FAILED"
    assert len(saved.attempts) == 1
    assert saved.llm_started_calls == saved.llm_completed_calls == 1
    assert saved.llm_rejected_calls == 1
    assert saved.llm_total_tokens == 60
    assert saved.llm_cost_usd > 0
    assert saved.llm_stop_reason == ledger.snapshot().stop_reason

    resumed_crew = make_crew()
    resumed_crew._chico_llm_budget = LLMBudgetLedger(**ledger_options)
    with pytest.raises(ContractError, match="LLM_BUDGET_STOPPED"):
        ats_process.run_agentic_tree(
            resumed_crew, AgenticTree.load_json(tree_path), manifest=saved, **options
        )
    assert load_manifest(manifest_path) == saved
