import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "TradeApp — Análisis Financiero Argentino",
  description:
    "Plataforma SaaS de análisis técnico y fundamental para el mercado financiero argentino. Alertas de compra/venta, comparador de tasas, seguimiento de portfolio.",
  keywords: [
    "análisis técnico",
    "mercado argentino",
    "BYMA",
    "acciones",
    "cedear",
    "bonos",
    "plazo fijo",
    "caución",
    "RSI",
    "Bollinger",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
