from app.core import logger, get_settings
from app.service import GatewayService

settings = get_settings()

async def fetch_period_data(
        period: str,
        department_id: str,
        gateway_service: GatewayService
) -> list:
    paginator_limit = settings.REQUEST_PAGINATOR_LIMIT
    all_records = []
    start = 0
    page_number = 1

    while True:
        logger.debug(f"Запрашиваем страницу №{page_number} (смещение: {start})...")

        payload = {
            "params": {"c": "Search", "m": "searchData"},
            "data": {
                "PersonPeriodicType_id": 1,
                "SearchFormType": "EvnUslugaPar",
                "EvnUslugaPar_setDate_Range": period,
                "SearchType_id": 1,
                "Part_of_the_study": "false",
                "PersonCardStateType_id": 1,
                "PrivilegeStateType_id": 1,
                "limit": paginator_limit,
                "start": start,
                "LpuSection_uid": department_id
            }
        }

        response_json = await gateway_service.make_request(method="post", json=payload)
        current_page_results = response_json.get("data", [])

        # Если текущая страница пуста, значит, данные закончились.
        if not current_page_results:
            logger.debug("Получена пустая страница, завершаем сбор.")
            break

        # Добавляем полученные результаты в общий список
        all_records.extend(current_page_results)
        logger.debug(f"Получено {len(current_page_results)} записей. Всего собрано: {len(all_records)}.")

        # Если API вернуло меньше записей, чем мы просили, это была последняя страница.
        if len(current_page_results) < paginator_limit:
            logger.debug("Это была последняя страница, завершаем сбор.")
            break

        start += paginator_limit
        page_number += 1

    logger.info(f"Сбор данных завершен. Итоговое количество записей: {len(all_records)}.")
    return all_records


async def fetch_test_result(result_id: str, gateway_service: GatewayService) -> dict:
    # Получает результат исследований по id
    payload = {
        "params": {"c": "EvnXml", "m": "doLoadData"},
        "data": {"EvnXml_id": result_id}
    }

    response = await gateway_service.make_request(method="post", json=payload)
    logger.critical(response)
    return response
