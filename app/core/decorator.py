import inspect
import json
from functools import wraps
from fastapi.responses import JSONResponse
from fastapi import status, HTTPException
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from app.core.logger_setup import logger
from app.core.config import get_settings

settings = get_settings()


def _truncate_for_log(data: any, max_length: int = 300) -> str:
    """
    Преобразует данные в строку (предпочтительно JSON) и обрезает их
    для безопасного логирования, добавляя маркер обрезки.
    """
    try:
        # --- ШАГ 2: ИСПОЛЬЗУЕМ jsonable_encoder ---
        # Сначала "подготавливаем" данные, превращая все сложные типы в JSON-совместимые
        json_compatible_data = jsonable_encoder(data)
        # И только потом передаем их в стандартный json.dumps
        data_str = json.dumps(json_compatible_data, ensure_ascii=False)

    except TypeError:
        data_str = f"<Несериализуемый объект типа {type(data).__name__}>"

    if len(data_str) > max_length:
        return data_str[:max_length] + "... [обрезано]"

    return data_str


def route_handle(func):
    """
    Декоратор для асинхронных роутов FastAPI, который:
    1. Отлавливает и логирует все необработанные исключения.
    2. Если включен DEBUG_MODE, логирует аргументы запроса и тело ответа.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        if settings.DEBUG_MODE:
            # Используем inspect, чтобы красиво сопоставить имена аргументов с их значениями
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            log_args = {}
            for name, value in bound_args.arguments.items():
                # Не логгируем 'self' или сложные объекты, которые не хотим видеть в логах
                if name in ['self', 'request'] or hasattr(value, '_client'):  # Пример фильтрации сервиса
                    log_args[name] = f"<Объект {type(value).__name__}>"
                elif isinstance(value, BaseModel):
                    log_args[name] = value.model_dump()  # Для Pydantic моделей выводим dict
                else:
                    log_args[name] = repr(value)  # repr() безопаснее str() для логирования
            logger.debug(f"Вызов роута '{func.__name__}'. Аргументы: {log_args}")

        try:
            response = await func(*args, **kwargs)

            if settings.DEBUG_MODE:
                truncated_response = _truncate_for_log(response, max_length=300)
                logger.debug(f"Роут '{func.__name__}' завершен. Ответ: {truncated_response}")
            return response

        except Exception as e:
            logger.exception(f"Ошибка в роуте '{func.__name__}': {e}")

            error_text = ""
            if isinstance(e, HTTPException):
                # Если это "чистая" ошибка FastAPI, берем ее детальное сообщение
                error_text = e.detail
            else:
                # Для всех остальных "грязных" ошибок берем их общее строковое представление
                error_text = str(e)

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": {
                        "text": error_text,
                        "type": "InternalServerError",
                        "message": "Произошла внутренняя ошибка на сервере. Пожалуйста, попробуйте позже."
                    }
                },
            )

    return wrapper
