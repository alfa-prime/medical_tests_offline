# отправка сообщения в телеграм

import httpx
from app.core import get_settings, logger

settings = get_settings()

async def send_telegram_message(message: str):
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.warning("⚠️ Telegram не настроен")
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": settings.TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(url, json=payload)
    except Exception as e:
        logger.error(f"Ошибка отправки в Telegram: {e}")