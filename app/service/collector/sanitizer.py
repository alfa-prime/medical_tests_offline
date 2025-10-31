from app.core import logger


async def sanitize_period_data(data: list) -> list:
    response = []
    logger.info("Очистка и подготовка данных для дальнейшей обработки")
    for each in data:
        result_id = each.get("EvnXml_id", "")
        if result_id:
            record = {
                "prefix": each["prefix"],
                "last_name": each["Person_Surname"].capitalize(),
                "first_name": each["Person_Firname"].capitalize(),
                "middle_name": each["Person_Secname"].capitalize() if each["Person_Secname"] else "",
                "birthday": each["Person_Birthday"],
                "service_date": each["EvnUslugaPar_setDate"],
                "service_name": each["Usluga_Name"],
                "service_code": each["Usluga_Code"],
                "result_id": each["EvnXml_id"],
            }
            response.append(record)
    logger.info("Получение результатов исследований")
    return response