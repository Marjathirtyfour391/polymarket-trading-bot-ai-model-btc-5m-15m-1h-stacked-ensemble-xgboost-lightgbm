# API Reference

## Data Layer

### `GammaClient`

```python
from polymarket_bot.data import GammaClient

client = GammaClient()
markets = await client.fetch_btc_updown_markets("btc-updown-5m")
```

### `BinanceSpotFeed`

WebSocket feed for BTCUSDT spot trades.

### `ClobOrderBookFeed`

Real-time order book from Polymarket CLOB WebSocket.

## Model Layer

### `StackedEnsembleModel`

```python
from polymarket_bot.models.ensemble import StackedEnsembleModel

model = StackedEnsembleModel.load("models/artifacts")
prob_up = model.predict_proba(features_df)
```

## Strategy Layer

### `EdgeStrategy`

```python
from polymarket_bot.strategy.edge import EdgeStrategy

strategy = EdgeStrategy()
signal = strategy.evaluate(model_prob_up=0.62, market_prob_up=0.55, spread=0.02)
```

## Execution Layer

### `ClobExecutor`

```python
from polymarket_bot.execution.clob import ClobExecutor

executor = ClobExecutor()
order = await executor.place_limit_order(market_id, token_id, side, price, size_usd)
```

## Keywords

polymarket api trading bot, polymarket clob api trading bot, polymarket orderbook trading bot
