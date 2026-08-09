"""Synthetic training data generator and model training pipeline."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from polymarket_bot.calibration.calibrator import ProbabilityCalibrator
from polymarket_bot.config import ensure_directories, load_yaml_config
from polymarket_bot.features.engineering import FEATURE_COLUMNS
from polymarket_bot.logging_setup import setup_logging, get_logger
from polymarket_bot.models.ensemble import StackedEnsembleModel

log = get_logger(__name__)


def generate_synthetic_dataset(n_samples: int = 5000, seed: int = 42) -> tuple[pd.DataFrame, pd.Series]:
    """Generate synthetic feature matrix for bootstrapping model training without historical data."""
    rng = np.random.default_rng(seed)
    x = pd.DataFrame(
        {
            col: rng.normal(0, 1, n_samples) if "timeframe" not in col else rng.integers(0, 2, n_samples)
            for col in FEATURE_COLUMNS
        }
    )
    x["time_to_expiry_min"] = rng.uniform(0.5, 60, n_samples)
    x["distance_to_beat_pct"] = rng.normal(0, 0.002, n_samples)
    logits = (
        2.5 * x["distance_to_beat_pct"]
        + 0.8 * x["momentum_5"]
        - 0.5 * x["realized_vol_10"]
        + 0.3 * x["book_imbalance"]
    )
    prob = 1 / (1 + np.exp(-logits))
    y = (rng.random(n_samples) < prob).astype(int)
    return x, pd.Series(y, name="target")


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(description="Train stacked ensemble model")
    parser.add_argument("--samples", type=int, default=5000, help="Synthetic training samples")
    parser.add_argument("--output", type=str, default="models/artifacts", help="Artifact output dir")
    args = parser.parse_args()

    ensure_directories()
    yaml_config = load_yaml_config()
    model_cfg = yaml_config.get("model", {})

    x, y = generate_synthetic_dataset(args.samples)
    split = int(len(x) * 0.8)
    x_train, x_val = x.iloc[:split], x.iloc[split:]
    y_train, y_val = y.iloc[:split], y.iloc[split:]

    ensemble = StackedEnsembleModel(
        base_model_names=model_cfg.get("base_models"),
        meta_learner_name=model_cfg.get("meta_learner", "logistic_regression"),
    )
    train_metrics = ensemble.fit(x_train, y_train)
    raw_probs = ensemble.predict_proba(x_val)

    calibrator = ProbabilityCalibrator(method=model_cfg.get("calibration", "platt"))
    cal_metrics = calibrator.fit(raw_probs, y_val.values)

    output = Path(args.output)
    ensemble.save(output)

    log.info(
        "training_complete",
        train_metrics=train_metrics,
        calibration={
            "brier": cal_metrics.brier_score,
            "log_loss": cal_metrics.log_loss,
            "ece": cal_metrics.ece,
        },
        artifact_dir=str(output),
    )
    print(f"Model saved to {output}")


if __name__ == "__main__":
    main()
