"""
Motor de Análisis Técnico.
Calcula todos los indicadores y genera señales de compra/venta.
"""
import pandas as pd
import numpy as np
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class IndicatorResult:
    """Resultado completo del análisis técnico para un activo."""
    ticker: str
    timeframe: str
    current_price: float
    signal: str          # strong_buy / buy / neutral / sell / strong_sell
    score: float         # -100 a +100
    reasoning: list[str] = field(default_factory=list)

    # Medias Móviles
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_9: Optional[float] = None
    ema_21: Optional[float] = None
    ema_55: Optional[float] = None

    # Momentum
    rsi_14: Optional[float] = None
    stoch_k: Optional[float] = None
    stoch_d: Optional[float] = None
    cci_20: Optional[float] = None
    williams_r: Optional[float] = None

    # MACD
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None

    # Bollinger Bands
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_pct_b: Optional[float] = None    # Posición dentro de las bandas (0-1)
    bb_bandwidth: Optional[float] = None

    # Volatilidad
    atr_14: Optional[float] = None

    # Volumen
    obv: Optional[float] = None
    vwap: Optional[float] = None
    mfi_14: Optional[float] = None

    # Soporte / Resistencia
    support: Optional[float] = None
    resistance: Optional[float] = None
    pivot: Optional[float] = None


