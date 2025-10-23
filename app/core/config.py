from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GATEWAY_URL: str
    GATEWAY_API_KEY: str
    GATEWAY_REQUEST_ENDPOINT: str

    LOGS_LEVEL: str  = "INFO"
    DEBUG_MODE: bool = True
    FOLDER_DEBUG: str = "debug"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings() # noqa