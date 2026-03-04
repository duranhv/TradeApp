"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, Filter } from "lucide-react";
import { getScreener } from "@/services/api";
import { SignalBadge } from "@/components/dashboard/SignalBadge";
import type { SignalType } from "@/types/market";
import Link from "next/link";

const SIGNAL_OPTIONS = [
  { value: "", label: "Todas las señales" },
  { value: "strong_buy", label: "Compra Fuerte" },
  { value: "buy", label: "Comprar" },
  { value: "neutral", label: "Neutral" },
  { value: "sell", label: "Vender" },
  { value: "strong_sell", label: "Venta Fuerte" },
];

const PANEL_OPTIONS = [
  { value: "acciones", label: "Acciones" },
  { value: "cedears", label: "CEDEARs" },
  { value: "bonos", label: "Bonos" },
  { value: "letras", label: "Letras" },
];

export default function ScreenerPage() {
  const [panel, setPanel] = useState("acciones");
  const [signalFilter, setSignalFilter] = useState("");

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["screener", panel, signalFilter],
    queryFn: () =>
      getScreener({
        panel,
        signal_filter: signalFilter || undefined,
        limit: 30,
      }),
    staleTime: 5 * 60 * 1000,
  });

  return (
    <main className="min-h-screen bg-slate-50 dark:bg-slate-900 p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Search className="w-6 h-6 text-blue-600" />
            Screener Técnico
          </h1>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Actualizar
          </button>
        </div>

        {/* Filtros */}
        <div className="bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm border border-slate-200 dark:border-slate-700">
          <div className="flex gap-4 flex-wrap items-center">
            <Filter className="w-4 h-4 text-slate-400" />
            <div className="flex gap-2">
              {PANEL_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setPanel(opt.value)}
                  className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                    panel === opt.value
                      ? "bg-blue-600 text-white border-blue-600"
                      : "border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            <select
              value={signalFilter}
              onChange={(e) => setSignalFilter(e.target.value)}
              className="px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
            >
              {SIGNAL_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Stats */}
        {data && (
          <div className="text-sm text-slate-500 dark:text-slate-400">
            Analizados: <strong>{data.analyzed}</strong> · Resultados: <strong>{data.matches}</strong>
          </div>
        )}

        {/* Table */}
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-x-auto">
          {isLoading ? (
            <div className="p-12 text-center text-slate-500">Ejecutando screener...</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-700/50 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                  <th className="px-4 py-3 text-left">Ticker</th>
                  <th className="px-4 py-3 text-right">Precio</th>
                  <th className="px-4 py-3 text-right">Var %</th>
                  <th className="px-4 py-3 text-center">Señal</th>
                  <th className="px-4 py-3 text-center">Score</th>
                  <th className="px-4 py-3 text-center">RSI</th>
                  <th className="px-4 py-3 text-center">SMA20</th>
                  <th className="px-4 py-3 text-center">MACD</th>
                  <th className="px-4 py-3 text-left">Razón principal</th>
                  <th className="px-4 py-3 text-center">Ver</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {data?.results.map((item) => (
                  <tr key={item.ticker} className="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
                    <td className="px-4 py-3 font-bold text-slate-900 dark:text-white">{item.ticker}</td>
                    <td className="px-4 py-3 text-right font-medium text-slate-900 dark:text-white">
                      ${item.price.toLocaleString("es-AR")}
                    </td>
                    <td className={`px-4 py-3 text-right font-medium ${
                      (item.change_pct ?? 0) > 0 ? "price-up" : (item.change_pct ?? 0) < 0 ? "price-down" : "price-neutral"
                    }`}>
                      {item.change_pct !== null ? `${item.change_pct > 0 ? "+" : ""}${item.change_pct.toFixed(2)}%` : "—"}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <SignalBadge signal={item.signal as SignalType} size="sm" />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className={`inline-flex items-center justify-center w-10 h-10 rounded-full text-sm font-bold ${
                        item.score >= 40 ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300" :
                        item.score >= 15 ? "bg-green-50 text-green-600" :
                        item.score <= -40 ? "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300" :
                        item.score <= -15 ? "bg-red-50 text-red-600" :
                        "bg-yellow-50 text-yellow-700"
                      }`}>
                        {item.score > 0 ? "+" : ""}{item.score.toFixed(0)}
                      </div>
                    </td>
                    <td className={`px-4 py-3 text-center font-medium ${
                      (item.rsi ?? 50) < 30 ? "text-green-600" :
                      (item.rsi ?? 50) > 70 ? "text-red-600" : "text-slate-600 dark:text-slate-400"
                    }`}>
                      {item.rsi?.toFixed(0) ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {item.above_sma20 === null ? "—" : item.above_sma20 ?
                        <span className="text-green-600">↑</span> :
                        <span className="text-red-600">↓</span>
                      }
                    </td>
                    <td className="px-4 py-3 text-center">
                      {item.macd_bullish === null ? "—" : item.macd_bullish ?
                        <span className="text-green-600 text-xs font-medium">Alcista</span> :
                        <span className="text-red-600 text-xs font-medium">Bajista</span>
                      }
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400 max-w-xs truncate">
                      {item.top_reason}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <Link
                        href={`/analysis?ticker=${item.ticker}`}
                        className="px-2 py-1 text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded hover:bg-blue-100 transition-colors"
                      >
                        Analizar
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </main>
  );
}
