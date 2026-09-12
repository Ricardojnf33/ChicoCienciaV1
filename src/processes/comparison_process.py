import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from src.core.contracts import (
    ComparisonManifest,
    ComparisonRunRecord,
    RunManifest,
    file_sha256,
    save_comparison_manifest,
    save_manifest,
    utc_now,
)
from src.core.tree import AgenticTree
from src.core.variants import ExperimentVariant, policy_for
from src.processes.ats_process import ExecutionMode, run_agentic_tree


CrewFactory = Callable[[Path], Any]
VARIANT_ORDER = (
    ExperimentVariant.B1,
    ExperimentVariant.A,
    ExperimentVariant.A0,
)


def run_variant_comparison(
    objective_path: str,
    output_root: str,
    *,
    budget: int,
    branching: int,
    max_depth: int,
    max_branching: int,
    mode: ExecutionMode = ExecutionMode.MOCK,
    campaign_id: str | None = None,
    crew_factory: CrewFactory | None = None,
) -> tuple[ComparisonManifest, Path]:
    """Execute B1, A and A0 from one immutable objective and shared limits."""
    objective = Path(objective_path)
    if not objective.is_file():
        raise FileNotFoundError(f"Objetivo ausente: {objective}")
    mode = ExecutionMode(mode)
    if mode is ExecutionMode.LIVE and crew_factory is None:
        raise ValueError("Comparação live requer crew_factory.")

    campaign_id = campaign_id or f"phase4-{uuid.uuid4().hex[:8]}"
    campaign_dir = Path(output_root) / campaign_id
    campaign_dir.mkdir(parents=True, exist_ok=False)
    comparison_path = campaign_dir / "comparison.json"
    runs = []
    for variant in VARIANT_ORDER:
        run_id = f"{campaign_id}-{variant.value.lower()}"
        run_dir = campaign_dir / variant.value
        runs.append(
            ComparisonRunRecord(
                run_id=run_id,
                variant=variant.value,
                run_directory=str(run_dir),
                tree_path=str(run_dir / "tree.json"),
                manifest_path=str(run_dir / "manifest.json"),
            )
        )
    comparison = ComparisonManifest(
        campaign_id=campaign_id,
        objective_path=str(objective),
        objective_sha256=file_sha256(objective),
        mode=mode.value,
        budget=budget,
        branching=branching,
        max_depth=max_depth,
        max_branching=max_branching,
        runs=runs,
    )
    save_comparison_manifest(comparison_path, comparison)

    comparison.status = "RUNNING"
    save_comparison_manifest(comparison_path, comparison)
    failed = []
    for comparison_run, variant in zip(comparison.runs, VARIANT_ORDER, strict=True):
        run_dir = Path(comparison_run.run_directory)
        run_dir.mkdir(parents=True)
        tree = AgenticTree.new(
            objective_yaml=str(objective),
            artifact_root=str(run_dir / "artifacts"),
            max_depth=max_depth,
            max_branching=max_branching,
        )
        policy = policy_for(variant)
        manifest = RunManifest(
            run_id=comparison_run.run_id,
            objective_path=str(objective),
            primary_metric=tree.primary_metric,
            variant=variant.value,
            budget=budget,
            branching=branching,
            effective_branching=policy.effective_branching(branching),
            max_depth=max_depth,
            automatic_correction=policy.automatic_correction,
        )
        save_manifest(comparison_run.manifest_path, manifest)
        comparison_run.status = "RUNNING"
        save_comparison_manifest(comparison_path, comparison)
        try:
            crew = crew_factory(run_dir / "llm-budget.json") if crew_factory else None
            run_agentic_tree(
                crew,
                tree,
                budget=budget,
                branching=branching,
                checkpoint_path=comparison_run.tree_path,
                mode=mode,
                sqlite_url=f"sqlite:///{run_dir / 'run.db'}",
                manifest=manifest,
                manifest_path=comparison_run.manifest_path,
                variant=variant,
            )
            comparison_run.status = "SUCCEEDED"
        except Exception as exc:
            comparison_run.status = "FAILED"
            comparison_run.error = str(exc)
            failed.append(variant.value)
        finally:
            save_comparison_manifest(comparison_path, comparison)

    comparison.status = "FAILED" if failed else "SUCCEEDED"
    comparison.updated_at = utc_now()
    save_comparison_manifest(comparison_path, comparison)
    if failed:
        raise RuntimeError(
            f"Comparação terminou com falha nas variantes: {', '.join(failed)}. "
            f"Consulte {comparison_path}."
        )
    return comparison, comparison_path
