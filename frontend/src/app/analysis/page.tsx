"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, TrendingUp, Activity } from "lucide-react";
import { getTechnicalAnalysis, getHistory } from "@/services/api";
import { SignalBadge } from "@/components/dashboard/SignalBadge";
import { PriceChart } from "@/components/charts/PriceChart";
import type { SignalType } from "@/types/market";
import { format, subDays } from "date-fns";

const POPULAR_TICKERS = [
  "GGAL", "YPF", "BMA", "PAMP", "TXAR", "COME", "MIRG", "ALUA",
  "VIST", "SUPV", "BYMA", "CRES", "LOMA", "CEPU",
];

function IndicatorRow({ label, value, signal }: { label: string; value: string | null; signal?: string }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-700 last:border-0">
      <span className="text-sm text-slate-600 dark:text-slate-400">{label}</span>
      <span className={`text-sm font-medium ${
        signal === "bull" ? "text-green-600 dark:text-green-400" :
        signal === "bear" ? "text-red-600 dark:text-red-400" :
        "text-slate-900 dark:text-white"
      }`}>
        {value ?? "—"}
      </span>
    </div>
  );
}

export default function AnalysisPage() {
  const [ticker, setTicker] = useState("GGAL");
  const [inputTicker, setInputTicker] = useState("GGAL");

  const dateFrom = format(subDays(new Date(), 365), "yyyy-MM-dd");

  const { data: history, isLoading: loadingHistory } = useQuery({
    queryKey: ["history", ticker],
    queryFn: () => getHistory(ticker, dateFrom),
    enabled: !!ticker,
  });

  const { data: analysis, isLoading: loadingAnalysis } = useQuery({
    queryKey: ["technical", ticker],
    queryFn: () => getTechnicalAnalysis(ticker, "1d", 365),
    enabled: !!ticker,
    staleTime: 5 * 60 * 1000,
  });

  const isLoading = loadingHistory || loadingAnalysis;

  return (
    <main className="min-h-screen bg-slate-50 dark:bg-slate-900 p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Search */}
        <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm border border-slate-200 dark:border-slate-700">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
            <Activity className="w-6 h-6 text-blue-600" />
            Análisis Técnico
          </h1>
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={inputTicker}
                onChange={(e) => setInputTicker(e.target.value.toUpperCase())}
                onKeyDown={(e) => e.key === "Enter" && setTicker(inputTicker)}
                placeholder="Ej: GGAL, YPF, AL30..."
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>
            <button
              onClick={() => setTicker(inputTicker)}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Analizar
            </button>
          </div>
          <div className="flex gap-2 mt-3 flex-wrap">
            {POPULAR_TICKERS.map((t) => (
              <button
                key={t}
                onClick={() => { setTicker(t); setInputTicker(t); }}
                className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
                  ticker === t
                    ? "bg-blue-600 text-white border-blue-600"
                    : "border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        {isLoading && (
          <div className="text-center py-12 text-slate-500">Analizando {ticker}...</div>
        )}

        {analysis && !isLoading && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Signal + Chart */}
            <div className="lg:col-span-2 space-y-4">
              {/* Signal Summary */}
              <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm border border-slate-200 dark:border-slate-700">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-white">{analysis.ticker}</h2>
                    <p className="text-3xl font-bold text-slate-900 dark:text-white mt-1">
                      ${analysis.current_price.toLocaleString("es-AR")}
                    </p>
                  </div>
                  <SignalBadge signal={analysis.signal as SignalType} score={analysis.score} size="lg" />
                </div>
                <div className="mt-4 space-y-2">
                  <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase">Justificación</p>
                  {analysis.reasoning.map((reason, i) => (
                    <div key={i} className="flex items-start gap-2 text-sm text-slate-700 dark:text-slate-300">
                      <span className="text-blue-500 mt-0.5">▸</span>
                      {reason}
                    </div>
                  ))}
                </div>
              </div>

              {/* Chart */}
              {history && history.length > 0 && (
                <PriceChart
                  data={history}
                  ticker={analysis.ticker}
                  indicators={analysis.indicators}
                />
              )}
            </div>

            {/* Indicators Panel */}
            <div className="space-y-4">
              {/* Medias Móviles */}
              <div className="bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm border border-slate-200 dark:border-slate-700">
                <h3 className="font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-blue-500" />
                  Medias Móviles
                </h3>
                <IndicatorRow
                  label="SMA 20"
                  value={analysis.indicators.moving_averages.sma_20?.toFixed(2) ?? null}
                  signal={analysis.current_price > (analysis.indicators.moving_averages.sma_20 ?? 0) ? "bull" : "bear"}
                />
                <IndicatorRow
                  label="SMA 50"
                  value={analysis.indicators.moving_averages.sma_50?.toFixed(2) ?? null}
                  signal={analysis.current_price > (analysis.indicators.moving_averages.sma_50 ?? 0) ? "bull" : "bear"}
                />
                <IndicatorRow
                  label="SMA 200"
                  value={analysis.indicators.moving_averages.sma_200?.toFixed(2) ?? null}
                  signal={analysis.current_price > (analysis.indicators.moving_averages.sma_200 ?? 0) ? "bull" : "bear"}
                />
                <IndicatorRow label="EMA 9" value={analysis.indicators.moving_averages.ema_9?.toFixed(2) ?? null} />
                <IndicatorRow label="EMA 21" value={analysis.indicators.moving_averages.ema_21?.toFixed(2) ?? null} />
              </div>

              {/* Momentum */}
              <div className="bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm border border-slate-200 dark:border-slate-700">
                <h3 className="font-semibold text-slate-900 dark:text-white mb-3">Momentum</h3>
                <IndicatorRow
                  label="RSI (14)"
                  value={analysis.indicators.momentum.rsi_14?.toFixed(1) ?? null}
                  signal={
                    (analysis.indicators.momentum.rsi_14 ?? 50) < 30 ? "bull" :
                    (analysis.indicators.momentum.rsi_14 ?? 50) > 70 ? "bear" : undefined
                  }
                />
                <IndicatorRow
                  label="Stoch K"
                  value={analysis.indicators.momentum.stochastic_k?.toFixed(1) ?? null}
                />
                <IndicatorRow
                  label="Stoch D"
                  value={analysis.indicators.momentum.stochastic_d?.toFixed(1) ?? null}
                />
                <IndicatorRow label="CCI (20)" value={analysis.indicators.momentum.cci_20?.toFixed(1) ?? null} />
                <IndicatorRow label="Williams %R" value={analysis.indicators.momentum.williams_r?.toFixed(1) ?? null} />
              </div>

              {/* MACD */}
              <div className="bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm border border-slate-200 dark:border-slate-700">
                <h3 className="font-semibold text-slate-900 dark:text-white mb-3">MACD</h3>
                <IndicatorRow label="Línea MACD" value={analysis.indicators.macd.line?.toFixed(3) ?? null} />
                <IndicatorRow label="Señal" value={analysis.indicators.macd.signal?.toFixed(3) ?? null} />
                <IndicatorRow
                  label="Histograma"
                  value={analysis.indicators.macd.histogram?.toFixed(3) ?? null}
                  signal={(analysis.indicators.macd.histogram ?? 0) > 0 ? "bull" : "bear"}
                />
              </div>

              {/* Bollinger */}
              <div className="bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm border border-slate-200 dark:border-slate-700">
                <h3 className="font-semibold text-slate-900 dark:text-white mb-3">Bollinger Bands</h3>
                <IndicatorRow label="Banda Superior" value={analysis.indicators.bollinger_bands.upper?.toFixed(2) ?? null} />
                <IndicatorRow label="Banda Media" value={analysis.indicators.bollinger_bands.middle?.toFixed(2) ?? null} />
                <IndicatorRow label="Banda Inferior" value={analysis.indicators.bollinger_bands.lower?.toFixed(2) ?? null} />
                <IndicatorRow
                  label="Posición %B"
                  value={analysis.indicators.bollinger_bands.pct_b !== null
                    ? `${(analysis.indicators.bollinger_bands.pct_b! * 100).toFixed(0)}%`
                    : null}
                />
              </div>

              {/* Soporte/Resistencia */}
              <div className="bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm border border-slate-200 dark:border-slate-700">
                <h3 className="font-semibold text-slate-900 dark:text-white mb-3">Soporte / Resistencia</h3>
                <IndicatorRow label="Resistencia" value={analysis.indicators.support_resistance.resistance?.toFixed(2) ?? null} signal="bear" />
                <IndicatorRow label="Pivot" value={analysis.indicators.support_resistance.pivot?.toFixed(2) ?? null} />
                <IndicatorRow label="Soporte" value={analysis.indicators.support_resistance.support?.toFixed(2) ?? null} signal="bull" />
                <IndicatorRow label="ATR (14)" value={analysis.indicators.volatility.atr_14?.toFixed(2) ?? null} />
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
