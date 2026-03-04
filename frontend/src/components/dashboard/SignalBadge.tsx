import { clsx } from "clsx";
import type { SignalType } from "@/types/market";

const SIGNAL_LABELS: Record<SignalType, string> = {
  strong_buy: "Compra Fuerte",
  buy: "Comprar",
  neutral: "Neutral",
  sell: "Vender",
  strong_sell: "Venta Fuerte",
};

const SIGNAL_CLASSES: Record<SignalType, string> = {
  strong_buy: "signal-strong-buy",
  buy: "signal-buy",
  neutral: "signal-neutral",
  sell: "signal-sell",
  strong_sell: "signal-strong-sell",
};

interface SignalBadgeProps {
  signal: SignalType;
  score?: number;
  size?: "sm" | "md" | "lg";
}

export function SignalBadge({ signal, score, size = "md" }: SignalBadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-full font-semibold",
        SIGNAL_CLASSES[signal],
        {
          "px-2 py-0.5 text-xs": size === "sm",
          "px-3 py-1 text-sm": size === "md",
          "px-4 py-1.5 text-base": size === "lg",
        }
      )}
    >
      {SIGNAL_LABELS[signal]}
      {score !== undefined && (
        <span className="opacity-80 text-xs">({score > 0 ? "+" : ""}{score.toFixed(0)})</span>
      )}
    </span>
  );
}