class TechnicalAnalysisEngine:
    """
    Calcula indicadores técnicos y genera señales de trading.
    Usa pandas y cálculos manuales para mayor control y sin deps pesadas.
    """

    def analyze(self, df: pd.DataFrame, ticker: str, timeframe: str = "1d") -> IndicatorResult:
        """
        Análisis completo de un DataFrame OHLCV.

        Args:
            df: DataFrame con columnas [open, high, low, close, volume]
            ticker: Símbolo del activo
            timeframe: Temporalidad del análisis

        Returns:
            IndicatorResult con todos los indicadores calculados y señal generada
        """
        if len(df) < 50:
            return IndicatorResult(
                ticker=ticker,
                timeframe=timeframe,
                current_price=df["close"].iloc[-1],
                signal="neutral",
                score=0,
                reasoning=["Datos insuficientes para análisis confiable (mínimo 50 velas)"],
            )

        df = df.copy().sort_values("date" if "date" in df.columns else df.index.name or "timestamp")
        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"] if "volume" in df.columns else pd.Series(0, index=df.index)

        result = IndicatorResult(
            ticker=ticker,
            timeframe=timeframe,
            current_price=float(close.iloc[-1]),
            signal="neutral",
            score=0,
        )

        # ── Medias Móviles ──────────────────────────────────────────────
        result.sma_20 = self._sma(close, 20)
        result.sma_50 = self._sma(close, 50)
        result.sma_200 = self._sma(close, 200) if len(df) >= 200 else None
        result.ema_9 = self._ema(close, 9)
        result.ema_21 = self._ema(close, 21)
        result.ema_55 = self._ema(close, 55)

        # ── RSI ─────────────────────────────────────────────────────────
        result.rsi_14 = self._rsi(close, 14)

        # ── MACD ────────────────────────────────────────────────────────
        macd_line, macd_signal, macd_hist = self._macd(close)
        result.macd_line = macd_line
        result.macd_signal = macd_signal
        result.macd_histogram = macd_hist

        # ── Bollinger Bands ──────────────────────────────────────────────
        bb_upper, bb_middle, bb_lower = self._bollinger(close, 20, 2)
        result.bb_upper = bb_upper
        result.bb_middle = bb_middle
        result.bb_lower = bb_lower
        if bb_upper and bb_lower and bb_upper != bb_lower:
            result.bb_pct_b = (result.current_price - bb_lower) / (bb_upper - bb_lower)
            result.bb_bandwidth = (bb_upper - bb_lower) / bb_middle if bb_middle else None

        # ── Stochastic ──────────────────────────────────────────────────
        stoch_k, stoch_d = self._stochastic(high, low, close, 14, 3)
        result.stoch_k = stoch_k
        result.stoch_d = stoch_d

        # ── CCI ─────────────────────────────────────────────────────────
        result.cci_20 = self._cci(high, low, close, 20)

        # ── Williams %R ──────────────────────────────────────────────────
        result.williams_r = self._williams_r(high, low, close, 14)

        # ── ATR ─────────────────────────────────────────────────────────
        result.atr_14 = self._atr(high, low, close, 14)

        # ── OBV ─────────────────────────────────────────────────────────
        result.obv = self._obv(close, volume)

        # ── MFI ─────────────────────────────────────────────────────────
        if volume.sum() > 0:
            result.mfi_14 = self._mfi(high, low, close, volume, 14)

        # ── VWAP (solo intradía, para diario usamos pivotes) ─────────────
        if timeframe in ("1m", "5m", "15m", "30m", "1h"):
            result.vwap = self._vwap(high, low, close, volume)

        # ── Soporte y Resistencia (Pivot Points) ─────────────────────────
        pivot, support, resistance = self._pivot_points(
            float(high.iloc[-2]), float(low.iloc[-2]), float(close.iloc[-2])
        )
        result.pivot = pivot
        result.support = support
        result.resistance = resistance

        # ── Generar Señal ────────────────────────────────────────────────
        result.score, result.signal, result.reasoning = self._generate_signal(result)

        return result

    # ─────────────────────────────────────────────────────────────────────
    # Indicadores
    # ─────────────────────────────────────────────────────────────────────

    def _sma(self, series: pd.Series, period: int) -> Optional[float]:
        if len(series) < period:
            return None
        return float(series.rolling(period).mean().iloc[-1])

    def _ema(self, series: pd.Series, period: int) -> Optional[float]:
        if len(series) < period:
            return None
        return float(series.ewm(span=period, adjust=False).mean().iloc[-1])

    def _rsi(self, close: pd.Series, period: int = 14) -> Optional[float]:
        if len(close) < period + 1:
            return None
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
        avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
        rs = avg_gain / avg_loss.replace(0, np.finfo(float).eps)
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])

    def _macd(
        self, close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> tuple[Optional[float], Optional[float], Optional[float]]:
        if len(close) < slow + signal:
            return None, None, None
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        macd_signal = macd_line.ewm(span=signal, adjust=False).mean()
        macd_hist = macd_line - macd_signal
        return float(macd_line.iloc[-1]), float(macd_signal.iloc[-1]), float(macd_hist.iloc[-1])

    def _bollinger(
        self, close: pd.Series, period: int = 20, std_dev: float = 2
    ) -> tuple[Optional[float], Optional[float], Optional[float]]:
        if len(close) < period:
            return None, None, None
        sma = close.rolling(period).mean()
        std = close.rolling(period).std()
        upper = sma + std_dev * std
        lower = sma - std_dev * std
        return float(upper.iloc[-1]), float(sma.iloc[-1]), float(lower.iloc[-1])

    def _stochastic(
        self, high: pd.Series, low: pd.Series, close: pd.Series,
        k_period: int = 14, d_period: int = 3
    ) -> tuple[Optional[float], Optional[float]]:
        if len(close) < k_period:
            return None, None
        lowest_low = low.rolling(k_period).min()
        highest_high = high.rolling(k_period).max()
        denom = (highest_high - lowest_low).replace(0, np.finfo(float).eps)
        k = 100 * (close - lowest_low) / denom
        d = k.rolling(d_period).mean()
        return float(k.iloc[-1]), float(d.iloc[-1])

    def _cci(
        self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20
    ) -> Optional[float]:
        if len(close) < period:
            return None
        typical_price = (high + low + close) / 3
        sma_tp = typical_price.rolling(period).mean()
        mad = typical_price.rolling(period).apply(lambda x: np.abs(x - x.mean()).mean())
        cci = (typical_price - sma_tp) / (0.015 * mad.replace(0, np.finfo(float).eps))
        return float(cci.iloc[-1])

    def _williams_r(
        self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> Optional[float]:
        if len(close) < period:
            return None
        highest_high = high.rolling(period).max()
        lowest_low = low.rolling(period).min()
        denom = (highest_high - lowest_low).replace(0, np.finfo(float).eps)
        wr = -100 * (highest_high - close) / denom
        return float(wr.iloc[-1])

    def _atr(
        self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> Optional[float]:
        if len(close) < period + 1:
            return None
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs(),
        ], axis=1).max(axis=1)
        atr = tr.ewm(com=period - 1, min_periods=period).mean()
        return float(atr.iloc[-1])

    def _obv(self, close: pd.Series, volume: pd.Series) -> Optional[float]:
        if volume.sum() == 0:
            return None
        direction = np.sign(close.diff()).fillna(0)
        obv = (direction * volume).cumsum()
        return float(obv.iloc[-1])

    def _mfi(
        self, high: pd.Series, low: pd.Series, close: pd.Series,
        volume: pd.Series, period: int = 14
    ) -> Optional[float]:
        if len(close) < period:
            return None
        typical_price = (high + low + close) / 3
        money_flow = typical_price * volume
        diff = typical_price.diff()
        pos_flow = money_flow.where(diff > 0, 0).rolling(period).sum()
        neg_flow = money_flow.where(diff < 0, 0).rolling(period).sum()
        mfi = 100 - (100 / (1 + pos_flow / neg_flow.replace(0, np.finfo(float).eps)))
        return float(mfi.iloc[-1])

    def _vwap(
        self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series
    ) -> Optional[float]:
        if volume.sum() == 0:
            return None
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        return float(vwap.iloc[-1])

    def _pivot_points(self, high: float, low: float, close: float) -> tuple[float, float, float]:
        pivot = (high + low + close) / 3
        support = 2 * pivot - high
        resistance = 2 * pivot - low
        return pivot, support, resistance

    # ─────────────────────────────────────────────────────────────────────
    # Generador de Señal Compuesta
    # ─────────────────────────────────────────────────────────────────────

    def _generate_signal(self, r: IndicatorResult) -> tuple[float, str, list[str]]:
        """
        Genera un score de -100 a +100 y una señal cualitativa.
        Ponderación por categoría de indicador.
        """
        score = 0.0
        reasons = []
        price = r.current_price

        # ── Tendencia (peso 35%) ──────────────────────────────────────────
        trend_score = 0.0
        if r.ema_9 and r.ema_21:
            if r.ema_9 > r.ema_21:
                trend_score += 15
                reasons.append("EMA9 > EMA21: tendencia alcista de corto plazo")
            else:
                trend_score -= 15
                reasons.append("EMA9 < EMA21: tendencia bajista de corto plazo")

        if r.sma_20 and r.sma_50:
            if price > r.sma_20 > r.sma_50:
                trend_score += 20
                reasons.append("Precio por encima de SMA20 y SMA50: tendencia alcista")
            elif price < r.sma_20 < r.sma_50:
                trend_score -= 20
                reasons.append("Precio por debajo de SMA20 y SMA50: tendencia bajista")

        score += trend_score * 0.35

        # ── Momentum/RSI (peso 25%) ───────────────────────────────────────
        momentum_score = 0.0
        if r.rsi_14 is not None:
            if r.rsi_14 < 30:
                momentum_score += 80
                reasons.append(f"RSI={r.rsi_14:.1f}: zona de sobreventa (< 30) — posible rebote")
            elif r.rsi_14 < 40:
                momentum_score += 40
                reasons.append(f"RSI={r.rsi_14:.1f}: acercándose a sobreventa")
            elif r.rsi_14 > 70:
                momentum_score -= 80
                reasons.append(f"RSI={r.rsi_14:.1f}: zona de sobrecompra (> 70) — posible corrección")
            elif r.rsi_14 > 60:
                momentum_score -= 40
                reasons.append(f"RSI={r.rsi_14:.1f}: acercándose a sobrecompra")
            else:
                reasons.append(f"RSI={r.rsi_14:.1f}: zona neutral")

        if r.stoch_k is not None and r.stoch_d is not None:
            if r.stoch_k < 20 and r.stoch_d < 20:
                momentum_score += 20
                reasons.append(f"Stochastic K={r.stoch_k:.1f}: sobreventa")
            elif r.stoch_k > 80 and r.stoch_d > 80:
                momentum_score -= 20
                reasons.append(f"Stochastic K={r.stoch_k:.1f}: sobrecompra")

        score += momentum_score * 0.25

        # ── MACD (peso 20%) ───────────────────────────────────────────────
        macd_score = 0.0
        if r.macd_line is not None and r.macd_signal is not None:
            if r.macd_line > r.macd_signal and r.macd_histogram > 0:
                macd_score += 60
                reasons.append("MACD: cruce alcista — momentum positivo")
            elif r.macd_line < r.macd_signal and r.macd_histogram < 0:
                macd_score -= 60
                reasons.append("MACD: cruce bajista — momentum negativo")
            elif r.macd_line > r.macd_signal:
                macd_score += 30
                reasons.append("MACD por encima de señal (histograma negativo)")

        score += macd_score * 0.20

        # ── Bollinger Bands (peso 20%) ────────────────────────────────────
        bb_score = 0.0
        if r.bb_lower and r.bb_upper and r.bb_pct_b is not None:
            if price <= r.bb_lower:
                bb_score += 80
                reasons.append(f"Precio tocando banda inferior de Bollinger: {r.bb_lower:.2f}")
            elif r.bb_pct_b < 0.2:
                bb_score += 40
                reasons.append("Precio en zona baja de las Bandas de Bollinger")
            elif price >= r.bb_upper:
                bb_score -= 80
                reasons.append(f"Precio tocando banda superior de Bollinger: {r.bb_upper:.2f}")
            elif r.bb_pct_b > 0.8:
                bb_score -= 40
                reasons.append("Precio en zona alta de las Bandas de Bollinger")

        score += bb_score * 0.20

        # ── Clasificar señal ──────────────────────────────────────────────
        if score >= 40:
            signal = "strong_buy"
        elif score >= 15:
            signal = "buy"
        elif score <= -40:
            signal = "strong_sell"
        elif score <= -15:
            signal = "sell"
        else:
            signal = "neutral"

        return round(score, 2), signal, reasons
