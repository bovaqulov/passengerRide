from typing import Union

from telebot.states.sync import StateContext
from telebot.types import CallbackQuery, Message


from .decorator import cb, UltraHandler, BotStates, BotNumber, BotPostStates
from ..keyboards.inline import order_inl, main_menu_inl, start_inl, phone_number_rb, recreate_inl, \
    back_inl
from ...core import t, logger
from ...services import TelegramUser, RideService
from ...services.city_service import CityServiceAPI
from ...services.order_service import OrderServiceAPI
from ...services.passenger_service import PassengerServiceAPI


@cb("lang_")
async def callback_lang(call: CallbackQuery, state: StateContext):
    h = UltraHandler(call, state)

    main_lang = call.data.split("_")[-1]
    await TelegramUser().update_user(telegram_id=call.from_user.id, update_data={"language": main_lang})

    # Passenger ni tekshirish
    passenger_api = PassengerServiceAPI()
    passenger = await passenger_api.get_by_user(call.from_user.id)

    if not passenger or not passenger.phone:
        await h.delete()
        await h.set_state(BotNumber.contact)
        return await h.send(
            "ask_phone_number.text",
            reply_markup=phone_number_rb(lang=main_lang)
        )

    # Agar passenger bor va telefon raqami bo'lsa
    lang = await h.lang()
    await h.edit(
        "main_menu.text",
        reply_markup=main_menu_inl(lang),
        name=passenger.full_name or call.from_user.full_name
    )


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

    backs = call.data.split("_")
    lang = await h.lang()
    user = await h.get_user()
    await h.clear_state()

    if len(backs) == 1:
        return await h.edit(
            "main_menu.text",
            reply_markup=main_menu_inl(lang),
            name=user.full_name)

    elif backs[-1] == "details":
        return await now_callback(call, state)

    elif backs[-1] == "city":
        return await order_callback(call, state)


@cb("now")
async def now_callback(call: Union[CallbackQuery, Message], state: StateContext):
    h = UltraHandler(call, state)
    lang = await h.lang()

    order_service = OrderServiceAPI()

    # Use the shared service instance
    orders = await order_service.get_by_id(call.from_user.id)

    if not orders:
        await h.set_state(stat=BotStates.from_location)
        return await h.edit(
            "travel_start.text",
            reply_markup=await start_inl(lang)
        )

    # Check if any order has active status
    active_statuses = ["created", "assigned", "arrived", "started"]
    has_active_order = any(
        order.get("status") in active_statuses
        for order in orders
    )

    if has_active_order:
        return await h.edit(
            "active_order",
            reply_markup=back_inl(lang)
        )
    else:
        await h.set_state(stat=BotStates.from_location)
        return await h.edit(
            "travel_start.text",
            reply_markup=await start_inl(lang)
        )

@cb("post")
async def post_callback(call: Union[CallbackQuery, Message], state: StateContext):
    h = UltraHandler(call, state)
    lang = await h.lang()

    orders = await OrderServiceAPI().get_by_id(call.from_user.id)

    for i in orders:
        if i.get("status") not in ["created", "assigned", "arrived", "started"]:
            await h.set_state(stat=BotPostStates.from_location)
            return await h.edit(
                "parcel_destination.text",
                reply_markup=await start_inl(lang),
            )
        else:
            return await h.edit(
                "active_order",
                reply_markup=back_inl(lang)
        )

@cb("in_car")
async def in_car_callback(call: Union[CallbackQuery, Message], state: StateContext):
    h = UltraHandler(call, state)
    data, _, order_id = call.data.split("_")
    await OrderServiceAPI().update_status(order_id, "started")
    await h.edit(
        "safe_trip"
    )



@cb("cancel_")
async def cancel_callback(call: Union[CallbackQuery, Message], state: StateContext):
    h = UltraHandler(call, state)
    lang = await h.lang()
    order_id = int(call.data.split("_")[-1])
    await OrderServiceAPI().update_status(order_id, "rejected")
    await h.send(
        "trip_canceled.text",
        reply_markup=recreate_inl(lang)
    )


@cb("my_trip")
async def my_trip_callback(call: Union[CallbackQuery, Message], state: StateContext):
    h = UltraHandler(call, state)
    lang = await h.lang()
    city_api = CityServiceAPI()
    try:
        # Safarlarni olish
        trips: list = await RideService().get_user_travels(call.from_user.id)
        # Agar safarlar bo'sh bo'lsa
        if not trips:
            return await h.edit(
                t("utils.no_trips_found", lang=lang),
                reply_markup=back_inl(lang)
            )

        # Safar ma'lumotlarini shakllantirish
        text_parts = []
        for i, trip in enumerate(trips[:5], 1):  # Maksimum 5 ta safar
            trip_text = t("utils.travel_info", lang=lang,
                          code=trip["id"],
                          from_location=await city_api.get_translate(trip.get("from_location").get("city"), lang),
                          to_location=await city_api.get_translate(trip.get("to_location").get("city"), lang),
                          price=trip["price"],
                          date=trip["created_at"],
                          number=i)

            text_parts.append(trip_text)

        # Asosiy matn
        main_text = t("utils.my_trips_header", lang=lang, count=len(trips))
        full_text = main_text + "\n\n" + "\n\n".join(text_parts)

        # Agar ko'p safar bo'lsa, ogohlantirish
        if len(trips) > 5:
            full_text += f"\n\n{t('utils.more_trips_hidden', lang=lang)}"

        return await h.edit(
            full_text,
            reply_markup=back_inl(lang)
        )

    except Exception as e:
        logger.error(f"Error getting trips: {e}")
        return await h.edit(
            "utils.error_loading_trips",
            reply_markup=back_inl(lang)
        )

@cb("restart")
async def restart_callback(call: Union[CallbackQuery, Message], state: StateContext):
    await now_callback(call, state)

@cb("re_post_start")
async def restart_post_callback(call: Union[CallbackQuery, Message], state: StateContext):
    await post_callback(call, state)


@cb("rate")
async def rate_callback(call: Union[CallbackQuery, Message], state: StateContext):
    h = UltraHandler(call, state)
    lang = await h.lang()

    data, rate, travel_id = call.data.split("_")

    order_api = RideService()
    await order_api.update_travel(travel_id, {"rate": rate})
    await h.delete()

