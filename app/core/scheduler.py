from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.logger_setup import logger
from app.service.scheduler.sync_database import sync_database

async def init_scheduler(app: FastAPI):
    """
    Инициализирует планировщик, сохраняет его в state приложения и запускает.
    """
    scheduler = AsyncIOScheduler()

    # --- ЗАДАЧА 1: Подготовка для Force-Update ---
    # Сохраняем в state, чтобы роут /service/force-update мог
    # достать планировщик и добавить задачу "прямо сейчас".
    app.state.scheduler = scheduler

    # --- ЗАДАЧА 2: Регистрация Daily-Update ---
    # Запускаем каждый день в 18:00 по МСК.
    # timezone='Europe/Moscow' позволяет игнорировать время контейнера (UTC).
    scheduler.add_job(
        sync_database,
        CronTrigger(hour=18, minute=0, timezone='Europe/Moscow'),
        args=[scheduler, 0],  # Передаем сам scheduler и счетчик попыток (0)
        id="daily_sync_task",
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler запущен. Ежедневная задача по сбору данных (18:00 MSK) запланирована.")


async def shutdown_scheduler(app: FastAPI):
    """
    Корректно останавливает планировщик при выключении приложения.
    """
    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown()
        logger.info("Scheduler остановлен.")