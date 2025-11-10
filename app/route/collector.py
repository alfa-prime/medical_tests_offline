from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_gateway_service, get_api_key
from app.core.decorator import route_handle
from app.core.dependencies import get_session, check_permission
from app.model import RequestByMonth, RequestByDay
from app.service import GatewayService
from app.service.collector.process import collect_by_day, collect_by_month
from app.service.collector.clear_db import reset_entire_database

router = APIRouter(prefix="/collector", tags=["Work with dbase"], dependencies=[Depends(get_api_key)])


@router.post(
    "/by_day",
    summary="Собирает данные о результатах тестов за период",
    description="Отправляет запрос на API-шлюз с указанием периода.",
)
@route_handle
async def get_data_for_day(
        day: RequestByDay,
        gateway_service: Annotated[GatewayService, Depends(get_gateway_service)],
        session: Annotated[AsyncSession, Depends(get_session)],
):
    # period = f"{day.date} - {day.date}"
    # result = await collect_by_day(period, gateway_service, session)
    # return {"status": "ok", "message": f"Processed {result} records."}
    return await collect_by_day(day.date, gateway_service, session)



@router.post(path="/by_month", summary="Собрать данные за месяц")
@route_handle
async def get_data_for_month(
        request_data: RequestByMonth,
        gateway_service: Annotated[GatewayService, Depends(get_gateway_service)],
        session: Annotated[AsyncSession, Depends(get_session)]
):
    """Собирает данные об исследованиях за месяц указанный в запросе"""
    year = request_data.year
    month = request_data.month
    return await collect_by_month(year, month, gateway_service, session)


@router.delete(
    "/reset-database",
    summary="Полностью сбросить базу данных",
    description="!!! ОПАСНО !!! Удаляет ВСЕ таблицы из базы данных и создает их заново. Все данные будут потеряны.",
    dependencies=[Depends(check_permission)]
)
async def clear_db():
    return await reset_entire_database()
