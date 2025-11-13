from sqlalchemy.ext.asyncio import AsyncSession
from app.model import TestResult
from app.core import logger
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException


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
            (rec.last_name, rec.first_name, rec.middle_name, rec.birthday, rec.test_date, rec.test_code,
             rec.result_hash): rec
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
                TestResult.last_name, TestResult.first_name, TestResult.middle_name,
                TestResult.birthday, TestResult.test_date, TestResult.test_code,
                TestResult.result_hash
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