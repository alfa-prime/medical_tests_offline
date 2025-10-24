import asyncio
from app.core import logger
from app.service import GatewayService, fetch_test_result
from app.service.utils.utils import parse_html_test_result


async def get_single_test_result(item: dict, gateway_service: GatewayService):
    """
    Безопасно получает результат для одного теста.
    Возвращает исходный item, дополненный результатом или сообщением об ошибке.
    """
    test_id = item.get("result_id")
    if not test_id:
        logger.warning(f"Не найден result_id для элемента: {item.get('service_name')}")
        return item

    try:
        test_result_raw = await fetch_test_result(test_id, gateway_service)
        html_content = test_result_raw.get("html")
        if html_content:
            pure_html = await parse_html_test_result(html_content)
            item["result"] = pure_html
        else:
            item["result"] = "Результат пуст"
        return item
    except Exception as e:
        logger.error(f"Не удалось получить результат для test_id {test_id}: {e}")
        item["result"] = f"Ошибка при получении данных: {e}"
        return item


async def get_tests_results(src_data: list, gateway_service: GatewayService) -> list:
    if not src_data:
        return []

    total_records = len(src_data)
    logger.info(f"Начато получение результатов для {total_records} исследований.")

    tasks = [get_single_test_result(item, gateway_service) for item in src_data]

    processed_count = 0
    results = []
    log_interval = max(1, total_records // 10)

    # asyncio.as_completed() возвращает задачи по мере их завершения
    for future in asyncio.as_completed(tasks):
        # Ожидаем завершения очередной задачи
        result_item = await future
        results.append(result_item)

        processed_count += 1
        if processed_count % log_interval == 0 or processed_count == total_records:
            logger.info(f"Обработано: {processed_count}/{total_records} ({processed_count / total_records:.0%})")

    logger.info("Все результаты исследований получены.")

    return results