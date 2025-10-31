from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GATEWAY_URL: str
    GATEWAY_API_KEY: str
    GATEWAY_REQUEST_ENDPOINT: str
    REQUEST_TIMEOUT: float
    REQUEST_PAGINATOR_LIMIT: int

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    ALLOW_DB_CLEAR_ENDPOINT: bool = False

    LOGS_LEVEL: str = "INFO"
    DEBUG_MODE: bool = True
    FOLDER_DEBUG: str = "debug"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


    @property
    def DATABASE_URL(self) -> str: # noqa
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # noqa
