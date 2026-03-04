# Fuentes de Datos — Guía Detallada

## Cotizaciones en Tiempo Real

### 1. Rava Bursátil (implementado)
- **URL**: `https://www.rava.com`
- **Datos**: Acciones, CEDEARs, Bonos, Letras, ONs del BYMA
- **Costo**: Gratuito (scraping de datos públicos)
- **Latencia**: ~5-10 segundos de delay respecto al mercado
- **Limite**: Sin límite conocido documentado
- **Uso en TradeApp**: Panel de cotizaciones, datos históricos

### 2. IOL (Invertir Online) — Recomendado para producción
- **URL**: `https://api.invertironline.com`
- **Docs**: https://api.invertironline.com/Help
- **Datos**: Cotizaciones en tiempo real, órdenes, portfolio
- **Costo**: Requiere cuenta en IOL (gratuita)
- **Latencia**: Tiempo real BYMA
- **Autenticación**: OAuth2 con usuario/contraseña IOL
- **Setup**:
  1. Crear cuenta en iol.com.ar
  2. Solicitar acceso a API en el portal
  3. Configurar `IOL_USERNAME` y `IOL_PASSWORD` en `.env`

### 3. Rava API Alternativa
- **URL**: `https://api.rava.com/v1/`
- **Datos**: Cotizaciones, portfolio (para clientes Rava)
- **Autenticación**: API Key

## Tasas de Referencia

### BCRA API (implementado)
- **URL**: `https://api.bcra.gob.ar`
- **Documentación**: https://www.bcra.gob.ar/Catalogo/apis.asp
- **Datos disponibles**:
  - Variable 4: USD BNA venta
  - Variable 6: TNA LELIQs
  - Variable 7: Tasa política monetaria
  - Variable 15: Inflación mensual IPC
  - Variable 27: BADLAR privados
  - Variable 40: TNA plazos fijos privados
- **Costo**: Totalmente gratuita
- **Límites**: Sin límites documentados

### CAFCI — Fondos Comunes de Inversión (implementado)
- **URL**: `https://api.cafci.org.ar`
- **Documentación**: https://api.cafci.org.ar/doc/
- **Datos**: Cuotapartes, rendimientos, patrimonio de todos los FCIs
- **Costo**: Gratuita
- **Actualización**: Diaria

## Datos Fundamentales

### CNV Open Data
- **URL**: https://datos.cnv.gob.ar
- **Datos**: ONs emitidas, estados financieros, hechos relevantes
- **Formato**: CSV/JSON
- **Uso**: Análisis fundamental de emisores de deuda corporativa

### Presentación de Balances
- Fuente: CNV (https://www.cnv.gov.ar) — Sistema FIDO
- BYMA (https://www.byma.com.ar) — Información relevante
- **Método**: Scraping + notificaciones RSS

### Noticias Financieras
```python
RSS_FEEDS = [
    "https://www.ambito.com/rss/pages/economia.xml",
    "https://www.infobae.com/economia/rss/",
    "https://www.cronista.com/rss/finanzas-mercados/",
    "https://www.iprofesional.com/rss/finanzas",
]
```

## Cotizaciones Dólar

### Dólar MEP y CCL
Calcular internamente desde:
- Precio ARS de un bono (ej: AL30)
- Precio USD del mismo bono (ej: AL30D)
- MEP = Precio ARS / Precio USD

### Dólar Blue / Informal
- Fuente: dolarapi.com (API pública)
- URL: `https://dolarapi.com/v1/dolares`

## MatbaRofex (Derivados)
- **URL**: `https://api.remarkets.primary.ventures`
- **Datos**: Futuros (dólar, soja, maíz), opciones
- **Autenticación**: Usuario/contraseña MatbaRofex
- **Librería Python**: `pyRofex`

## Cotizaciones Internacionales (para CEDEARs)
- **Yahoo Finance** vía `yfinance` (gratuito, sin key)
- **Alpha Vantage** (gratuito con límites, 25 req/día)
- **Polygon.io** (pago, más confiable)

```python
import yfinance as yf
aapl = yf.Ticker("AAPL")
hist = aapl.history(period="1y")
```
