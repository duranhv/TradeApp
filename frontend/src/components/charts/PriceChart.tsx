"use client";
import { useEffect, useRef } from "react";
import {
  createChart,
  ColorType,
  LineStyle,
  type IChartApi,
  type ISeriesApi,
} from "lightweight-charts";
import type { OHLCV, TechnicalIndicators } from "@/types/market";

interface PriceChartProps {
  data: OHLCV[];
  ticker: string;
  indicators?: TechnicalIndicators;
  height?: number;
}

export function PriceChart({ data, ticker, indicators, height = 400 }: PriceChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartApiRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!chartRef.current || !data.length) return;

    const chart = createChart(chartRef.current, {
      width: chartRef.current.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#94a3b8",
      },
      grid: {
        vertLines: { color: "#1e293b", style: LineStyle.Dotted },
        horzLines: { color: "#1e293b", style: LineStyle.Dotted },
      },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: "#334155" },
      timeScale: {
        borderColor: "#334155",
        timeVisible: true,
      },
    });

    chartApiRef.current = chart;

    // Velas japonesas
    const candleSeries = chart.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    const candleData = data.map((bar) => ({
      time: bar.date as any,
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
    }));

    candleSeries.setData(candleData);

    // Bollinger Bands
    if (indicators?.bollinger_bands) {
      const bbUpper = chart.addLineSeries({
        color: "rgba(59, 130, 246, 0.5)",
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
      });
      const bbMiddle = chart.addLineSeries({
        color: "rgba(59, 130, 246, 0.8)",
        lineWidth: 1,
      });
      const bbLower = chart.addLineSeries({
        color: "rgba(59, 130, 246, 0.5)",
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
      });

      const lastBar = data[data.length - 1];
      const bb = indicators.bollinger_bands;

      if (bb.upper && bb.middle && bb.lower) {
        bbUpper.setData([{ time: lastBar.date as any, value: bb.upper }]);
        bbMiddle.setData([{ time: lastBar.date as any, value: bb.middle }]);
        bbLower.setData([{ time: lastBar.date as any, value: bb.lower }]);
      }
    }

    // SMA 20 y 50
    if (indicators?.moving_averages) {
      const ma = indicators.moving_averages;
      const lastBar = data[data.length - 1];

      if (ma.sma_20) {
        const sma20Series = chart.addLineSeries({
          color: "#f59e0b",
          lineWidth: 1,
          title: "SMA 20",
        });
        sma20Series.setData([{ time: lastBar.date as any, value: ma.sma_20 }]);
      }

      if (ma.sma_50) {
        const sma50Series = chart.addLineSeries({
          color: "#8b5cf6",
          lineWidth: 1,
          title: "SMA 50",
        });
        sma50Series.setData([{ time: lastBar.date as any, value: ma.sma_50 }]);
      }
    }

    chart.timeScale().fitContent();

    // Responsive
    const resizeObserver = new ResizeObserver(() => {
      if (chartRef.current) {
        chart.applyOptions({ width: chartRef.current.clientWidth });
      }
    });
    resizeObserver.observe(chartRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
    };
  }, [data, indicators, height]);

  return (
    <div className="bg-slate-900 rounded-xl overflow-hidden">
      <div className="px-4 pt-4 pb-2 flex items-center justify-between">
        <h3 className="font-semibold text-white">{ticker} — Gráfico de Precios</h3>
        <div className="flex gap-3 text-xs text-slate-400">
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-yellow-400 inline-block"></span> SMA 20
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-purple-400 inline-block"></span> SMA 50
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-blue-400 inline-block border-dashed border"></span> BB
          </span>
        </div>
      </div>
      <div ref={chartRef} />
    </div>
  );
}
