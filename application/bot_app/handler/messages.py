import re

from telebot import types
from telebot.states.asyncio import StateContext

from application.bot_app.handler import msg, UltraHandler
from application.bot_app.handler.decorator import BotNumber
from application.bot_app.keyboards.inline import phone_number_rb, main_menu_inl
from application.services.passenger_service import PassengerServiceAPI, PassengerCreateService
from application.services.sms_service import SmsService


@msg(content_types=['text', "contact"], state=BotNumber.contact)
async def create_user_number(message: types.Message, state: StateContext):
    try:
        h = UltraHandler(message, state)
        lang = await h.lang()
        if message.contact:
            number = message.contact.phone_number
        else:
            if re.match("^[+]998([0-9][012345789]|[0-9][125679]|7[01234569])[0-9]{7}$", message.text):
                number = message.text
            else:
                await h.set_state(BotNumber.contact)
                return await h.send(
                    "error.invalid_phone",
                    reply_markup=phone_number_rb(lang)
                )
        await h.clear_state()

        result = await SmsService().send_sms(message.from_user.id, number)

        if result.get("status") == "success":
            await h.set_state(BotNumber.confirm_code,
                              {
                                  "code": result.get("result", {}).get("sms_code"),
                                  "phone": number
                              }
                              )
            return await h.send("enter_sms_code")
        else:
            return await h.send(
                "Error, Please try again later",
            )
    except Exception as e:
        print(e)


@msg(content_types=['text', "contact"], state=BotNumber.confirm_code)
async def confirm_code(message: types.Message, state: StateContext):
    h = UltraHandler(message, state)
    lang = await h.lang()
    data = await h.get_data()

    if message.text.isdigit():
        if int(message.text) == data.get("code"):
            await h.clear_state()
            await PassengerServiceAPI().create(passenger=PassengerCreateService(
                telegram_id=message.from_user.id,
                full_name=message.from_user.full_name,
                phone=data.get("phone")
            ))

            await h.delete(count=2)
            return await h.send(
                "main_menu",
                reply_markup=main_menu_inl(lang),
                name=message.from_user.full_name
            )
        else:
            await h.set_state(BotNumber.confirm_code)
            return await h.send(
            )
    else:
        await h.set_state(BotNumber.confirm_code)
        return await h.send(
            "error.invalid_format",
        )


