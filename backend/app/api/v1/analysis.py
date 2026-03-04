from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import date, timedelta
import pandas as pd
from app.services.market_data.rava_client import RavaClient
from app.services.technical.engine import TechnicalAnalysisEngine

router = APIRouter(prefix="/analysis", tags=["Technical Analysis"])

rava = RavaClient()
engine = TechnicalAnalysisEngine()


@router.get("/technical/{ticker}")
async def get_technical_analysis(
    ticker: str,
    timeframe: str = Query("1d", description="Temporalidad: 1d, 1w"),
    lookback_days: int = Query(365, description="Días de historia a analizar"),
):
    """
    Análisis técnico completo de un ticker.
    Retorna todos los indicadores y una señal de compra/venta con score.
    """
    date_from = date.today() - timedelta(days=lookback_days)
    bars = await rava.get_historical(ticker.upper(), date_from, date.today())

    if len(bars) < 30:
        raise HTTPException(
            400,
            f"Datos insuficientes para {ticker}. Se obtuvieron {len(bars)} velas (mínimo 30)."
        )

    df = pd.DataFrame(bars)
    df.columns = [c.lower() for c in df.columns]

    result = engine.analyze(df, ticker.upper(), timeframe)

    return {
        "ticker": result.ticker,
        "timeframe": result.timeframe,
        "current_price": result.current_price,
        "signal": result.signal,
        "score": result.score,
        "reasoning": result.reasoning,
        "indicators": {
            "moving_averages": {
                "sma_20": result.sma_20,
                "sma_50": result.sma_50,
                "sma_200": result.sma_200,
                "ema_9": result.ema_9,
                "ema_21": result.ema_21,
                "ema_55": result.ema_55,
            },
            "momentum": {
                "rsi_14": result.rsi_14,
                "stochastic_k": result.stoch_k,
                "stochastic_d": result.stoch_d,
                "cci_20": result.cci_20,
                "williams_r": result.williams_r,
            },
            "macd": {
                "line": result.macd_line,
                "signal": result.macd_signal,
                "histogram": result.macd_histogram,
            },
            "bollinger_bands": {
                "upper": result.bb_upper,
                "middle": result.bb_middle,
                "lower": result.bb_lower,
                "pct_b": result.bb_pct_b,
                "bandwidth": result.bb_bandwidth,
            },
            "volatility": {
                "atr_14": result.atr_14,
            },
            "volume": {
                "obv": result.obv,
                "vwap": result.vwap,
                "mfi_14": result.mfi_14,
            },
            "support_resistance": {
                "pivot": result.pivot,
                "support": result.support,
                "resistance": result.resistance,
            },
        },
    }


@router.get("/screener")
async def market_screener(
    panel: str = Query("acciones", description="Panel a analizar"),
    signal_filter: Optional[str] = Query(None, description="Filtrar por señal: strong_buy, buy, sell, strong_sell"),
    min_score: Optional[float] = Query(None, description="Score mínimo (-100 a 100)"),
    max_score: Optional[float] = Query(None, description="Score máximo"),
    limit: int = Query(20, le=100),
):
    """
    Screener técnico: analiza todo un panel y filtra por señal/score.
    Útil para encontrar oportunidades de trading en todo el mercado.
    """
    quotes = await rava.get_panel_quotes(panel)

    results = []
    analyzed = 0

    for quote in quotes[:50]:  # Limitar para no sobrecargar
        ticker = quote.get("ticker", "")
        if not ticker:
            continue

        try:
            date_from = date.today() - timedelta(days=365)
            bars = await rava.get_historical(ticker, date_from, date.today())

            if len(bars) < 30:
                continue

            df = pd.DataFrame(bars)
            df.columns = [c.lower() for c in df.columns]
            result = engine.analyze(df, ticker, "1d")
            analyzed += 1

            # Aplicar filtros
            if signal_filter and result.signal != signal_filter:
                continue
            if min_score is not None and result.score < min_score:
                continue
            if max_score is not None and result.score > max_score:
                continue

            results.append({
                "ticker": result.ticker,
                "price": result.current_price,
                "signal": result.signal,
                "score": result.score,
                "rsi": result.rsi_14,
                "above_sma20": result.current_price > result.sma_20 if result.sma_20 else None,
                "above_sma50": result.current_price > result.sma_50 if result.sma_50 else None,
                "macd_bullish": result.macd_histogram > 0 if result.macd_histogram else None,
                "bb_position": result.bb_pct_b,
                "top_reason": result.reasoning[0] if result.reasoning else "",
                "change_pct": quote.get("change_pct"),
                "volume": quote.get("volume"),
            })

        except Exception:
            continue

        if len(results) >= limit:
            break

    results.sort(key=lambda x: x["score"], reverse=True)
    return {
        "panel": panel,
        "analyzed": analyzed,
        "matches": len(results),
        "results": results,
    }
