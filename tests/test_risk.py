"""Unit tests for risk manager."""

from polymarket_bot.risk.manager import RiskManager


def test_circuit_breaker_on_session_loss():
    risk = RiskManager()
    risk.max_session_loss = 50
    risk.record_pnl("market-1", -60)
    can_trade, reason = risk.can_trade("market-1")
    assert not can_trade
    assert reason == "circuit_breaker_active"
