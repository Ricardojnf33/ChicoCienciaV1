import json
import time
from pathlib import Path

import pytest
from requests.exceptions import Timeout
from tenacity import wait_none

from src.clients.semantic_scholar_client import SemanticScholarClient
from src.core import atomic_io
from src.core.contracts import (
    AttemptRecord,
    CanonicalResult,
    ExecutionEvidence,
    RunManifest,
    file_sha256,
    load_result,
    write_result,
)
from src.core.enums import ExecStatus
from src.core.persistence import get_node, init_db
from src.core.tree import AgenticTree
from src.processes.ats_process import ExecutionMode, run_agentic_tree
from src.tools.python_repl import PythonRunnerTool, SandboxUnavailableError


def test_atomic_write_preserves_previous_checkpoint_on_replace_failure(tmp_path, monkeypatch):
    checkpoint = tmp_path / "tree.json"
    checkpoint.write_text("previous")

    def fail_replace(source, target):
        raise OSError("injected replace failure")

    monkeypatch.setattr(atomic_io.os, "replace", fail_replace)
    with pytest.raises(OSError, match="injected"):
        atomic_io.atomic_write_text(checkpoint, "new")

    assert checkpoint.read_text() == "previous"
    assert list(tmp_path.glob(".tree.json.*.tmp")) == []


def test_runner_removes_credentials_and_writes_independent_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-cross-boundary")
    script = tmp_path / "code.py"
    script.write_text(
        "import json, os\n"
        "json.dump({'secret': os.getenv('OPENAI_API_KEY')}, "
        "open('raw_results.json', 'w'))\n"
        "print('completed')\n"
    )

    result = PythonRunnerTool(require_network_isolation=False).run_script(
        str(script), workdir=str(tmp_path), timeout=5
    )

    assert result["returncode"] == 0
    assert json.loads((tmp_path / "raw_results.json").read_text()) == {"secret": None}
    evidence = ExecutionEvidence.model_validate_json(
        (tmp_path / "execution.json").read_text()
    )
    assert evidence.return_code == 0
    assert evidence.network_isolated is False
    assert evidence.network_used is False
    assert Path(evidence.stdout_path).read_text().strip() == "completed"


def test_runner_timeout_terminates_process_group(tmp_path):
    sentinel = tmp_path / "child-survived"
    script = tmp_path / "code.py"
    script.write_text(
        "import subprocess, sys, time\n"
        f"subprocess.Popen([sys.executable, '-c', \"import time; time.sleep(.5); "
        f"open({str(sentinel)!r}, 'w').write('bad')\"])\n"
        "time.sleep(30)\n"
    )

    result = PythonRunnerTool(require_network_isolation=False).run_script(
        str(script), workdir=str(tmp_path), timeout=0.1
    )
    time.sleep(0.7)

    assert result["returncode"] == 124
    assert result["timed_out"] is True
    assert sentinel.exists() is False


def test_runner_enforces_file_size_budget(tmp_path):
    script = tmp_path / "code.py"
    script.write_text("open('oversized.bin', 'wb').write(b'x' * 2 * 1024 * 1024)\n")

    result = PythonRunnerTool(
        require_network_isolation=False, output_mb=1
    ).run_script(str(script), workdir=str(tmp_path), timeout=5)

    assert result["returncode"] != 0
    assert (tmp_path / "oversized.bin").stat().st_size <= 1024 * 1024


def test_runner_fails_closed_without_os_sandbox(tmp_path, monkeypatch):
    script = tmp_path / "code.py"
    script.write_text("raise SystemExit(0)\n")
    monkeypatch.setattr("src.tools.python_repl.shutil.which", lambda name: None)

    with pytest.raises(SandboxUnavailableError, match="bubblewrap"):
        PythonRunnerTool().run_script(str(script), workdir=str(tmp_path))


class FakeClock:
    def __init__(self):
        self.now = 100.0
        self.sleeps = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def test_rate_limit_is_shared_across_instances_without_real_wait():
    fake = FakeClock()
    SemanticScholarClient._reset_rate_limit_for_tests()
    first = SemanticScholarClient(
        client=object(), min_interval=1.25, clock=fake.clock, sleeper=fake.sleep
    )
    second = SemanticScholarClient(
        client=object(), min_interval=1.25, clock=fake.clock, sleeper=fake.sleep
    )

    first._rate_limit()
    second._rate_limit()

    assert fake.sleeps == [pytest.approx(1.25)]


