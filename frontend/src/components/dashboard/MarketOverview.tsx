"use client";
import { useQuery } from "@tanstack/react-query";
import { TrendingUp, TrendingDown, DollarSign, Percent } from "lucide-react";
import { getBCRARates, getRatesSummary } from "@/services/api";

function StatCard({
  label,
  value,
  sub,
  icon: Icon,
  trend,
}: {
  label: string;
  value: string;
  sub?: string;
  icon: React.ElementType;
  trend?: "up" | "down" | "neutral";
}) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm border border-slate-200 dark:border-slate-700">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide">
          {label}
        </span>
        <Icon
          className={`w-4 h-4 ${
            trend === "up"
              ? "text-green-500"
              : trend === "down"
              ? "text-red-500"
              : "text-slate-400"
          }`}
        />
      </div>
      <p className="text-2xl font-bold text-slate-900 dark:text-white">{value}</p>
      {sub && (
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{sub}</p>
      )}
    </div>
  );
}

export function MarketOverview() {
  const { data: bcra } = useQuery({
    queryKey: ["bcra-rates"],
    queryFn: getBCRARates,
    refetchInterval: 60 * 60 * 1000, // cada hora
  });

  const { data: summary } = useQuery({
    queryKey: ["rates-summary"],
    queryFn: getRatesSummary,
    refetchInterval: 60 * 60 * 1000,
  });

  const pf = bcra?.tna_pf_privados;
  const usd = bcra?.usd_minorista;
  const inflacion = bcra?.inflacion_mensual;
  const politica = bcra?.tna_politica_monetaria;

  return (
    <div>
      <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
        Panorama del Mercado
      </h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Plazo Fijo TNA"
          value={pf ? `${pf.toFixed(1)}%` : "—"}
          sub="Bancos privados"
          icon={Percent}
          trend="neutral"
        />
        <StatCard
          label="Dólar Oficial"
          value={usd ? `$${usd.toFixed(0)}` : "—"}
          sub="BNA venta"
          icon={DollarSign}
          trend="up"
        />
        <StatCard
          label="Inflación Mensual"
          value={inflacion ? `${inflacion.toFixed(1)}%` : "—"}
          sub="IPC Nacional"
          icon={TrendingUp}
          trend={inflacion && inflacion > 5 ? "down" : "up"}
        />
        <StatCard
          label="Tasa Política"
          value={politica ? `${politica.toFixed(1)}%` : "—"}
          sub="TNA BCRA"
          icon={Percent}
          trend="neutral"
        />
      </div>
    </div>
  );
}
