"""Risk management and circuit breakers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from polymarket_bot.config import get_settings


@dataclass
class RiskState:
    session_pnl: float = 0.0
    market_pnl: dict[str, float] = field(default_factory=dict)
    open_positions: int = 0
    circuit_breaker_until: datetime | None = None


class RiskManager:
    """Session and per-market loss limits with circuit breakers."""

    def __init__(self) -> None:
        settings = get_settings()
        self.max_session_loss = settings.max_session_loss_usd
        self.max_market_loss = settings.max_market_loss_usd
        self.max_open_positions = 6
        self.cooldown_minutes = 30
        self.state = RiskState()

    def can_trade(self, market_id: str) -> tuple[bool, str]:
        now = datetime.now(timezone.utc)
        if self.state.circuit_breaker_until and now < self.state.circuit_breaker_until:
            return False, "circuit_breaker_active"

        if self.state.session_pnl <= -self.max_session_loss:
            self._trigger_breaker()
            return False, "session_loss_limit"

        market_pnl = self.state.market_pnl.get(market_id, 0.0)
        if market_pnl <= -self.max_market_loss:
            return False, "market_loss_limit"

        if self.state.open_positions >= self.max_open_positions:
            return False, "max_open_positions"

        return True, "ok"

    def record_pnl(self, market_id: str, pnl: float) -> None:
        self.state.session_pnl += pnl
        self.state.market_pnl[market_id] = self.state.market_pnl.get(market_id, 0.0) + pnl
        if self.state.session_pnl <= -self.max_session_loss:
            self._trigger_breaker()

    def _trigger_breaker(self) -> None:
        self.state.circuit_breaker_until = datetime.now(timezone.utc) + timedelta(
            minutes=self.cooldown_minutes
        )

    def register_position(self) -> None:
        self.state.open_positions += 1

    def release_position(self) -> None:
        self.state.open_positions = max(0, self.state.open_positions - 1)
