"""Application settings loaded from environment and YAML."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT_DIR / "config" / "default.yaml"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    trading_mode: str = Field(default="paper", alias="TRADING_MODE")
    polymarket_private_key: str = Field(default="", alias="POLYMARKET_PRIVATE_KEY")
    polymarket_wallet_address: str = Field(default="", alias="POLYMARKET_WALLET_ADDRESS")
    polymarket_clob_host: str = Field(
        default="https://clob.polymarket.com", alias="POLYMARKET_CLOB_HOST"
    )
    polymarket_gamma_host: str = Field(
        default="https://gamma-api.polymarket.com", alias="POLYMARKET_GAMMA_HOST"
    )
    polymarket_chain_id: int = Field(default=137, alias="POLYMARKET_CHAIN_ID")
    binance_ws_url: str = Field(
        default="wss://stream.binance.com:9443/ws/btcusdt@trade",
        alias="BINANCE_WS_URL",
    )
    chainlink_data_streams_url: str = Field(default="", alias="CHAINLINK_DATA_STREAMS_URL")
    chainlink_api_key: str = Field(default="", alias="CHAINLINK_API_KEY")
    database_url: str = Field(default="sqlite:///data/trades.db", alias="DATABASE_URL")
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")
    telegram_alerts_enabled: bool = Field(default=False, alias="TELEGRAM_ALERTS_ENABLED")
    max_usd_per_trade: float = Field(default=25.0, alias="MAX_USD_PER_TRADE")
    max_session_loss_usd: float = Field(default=100.0, alias="MAX_SESSION_LOSS_USD")
    max_market_loss_usd: float = Field(default=50.0, alias="MAX_MARKET_LOSS_USD")
    kelly_fraction: float = Field(default=0.25, alias="KELLY_FRACTION")
    min_edge: float = Field(default=0.03, alias="MIN_EDGE")
    fee_rate: float = Field(default=0.02, alias="FEE_RATE")
    slippage_buffer: float = Field(default=0.005, alias="SLIPPAGE_BUFFER")
    stop_trading_seconds_before_close: int = Field(
        default=75, alias="STOP_TRADING_SECONDS_BEFORE_CLOSE"
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(default="logs/bot.log", alias="LOG_FILE")

    @property
    def is_paper_mode(self) -> bool:
        return self.trading_mode.lower() == "paper"

    @property
    def is_live_mode(self) -> bool:
        return self.trading_mode.lower() == "live"


@lru_cache
def load_yaml_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or DEFAULT_CONFIG
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


@lru_cache
def get_settings() -> Settings:
    return Settings()


def ensure_directories() -> None:
    for relative in ("data", "logs", "models/artifacts", "reports"):
        (ROOT_DIR / relative).mkdir(parents=True, exist_ok=True)
