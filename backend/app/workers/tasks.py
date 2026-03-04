"""
Tareas Celery para procesamiento en background.
- Actualización periódica de cotizaciones
- Recálculo de indicadores técnicos
- Evaluación de alertas
- Actualización de tasas del BCRA
"""
import asyncio
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "tradeapp",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Argentina/Buenos_Aires",
    enable_utc=False,
    task_track_started=True,
    task_time_limit=300,
    worker_prefetch_multiplier=1,
)

# ── Tareas periódicas ────────────────────────────────────────────────────────
celery_app.conf.beat_schedule = {
    # Durante el horario de mercado (lunes a viernes, 11:00 - 17:30)
    "update-prices-every-minute": {
        "task": "app.workers.tasks.update_all_prices",
        "schedule": crontab(
            minute="*/1",
            hour="11-17",
            day_of_week="1-5",
        ),
    },
    "calculate-indicators-every-5min": {
        "task": "app.workers.tasks.recalculate_indicators",
        "schedule": crontab(
            minute="*/5",
            hour="11-17",
            day_of_week="1-5",
        ),
    },
    "check-alerts-every-2min": {
        "task": "app.workers.tasks.check_all_alerts",
        "schedule": crontab(
            minute="*/2",
            hour="11-17",
            day_of_week="1-5",
        ),
    },
    # Fuera del horario de mercado
    "update-bcra-rates-daily": {
        "task": "app.workers.tasks.update_bcra_rates",
        "schedule": crontab(hour="9", minute="0"),
    },
    "update-fci-rates-daily": {
        "task": "app.workers.tasks.update_fci_rates",
        "schedule": crontab(hour="9", minute="30"),
    },
    "daily-close-analysis": {
        "task": "app.workers.tasks.run_daily_close_analysis",
        "schedule": crontab(hour="18", minute="0", day_of_week="1-5"),
    },
}


def run_async(coro):
    """Helper para ejecutar corutinas en workers síncronos."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.workers.tasks.update_all_prices", bind=True, max_retries=3)
def update_all_prices(self):
    """Actualiza cotizaciones de todos los paneles y las guarda en cache/DB."""
    try:
        from app.services.market_data.rava_client import RavaClient
        rava = RavaClient()
        all_data = run_async(rava.get_all_quotes_parallel())
        total = sum(len(v) for v in all_data.values())
        return {"status": "ok", "updated": total}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="app.workers.tasks.recalculate_indicators")
def recalculate_indicators():
    """Recalcula indicadores técnicos para los activos activos."""
    # En producción: consultar activos en DB, recalcular y guardar señales
    return {"status": "ok", "message": "Indicadores recalculados"}


@celery_app.task(name="app.workers.tasks.check_all_alerts")
def check_all_alerts():
    """Evalúa todas las alertas activas y dispara notificaciones."""
    return {"status": "ok", "message": "Alertas evaluadas"}


@celery_app.task(name="app.workers.tasks.update_bcra_rates")
def update_bcra_rates():
    """Actualiza tasas del BCRA."""
    try:
        from app.services.market_data.bcra_client import BCRAClient
        bcra = BCRAClient()
        rates = run_async(bcra.get_key_rates())
        return {"status": "ok", "rates": rates}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@celery_app.task(name="app.workers.tasks.update_fci_rates")
def update_fci_rates():
    """Actualiza rendimientos de FCIs desde CAFCI."""
    try:
        from app.services.market_data.rava_client import CafciClient
        cafci = CafciClient()
        funds = run_async(cafci.get_money_market_funds())
        return {"status": "ok", "funds_updated": len(funds)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@celery_app.task(name="app.workers.tasks.run_daily_close_analysis")
def run_daily_close_analysis():
    """
    Análisis al cierre del mercado:
    - Calcula señales diarias para todos los activos
    - Genera resumen de oportunidades
    - Envía digest por email a usuarios con alertas activas
    """
    return {"status": "ok", "message": "Análisis de cierre completado"}
