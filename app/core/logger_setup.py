import logging
import sys
from pathlib import Path
from loguru import logger


def configure_logger(log_level: str = "INFO"):
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Очистка стандартных хендлеров logging
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).propagate = False

    # Настройка loguru
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{message}</cyan>",
        level=log_level,
        colorize=True,
    )

    # === Оборачиваем в try-except ===
    try:
        logger.add(
            "logs/app.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            level="INFO",
            rotation="10 MB",
            retention="14 days",
            compression="zip",
        )
        logger.add(
            "logs/errors.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            level="ERROR",
            rotation="5 MB",
            retention="10 days",
            compression="zip",
        )
    except Exception as e:
        print(f"Не удалось настроить файловые логи: {e}")

    # Перехват логов FastAPI
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            level = record.levelname if logger.level(record.levelname) is not None else "INFO"
            logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())

    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).handlers = [InterceptHandler()]


from .config import get_settings

settings = get_settings()
configure_logger(settings.LOGS_LEVEL)