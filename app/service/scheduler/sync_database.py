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
from app.service.collector.tools import full_audit_dbase
from app.service.utils.telegram import send_telegram_message
from app.service.dbase.dump_bd import create_database_dump

settings = get_settings()


async def sync_database(scheduler, retry_count: int = 0):
    logger.info(f"[Синхронизация базы] Старт задачи. Попытка #{retry_count + 1}")

    async with AsyncSession(engine) as session:
        limits = httpx.Limits(max_connections=10)
        async with httpx.AsyncClient(
                base_url=settings.GATEWAY_URL,
                headers={"X-API-KEY": settings.GATEWAY_API_KEY},
                timeout=settings.REQUEST_TIMEOUT,
                limits=limits
        ) as client:

            gateway_service = GatewayService(client=client)

            try:
                # --- СИНХРОНИЗАЦИЯ ---
                result = await session.exec(select(func.max(TestResult.test_date)))
                last_db_date = result.first()

                if not last_db_date:
                    start_date = datetime.date(datetime.datetime.now().year, 1, 1)
                else:
                    start_date = last_db_date - datetime.timedelta(days=2)  # noqa

                today = datetime.date.today()

                # Логика сбора данных
                if start_date > today:
                    logger.info("Данные актуальны, сбор не требуется.")
                else:
                    logger.info(f"Сбор данных за период: {start_date} -> {today}")
                    delta = (today - start_date).days
                    days_list = [start_date + datetime.timedelta(days=i) for i in range(delta + 1)]

                    for current_date in days_list:
                        await collect_by_day(current_date.strftime("%d.%m.%Y"), gateway_service, session)
                        await asyncio.sleep(1.0)

                # --- АУДИТ ---
                logger.info("Запуск пре-бэкап аудита...")
                audit_result = await full_audit_dbase()

                if audit_result["status"] == "OK":
                    audit_icon = "✅"
                    audit_text = "Целостность ОК"
                else:
                    audit_icon = "⚠️"
                    audit_text = f"Найдено {audit_result['bad_count']} битых!"

                # --- ДАМП БАЗЫ ---
                logger.info("Создание ежедневного дампа...")
                dump_result = await create_database_dump(filename="daily_latest.dump")
                dump_path = dump_result.get("file_path", "unknown")

                # --- УВЕДОМЛЕНИЕ ---
                message = (
                    f"Результаты исследований offline\n"
                    f"📅 Синхронизация: {start_date} — {today}\n"
                    f"💾 Бэкап: {dump_path}\n"
                    f"──────────────────\n"
                    f"📊 <b>Статистика БД:</b>\n"
                    f"{audit_icon} Аудит: {audit_text} ({audit_result['duration']}с)\n"
                    f"✅ Готовые результаты: {audit_result['total_checked']}\n"
                    f"⏳ <b>Пустые: {audit_result['empty_count']}</b>"
                )
                logger.info("[Синхронизация базы] Успешно завершено.")
                await send_telegram_message(message)

            except Exception as e:
                logger.error(f"❌ [Синхронизация базы] Ошибка: {e}", exc_info=True)

                await send_telegram_message(
                    f"Результаты исследований offline\n"
                    f"❌ <b>Update Error</b>\n"
                    f"Ошибка: {e}\n"
                    f"⏳ Попытка {retry_count + 1}/{settings.UPDATE_RETRY_ATTEMPTS}. Повтор через 30 мин."
                )

                if retry_count < settings.UPDATE_RETRY_ATTEMPTS:
                    run_time = datetime.datetime.now() + datetime.timedelta(minutes=30)
                    scheduler.add_job(
                        sync_database,
                        'date',
                        run_date=run_time,
                        args=[scheduler, retry_count + 1],
                        id=f"retry_sync_{datetime.datetime.now().timestamp()}"
                    )
                else:
                    await send_telegram_message(
                        "Результаты исследований offline\n"
                        "⛔ <b>Update</b>: Превышен лимит попыток. Остановка."
                    )