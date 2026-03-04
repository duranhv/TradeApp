export type AssetType =
  | "accion"
  | "cedear"
  | "bono"
  | "letra"
  | "on"
  | "fci"
  | "caucion"
  | "plazo_fijo";

export type Currency = "ARS" | "USD" | "USD_MEP" | "USD_CCL";

export type SignalType =
  | "strong_buy"
  | "buy"
  | "neutral"
  | "sell"
  | "strong_sell";

export interface Quote {
  ticker: string;
  name?: string;
  last: number | null;
  open: number | null;
  high: number | null;
  low: number | null;
  close_prev: number | null;
  change_pct: number | null;
  volume: number | null;
  bid?: number | null;
  ask?: number | null;
  timestamp: string;
}

export interface OHLCV {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface TechnicalIndicators {
  moving_averages: {
    sma_20: number | null;
    sma_50: number | null;
    sma_200: number | null;
    ema_9: number | null;
    ema_21: number | null;
    ema_55: number | null;
  };
  momentum: {
    rsi_14: number | null;
    stochastic_k: number | null;
    stochastic_d: number | null;
    cci_20: number | null;
    williams_r: number | null;
  };
  macd: {
    line: number | null;
    signal: number | null;
    histogram: number | null;
  };
  bollinger_bands: {
    upper: number | null;
    middle: number | null;
    lower: number | null;
    pct_b: number | null;
    bandwidth: number | null;
  };
  volatility: {
    atr_14: number | null;
  };
  volume: {
    obv: number | null;
    vwap: number | null;
    mfi_14: number | null;
  };
  support_resistance: {
    pivot: number | null;
    support: number | null;
    resistance: number | null;
  };
}

export interface TechnicalAnalysis {
  ticker: string;
  timeframe: string;
  current_price: number;
  signal: SignalType;
  score: number;
  reasoning: string[];
  indicators: TechnicalIndicators;
}

export interface RateComparisonRow {
  tipo: string;
  instrumento: string;
  emisor: string;
  tna: string;
  tea: string;
  tem: string;
  moneda: string;
  plazo_min: string;
  liquidez: string;
  riesgo: string;
  retorno_proyectado: string;
  capital_final: string;
  notas: string;
}

export interface RateComparison {
  horizon_days: number;
  currency: string;
  amount: number;
  reference_rates: {
    bcra_tasa_politica: number | null;
    badlar_privados: number | null;
    inflacion_mensual: number | null;
    usd_oficial: number | null;
  };
  comparison_table: RateComparisonRow[];
  count: number;
}

export interface BCRAKeys {
  tna_pf_privados: number | null;
  tna_pf_publicos: number | null;
  tna_badlar_privados: number | null;
  tna_politica_monetaria: number | null;
  inflacion_mensual: number | null;
  inflacion_interanual: number | null;
  usd_minorista: number | null;
  usd_mayorista: number | null;
  tea_pf_privados?: number | null;
}

export interface ScreenerResult {
  ticker: string;
  price: number;
  signal: SignalType;
  score: number;
  rsi: number | null;
  above_sma20: boolean | null;
  above_sma50: boolean | null;
  macd_bullish: boolean | null;
  bb_position: number | null;
  top_reason: string;
  change_pct: number | null;
  volume: number | null;
}
