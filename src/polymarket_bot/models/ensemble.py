"""Stacked ensemble probability model."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import TimeSeriesSplit
from xgboost import XGBClassifier

from polymarket_bot.features.engineering import FEATURE_COLUMNS
from polymarket_bot.logging_setup import get_logger

log = get_logger(__name__)


def _build_base_model(name: str) -> Any:
    builders = {
        "xgboost": lambda: XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            random_state=42,
        ),
        "lightgbm": lambda: LGBMClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbose=-1,
        ),
        "hist_gradient_boosting": lambda: HistGradientBoostingClassifier(
            max_iter=200, max_depth=4, learning_rate=0.05, random_state=42
        ),
        "extra_trees": lambda: ExtraTreesClassifier(
            n_estimators=200, max_depth=6, random_state=42
        ),
        "random_forest": lambda: RandomForestClassifier(
            n_estimators=200, max_depth=6, random_state=42
        ),
    }
    if name not in builders:
        raise ValueError(f"Unknown base model: {name}")
    return builders[name]()


class StackedEnsembleModel:
    """Two-level stacked ensemble producing calibrated P(UP)."""

    def __init__(
        self,
        base_model_names: list[str] | None = None,
        meta_learner_name: str = "logistic_regression",
    ) -> None:
        self.base_model_names = base_model_names or [
            "xgboost",
            "lightgbm",
            "hist_gradient_boosting",
            "extra_trees",
            "random_forest",
        ]
        self.meta_learner_name = meta_learner_name
        self.base_models: dict[str, Any] = {}
        self.meta_learner: Any = None
        self.feature_columns = FEATURE_COLUMNS

    def _meta_learner(self) -> Any:
        if self.meta_learner_name == "lightgbm":
            return LGBMClassifier(n_estimators=100, max_depth=3, verbose=-1, random_state=42)
        return LogisticRegression(max_iter=1000, random_state=42)

    def fit(self, x_train: pd.DataFrame, y_train: pd.Series) -> dict[str, float]:
        x = x_train[self.feature_columns].values
        y = y_train.values
        oof = np.zeros((len(x), len(self.base_model_names)))
        tscv = TimeSeriesSplit(n_splits=5)

        for idx, name in enumerate(self.base_model_names):
            model = _build_base_model(name)
            fold_preds = np.zeros(len(x))
            for train_idx, val_idx in tscv.split(x):
                model.fit(x[train_idx], y[train_idx])
                fold_preds[val_idx] = model.predict_proba(x[val_idx])[:, 1]
            oof[:, idx] = fold_preds
            model.fit(x, y)
            self.base_models[name] = model

        self.meta_learner = self._meta_learner()
        self.meta_learner.fit(oof, y)
        train_prob = self.predict_proba(x_train)
        metrics = {
            "brier": float(np.mean((train_prob - y) ** 2)),
            "log_loss": float(-np.mean(y * np.log(train_prob + 1e-9) + (1 - y) * np.log(1 - train_prob + 1e-9))),
        }
        log.info("model_trained", metrics=metrics)
        return metrics

    def predict_proba(self, features: pd.DataFrame) -> np.ndarray:
        x = features[self.feature_columns].values
        base_preds = np.column_stack(
            [self.base_models[name].predict_proba(x)[:, 1] for name in self.base_model_names]
        )
        if self.meta_learner is None:
            raise RuntimeError("Model not trained")
        return self.meta_learner.predict_proba(base_preds)[:, 1]

    def save(self, artifact_dir: Path) -> None:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.base_models, artifact_dir / "base_models.joblib")
        joblib.dump(self.meta_learner, artifact_dir / "meta_learner.joblib")
        meta = {
            "base_model_names": self.base_model_names,
            "meta_learner_name": self.meta_learner_name,
            "feature_columns": self.feature_columns,
        }
        (artifact_dir / "model_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, artifact_dir: Path) -> "StackedEnsembleModel":
        meta = json.loads((artifact_dir / "model_meta.json").read_text(encoding="utf-8"))
        model = cls(
            base_model_names=meta["base_model_names"],
            meta_learner_name=meta["meta_learner_name"],
        )
        model.base_models = joblib.load(artifact_dir / "base_models.joblib")
        model.meta_learner = joblib.load(artifact_dir / "meta_learner.joblib")
        model.feature_columns = meta["feature_columns"]
        return model
