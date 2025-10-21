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
    gateway_client = httpx.AsyncClient(
        base_url=settings.GATEWAY_URL,
        headers={"X-API-KEY": settings.GATEWAY_API_KEY},
        timeout=30.0
    )
    app.state.gateway_client = gateway_client
    logger.info(f"Gateway client initialized for base_url: {settings.GATEWAY_URL}")


async def shutdown_gateway_client(app: FastAPI):
    """
    Закрывает HTTPX клиент.
    Вызывается при остановке приложения.
    """
    if hasattr(app.state, 'gateway_client'):
        await app.state.gateway_client.aclose()
        logger.info("Gateway client closed.")
