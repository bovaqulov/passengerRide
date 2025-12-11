# application/bot_app/handler/decorator.py

from typing import Any, Optional, Union, Callable, List, Dict
from functools import wraps, lru_cache

from telebot.states.asyncio import StateContext
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, ReplyKeyboardMarkup, BotCommand, \
    ReplyKeyboardRemove
from telebot.handler_backends import State, StatesGroup
from application.core.bot import bot
from application.core.i18n import t
from application.core.log import logger
from application.services.city_service import CityServiceAPI
from application.services.passenger_service import PassengerServiceAPI, PassengerGetService
from application.services.user_service import TelegramUser, UserService

# Admin IDs - environment variables dan olish kerak
ADMINS: List[int] = []


# ==================== STATE CLASSES ====================

class BotStates(StatesGroup):
    """Bot davlatlari - TeleBot native states"""
    from_location: State = State()
    to_location: State = State()
    details: State = State()

class BotPostStates(StatesGroup):
    from_location: State = State()
    to_location: State = State()
    confirm: State = State()



class BotNumber(StatesGroup):
    contact: State = State()
    confirm_code: State = State()

# ==================== PERFORMANCE DECORATORS ====================

def async_lru_cache(maxsize: int = 128):
    """Async funksiyalar uchun cache decorator"""

    def decorator(func):
        cache = {}

        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            if key not in cache:
                cache[key] = await func(*args, **kwargs)
            return cache[key]

        wrapper.cache_clear = lambda: cache.clear()
        return wrapper

    return decorator


def throttle(seconds: int = 1):
    """Rate limiting decorator"""
    last_called = {}

    def decorator(func):
        @wraps(func)
        async def wrapper(msg: Union[Message, CallbackQuery], *args, **kwargs):
            user_id = msg.from_user.id
            current_time = __import__('time').time()

            if user_id in last_called:
                elapsed = current_time - last_called[user_id]
                if elapsed < seconds:
                    return None

            last_called[user_id] = current_time
            return await func(msg, *args, **kwargs)

        return wrapper

    return decorator


