"""Optional Telegram alert notifications."""

from __future__ import annotations

import httpx

from polymarket_bot.config import get_settings
from polymarket_bot.logging_setup import get_logger

log = get_logger(__name__)


async def send_telegram_alert(message: str) -> bool:
    settings = get_settings()
    if not settings.telegram_alerts_enabled:
        return False
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        log.warning("telegram_not_configured")
        return False

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            url,
            json={"chat_id": settings.telegram_chat_id, "text": message, "parse_mode": "HTML"},
        )
        return response.status_code == 200
