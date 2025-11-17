from datetime import datetime
from typing import Optional, Any

from app.core import logger


def _sanitize_date(date_str: Optional[str]) -> Optional[datetime.date]:
    """Преобразует строку формата 'ДД.ММ.ГГГГ' в объект date."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%d.%m.%Y').date()
    except (ValueError, TypeError):
        return None


def sanitize_data(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    response = []
    logger.info("Очистка и подготовка данных для дальнейшей обработки")
    for each in data:
        # отфильтровываем записи без результатов исследований
        result_id = each.get("EvnXml_id", None)
        if result_id:
            record = {
                "person_id": each["Person_id"],
                "last_name": each["Person_Surname"].capitalize(),
                "first_name": each["Person_Firname"].capitalize(),
                "middle_name": each["Person_Secname"].capitalize() if each["Person_Secname"] else "",
                "birthday": _sanitize_date(each["Person_Birthday"]),
                "test_id": each["EvnUslugaPar_id"],
                "prefix": each["prefix"],
                "service": each["MedService_Name"],
                "analyzer_name": each["Resource_Name"],
                "test_date": _sanitize_date(each["EvnUslugaPar_setDate"]),
                "test_name": each["Usluga_Name"],
                "test_code": each["Usluga_Code"],
                "result_id": result_id,
            }
            response.append(record)
    logger.info("Получение результатов исследований")
    return response
