# Qisqartirilgan versiya - hammasini bitta classda
import time
from typing import Dict, Any, Union

from telebot.asyncio_handler_backends import BaseMiddleware, CancelUpdate
from telebot.types import Message, CallbackQuery
from application.core import bot, logger
from application.services import TelegramUser


class AllInOneMiddleware(BaseMiddleware):
    """Barcha vazifalarni bajaruvchi yagona middleware"""
    __slots__ = ("rate_limit", "admin_ids", "last_requests", "update_types")

    def __init__(self, rate_limit: int = 2, admin_ids: list = None):
        super().__init__()
        self.rate_limit = rate_limit
        self.admin_ids = admin_ids or []
        self.last_requests: Dict[int, float] = {}
        self.update_types = ['message', 'callback_query']

    async def pre_process(self, message: Message, data: Any):
        """Barcha pre-processing vazifalari"""

        # 1. Logging
        await self._log_request(message)

        # 2. Rate limiting
        if not await self._check_rate_limit(message):
            return CancelUpdate()

        # 3. Admin check
        if not await self._check_admin_commands(message):
            return CancelUpdate()

        # 4. Auth & Ban check
        if not await self._check_user_status(message):
            return CancelUpdate()

        # 5. Metrics
        data['start_time'] = time.time()

        return True

    async def post_process(self, message: Union[Message, CallbackQuery], data: Any, exception: Exception = None):
        """Post-processing"""
        if 'start_time' in data:
            duration = time.time() - data['start_time']
            logger.info(f"⏱️ Request completed in {duration:.2f}s")

    async def _log_request(self, message: Union[Message, CallbackQuery],) -> None:
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name

        if isinstance(message, Message):
            text = message.text or message.caption or "[no text]"
            msg_type = "📨 Message"
        else:
            text = message.data
            msg_type = "🔘 Callback"

        logger.info(f"{msg_type} from @{username} ({user_id}): {text[:50]}")

    async def _check_rate_limit(self, message: Message) -> bool:
        user_id = message.from_user.id
        current_time = time.time()

        if user_id in self.last_requests:
            if current_time - self.last_requests[user_id] < self.rate_limit:
                try:
                    await bot.send_message(message.chat.id, "🚫 Too fast! Please wait.")
                except:
                    pass
                return False

        self.last_requests[user_id] = current_time
        return True

    async def _check_admin_commands(self, message: Message) -> bool:
        if not isinstance(message, Message) or not message.text:
            return True

        admin_commands = ['/admin', '/stats', '/broadcast', '/ban']
        command = message.text.split()[0].lower()

        if command in admin_commands and message.from_user.id not in self.admin_ids:
            await bot.send_message(message.chat.id, "❌ Admin only command.")
            return False

        return True

    async def _check_user_status(self, message: Message) -> bool:
        try:
            user_id = message.from_user.id

            # Ban check
            if await TelegramUser().is_ban_user(user_id):
                await bot.send_message(message.chat.id, "🚫 You are banned.")
                return False

            return True

        except Exception as e:
            logger.error(f"User status check error: {e}")
            return True


# Sozlash funksiyasi
def setup_my_middleware(admin_ids: list = None):
    """Soddalashtirilgan middleware sozlash"""
    middleware = AllInOneMiddleware(rate_limit=1, admin_ids=admin_ids)
    bot.setup_middleware(middleware)
    logger.info("✅ Simple all-in-one middleware setup completed")