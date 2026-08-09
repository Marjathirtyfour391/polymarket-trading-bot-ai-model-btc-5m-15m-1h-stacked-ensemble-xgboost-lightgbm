"""Trading strategy: edge detection and position sizing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from polymarket_bot.config import get_settings


class Side(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    NONE = "NONE"


@dataclass
class TradeSignal:
    side: Side
    model_prob: float
    market_prob: float
    edge: float
    size_usd: float
    reason: str


@dataclass
class StrategyConfig:
    min_edge: float
    fee_rate: float
    slippage_buffer: float
    kelly_fraction: float
    max_usd_per_trade: float

    @classmethod
    def from_settings(cls) -> "StrategyConfig":
        settings = get_settings()
        return cls(
            min_edge=settings.min_edge,
            fee_rate=settings.fee_rate,
            slippage_buffer=settings.slippage_buffer,
            kelly_fraction=settings.kelly_fraction,
            max_usd_per_trade=settings.max_usd_per_trade,
        )


class EdgeStrategy:
    """Compare model probability to market-implied probability and size positions."""

    def __init__(self, config: StrategyConfig | None = None) -> None:
        self.config = config or StrategyConfig.from_settings()

    def required_edge(self, half_spread: float) -> float:
        return (
            self.config.fee_rate
            + half_spread
            + self.config.slippage_buffer
            + self.config.min_edge
        )

    def kelly_size(self, edge: float, odds: float) -> float:
        if edge <= 0 or odds <= 0:
            return 0.0
        kelly = edge / odds
        fractional = kelly * self.config.kelly_fraction
        size = fractional * self.config.max_usd_per_trade
        return min(max(size, 0.0), self.config.max_usd_per_trade)

    def evaluate(
        self,
        model_prob_up: float,
        market_prob_up: float,
        spread: float,
        bankroll_usd: float = 1000.0,
    ) -> TradeSignal:
        half_spread = spread / 2
        threshold = self.required_edge(half_spread)
        edge_up = model_prob_up - market_prob_up
        edge_down = (1 - model_prob_up) - (1 - market_prob_up)

        if edge_up > threshold:
            odds = max(1 / max(market_prob_up, 0.01) - 1, 0.01)
            size = self.kelly_size(edge_up, odds)
            return TradeSignal(
                side=Side.UP,
                model_prob=model_prob_up,
                market_prob=market_prob_up,
                edge=edge_up,
                size_usd=min(size, self.config.max_usd_per_trade),
                reason=f"edge_up={edge_up:.4f} > threshold={threshold:.4f}",
            )

        if edge_down > threshold:
            market_prob_down = 1 - market_prob_up
            model_prob_down = 1 - model_prob_up
            odds = max(1 / max(market_prob_down, 0.01) - 1, 0.01)
            size = self.kelly_size(edge_down, odds)
            return TradeSignal(
                side=Side.DOWN,
                model_prob=model_prob_down,
                market_prob=market_prob_down,
                edge=edge_down,
                size_usd=min(size, self.config.max_usd_per_trade),
                reason=f"edge_down={edge_down:.4f} > threshold={threshold:.4f}",
            )

        return TradeSignal(
            side=Side.NONE,
            model_prob=model_prob_up,
            market_prob=market_prob_up,
            edge=max(edge_up, edge_down),
            size_usd=0.0,
            reason="insufficient_edge",
        )
