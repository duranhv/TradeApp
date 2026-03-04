"""
Comparador de Tasas y Rendimientos.
Genera cuadros comparativos entre PF, Caución, Letras, FCI, ONs, Bonos, etc.
"""
from dataclasses import dataclass, field
from typing import Optional
import math


@dataclass
class RateEntry:
    instrument_type: str       # plazo_fijo, caucion, letra, fci, on, bono
    name: str
    issuer: str
    tna: Optional[float]       # Tasa Nominal Anual (%)
    tea: Optional[float]       # Tasa Efectiva Anual (%)
    tem: Optional[float]       # Tasa Efectiva Mensual (%)
    currency: str              # ARS, USD
    min_days: Optional[int]
    max_days: Optional[int]
    min_amount: Optional[float]
    risk_level: str            # bajo, medio, alto
    liquidity: str             # T+0, T+1, T+2, al vencimiento
    notes: str = ""


@dataclass
class ComparisonResult:
    """Resultado del comparador para un horizonte de inversión dado."""
    horizon_days: int
    currency: str
    amount: float
    entries: list[RateEntry] = field(default_factory=list)

    def projected_return(self, entry: RateEntry) -> Optional[float]:
        """Calcula el retorno proyectado en pesos/USD para el horizonte dado."""
        if entry.tna is None:
            return None
        tna_decimal = entry.tna / 100
        return self.amount * tna_decimal * (self.horizon_days / 365)

    def final_amount(self, entry: RateEntry) -> Optional[float]:
        projected = self.projected_return(entry)
        if projected is None:
            return None
        return self.amount + projected

    def effective_rate_for_period(self, entry: RateEntry) -> Optional[float]:
        """Tasa efectiva para el período de inversión específico."""
        if entry.tna is None:
            return None
        tna_decimal = entry.tna / 100
        return tna_decimal * (self.horizon_days / 365) * 100


