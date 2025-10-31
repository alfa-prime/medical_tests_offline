from typing import Annotated, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import SQLModel
from pydantic import ValidationError
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_gateway_service, get_api_key, logger
from app.core.config import get_settings, Settings
from app.core.database import engine
from app.core.decorator import route_handle
from app.core.dependencies import get_session
from app.model import RequestPeriod, TestResult
from app.model.response import TestResultResponse
from app.service import GatewayService, fetch_period_data, sanitize_period_data, save_json, get_tests_results
from app.mapper.section import sections

router = APIRouter(prefix="/dbase", tags=["Work with dbase"], dependencies=[Depends(get_api_key)])


# --- ЗАЩИТНАЯ ЗАВИСИМОСТЬ ---
async def check_permission(settings: Annotated[Settings, Depends(get_settings)]):
    """
    Dependency, которая проверяет, разрешено ли использовать этот роут.
    Если нет, выбрасывает ошибку 404, чтобы скрыть его существование.
    """
    if not settings.ALLOW_DB_CLEAR_ENDPOINT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This endpoint is not available."
        )


@router.delete(
    "/reset-database",
    summary="Полностью сбросить базу данных",
    description="!!! ОПАСНО !!! Удаляет ВСЕ таблицы из базы данных и создает их заново. Все данные будут потеряны.",
    dependencies=[Depends(check_permission)]
)
async def reset_entire_database():
    try:
        logger.warning("Attempting to reset the entire database...")
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
            await conn.run_sync(SQLModel.metadata.create_all)

        message = "The entire database has been successfully reset."
        logger.info(message)
        return {"status": "ok", "message": message}
    except Exception as e:
        logger.error(f"Failed to reset the database: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not reset the database due to an error."
        )


# Вспомогательная функция для безопасного парсинга дат
def _parse_ru_date(date_str: Optional[str]) -> Optional[datetime.date]:
    """Преобразует строку формата 'ДД.ММ.ГГГГ' в объект date."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%d.%m.%Y').date()
    except (ValueError, TypeError):
        return None


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
        gateway_service: Annotated[GatewayService, Depends(get_gateway_service)],
        session: Annotated[AsyncSession, Depends(get_session)],
        settings: Annotated[Settings, Depends(get_settings)]
):
    raw_data_all = []
    for section_id, section_data in sections.items():
        logger.info(f"Начинаем сбор данных для '{section_data.prefix}'")
        raw_data = await fetch_period_data(period, section_id, gateway_service)
        raw_data = add_section_prefix(section_data.prefix, raw_data)
        raw_data_all += raw_data

    sanitize_data = await sanitize_period_data(raw_data_all)

    results = await get_tests_results(sanitize_data, gateway_service)

    # --- 2. ЛОГИКА СОХРАНЕНИЯ В БАЗУ ДАННЫХ (новая часть) ---
    if not results:
        logger.info("Нет данных для сохранения. Завершение работы.")
        return []

    # 2.1. Преобразуем словари в экземпляры модели для валидации и вставки
    validated_records = []
    for res_dict in results:

        res_dict['birthday'] = _parse_ru_date(res_dict.get('birthday'))
        res_dict['service_date'] = _parse_ru_date(res_dict.get('service_date'))

        try:
            validated_records.append(TestResult.model_validate(res_dict))
        except ValidationError as e:
            logger.warning(f"Пропуск записи из-за ошибки валидации: {res_dict}. Ошибка: {e}")
            continue

    # 2.2. Выполняем массовую вставку с обработкой конфликтов (UPSERT)
    if validated_records:
        try:
            # Преобразуем объекты модели обратно в словари для функции insert()
            insert_dicts = [r.model_dump(exclude_unset=True) for r in validated_records]

            # Создаем инструкцию INSERT ... ON CONFLICT DO NOTHING
            stmt = insert(TestResult).values(insert_dicts)
            stmt = stmt.on_conflict_do_nothing(
                constraint="uq_patient_service"  # Имя уникального ограничения
            )

            await session.execute(stmt)
            await session.commit()
            logger.info(f"Операция сохранения в БД завершена. Обработано {len(insert_dicts)} записей.")
        except Exception as e:
            await session.rollback()
            logger.error(f"Критическая ошибка при сохранении данных в БД: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Database save operation failed.")
    else:
        logger.info("После валидации не осталось записей для сохранения в БД.")

    if settings.DEBUG_MODE:
        save_json("01. raw.json", raw_data_all)
        save_json("02. sanitize.json", sanitize_data)
        save_json("03. results.json", results)

    return validated_records
