from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, Enum, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class AssetType(str, enum.Enum):
    ACCION = "accion"
    CEDEAR = "cedear"
    BONO = "bono"
    LETRA = "letra"
    ON = "on"               # Obligacion Negociable
    FCI = "fci"             # Fondo Comun de Inversion
    CAUCION = "caucion"
    PLAZO_FIJO = "plazo_fijo"
    FUTURO = "futuro"
    OPCION = "opcion"


class Currency(str, enum.Enum):
    ARS = "ARS"
    USD = "USD"
    USD_MEP = "USD_MEP"     # Dólar MEP / Bolsa
    USD_CCL = "USD_CCL"     # Contado con Liquidación


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    asset_type = Column(Enum(AssetType), nullable=False, index=True)
    currency = Column(Enum(Currency), default=Currency.ARS)
    market = Column(String(50), default="BYMA")   # BYMA, MATBA, etc.
    is_active = Column(Boolean, default=True)

    # Para bonos/letras/ONs
    maturity_date = Column(DateTime, nullable=True)
    coupon_rate = Column(Float, nullable=True)
    issuer = Column(String(200), nullable=True)

    # Para CEDEARs
    underlying_ticker = Column(String(20), nullable=True)  # Ticker en NYSE/NASDAQ
    ratio = Column(Float, nullable=True)                    # Ratio de conversión

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    prices = relationship("PriceBar", back_populates="asset", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="asset")


class PriceBar(Base):
    """OHLCV data - TimescaleDB hypertable (particionado por timestamp)"""
    __tablename__ = "price_bars"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    timeframe = Column(String(10), nullable=False)  # 1m, 5m, 15m, 1h, 1d
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, default=0)
    trades = Column(Integer, default=0)

    asset = relationship("Asset", back_populates="prices")

    __table_args__ = (
        Index("ix_price_bars_asset_timeframe_ts", "asset_id", "timeframe", "timestamp"),
    )


class MarketRate(Base):
    """Tasas del mercado de dinero para comparador"""
    __tablename__ = "market_rates"

    id = Column(Integer, primary_key=True)
    source = Column(String(50), nullable=False)        # BCRA, BYMA, Banco X
    instrument_type = Column(String(50), nullable=False)  # plazo_fijo, caucion, letra
    instrument_name = Column(String(200))
    tna = Column(Float, nullable=True)     # Tasa Nominal Anual
    tea = Column(Float, nullable=True)     # Tasa Efectiva Anual
    tem = Column(Float, nullable=True)     # Tasa Efectiva Mensual
    currency = Column(Enum(Currency), default=Currency.ARS)
    min_days = Column(Integer, nullable=True)
    max_days = Column(Integer, nullable=True)
    min_amount = Column(Float, nullable=True)
    extra_data = Column(Text, nullable=True)  # JSON con datos adicionales
    recorded_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_market_rates_type_recorded", "instrument_type", "recorded_at"),
    )
