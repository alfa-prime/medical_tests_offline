from typing import Annotated, Optional

import httpx
from fastapi import Request, Depends, HTTPException, status, Security
from fastapi.security import APIKeyHeader
from app.service import GatewayService
from app.core import get_settings

settings = get_settings()


async def get_base_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.gateway_client


async def get_gateway_service(
        client: Annotated[httpx.AsyncClient, Depends(get_base_http_client)]
) -> GatewayService:
    return GatewayService(client=client)

api_key_header_scheme = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def get_api_key(api_key: Optional[str] = Security(api_key_header_scheme)):
    """
    Проверяет X-API-KEY. Теперь эта функция полностью контролирует ответ об ошибке.
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
