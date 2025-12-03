# application/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Application settings with environment variables"""

    # App settings
    DEBUG: bool
    REDIS_PUBLIC_URL: str
    BOT_TOKEN_PROD: str
    AUTH_TOKEN: str
    WEBHOOK_URL_PROD: str
    HOST_PROD: str


    HOST_DEMO: str = "0.0.0.0"
    PORT_DEMO: int = 8888

    # Bot tokens
    BOT_TOKEN_DEMO: str = "8448377050:AAH5mpmRq4LARRfg6-c-zSiUzMCXcU5tiVo"

    # Redis
    REDIS_URL_DEMO: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 10

    # Localization
    LOCALES_PATH: str = "./locales"
    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGES: str = "en,uz,ru"
    API_VERSION: str = "api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: str = 8000
    PROD_API_HOST: str

    # Admin
    ADMIN_IDS: str = ""

    WEBHOOK_URL_DEMO: str = "http://127.0.0.1:8888"



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
    def HOST(self):
        """Get host based on DEBUG mode"""
        return self.HOST_DEMO if self.DEBUG else self.HOST_PROD

    @property
    def PORT(self):
        """Get port based on DEBUG mode"""
        return self.PORT_DEMO if self.DEBUG else self.PORT_PROD

    @property
    def  MAIN_URL(self):
        """Get main url based on DEBUG mode"""
        return f"http://{self.API_HOST}:{self.API_PORT}" if self.DEBUG else self.PROD_API_HOST

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()