import asyncio
from fastapi import HTTPException, status

from app.core import logger
from app.service import GatewayService, fetch_test_result
from app.service.utils.utils import parse_html_test_result


async def get_single_test_result(item: dict, gateway_service: GatewayService) -> dict:
    """
    Получает результат для ОДНОГО теста.
    Если происходит ошибка, выбрасывает исключение.
    """
    test_id = item.get("result_id")
    if not test_id:
        raise ValueError(f"Не найден result_id для элемента: {item.get('service_name')}")

    test_result_raw = await fetch_test_result(test_id, gateway_service)
    item.pop("result_id")

    html_content = test_result_raw.get("html")
    if html_content:
        item["result"] = await parse_html_test_result(html_content)
    else:
        item["result"] = "Результат пуст"


    return item


async def get_tests_results(src_data: list, gateway_service: GatewayService) -> list:
    if not src_data:
        return []

    total_records = len(src_data)
    logger.info(f"Начато получение {total_records} результатов.")

    tasks = [asyncio.create_task(get_single_test_result(item, gateway_service)) for item in src_data]

    try:
        # Используем gather, так как он проще для логики "Все или ничего".
        # Он сам отменит все при первой ошибке.
        results = await asyncio.gather(*tasks)
        logger.info("Все результаты исследований успешно получены.")
        return list(results)

    except Exception as e:
        # gather уже отменил остальные задачи, нам не нужно делать это вручную.
        # Теперь нам нужно просто правильно классифицировать ошибку.

        # Логируем исходную ошибку для себя
        logger.exception(f"Операция сбора данных прервана из-за ошибки: {e}")

        # Формируем правильный ответ для клиента
        if isinstance(e, ValueError):
            # Это ошибка в данных
            detail_message = f"Ошибка в данных: {e}"
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        elif isinstance(e, HTTPException):
            # Это ошибка от шлюза
            detail_message = "Не удалось получить все результаты: один из запросов к шлюзу не удался."
            status_code = status.HTTP_502_BAD_GATEWAY
        else:
            # Все остальное - наша внутренняя ошибка
            detail_message = "Произошла непредвиденная внутренняя ошибка при обработке исследований."
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        # И выбрасываем финальную, "чистую" ошибку
        raise HTTPException(status_code=status_code, detail=detail_message) from e