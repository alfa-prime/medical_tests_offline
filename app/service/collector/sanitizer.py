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
                "prefix": each["prefix"],
                "last_name": each["Person_Surname"].capitalize(),
                "first_name": each["Person_Firname"].capitalize(),
                "middle_name": each["Person_Secname"].capitalize() if each["Person_Secname"] else "",
                "birthday": _sanitize_date(each["Person_Birthday"]),
                "service_date": _sanitize_date(each["EvnUslugaPar_setDate"]),
                "service_name": each["Usluga_Name"],
                "service_code": each["Usluga_Code"],
                "result_id": result_id,
            }
            response.append(record)
    logger.info("Получение результатов исследований")
    return response
