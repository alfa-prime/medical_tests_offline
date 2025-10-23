from app.core import logger

DEPARTMENTS = {
    "Отделение функциональной диагностики ММЦ": "functional",
    "Клинико-диагностическая лаборатория ММЦ": "medtest",
    "Отделение ультразвуковой диагностики стационар ММЦ": "ultra_sound",
    "Рентгеновское отделение ММЦ": "x_ray"
}



async def sanitize_period_data(data: list) -> list:
    response = []
    logger.info("Очистка и подготовка данных для дальнейшей обработки")
    for each in data:
        department = each.get("LpuSection_Name")
        department_prefix = DEPARTMENTS.get(department)
        if department in DEPARTMENTS:
            response.append({
                "last_name": each["Person_Surname"].capitalize(),
                "first_name": each["Person_Firname"].capitalize(),
                "middle_name": each["Person_Secname"].capitalize(),
                "birthday": each["Person_Birthday"],
                "service_date": each["EvnUslugaPar_setDate"],
                "service_name": each["Usluga_Name"],
                "service_code": each["Usluga_Code"],
                "department_prefix": department_prefix,
                "result_id": each["EvnXml_id"],
            })
    logger.info("Получение результатов исследований")
    return response