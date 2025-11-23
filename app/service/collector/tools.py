from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from sqlmodel import select, func
import time

from app.model import TestResult
from app.core import logger

async def process_and_save_in_batches(
        validated_records: list[TestResult],
        session: AsyncSession,
        batch_size: int = 1000
)-> dict[str, any]:
    """
    Принимает список ВАЛИДИРОВАННЫХ моделей TestResult и сохраняет их в БД пакетами,
    пропуская дубликаты на основе уникального индекса 'uq_patient_service'.
    """
    if not validated_records:
        return {"inserted": 0, "skipped": []}

    total_inserted = 0
    all_skipped_records = []
    total_to_insert = len(validated_records)
    logger.info(f"Начало сохранения {total_to_insert} записей в БД пакетами по {batch_size}.")

    for i in range(0, total_to_insert, batch_size):
        batch = validated_records[i:i + batch_size]

        key_to_record_map = {
            (rec.test_id, rec.last_name, rec.first_name, rec.middle_name, rec.birthday, rec.test_date,
             rec.test_code): rec
            for rec in batch
        }
        attempted_keys = set(key_to_record_map.keys())

        # Преобразуем экземпляры моделей в словари прямо перед вставкой
        records_to_insert = [rec.model_dump(exclude={'id', 'created_at'}) for rec in batch]

        if not records_to_insert:
            continue

        try:
            statement = insert(TestResult).values(records_to_insert)

            # Правильно ссылаемся на уникальный ИНДЕКС через index_elements
            statement = statement.on_conflict_do_nothing(
                constraint='uq_patient_service_hash'
            )

            statement = statement.returning(
                TestResult.test_id, TestResult.last_name, TestResult.first_name, TestResult.middle_name,
                TestResult.birthday, TestResult.test_date, TestResult.test_code
            )

            result_proxy = await session.execute(statement)
            inserted_rows = result_proxy.all()
            total_inserted += len(inserted_rows)

            inserted_keys = {tuple(row) for row in inserted_rows}
            skipped_keys = attempted_keys - inserted_keys # noqa

            if skipped_keys:
                batch_skipped = [key_to_record_map[key] for key in skipped_keys]
                all_skipped_records.extend(batch_skipped)

            logger.info(
                f"Обработан пакет {i // batch_size + 1}. Попытка: {len(batch)}. Вставлено новых: {len(inserted_rows)}.")

        except (IntegrityError, Exception) as e:
            # Откатываем транзакцию в случае любой ошибки в любом из пакетов
            await session.rollback()
            logger.error(f"Критическая ошибка при сохранении пакета: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Ошибка при пакетной записи в БД.")

    return {"inserted": total_inserted, "skipped": all_skipped_records}


async def full_audit_dbase(session: AsyncSession, batch_size: int = 1000) -> dict:
    """
    Выполняет полный аудит базы данных на предмет целостности зашифрованных данных.
    Проверяет записи с is_result=True на:
    1. None
    2. Короткую длину (< 5 символов)
    3. Наличие фразы-заглушки "Результат пуст" (которая могла попасть туда по ошибке с флагом True)
    """
    start_time = time.time()
    logger.info(f"🚀 ЗАПУСК ПОЛНОГО АУДИТА (Service Layer). Размер пачки: {batch_size}")

    # 1. Считаем общее количество
    total_query = select(func.count()).where(TestResult.is_result == True)
    total_count = (await session.exec(total_query)).one()

    suspicious_records = []
    offset = 0
    processed = 0

    while True:
        # 2. Читаем пачками
        statement = (
            select(TestResult)
            .where(TestResult.is_result == True)
            .order_by(TestResult.id)
            .offset(offset)
            .limit(batch_size)
        )
        result = await session.exec(statement)
        batch = result.all()

        if not batch:
            break

        # 3. Анализируем
        for rec in batch:
            # Расшифровка происходит при обращении к атрибуту
            content = rec.test_result
            content_str = str(content).strip() if content else ""

            problem = None

            if content is None:
                problem = "Content is None"
            elif len(content_str) < 5:
                problem = f"Too short content: '{content_str}'"
            elif content_str == "Результат пуст":
                problem = "Phrase 'Результат пуст' found in Valid record"

            if problem:
                suspicious_records.append({
                    "id": rec.id,
                    "test_id": rec.test_id,
                    "date": rec.test_date.strftime('%d.%m.%Y'),
                    "patient": f"{rec.last_name} {rec.first_name}",
                    "problem": problem
                })

        processed += len(batch)
        offset += batch_size

        # Логируем прогресс
        if processed % 5000 == 0:
            logger.info(f"Проверено {processed} / {total_count}...")

    duration = time.time() - start_time

    # 4. Формируем итог и логируем его здесь же
    if not suspicious_records:
        msg = f"✅ АУДИТ ЗАВЕРШЕН. База идеально чиста. Проверено {processed} записей за {duration:.2f} сек."
        logger.info(msg)
        return {"status": "OK", "message": msg}

    # Если есть проблемы
    msg = (
        f"⚠️ АУДИТ ЗАВЕРШЕН С ОШИБКАМИ. "
        f"Найдено битых записей: {len(suspicious_records)}. "
        f"Время: {duration:.2f} сек."
    )
    logger.warning(msg)

    return {
        "status": "FAIL",
        "message": msg,
        "total_checked": processed,
        "bad_records_count": len(suspicious_records),
        "bad_records_sample": suspicious_records[:100]  # Возвращаем только первые 100, чтобы не забить канал
    }