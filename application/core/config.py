# application/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Application settings with environment variables"""

    # Required settings with defaults
    DEBUG: bool = True
    REDIS_PUBLIC_URL: str = "redis://localhost:6379/0"
    BOT_TOKEN_PROD: str = ""
    AUTH_TOKEN: str = ""
    WEBHOOK_URL_PROD: str = ""
    HOST_PROD: str = "0.0.0.0"  # Default qiymat
    PROD_API_HOST: str = "http://localhost:8000"  # Default qiymat

    # Development defaults
    HOST_DEMO: str = "127.0.0.1"
    PORT_DEMO: int = 8888
    BOT_TOKEN_DEMO: str = "8448377050:AAH5mpmRq4LARRfg6-c-zSiUzMCXcU5tiVo"
    REDIS_URL_DEMO: str = "redis://localhost:6379/0"

    # Webhook
    WEBHOOK_URL_DEMO: str = "e5f159555443.ngrok-free.app"

    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Localization
    LOCALES_PATH: str = "./locales"
    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGES: str = "en,uz,ru"
    API_VERSION: str = "api/v1"

    # Admin
    ADMIN_IDS: str = ""

    # Redis
    REDIS_MAX_CONNECTIONS: int = 10

    @property
    def BOT_TOKEN(self) -> str:
        """Get bot token based on DEBUG mode"""
        return self.BOT_TOKEN_DEMO if self.DEBUG else self.BOT_TOKEN_PROD

    @property
    def REDIS_URL(self) -> str:
        """Get Redis URL based on DEBUG mode"""
        return self.REDIS_URL_DEMO if self.DEBUG else self.REDIS_PUBLIC_URL

    @property
    def SUPPORTED_LANGS(self) -> List[str]:
        """Get list of supported languages"""
        return [lang.strip() for lang in self.SUPPORTED_LANGUAGES.split(',')]

    @property
    def ADMINS(self) -> List[int]:
        """Get list of admin user IDs"""
        if not self.ADMIN_IDS:
            return []
        return [int(uid.strip()) for uid in self.ADMIN_IDS.split(',') if uid.strip()]

    @property
    def WEBHOOK_URL(self) -> str:
        """Get webhook url based on DEBUG mode"""
        return self.WEBHOOK_URL_DEMO if self.DEBUG else self.WEBHOOK_URL_PROD

    @property
    def HOST(self) -> str:
        """Get host based on DEBUG mode"""
        return self.HOST_DEMO

    @property
    def PORT(self) -> int:
        """Get port based on DEBUG mode"""
        return self.PORT_DEMO

    @property
    def MAIN_URL(self) -> str:
        """Get main url based on DEBUG mode"""
        return f"http://{self.API_HOST}:{self.API_PORT}" if self.DEBUG else self.PROD_API_HOST

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        env_nested_delimiter="__"
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()