class RateComparator:
    """
    Consolida tasas de múltiples fuentes y genera comparativas.
    """

    @staticmethod
    def tna_to_tea(tna_pct: float, capitalization_periods: int = 12) -> float:
        """Convierte TNA a TEA."""
        tna = tna_pct / 100
        tea = (1 + tna / capitalization_periods) ** capitalization_periods - 1
        return tea * 100

    @staticmethod
    def tna_to_tem(tna_pct: float) -> float:
        """Convierte TNA a TEM."""
        tna = tna_pct / 100
        tem = (1 + tna / 12) - 1
        return tem * 100

    @staticmethod
    def tea_to_tna(tea_pct: float, capitalization_periods: int = 12) -> float:
        """Convierte TEA a TNA."""
        tea = tea_pct / 100
        tna = ((1 + tea) ** (1 / capitalization_periods) - 1) * capitalization_periods
        return tna * 100

    @staticmethod
    def yield_to_maturity(
        price: float,
        face_value: float,
        coupon_rate: float,
        years_to_maturity: float,
        payments_per_year: int = 2,
    ) -> float:
        """
        Calcula la Tasa Interna de Retorno (TIR / YTM) de un bono.
        Implementación iterativa (Newton-Raphson simplificado).
        """
        coupon = face_value * (coupon_rate / 100) / payments_per_year
        total_periods = int(years_to_maturity * payments_per_year)

        def bond_price(ytm_periodic):
            pv_coupons = sum(
                coupon / (1 + ytm_periodic) ** t
                for t in range(1, total_periods + 1)
            )
            pv_face = face_value / (1 + ytm_periodic) ** total_periods
            return pv_coupons + pv_face

        # Newton-Raphson
        ytm = 0.10 / payments_per_year  # Estimación inicial
        for _ in range(100):
            price_calc = bond_price(ytm)
            delta = 1e-6
            derivative = (bond_price(ytm + delta) - bond_price(ytm - delta)) / (2 * delta)
            if abs(derivative) < 1e-10:
                break
            ytm_new = ytm - (price_calc - price) / derivative
            if abs(ytm_new - ytm) < 1e-10:
                ytm = ytm_new
                break
            ytm = ytm_new

        return ytm * payments_per_year * 100  # Anualizar y convertir a %

    def build_comparison(
        self,
        bcra_rates: dict,
        caucion_rates: list[dict],
        fci_rates: list[dict],
        bond_quotes: list[dict],
        horizon_days: int = 30,
        currency: str = "ARS",
        amount: float = 1_000_000,
    ) -> ComparisonResult:
        """
        Construye la tabla comparativa consolidada.

        Args:
            bcra_rates: Tasas del BCRA (PF, BADLAR, etc.)
            caucion_rates: Tasas de cauciones de BYMA
            fci_rates: Rendimientos de FCIs de CAFCI
            bond_quotes: Cotizaciones de bonos/letras
            horizon_days: Horizonte de inversión en días
            currency: Moneda de comparación
            amount: Capital a invertir
        """
        result = ComparisonResult(
            horizon_days=horizon_days,
            currency=currency,
            amount=amount,
        )

        if currency == "ARS":
            # ── Plazo Fijo ────────────────────────────────────────────────
            if bcra_rates.get("tna_pf_privados"):
                tna = bcra_rates["tna_pf_privados"]
                result.entries.append(RateEntry(
                    instrument_type="plazo_fijo",
                    name="Plazo Fijo (bancos privados)",
                    issuer="Bancos Privados",
                    tna=tna,
                    tea=self.tna_to_tea(tna),
                    tem=self.tna_to_tem(tna),
                    currency="ARS",
                    min_days=30,
                    max_days=180,
                    min_amount=1000,
                    risk_level="bajo",
                    liquidity="al vencimiento",
                    notes="Garantizado por FGD hasta $6M",
                ))

            if bcra_rates.get("tna_pf_publicos"):
                tna = bcra_rates["tna_pf_publicos"]
                result.entries.append(RateEntry(
                    instrument_type="plazo_fijo",
                    name="Plazo Fijo (bancos públicos)",
                    issuer="Bancos Públicos",
                    tna=tna,
                    tea=self.tna_to_tea(tna),
                    tem=self.tna_to_tem(tna),
                    currency="ARS",
                    min_days=30,
                    max_days=180,
                    min_amount=1000,
                    risk_level="bajo",
                    liquidity="al vencimiento",
                    notes="Garantizado por Estado Nacional",
                ))

            # ── Cauciones ─────────────────────────────────────────────────
            for cauc in caucion_rates:
                if cauc.get("tna"):
                    result.entries.append(RateEntry(
                        instrument_type="caucion",
                        name=f"Caución {cauc.get('days', '?')}d",
                        issuer="BYMA",
                        tna=cauc["tna"],
                        tea=self.tna_to_tea(cauc["tna"]),
                        tem=self.tna_to_tem(cauc["tna"]),
                        currency="ARS",
                        min_days=cauc.get("days", 1),
                        max_days=cauc.get("days", 7),
                        min_amount=None,
                        risk_level="bajo",
                        liquidity=f"T+{cauc.get('days', 1)}",
                        notes="Garantizada por BYMA/MAAV",
                    ))

            # ── FCIs Money Market ─────────────────────────────────────────
            for fci in fci_rates[:5]:  # Top 5
                if fci.get("tna_30d"):
                    result.entries.append(RateEntry(
                        instrument_type="fci",
                        name=fci.get("name", "FCI MM"),
                        issuer=fci.get("manager", ""),
                        tna=fci["tna_30d"],
                        tea=self.tna_to_tea(fci["tna_30d"]),
                        tem=self.tna_to_tem(fci["tna_30d"]),
                        currency="ARS",
                        min_days=1,
                        max_days=None,
                        min_amount=None,
                        risk_level="bajo",
                        liquidity="T+0",
                        notes="Rescate inmediato 24/7",
                    ))

            # ── Bonos y Letras ────────────────────────────────────────────
            for bond in bond_quotes:
                if bond.get("tir") and bond.get("currency") == "ARS":
                    days = bond.get("days_to_maturity", 0)
                    result.entries.append(RateEntry(
                        instrument_type=bond.get("type", "letra"),
                        name=bond.get("ticker", ""),
                        issuer="Tesoro Nacional",
                        tna=bond.get("tna"),
                        tea=bond.get("tea") or (self.tna_to_tea(bond["tna"]) if bond.get("tna") else None),
                        tem=self.tna_to_tem(bond["tna"]) if bond.get("tna") else None,
                        currency="ARS",
                        min_days=days,
                        max_days=days,
                        min_amount=None,
                        risk_level="bajo",
                        liquidity="T+1",
                        notes=f"Vence en {days} días",
                    ))

        # Ordenar por TNA descendente
        result.entries.sort(key=lambda x: x.tna or 0, reverse=True)
        return result

    def to_dataframe_dict(self, result: ComparisonResult) -> list[dict]:
        """Convierte el resultado a formato de tabla para la API."""
        rows = []
        for entry in result.entries:
            projected = result.projected_return(entry)
            rows.append({
                "tipo": entry.instrument_type.replace("_", " ").title(),
                "instrumento": entry.name,
                "emisor": entry.issuer,
                "tna": f"{entry.tna:.2f}%" if entry.tna else "-",
                "tea": f"{entry.tea:.2f}%" if entry.tea else "-",
                "tem": f"{entry.tem:.2f}%" if entry.tem else "-",
                "moneda": entry.currency,
                "plazo_min": f"{entry.min_days}d" if entry.min_days else "-",
                "liquidez": entry.liquidity,
                "riesgo": entry.risk_level,
                "retorno_proyectado": f"${projected:,.0f}" if projected else "-",
                "capital_final": f"${result.final_amount(entry):,.0f}" if projected else "-",
                "notas": entry.notes,
            })
        return rows
