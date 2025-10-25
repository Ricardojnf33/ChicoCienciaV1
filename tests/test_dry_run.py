import json
from pathlib import Path
import subprocess
import sys


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
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    assert res.returncode == 0
    files = list(runs_dir.glob("*.json"))
    assert files, res.stderr
    data = json.loads(files[0].read_text())
    assert "nodes" in data and len(data["nodes"]) >= 1