def error_handler(send_to_user: bool = True):
    """Xatoliklarni handle qiluvchi decorator"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"❌ Error in {func.__name__}: {e}", exc_info=True)

                if send_to_user and args:
                    msg = args[0]
                    if isinstance(msg, (Message, CallbackQuery)):
                        h = UltraHandler(msg)
                        await h.send("errors.something_went_wrong")

                return None

        return wrapper

    return decorator


# ==================== ULTRA HANDLER ====================

class UltraHandler:
    __slots__ = ('msg', 'context', '_user_cache', '_lang_cache', 'chat_id', 'user_id')

    def __init__(self, message: Union[Message, CallbackQuery], context: Optional[StateContext] = None):
        self.msg = message
        self.context = context
        self._user_cache: Optional[UserService] = None
        self._lang_cache: Optional[str] = None

        self.user_id = message.from_user.id
        self.chat_id = message.chat.id if isinstance(message, Message) else message.message.chat.id

    async def get_user(self) -> UserService:
        if not self._user_cache:
            self._user_cache = await TelegramUser().get_user(self.user_id)
        return self._user_cache

    async def get_passenger(self) -> Optional[PassengerGetService]:
        """Get passenger or return None if not exists"""
        try:
            passenger_api = PassengerServiceAPI()
            return await passenger_api.get_by_user(self.user_id)
        except Exception as e:
            logger.error(f"Error getting passenger: {e}")
            return None

    async def lang(self) -> str:
        user = await self.get_user()
        return user.language or "en"


    async def _(self, key: str, **kwargs) -> str:
        lang = await self.lang()
        return t(key, lang, **kwargs)

    @error_handler(send_to_user=False)
    async def send_verification_code(self, code: str) -> str:
        return await bot.verify_user(code)

    @error_handler(send_to_user=False)
    async def get_city_name(self, city, lang):
        city_api = CityServiceAPI()
        return await city_api.get_translate(city, lang)

    @error_handler(send_to_user=False)
    async def send(
            self,
            text: str,
            translate: bool = True,
            reply_markup: Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, None] = None,
            **kwargs
    ) -> Optional[Message]:
        final_text = await self._(text, **kwargs) if translate else text

        return await bot.send_message(
            self.chat_id,
            final_text,
            reply_markup=reply_markup,
        )

    @error_handler(send_to_user=False)
    async def reply(
            self,
            text: str,
            translate: bool = True,
            reply_markup: Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, None] = None,
            **kwargs
    ) -> Optional[Message]:
        final_text = await self._(text, **kwargs) if translate else text
        return await bot.reply_to(
            self.msg,
            final_text,
            reply_markup=reply_markup
        )

    @error_handler(send_to_user=False)
    async def edit(
            self,
            text: str,
            translate: bool = True,
            reply_markup: Optional[InlineKeyboardMarkup] = None,
            **kwargs
    ) -> Optional[Message]:
        final_text = await self._(text, **kwargs) if translate else text
        message_id = self._get_message_id()
        return await bot.edit_message_text(
            final_text,
            self.chat_id,
            message_id,
            reply_markup=reply_markup
        )

    @error_handler(send_to_user=False)
    async def delete(self, msg_id=None, count=1) -> bool:
        message_id = self._get_message_id() if not msg_id else msg_id
        return await bot.delete_messages(self.chat_id, list(range(message_id, message_id - count, -1)))

    @error_handler(send_to_user=False)
    async def answer(
            self,
            text: str = "",
            show_alert: bool = False,
            translate: bool = True
    ) -> bool:
        if not isinstance(self.msg, CallbackQuery):
            return False

        final_text = await self._(text) if (text and translate) else text
        return await bot.answer_callback_query(
            self.msg.id,
            text=final_text,
            show_alert=show_alert
        )

    def _get_message_id(self) -> int:
        return (self.msg.message_id if isinstance(self.msg, Message)
                else self.msg.message.message_id)

    async def set_state(self, stat: State, data: Union[Dict[str, str|dict], None] = None) -> None:
        await self.context.set(stat)
        if data:
            await self.context.add_data(**data)

    async def get_state(self) -> Optional[str]:
        return await self.context.get()

    async def get_data(self) -> Dict[str, Any]:
        async with self.context.data() as data:
            return data

    async def clear_state(self) -> None:
        await self.context.delete()

    # ==================== CALLBACK DATA PARSER ====================

    @staticmethod
    @lru_cache(maxsize=512)
    def parse_callback(data: str, sep: str = ':') -> Dict[str, str]:
        parts = data.split(sep, 3)
        return {
            'action': parts[0] if len(parts) > 0 else '',
            'value': parts[1] if len(parts) > 1 else '',
            'param': parts[2] if len(parts) > 2 else '',
            'extra': parts[3] if len(parts) > 3 else '',
            'raw': data
        }

    @property
    def callback_data(self) -> Dict[str, str]:
        if isinstance(self.msg, CallbackQuery):
            return self.parse_callback(self.msg.data)
        return {}

    @property
    def text(self) -> str:
        if isinstance(self.msg, Message):
            return self.msg.text or self.msg.caption or ""
        return ""

    @property
    def is_callback(self) -> bool:
        return isinstance(self.msg, CallbackQuery)

    @property
    def is_message(self) -> bool:
        return isinstance(self.msg, Message)


# ==================== HANDLER MASTER ====================

class HandlerMaster:
    """Optimized handler management system"""

    _commands: Dict[str, Dict] = {}
    _callbacks: Dict[str, Callable] = {}
    _messages: Dict[str, Dict] = {}
    _states: Dict[State, Callable] = {}
    _error_handlers: List[Callable] = []

    # ==================== DECORATORS ====================

    @classmethod
    def command(cls, name: str, desc: str = "", admin: bool = False, state: State = None):
        """Register command handler"""

        def decorator(func):
            cls._commands[name] = {
                'func': func,
                'desc': desc,
                'admin': admin,
                'state': state
            }
            return func

        return decorator

    @classmethod
    def callback(cls, pattern: str = "", state: State = None):
        """Register callback handler"""

        def decorator(func):
            key = f"{pattern}:{state}" if state else pattern
            cls._callbacks[key] = {'func': func, 'pattern': pattern, 'state': state}
            return func

        return decorator

    @classmethod
    def message(cls, content_types: List[str] = None, regex: str = None, state: State = None):
        """Register message handler"""

        def decorator(func):
            cls._messages[func.__name__] = {
                'func': func,
                'content_types': content_types or ['text'],
                'regex': regex,
                'state': state
            }
            return func

        return decorator

    @classmethod
    def state_handler(cls, state: State):
        """Register state handler"""

        def decorator(func):
            cls._states[state] = func
            return func

        return decorator


    @classmethod
    def error(cls, func: Callable):
        """Register error handler"""
        cls._error_handlers.append(func)
        return func

    # ==================== HELPERS ====================

    @staticmethod
    async def is_admin(user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in ADMINS


    @classmethod
    async def handle_error(cls, msg: Union[Message, CallbackQuery], error: Exception):
        """Handle errors"""
        for handler in cls._error_handlers:
            try:
                await handler(msg, error)
            except Exception as e:
                logger.error(f"Error handler failed: {e}")

    # ==================== REGISTRATION ====================

    @classmethod
    async def register_all(cls):
        """Register all handlers at once - CALL ONLY ONCE"""
        await cls._register_bot_commands()
        # 1. COMMAND HANDLERS
        for cmd_name, config in cls._commands.items():

            @bot.message_handler(commands=[cmd_name], state=config['state'])
            @throttle(seconds=0)
            @error_handler()
            async def cmd_handler(message: Message, state: StateContext, cfg=config):

                # Admin check
                if cfg['admin'] and not await cls.is_admin(message.from_user.id):
                    h = UltraHandler(message)
                    await h.send("errors.admin_only")
                    return

                try:
                    await cfg['func'](message, state)
                except Exception as e:
                    await cls.handle_error(message, e)

        # 2. CALLBACK HANDLERS
        for key, config in cls._callbacks.items():
            pattern = config['pattern']
            state = config['state']

            @bot.callback_query_handler(
                func=lambda c, p=pattern: c.data.startswith(p) if p else True,
                state=state
            )
            @throttle(seconds=1)
            @error_handler()
            async def cb_handler(call: CallbackQuery, state: StateContext, cfg=config):
                try:
                    await cfg['func'](call, state)
                except Exception as e:
                    await cls.handle_error(call, e)

        # 3. STATE HANDLERS
        for state, func in cls._states.items():

            @bot.message_handler(content_types=["location", "text"], state=state)
            @bot.callback_query_handler(func=lambda call: call.data, state=state)
            @error_handler()
            async def state_msg_handler(message: Message, state: StateContext, f=func):
                try:
                    await f(message, state)
                except Exception as e:
                    await cls.handle_error(message, e)

        # 4. MESSAGE HANDLERS
        for name, config in cls._messages.items():

            @bot.message_handler(
                content_types=config['content_types'],
                state=config['state']
            )
            @error_handler()
            async def msg_handler(message: Message, state: StateContext, cfg=config):

                # Regex check
                if cfg['regex'] and message.text:
                    import re
                    if not re.match(cfg['regex'], message.text):
                        return

                try:
                    await cfg['func'](message, state)
                except Exception as e:
                    await cls.handle_error(message, e)

        logger.info(
            f"✅ Registered: {len(cls._commands)} commands, "
            f"{len(cls._callbacks)} callbacks, "
            f"{len(cls._states)} states, "
            f"{len(cls._messages)} messages"
        )

    @classmethod
    async def _register_bot_commands(cls):
        """Register bot commands in Telegram menu"""
        try:
            from telebot.types import BotCommand

            commands_list = []

            for cmd_name, config in cls._commands.items():
                # Faqat admin emas va description bo'lgan commandlarni qo'shamiz
                if not config['admin'] and config.get('desc'):
                    commands_list.append(
                        BotCommand(command=cmd_name, description=config['desc'])
                    )

            if commands_list:
                await bot.set_my_commands(commands_list)
                logger.info(f"📝 Registered {len(commands_list)} bot commands: {[cmd.command for cmd in commands_list]}")
            else:
                logger.warning("⚠️ No commands to register")

        except Exception as e:
            logger.error(f"❌ Failed to register bot commands: {e}")


# ==================== SHORTHAND ALIASES ====================

cmd = HandlerMaster.command
cb = HandlerMaster.callback
msg = HandlerMaster.message
state = HandlerMaster.state_handler
err = HandlerMaster.error
