# Polymarket Bot Paper Trading Guide

Paper trading is the **default mode** for this polymarket trading bot. No real funds are at risk.

## Enable Paper Mode

```bash
# .env
TRADING_MODE=paper
```

## Run Paper Trading

```bash
python scripts/paper_trade.py
```

## What Paper Mode Does

- Connects to live Polymarket Gamma API and Binance WebSocket feeds
- Runs the full stacked ensemble inference pipeline
- Simulates order fills without submitting to the CLOB
- Logs all predictions and trades to SQLite

## Monitor Performance

The CLI dashboard prints session PnL, open positions, feed status, and last detected edge every 5 seconds.

## Dry Run Checklist

- [ ] Model artifacts exist in `models/artifacts/`
- [ ] `.env` configured with `TRADING_MODE=paper`
- [ ] Logs directory writable
- [ ] Review `reports/backtest_report.json` from walk-forward validation

## Keywords

polymarket bot dry run paper trading, polymarket trading bot python, polymarket open source trading bot
