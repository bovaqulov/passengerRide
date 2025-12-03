from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import JSONResponse
from telebot.types import Update

from .driver_found import driver_response
from ..core.bot import bot
from ..core.config import settings
from ..core.log import logger
from ..database.cache import cache
from ..core.i18n import t
from ..services.user_service import UserService, TelegramUser

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
async def set_webhooks(request: Request):
    """Set webhook endpoint."""
    try:
        print(f"Token: {settings.BOT_TOKEN[:15]}...")
        print(f"Webhook URL from settings: {settings.WEBHOOK_URL}")

        # 检查并格式化 webhook URL
        webhook_url = settings.WEBHOOK_URL

        # 确保 URL 包含协议
        if not webhook_url.startswith(('http://', 'https://')):
            # CloudFlare 隧道通常需要 https
            webhook_url = f"https://{webhook_url}"

        # 确保 URL 以 /webhook 结尾
        if not webhook_url.endswith('/webhook'):
            webhook_url = f"{webhook_url}/webhook"

        print(f"Formatted webhook URL: {webhook_url}")

        me = await bot.get_me()
        print(f"✅ Bot authenticated: @{me.username}")

        # 移除现有 webhook
        print("Removing existing webhook...")
        await bot.remove_webhook()

        # 设置新的 webhook
        print(f"Setting webhook to: {webhook_url}")
        await bot.set_webhook(url=webhook_url)

        # 获取 webhook 信息
        info = await bot.get_webhook_info()
        print(f"✅ Webhook set successfully: {info.url}")

        return JSONResponse(
            content={
                "status": "success",
                "message": "Webhook set successfully",
                "bot": f"@{me.username}",
                "webhook_url": webhook_url,
                "webhook_info": {
                    "url": info.url,
                    "has_custom_certificate": info.has_custom_certificate,
                    "pending_update_count": info.pending_update_count,
                    "last_error_date": info.last_error_date,
                    "last_error_message": info.last_error_message,
                    "max_connections": info.max_connections,
                    "ip_address": info.ip_address
                }
            },
            status_code=200
        )

    except Exception as e:
        import traceback
        print(f"❌ Error setting webhook: {e}")
        print(traceback.format_exc())

        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "type": type(e).__name__,
                "debug_info": {
                    "bot_token_exists": bool(settings.BOT_TOKEN),
                    "webhook_url_original": settings.WEBHOOK_URL,
                    "webhook_url_formatted": f"https://{settings.WEBHOOK_URL}/webhook" if settings.WEBHOOK_URL else None
                }
            },
            status_code=500
        )


@router.post("/passenger")
async def driver_web(request: Request):
    return await driver_response(request)


