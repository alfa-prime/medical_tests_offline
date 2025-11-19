from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.logger_setup import logger


async def init_scheduler(app: FastAPI):
    """
    Инициализирует планировщик, сохраняет его в state приложения и запускает.
    """
    scheduler = AsyncIOScheduler()

    # Сохраняем в state, чтобы потом доставать через request.app.state.scheduler
    app.state.scheduler = scheduler

    scheduler.start()
    logger.info("Scheduler инициализирован и запущен.")


async def shutdown_scheduler(app: FastAPI):
    """
    Корректно останавливает планировщик при выключении приложения.
    """
    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown()
        logger.info("Scheduler остановлен.")