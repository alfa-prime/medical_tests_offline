from typing import Annotated

from fastapi import APIRouter, Depends

from app.core import get_gateway_service, get_api_key, get_settings
from app.model import RequestPeriod
from app.service import GatewayService, fetch_period_data, sanitize_period_data, save_json, get_tests_results

router = APIRouter(prefix="/dbase", tags=["Work with dbase"], dependencies=[Depends(get_api_key)])
settings = get_settings()

DEBUG_MODE = settings.DEBUG_MODE

@router.post(
    "/collector",
    summary="Собирает данные о результатах тестов за период",
    description="Отправляет запрос на API-шлюз с указанием периода."
)
async def check_gateway_connection(
        period: RequestPeriod,
        gateway_service: Annotated[GatewayService, Depends(get_gateway_service)]
):
    data = await fetch_period_data(period, gateway_service)
    sanitize_data = await sanitize_period_data(data)
    with_results = await get_tests_results(sanitize_data, gateway_service)



    if DEBUG_MODE:
        save_json("01. raw_period.json", data)
        save_json("02. sanitize_period.json", sanitize_data)
        save_json("03. results.json", with_results)

    return sanitize_data
