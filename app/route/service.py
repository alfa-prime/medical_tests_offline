from datetime import datetime

from fastapi import APIRouter, Depends, Request
from app.core.dependencies import check_permission, get_api_key
from app.service.dbase.clear_db import reset_entire_database
from app.service.dbase.dump_bd import create_database_dump
from app.core.decorator import route_handle
from app.service.scheduler import sync_database

router = APIRouter(prefix="/service", tags=["Service functions"], dependencies=[Depends(get_api_key)])


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
    dependencies=[Depends(check_permission)]  # !!! ОБЯЗАТЕЛЬНО защищаем этот роут
)
@route_handle
async def create_db_dump():
    """
    Создает полную резервную копию базы данных в сжатом формате.
    """
    return await create_database_dump()


@router.delete(
    "/reset-database",
    summary="Полностью сбросить базу данных",
    description="!!! ОПАСНО !!! Удаляет ВСЕ таблицы из базы данных и создает их заново. Все данные будут потеряны.",
    dependencies=[Depends(check_permission)]
)
@route_handle
async def clear_db():
    return await reset_entire_database()
