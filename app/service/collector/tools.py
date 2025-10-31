from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError
from sqlalchemy.dialects.postgresql import insert
from fastapi import HTTPException

from app.model import TestResult
from app.core import logger


async def process_and_save_in_batches(
        results: list,
        session: AsyncSession,
        batch_size: int = 1000
):
    total_processed = 0
    total_newly_saved = 0  # Переименовали для ясности

    for i in range(0, len(results), batch_size):
        batch_dicts = results[i:i + batch_size]

        validated_records = []
        for res_dict in batch_dicts:
            try:
                validated_records.append(TestResult.model_validate(res_dict))
            except ValidationError as e:
                logger.warning(f"Пропуск записи из-за ошибки валидации: {res_dict}. Ошибка: {e}")
                continue

        if not validated_records:
            continue

        try:
            insert_dicts = [r.model_dump(exclude={'id', 'created_at'}) for r in validated_records]

            stmt = insert(TestResult).values(insert_dicts)
            stmt = stmt.on_conflict_do_nothing(
                constraint="uq_patient_service"
            )

            # Добавляем RETURNING id, чтобы запрос вернул ID вставленных строк
            stmt = stmt.returning(TestResult.id)

            result_proxy = await session.execute(stmt)

            # Считаем, сколько строк нам вернулось
            inserted_count = len(result_proxy.all())

            total_processed += len(batch_dicts)
            total_newly_saved += inserted_count

            logger.info(
                f"Обработан пакет {i // batch_size + 1}. "
                f"Обработано записей: {total_processed}/{len(results)}. "
                f"Сохранено новых: {total_newly_saved}"
            )

        except Exception as e:
            await session.rollback()
            logger.error(f"Критическая ошибка при сохранении пакета: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Database save operation failed on a batch.")

    await session.commit()
    logger.info(
        f"Операция сохранения в БД завершена. "
        f"Всего обработано: {total_processed}. "
        f"Всего сохранено новых: {total_newly_saved}."
    )
