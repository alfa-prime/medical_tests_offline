from app.core import logger, get_settings
from app.model import RequestPeriod
from app.service import GatewayService

settings = get_settings()

async def fetch_period_data(
        dates: RequestPeriod,
        section_id: str,
        gateway_service: GatewayService
) -> list:
    # Получает список исследований за период
    paginator_limit = settings.REQUEST_PAGINATOR_LIMIT
    all_records = []
    start = 0
    page_number = 1

    logger.info(
        f"Начат сбор всех данных для LpuSection_uid='{section_id}' "
        f"за период {dates.date_range} (размер страницы: {paginator_limit})."
    )

    while True:
        logger.info(f"Запрашиваем страницу №{page_number} (смещение: {start})...")

        payload = {
            "headers": {
                "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 YaBrowser/25.6.0.0 Safari/537.36"},
            "params": {"c": "Search", "m": "searchData"},
            "data": {
                "PersonPeriodicType_id": 1,
                "SearchFormType": "EvnUslugaPar",
                "EvnUslugaPar_setDate_Range": dates.date_range,
                "SearchType_id": 1,
                "Part_of_the_study": "false",
                "PersonCardStateType_id": 1,
                "PrivilegeStateType_id": 1,
                "limit": paginator_limit,
                "start": start,
                "LpuSection_uid": section_id
            }
        }

        response_json = await gateway_service.make_request(method="post", json=payload)
        current_page_results = response_json.get("data", [])

        # Если текущая страница пуста, значит, данные закончились.
        if not current_page_results:
            logger.info("Получена пустая страница, завершаем сбор.")
            break

        # Добавляем полученные результаты в общий список
        all_records.extend(current_page_results)
        logger.info(f"Получено {len(current_page_results)} записей. Всего собрано: {len(all_records)}.")

        # Если API вернуло меньше записей, чем мы просили, это была последняя страница.
        if len(current_page_results) < paginator_limit:
            logger.info("Это была последняя страница, завершаем сбор.")
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
    return response
