# application/bot_app/handler/commands.py

from telebot.states.asyncio import StateContext
from telebot.types import Message, ReplyKeyboardRemove
from .decorator import cmd, UltraHandler, BotNumber
from ..keyboards.inline import main_menu_inl, language_inl, phone_number_rb
from ...services import TelegramUser


@cmd("start", "Start the bot")
async def start_command(message: Message, state: StateContext):
    try:
        h = UltraHandler(message, state)
        user = await TelegramUser().get_user(message.from_user.id)
        if user is None:
            obj = TelegramUser()
            await obj.create_user({
                "telegram_id": message.from_user.id,
                "full_name": message.from_user.full_name,
                "username": message.from_user.username,
            })

        msg_id = await h.send(".", reply_markup=ReplyKeyboardRemove(), translate=False)
        await h.delete(msg_id=msg_id.id)
        lang = await h.lang()
        await state.delete()
        # passenger = await h.get_passenger()
        #
        # if not passenger:
        #     return await h.send(
        #         "utils.select_language",
        #         reply_markup=language_inl(lang=lang)
        #     )
        #
        # # 3. Agar passenger bor bo'lsa, asosiy menyu
        # if not passenger.phone:
        #     # Telefon raqam yo'q bo'lsa
        #     await h.set_state(BotNumber.contact)
        #     return await h.send(
        #         "ask_phone_number.text",
        #         reply_markup=phone_number_rb(lang=lang)
        #     )

        # 4. Hamma narsa to'g'ri bo'lsa
        await h.send(
            "main_menu",
            reply_markup=main_menu_inl(lang),
            name=message.from_user.full_name
        )
    except Exception as err:
        print(err)

@cmd("language", "Change language code")
async def language_command(message: Message, state: StateContext):
    """Handle /language command"""
    h = UltraHandler(message, state)
    lang = await h.lang()
    return await h.send(
        "utils.select_language",
        reply_markup=language_inl(lang)
    )
