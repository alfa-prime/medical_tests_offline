from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib

from app.model import TestResult
from app.service import GatewayService, fetch_period_data, sanitize_data, get_tests_results
from app.service.collector.tools import process_and_save_in_batches
from app.core.logger_setup import logger
from app.model.department import DEPARTMENTS
from app.service.utils.utils import date_generator, save_json


def _add_prefix(session_prefix: str, data: list[dict]) -> list[dict]:
    """Добавляет к записи префикс отделения"""
    for each in data:
        each.update({"prefix": session_prefix})
    return data


def _add_result_hash(data: list[dict]):
    """
    Добавляет md5-хэш для поля results, это нужно для построения уникального индекса,
    при вставке данных БД для избежания дубликатов
    (так как postgres не справляется с объемом поля results при построении индекса)
    """
    for each in data:
        result_text = each.get("result")
        each["result_hash"] = hashlib.md5(result_text.encode('utf-8')).hexdigest()
    return data


def _validate_records(records_as_dicts: list[dict[str, any]]) -> list[TestResult]:
    """
    Принимает список словарей, проверяет каждый из них с помощью модели TestResult.
    - Пропускает невалидные записи и логирует ошибки.
    - Возвращает список валидных экземпляров модели TestResult.
    """
    if not records_as_dicts:
        return []

    logger.info(f"Начата валидация {len(records_as_dicts)} записей.")
    validated_records = []

    for record_dict in records_as_dicts:
        try:
            validated_model = TestResult.model_validate(record_dict)
            validated_records.append(validated_model)
        except ValidationError as e:
            logger.warning(
                f"Пропуск записи из-за ошибки валидации. "
                f"Данные: {record_dict}. Ошибка: {e}"
            )
            continue

    logger.info(
        f"Валидация завершена. "
        f"Успешно: {len(validated_records)}. "
        f"Отброшено: {len(records_as_dicts) - len(validated_records)}."
    )

    return validated_records


async def _collect_and_process_data(
        periods: list[str],
        gateway_service: GatewayService,
        session: AsyncSession
) -> dict:
    """
    Собирает данные за список периодов, обрабатывает и сохраняет в БД.
    """
    gateway_response = []

    for day in periods:
        period = f"{day} - {day}"
        for department in DEPARTMENTS:
            logger.info(f"Период '{period}': собираю данные для '{department.prefix}'")
            data_raw = await fetch_period_data(period, department.id, gateway_service)

            if data_raw:
                data_prefix = _add_prefix(department.prefix, data_raw)
                data_sanitized = sanitize_data(data_prefix)
                data_with_test_results = await get_tests_results(data_sanitized, gateway_service)
                data_with_result_hash = _add_result_hash(data_with_test_results)
                gateway_response.extend(data_with_result_hash)

    if not gateway_response:
        logger.info("Нет данных для сохранения по указанным периодам. Завершение работы.")
        return {"success": True, "message": "No data found to process"}

    validated_records = _validate_records(gateway_response)

    if not validated_records:
        logger.info("Нет валидных данных для сохранения после фильтрации.")
        return {"success": True, "message": "No valid data to save"}

    logger.info(f"Передача {len(validated_records)} проверенных записей для сохранения в БД.")
    save_report = await process_and_save_in_batches(validated_records, session)

    await session.commit()
    logger.info("Транзакция успешно зафиксирована.")

    inserted_count = save_report.get("inserted", 0)
    skipped_records = save_report.get("skipped", [])

    logger.info(f"Операция завершена. Вставлено новых: {inserted_count}. Пропущено дубликатов: {len(skipped_records)}.")

    if skipped_records:
        records_for_json = []
        for rec in skipped_records:
            rec_dict = rec.model_dump(mode='json')
            # Убираем ненужные поля
            for key in ['prefix', 'id', 'result_hash', 'result', 'created_at']:
                rec_dict.pop(key, None)
            records_for_json.append(rec_dict)

        try:
            save_json(filename="skipped_duplicates.json", data=records_for_json)
            logger.info(f"Отчет о {len(skipped_records)} пропущенных записях сохранен.")
        except Exception as e:
            logger.error(f"Не удалось сохранить JSON с пропущенными записями: {e}")

    return {
        "success": True,
        "message": f"Операция завершена. Вставлено новых: {inserted_count}. Пропущено дубликатов: {len(skipped_records)}."
    }


async def collect_by_day(period: str, gateway_service: GatewayService, session: AsyncSession):
    """
    Собирает и сохраняет данные за один указанный день.
    """
    try:
        periods = [period]
        return await _collect_and_process_data(periods, gateway_service, session)

    except Exception as e:
        logger.error(f"Операция сбора за день '{period}' прервана: {e}", exc_info=True)
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail="Произошла непредвиденная ошибка на сервере.")


async def collect_by_month(year: int, month: int, gateway_service: GatewayService, session: AsyncSession):
    """
    Собирает и сохраняет данные за весь указанный месяц.
    """
    try:
        # Генерируем список периодов (дней) для всего месяца
        days_in_month = date_generator(year, month)
        periods = [day.strftime("%d.%m.%Y") for day in days_in_month]
        return await _collect_and_process_data(periods, gateway_service, session)

    except Exception as e:
        logger.error(f"Операция сбора за месяц '{month}-{year}' прервана: {e}", exc_info=True)
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail="Произошла непредвиденная ошибка на сервере.")
