from typing import Annotated, Optional

import httpx
from fastapi import Request, Depends, HTTPException, status, Security
from fastapi.security import APIKeyHeader
from app.service import GatewayService
from app.core import get_settings
from app.core.database import AsyncSessionLocal

settings = get_settings()


def get_base_http_client(request: Request) -> httpx.AsyncClient:
    """
    Возвращает HTTP-клиент, созданный при запуске приложения и сохранённый в `app.state`.
    Используется для выполнения HTTP-запросов к внешнему API (шлюзу).
    Args:
        request (Request): Объект запроса FastAPI.
    Returns:
        httpx.AsyncClient: Асинхронный HTTP-клиент.
    """
    return request.app.state.gateway_client


async def get_gateway_service(
        client: Annotated[httpx.AsyncClient, Depends(get_base_http_client)]
) -> GatewayService:
    """
    Создаёт и возвращает экземпляр сервиса для работы с API-шлюзом.
    Args:
        client (httpx.AsyncClient): HTTP-клиент, внедрённый через зависимость.
    Returns:
        GatewayService: Сервис для взаимодействия с API-шлюзом.
    """
    return GatewayService(client=client)


api_key_header_scheme = APIKeyHeader(name="X-API-KEY", auto_error=False)


async def get_api_key(api_key: Optional[str] = Security(api_key_header_scheme)):
    """
    Проверяет наличие и валидность X-API-KEY в заголовках запроса.
    Если ключ отсутствует или не совпадает с ожидаемым, выбрасывает HTTPException.
    Args:
        api_key (Optional[str]): Значение заголовка X-API-KEY.
    Raises:
        HTTPException: Если ключ отсутствует или невалиден (403).
    Returns:
        str: Валидный API-ключ.
    """
    if api_key and api_key == settings.GATEWAY_API_KEY:
        return api_key

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "error": "Authentication Failed",
            "message": "The provided X-API-KEY is missing or invalid.",
            "remedy": "Please include a valid 'X-API-KEY' header in your request."
        },
    )


async def get_db_session():
    """
    Создаёт асинхронную сессию для взаимодействия с БД.
    Используется как зависимость в роутах FastAPI для получения доступа к БД.
    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy.
    """
    async with AsyncSessionLocal() as session:
        yield session