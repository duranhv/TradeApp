# TradeApp — SaaS de Análisis Financiero para el Mercado Argentino

## Visión General

Plataforma SaaS web para análisis técnico y fundamental de activos del mercado financiero argentino, con generación automática de alertas de compra/venta y cuadros comparativos de rendimientos.

---

## Activos Soportados

| Categoría | Instrumentos |
|-----------|-------------|
| Renta Variable | Acciones (BYMA), CEDEARs |
| Renta Fija Soberana | Bonos en ARS/USD, Letras del Tesoro (LETES, LECAP, BONCAP) |
| Renta Fija Corporativa | Obligaciones Negociables (ONs) |
| Fondos | FCI (Fondos Comunes de Inversión) |
| Mercado de Dinero | Cauciones (BYMA), Plazos Fijos bancarios |
| Derivados (futuro) | Futuros y Opciones (MatbaRofex) |

---

## Arquitectura de la Solución

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js 14)                     │
│  Dashboard │ Charts │ Alerts │ Comparador │ Portfolio │ Settings  │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/WebSocket
┌─────────────────────────▼───────────────────────────────────────┐
│                      BACKEND (FastAPI)                           │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │ Market Data  │  │  Technical   │  │   Fundamental         │ │
│  │   Service    │  │  Analysis    │  │   Analysis (NLP)      │ │
│  │              │  │  Engine      │  │   News + Informes     │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬────────────┘ │
│         │                 │                       │              │
│  ┌──────▼─────────────────▼───────────────────────▼──────────┐  │
│  │              Alert Engine + Signal Generator               │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────┐  ┌─────────────────────────────────┐  │
│  │  Comparador de Tasas │  │   Portfolio Tracker             │  │
│  │  PF/Cución/Bono/FCI  │  │   Rentabilidad / Risk           │  │
│  └──────────────────────┘  └─────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                   WORKERS (Celery + Redis)                        │
│   Data Fetcher │ Indicator Calculator │ Alert Processor          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    DATA LAYER                                     │
│   PostgreSQL (+ TimescaleDB)  │  Redis Cache  │  S3/MinIO        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                  FUENTES DE DATOS EXTERNAS                        │
│                                                                  │
│  BYMA / IOL API     │  BCRA API          │  Alpha Vantage       │
│  MatbaRofex         │  Ambito/Infobae    │  CNV Open Data       │
│  Bancos (scraping)  │  RSS News Feeds    │  CAFCI (FCI)         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Stack Tecnológico

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Task Queue**: Celery + Redis
- **ORM**: SQLAlchemy 2.0 + Alembic
- **WebSockets**: FastAPI WebSockets nativo
- **Analysis**: pandas, pandas-ta, numpy, scipy
- **NLP**: OpenAI API / LangChain para análisis fundamental

### Frontend
- **Framework**: Next.js 14 (App Router) + TypeScript
- **UI**: TailwindCSS + shadcn/ui
- **Charts**: TradingView Lightweight Charts + Recharts
- **State**: Zustand + React Query (TanStack Query)
- **Realtime**: Socket.io client

### Base de Datos
- **PostgreSQL 15** + TimescaleDB (series temporales de precios)
- **Redis 7** (cache, sesiones, pub/sub para alertas)

### Infraestructura
- **Docker** + Docker Compose (desarrollo)
- **Nginx** (reverse proxy)
- **CI/CD**: GitHub Actions

---

## Fuentes de Datos

### Mercado de Capitales Argentino

| Fuente | Datos | API/Método |
|--------|-------|------------|
| **IOL (Invertir Online)** | Acciones, CEDEARs, Bonos, ONs | REST API (requiere cuenta) |
| **byma-data** | BYMA oficial | Open source Python lib |
| **MatbaRofex** | Futuros, Opciones | REST API |
| **BCRA API** | Tasas de referencia, variables monetarias | `api.bcra.gob.ar` (pública) |
| **CAFCI** | FCI (cuotapartes, rendimientos) | REST API pública |
| **CNV Open Data** | Datos regulatorios, ONs | Portal de datos abiertos |
| **Ambito Financiero** | Cotizaciones, PF, noticias | Scraping / RSS |
| **Rava Bursátil** | Acciones en tiempo real | REST API |

### Tasas de Referencia

```
BCRA API endpoints utilizados:
- /estadisticas/v2.0/dastos/variable/6  → Tasa BADLAR
- /estadisticas/v2.0/dastos/variable/7  → Tasa política monetaria
- /estadisticas/v2.0/dastos/variable/40 → TNA de plazos fijos
```

---

## Módulos Funcionales

### 1. Análisis Técnico
Indicadores implementados:
- **Tendencia**: SMA (20/50/200), EMA (9/21/55), MACD, ADX
- **Momentum**: RSI (14), Stochastic (14,3,3), CCI, Williams %R
- **Volatilidad**: Bollinger Bands (20,2), ATR, Keltner Channels
- **Volumen**: OBV, VWAP, MFI, Accumulation/Distribution
- **Patrones**: Detección automática de patrones de velas japonesas

