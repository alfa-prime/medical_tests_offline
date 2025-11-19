import datetime
import asyncio
import httpx
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core import logger, get_settings
from app.core.database import engine
from app.model import TestResult
from app.service import GatewayService
from app.service.collector.process import collect_by_day
from app.service.utils.telegram import send_telegram_message

settings = get_settings()


async def sync_database(scheduler, retry_count: int = 0):
    """
    Логика обновления: Last Date - 1 Day -> Today.
    """
    logger.info(f"🔄 [ManualUpdate] Старт задачи. Попытка #{retry_count + 1}")

    async with AsyncSession(engine) as session:
        # Создаем чистый клиент
        limits = httpx.Limits(max_connections=10)
        async with httpx.AsyncClient(
                base_url=settings.GATEWAY_URL,
                headers={"X-API-KEY": settings.GATEWAY_API_KEY},
                timeout=settings.REQUEST_TIMEOUT,
                limits=limits
        ) as client:

            gateway_service = GatewayService(client=client)

            try:
                # 1. Ищем дату
                result = await session.exec(select(func.max(TestResult.test_date)))
                last_db_date = result.first()

                # Если база пустая — берем начало года, иначе — шаг назад на 1 день
                if not last_db_date:
                    start_date = datetime.date(datetime.datetime.now().year, 1, 1)
                else:
                    start_date = last_db_date - datetime.timedelta(days=1)

                today = datetime.date.today()
                logger.info(f"📅 Период: {start_date} -> {today}")

                if start_date > today:
                    await send_telegram_message("Результаты исследований offline\n✅ Данные актуальны.")
                    return

                # 2. Качаем
                delta = (today - start_date).days
                days_list = [start_date + datetime.timedelta(days=i) for i in range(delta + 1)]

                for current_date in days_list:
                    await collect_by_day(current_date.strftime("%d.%m.%Y"), gateway_service, session)
                    await asyncio.sleep(1.0)  # Небольшая пауза

                # 3. Успех
                await send_telegram_message(f"Результаты исследований offline\n✅ <b>Update Done</b>\n{start_date} — {today}")

            except Exception as e:
                logger.error(f"❌ Ошибка: {e}", exc_info=True)
                await send_telegram_message(f"Результаты исследований offline\n❌ <b>Error</b>: {e}\nПовтор через 30 мин.")

                # 4. Повторные попытки (количество попыток задаем в .env)
                if retry_count < settings.UPDATE_RETRY_ATTEMPTS:
                    run_time = datetime.datetime.now() + datetime.timedelta(minutes=30)
                    scheduler.add_job(
                        update_database_job, 'date', run_date=run_time,
                        args=[scheduler, retry_count + 1],
                        id=f"retry_{datetime.datetime.now().timestamp()}"
                    )