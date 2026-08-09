"""Order execution on Polymarket CLOB."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

import httpx

from polymarket_bot.config import get_settings
from polymarket_bot.logging_setup import get_logger
from polymarket_bot.strategy.edge import Side

log = get_logger(__name__)


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class Order:
    order_id: str
    market_id: str
    token_id: str
    side: Side
    price: float
    size_usd: float
    status: OrderStatus
    is_paper: bool
    created_at: datetime


class ClobExecutor:
    """Polymarket CLOB client with paper trading support."""

    def __init__(self) -> None:
        settings = get_settings()
        self.host = settings.polymarket_clob_host
        self.private_key = settings.polymarket_private_key
        self.wallet = settings.polymarket_wallet_address
        self.is_paper = settings.is_paper_mode

    async def place_limit_order(
        self,
        market_id: str,
        token_id: str,
        side: Side,
        price: float,
        size_usd: float,
        maker_first: bool = True,
    ) -> Order:
        order = Order(
            order_id=str(uuid.uuid4()),
            market_id=market_id,
            token_id=token_id,
            side=side,
            price=price,
            size_usd=size_usd,
            status=OrderStatus.PENDING,
            is_paper=self.is_paper,
            created_at=datetime.now(timezone.utc),
        )

        if self.is_paper:
            order.status = OrderStatus.FILLED
            log.info(
                "paper_order_filled",
                order_id=order.order_id,
                market_id=market_id,
                side=side.value,
                price=price,
                size_usd=size_usd,
            )
            return order

        if not self.private_key or not self.wallet:
            order.status = OrderStatus.REJECTED
            log.error("live_order_rejected", reason="missing_credentials")
            return order

        payload = {
            "token_id": token_id,
            "price": price,
            "size": size_usd,
            "side": "BUY",
            "type": "GTC" if maker_first else "FOK",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.host}/order",
                json=payload,
                headers={"Authorization": f"Bearer {self.private_key}"},
            )
            if response.status_code >= 400:
                order.status = OrderStatus.REJECTED
                log.error("live_order_failed", status=response.status_code, body=response.text)
            else:
                order.status = OrderStatus.FILLED
                data = response.json()
                order.order_id = str(data.get("orderID", order.order_id))
        return order

    async def cancel_order(self, order_id: str) -> bool:
        if self.is_paper:
            log.info("paper_order_cancelled", order_id=order_id)
            return True
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.delete(
                f"{self.host}/order/{order_id}",
                headers={"Authorization": f"Bearer {self.private_key}"},
            )
            return response.status_code < 400
