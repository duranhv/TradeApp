import { MarketOverview } from "@/components/dashboard/MarketOverview";
import { RateComparisonTable } from "@/components/comparison/RateComparisonTable";
import { TrendingUp, BarChart2, Bell, Layers } from "lucide-react";
import Link from "next/link";

const NAV_ITEMS = [
  { href: "/screener", label: "Screener", icon: BarChart2, desc: "Buscar oportunidades por señal técnica" },
  { href: "/analysis", label: "Análisis", icon: TrendingUp, desc: "Análisis técnico completo por ticker" },
  { href: "/alerts", label: "Alertas", icon: Bell, desc: "Configura alertas de compra/venta" },
  { href: "/portfolio", label: "Portfolio", icon: Layers, desc: "Seguimiento de tus posiciones" },
];

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* Header */}
      <header className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-xl text-slate-900 dark:text-white">TradeApp</span>
            <span className="text-xs bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300 px-2 py-0.5 rounded-full font-medium">
              Beta
            </span>
          </div>
          <nav className="hidden md:flex gap-1">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
              >
                <item.icon className="w-4 h-4" />
                {item.label}
              </Link>
            ))}
          </nav>
          <Link
            href="/login"
            className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Ingresar
          </Link>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
        {/* Market Overview */}
        <MarketOverview />

        {/* Quick Access */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="bg-white dark:bg-slate-800 rounded-xl p-4 border border-slate-200 dark:border-slate-700 hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-md transition-all group"
            >
              <item.icon className="w-6 h-6 text-blue-600 mb-3 group-hover:scale-110 transition-transform" />
              <h3 className="font-semibold text-slate-900 dark:text-white mb-1">{item.label}</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">{item.desc}</p>
            </Link>
          ))}
        </div>

        {/* Rate Comparison */}
        <RateComparisonTable />

        {/* Disclaimer */}
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-4">
          <p className="text-xs text-amber-800 dark:text-amber-200">
            <strong>Aviso legal:</strong> TradeApp es una herramienta de análisis e información financiera.
            No constituye asesoramiento de inversión. Toda decisión es responsabilidad del inversor.
            Invertir en mercados financieros implica riesgos, incluyendo la pérdida del capital invertido.
          </p>
        </div>
      </div>
    </main>
  );
}
