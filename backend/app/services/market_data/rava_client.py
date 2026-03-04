"""
Cliente para datos de mercado de Rava Bursátil y byma-data.
Provee cotizaciones de acciones, CEDEARs, bonos y demás instrumentos del mercado argentino.
"""
import httpx
import asyncio
from typing import Optional, List
from datetime import date, datetime
from app.core.config import settings


class RavaClient:
    """
    Scraper/client para cotizaciones de Rava Bursátil.
    Rava expone datos BYMA en formato JSON desde su sitio web.
    """
    BASE_URL = "https://www.rava.com"
    PRICES_URL = f"{BASE_URL}/series/preciostabla.php"
    HISTORY_URL = f"{BASE_URL}/series/cotizaciones.php"

    PANELS = {
        "acciones": "panel=0",
        "cedears": "panel=4",
        "bonos": "panel=2",
        "letras": "panel=3",
        "on": "panel=9",
    }

    def __init__(self):
        self.timeout = 20.0
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; TradeApp/1.0; financial data aggregator)",
            "Accept": "application/json, text/javascript, */*",
            "Referer": "https://www.rava.com/",
        }

    async def get_panel_quotes(self, panel: str = "acciones") -> List[dict]:
        """Obtiene todas las cotizaciones de un panel."""
        panel_param = self.PANELS.get(panel, "panel=0")
        url = f"{self.PRICES_URL}?{panel_param}&tipo=P"

        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        quotes = []
        for item in data.get("cotizaciones", []):
            quotes.append({
                "ticker": item.get("simbolo", "").strip(),
                "name": item.get("descripcion", ""),
                "last": item.get("ultimo"),
                "open": item.get("apertura"),
                "high": item.get("maximo"),
                "low": item.get("minimo"),
                "close_prev": item.get("cierreant"),
                "change_pct": item.get("variacion"),
                "volume": item.get("volumen"),
                "trades": item.get("operaciones"),
                "timestamp": datetime.now().isoformat(),
            })
        return quotes

    async def get_quote(self, ticker: str) -> Optional[dict]:
        """Obtiene cotización de un ticker específico."""
        url = f"{self.PRICES_URL}?especie={ticker}&tipo=P"

        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        cotizaciones = data.get("cotizaciones", [])
        if cotizaciones:
            item = cotizaciones[0]
            return {
                "ticker": ticker,
                "last": item.get("ultimo"),
                "open": item.get("apertura"),
                "high": item.get("maximo"),
                "low": item.get("minimo"),
                "close_prev": item.get("cierreant"),
                "change_pct": item.get("variacion"),
                "volume": item.get("volumen"),
                "bid": item.get("compra"),
                "ask": item.get("venta"),
                "timestamp": datetime.now().isoformat(),
            }
        return None

    async def get_historical(
        self,
        ticker: str,
        date_from: date,
        date_to: date,
    ) -> List[dict]:
        """Obtiene datos históricos OHLCV de un ticker."""
        url = (
            f"{self.HISTORY_URL}?especie={ticker}"
            f"&desde={date_from.strftime('%Y-%m-%d')}"
            f"&hasta={date_to.strftime('%Y-%m-%d')}"
        )

        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        bars = []
        for item in data.get("series", []):
            bars.append({
                "date": item.get("fecha"),
                "open": item.get("apertura"),
                "high": item.get("maximo"),
                "low": item.get("minimo"),
                "close": item.get("cierre"),
                "volume": item.get("volumen", 0),
            })
        return sorted(bars, key=lambda x: x["date"])

    async def get_all_quotes_parallel(self) -> dict:
        """Obtiene cotizaciones de todos los paneles en paralelo."""
        panels = ["acciones", "cedears", "bonos", "letras", "on"]
        tasks = [self.get_panel_quotes(panel) for panel in panels]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_quotes = {}
        for panel, result in zip(panels, results):
            if isinstance(result, Exception):
                all_quotes[panel] = []
            else:
                all_quotes[panel] = result
        return all_quotes


class CafciClient:
    """
    Cliente para la API pública de CAFCI (Cámara Argentina de Fondos Comunes de Inversión).
    Provee datos de cuotapartes y rendimientos de FCIs.
    Documentación: https://api.cafci.org.ar
    """
    BASE_URL = "https://api.cafci.org.ar"

    async def get_funds(self, fund_type: Optional[str] = None) -> List[dict]:
        """Lista todos los fondos disponibles."""
        url = f"{self.BASE_URL}/fondo"
        params = {}
        if fund_type:
            params["tipo"] = fund_type

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json().get("data", [])

    async def get_fund_performance(self, fund_id: int) -> dict:
        """Obtiene rendimientos de un fondo."""
        url = f"{self.BASE_URL}/fondo/{fund_id}/serie"

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def get_money_market_funds(self) -> List[dict]:
        """Retorna los fondos money market (T+0) con sus rendimientos actuales."""
        funds = await self.get_funds(fund_type="1")  # Tipo 1 = Money Market
        enriched = []
        for fund in funds[:20]:  # Top 20 para no sobrecargar
            try:
                perf = await self.get_fund_performance(fund["id"])
                enriched.append({
                    "id": fund["id"],
                    "name": fund.get("nombre"),
                    "manager": fund.get("gerente"),
                    "tna_30d": perf.get("rendimiento30d"),
                    "tna_7d": perf.get("rendimiento7d"),
                    "currency": "ARS",
                    "liquidity": "T+0",
                })
            except Exception:
                pass
        return enriched
