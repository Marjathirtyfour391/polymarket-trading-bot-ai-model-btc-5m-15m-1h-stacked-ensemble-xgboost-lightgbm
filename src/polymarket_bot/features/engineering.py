"""Feature engineering for BTC Up/Down probability models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    "distance_to_beat",
    "distance_to_beat_pct",
    "momentum_3",
    "momentum_5",
    "momentum_10",
    "momentum_20",
    "roc_3",
    "roc_5",
    "realized_vol_10",
    "realized_vol_20",
    "atr_14",
    "book_imbalance",
    "microprice",
    "spread",
    "spread_pct",
    "time_to_expiry_min",
    "timeframe_5m",
    "timeframe_15m",
    "timeframe_1h",
    "mtf_bias_1h",
    "mtf_bias_15m",
]


@dataclass
class FeatureVector:
    values: dict[str, float]
    timestamp: datetime

    def to_array(self) -> np.ndarray:
        return np.array([self.values[col] for col in FEATURE_COLUMNS], dtype=float)


class FeatureEngineer:
    """Compute model features from spot, order book, and market metadata."""

    def __init__(self, multi_timeframe_bias: bool = True) -> None:
        self.multi_timeframe_bias = multi_timeframe_bias
        self._price_history: list[float] = []

    def update_spot(self, price: float) -> None:
        self._price_history.append(price)
        if len(self._price_history) > 500:
            self._price_history = self._price_history[-500:]

    def _momentum(self, periods: int) -> float:
        if len(self._price_history) <= periods:
            return 0.0
        return self._price_history[-1] - self._price_history[-1 - periods]

    def _roc(self, periods: int) -> float:
        if len(self._price_history) <= periods:
            return 0.0
        base = self._price_history[-1 - periods]
        if base == 0:
            return 0.0
        return (self._price_history[-1] - base) / base

    def _realized_vol(self, window: int) -> float:
        if len(self._price_history) < window + 1:
            return 0.0
        returns = np.diff(self._price_history[-window - 1 :]) / np.array(
            self._price_history[-window - 1 : -1]
        )
        return float(np.std(returns))

    def _atr(self, window: int = 14) -> float:
        if len(self._price_history) < window + 1:
            return 0.0
        diffs = np.abs(np.diff(self._price_history[-window - 1 :]))
        return float(np.mean(diffs))

    def build(
        self,
        spot_price: float,
        price_to_beat: float,
        end_time: datetime,
        timeframe: str,
        best_bid: float,
        best_ask: float,
        bid_size: float,
        ask_size: float,
        mtf_bias_1h: float = 0.0,
        mtf_bias_15m: float = 0.0,
    ) -> FeatureVector:
        self.update_spot(spot_price)
        mid = (best_bid + best_ask) / 2 if best_bid and best_ask else spot_price
        spread = max(best_ask - best_bid, 0.0)
        total = bid_size + ask_size
        imbalance = (bid_size - ask_size) / total if total else 0.0
        microprice = (
            (best_ask * bid_size + best_bid * ask_size) / total if total else mid
        )
        now = datetime.now(timezone.utc)
        tte = max((end_time - now).total_seconds() / 60.0, 0.0)
        distance = spot_price - price_to_beat
        distance_pct = distance / price_to_beat if price_to_beat else 0.0

        values = {
            "distance_to_beat": distance,
            "distance_to_beat_pct": distance_pct,
            "momentum_3": self._momentum(3),
            "momentum_5": self._momentum(5),
            "momentum_10": self._momentum(10),
            "momentum_20": self._momentum(20),
            "roc_3": self._roc(3),
            "roc_5": self._roc(5),
            "realized_vol_10": self._realized_vol(10),
            "realized_vol_20": self._realized_vol(20),
            "atr_14": self._atr(14),
            "book_imbalance": imbalance,
            "microprice": microprice,
            "spread": spread,
            "spread_pct": spread / mid if mid else 0.0,
            "time_to_expiry_min": tte,
            "timeframe_5m": 1.0 if timeframe == "5m" else 0.0,
            "timeframe_15m": 1.0 if timeframe == "15m" else 0.0,
            "timeframe_1h": 1.0 if timeframe == "1h" else 0.0,
            "mtf_bias_1h": mtf_bias_1h if self.multi_timeframe_bias else 0.0,
            "mtf_bias_15m": mtf_bias_15m if self.multi_timeframe_bias else 0.0,
        }
        return FeatureVector(values=values, timestamp=now)

    @staticmethod
    def dataframe_from_records(records: list[dict]) -> pd.DataFrame:
        frame = pd.DataFrame(records)
        for col in FEATURE_COLUMNS:
            if col not in frame.columns:
                frame[col] = 0.0
        return frame[FEATURE_COLUMNS]
