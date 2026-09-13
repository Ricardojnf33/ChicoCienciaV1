import json
import subprocess
import sys
import os
from pathlib import Path

import pytest

from src.core.tree import AgenticTree
from src.processes.ats_process import ExecutionMode, run_agentic_tree


def test_cli_init_dry_run(tmp_path):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    cmd = [
        sys.executable,
        "-m",
        "src.cli",
        "init",
        "objective.example.yaml",
        "--budget",
        "2",
        "--out-dir",
        str(runs_dir),
    ]
    env = os.environ.copy()
    env.pop("OPENAI_API_KEY", None)
    env.pop("SEMANTIC_SCHOLAR_API_KEY", None)
    env["WANDB_ON"] = "true"
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=env)
    assert res.returncode == 0, res.stderr
    files = list(runs_dir.glob("*.json"))
    assert files, res.stderr
    data = json.loads(files[0].read_text())
    assert "nodes" in data and len(data["nodes"]) >= 1
    completed = [node for node in data["nodes"] if node["status"] == "SUCCEEDED"]
    assert completed
    for node in completed:
        assert node["meta"]["execution_mode"] == "mock"
        assert node["meta"]["synthetic"] is True
        result_path = Path(node["results_path"])
        assert result_path.is_file()
        result = json.loads(result_path.read_text())
        assert result["_execution"] == {
            "mode": "mock",
            "synthetic": True,
            "network_used": False,
        }


def test_live_mode_rejects_empty_api_key(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    tree = AgenticTree.new(
        objective_yaml="objective.example.yaml",
        artifact_root=str(tmp_path / "artifacts"),
    )

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        run_agentic_tree(
            object(),
            tree,
            budget=1,
            mode=ExecutionMode.LIVE,
            sqlite_url=f"sqlite:///{tmp_path / 'run.db'}",
        )

