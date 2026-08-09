# Live Trading Setup for Polymarket Bot

> **Important:** Only enable live trading after thorough paper trading and walk-forward validation.

## Prerequisites

1. Polygon wallet with USDC
2. Polymarket account linked to wallet
3. Private key stored securely (never commit to git)

## Configuration

```bash
# .env
TRADING_MODE=live
POLYMARKET_PRIVATE_KEY=your_key_here
POLYMARKET_WALLET_ADDRESS=0xYourAddress
```

```yaml
# config/default.yaml
trading:
  mode: live
  live_trading_confirmed: true  # Required safety flag
```

## Risk Controls

- Max USD per trade: `MAX_USD_PER_TRADE`
- Session loss limit: `MAX_SESSION_LOSS_USD`
- Per-market loss limit: `MAX_MARKET_LOSS_USD`
- Circuit breaker cooldown: 30 minutes
- Stop trading 75–120 seconds before market close

## Run Live

```bash
python -m polymarket_bot.main
```

## Keywords

polymarket automated trading, polymarket algo trading, polygon polymarket trading bot, polymarket clob bot
