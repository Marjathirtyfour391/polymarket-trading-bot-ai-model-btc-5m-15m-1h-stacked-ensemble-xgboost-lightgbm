"""CLI dashboard and health monitoring."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from polymarket_bot.risk.manager import RiskManager


@dataclass
class HealthSnapshot:
    timestamp: datetime
    mode: str
    session_pnl: float
    open_positions: int
    circuit_breaker: bool
    feeds_connected: dict[str, bool]
    last_prediction_edge: float | None


class HealthMonitor:
    """Aggregate bot health metrics for CLI or dashboard display."""

    def __init__(self, risk_manager: RiskManager, mode: str) -> None:
        self.risk_manager = risk_manager
        self.mode = mode
        self.feeds: dict[str, bool] = {
            "binance": False,
            "clob": False,
            "gamma": False,
            "chainlink": False,
        }
        self.last_edge: float | None = None

    def set_feed_status(self, feed: str, connected: bool) -> None:
        self.feeds[feed] = connected

    def set_last_edge(self, edge: float) -> None:
        self.last_edge = edge

    def snapshot(self) -> HealthSnapshot:
        state = self.risk_manager.state
        return HealthSnapshot(
            timestamp=datetime.now(timezone.utc),
            mode=self.mode,
            session_pnl=state.session_pnl,
            open_positions=state.open_positions,
            circuit_breaker=state.circuit_breaker_until is not None,
            feeds_connected=dict(self.feeds),
            last_prediction_edge=self.last_edge,
        )

    def render_cli(self) -> str:
        snap = self.snapshot()
        lines = [
            "=" * 60,
            "  Polymarket Trading Bot – Health Dashboard",
            "=" * 60,
            f"  Mode:              {snap.mode.upper()}",
            f"  Session PnL:       ${snap.session_pnl:+.2f}",
            f"  Open Positions:    {snap.open_positions}",
            f"  Circuit Breaker:   {'ACTIVE' if snap.circuit_breaker else 'OK'}",
            f"  Last Edge:         {snap.last_prediction_edge or 'N/A'}",
            "  Feeds:",
        ]
        for name, ok in snap.feeds_connected.items():
            status = "CONNECTED" if ok else "DISCONNECTED"
            lines.append(f"    {name:12s} {status}")
        lines.append("=" * 60)
        return "\n".join(lines)
