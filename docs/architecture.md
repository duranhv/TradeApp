# Arquitectura Técnica Detallada

## Decisiones de Diseño

### ¿Por qué FastAPI + Python para el backend?

1. **Ecosistema financiero maduro**: pandas, numpy, scipy, TA-Lib, yfinance
2. **Async nativo**: FastAPI soporta async/await, ideal para múltiples llamadas a APIs externas en paralelo
3. **Validación automática**: Pydantic para validar todos los datos de entrada/salida
4. **Documentación automática**: OpenAPI/Swagger generado automáticamente
5. **Performance**: Uvicorn (ASGI) con rendimiento comparable a Node.js

### ¿Por qué Next.js 14 para el frontend?

1. **Server Components**: Renderizado del servidor para SEO y carga inicial rápida
2. **App Router**: Routing basado en directorio, layouts compartidos
3. **TypeScript de primera clase**: Tipado fuerte para datos financieros complejos
4. **Optimizaciones built-in**: Image optimization, font optimization, code splitting

### ¿Por qué TimescaleDB para series temporales?

Los precios históricos son un caso de uso ideal para TimescaleDB:
- **Compresión nativa**: 10-90x menos espacio que PostgreSQL estándar para series temporales
- **Hipertablas**: Particionado automático por tiempo
- **Funciones especializadas**: `time_bucket`, `first`, `last` para OHLCV
- **Compatible con PostgreSQL**: Sin cambios en el ORM

### Flujo de Datos

```
1. Celery Beat dispara tarea cada 1 minuto (horario de mercado)
2. Task: fetch prices desde Rava/IOL → guardar en PostgreSQL
3. Task: recalcular indicadores → guardar en technical_signals
4. Task: evaluar alertas activas → enviar notificaciones
5. Frontend polling: React Query refresca datos cada 60s
6. WebSocket (futuro): push de alertas en tiempo real
```

## Seguridad

- JWT tokens con rotación
- Rate limiting en Nginx (30 req/min por IP)
- CORS configurado explícitamente
- Secrets en variables de entorno (nunca en código)
- Sanitización de inputs con Pydantic
- SQL injection imposible con SQLAlchemy ORM

## Escalabilidad

### Nivel actual (MVP)
- 1 instancia backend + 1 worker Celery
- PostgreSQL single instance
- Redis single instance
- Soporta ~100 usuarios concurrentes

### Escala media (producción)
- Backend: 2-4 instancias detrás de Nginx load balancer
- Celery: múltiples workers por tipo de tarea (fast/slow)
- PostgreSQL: primary + read replica
- Redis Cluster

### Escala alta (SaaS con miles de usuarios)
- Backend: Kubernetes con HPA (auto-scaling horizontal)
- Base de datos: TimescaleDB Cloud o Aurora PostgreSQL
- Cache: ElastiCache Redis
- Mensajería: AWS SQS o Kafka para alertas
- CDN: CloudFront para assets del frontend
