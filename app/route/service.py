from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from fastapi import APIRouter, Depends, Request

from app.core.dependencies import get_session, check_permission, get_api_key
# from app.service.dbase.clear_db import reset_entire_database
from app.service.dbase.dump_bd import create_database_dump
from app.core.decorator import route_handle
from app.service.scheduler import sync_database
from app.core import get_gateway_service
from app.model import RequestByMonth, RequestByDay
from app.service import GatewayService
from app.service.collector.process import collect_by_day, collect_by_month

router = APIRouter(prefix="/service", tags=["Service functions"], dependencies=[Depends(get_api_key)])


@router.post(
    "/by_day",
    summary="Собрать данные о результатах исследований за ОДИН день",
    description="Отправляет запрос на API-шлюз с указанием даты дня, ответ обрабатывается и сохраняется в БД.",
    dependencies=[Depends(check_permission)]
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
    description="Отправляет запрос на API-шлюз с указанием периода, ответ обрабатывается и сохраняется в БД.",
    dependencies=[Depends(check_permission)]
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


@router.post(
    "/force-update",
    summary="Ручной запуск обновления [ОЧЕНЬ ЖЕЛАТЕЛЬНО ДЕЛАТЬ ПОСЛЕ загрузки dump!]",
    description="Запускает задачу обновления (LastDate - 1 -> Today) в фоне.",
    dependencies=[Depends(check_permission)]
)
@route_handle
async def force_update_now(request: Request):
    scheduler = request.app.state.scheduler

    # Добавляем задачу на исполнение ПРЯМО СЕЙЧАС
    scheduler.add_job(
        sync_database,
        'date',
        run_date=datetime.now(),
        args=[scheduler],  # Передаем scheduler для повторных попыток в случае неудачи
        id=f"manual_{datetime.now().timestamp()}"
    )

    return {"success": True, "message": "Задача запущена. Следите за Telegram."}


@router.post(
    "/dump",
    summary="Создать дамп базы данных",
    description="Запускает процесс pg_dump для создания резервной копии базы данных. Файл будет сохранен на сервере.",
    dependencies=[Depends(check_permission)]
)
@route_handle
async def create_db_dump():
    """
    Создает полную резервную копию базы данных в сжатом формате.
    """
    return await create_database_dump()

# отключаем на проде он на фиг не нужен
# @router.delete(
#     "/reset-database",
#     summary="Полностью сбросить базу данных",
#     description="!!! ОПАСНО !!! Удаляет ВСЕ таблицы из базы данных и создает их заново. Все данные будут потеряны.",
#     dependencies=[Depends(check_permission)]
# )
# @route_handle
# async def clear_db():
#     return await reset_entire_database()
