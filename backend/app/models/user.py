from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class SubscriptionPlan(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    subscription_plan = Column(Enum(SubscriptionPlan), default=SubscriptionPlan.FREE)
    subscription_expires_at = Column(DateTime, nullable=True)

    # Preferencias
    default_currency = Column(String(10), default="ARS")
    telegram_chat_id = Column(String(50), nullable=True)
    preferences = Column(JSON, default={})

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    alerts = relationship("Alert", back_populates="user")
    portfolios = relationship("Portfolio", back_populates="user")


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # type: ignore[name-defined]
    name = Column(String(200), nullable=False)
    description = Column(String(500))
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="portfolios")
    positions = relationship("Position", back_populates="portfolio")


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    avg_cost = Column(Float, nullable=False)    # Precio promedio de compra
    currency = Column(String(10), default="ARS")
    opened_at = Column(DateTime, server_default=func.now())
    closed_at = Column(DateTime, nullable=True)
    is_open = Column(Boolean, default=True)
    notes = Column(String(500))

    portfolio = relationship("Portfolio", back_populates="positions")


# Fix forward reference
from sqlalchemy import ForeignKey  # noqa
Portfolio.user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
