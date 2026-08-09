"""Unit tests for feature engineering."""

import numpy as np
from datetime import datetime, timedelta, timezone

from polymarket_bot.features.engineering import FeatureEngineer, FEATURE_COLUMNS


def test_feature_engineer_build():
    engineer = FeatureEngineer()
    end = datetime.now(timezone.utc) + timedelta(minutes=5)
    for i in range(25):
        fv = engineer.build(
            spot_price=95000 + i * 10,
            price_to_beat=95000,
            end_time=end,
            timeframe="5m",
            best_bid=0.48,
            best_ask=0.52,
            bid_size=100,
            ask_size=80,
        )
    assert len(fv.values) == len(FEATURE_COLUMNS)
    assert fv.values["timeframe_5m"] == 1.0
    assert fv.values["timeframe_15m"] == 0.0


def test_feature_columns_complete():
    assert "distance_to_beat" in FEATURE_COLUMNS
    assert "book_imbalance" in FEATURE_COLUMNS
    assert len(FEATURE_COLUMNS) == 21
