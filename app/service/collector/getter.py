import asyncio
import httpx
from fastapi import HTTPException, status
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception

from app.core import logger
from app.service import GatewayService, fetch_test_result
from app.service.utils.utils import parse_html_test_result
from app.service.utils.telegram import send_telegram_message


def is_retryable_exception(exception) -> bool:
    """Возвращает True, если исключение - это ошибка, которую стоит повторить."""
    if isinstance(exception, (
            httpx.ReadError,
            httpx.ConnectError,
            httpx.ReadTimeout,
            httpx.ConnectTimeout,
            httpx.WriteTimeout,
            httpx.RemoteProtocolError,
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
    test_result_raw = ''
    result_id = item.get("result_id")
    if not result_id:
        raise ValueError(f"Не найден result_id для элемента: {item.get('service_name')}")

    MAX_EMPTY_RETRIES = 5
    RETRY_DELAY = 2.0
    html_content = None

    for attempt in range(1, MAX_EMPTY_RETRIES + 1):
        # Делаем запрос
        test_result_raw = await fetch_test_result(result_id, gateway_service)
        html_content = test_result_raw.get("html")

        if html_content:
            break

        # Если контента нет и это не последняя попытка - ждем
        if attempt < MAX_EMPTY_RETRIES:
            logger.warning(f"Пустой ответ для {result_id}. Ждем {RETRY_DELAY}с и пробуем снова ({attempt}/{MAX_EMPTY_RETRIES})")
            await asyncio.sleep(RETRY_DELAY)

    if html_content:
        item["test_result"] = await parse_html_test_result(html_content)
        item["is_result"] = True
    else:
        patient_name = f"{item.get('last_name')} {item.get('first_name')} {item.get('middle_name', '')}".strip()
        test_date = item.get('test_date')
        date_str = test_date.strftime('%d.%m.%Y') if test_date else "Неизвестная дата"
        test_name = item.get('test_name', 'Неизвестный анализ')
        # Шлем алерт в Телеграм
        msg = (
            f"Результаты исследований offline\n"
            f"⚠️ <b>Внимание: Пустой результат!</b>\n"
            f"👤 Пациент: {patient_name}\n"
            f"📅 Дата: {date_str}\n"
            f"🔬 Анализ: {test_name}\n"
            f"🆔 ID: {result_id}\n"
            f"ℹ️ <i>Попыток получения: {MAX_EMPTY_RETRIES}</i>"
        )
        await send_telegram_message(msg)

        logger.warning(f"Пустой результат: {item.get('last_name')} (ID: {result_id})")
        item["test_result"] = "Результат пуст"
        item["is_result"] = False

    item.pop("result_id")
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