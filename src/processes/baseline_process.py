import hashlib
import time
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field, model_validator
from sklearn import datasets
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.core.atomic_io import atomic_write_text
from src.core.campaign import CampaignRunSpec


class BaselineResult(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    run_id: str = Field(min_length=1)
    condition: Literal["B0"] = "B0"
    dataset: str = Field(min_length=1)
    dataset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    seed: int
    train_size: int = Field(ge=1)
    test_size: int = Field(ge=1)
    train_indices_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    test_indices_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    cv_folds: int = Field(default=5, ge=2)
    candidate_c: list[float]
    selected_c: float = Field(gt=0)
    validation_scores: dict[str, float]
    primary_metric: str = Field(min_length=1)
    metrics: dict[str, float]
    duration_seconds: float = Field(ge=0)
    llm_tokens: int = Field(default=0, ge=0)
    llm_cost_usd: float = Field(default=0, ge=0)
    test_evaluations: int = 1

    @model_validator(mode="after")
    def validate_baseline(self):
        if self.llm_tokens != 0 or self.llm_cost_usd != 0:
            raise ValueError("B0 não pode registrar consumo de LLM.")
        if self.primary_metric not in self.metrics:
            raise ValueError("Métrica primária ausente do resultado B0.")
        if self.test_evaluations != 1:
            raise ValueError("O teste reservado deve ser avaliado uma única vez.")
        if set(self.validation_scores) != {str(value) for value in self.candidate_c}:
            raise ValueError("Scores de validação não correspondem aos candidatos.")
        return self


def _array_digest(*arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    for array in arrays:
        contiguous = np.ascontiguousarray(array)
        digest.update(str(contiguous.dtype).encode())
        digest.update(str(contiguous.shape).encode())
        digest.update(contiguous.tobytes())
    return digest.hexdigest()


def _load_dataset(name: str) -> tuple[np.ndarray, np.ndarray]:
    loaders = {
        "iris": datasets.load_iris,
        "wine": datasets.load_wine,
        "digits": datasets.load_digits,
    }
    try:
        dataset = loaders[name]()
    except KeyError as exc:
        raise ValueError(f"Dataset B0 não suportado: {name}") from exc
    return np.asarray(dataset.data), np.asarray(dataset.target)


def run_b0(
    spec: CampaignRunSpec,
    output_path: str | Path,
    *,
    candidate_c: tuple[float, ...] = (0.1, 1.0, 10.0),
) -> BaselineResult:
    if spec.condition != "B0" or spec.uses_llm:
        raise ValueError("run_b0 aceita somente especificações B0 sem LLM.")
    started = time.monotonic()
    features, target = _load_dataset(spec.dataset)
    indices = np.arange(len(target))
    train_indices, test_indices = train_test_split(
        indices,
        test_size=0.2,
        random_state=spec.seed,
        stratify=target,
    )
    train_x, test_x = features[train_indices], features[test_indices]
    train_y, test_y = target[train_indices], target[test_indices]
    primary_metric = "f1_macro" if spec.dataset == "wine" else "accuracy"
    scoring = "f1_macro" if primary_metric == "f1_macro" else "accuracy"
    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2_000,
                    solver="lbfgs",
                    random_state=spec.seed,
                ),
            ),
        ]
    )
    cross_validation = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=spec.seed,
    )
    search = GridSearchCV(
        pipeline,
        param_grid={"classifier__C": list(candidate_c)},
        scoring=scoring,
        cv=cross_validation,
        n_jobs=1,
        refit=True,
        return_train_score=False,
    )
    search.fit(train_x, train_y)
    prediction = search.best_estimator_.predict(test_x)
    metrics = {
        "accuracy": float(accuracy_score(test_y, prediction)),
        "f1_macro": float(f1_score(test_y, prediction, average="macro")),
    }
    validation_scores = {
        str(value): float(score)
        for value, score in zip(
            search.cv_results_["param_classifier__C"].data,
            search.cv_results_["mean_test_score"],
            strict=True,
        )
    }
    result = BaselineResult(
        run_id=spec.run_id,
        dataset=spec.dataset,
        dataset_sha256=_array_digest(features, target),
        seed=spec.seed,
        train_size=len(train_indices),
        test_size=len(test_indices),
        train_indices_sha256=_array_digest(train_indices),
        test_indices_sha256=_array_digest(test_indices),
        candidate_c=list(candidate_c),
        selected_c=float(search.best_params_["classifier__C"]),
        validation_scores=validation_scores,
        primary_metric=primary_metric,
        metrics=metrics,
        duration_seconds=time.monotonic() - started,
    )
    atomic_write_text(output_path, result.model_dump_json(indent=2))
    return result
