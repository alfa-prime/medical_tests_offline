from fastapi import APIRouter, Depends
from app.core.dependencies import check_permission, get_api_key
from app.service.dbase.clear_db import reset_entire_database

router = APIRouter(prefix="/service", tags=["Service functions"], dependencies=[Depends(get_api_key)])


@router.delete(
    "/reset-database",
    summary="Полностью сбросить базу данных",
    description="!!! ОПАСНО !!! Удаляет ВСЕ таблицы из базы данных и создает их заново. Все данные будут потеряны.",
    dependencies=[Depends(check_permission)]
)
async def clear_db():
    return await reset_entire_database()
