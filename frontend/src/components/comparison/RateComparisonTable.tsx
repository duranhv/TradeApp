"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getRateComparison } from "@/services/api";
import type { RateComparisonRow } from "@/types/market";

const RISK_COLORS: Record<string, string> = {
  bajo: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  medio: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  alto: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
};

const HORIZON_OPTIONS = [
  { label: "1 semana", days: 7 },
  { label: "30 días", days: 30 },
  { label: "60 días", days: 60 },
  { label: "90 días", days: 90 },
  { label: "180 días", days: 180 },
  { label: "1 año", days: 365 },
];

export function RateComparisonTable() {
  const [horizonDays, setHorizonDays] = useState(30);
  const [amount, setAmount] = useState(1_000_000);
  const [currency] = useState("ARS");

  const { data, isLoading, error } = useQuery({
    queryKey: ["rate-comparison", horizonDays, amount, currency],
    queryFn: () => getRateComparison({ horizon_days: horizonDays, amount, currency }),
    staleTime: 5 * 60 * 1000,
  });

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700">
      {/* Header */}
      <div className="p-6 border-b border-slate-200 dark:border-slate-700">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-1">
          Comparador de Tasas y Rendimientos
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          PF · Caución · FCIs · Letras · Bonos — en ARS
        </p>

        <div className="flex flex-wrap gap-4 mt-4">
          {/* Horizonte */}
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
              Horizonte de inversión
            </label>
            <div className="flex gap-2 flex-wrap">
              {HORIZON_OPTIONS.map((opt) => (
                <button
                  key={opt.days}
                  onClick={() => setHorizonDays(opt.days)}
                  className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                    horizonDays === opt.days
                      ? "bg-blue-600 text-white border-blue-600"
                      : "border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Capital */}
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
              Capital a invertir (ARS)
            </label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(Number(e.target.value))}
              className="px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white w-40"
              step={100000}
              min={1000}
            />
          </div>
        </div>
      </div>

      {/* Reference Rates */}
      {data?.reference_rates && (
        <div className="px-6 py-3 bg-slate-50 dark:bg-slate-700/50 border-b border-slate-200 dark:border-slate-700">
          <div className="flex gap-6 text-xs text-slate-600 dark:text-slate-400">
            <span>Tasa política: <strong>{data.reference_rates.bcra_tasa_politica?.toFixed(1)}% TNA</strong></span>
            <span>BADLAR: <strong>{data.reference_rates.badlar_privados?.toFixed(1)}% TNA</strong></span>
            <span>Inflación mensual: <strong>{data.reference_rates.inflacion_mensual?.toFixed(1)}%</strong></span>
            <span>USD oficial: <strong>${data.reference_rates.usd_oficial?.toFixed(0)}</strong></span>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        {isLoading ? (
          <div className="p-12 text-center text-slate-500">Cargando tasas...</div>
        ) : error ? (
          <div className="p-12 text-center text-red-500">Error al cargar tasas</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-700/50 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                <th className="px-4 py-3 text-left">Instrumento</th>
                <th className="px-4 py-3 text-right">TNA</th>
                <th className="px-4 py-3 text-right">TEA</th>
                <th className="px-4 py-3 text-right">TEM</th>
                <th className="px-4 py-3 text-left">Plazo mín.</th>
                <th className="px-4 py-3 text-left">Liquidez</th>
                <th className="px-4 py-3 text-center">Riesgo</th>
                <th className="px-4 py-3 text-right">Retorno {horizonDays}d</th>
                <th className="px-4 py-3 text-right">Capital Final</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
              {data?.comparison_table.map((row: RateComparisonRow, idx: number) => (
                <tr
                  key={idx}
                  className="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="font-medium text-slate-900 dark:text-white">
                      {row.instrumento}
                    </div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">
                      {row.emisor} · {row.tipo}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right font-bold text-green-600 dark:text-green-400">
                    {row.tna}
                  </td>
                  <td className="px-4 py-3 text-right text-slate-700 dark:text-slate-300">
                    {row.tea}
                  </td>
                  <td className="px-4 py-3 text-right text-slate-700 dark:text-slate-300">
                    {row.tem}
                  </td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{row.plazo_min}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{row.liquidez}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${RISK_COLORS[row.riesgo] || ""}`}>
                      {row.riesgo}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-medium text-blue-600 dark:text-blue-400">
                    {row.retorno_proyectado}
                  </td>
                  <td className="px-4 py-3 text-right font-bold text-slate-900 dark:text-white">
                    {row.capital_final}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="px-6 py-3 text-xs text-slate-400 dark:text-slate-500 border-t border-slate-100 dark:border-slate-700">
        Fuentes: BCRA API · CAFCI · BYMA. Tasas indicativas, pueden variar. No constituye asesoramiento financiero.
      </div>
    </div>
  );
}
