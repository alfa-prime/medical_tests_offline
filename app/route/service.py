from fastapi import APIRouter, Depends
from app.core.dependencies import check_permission, get_api_key
from app.service.dbase.clear_db import reset_entire_database
from app.service.dbase.dump_bd import create_database_dump
from app.core.decorator import route_handle

router = APIRouter(prefix="/service", tags=["Service functions"], dependencies=[Depends(get_api_key)])


@router.delete(
    "/reset-database",
    summary="Полностью сбросить базу данных",
    description="!!! ОПАСНО !!! Удаляет ВСЕ таблицы из базы данных и создает их заново. Все данные будут потеряны.",
    dependencies=[Depends(check_permission)]
)
@route_handle
async def clear_db():
    return await reset_entire_database()



@router.post(
    "/dump",
    summary="Создать дамп базы данных",
    description="Запускает процесс pg_dump для создания резервной копии базы данных. Файл будет сохранен на сервере.",
    dependencies=[Depends(check_permission)] # !!! ОБЯЗАТЕЛЬНО защищаем этот роут
)
@route_handle
async def create_db_dump():
    """
    Создает полную резервную копию базы данных в сжатом формате.
    """
    return await create_database_dump()
