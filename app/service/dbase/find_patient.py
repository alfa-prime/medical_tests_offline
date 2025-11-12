from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.model import TestResult, RequestByPatient
from app.core.logger_setup import logger


async def find_records_by_patient(
        patient_data: RequestByPatient,
        session: AsyncSession
) -> Sequence[TestResult]:
    """
    Выполняет поиск всех записей в таблице test_results по данным пациента.
    Возвращает список найденных записей.
    """
    logger.info(
        f"Выполняется поиск по пациенту: "
        f"{patient_data.last_name} {patient_data.first_name}, ДР: {patient_data.birthday}"
    )

    statement = select(TestResult).where(
        TestResult.last_name == patient_data.last_name,
        TestResult.first_name == patient_data.first_name,
        TestResult.birthday == patient_data.birthday
    )

    if patient_data.middle_name is not None:
        statement = statement.where(TestResult.middle_name == patient_data.middle_name)
    else:
        statement = statement.where(TestResult.middle_name == "")

    results = await session.exec(statement)
    found_records = results.all()

    logger.info(f"Найдено записей: {len(found_records)}")

    return found_records
