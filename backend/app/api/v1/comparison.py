from fastapi import APIRouter, Query
from app.services.market_data.bcra_client import BCRAClient
from app.services.market_data.rava_client import CafciClient
from app.services.comparison.rate_comparator import RateComparator

router = APIRouter(prefix="/comparison", tags=["Rate Comparison"])

bcra = BCRAClient()
cafci = CafciClient()
comparator = RateComparator()


@router.get("/rates")
async def compare_rates(
    horizon_days: int = Query(30, description="Horizonte de inversión en días", ge=1, le=1825),
    amount: float = Query(1_000_000, description="Capital a invertir en ARS"),
    currency: str = Query("ARS", description="Moneda: ARS o USD"),
):
    """
    Cuadro comparativo de tasas y rendimientos.

    Compara PF, Caución, Letras, FCIs y más, para un horizonte y capital dado.
    Ideal para decidir dónde colocar efectivo a corto/mediano plazo.
    """
    # Obtener tasas de fuentes externas
    bcra_rates = await bcra.get_key_rates()
    fci_rates = await cafci.get_money_market_funds()

    # Cauciones típicas (en producción vendría de BYMA en tiempo real)
    caucion_rates = [
        {"days": 1, "tna": 105.0},
        {"days": 7, "tna": 107.0},
        {"days": 14, "tna": 108.0},
        {"days": 30, "tna": 110.0},
    ]

    # Letras típicas (en producción vendría de cotizaciones reales)
    bond_quotes = []

    result = comparator.build_comparison(
        bcra_rates=bcra_rates,
        caucion_rates=caucion_rates,
        fci_rates=fci_rates,
        bond_quotes=bond_quotes,
        horizon_days=horizon_days,
        currency=currency,
        amount=amount,
    )

    table = comparator.to_dataframe_dict(result)

    return {
        "horizon_days": horizon_days,
        "currency": currency,
        "amount": amount,
        "reference_rates": {
            "bcra_tasa_politica": bcra_rates.get("tna_politica_monetaria"),
            "badlar_privados": bcra_rates.get("tna_badlar_privados"),
            "inflacion_mensual": bcra_rates.get("inflacion_mensual"),
            "usd_oficial": bcra_rates.get("usd_minorista"),
        },
        "comparison_table": table,
        "count": len(table),
    }


@router.get("/bond-ytm")
async def calculate_bond_ytm(
    ticker: str = Query(..., description="Ticker del bono (ej: AL30)"),
    market_price: float = Query(..., description="Precio de mercado"),
    face_value: float = Query(100.0, description="Valor nominal (VN)"),
    coupon_rate: float = Query(..., description="Tasa de cupón anual (%)"),
    years_to_maturity: float = Query(..., description="Años al vencimiento"),
):
    """
    Calcula la TIR/YTM de un bono dado su precio de mercado.
    Útil para comparar rendimientos de bonos soberanos y corporativos.
    """
    ytm = comparator.yield_to_maturity(
        price=market_price,
        face_value=face_value,
        coupon_rate=coupon_rate,
        years_to_maturity=years_to_maturity,
    )

    return {
        "ticker": ticker.upper(),
        "market_price": market_price,
        "face_value": face_value,
        "coupon_rate": coupon_rate,
        "years_to_maturity": years_to_maturity,
        "ytm_annual": round(ytm, 2),
        "ytm_interpretation": (
            "El bono rinde más que el cupón (compra con descuento)" if ytm > coupon_rate
            else "El bono rinde menos que el cupón (compra con prima)" if ytm < coupon_rate
            else "El bono cotiza a la par"
        ),
    }


@router.get("/summary")
async def rates_summary():
    """Resumen ejecutivo de tasas del mercado. Vista rápida para el dashboard."""
    bcra_rates = await bcra.get_key_rates()

    pf_tna = bcra_rates.get("tna_pf_privados") or 0
    badlar = bcra_rates.get("tna_badlar_privados") or 0
    politica = bcra_rates.get("tna_politica_monetaria") or 0
    inflacion = bcra_rates.get("inflacion_interanual") or 0

    return {
        "plazo_fijo_privados_tna": pf_tna,
        "plazo_fijo_privados_tea": comparator.tna_to_tea(pf_tna) if pf_tna else None,
        "badlar_privados": badlar,
        "tasa_politica_monetaria": politica,
        "inflacion_interanual": inflacion,
        "tasa_real_pf": (pf_tna - inflacion) if pf_tna and inflacion else None,
        "usd_oficial": bcra_rates.get("usd_minorista"),
        "note": "Tasas en % TNA. Fuente: BCRA API.",
    }
