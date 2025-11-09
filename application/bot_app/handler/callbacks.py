from typing import Union

from telebot.states.sync import StateContext
from telebot.types import CallbackQuery, Message

from .decorator import cb, UltraHandler, BotStates
from ..keyboards.inline import order_inl, main_menu_inl, start_inl


@cb("order")
async def order_callback(call: Union[CallbackQuery, Message], state):
    h = UltraHandler(call, state)
    lang = await h.lang()
    func = h.edit
    if isinstance(call, Message):
        await state.delete()
        await h.delete(count=2)
        func = h.send

    return await func(
        "travel_type.text",
        reply_markup=order_inl(lang)
    )

@cb("back")
async def back_callback(call: CallbackQuery, state):
    h = UltraHandler(call, state)
    lang = await h.lang()
    user = await h.get_user()
    await h.edit(
        "main_menu.text",
        reply_markup=main_menu_inl(lang),
        name=user.full_name
    )

@cb("now")
async def now_callback(call: Union[CallbackQuery, Message], state: StateContext):
    h = UltraHandler(call, state)
    lang = await h.lang()
    await h.delete()
    await h.set_state(BotStates.from_location)
    return await h.send(
        "travel_start.text",
        reply_markup=start_inl(lang)
    )