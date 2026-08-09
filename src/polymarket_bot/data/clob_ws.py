"""Polymarket CLOB WebSocket order book feed."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Callable

from polymarket_bot.config import get_settings
from polymarket_bot.data import OrderBookSnapshot, ReconnectingWebSocket
from polymarket_bot.logging_setup import get_logger

log = get_logger(__name__)


class ClobOrderBookFeed:
    """Subscribe to Polymarket CLOB order book updates."""

    def __init__(
        self,
        token_id: str,
        market_id: str,
        on_snapshot: Callable[[OrderBookSnapshot], None],
    ) -> None:
        settings = get_settings()
        host = settings.polymarket_clob_host.replace("https://", "wss://").replace("http://", "ws://")
        self.url = f"{host}/ws/market"
        self.token_id = token_id
        self.market_id = market_id
        self.on_snapshot = on_snapshot
        self._ws: ReconnectingWebSocket | None = None

    def _handle_message(self, payload: dict) -> None:
        bids = payload.get("bids") or []
        asks = payload.get("asks") or []
        if not bids or not asks:
            return
        best_bid = float(bids[0]["price"])
        best_ask = float(asks[0]["price"])
        bid_size = float(bids[0].get("size", 0))
        ask_size = float(asks[0].get("size", 0))
        mid = (best_bid + best_ask) / 2
        spread = best_ask - best_bid
        total = bid_size + ask_size
        imbalance = (bid_size - ask_size) / total if total else 0.0
        snapshot = OrderBookSnapshot(
            market_id=self.market_id,
            best_bid=best_bid,
            best_ask=best_ask,
            mid=mid,
            spread=spread,
            bid_size=bid_size,
            ask_size=ask_size,
            imbalance=imbalance,
            timestamp=datetime.now(timezone.utc),
        )
        self.on_snapshot(snapshot)

    async def start(self) -> None:
        subscribe = json.dumps({"assets_ids": [self.token_id], "type": "market"})
        url = f"{self.url}?subscribe={subscribe}"

        def handler(payload: dict) -> None:
            if payload.get("asset_id") == self.token_id or payload.get("market"):
                self._handle_message(payload)

        self._ws = ReconnectingWebSocket(url, handler, name=f"clob-{self.market_id[:8]}")
        await self._ws.run()

    def stop(self) -> None:
        if self._ws:
            self._ws.stop()
