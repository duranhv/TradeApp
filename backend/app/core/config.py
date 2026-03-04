from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "TradeApp"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://tradeapp:tradeapp@localhost:5432/tradeapp"
    DATABASE_POOL_SIZE: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Cache TTLs (seconds)
    PRICE_CACHE_TTL: int = 60          # Precios: 1 minuto
    INDICATOR_CACHE_TTL: int = 300     # Indicadores: 5 minutos
    RATE_CACHE_TTL: int = 3600         # Tasas: 1 hora
    NEWS_CACHE_TTL: int = 900          # Noticias: 15 minutos

    # External APIs
    IOL_BASE_URL: str = "https://api.invertironline.com"
    IOL_USERNAME: str = ""
    IOL_PASSWORD: str = ""

    RAVA_BASE_URL: str = "https://www.rava.com/series/preciostabla.php"

    BCRA_API_URL: str = "https://api.bcra.gob.ar"

    CAFCI_API_URL: str = "https://api.cafci.org.ar"

    MATBA_ROFEX_URL: str = "https://api.remarkets.primary.ventures"
    MATBA_USER: str = ""
    MATBA_PASSWORD: str = ""

    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Telegram Bot (alertas)
    TELEGRAM_BOT_TOKEN: str = ""

    # Email (alertas)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://tradeapp.com.ar"]

    # Market Schedule (Buenos Aires timezone)
    MARKET_OPEN_HOUR: int = 11
    MARKET_OPEN_MINUTE: int = 0
    MARKET_CLOSE_HOUR: int = 17
    MARKET_CLOSE_MINUTE: int = 30
    MARKET_TIMEZONE: str = "America/Argentina/Buenos_Aires"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
