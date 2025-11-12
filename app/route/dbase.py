from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_gateway_service
from app.core.decorator import route_handle
from app.core.dependencies import get_session, get_api_key
from app.model import RequestByMonth, RequestByDay, RequestByPatient, TestResultResponse
from app.service import GatewayService
from app.service.collector.process import collect_by_day, collect_by_month
from app.service.dbase.find_patient import find_records_by_patient

router = APIRouter(prefix="/dbase", tags=["Work with dbase"], dependencies=[Depends(get_api_key)])


@router.post(
    "/find_by_patient",
    summary="Найти все исследования по данным пациента",
    description="Выполняет поиск по ФИО и дате рождения. Возвращает список всех найденных исследований.",
    response_model=list[TestResultResponse]
)
@route_handle
async def find_by_patient(
        patient_data: RequestByPatient,
        session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Ищет и возвращает все записи о результатах тестов для указанного пациента.
    """
    return await find_records_by_patient(patient_data, session)


@router.post(
    "/by_day",
    summary="Собрать данные о результатах исследований за ОДИН день",
    description="Отправляет запрос на API-шлюз с указанием даты дня, ответ обрабатывается и сохраняется в БД.",
)
@route_handle
async def get_data_for_day(
        day: RequestByDay,
        gateway_service: Annotated[GatewayService, Depends(get_gateway_service)],
        session: Annotated[AsyncSession, Depends(get_session)],
):
    return await collect_by_day(day.date, gateway_service, session)


@router.post(
    path="/by_month",
    summary="Собрать данные о результатах исследований за месяц",
    description="Отправляет запрос на API-шлюз с указанием периода, ответ обрабатывается и сохраняется в БД."
)
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
