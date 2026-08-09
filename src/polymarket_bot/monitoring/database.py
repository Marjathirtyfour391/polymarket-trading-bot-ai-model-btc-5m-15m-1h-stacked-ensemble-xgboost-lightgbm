"""Trade and prediction persistence."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from polymarket_bot.config import get_settings


class Base(DeclarativeBase):
    pass


class PredictionLog(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    market_id = Column(String(128), nullable=False)
    timeframe = Column(String(8), nullable=False)
    model_prob = Column(Float, nullable=False)
    market_prob = Column(Float, nullable=False)
    edge = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TradeLog(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(64), nullable=False)
    market_id = Column(String(128), nullable=False)
    side = Column(String(8), nullable=False)
    price = Column(Float, nullable=False)
    size_usd = Column(Float, nullable=False)
    pnl = Column(Float, default=0.0)
    is_paper = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Database:
    def __init__(self, url: str | None = None) -> None:
        settings = get_settings()
        self.engine = create_engine(url or settings.database_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def log_prediction(
        self,
        market_id: str,
        timeframe: str,
        model_prob: float,
        market_prob: float,
        edge: float,
    ) -> None:
        with Session(self.engine) as session:
            session.add(
                PredictionLog(
                    market_id=market_id,
                    timeframe=timeframe,
                    model_prob=model_prob,
                    market_prob=market_prob,
                    edge=edge,
                )
            )
            session.commit()

    def log_trade(
        self,
        order_id: str,
        market_id: str,
        side: str,
        price: float,
        size_usd: float,
        pnl: float = 0.0,
        is_paper: bool = True,
    ) -> None:
        with Session(self.engine) as session:
            session.add(
                TradeLog(
                    order_id=order_id,
                    market_id=market_id,
                    side=side,
                    price=price,
                    size_usd=size_usd,
                    pnl=pnl,
                    is_paper=1 if is_paper else 0,
                )
            )
            session.commit()
