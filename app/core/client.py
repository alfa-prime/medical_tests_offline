import httpx
from fastapi import FastAPI

from .config import get_settings
from app.core import logger

async def init_gateway_client(app: FastAPI):
    """
    Создает экземпляр HTTPX клиента и сохраняет его в app.state.
    Вызывается при старте приложения.
    """
    settings = get_settings()

    # Устанавливаем лимиты для клиента
    # max_connections: сколько всего соединений может быть в пуле
    # max_keepalive_connections: сколько из них могут быть "простаивающими" (keep-alive)
    limits = httpx.Limits(max_connections=50, max_keepalive_connections=25)

    gateway_client = httpx.AsyncClient(
        base_url=settings.GATEWAY_URL,
        headers={
            "X-API-KEY": settings.GATEWAY_API_KEY,
            "user-agen": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 YaBrowser/25.6.0.0 Safari/537.36"
        },
        timeout=settings.REQUEST_TIMEOUT,
        limits=limits

    )
    app.state.gateway_client = gateway_client
    logger.info(
        f"Gateway client initialized for base_url: {settings.GATEWAY_URL} with connection limit: {limits.max_connections}"
    )


async def shutdown_gateway_client(app: FastAPI):
    """
    Закрывает HTTPX клиент.
    Вызывается при остановке приложения.
    """
    if hasattr(app.state, 'gateway_client'):
        await app.state.gateway_client.aclose()
        logger.info("Gateway client closed.")
