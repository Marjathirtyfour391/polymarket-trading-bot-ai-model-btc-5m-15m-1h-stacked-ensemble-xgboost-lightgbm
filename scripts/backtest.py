"""Walk-forward backtest with calibration reporting."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

from polymarket_bot.calibration.calibrator import ProbabilityCalibrator
from polymarket_bot.config import ensure_directories, load_yaml_config
from polymarket_bot.logging_setup import setup_logging, get_logger
from polymarket_bot.models.ensemble import StackedEnsembleModel
from train import generate_synthetic_dataset

log = get_logger(__name__)


def walk_forward_backtest(
    x: pd.DataFrame,
    y: pd.Series,
    train_days: int = 14,
    test_days: int = 3,
) -> dict:
    window = max(int(len(x) * train_days / (train_days + test_days)), 100)
    test_size = max(int(len(x) * test_days / (train_days + test_days)), 50)
    results = []
    for start in range(0, len(x) - window - test_size, test_size):
        train_end = start + window
        test_end = min(train_end + test_size, len(x))
        x_train, y_train = x.iloc[start:train_end], y.iloc[start:train_end]
        x_test, y_test = x.iloc[train_end:test_end], y.iloc[train_end:test_end]

        model = StackedEnsembleModel()
        model.fit(x_train, y_train)
        raw = model.predict_proba(x_test)
        calibrator = ProbabilityCalibrator()
        calibrator.fit(raw, y_test.values)
        calibrated = calibrator.transform(raw)
        metrics = ProbabilityCalibrator.evaluate(calibrated, y_test.values)
        results.append(
            {
                "fold": len(results) + 1,
                "brier": metrics.brier_score,
                "log_loss": metrics.log_loss,
                "ece": metrics.ece,
            }
        )
    return {"folds": results, "avg_brier": float(np.mean([r["brier"] for r in results]))}


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(description="Run walk-forward backtest")
    parser.add_argument("--samples", type=int, default=8000)
    parser.add_argument("--output", type=str, default="reports/backtest_report.json")
    args = parser.parse_args()

    ensure_directories()
    yaml_config = load_yaml_config()
    wf = yaml_config.get("model", {}).get("walk_forward", {})

    x, y = generate_synthetic_dataset(args.samples)
    report = walk_forward_backtest(
        x,
        y,
        train_days=wf.get("train_days", 14),
        test_days=wf.get("test_days", 3),
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log.info("backtest_complete", report=report)
    print(f"Backtest report saved to {output}")


if __name__ == "__main__":
    main()