class AlwaysTimeoutClient:
    def __init__(self):
        self.calls = 0

    def search_paper(self, **kwargs):
        self.calls += 1
        raise Timeout("fixture timeout")


def test_external_timeout_fixture_exhausts_three_retries_without_real_wait():
    dependency = AlwaysTimeoutClient()
    SemanticScholarClient._reset_rate_limit_for_tests()
    client = SemanticScholarClient(client=dependency, min_interval=0)

    with pytest.raises(Timeout, match="fixture timeout"):
        client.search.retry_with(wait=wait_none())(client, "fault injection")

    assert dependency.calls == 3


def test_resume_reconciles_success_once_without_reexecution(tmp_path):
    tree = AgenticTree.new(
        objective_yaml="objective.example.yaml",
        artifact_root=str(tmp_path / "artifacts"),
    )
    node = tree.nodes[tree.frontier[0]]
    attempt_dir = tree.artifact_root / node.id / "attempt-1"
    result_path = write_result(
        attempt_dir / "results.json",
        CanonicalResult(
            node_id=node.id,
            attempt=1,
            status="SUCCEEDED",
            primary_metric=tree.primary_metric,
            metrics={tree.primary_metric: 0.5},
            execution=ExecutionEvidence(
                mode="mock", synthetic=True, network_used=False, return_code=0
            ),
        ),
    )
    manifest = RunManifest(
        run_id="resume-test",
        objective_path="objective.example.yaml",
        primary_metric=tree.primary_metric,
        attempts=[
            AttemptRecord(
                node_id=node.id,
                attempt=1,
                mode="mock",
                status="SUCCEEDED",
                directory=str(attempt_dir),
                result_path=str(result_path),
                result_sha256=file_sha256(result_path),
                finished_at="2026-09-11T00:00:00Z",
            )
        ],
    )
    checkpoint = tmp_path / "tree.json"

    for _ in range(2):
        run_agentic_tree(
            None,
            tree,
            budget=0,
            branching=1,
            checkpoint_path=str(checkpoint),
            mode=ExecutionMode.MOCK,
            sqlite_url=f"sqlite:///{tmp_path / 'run.db'}",
            manifest=manifest,
            manifest_path=str(tmp_path / "manifest.json"),
        )

    assert node.status is ExecStatus.SUCCEEDED
    assert node.visits == 1
    assert len([item for item in tree.nodes.values() if item.parent_id == node.id]) == 1
    assert len(manifest.attempts) == 1
    load_result(node.results_path, node_id=node.id, attempt=1, mode="mock")
    projection = init_db(f"sqlite:///{tmp_path / 'run.db'}")
    assert get_node(projection, node.id).status == "SUCCEEDED"


def test_resume_stops_when_attempt_budget_is_exhausted(tmp_path):
    tree = AgenticTree.new(
        objective_yaml="objective.example.yaml",
        artifact_root=str(tmp_path / "artifacts"),
    )
    node = tree.nodes[tree.frontier[0]]
    manifest = RunManifest(
        run_id="exhausted-test",
        objective_path="objective.example.yaml",
        primary_metric=tree.primary_metric,
        attempts=[
            AttemptRecord(
                node_id=node.id,
                attempt=1,
                mode="mock",
                status="FAILED",
                directory=str(tree.artifact_root / node.id / "attempt-1"),
                error="injected failure",
                finished_at="2026-09-11T00:00:00Z",
            )
        ],
    )
    checkpoint = tmp_path / "tree.json"
    manifest_path = tmp_path / "manifest.json"

    with pytest.raises(RuntimeError, match="esgotou o limite"):
        run_agentic_tree(
            None,
            tree,
            budget=1,
            checkpoint_path=str(checkpoint),
            mode=ExecutionMode.MOCK,
            sqlite_url=f"sqlite:///{tmp_path / 'run.db'}",
            manifest=manifest,
            manifest_path=str(manifest_path),
        )

    assert tree.nodes[node.id].status is ExecStatus.FAILED
    assert checkpoint.is_file()
    assert RunManifest.model_validate_json(manifest_path.read_text()).status == "FAILED"
