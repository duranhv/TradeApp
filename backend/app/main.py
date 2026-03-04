from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.v1 import market, analysis, comparison


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} iniciando...")
    yield
    # Shutdown
    print("Cerrando conexiones...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## TradeApp — API de Análisis Financiero

Plataforma SaaS para análisis técnico y fundamental del mercado financiero argentino.

### Módulos
- **Market Data**: Cotizaciones en tiempo real (BYMA, CEDEARs, Bonos, Letras)
- **Technical Analysis**: Indicadores y señales de compra/venta
- **Rate Comparison**: Cuadro comparativo de tasas (PF, Caución, FCI, Bonos)
- **Alerts**: Sistema de alertas personalizadas

### Fuentes de Datos
- BYMA vía Rava Bursátil
- BCRA API (tasas oficiales)
- CAFCI (FCIs)
- MatbaRofex (futuros)
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Routers
app.include_router(market.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(comparison.router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
