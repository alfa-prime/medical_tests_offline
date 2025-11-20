import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import HTTPException

from app.core.config import get_settings
from app.core.logger_setup import logger

settings = get_settings()

async def create_database_dump(filename: Optional[str] = None) -> dict:
    """
    Создает дамп базы данных с помощью pg_dump и сохраняет его в файл.
    Возвращает путь к файлу в случае успеха.
    """
    dump_folder = Path(settings.OUTPUT_FOLDER) / "dumps"
    dump_folder.mkdir(parents=True, exist_ok=True)

    if filename:
        dump_filename = filename
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dump_filename = f"dump_{timestamp}.dump"

    dump_filepath = dump_folder / dump_filename

    #  Формируем команду для pg_dump
    # Важно: пароль передаем через переменную окружения PGPASSWORD
    # для безопасности, чтобы он не отображался в процессах системы.
    pg_dump_command = [
        "pg_dump",
        "-U", settings.POSTGRES_USER,
        "-h", settings.POSTGRES_HOST,
        "-p", str(settings.POSTGRES_PORT),
        "--dbname", settings.POSTGRES_DB,
        "--no-password", # Явно говорим не запрашивать пароль
        "-F", "c", # Формат custom, хорошо сжимается и подходит для pg_restore
        "-b", # Включать большие объекты (blobs)
        "-v", # Verbose режим для логов
        "-f", str(dump_filepath) # Указываем выходной файл
    ]

    # Создаем окружение для подпроцесса, включая пароль
    env = os.environ.copy()
    # Если используете Pydantic SecretStr, .get_secret_value() вернет строку
    env["PGPASSWORD"] = settings.POSTGRES_PASSWORD

    logger.info(f"Начинаем создание дампа базы данных в файл: {dump_filepath}")

    # Асинхронно запускаем команду
    process = await asyncio.create_subprocess_exec(
        *pg_dump_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env
    )

    # Ожидаем завершения процесса
    stdout, stderr = await process.communicate()

    # Проверяем результат
    if process.returncode == 0:
        logger.info(f"Дамп базы данных успешно создан. Файл: {dump_filepath}")
        return {
            "success": True,
            "message": "Дамп базы данных успешно создан.",
            "file_path": str(dump_filepath)
        }
    else:
        # Если pg_dump завершился с ошибкой
        error_message = stderr.decode('utf-8').strip()
        logger.error(f"Ошибка при создании дампа БД: {error_message}")
        raise HTTPException(
            status_code=500,
            detail=f"Не удалось создать дамп базы данных: {error_message}"
        )