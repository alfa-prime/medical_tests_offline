from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core import get_gateway_service, get_api_key, get_settings, logger
from app.core.decorator import route_handle
from app.model import RequestPeriod
from app.model.response import TestResultResponse
from app.service import GatewayService, fetch_period_data, sanitize_period_data, save_json, get_tests_results
from app.mapper.section import sections

router = APIRouter(prefix="/dbase", tags=["Work with dbase"], dependencies=[Depends(get_api_key)])
settings = get_settings()

DEBUG_MODE = settings.DEBUG_MODE


def add_section_prefix(session_prefix: str, data: list[dict]) -> list[dict]:
    for each in data:
        each.update({"prefix": session_prefix})
    return data


@router.post(
    "/collector",
    summary="Собирает данные о результатах тестов за период",
    description="Отправляет запрос на API-шлюз с указанием периода.",
    response_model=List[TestResultResponse]
)
@route_handle
async def tests_results(
        period: RequestPeriod,
        gateway_service: Annotated[GatewayService, Depends(get_gateway_service)]
) -> List[TestResultResponse]:
    raw_data_all = []
    for section_id, section_data in sections.items():
        logger.warning(f"собираем данные для {section_id}")
        raw_data = await fetch_period_data(period, section_id, gateway_service)
        raw_data = add_section_prefix(section_data.prefix, raw_data)
        raw_data_all += raw_data

    sanitize_data = await sanitize_period_data(raw_data_all)

    results = await get_tests_results(sanitize_data, gateway_service)

    if DEBUG_MODE:
        save_json("01. raw_period.json", raw_data_all)
        save_json("02. sanitize_period.json", sanitize_data)
        save_json("03. results.json", results)

    return []
