# application/bot_app/handler/commands.py

from telebot.states.asyncio import StateContext
from telebot.types import Message
from .decorator import cmd, UltraHandler, BotNumber
from ..keyboards.inline import main_menu_inl, language_inl, phone_number_rb
from ...services import TelegramUser


@cmd("start", "Start the bot")
async def start_command(message: Message, state: StateContext):
    """Handle /start command"""
    h = UltraHandler(message, state)

    # 1. TelegramUser ni tekshirish yoki yaratish
    user = await TelegramUser().get_user(message.from_user.id)
    if user is None:
        obj = TelegramUser()
        await obj.create_user({
            "telegram_id": message.from_user.id,
            "full_name": message.from_user.full_name,
            "username": message.from_user.username,
        })

    # 2. Passenger ni tekshirish
    lang = await h.lang()
    await state.delete()
    passenger = await h.get_passenger()

    if not passenger:
        # Agar passenger yo'q bo'lsa, telefon raqam so'rash
        await h.set_state(BotNumber.contact)
        return await h.send(
            "ask_phone_number.text",
            reply_markup=phone_number_rb(lang=lang)
        )

    # 3. Agar passenger bor bo'lsa, asosiy menyu
    if not passenger.phone:
        # Telefon raqam yo'q bo'lsa
        await h.set_state(BotNumber.contact)
        return await h.send(
            "ask_phone_number.text",
            reply_markup=phone_number_rb(lang=lang)
        )

    # 4. Hamma narsa to'g'ri bo'lsa
    await h.send(
        "main_menu.text",
        reply_markup=main_menu_inl(lang),
        name=passenger.full_name or message.from_user.full_name
    )

@cmd("language", "Change language code")
async def language_command(message: Message, state: StateContext):
    """Handle /language command"""
    h = UltraHandler(message, state)
    lang = await h.lang()
    return await h.send(
        "utils.select_language",
        reply_markup=language_inl(lang)
    )
