from telebot import types

from application.bot_app.handler import UltraHandler
from application.core.bot import bot


@bot.message_handler(commands=["send"])
async def send_msg(message: types.Message):
    h = UltraHandler(message)

