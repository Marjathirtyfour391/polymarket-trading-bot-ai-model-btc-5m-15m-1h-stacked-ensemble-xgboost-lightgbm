# Strategy Methodology

## Core Edge Formula

```
edge = model_prob - market_implied_prob
trade if edge > fees + half_spread + slippage + min_edge
```

## Feature Engineering

| Feature | Description |
|---------|-------------|
| `distance_to_beat` | Spot price minus Polymarket reference price |
| `momentum_*` | Short-horizon price momentum |
| `realized_vol_*` | Rolling realized volatility |
| `book_imbalance` | Bid/ask size imbalance from CLOB |
| `microprice` | Volume-weighted mid price |
| `time_to_expiry_min` | Minutes until market resolution |
| `mtf_bias_*` | Multi-timeframe directional bias (1h → 15m → 5m) |

## Stacked Ensemble

- **Base models:** XGBoost, LightGBM, HistGradientBoosting, ExtraTrees, RandomForest
- **Meta-learner:** Logistic Regression (or LightGBM stacking)
- **Calibration:** Platt scaling / isotonic regression
- **Validation:** Walk-forward with purge/embargo

## Position Sizing

Quarter-Kelly with hard cap:

```
size = min(kelly_fraction × kelly_optimal × bankroll, max_usd_per_trade)
```

## Keywords

polymarket bot strategy, polymarket fair odds bot, polymarket probability trading bot, polymarket yes no arbitrage bot
