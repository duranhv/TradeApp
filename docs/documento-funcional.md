# TradeApp — Documento Funcional de la Solución

**Versión**: 1.0
**Fecha**: Marzo 2026
**Estado**: Borrador para revisión

---

## Índice

1. [Propósito y Alcance](#1-propósito-y-alcance)
2. [Actores y Perfiles de Usuario](#2-actores-y-perfiles-de-usuario)
3. [Módulos Funcionales](#3-módulos-funcionales)
4. [Flujos de Trabajo Principales](#4-flujos-de-trabajo-principales)
5. [Comparador de Tasas y Rendimientos](#5-comparador-de-tasas-y-rendimientos)
6. [Sistema de Alertas](#6-sistema-de-alertas)
7. [Portfolio Tracker](#7-portfolio-tracker)
8. [Análisis Fundamental](#8-análisis-fundamental)
9. [Reglas de Negocio](#9-reglas-de-negocio)
10. [Planes de Suscripción](#10-planes-de-suscripción)
11. [Consideraciones Regulatorias y Legales](#11-consideraciones-regulatorias-y-legales)
12. [Glosario de Términos Financieros](#12-glosario-de-términos-financieros)

---

## 1. Propósito y Alcance

### 1.1 Propósito

TradeApp es una plataforma SaaS web orientada a inversores individuales y profesionales del mercado financiero argentino. Su propósito es centralizar el análisis técnico y fundamental de los distintos instrumentos disponibles en el mercado local, generando señales de compra y venta fundamentadas, y facilitando la comparación de rendimientos entre alternativas de inversión.

La plataforma **no ejecuta órdenes de compra/venta** ni actúa como intermediario financiero. Su función es exclusivamente de análisis e información.

### 1.2 Problema que resuelve

El inversor argentino enfrenta una complejidad particular:

- **Multiplicidad de instrumentos**: acciones, CEDEARs, bonos, letras, cauciones, ONs, FCIs, plazos fijos, todos en ARS y/o USD, con mecánicas distintas
- **Volatilidad cambiaria**: las decisiones deben evaluarse en ARS, USD oficial, USD MEP y USD CCL simultáneamente
- **Inflación como variable dominante**: la tasa real (rendimiento nominal menos inflación) es determinante en la toma de decisiones
- **Dispersión de información**: las cotizaciones están en Rava, las tasas en BCRA, los FCI en CAFCI, los balances en CNV — sin un lugar unificado
- **Análisis técnico manual**: requiere conocimientos específicos y tiempo para calcular indicadores

TradeApp resuelve esto integrando todas las fuentes en una sola interfaz, automatizando el análisis y presentando recomendaciones accionables.

### 1.3 Alcance del MVP (Fase 1)

**Incluido:**
- Cotizaciones en tiempo real: acciones (BYMA), CEDEARs, bonos soberanos, letras del Tesoro, ONs
- Análisis técnico con señales automáticas de compra/venta
- Comparador de tasas: PF, Caución, FCI Money Market, Letras, Bonos
- Alertas de precio y técnicas por email
- Dashboard con resumen del mercado

**No incluido en MVP (Fase 2+):**
- Análisis fundamental con NLP de noticias
- Portfolio tracker con P&L
- Futuros y opciones (MatbaRofex)
- App móvil nativa
- Ejecución de órdenes vía broker

---

## 2. Actores y Perfiles de Usuario

### 2.1 Inversor Retail (usuario principal)

**Perfil**: Persona física con ahorros para invertir, conocimiento financiero básico-intermedio. Invierte en PF, FCI, CEDEARs y acciones locales.

**Necesidades**:
- Saber dónde conviene poner el dinero hoy (comparador de tasas)
- Entender si una acción o CEDEAR está cara o barata (análisis técnico)
- Recibir una señal clara cuando hay oportunidad de compra o venta
- Ver todo en ARS y comparar contra el dólar

**Frequencia de uso**: Diaria o semanal

### 2.2 Inversor Avanzado / Trader

**Perfil**: Persona con conocimiento técnico del mercado, opera con frecuencia, maneja múltiples posiciones.

**Necesidades**:
- Screener para identificar oportunidades en todo el mercado simultáneamente
- Indicadores técnicos completos con personalización de parámetros
- Alertas en tiempo real (email + Telegram)
- Análisis de bonos con TIR/YTM y duración

**Frecuencia de uso**: Varias veces por día (durante el horario de mercado)

### 2.3 Asesor Financiero / ALyC

**Perfil**: Profesional que gestiona carteras de clientes, necesita justificar sus recomendaciones.

**Necesidades**:
- Informes exportables en PDF
- Historial de señales para auditoría
- Comparativos de rendimientos para presentar a clientes
- API propia para integrar en sus sistemas

**Frecuencia de uso**: Diaria

### 2.4 Administrador del Sistema

**Perfil**: Equipo técnico de TradeApp.

**Responsabilidades**: Gestión de usuarios, monitoreo del sistema, actualización de fuentes de datos, configuración de parámetros del sistema de alertas.

---

## 3. Módulos Funcionales

### 3.1 Mapa de Módulos

```
┌─────────────────────────────────────────────────────────────────┐
│                         TradeApp                                 │
├──────────────┬──────────────┬───────────────┬───────────────────┤
│   Dashboard  │  Análisis    │  Comparador   │    Portfolio      │
│   General    │  Técnico     │  de Tasas     │    Tracker        │
├──────────────┼──────────────┼───────────────┼───────────────────┤
│   Screener   │  Análisis    │   Sistema de  │   Reportes y      │
│   de Mercado │  Fundamental │   Alertas     │   Exportación     │
└──────────────┴──────────────┴───────────────┴───────────────────┘
```

### 3.2 Dashboard General

**Descripción**: Pantalla principal. Presenta un resumen ejecutivo del mercado en el momento de ingresar.

**Información mostrada**:
- Indicadores macroeconómicos del día (obtenidos del BCRA):
  - Tasa política monetaria (TNA)
  - Tasa de PF bancos privados (TNA / TEA)
  - Inflación mensual y anual acumulada
  - Cotización dólar oficial, MEP y CCL
- Variación del índice S&P Merval (ARS y USD)
- Top 5 acciones con mayor señal alcista del día
- Top 5 acciones con mayor señal bajista del día
- Alertas recientes del usuario

**Actualización**: Los indicadores del BCRA se actualizan 1 vez por día. Las cotizaciones, cada 1 minuto durante el horario de mercado (11:00 - 17:30, lunes a viernes).

### 3.3 Módulo de Análisis Técnico

**Descripción**: Análisis completo de un activo individual con todos los indicadores técnicos.

**Funcionalidades**:
1. **Búsqueda de activo**: por ticker o nombre (GGAL, YPF, AL30, CEDEAR AAPL, etc.)
2. **Gráfico de precios interactivo**: velas japonesas con zoom, escala logarítmica opcional
3. **Selección de temporalidad**: intradía (1m, 5m, 15m, 1h), diario, semanal
4. **Panel de indicadores**: visualización gráfica y numérica de cada indicador
5. **Señal consolidada**: score numérico (-100 a +100) con justificación textual

**Indicadores disponibles**:

| Categoría | Indicadores |
|-----------|------------|
| Medias Móviles | SMA 20, SMA 50, SMA 200, EMA 9, EMA 21, EMA 55 |
| Momentum | RSI (14), Stochastic (14,3,3), CCI (20), Williams %R (14) |
| Tendencia | MACD (12,26,9), ADX (14) |
| Volatilidad | Bollinger Bands (20,2), ATR (14), Keltner Channels |
| Volumen | OBV, VWAP (intradía), MFI (14) |
| Niveles | Pivot Points, Fibonacci Retracement, Soporte/Resistencia automático |

**Interpretación de señales**:

| Señal | Score | Color | Descripción |
|-------|-------|-------|-------------|
| Compra Fuerte | 40 a 100 | Verde oscuro | Múltiples indicadores alineados alcistas |
| Comprar | 15 a 39 | Verde | Mayoría de indicadores apuntan al alza |
| Neutral | -14 a 14 | Amarillo | Señales contradictorias o sin tendencia clara |
| Vender | -15 a -39 | Naranja | Mayoría de indicadores apuntan a la baja |
| Venta Fuerte | -40 a -100 | Rojo | Múltiples indicadores alineados bajistas |

### 3.4 Screener de Mercado

**Descripción**: Herramienta para analizar todo un panel de instrumentos simultáneamente y filtrar por señal técnica.

**Parámetros de filtrado**:
- Panel: Acciones, CEDEARs, Bonos, Letras
- Tipo de señal: Compra Fuerte / Comprar / Neutral / Vender / Venta Fuerte
- Rango de score: ej. score > 30
- RSI: ej. RSI < 35 (zona de sobreventa)
- Posición relativa a medias: precio por encima de SMA50
- Variación del día: ej. sube más del 3%

**Resultado**: Tabla ordenable con ticker, precio, variación, señal, score, RSI, posición vs. medias, y acceso directo al análisis completo.

**Caso de uso típico**: "Quiero ver todas las acciones del BYMA que estén en zona de sobreventa (RSI < 30) y con señal de compra o compra fuerte"

---

## 4. Flujos de Trabajo Principales

### 4.1 Flujo: Análisis de una Acción

```
Usuario ingresa ticker (ej. "GGAL")
    ↓
Sistema carga cotización actual + histórico 12 meses
    ↓
Motor de análisis calcula los 15+ indicadores
    ↓
Algoritmo de señal pondera indicadores → genera score y señal
    ↓
Frontend presenta:
    ├── Gráfico de velas con BB, SMA20, SMA50
    ├── Panel de indicadores con valores y colores semafóricos
    └── Señal final con justificación textual ("RSI = 28: zona de sobreventa...")
    ↓
Usuario puede configurar alerta en base al análisis
```

### 4.2 Flujo: Decisión de Inversión de Corto Plazo

```
Usuario quiere invertir $500.000 ARS por 30 días
    ↓
Abre Comparador de Tasas → ingresa: capital $500.000 / horizonte 30 días / ARS
    ↓
Sistema consulta:
    ├── BCRA API → TNA Plazo Fijo bancos privados y públicos
    ├── BYMA → Tasa de cauciones (1d, 7d, 30d)
    ├── CAFCI → Rendimientos FCIs Money Market (T+0)
    └── Cotizaciones → LECAPs y BONCAPs disponibles con TIR calculada
    ↓
Tabla comparativa ordenada por TNA descendente:
    ├── Retorno proyectado en $
    ├── Capital final al vencimiento
    └── Información de riesgo y liquidez
    ↓
Usuario toma decisión informada (ej. LECAP con mayor TNA que PF)
```

### 4.3 Flujo: Configuración de Alerta

```
Usuario navega al activo (ej. AAPL CEDEAR)
    ↓
Hace click en "Crear Alerta"
    ↓
Selecciona tipo:
    ├── Precio: "Avisar cuando supere $15.000"
    ├── Técnica: "Avisar cuando RSI baje de 30"
    └── Cruce: "Avisar cuando EMA9 cruce EMA21 al alza"
    ↓
Selecciona canal: Email / Telegram / Notificación web
    ↓
Confirma. Alerta queda activa.
    ↓
Celery evalúa la alerta cada 2 minutos durante el horario de mercado
    ↓
Cuando la condición se cumple → dispara notificación con:
    ├── Nombre del activo y tipo de señal
    ├── Precio actual y valor del indicador
    └── Link directo al análisis completo
```

---

## 5. Comparador de Tasas y Rendimientos

Este módulo es uno de los diferenciadores principales de TradeApp para el mercado argentino.

### 5.1 Instrumentos Comparados

#### Renta Fija en ARS

| Instrumento | Fuente de Datos | Plazo | Liquidez | Riesgo |
|-------------|----------------|-------|----------|--------|
| **Plazo Fijo tradicional** | BCRA API (TNA oficial) | 30-180 días | Al vencimiento | Bajo (FGD hasta $6M) |
| **Plazo Fijo UVA** | BCRA API | 90+ días | Al vencimiento | Bajo (ajusta por CER) |
| **Caución bursátil** | BYMA en tiempo real | 1-120 días | Al vencimiento | Bajo (garantía BYMA) |
| **FCI Money Market** | CAFCI API | Diario | T+0 (inmediato) | Bajo |
| **FCI Renta Fija** | CAFCI API | Variable | T+1 a T+3 | Bajo-Medio |
| **LECAP / BONCAP** | Cotizaciones BYMA | Hasta vencimiento | T+1 (mercado) | Bajo (soberano) |
| **LETES / LECER** | Cotizaciones BYMA | Hasta vencimiento | T+1 (mercado) | Bajo (soberano) |

#### Renta Fija en USD

| Instrumento | Fuente de Datos | Plazo | Liquidez | Riesgo |
|-------------|----------------|-------|----------|--------|
| **Bonos Soberanos USD** (AL30, GD30, AL35...) | BYMA | Largo plazo | T+1 | Alto |
| **ON Corporativas USD** (YPF, PAMPA, MSU...) | BYMA | Variable | T+1 | Medio |
| **PF en USD** | Bancos (scraping) | 30+ días | Al vencimiento | Bajo-Medio |
| **Obligaciones Negociables Dólar Linked** | BYMA | Variable | T+1 | Medio |

#### Renta Variable

| Instrumento | Notas |
|-------------|-------|
| **Acciones BYMA** | Análisis técnico y fundamental |
| **CEDEARs** | Cotización en ARS, subyacente en USD |

### 5.2 Métricas Calculadas

Para cada instrumento, TradeApp calcula y muestra:

- **TNA** (Tasa Nominal Anual): base de comparación
- **TEA** (Tasa Efectiva Anual): considerando reinversión mensual
- **TEM** (Tasa Efectiva Mensual): para horizontes de 30 días
- **Retorno proyectado en $**: capital × TNA × (días / 365)
- **Capital final**: capital inicial + retorno proyectado
- **Tasa real**: TNA ajustada por inflación mensual del BCRA
- **TIR/YTM** (para bonos y letras): rendimiento considerando precio de mercado

### 5.3 Parámetros Configurables

- **Horizonte**: 7 / 30 / 60 / 90 / 180 / 365 días (o personalizado)
- **Capital**: libre ingreso en ARS o USD
- **Moneda base**: ARS o USD
- **Filtro de riesgo**: bajo / medio / alto

### 5.4 Escenarios de Uso Típicos

**Escenario 1 — Colocación de corto plazo (< 30 días)**
> Comparar: Caución 7d vs FCI Money Market vs LECAP corta
> Prioridad: liquidez + tasa

**Escenario 2 — Ahorro de mediano plazo (30-180 días)**
> Comparar: PF 60d vs LECAP vs Caución vs FCI Renta Fija
> Prioridad: tasa máxima con garantía de capital

**Escenario 3 — Cobertura en dólares**
> Comparar: ON en USD vs Bono soberano USD vs PF en USD
> Prioridad: rendimiento en USD + riesgo emisor

---

## 6. Sistema de Alertas

### 6.1 Tipos de Alertas

#### Alertas de Precio
- Precio **supera** un valor definido (ej. GGAL > $5.000)
- Precio **cae por debajo** de un valor definido (ej. YPF < $20.000)
- Variación porcentual en el día **supera** un umbral (ej. +5% en el día)

#### Alertas Técnicas
- **RSI** entra en zona de sobreventa (< 30) o sobrecompra (> 70)
- **Cruce de medias móviles**: EMA9 cruza EMA21 al alza o a la baja
- **MACD** genera cruce de señal alcista o bajista
- **Bollinger**: precio toca la banda superior o inferior
- **Stochastic**: K cruza D en zona extrema (< 20 o > 80)

#### Alertas Fundamentales (Fase 2)
- Nueva publicación de **balance trimestral** de un emisor
- **Hecho relevante** publicado en CNV para un activo
- Cambio de **calificación crediticia** de un bono
- **Noticias** con sentimiento fuerte (positivo/negativo) sobre un activo

#### Alertas del Comparador
- La tasa del PF **sube** o **baja** más de X puntos porcentuales
- Una LECAP o bono supera en rendimiento al PF por X%

### 6.2 Canales de Notificación

| Canal | Disponibilidad | Plan mínimo |
|-------|---------------|-------------|
| Notificación web (push) | Tiempo real | Gratuito |
| Email | Hasta 5 alertas/día | Gratuito |
| Email sin límite | Ilimitado | Pro |
| Telegram Bot | Tiempo real | Pro |
| SMS | Disponible | Premium |

### 6.3 Gestión de Alertas

- Las alertas pueden ser de **disparo único** (se desactivan al cumplirse) o **recurrentes**
- Historial de alertas disparadas con snapshot de indicadores al momento del disparo
- Máximo de alertas activas según plan (Free: 5, Pro: 50, Premium: ilimitado)

---

## 7. Portfolio Tracker

### 7.1 Funcionalidades

- **Registro de posiciones**: ticker, cantidad, precio promedio de compra, fecha, moneda
- **Valuación en tiempo real**: valor actual de la cartera en ARS y USD
- **P&L** (Profit & Loss): ganancia/pérdida en ARS, USD y en % desde la compra
- **Comparación vs. benchmarks**:
  - S&P Merval (ARS)
  - Dólar MEP
  - CER (inflación)
  - S&P 500 (USD)
- **Diversificación**: gráfico de composición por tipo de activo y moneda

### 7.2 Ejemplo de Valuación

```
Posición: 1.000 acciones de GGAL
Precio promedio compra: $4.200 ARS
Precio actual: $5.100 ARS
Variación: +21,4% en ARS

Costo total: $4.200.000 ARS
Valor actual: $5.100.000 ARS
Ganancia: +$900.000 ARS

En USD MEP (tipo $1.250):
Costo: USD 3.360
Valor: USD 4.080
Ganancia: +USD 720 (+21,4%)
```

### 7.3 Importación de Posiciones

- Ingreso manual
- Importación desde CSV (formato IOL/Balanz/PPI)
- Futura integración directa con brokers vía API (Fase 3)

---

## 8. Análisis Fundamental

### 8.1 Fuentes de Información (Fase 2)

**Noticias financieras** (procesadas con NLP):
- Ambito Financiero, Infobae Economía, El Cronista, iProfesional
- Feeds RSS actualizados cada 15 minutos
- Análisis de sentimiento: positivo / negativo / neutro por ticker

**Balances y estados contables**:
- Presentaciones al CNV (Sistema FIDO)
- Alertas automáticas cuando se publica un nuevo balance
- Extracción de KPIs: ingresos, EBITDA, deuda neta, resultado neto

**Ratios fundamentales**:

| Ratio | Descripción | Uso |
|-------|-------------|-----|
| P/E | Precio / Ganancias | ¿La acción está cara o barata? |
| EV/EBITDA | Valor empresa / EBITDA | Valoración comparativa entre empresas |
| ROE | Retorno sobre patrimonio | Rentabilidad del negocio |
| Deuda Neta / EBITDA | Apalancamiento | Riesgo crediticio |
| Margen EBITDA | EBITDA / Ingresos | Eficiencia operativa |

### 8.2 Score Fundamental

Cada emisor tendrá un **Score Fundamental (0-100)** calculado en base a:
- Calidad de los últimos 3 balances presentados (30%)
- Sentimiento de noticias últimos 30 días (25%)
- Ratios financieros vs. promedio del sector (25%)
- Historial de cumplimiento de deuda / dividendos (20%)

### 8.3 Señal Combinada (Técnica + Fundamental)

En Fase 2, la señal final integrará ambos análisis:

```
Score Técnico: +45 (Comprar)  × peso 60%
Score Fundamental: +70 (Positivo) × peso 40%

Score Combinado = (45 × 0.6) + (70 × 0.4) = 27 + 28 = 55 → Compra Fuerte
```

---

## 9. Reglas de Negocio

### 9.1 Horarios

- **Mercado BYMA**: lunes a viernes, 11:00 - 17:30 (hora Argentina)
- **Actualización de cotizaciones**: cada 1 minuto durante el horario de mercado
- **Evaluación de alertas**: cada 2 minutos durante el horario de mercado
- **Actualización de tasas BCRA**: 1 vez por día, a las 9:00
- **Análisis de cierre**: 18:00, con el resumen del día

### 9.2 Cálculo de Tasas

- Todas las tasas se expresan en **TNA (base 365 días)**, salvo indicación contraria
- La **TEA** se calcula asumiendo reinversión mensual: `TEA = (1 + TNA/12)^12 - 1`
- El **rendimiento real** se calcula: `Tasa Real = ((1 + TNA) / (1 + Inflación)) - 1`
- Para bonos y letras, la **TIR** se calcula a partir del precio de mercado (no del valor nominal)

### 9.3 Ponderación del Score Técnico

| Indicador / Categoría | Peso |
|-----------------------|------|
| Tendencia (cruces de medias) | 35% |
| Momentum (RSI + Stochastic) | 25% |
| MACD | 20% |
| Bollinger Bands | 20% |

### 9.4 Datos Históricos

- Se almacenan como mínimo **2 años de datos diarios** por activo
- Para intradía, se almacenan **90 días de datos en velas de 1 hora**
- Los datos se actualizan en tiempo real durante el horario de mercado
- Los activos sin cotización por más de 90 días se marcan como "inactivos"

---

## 10. Planes de Suscripción

### 10.1 Estructura de Planes

| Funcionalidad | Gratuito | Pro | Premium |
|---------------|----------|-----|---------|
| Dashboard general | ✓ | ✓ | ✓ |
| Comparador de tasas | ✓ | ✓ | ✓ |
| Análisis técnico (5 tickers/día) | ✓ | ✓ | ✓ |
| Análisis técnico ilimitado | — | ✓ | ✓ |
| Screener de mercado | Básico | Completo | Completo |
| Alertas activas | 5 | 50 | Ilimitado |
| Notificaciones email | 5/día | Ilimitado | Ilimitado |
| Notificaciones Telegram | — | ✓ | ✓ |
| Portfolio Tracker | 1 cartera | 5 carteras | Ilimitado |
| Análisis fundamental | — | ✓ | ✓ |
| Exportación PDF/CSV | — | ✓ | ✓ |
| API Access | — | — | ✓ |
| Soporte | Email | Prioritario | Dedicado |
| **Precio** | **Gratis** | **$X/mes ARS** | **$Y/mes ARS** |

> Los precios en ARS se ajustarán trimestralmente por inflación.

### 10.2 Política de Datos

- Los usuarios Free tienen acceso a datos con 15 minutos de demora
- Los usuarios Pro y Premium acceden a datos casi en tiempo real (delay < 2 min)
- Los datos históricos están disponibles para todos los planes

---

## 11. Consideraciones Regulatorias y Legales

### 11.1 Marco Legal

TradeApp opera como una plataforma de **información y análisis financiero**, no como Agente de Liquidación y Compensación (ALyC), asesor de inversiones registrado ni entidad regulada por la CNV en su actividad de intermediación.

> Las recomendaciones generadas por los algoritmos de TradeApp son de carácter informativo. No constituyen asesoramiento financiero personalizado. El usuario es el único responsable de sus decisiones de inversión.

### 11.2 Disclaimer Obligatorio

En toda pantalla que muestre señales o recomendaciones se mostrará el siguiente texto:

> *"Las señales, scores y análisis presentados en TradeApp son generados automáticamente a partir de datos históricos y modelos matemáticos. No constituyen asesoramiento de inversión. Invertir en mercados financieros implica riesgos, incluyendo la posible pérdida del capital invertido. Rentabilidades pasadas no garantizan resultados futuros."*

### 11.3 Uso de Datos de Mercado

- Los datos de cotizaciones son redistribuidos conforme a las condiciones de uso de cada fuente (BCRA, CAFCI, Rava Bursátil)
- Para una versión comercial a escala, se requerirá firma de acuerdos de distribución con BYMA o un proveedor de market data certificado

### 11.4 Privacidad de Datos

- Los datos de portfolio del usuario se almacenan encriptados
- TradeApp no comparte datos de posiciones de usuarios con terceros
- Cumplimiento con la Ley 25.326 de Protección de Datos Personales (Argentina)

---

## 12. Glosario de Términos Financieros

| Término | Definición |
|---------|-----------|
| **TNA** | Tasa Nominal Anual. Base de comparación de tasas. |
| **TEA** | Tasa Efectiva Anual. Incluye el efecto del interés compuesto. |
| **TEM** | Tasa Efectiva Mensual. Equivalente mensual de la TEA. |
| **TIR / YTM** | Tasa Interna de Retorno. Para bonos: rendimiento real considerando precio de mercado. |
| **Caución Bursátil** | Préstamo de corto plazo garantizado con títulos valores, operado en BYMA. |
| **LECAP / BONCAP** | Letras y Bonos capitalizables del Tesoro Nacional en ARS. |
| **LETES** | Letras del Tesoro en dólares. |
| **LECER** | Letras del Tesoro ajustadas por CER (inflación). |
| **ON** | Obligación Negociable. Deuda corporativa emitida por empresas. |
| **FCI** | Fondo Común de Inversión. |
| **Money Market** | FCI de muy corto plazo, invierte en cauciones y cuentas bancarias. T+0. |
| **CEDEAR** | Certificado de Depósito Argentino. Cotiza en BYMA, representa acciones extranjeras. |
| **MEP / Dólar Bolsa** | Dólar obtenido comprando y vendiendo bonos en ARS y USD. |
| **CCL** | Contado con Liquidación. Dólar bursátil con liquidación en el exterior. |
| **CER** | Coeficiente de Estabilización de Referencia. Índice que replica la inflación minorista. |
| **BADLAR** | Tasa de depósitos a plazo fijo de más de $1M en bancos privados. |
| **RSI** | Relative Strength Index. Indicador de momentum (0-100). < 30: sobreventa, > 70: sobrecompra. |
| **MACD** | Moving Average Convergence Divergence. Indicador de tendencia y momentum. |
| **Bollinger Bands** | Bandas de volatilidad alrededor de una media móvil. |
| **Stochastic** | Indicador de momentum que compara precio de cierre con el rango del período. |
| **ATR** | Average True Range. Medida de volatilidad del mercado. |
| **OBV** | On Balance Volume. Indicador de volumen acumulado. |
| **VWAP** | Volume Weighted Average Price. Precio promedio ponderado por volumen intradía. |
| **P&L** | Profit & Loss. Ganancias y pérdidas de una posición. |
| **FGD** | Fondo de Garantía de Depósitos. Garantiza PF hasta $6M por entidad. |
| **ALyC** | Agente de Liquidación y Compensación. Broker autorizado por CNV. |
