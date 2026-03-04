import axios from "axios";
import type {
  Quote,
  OHLCV,
  TechnicalAnalysis,
  RateComparison,
  BCRAKeys,
  ScreenerResult,
} from "@/types/market";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

// ── Market Data ───────────────────────────────────────────────────────────────

export async function getPanelQuotes(panel: string): Promise<Quote[]> {
  const { data } = await api.get(`/market/quotes/${panel}`);
  return data.data;
}

export async function getTickerQuote(ticker: string): Promise<Quote> {
  const { data } = await api.get(`/market/quote/${ticker}`);
  return data;
}

export async function getHistory(
  ticker: string,
  dateFrom: string,
  dateTo?: string
): Promise<OHLCV[]> {
  const params: Record<string, string> = { date_from: dateFrom };
  if (dateTo) params.date_to = dateTo;
  const { data } = await api.get(`/market/history/${ticker}`, { params });
  return data.bars;
}

export async function getBCRARates(): Promise<BCRAKeys> {
  const { data } = await api.get("/market/bcra/rates");
  return data.data;
}

export async function getMoneyMarketFunds() {
  const { data } = await api.get("/market/fci/money-market");
  return data.data;
}

// ── Technical Analysis ────────────────────────────────────────────────────────

export async function getTechnicalAnalysis(
  ticker: string,
  timeframe: string = "1d",
  lookbackDays: number = 365
): Promise<TechnicalAnalysis> {
  const { data } = await api.get(`/analysis/technical/${ticker}`, {
    params: { timeframe, lookback_days: lookbackDays },
  });
  return data;
}

export async function getScreener(params: {
  panel?: string;
  signal_filter?: string;
  min_score?: number;
  max_score?: number;
  limit?: number;
}): Promise<{ results: ScreenerResult[]; analyzed: number; matches: number }> {
  const { data } = await api.get("/analysis/screener", { params });
  return data;
}

// ── Rate Comparison ───────────────────────────────────────────────────────────

export async function getRateComparison(params: {
  horizon_days: number;
  amount: number;
  currency: string;
}): Promise<RateComparison> {
  const { data } = await api.get("/comparison/rates", { params });
  return data;
}

export async function getRatesSummary() {
  const { data } = await api.get("/comparison/summary");
  return data;
}

export async function calculateBondYTM(params: {
  ticker: string;
  market_price: number;
  face_value?: number;
  coupon_rate: number;
  years_to_maturity: number;
}) {
  const { data } = await api.get("/comparison/bond-ytm", { params });
  return data;
}
