"""Data ingestion from Polymarket, Binance, and Chainlink."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

import httpx
import websockets
from websockets.exceptions import ConnectionClosed

from polymarket_bot.config import get_settings
from polymarket_bot.logging_setup import get_logger

log = get_logger(__name__)


@dataclass
class OrderBookSnapshot:
    market_id: str
    best_bid: float
    best_ask: float
    mid: float
    spread: float
    bid_size: float
    ask_size: float
    imbalance: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SpotTick:
    symbol: str
    price: float
    quantity: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MarketInfo:
    market_id: str
    slug: str
    timeframe: str
    price_to_beat: float
    end_time: datetime
    up_token_id: str
    down_token_id: str
    implied_up_prob: float


class GammaClient:
    """Polymarket Gamma API client for BTC Up/Down market discovery."""

    def __init__(self, base_url: str | None = None) -> None:
        settings = get_settings()
        self.base_url = base_url or settings.polymarket_gamma_host

    async def fetch_btc_updown_markets(self, slug_pattern: str) -> list[MarketInfo]:
        url = f"{self.base_url}/markets"
        params = {"active": "true", "closed": "false", "limit": 50}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()

        markets: list[MarketInfo] = []
        for item in payload if isinstance(payload, list) else payload.get("data", []):
            slug = str(item.get("slug", ""))
            if slug_pattern not in slug:
                continue
            tokens = item.get("clobTokenIds") or item.get("tokens") or []
            if len(tokens) < 2:
                continue
            timeframe = slug_pattern.split("-")[-1]
            end_time_raw = item.get("endDate") or item.get("end_date_iso")
            end_time = datetime.fromisoformat(str(end_time_raw).replace("Z", "+00:00"))
            markets.append(
                MarketInfo(
                    market_id=str(item.get("id") or item.get("conditionId")),
                    slug=slug,
                    timeframe=timeframe,
                    price_to_beat=float(item.get("priceToBeat") or item.get("referencePrice") or 0),
                    end_time=end_time,
                    up_token_id=str(tokens[0]),
                    down_token_id=str(tokens[1]),
                    implied_up_prob=float(item.get("outcomePrices", [0.5, 0.5])[0]),
                )
            )
        return markets


class ReconnectingWebSocket:
    """Generic reconnecting WebSocket wrapper with heartbeat support."""

    def __init__(
        self,
        url: str,
        on_message: Callable[[dict[str, Any]], None],
        name: str = "ws",
        max_retries: int = 10,
        backoff_seconds: float = 2.0,
    ) -> None:
        self.url = url
        self.on_message = on_message
        self.name = name
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self._running = False

    async def run(self) -> None:
        self._running = True
        attempt = 0
        while self._running and attempt < self.max_retries:
            try:
                async with websockets.connect(self.url, ping_interval=20, ping_timeout=20) as ws:
                    log.info("websocket_connected", source=self.name)
                    attempt = 0
                    async for raw in ws:
                        if not self._running:
                            break
                        try:
                            payload = json.loads(raw)
                            self.on_message(payload)
                        except json.JSONDecodeError:
                            log.warning("invalid_json", source=self.name)
            except ConnectionClosed:
                log.warning("websocket_closed", source=self.name)
            except Exception as exc:
                log.error("websocket_error", source=self.name, error=str(exc))
            attempt += 1
            await asyncio.sleep(self.backoff_seconds * attempt)

    def stop(self) -> None:
        self._running = False


class BinanceSpotFeed:
    """Binance BTCUSDT trade stream for spot context."""

    def __init__(self, on_tick: Callable[[SpotTick], None]) -> None:
        settings = get_settings()
        self.url = settings.binance_ws_url
        self.on_tick = on_tick
        self._ws: ReconnectingWebSocket | None = None

    def _handle_message(self, payload: dict[str, Any]) -> None:
        if payload.get("e") != "trade":
            return
        tick = SpotTick(
            symbol=str(payload.get("s", "BTCUSDT")),
            price=float(payload.get("p", 0)),
            quantity=float(payload.get("q", 0)),
            timestamp=datetime.fromtimestamp(payload.get("T", 0) / 1000, tz=timezone.utc),
        )
        self.on_tick(tick)

    async def start(self) -> None:
        self._ws = ReconnectingWebSocket(self.url, self._handle_message, name="binance")
        await self._ws.run()

    def stop(self) -> None:
        if self._ws:
            self._ws.stop()


class ChainlinkPriceFeed:
    """Chainlink Data Streams placeholder for settlement-aligned price truth."""

    def __init__(self) -> None:
        settings = get_settings()
        self.url = settings.chainlink_data_streams_url
        self.api_key = settings.chainlink_api_key
        self.latest_price: float | None = None

    async def fetch_latest(self) -> float | None:
        if not self.url:
            return None
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(self.url, headers=headers)
            response.raise_for_status()
            payload = response.json()
        price = float(payload.get("price") or payload.get("data", {}).get("price", 0))
        self.latest_price = price
        return price
