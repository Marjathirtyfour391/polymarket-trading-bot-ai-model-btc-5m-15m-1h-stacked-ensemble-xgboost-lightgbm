"""Probability calibration: Platt scaling and isotonic regression."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


@dataclass
class CalibrationMetrics:
    brier_score: float
    log_loss: float
    ece: float


class ProbabilityCalibrator:
    """Post-hoc calibration layer for ensemble outputs."""

    def __init__(self, method: str = "platt") -> None:
        self.method = method
        self._model: LogisticRegression | IsotonicRegression | None = None

    def fit(self, raw_probs: np.ndarray, y_true: np.ndarray) -> CalibrationMetrics:
        if self.method == "isotonic":
            self._model = IsotonicRegression(out_of_bounds="clip")
            self._model.fit(raw_probs, y_true)
        else:
            self._model = LogisticRegression(max_iter=1000)
            self._model.fit(raw_probs.reshape(-1, 1), y_true)
        calibrated = self.transform(raw_probs)
        return self.evaluate(calibrated, y_true)

    def transform(self, raw_probs: np.ndarray) -> np.ndarray:
        if self._model is None:
            return raw_probs
        if isinstance(self._model, IsotonicRegression):
            return self._model.predict(raw_probs)
        return self._model.predict_proba(raw_probs.reshape(-1, 1))[:, 1]

    @staticmethod
    def evaluate(probs: np.ndarray, y_true: np.ndarray, n_bins: int = 10) -> CalibrationMetrics:
        brier = float(np.mean((probs - y_true) ** 2))
        log_loss = float(
            -np.mean(y_true * np.log(probs + 1e-9) + (1 - y_true) * np.log(1 - probs + 1e-9))
        )
        fraction_pos, mean_pred = calibration_curve(y_true, probs, n_bins=n_bins, strategy="uniform")
        ece = float(np.mean(np.abs(fraction_pos - mean_pred)))
        return CalibrationMetrics(brier_score=brier, log_loss=log_loss, ece=ece)
