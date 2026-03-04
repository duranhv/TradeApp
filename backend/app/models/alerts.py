from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, Enum, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class AlertType(str, enum.Enum):
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PRICE_CHANGE_PCT = "price_change_pct"
    RSI_OVERBOUGHT = "rsi_overbought"
    RSI_OVERSOLD = "rsi_oversold"
    MA_CROSS_BULLISH = "ma_cross_bullish"
    MA_CROSS_BEARISH = "ma_cross_bearish"
    BOLLINGER_UPPER = "bollinger_upper"
    BOLLINGER_LOWER = "bollinger_lower"
    MACD_CROSS_BULLISH = "macd_cross_bullish"
    MACD_CROSS_BEARISH = "macd_cross_bearish"
    VOLUME_SPIKE = "volume_spike"
    FUNDAMENTAL = "fundamental"


class SignalStrength(str, enum.Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    NEUTRAL = "neutral"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    alert_type = Column(Enum(AlertType), nullable=False)
    name = Column(String(200))
    condition_value = Column(Float, nullable=True)
    condition_params = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    is_recurring = Column(Boolean, default=False)  # Se repite o dispara una vez
    notify_email = Column(Boolean, default=True)
    notify_telegram = Column(Boolean, default=False)
    notify_push = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    last_triggered_at = Column(DateTime, nullable=True)

    asset = relationship("Asset", back_populates="alerts")
    user = relationship("User", back_populates="alerts")
    events = relationship("AlertEvent", back_populates="alert")


class AlertEvent(Base):
    """Historial de alertas disparadas"""
    __tablename__ = "alert_events"

    id = Column(Integer, primary_key=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    triggered_at = Column(DateTime, server_default=func.now())
    trigger_price = Column(Float, nullable=True)
    trigger_value = Column(Float, nullable=True)
    signal_strength = Column(Enum(SignalStrength), nullable=True)
    message = Column(Text)
    indicators_snapshot = Column(JSON)  # Snapshot de todos los indicadores al momento

    alert = relationship("Alert", back_populates="events")


class TechnicalSignal(Base):
    """Señales técnicas calculadas automáticamente"""
    __tablename__ = "technical_signals"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    timeframe = Column(String(10), nullable=False)
    signal = Column(Enum(SignalStrength), nullable=False)
    score = Column(Float)  # -100 a +100
    indicators = Column(JSON)  # Todos los valores calculados
    reasoning = Column(Text)   # Explicación de la señal
    calculated_at = Column(DateTime, server_default=func.now())
