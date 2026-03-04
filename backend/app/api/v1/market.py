from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.core.database import get_db
from app.services.market_data.rava_client import RavaClient, CafciClient
from app.services.market_data.bcra_client import BCRAClient

router = APIRouter(prefix="/market", tags=["Market Data"])

rava = RavaClient()
cafci = CafciClient()
bcra = BCRAClient()


@router.get("/quotes/{panel}")
async def get_quotes(
    panel: str = "acciones",
    db: AsyncSession = Depends(get_db),
):
    """
    Cotizaciones en tiempo real por panel.
    Paneles disponibles: acciones, cedears, bonos, letras, on
    """
    valid_panels = ["acciones", "cedears", "bonos", "letras", "on"]
    if panel not in valid_panels:
        raise HTTPException(400, f"Panel inválido. Opciones: {valid_panels}")

    quotes = await rava.get_panel_quotes(panel)
    return {"panel": panel, "count": len(quotes), "data": quotes}


@router.get("/quote/{ticker}")
async def get_ticker_quote(ticker: str):
    """Cotización individual de un ticker."""
    quote = await rava.get_quote(ticker.upper())
    if not quote:
        raise HTTPException(404, f"No se encontró cotización para {ticker}")
    return quote


@router.get("/history/{ticker}")
async def get_history(
    ticker: str,
    date_from: str = Query(..., description="Fecha inicio YYYY-MM-DD"),
    date_to: str = Query(None, description="Fecha fin YYYY-MM-DD (default: hoy)"),
):
    """Datos históricos OHLCV de un ticker."""
    from datetime import date, datetime
    d_from = datetime.strptime(date_from, "%Y-%m-%d").date()
    d_to = datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else date.today()

    bars = await rava.get_historical(ticker.upper(), d_from, d_to)
    return {"ticker": ticker.upper(), "count": len(bars), "bars": bars}


@router.get("/bcra/rates")
async def get_bcra_rates():
    """Tasas de referencia del BCRA (política monetaria, PF, BADLAR, etc.)"""
    rates = await bcra.get_key_rates()
    return {"source": "BCRA", "data": rates}


@router.get("/bcra/exchange")
async def get_exchange_rates():
    """Cotizaciones del dólar oficial (BNA y mayorista)."""
    rates = await bcra.get_exchange_rates()
    return {"source": "BCRA", "data": rates}


@router.get("/fci/money-market")
async def get_money_market_funds():
    """Rendimientos de los principales FCIs Money Market."""
    funds = await cafci.get_money_market_funds()
    return {"source": "CAFCI", "count": len(funds), "data": funds}


@router.get("/all-panels")
async def get_all_panels():
    """Cotizaciones de todos los paneles (acciones, CEDEARs, bonos, letras, ONs)."""
    all_data = await rava.get_all_quotes_parallel()
    summary = {panel: len(quotes) for panel, quotes in all_data.items()}
    return {"summary": summary, "data": all_data}
