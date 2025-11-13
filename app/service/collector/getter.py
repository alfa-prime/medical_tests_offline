import asyncio
import httpx
from fastapi import HTTPException, status
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception

from app.core import logger
from app.service import GatewayService, fetch_test_result
from app.service.utils.utils import parse_html_test_result



def is_retryable_exception(exception) -> bool:
    """Возвращает True, если исключение - это ошибка, которую стоит повторить."""
    if isinstance(exception, (
            httpx.ReadError,
            httpx.ConnectError,
            httpx.ReadTimeout,
            httpx.ConnectTimeout,
            httpx.WriteTimeout
    )):
        return True

    if isinstance(exception, HTTPException) and 500 <= exception.status_code < 600:
        return True
    return False


@retry(
    stop=stop_after_attempt(5),  # Остановиться после 5 попыток (1 первая + 4 повторных)
    wait=wait_fixed(2),  # Ждать 2 секунды между попытками
    retry=retry_if_exception(is_retryable_exception), # noqa
    before_sleep=lambda retry_state: logger.warning(
        f"Повторная попытка {retry_state.attempt_number}/5 для запроса "
        f"из-за ошибки: {retry_state.outcome.exception()}"
    )
)
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
        item["test_result"] = await parse_html_test_result(html_content)
    else:
        item["test_result"] = "Результат пуст"

    return item


async def get_tests_results(src_data: list, gateway_service: GatewayService) -> list:
    if not src_data:
        return []

    total_records = len(src_data)

    # Устанавливаем лимит одновременных задач.
    # Он должен быть РАВЕН или МЕНЬШЕ лимита в httpx.
    CONCURRENCY_LIMIT = 30 # noqa
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    logger.info(
        f"Начато получение {total_records} результатов. "
        f"Лимит одновременных запросов: {CONCURRENCY_LIMIT}."
    )

    # Создаем "обертку", которая будет использовать семафор.
    # Она принимает задачу (get_single_test_result) и ее аргументы.
    async def run_with_semaphore(coro, *args):
        async with semaphore:
            return await coro(*args)

    tasks = [
        asyncio.create_task(
            run_with_semaphore(get_single_test_result, item, gateway_service)
        )
        for item in src_data
    ]

    try:
        results = await asyncio.gather(*tasks)
        logger.info("Все результаты исследований успешно получены.")
        return list(results)

    except Exception as e:
        logger.exception(f"Операция сбора данных прервана из-за ошибки: {e}")

        if isinstance(e, ValueError):
            detail_message = f"Ошибка в данных: {e}"
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        elif isinstance(e, HTTPException):
            detail_message = "Не удалось получить все результаты: один из запросов к шлюзу не удался."
            status_code = status.HTTP_502_BAD_GATEWAY
        else:
            detail_message = "Произошла непредвиденная внутренняя ошибка при обработке исследований."
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        raise HTTPException(status_code=status_code, detail=detail_message) from e