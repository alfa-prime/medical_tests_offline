from typing import Annotated

from fastapi import APIRouter, Depends

from app.core import get_gateway_service, get_api_key, get_settings
from app.service import GatewayService, save_json, fetch_test_result

settings = get_settings()

router = APIRouter(prefix="/debug", tags=["Test requests for debug"], dependencies=[Depends(get_api_key)])


@router.post(
    "/test_result/{result_id}",
    summary="Собирает данные о результатах тестов за период",
    description="Отправляет запрос на API-шлюз с указанием периода."
)
async def get_test_result(
        result_id: str,
        gateway_service: Annotated[GatewayService, Depends(get_gateway_service)]
):
    result = await fetch_test_result(result_id, gateway_service)

    if settings.DEBUG_MODE:
        save_json("44. test_result_raw.json", result)

    return result
