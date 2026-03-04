"""
Cliente para la API pública del BCRA (Banco Central de la República Argentina)
Documentación: https://api.bcra.gob.ar
"""
import httpx
from typing import Optional
from datetime import date, timedelta
from app.core.config import settings


# Variables más relevantes del BCRA
BCRA_VARIABLES = {
    1: "Reservas Internacionales del BCRA (en millones de USD)",
    4: "Tipo de cambio minorista ARS/USD (Promedio Bancos)",
    5: "Tipo de cambio mayorista ARS/USD",
    6: "Tasa de interés de las LELIQs (promedio, TNA %)",
    7: "Tasa de política monetaria (TNA %)",
    15: "Inflación mensual (IPC Nacional - %)",
    16: "Inflación interanual (IPC Nacional - %)",
    17: "Tipo de cambio nominal (Promedio Bancos - BNA)",
    27: "Tasa BADLAR bancos privados (TNA %)",
    28: "Tasa BADLAR bancos públicos (TNA %)",
    29: "Tasa de interés por préstamos entre entidades (CALL, TNA %)",
    34: "Tasa de préstamos personales (TNA %)",
    40: "TNA plazos fijos ($) - hasta 44 días - bancos privados",
    41: "TNA plazos fijos ($) - hasta 44 días - bancos públicos",
}


class BCRAClient:
    """
    Wrapper para la API del BCRA.
    Endpoint: GET /estadisticas/v2.0/datosvariable/{id_variable}/{fecha_desde}/{fecha_hasta}
    """

    def __init__(self):
        self.base_url = settings.BCRA_API_URL
        self.timeout = 15.0

    async def get_variable(
        self,
        variable_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> dict:
        if date_to is None:
            date_to = date.today()
        if date_from is None:
            date_from = date_to - timedelta(days=30)

        url = (
            f"{self.base_url}/estadisticas/v2.0/datosvariable"
            f"/{variable_id}"
            f"/{date_from.strftime('%Y-%m-%d')}"
            f"/{date_to.strftime('%Y-%m-%d')}"
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def get_latest_value(self, variable_id: int) -> Optional[float]:
        """Retorna el último valor disponible de una variable."""
        data = await self.get_variable(variable_id)
        results = data.get("results", [])
        if results:
            return results[-1].get("valor")
        return None

    async def get_key_rates(self) -> dict:
        """Obtiene las tasas clave del mercado en una sola llamada."""
        rates = {}

        rate_vars = {
            "tna_pf_privados": 40,
            "tna_pf_publicos": 41,
            "tna_badlar_privados": 27,
            "tna_badlar_publicos": 28,
            "tna_politica_monetaria": 7,
            "tna_leliq": 6,
            "inflacion_mensual": 15,
            "inflacion_interanual": 16,
            "usd_minorista": 4,
            "usd_mayorista": 5,
        }

        for key, var_id in rate_vars.items():
            try:
                rates[key] = await self.get_latest_value(var_id)
            except Exception:
                rates[key] = None

        # Calcular TEA desde TNA (capitalización mensual)
        if rates.get("tna_pf_privados"):
            tna = rates["tna_pf_privados"] / 100
            rates["tea_pf_privados"] = ((1 + tna / 12) ** 12 - 1) * 100

        if rates.get("tna_pf_publicos"):
            tna = rates["tna_pf_publicos"] / 100
            rates["tea_pf_publicos"] = ((1 + tna / 12) ** 12 - 1) * 100

        return rates

    async def get_exchange_rates(self) -> dict:
        """Obtiene cotizaciones del dólar oficial."""
        return {
            "usd_bna_venta": await self.get_latest_value(4),
            "usd_mayorista": await self.get_latest_value(5),
        }
