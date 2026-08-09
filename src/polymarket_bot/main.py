"""Main trading bot orchestrator."""

from __future__ import annotations

import asyncio
import signal
from datetime import datetime, timezone

import pandas as pd

from polymarket_bot.config import ensure_directories, get_settings, load_yaml_config
from polymarket_bot.data import BinanceSpotFeed, GammaClient, SpotTick
from polymarket_bot.execution.clob import ClobExecutor
from polymarket_bot.features.engineering import FeatureEngineer
from polymarket_bot.logging_setup import get_logger, setup_logging
from polymarket_bot.models.ensemble import StackedEnsembleModel
from polymarket_bot.monitoring.database import Database
from polymarket_bot.monitoring.health import HealthMonitor
from polymarket_bot.risk.manager import RiskManager
from polymarket_bot.strategy.edge import EdgeStrategy, Side

log = get_logger(__name__)


class TradingBot:
    """Production-oriented paper/live trading loop for BTC Up/Down markets."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.yaml_config = load_yaml_config()
        self.risk = RiskManager()
        self.strategy = EdgeStrategy()
        self.executor = ClobExecutor()
        self.db = Database()
        self.feature_engineer = FeatureEngineer(
            multi_timeframe_bias=self.yaml_config.get("features", {}).get(
                "multi_timeframe_bias", True
            )
        )
        self.health = HealthMonitor(self.risk, self.settings.trading_mode)
        self.gamma = GammaClient()
        self.latest_spot: float | None = None
        self._running = False
        self._model: StackedEnsembleModel | None = None

    def _load_model(self) -> None:
        artifact_dir = self.yaml_config.get("model", {}).get("artifact_dir", "models/artifacts")
        from pathlib import Path

        path = Path(artifact_dir)
        if (path / "model_meta.json").exists():
            self._model = StackedEnsembleModel.load(path)
            log.info("model_loaded", path=str(path))
        else:
            log.warning("model_not_found", path=str(path), hint="Run training first")

    def _on_spot_tick(self, tick: SpotTick) -> None:
        self.latest_spot = tick.price
        self.health.set_feed_status("binance", True)

    async def _evaluate_market(self, market) -> None:
        if self.latest_spot is None:
            return

        now = datetime.now(timezone.utc)
        seconds_left = (market.end_time - now).total_seconds()
        stop_seconds = self.settings.stop_trading_seconds_before_close
        if seconds_left < stop_seconds:
            log.debug("market_near_close", market_id=market.market_id, seconds_left=seconds_left)
            return

        can_trade, reason = self.risk.can_trade(market.market_id)
        if not can_trade:
            log.info("trade_blocked", market_id=market.market_id, reason=reason)
            return

        features = self.feature_engineer.build(
            spot_price=self.latest_spot,
            price_to_beat=market.price_to_beat or self.latest_spot,
            end_time=market.end_time,
            timeframe=market.timeframe,
            best_bid=max(market.implied_up_prob - 0.01, 0.01),
            best_ask=min(market.implied_up_prob + 0.01, 0.99),
            bid_size=100,
            ask_size=100,
        )

        model_prob = market.implied_up_prob
        if self._model:
            frame = pd.DataFrame([features.values])
            model_prob = float(self._model.predict_proba(frame)[0])

        signal_result = self.strategy.evaluate(
            model_prob_up=model_prob,
            market_prob_up=market.implied_up_prob,
            spread=0.02,
        )
        self.health.set_last_edge(signal_result.edge)
        self.db.log_prediction(
            market.market_id,
            market.timeframe,
            model_prob,
            market.implied_up_prob,
            signal_result.edge,
        )

        if signal_result.side == Side.NONE:
            return

        token_id = market.up_token_id if signal_result.side == Side.UP else market.down_token_id
        price = market.implied_up_prob if signal_result.side == Side.UP else 1 - market.implied_up_prob
        order = await self.executor.place_limit_order(
            market_id=market.market_id,
            token_id=token_id,
            side=signal_result.side,
            price=price,
            size_usd=signal_result.size_usd,
        )
        if order.status.value == "FILLED":
            self.risk.register_position()
            self.db.log_trade(
                order.order_id,
                market.market_id,
                signal_result.side.value,
                price,
                signal_result.size_usd,
                is_paper=order.is_paper,
            )

    async def run_cycle(self) -> None:
        market_configs = self.yaml_config.get("trading", {}).get("markets", [])
        for cfg in market_configs:
            slug = cfg.get("slug_pattern", "")
            try:
                markets = await self.gamma.fetch_btc_updown_markets(slug)
                self.health.set_feed_status("gamma", True)
                for market in markets[:3]:
                    await self._evaluate_market(market)
            except Exception as exc:
                log.error("market_fetch_failed", slug=slug, error=str(exc))
                self.health.set_feed_status("gamma", False)

    async def run(self) -> None:
        ensure_directories()
        self._load_model()
        self._running = True
        binance = BinanceSpotFeed(self._on_spot_tick)
        binance_task = asyncio.create_task(binance.start())

        log.info("bot_started", mode=self.settings.trading_mode)
        try:
            while self._running:
                await self.run_cycle()
                print(self.health.render_cli())
                await asyncio.sleep(5)
        finally:
            binance.stop()
            binance_task.cancel()
            log.info("bot_stopped")

    def stop(self) -> None:
        self._running = False


def main() -> None:
    setup_logging()
    settings = get_settings()
    if settings.is_live_mode:
        yaml_config = load_yaml_config()
        confirmed = yaml_config.get("trading", {}).get("live_trading_confirmed", False)
        if not confirmed:
            log.error("live_trading_blocked", hint="Set live_trading_confirmed: true in config")
            return

    bot = TradingBot()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, bot.stop)

    try:
        loop.run_until_complete(bot.run())
    except KeyboardInterrupt:
        bot.stop()


if __name__ == "__main__":
    main()
