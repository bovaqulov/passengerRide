from telebot.states.asyncio import StateContext
from telebot.types import Message
from . import order_callback, now_callback
from .decorator import state, UltraHandler, BotStates
from .validation import validate_location
from ..keyboards.inline import start_inl


@state(state=BotStates.from_location)
@validate_location
async def from_location_state_handler(message: Message, state: StateContext, validated_data: dict):
    h = UltraHandler(message, state)
    lang = await h.lang()

    if validated_data.get("action") == "btn.back":
        return await order_callback(message, state)
    await h.delete(count=2)
    await h.set_state(BotStates.to_location, {"from_location": validated_data})
    await h.send("travel_end.text", reply_markup=start_inl(lang))


@state(state=BotStates.to_location)
@validate_location
async def to_location_state_handler(message: Message, state: StateContext, validated_data: dict):
    h = UltraHandler(message, state)
    lang = await h.lang()

    if validated_data.get("action") == "btn.back":
        await h.delete(count=2)
        return await now_callback(message, state)

    await h.set_state(BotStates.to_location, {"to_location": validated_data})
    await h.send("travel_end.text", reply_markup=start_inl(lang))