**Generación de Señales:**
```
COMPRA FUERTE  → RSI < 30 + precio toca banda inferior BB + MACD cruce alcista
COMPRA         → RSI < 40 + EMA20 > EMA50 + volumen creciente
VENTA FUERTE   → RSI > 70 + precio toca banda superior BB + MACD cruce bajista
VENTA          → RSI > 60 + EMA20 < EMA50 + volumen decreciente
NEUTRO         → Señales contradictorias o dentro de rango
```

### 2. Análisis Fundamental
- Procesamiento de noticias con NLP (OpenAI GPT / Claude API)
- Seguimiento de presentación de balances (EECC)
- Análisis de ratios financieros: P/E, EV/EBITDA, Deuda/EBITDA, ROE
- Scoring fundamental (0-100) para cada emisor

### 3. Comparador de Tasas y Rendimientos

```
Instrumento    │ TNA %  │ TEA %  │ Plazo  │ Moneda │ Riesgo
───────────────┼────────┼────────┼────────┼────────┼───────
Plazo Fijo     │ 118%   │ 212%   │ 30d    │ ARS    │ Bajo
Caución 7d     │ 105%   │  -     │ 7d     │ ARS    │ Bajo
LECAP Jun25    │ 130%   │  -     │ 90d    │ ARS    │ Bajo
FCI Money Mkt  │ 120%   │  -     │ T+0    │ ARS    │ Bajo
ON YPF USD     │  9%    │  -     │ 3 años │ USD    │ Medio
Bono AL30      │ 15%    │  -     │ 10 años│ USD    │ Alto
```

### 4. Sistema de Alertas
- Alertas técnicas: cruce de medias, niveles de RSI, Bollinger
- Alertas de precio: soporte/resistencia, % de variación
- Alertas fundamentales: publicación de balances, noticias relevantes
- Canales: Email, notificaciones push (web), Telegram bot

### 5. Portfolio Tracker
- Seguimiento de posiciones en ARS y USD
- Cálculo de rentabilidad en ARS, USD y vs. inflación (IPC)
- Comparación vs. benchmarks (S&P Merval, S&P 500, Dólar MEP)

---

## Estructura del Proyecto

```
TradeApp/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── api/               # Endpoints REST
│   │   │   ├── v1/
│   │   │   │   ├── market.py
│   │   │   │   ├── analysis.py
│   │   │   │   ├── alerts.py
│   │   │   │   ├── comparison.py
│   │   │   │   └── portfolio.py
│   │   ├── core/              # Config, security, DB
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/
│   │   │   ├── market_data/   # Connectors a fuentes externas
│   │   │   ├── technical/     # Motor de análisis técnico
│   │   │   ├── fundamental/   # NLP + análisis fundamental
│   │   │   ├── alerts/        # Motor de alertas
│   │   │   └── comparison/    # Comparador de tasas
│   │   └── workers/           # Celery tasks
│   ├── alembic/               # Migraciones DB
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Next.js application
│   ├── src/
│   │   ├── app/               # App Router pages
│   │   ├── components/
│   │   │   ├── charts/        # TradingView + Recharts
│   │   │   ├── dashboard/
│   │   │   ├── alerts/
│   │   │   └── comparison/
│   │   ├── hooks/
│   │   ├── services/          # API clients
│   │   ├── store/             # Zustand stores
│   │   └── types/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── nginx/
│   └── nginx.conf
├── .env.example
└── docs/
    ├── architecture.md
    ├── api-reference.md
    └── data-sources.md
```

---

## Roadmap

### Fase 1 — MVP (8 semanas)
- [x] Arquitectura base (FastAPI + Next.js + PostgreSQL)
- [ ] Integración BCRA API (tasas de referencia)
- [ ] Integración byma-data / Rava (cotizaciones)
- [ ] Análisis técnico: SMA, EMA, RSI, Bollinger, MACD
- [ ] Comparador básico: PF vs Caución vs Letras
- [ ] Dashboard con gráficos de precios
- [ ] Sistema de alertas por email

### Fase 2 — Análisis Avanzado (4 semanas)
- [ ] Integración IOL API completa
- [ ] Indicadores avanzados: Stochastic, Williams %R, ADX, VWAP
- [ ] Detección de patrones de velas
- [ ] Análisis fundamental con NLP
- [ ] Portfolio tracker

### Fase 3 — SaaS y Monetización (4 semanas)
- [ ] Sistema de suscripciones (Free/Pro/Premium)
- [ ] Telegram bot para alertas
- [ ] API pública para usuarios Pro
- [ ] Reportes PDF exportables
- [ ] App móvil (PWA)

---

## Consideraciones Regulatorias

> **IMPORTANTE**: Esta plataforma es una **herramienta de análisis e información**.
> No constituye asesoramiento financiero ni recomendaciones de inversión.
> Toda decisión de inversión es responsabilidad exclusiva del usuario.
> Cumplimiento con normativa CNV aplicable a distribuidores de información financiera.

---

## Quick Start (Desarrollo)

```bash
# Clonar y configurar
git clone <repo>
cd TradeApp
cp .env.example .env

# Levantar con Docker
docker-compose up -d

# Backend disponible en: http://localhost:8000
# Frontend disponible en: http://localhost:3000
# API Docs (Swagger): http://localhost:8000/docs
```
