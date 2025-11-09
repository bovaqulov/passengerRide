from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import JSONResponse
from telebot.types import Update

from ..core.bot import bot
from ..core.config import settings
from ..core.log import logger
from ..database.cache import cache
from ..core.i18n import t

router = APIRouter()

@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Passenger Bot API",
        "version": "1.0.0",
        "status": "running"
    }

@router.get("/health")
async def health():
    """Health check."""
    try:
        await cache.client.ping()
        return {
            "status": "healthy",
            "redis": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }, 503

@router.get("/translate/{key}")
async def translate(key: str, lang: str = "en"):
    """Get translation."""
    logger.info(f"Translating:  {key}")
    return {
        "key": key,
        "lang": lang,
        "value": t(key, lang)
    }

@router.post("/webhook")
async def webhook(request: Request):
    """ webhook endpoint."""
    try:
        update = await request.body()
        await bot.process_new_updates([Update.de_json(update.decode("utf-8"))])
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/set-webhook")
async def set_webhook(request: Request):
    """Set webhook endpoint."""
    try:
        await bot.remove_webhook()
        await bot.set_webhook(url=f"{settings.WEBHOOK_URL}/webhook")
        info = await bot.get_webhook_info()
        return JSONResponse(content={"status": str(info)},status_code=200)
    except Exception as e:
        return {"status": "error", "error": str(e)}
