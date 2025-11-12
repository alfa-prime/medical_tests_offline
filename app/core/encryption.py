from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import TypeDecorator, String
from sqlalchemy.engine import Dialect

from app.core.config import get_settings
from app.core.logger_setup import logger

settings = get_settings()
ENCRYPTION_KEY = settings.ENCRYPTION_KEY.encode()

try:
    fernet = Fernet(ENCRYPTION_KEY)
except (ValueError, TypeError) as e:
    logger.critical(f"КРИТИЧЕСКАЯ ОШИБКА: Неверный ключ шифрования. {e}")
    fernet = None


class EncryptedString(TypeDecorator):
    """
    Кастомный тип для SQLAlchemy, который автоматически шифрует и расшифровывает
    строковые данные при взаимодействии с базой данных.
    """
    impl = String
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect: Dialect) -> str | None:
        """
        Вызывается ПЕРЕД записью данных в БД.
        Шифрует значение.
        """
        if value is None or fernet is None:
            return None

        # Преобразуем строку в байты и шифруем
        encrypted_value = fernet.encrypt(value.encode('utf-8'))
        return encrypted_value.decode('utf-8')  # Храним в БД как строку

    def process_result_value(self, value: str | None, dialect: Dialect) -> str | None:
        """
        Вызывается ПОСЛЕ чтения данных из БД.
        Расшифровывает значение.
        """
        if value is None or fernet is None:
            return None

        try:
            # Преобразуем строку из БД в байты и расшифровываем
            decrypted_value = fernet.decrypt(value.encode('utf-8'))
            return decrypted_value.decode('utf-8')
        except InvalidToken:
            # Если в БД хранится нешифрованное или поврежденное значение
            logger.warning("Не удалось расшифровать значение из БД. Возможно, оно не было зашифровано.")
            return value  # Возвращаем как есть
        except Exception as e:
            logger.error(f"Ошибка при расшифровке значения: {e}")
            return None  # Возвращаем None в случае серьезной ошибки