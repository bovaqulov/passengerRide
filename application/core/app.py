"""
Main FastAPI application
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager

from application.core.config import settings
from application.core.log import logger
from application.database.cache import cache
from application.core.i18n import init_translations
from application.api.routes import router
from application.services.http_client import GlobalHTTPClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with proper cleanup"""
    # Startup
    logger.info("🚀 Starting application...")

    try:
        # Connect to Redis
        await cache.connect()
        logger.info("✅ Redis connected")

        # Initialize translations
        await init_translations(cache.client)
        logger.info("✅ Translations initialized")

        # Setup bot handlers
        from application.bot_app.handler import setup_handlers
        await setup_handlers()
        logger.info("✅ Bot handlers setup complete")

        logger.info("✅ Application started successfully")

        yield

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    finally:
        # Shutdown
        logger.info("🛑 Shutting down application...")

        try:
            # Close HTTP client sessions
            await GlobalHTTPClient().close()
            logger.info("✅ HTTP client sessions closed")
        except Exception as e:
            logger.error(f"❌ Error closing HTTP client: {e}")

        try:
            # Disconnect Redis
            await cache.disconnect()
            logger.info("✅ Redis disconnected")
        except Exception as e:
            logger.error(f"❌ Error disconnecting Redis: {e}")

        logger.info("✅ Application stopped")


# Create FastAPI app
app = FastAPI(
    title="Passenger Bot API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

app.include_router(router)

