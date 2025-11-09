# application/bot_app/handler/commands.py
from telebot.states.asyncio import StateContext
from telebot.types import Message
from .decorator import cmd, UltraHandler, BotStates
from ..keyboards.inline import main_menu_inl


@cmd("start", "Start the bot")
async def start_command(message: Message, state: StateContext):
    """Handle /start command"""
    h = UltraHandler(message, state)
    lang = await h.lang()
    user = await h.get_user()
    await h.send(
            "main_menu.text",
            reply_markup=main_menu_inl(lang),
            name=user.full_name
        )

