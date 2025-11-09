# application/app.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from application.core.config import settings
from application.core.log import logger
from application.database.cache import cache
from application.core.i18n import init_translations
from application.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting application...")

    try:
        # Connect to Redis
        await cache.connect()

        # Initialize translations
        await init_translations(cache.client)

        # Setup bot handlers
        from application.bot_app.handler import setup_handlers
        await setup_handlers()
        logger.info("✅ Application started successfully")

        yield

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    finally:
        # Shutdown
        logger.info("🛑 Shutting down application...")

        # Disconnect Redis
        await cache.disconnect()

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