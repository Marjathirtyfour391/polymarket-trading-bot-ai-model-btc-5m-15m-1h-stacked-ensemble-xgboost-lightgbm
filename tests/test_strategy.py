"""Unit tests for edge strategy."""

from polymarket_bot.strategy.edge import EdgeStrategy, Side, StrategyConfig


def test_no_trade_when_insufficient_edge():
    strategy = EdgeStrategy(
        StrategyConfig(
            min_edge=0.05,
            fee_rate=0.02,
            slippage_buffer=0.005,
            kelly_fraction=0.25,
            max_usd_per_trade=25,
        )
    )
    signal = strategy.evaluate(model_prob_up=0.52, market_prob_up=0.50, spread=0.02)
    assert signal.side == Side.NONE


def test_buy_up_when_strong_edge():
    strategy = EdgeStrategy(
        StrategyConfig(
            min_edge=0.01,
            fee_rate=0.01,
            slippage_buffer=0.005,
            kelly_fraction=0.25,
            max_usd_per_trade=25,
        )
    )
    signal = strategy.evaluate(model_prob_up=0.75, market_prob_up=0.50, spread=0.02)
    assert signal.side == Side.UP
    assert signal.size_usd > 0
