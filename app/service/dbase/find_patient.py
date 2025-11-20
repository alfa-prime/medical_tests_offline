import datetime
from typing import Sequence
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc

from app.model import TestResult, RequestByPatient
from app.core.logger_setup import logger

CATEGORY_MAP = {
    "tests": "medtests",
    "ultra_sound": "ultrasound_scan",
    "x-ray": "x_ray",
    "functional": "functional_tests",
    "ct_scan": "ct_scan",
    "endoscopy": "endoscopy"
}


def _calculate_age(birth_date: datetime.date) -> int:
    """Вычисляет возраст на основе даты рождения."""
    today = datetime.date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age


def _process_category_data(tests: Sequence['TestResult']) -> dict[str, any]:
    """Обрабатывает список тестов для одной категории."""
    if not tests:
        return {
            "tests_total": 0,
            "tests_dates": [],
            "tests_dates_latest": None,
            "tests_with_results": {}
        }

    tests_by_date = defaultdict(list)
    for test in tests:
        test_info = {
            "test_id": test.test_id,
            "service": test.service,
            "analyzer_name": test.analyzer_name,
            "test_code": test.test_code,
            "test_name": test.test_name,
            "test_result": test.test_result,
        }
        tests_by_date[test.test_date.isoformat()].append(test_info)

    sorted_dates = sorted(tests_by_date.keys(), reverse=True)

    return {
        "tests_total": len(tests),
        "tests_dates": sorted_dates,
        "tests_dates_latest": sorted_dates[0] if sorted_dates else None,
        "tests_with_results": dict(tests_by_date)
    }


async def find_records_by_patient(
        patient_data: RequestByPatient,
        session: AsyncSession
) -> Sequence[TestResult]:
    """
    Выполняет поиск всех записей в таблице test_results по данным пациента.
    Возвращает список найденных записей.
    """
    target_birthday = datetime.datetime.strptime(patient_data.birthday, '%d.%m.%Y').date()

    logger.info(
        f"Выполняется поиск по пациенту: "
        f"{patient_data.last_name} {patient_data.first_name}, ДР: {target_birthday}"
    )

    statement = select(TestResult).where(
        TestResult.last_name == patient_data.last_name,
        TestResult.first_name == patient_data.first_name,
        TestResult.birthday == target_birthday
    ).order_by(desc(TestResult.test_date))

    if patient_data.middle_name is not None:
        statement = statement.where(TestResult.middle_name == patient_data.middle_name)
    else:
        statement = statement.where(TestResult.middle_name == "")

    results = await session.exec(statement)
    found_records = results.all()

    if not found_records:
        return {"success": True, "result": {}}

    # Извлекаем информацию о пациенте
    first_record = found_records[0]
    person_info = {
        "person_id": first_record.person_id,
        "last_name": first_record.last_name,
        "first_name": first_record.first_name,
        "middle_name": first_record.middle_name,
        "birthday": first_record.birthday.strftime('%d.%m.%Y'),
        "age": str(_calculate_age(first_record.birthday))
    }

    # Разделяем все тесты по категориям, используя поле 'prefix'
    categorized_tests = defaultdict(list)
    for record in found_records:
        category_key = CATEGORY_MAP.get(record.prefix, "unknown")
        categorized_tests[category_key].append(record)

    # Обрабатываем каждую категорию
    processed_categories = {}
    for category_name, tests_in_category in categorized_tests.items():
        processed_categories[category_name] = _process_category_data(tests_in_category)

    # Собираем финальный ответ
    final_result = {
        "success": True,
        "result": {
            "person": person_info,
            **processed_categories
        }
    }

    logger.info(f"Найдено записей: {len(found_records)}")

    return final_result
