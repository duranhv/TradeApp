# TradeApp — Documento Técnico de la Solución

**Versión**: 1.0
**Fecha**: Marzo 2026
**Estado**: Borrador técnico

---

## Índice

1. [Visión General de la Arquitectura](#1-visión-general-de-la-arquitectura)
2. [Stack Tecnológico y Justificaciones](#2-stack-tecnológico-y-justificaciones)
3. [Estructura del Proyecto](#3-estructura-del-proyecto)
4. [Backend — FastAPI](#4-backend--fastapi)
5. [Motor de Análisis Técnico](#5-motor-de-análisis-técnico)
6. [Módulo de Comparación de Tasas](#6-módulo-de-comparación-de-tasas)
7. [Integración con Fuentes de Datos Externas](#7-integración-con-fuentes-de-datos-externas)
8. [Base de Datos](#8-base-de-datos)
9. [Sistema de Workers (Celery)](#9-sistema-de-workers-celery)
10. [Frontend — Next.js](#10-frontend--nextjs)
11. [Seguridad](#11-seguridad)
12. [Infraestructura y Despliegue](#12-infraestructura-y-despliegue)
13. [Monitoreo y Observabilidad](#13-monitoreo-y-observabilidad)
14. [Decisiones Técnicas y Trade-offs](#14-decisiones-técnicas-y-trade-offs)
15. [Guía de Configuración Local](#15-guía-de-configuración-local)

---

## 1. Visión General de la Arquitectura

### 1.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USUARIO (Browser)                                │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ HTTPS
                    ┌───────────▼───────────┐
                    │        NGINX          │
                    │   Reverse Proxy       │
                    │   Rate Limiting       │
                    │   SSL Termination     │
                    └─────┬──────────┬──────┘
                          │          │
          ┌───────────────▼──┐  ┌────▼─────────────────┐
          │  Next.js (SSR)   │  │    FastAPI (ASGI)     │
          │  Port 3000       │  │    Port 8000          │
          │  React + TS      │  │    Uvicorn            │
          └──────────────────┘  └────┬─────────────────┘
                                     │
                    ┌────────────────┼────────────────────┐
                    │                │                    │
          ┌─────────▼──────┐  ┌──────▼──────┐  ┌────────▼───────┐
          │  PostgreSQL 15  │  │   Redis 7   │  │  Celery Workers│
          │  + TimescaleDB  │  │             │  │  + Beat        │
          │  Port 5432      │  │  Port 6379  │  │                │
          └─────────────────┘  └─────────────┘  └────────────────┘

                    FUENTES DE DATOS EXTERNAS
          ┌──────────────────────────────────────────────┐
          │  BCRA API  │  Rava  │  CAFCI  │  IOL  │ Yahoo│
          └──────────────────────────────────────────────┘
```

### 1.2 Flujo de Datos

```
1. Celery Beat (scheduler) → dispara tasks periódicas
2. Task "fetch_prices"  → llama Rava/IOL API → guarda en PostgreSQL + cache Redis
3. Task "calc_indicators" → lee OHLCV desde DB → calcula técnicos → guarda señales
4. Task "check_alerts"    → compara señales/precios con alertas activas → notifica
5. Usuario consulta API   → FastAPI lee de Redis (cache) o PostgreSQL (fallback)
6. Frontend               → React Query gestiona cache del lado cliente
```

### 1.3 Principios de Diseño

- **Async first**: todas las operaciones I/O son async (FastAPI + asyncpg + httpx)
- **Cache en capas**: Redis L1 (hot data) → PostgreSQL L2 (historical)
- **Separación de concerns**: ingesta de datos, análisis y presentación en módulos independientes
- **Fail gracefully**: si una fuente de datos falla, se sirven datos del cache sin romper el frontend
- **Idempotencia**: los workers pueden re-ejecutarse sin efectos secundarios

---

## 2. Stack Tecnológico y Justificaciones

### 2.1 Backend

#### FastAPI (Python 3.11)
**Justificación**:
- El ecosistema Python para análisis financiero (pandas, numpy, scipy, TA-Lib) no tiene equivalente en otros lenguajes
- FastAPI provee async nativo con rendimiento comparable a Node.js (benchmarks: FastAPI > Flask > Django, similar a Express.js)
- Generación automática de documentación OpenAPI/Swagger — crítico para APIs financieras que otros sistemas pueden consumir
- Pydantic v2 para validación de esquemas — garantiza integridad de datos financieros con tipado estricto
- Alternativa considerada y descartada: Node.js/NestJS (inferio ecosistema financiero), Django (sync, overhead innecesario)

#### SQLAlchemy 2.0 + asyncpg
- ORM maduro con soporte async nativo en v2
- asyncpg es el driver más performante para PostgreSQL en Python async
- Alembic para migraciones versionadas

#### Celery + Redis
- Cola de tareas distribuida, estándar de industria para Python
- Redis como broker es más simple de operar que RabbitMQ para este escenario
- Celery Beat integrado para scheduling — evita un cron externo
- Alternativa considerada: APScheduler (menos robusto, sin worker distribuido)

### 2.2 Base de Datos

#### PostgreSQL 15 + TimescaleDB

Los datos de precios OHLCV son series temporales puras. TimescaleDB extiende PostgreSQL con:

| Característica | PostgreSQL estándar | TimescaleDB |
|---------------|---------------------|-------------|
| Espacio en disco (1 año OHLCV 500 activos) | ~8 GB | ~0.8 GB (compresión ~90%) |
| Query "dame el precio de X entre fecha A y B" | Full scan o index scan | Chunk pruning automático |
| Funciones time-series | Ninguna nativa | `time_bucket`, `first`, `last`, `histogram` |
| Compatibilidad | — | 100% PostgreSQL |

No requiere aprender una base de datos nueva (como InfluxDB), y permite joins con datos relacionales (usuarios, alertas).

#### Redis 7
- Cache de cotizaciones recientes (TTL: 60 segundos)
- Cache de indicadores calculados (TTL: 5 minutos)
- Cache de tasas BCRA (TTL: 1 hora)
- Pub/Sub para WebSocket de alertas en tiempo real (futuro)
- Session store para JWT tokens

### 2.3 Frontend

#### Next.js 14 (App Router) + TypeScript
- **Server Components**: la página de análisis puede pre-renderizar con datos del día, mejorando SEO y tiempo de carga inicial
- **TypeScript estricto**: los tipos `TechnicalIndicators`, `RateComparisonRow`, etc. garantizan consistencia entre frontend y backend
- **TradingView Lightweight Charts**: biblioteca de gráficos financieros open source de TradingView — la mejor opción gratuita para gráficos OHLCV
- **React Query (TanStack)**: manejo de cache del lado cliente, re-fetch automático, estados loading/error

#### TailwindCSS + shadcn/ui
- Diseño utility-first: componentes financieros (tablas, badges de señal) se construyen rápido
- shadcn/ui provee componentes accesibles (Radix UI) sin opinionated styling
- No se usa un framework de componentes monolítico (MUI/Antd) para mantener el bundle pequeño

### 2.4 Infraestructura

#### Docker + Docker Compose
- Desarrollo reproducible: cualquier desarrollador levanta el entorno completo con `docker-compose up`
- Imagen backend basada en `python:3.11-slim` (~180 MB vs ~900 MB de la imagen estándar)
- Imagen frontend con multi-stage build: build en Node, runtime en Alpine (~120 MB)

#### Nginx
- Reverse proxy que expone solo el puerto 80/443 al exterior
- Rate limiting: 30 requests/minuto por IP en endpoints `/api/`
- Gzip para respuestas JSON (reducción ~70% en tamaño de transferencia)
- En producción: SSL termination con Let's Encrypt

---

## 3. Estructura del Proyecto

```
TradeApp/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── market.py        # GET /market/quotes/{panel}, /quote/{ticker}, /history/{ticker}
│   │   │       ├── analysis.py      # GET /analysis/technical/{ticker}, /analysis/screener
│   │   │       └── comparison.py    # GET /comparison/rates, /comparison/bond-ytm, /comparison/summary
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic Settings — carga .env
│   │   │   └── database.py          # Engine async SQLAlchemy, get_db dependency
│   │   ├── models/
│   │   │   ├── market.py            # Asset, PriceBar, MarketRate (SQLAlchemy ORM)
│   │   │   ├── alerts.py            # Alert, AlertEvent, TechnicalSignal
│   │   │   └── user.py              # User, Portfolio, Position
│   │   ├── schemas/                 # Pydantic request/response schemas (a implementar)
│   │   ├── services/
│   │   │   ├── market_data/
│   │   │   │   ├── bcra_client.py   # BCRA API client async
│   │   │   │   └── rava_client.py   # Rava quotes + CAFCI FCIs
│   │   │   ├── technical/
│   │   │   │   └── engine.py        # TechnicalAnalysisEngine — todos los indicadores
│   │   │   ├── fundamental/         # (Fase 2) NLP news analysis
│   │   │   ├── alerts/              # (Fase 2) Alert evaluation logic
│   │   │   └── comparison/
│   │   │       └── rate_comparator.py  # RateComparator, YTM calculator
│   │   ├── workers/
│   │   │   └── tasks.py             # Celery tasks + beat schedule
│   │   └── main.py                  # FastAPI app factory, middlewares, routers
│   ├── alembic/                     # Migraciones de base de datos
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                     # Next.js App Router
│   │   │   ├── page.tsx             # Dashboard principal
│   │   │   ├── analysis/page.tsx    # Análisis técnico
│   │   │   ├── screener/page.tsx    # Screener de mercado
│   │   │   ├── layout.tsx           # Root layout
│   │   │   └── providers.tsx        # QueryClient + Toaster
│   │   ├── components/
│   │   │   ├── charts/
│   │   │   │   └── PriceChart.tsx   # TradingView Lightweight Charts wrapper
│   │   │   ├── dashboard/
│   │   │   │   ├── MarketOverview.tsx  # KPIs del mercado desde BCRA
│   │   │   │   └── SignalBadge.tsx     # Badge colored por tipo de señal
│   │   │   └── comparison/
│   │   │       └── RateComparisonTable.tsx  # Tabla comparativa interactiva
│   │   ├── services/
│   │   │   └── api.ts               # Axios client, todos los endpoints tipados
│   │   └── types/
│   │       └── market.ts            # TypeScript interfaces del dominio
│   ├── package.json
│   ├── next.config.mjs
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── Dockerfile
├── nginx/
│   └── nginx.conf
├── docs/
│   ├── documento-funcional.md
│   ├── documento-tecnico.md         (este archivo)
│   ├── architecture.md
│   └── data-sources.md
├── docker-compose.yml
├── .env.example
└── .gitignore
```

---

## 4. Backend — FastAPI

### 4.1 Configuración (app/core/config.py)

Usa `pydantic-settings` para cargar variables de entorno con validación de tipos:

```python
class Settings(BaseSettings):
    DATABASE_URL: str         # postgresql+asyncpg://...
    REDIS_URL: str            # redis://...
    IOL_USERNAME: str = ""    # Credenciales IOL (opcional en dev)
    OPENAI_API_KEY: str = ""  # Para análisis fundamental (Fase 2)
    MARKET_OPEN_HOUR: int = 11
    MARKET_CLOSE_HOUR: int = 17
    MARKET_TIMEZONE: str = "America/Argentina/Buenos_Aires"
```

**Patrón de uso**: `from app.core.config import settings` — instancia singleton cargada al inicio.

### 4.2 Endpoints Principales

#### Market Data API

```
GET /api/v1/market/quotes/{panel}
    panel: acciones | cedears | bonos | letras | on
    Respuesta: lista de cotizaciones del panel con OHLC, volumen, variación %
    Cache: Redis 60s

GET /api/v1/market/quote/{ticker}
    Respuesta: cotización individual con bid/ask
    Cache: Redis 60s

GET /api/v1/market/history/{ticker}?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
    Respuesta: array de OHLCV (open, high, low, close, volume, date)
    Cache: Redis 5min para fechas recientes

GET /api/v1/market/bcra/rates
    Respuesta: TNA PF, BADLAR, tasa política, inflación, USD
    Cache: Redis 1h

GET /api/v1/market/fci/money-market
    Respuesta: top FCIs MM con TNA 7d y 30d
    Cache: Redis 1h
```

#### Technical Analysis API

```
GET /api/v1/analysis/technical/{ticker}?timeframe=1d&lookback_days=365
    Respuesta: {
      signal: "strong_buy" | "buy" | "neutral" | "sell" | "strong_sell",
      score: float (-100 a 100),
      reasoning: string[],
      indicators: { moving_averages, momentum, macd, bollinger_bands, ... }
    }
    Cache: Redis 5min

GET /api/v1/analysis/screener?panel=acciones&signal_filter=buy&limit=20
    Respuesta: lista de activos con señal/score, ordenados por score desc
    Nota: este endpoint es intensivo en cómputo — usar con moderación
```

#### Rate Comparison API

```
GET /api/v1/comparison/rates?horizon_days=30&amount=1000000&currency=ARS
    Respuesta: tabla comparativa con TNA/TEA/TEM, retorno proyectado, capital final
    Cache: Redis 5min

GET /api/v1/comparison/bond-ytm?ticker=AL30&market_price=57.5&coupon_rate=0.0&years_to_maturity=4.2
    Respuesta: YTM calculada con Newton-Raphson, interpretación

GET /api/v1/comparison/summary
    Respuesta: resumen rápido de tasas clave para el dashboard
```

### 4.3 Gestión de Errores

Todos los endpoints manejan errores de forma consistente:

```python
# Fuente externa no disponible → sirve del cache
try:
    data = await external_client.get_data()
    await redis.setex(cache_key, ttl, json.dumps(data))
except httpx.RequestError:
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    raise HTTPException(503, "Servicio temporalmente no disponible")

# Ticker no encontrado → 404 limpio
if not quote:
    raise HTTPException(404, f"No se encontró cotización para {ticker}")

# Datos insuficientes → 400 con mensaje descriptivo
if len(df) < 30:
    raise HTTPException(400, f"Datos insuficientes: {len(df)} velas (mínimo 30)")
```

---

## 5. Motor de Análisis Técnico

### 5.1 Diseño del Engine (services/technical/engine.py)

El `TechnicalAnalysisEngine` recibe un DataFrame OHLCV y retorna un `IndicatorResult` con todos los indicadores calculados y la señal generada.

**Decisión de diseño**: se implementaron los indicadores manualmente con pandas/numpy en lugar de usar TA-Lib, por las siguientes razones:
- TA-Lib requiere compilación de dependencias C — complica el Dockerfile
- Control total sobre los parámetros y el comportamiento en series cortas
- La implementación manual es perfectamente precisa para los indicadores usados
- Facilita testing unitario de cada indicador

### 5.2 Implementación de Indicadores Clave

#### RSI (Relative Strength Index)
```python
def _rsi(self, close: pd.Series, period: int = 14) -> float:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    # Exponential moving average (método Wilder)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.finfo(float).eps)
    return float((100 - 100 / (1 + rs)).iloc[-1])
```

#### MACD
```python
def _macd(self, close, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    macd_signal = macd_line.ewm(span=signal, adjust=False).mean()
    macd_hist = macd_line - macd_signal
    return macd_line.iloc[-1], macd_signal.iloc[-1], macd_hist.iloc[-1]
```

#### Bollinger Bands
```python
def _bollinger(self, close, period=20, std_dev=2.0):
    sma = close.rolling(period).mean()
    std = close.rolling(period).std()
    return sma + std_dev * std, sma, sma - std_dev * std
```

#### YTM (Yield to Maturity) — Newton-Raphson
```python
def yield_to_maturity(self, price, face_value, coupon_rate, years_to_maturity, payments_per_year=2):
    coupon = face_value * (coupon_rate / 100) / payments_per_year
    total_periods = int(years_to_maturity * payments_per_year)

    def bond_price(ytm_periodic):
        pv_coupons = sum(coupon / (1 + ytm_periodic)**t for t in range(1, total_periods + 1))
        pv_face = face_value / (1 + ytm_periodic)**total_periods
        return pv_coupons + pv_face

    ytm = 0.10 / payments_per_year  # Seed inicial
    for _ in range(100):            # Máximo 100 iteraciones
        f_ytm = bond_price(ytm) - price
        delta = 1e-6
        f_prime = (bond_price(ytm + delta) - bond_price(ytm - delta)) / (2 * delta)
        ytm -= f_ytm / f_prime
        if abs(f_ytm) < 1e-10:
            break

    return ytm * payments_per_year * 100  # Anualizar
```

### 5.3 Algoritmo de Señal Compuesta

El score final (-100 a +100) se calcula como suma ponderada de sub-scores por categoría:

```
Score Final = (Trend_score × 0.35)
            + (Momentum_score × 0.25)
            + (MACD_score × 0.20)
            + (Bollinger_score × 0.20)

Clasificación:
  score ≥ 40  → STRONG_BUY
  score ≥ 15  → BUY
  score ≤ -40 → STRONG_SELL
  score ≤ -15 → SELL
  else        → NEUTRAL
```

**Lógica de Trend score** (ejemplos):
- EMA9 > EMA21: +15 pts ("tendencia alcista corto plazo")
- Precio > SMA20 > SMA50: +20 pts ("tendencia alcista confirmada")
- Precio < SMA20 < SMA50: -20 pts ("tendencia bajista confirmada")

**Lógica de Momentum score** (ejemplos):
- RSI < 30: +80 pts ("sobreventa — posible rebote")
- RSI > 70: -80 pts ("sobrecompra — posible corrección")
- Stoch K < 20 y D < 20: +20 pts adicionales

---

## 6. Módulo de Comparación de Tasas

### 6.1 Fórmulas de Conversión de Tasas

```python
# TNA → TEA (capitalización mensual, n=12 períodos)
TEA = (1 + TNA/12)^12 - 1

# TNA → TEM
TEM = (1 + TNA/12) - 1  # equivalente a TNA/12 (aproximado)

# TEA → TNA
TNA = ((1 + TEA)^(1/12) - 1) × 12

# Tasa real (Fisher)
tasa_real = ((1 + tasa_nominal) / (1 + inflacion)) - 1

# Retorno proyectado (base simple)
retorno = capital × (TNA/100) × (dias/365)
```

### 6.2 Pipeline del Comparador

```python
async def build_comparison(bcra_rates, caucion_rates, fci_rates, bond_quotes, ...):
    # 1. Normalizar todas las tasas a TNA base 365
    # 2. Calcular TEA y TEM para cada instrumento
    # 3. Calcular retorno proyectado para el horizonte dado
    # 4. Enriquecer con metadata (riesgo, liquidez, emisor)
    # 5. Ordenar por TNA descendente
    # 6. Retornar lista de RateEntry normalizados
```

---

## 7. Integración con Fuentes de Datos Externas

### 7.1 BCRA API

**Endpoint base**: `https://api.bcra.gob.ar`
**Autenticación**: Ninguna (API pública)
**Rate limit**: No documentado — se usa 1 req/día por variable como práctica conservadora

```python
# Ejemplo de respuesta para variable 40 (TNA PF privados)
GET /estadisticas/v2.0/datosvariable/40/2026-02-01/2026-03-04

{
  "results": [
    {"idVariable": 40, "cdSerie": 172, "fecha": "2026-03-03", "valor": 35.00},
    {"idVariable": 40, "cdSerie": 172, "fecha": "2026-03-04", "valor": 35.00}
  ],
  "status": 200
}
```

### 7.2 Rava Bursátil

**Endpoint**: `https://www.rava.com/series/preciostabla.php`
**Tipo**: JSON público (sin autenticación)
**Parámetros**:
- `panel=0` → Acciones
- `panel=4` → CEDEARs
- `panel=2` → Bonos
- `panel=3` → Letras
- `panel=9` → ONs

```python
# Estructura de respuesta
{
  "cotizaciones": [
    {
      "simbolo": "GGAL",
      "descripcion": "Grupo Galicia",
      "ultimo": 4850.50,
      "apertura": 4700.00,
      "maximo": 4900.00,
      "minimo": 4680.00,
      "cierreant": 4720.00,
      "variacion": 2.76,
      "volumen": 1234567,
      "operaciones": 3421
    }
  ]
}
```

**Limitaciones conocidas**:
- Datos con ~5-10 segundos de delay respecto al mercado real
- Sin SLA oficial — servicio puede tener interrupciones
- En producción: reemplazar por IOL API (tiene SLA)

### 7.3 CAFCI API

**Endpoint base**: `https://api.cafci.org.ar`
**Autenticación**: Ninguna (API pública)

```python
# Listar fondos Money Market
GET /fondo?tipo=1

# Rendimiento de un fondo específico
GET /fondo/{id}/serie
```

### 7.4 IOL API (Invertir Online) — Producción

**Endpoint base**: `https://api.invertironline.com`
**Autenticación**: OAuth2 con refresh token

```python
# Autenticación
POST /token
  username, password, grant_type=password

# Cotización
GET /api/v2/Cotizaciones/titulos/{mercado}/{simbolo}
  mercado: bCBA (BYMA)

# Datos históricos
GET /api/v2/{mercado}/{simbolo}/cotizaciones/{tipo}/{desde}/{hasta}
  tipo: minuto | hora | diaria

# Ventajas vs Rava:
# - Datos en tiempo real real
# - Más activos disponibles (incluye ONs, opciones)
# - SLA oficial
# - Permite integración futura de órdenes
```

### 7.5 Estrategia de Fallback

```python
async def get_quote_with_fallback(ticker: str) -> dict:
    # 1. Intentar Redis cache (más rápido)
    cached = await redis.get(f"quote:{ticker}")
    if cached:
        return json.loads(cached)

    # 2. Intentar IOL (más confiable, requiere credenciales)
    if settings.IOL_USERNAME:
        try:
            data = await iol_client.get_quote(ticker)
            await redis.setex(f"quote:{ticker}", 60, json.dumps(data))
            return data
        except Exception:
            pass

    # 3. Fallback a Rava (siempre disponible, datos públicos)
    data = await rava_client.get_quote(ticker)
    await redis.setex(f"quote:{ticker}", 60, json.dumps(data))
    return data
```

---

## 8. Base de Datos

### 8.1 Modelo de Datos

#### Tabla `assets` — Catálogo de instrumentos

```sql
CREATE TABLE assets (
    id          SERIAL PRIMARY KEY,
    ticker      VARCHAR(20) UNIQUE NOT NULL,
    name        VARCHAR(200) NOT NULL,
    asset_type  asset_type_enum NOT NULL,  -- accion, cedear, bono, letra, on, fci, caucion, plazo_fijo
    currency    currency_enum DEFAULT 'ARS',
    market      VARCHAR(50) DEFAULT 'BYMA',
    is_active   BOOLEAN DEFAULT TRUE,
    -- Campos específicos para bonos/letras
    maturity_date   TIMESTAMP,
    coupon_rate     FLOAT,
    issuer          VARCHAR(200),
    -- Campos específicos para CEDEARs
    underlying_ticker VARCHAR(20),  -- Ej: "AAPL" para el CEDEAR de Apple
    ratio             FLOAT,        -- Ej: 10 → 10 CEDEAR = 1 acción
    created_at  TIMESTAMP DEFAULT NOW()
);
CREATE INDEX ix_assets_type ON assets(asset_type);
CREATE INDEX ix_assets_ticker ON assets(ticker);
```

#### Tabla `price_bars` — Serie temporal OHLCV

```sql
-- TimescaleDB hypertable
CREATE TABLE price_bars (
    id          BIGSERIAL,
    asset_id    INTEGER NOT NULL REFERENCES assets(id),
    timestamp   TIMESTAMPTZ NOT NULL,
    timeframe   VARCHAR(10) NOT NULL,  -- 1m, 5m, 15m, 1h, 1d
    open        FLOAT NOT NULL,
    high        FLOAT NOT NULL,
    low         FLOAT NOT NULL,
    close       FLOAT NOT NULL,
    volume      FLOAT DEFAULT 0,
    trades      INTEGER DEFAULT 0
);

-- Convertir a hypertable (partición por tiempo)
SELECT create_hypertable('price_bars', 'timestamp');

-- Compresión automática de datos > 7 días (ahorros ~90%)
ALTER TABLE price_bars SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'asset_id, timeframe'
);
SELECT add_compression_policy('price_bars', INTERVAL '7 days');

-- Índice compuesto para queries típicas
CREATE INDEX ix_price_bars_asset_tf_ts ON price_bars(asset_id, timeframe, timestamp DESC);
```

#### Tabla `market_rates` — Tasas del mercado de dinero

```sql
CREATE TABLE market_rates (
    id                SERIAL PRIMARY KEY,
    source            VARCHAR(50) NOT NULL,        -- BCRA, BYMA, CAFCI
    instrument_type   VARCHAR(50) NOT NULL,        -- plazo_fijo, caucion, letra, fci
    instrument_name   VARCHAR(200),
    tna               FLOAT,
    tea               FLOAT,
    tem               FLOAT,
    currency          currency_enum DEFAULT 'ARS',
    min_days          INTEGER,
    max_days          INTEGER,
    min_amount        FLOAT,
    extra_data        JSONB,                       -- Datos adicionales flexibles
    recorded_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ix_market_rates_type_recorded ON market_rates(instrument_type, recorded_at DESC);
```

#### Tabla `technical_signals` — Señales precalculadas

```sql
CREATE TABLE technical_signals (
    id          BIGSERIAL PRIMARY KEY,
    asset_id    INTEGER NOT NULL REFERENCES assets(id),
    timeframe   VARCHAR(10) NOT NULL,
    signal      signal_enum NOT NULL,  -- strong_buy, buy, neutral, sell, strong_sell
    score       FLOAT,
    indicators  JSONB NOT NULL,  -- Snapshot completo: {rsi: 28.5, macd: {...}, ...}
    reasoning   TEXT[],
    calculated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Solo necesitamos la señal más reciente por activo/timeframe
CREATE INDEX ix_signals_asset_tf_calc ON technical_signals(asset_id, timeframe, calculated_at DESC);
```

#### Tabla `alerts` — Alertas de usuario

```sql
CREATE TABLE alerts (
    id                SERIAL PRIMARY KEY,
    user_id           INTEGER NOT NULL REFERENCES users(id),
    asset_id          INTEGER NOT NULL REFERENCES assets(id),
    alert_type        alert_type_enum NOT NULL,
    name              VARCHAR(200),
    condition_value   FLOAT,         -- Ej: 4500 para "precio > $4500"
    condition_params  JSONB,         -- Parámetros adicionales según tipo
    is_active         BOOLEAN DEFAULT TRUE,
    is_recurring      BOOLEAN DEFAULT FALSE,
    notify_email      BOOLEAN DEFAULT TRUE,
    notify_telegram   BOOLEAN DEFAULT FALSE,
    notify_push       BOOLEAN DEFAULT TRUE,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    last_triggered_at TIMESTAMPTZ
);
```

### 8.2 Queries Frecuentes Optimizadas

```sql
-- Último precio de un activo (usa index + TimescaleDB chunk pruning)
SELECT close, timestamp
FROM price_bars
WHERE asset_id = $1 AND timeframe = '1d'
ORDER BY timestamp DESC
LIMIT 1;

-- Histórico para análisis técnico (últimos N días)
SELECT date_trunc('day', timestamp) as date,
       first(open, timestamp) as open,
       max(high) as high,
       min(low) as low,
       last(close, timestamp) as close,
       sum(volume) as volume
FROM price_bars
WHERE asset_id = $1
  AND timeframe = '1d'
  AND timestamp > NOW() - INTERVAL '365 days'
GROUP BY 1
ORDER BY 1;

-- Tasas del comparador (última lectura por instrumento)
SELECT DISTINCT ON (source, instrument_type)
    source, instrument_type, instrument_name, tna, tea, currency, min_days
FROM market_rates
ORDER BY source, instrument_type, recorded_at DESC;
```

### 8.3 Migraciones con Alembic

```bash
# Crear nueva migración
alembic revision --autogenerate -m "add_portfolio_table"

# Aplicar migraciones pendientes
alembic upgrade head

# Rollback una migración
alembic downgrade -1
```

---

## 9. Sistema de Workers (Celery)

### 9.1 Configuración de Tareas

```python
# Configuración de colas por prioridad
celery_app.conf.task_routes = {
    "app.workers.tasks.update_all_prices":    {"queue": "high"},
    "app.workers.tasks.check_all_alerts":     {"queue": "high"},
    "app.workers.tasks.recalculate_indicators": {"queue": "normal"},
    "app.workers.tasks.update_bcra_rates":    {"queue": "low"},
    "app.workers.tasks.run_daily_close_analysis": {"queue": "low"},
}
```

### 9.2 Beat Schedule — Horarios de Ejecución

```
Horario BYMA: lunes a viernes, 11:00 - 17:30 (UTC-3)

Durante el mercado:
├── Cada 1 min  → update_all_prices (actualiza cotizaciones)
├── Cada 2 min  → check_all_alerts  (evalúa alertas activas)
└── Cada 5 min  → recalculate_indicators (recalcula señales)

Fuera del mercado:
├── 09:00 diario  → update_bcra_rates  (tasas del día)
├── 09:30 diario  → update_fci_rates   (rendimientos FCIs)
└── 18:00 L-V    → daily_close_analysis (resumen del día)
```

### 9.3 Manejo de Errores en Workers

```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def update_all_prices(self):
    try:
        # ... lógica de actualización ...
    except httpx.RequestError as exc:
        # Retry con backoff exponencial: 30s, 60s, 120s
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
    except Exception as exc:
        # Error inesperado: loguear y notificar al equipo
        logger.error(f"update_all_prices falló: {exc}", exc_info=True)
        send_alert_to_ops_team(exc)
        raise
```

---

## 10. Frontend — Next.js

### 10.1 Patrones de Fetch y Cache

```typescript
// React Query — fetch con cache automático
const { data, isLoading } = useQuery({
  queryKey: ["technical", ticker],        // Cache key
  queryFn: () => getTechnicalAnalysis(ticker),
  staleTime: 5 * 60 * 1000,             // Datos frescos por 5 minutos
  refetchInterval: 5 * 60 * 1000,       // Re-fetch automático
  retry: 2,                              // 2 reintentos en caso de error
});

// Para datos en tiempo real durante el mercado:
refetchInterval: isMarketOpen() ? 60_000 : false,
```

### 10.2 Estructura de Tipos (TypeScript)

```typescript
// types/market.ts — define el contrato frontend-backend
export interface TechnicalAnalysis {
  ticker: string;
  signal: "strong_buy" | "buy" | "neutral" | "sell" | "strong_sell";
  score: number;          // -100 a +100
  reasoning: string[];
  indicators: {
    moving_averages: { sma_20: number | null; sma_50: number | null; ... };
    momentum: { rsi_14: number | null; stochastic_k: number | null; ... };
    macd: { line: number | null; signal: number | null; histogram: number | null };
    bollinger_bands: { upper: number | null; lower: number | null; pct_b: number | null; ... };
    ...
  }
}
```

### 10.3 Gráfico TradingView

`PriceChart.tsx` usa `lightweight-charts` (open source de TradingView):

```typescript
const chart = createChart(containerRef.current, {
  layout: { background: { type: ColorType.Solid, color: "transparent" } },
  ...
});

// Serie de velas japonesas
const candleSeries = chart.addCandlestickSeries({
  upColor: "#22c55e",    // verde para velas alcistas
  downColor: "#ef4444",  // rojo para velas bajistas
});

// Series adicionales: Bollinger Bands, SMA 20/50
const bbUpperSeries = chart.addLineSeries({ color: "rgba(59,130,246,0.5)", lineStyle: LineStyle.Dashed });
```

### 10.4 API Client (services/api.ts)

Axios con base URL configurable por entorno:

```typescript
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  timeout: 30000,
});

// Interceptor para manejo global de errores
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 503) {
      toast.error("Servicio temporalmente no disponible");
    }
    return Promise.reject(error);
  }
);
```

---

## 11. Seguridad

### 11.1 Autenticación

**JWT (JSON Web Tokens)**:
- Tokens firmados con algoritmo HS256, secret en variable de entorno
- Access token: duración 24h
- Refresh token: duración 30 días, almacenado en cookie HttpOnly
- Endpoints protegidos requieren header `Authorization: Bearer <token>`

```python
# Dependency para proteger endpoints
async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
    credentials_exception = HTTPException(401, "No autorizado")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await db.get(User, int(user_id))
    if not user:
        raise credentials_exception
    return user
```

### 11.2 Rate Limiting

Dos niveles:
1. **Nginx**: 30 req/minuto por IP para `/api/`
2. **FastAPI** (via `slowapi`): límites específicos por endpoint:
   - `/analysis/screener`: 5 req/minuto (intensivo en cómputo)
   - `/analysis/technical/{ticker}`: 30 req/minuto
   - `/market/quotes/*`: 60 req/minuto

### 11.3 Validación de Entradas

Pydantic valida automáticamente todos los parámetros:

```python
@router.get("/comparison/rates")
async def compare_rates(
    horizon_days: int = Query(30, ge=1, le=1825),   # 1 día a 5 años máximo
    amount: float = Query(1_000_000, ge=100),        # Mínimo $100
    currency: Literal["ARS", "USD"] = Query("ARS"),  # Solo valores válidos
):
```

### 11.4 CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # ["https://tradeapp.com.ar"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 11.5 Secrets Management

- Nunca se hardcodean credenciales en el código
- Variables de entorno en `.env` (no commiteado, en `.gitignore`)
- En producción: AWS Secrets Manager o HashiCorp Vault
- Rotación de `SECRET_KEY` sin downtime usando tokens con campo `iat`

---

## 12. Infraestructura y Despliegue

### 12.1 Entorno de Desarrollo

```bash
# Requisitos: Docker Desktop
git clone <repo>
cd TradeApp
cp .env.example .env
# Editar .env con credenciales opcionales (IOL, OpenAI, etc.)
docker-compose up -d

# Verificar servicios
docker-compose ps
curl http://localhost:8000/health   # → {"status": "ok"}
open http://localhost:3000           # Frontend
open http://localhost:8000/docs     # Swagger API
```

### 12.2 Entorno de Producción

```yaml
# docker-compose.prod.yml — diferencias clave:
backend:
  environment:
    DEBUG: "false"
    DATABASE_URL: ${DATABASE_URL_PROD}     # RDS / Managed PostgreSQL
    REDIS_URL: ${REDIS_URL_PROD}           # ElastiCache / Managed Redis
  deploy:
    replicas: 2                             # Alta disponibilidad
    resources:
      limits:
        memory: 1G

nginx:
  volumes:
    - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf
    - /etc/letsencrypt:/etc/letsencrypt:ro  # SSL
```

### 12.3 Recomendaciones de Infraestructura en Producción

**AWS (opción recomendada)**:

| Componente | Servicio AWS | Instancia sugerida | Costo estimado/mes |
|------------|-------------|-------------------|-------------------|
| Backend API | ECS Fargate (2 tasks) | 0.5 vCPU / 1 GB | ~$40 |
| Frontend | Vercel o ECS | — | ~$20 |
| PostgreSQL | RDS db.t4g.micro (TimescaleDB Cloud) | 2 vCPU / 1 GB | ~$30 |
| Redis | ElastiCache cache.t4g.micro | — | ~$15 |
| Load Balancer | ALB | — | ~$20 |
| **Total MVP** | | | **~$125/mes** |

**Alternativa más económica (VPS)**:
- Hetzner Cloud CX31 (8 GB RAM, 4 vCPU): ~$15/mes
- Un único servidor con Docker Compose
- Suficiente para hasta 1.000 usuarios activos

### 12.4 CI/CD (GitHub Actions)

```yaml
# .github/workflows/deploy.yml
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/ -v

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build and push Docker images
        run: docker buildx bake --push
      - name: Deploy to production
        run: |
          ssh deploy@server 'cd TradeApp && docker-compose pull && docker-compose up -d'
```

---

## 13. Monitoreo y Observabilidad

### 13.1 Métricas (Prometheus + Grafana)

```python
# Backend usa prometheus-fastapi-instrumentator
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)

# Métricas expuestas en /metrics:
# - http_requests_total (por endpoint, método, status)
# - http_request_duration_seconds (latencia por endpoint)
# - http_requests_in_progress
```

**Dashboards Grafana recomendados**:
- Latencia p50/p95/p99 por endpoint
- Tasa de errores 5xx
- Precios en cache (hit ratio Redis)
- Tareas Celery: success/failure rate, tiempo de ejecución
- Lag de datos: tiempo desde última actualización de cotizaciones

### 13.2 Logging Estructurado

```python
import structlog

logger = structlog.get_logger()

# Ejemplo de log estructurado
logger.info(
    "technical_analysis_completed",
    ticker=ticker,
    signal=result.signal,
    score=result.score,
    duration_ms=elapsed * 1000,
    data_points=len(df),
)
```

### 13.3 Health Checks

```
GET /health                → {"status": "ok"}
GET /health/db             → {"status": "ok", "latency_ms": 2.3}
GET /health/redis          → {"status": "ok", "latency_ms": 0.5}
GET /health/data-freshness → {"status": "ok", "last_price_update": "2026-03-04T17:29:00"}
```

### 13.4 Alertas de Sistema

- Si `/health/data-freshness` muestra datos de más de 5 minutos durante horario de mercado → alerta a ops
- Si tasa de errores 5xx supera 1% → alerta a ops
- Si Redis hit ratio cae por debajo del 80% → revisar TTLs

---

## 14. Decisiones Técnicas y Trade-offs

### 14.1 ¿Por qué no usar WebSockets desde el inicio?

**Decisión**: Polling con React Query (cada 60 segundos) en lugar de WebSockets.

**Razonamiento**:
- El mercado argentino tiene datos con delay intrínseco (Rava ~10s, IOL ~3s) — WebSockets no agregan valor real
- Polling simplifica enormemente el backend (no hay estado de conexión)
- React Query provee un excelente UX: loading states, error handling, background refetch
- WebSockets se agregarán en Fase 2 exclusivamente para notificaciones de alertas en tiempo real

### 14.2 ¿Por qué TimescaleDB y no InfluxDB?

**Decisión**: TimescaleDB (extensión de PostgreSQL)

**Razonamiento**:
- Los datos de precios necesitan joins con tablas relacionales (assets, users, alerts) — InfluxDB no hace joins
- El equipo ya conoce SQL — curva de aprendizaje cero
- TimescaleDB alcanza 90% de las ventajas de InfluxDB para series temporales financieras
- Un único sistema de base de datos simplifica las operaciones

### 14.3 ¿Por qué implementar indicadores manualmente?

**Decisión**: pandas/numpy en lugar de TA-Lib

**Razonamiento**:
- TA-Lib requiere compilación de extensiones C (`libta-lib-dev`) — complica Docker y CI
- Las implementaciones manuales son suficientemente precisas para todos los indicadores usados
- Mayor control para adaptar el comportamiento en series con pocos datos
- Facilita testing unitario sin dependencias externas

**Trade-off**: Si en el futuro se necesitan indicadores muy específicos (Ichimoku Cloud, TRIX, etc.), evaluar agregar `pandas-ta` que sí instala sin compilación.

### 14.4 ¿Por qué no usar una biblioteca de UI de componentes (MUI, Antd)?

**Decisión**: TailwindCSS + shadcn/ui (componentes sin opinionated styling)

**Razonamiento**:
- MUI/Antd agregan ~500KB al bundle
- Un dashboard financiero requiere alto grado de personalización visual
- shadcn/ui usa Radix UI (accesibilidad garantizada) con zero runtime CSS
- TailwindCSS permite crear exactamente el diseño necesario para tablas financieras densas

---

## 15. Guía de Configuración Local

### 15.1 Prerrequisitos

```bash
# Verificar versiones
docker --version        # >= 24.0
docker-compose --version # >= 2.0
git --version
```

### 15.2 Setup Completo

```bash
# 1. Clonar repo
git clone <url> TradeApp && cd TradeApp

# 2. Configurar variables de entorno
cp .env.example .env
# El archivo .env ya funciona para desarrollo sin credenciales externas

# 3. Levantar infraestructura
docker-compose up -d postgres redis

# 4. Esperar a que PostgreSQL esté listo
docker-compose exec postgres pg_isready -U tradeapp

# 5. Ejecutar migraciones
docker-compose run --rm backend alembic upgrade head

# 6. Levantar servicios completos
docker-compose up -d

# 7. Verificar
curl http://localhost:8000/health          # → {"status":"ok"}
curl http://localhost:8000/api/v1/market/bcra/rates  # → tasas del BCRA
curl http://localhost:8000/docs            # Swagger UI
open http://localhost:3000                 # Frontend
```

### 15.3 Desarrollo del Backend

```bash
# Instalar dependencias localmente para IDE support
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows
pip install -r backend/requirements.txt

# Ejecutar backend sin Docker (requiere PostgreSQL y Redis corriendo)
cd backend
uvicorn app.main:app --reload --port 8000

# Ejecutar tests
pytest tests/ -v

# Ejecutar worker Celery (terminal separada)
celery -A app.workers.tasks worker --loglevel=info
```

### 15.4 Desarrollo del Frontend

```bash
cd frontend
npm install
npm run dev          # Puerto 3000
npm run type-check   # Verificar tipos TypeScript
npm run lint         # ESLint
npm run build        # Build de producción
```

### 15.5 Agregar un Nuevo Indicador Técnico

```python
# 1. Implementar el cálculo en services/technical/engine.py
def _nuevo_indicador(self, close: pd.Series, period: int) -> Optional[float]:
    # ... implementación ...

# 2. Agregar al método analyze()
result.nuevo_indicador = self._nuevo_indicador(close, period)

# 3. Agregar al dataclass IndicatorResult
nuevo_indicador: Optional[float] = None

# 4. Incorporar al algoritmo de señal en _generate_signal()
if result.nuevo_indicador and ...:
    score += X
    reasons.append("...")

# 5. Exponer en la respuesta de la API (api/v1/analysis.py)
"nuevo_indicador": result.nuevo_indicador,

# 6. Agregar tipo en frontend (types/market.ts) y mostrar en UI
```

### 15.6 Variables de Entorno por Módulo

| Variable | Módulo | Requerida | Descripción |
|----------|--------|-----------|-------------|
| `DATABASE_URL` | Backend, Workers | Sí | PostgreSQL + TimescaleDB |
| `REDIS_URL` | Backend, Workers | Sí | Redis para cache y queue |
| `SECRET_KEY` | Auth | Sí | JWT signing key |
| `IOL_USERNAME/PASSWORD` | Market Data | No (usa Rava como fallback) | Invertir Online |
| `MATBA_USER/PASSWORD` | Market Data | No | Futuros MatbaRofex |
| `OPENAI_API_KEY` | Fundamental (Fase 2) | No | Análisis NLP |
| `ANTHROPIC_API_KEY` | Fundamental (Fase 2) | No | Alternativa a OpenAI |
| `TELEGRAM_BOT_TOKEN` | Alertas | No | Bot de Telegram |
| `SMTP_USER/PASSWORD` | Alertas | No | Email de alertas |
