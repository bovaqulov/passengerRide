from telebot.states.asyncio import StateContext
from telebot.types import CallbackQuery, Message

from .decorator import UltraHandler, BotStates, BotPostStates, state, cb
from ..keyboards.inline import start_inl, details_inl, cancel_inl, start_post_inl, cancel_post_inl, location_btn, \
    order_inl
from ...core import t, logger
from ...services.city_service import CityServiceAPI
from ...services.post_service import PassengerPostService
from ...services.ride_service import RideService


async def ask_location(call, state):
    h = UltraHandler(call, state)
    lang = await h.lang()
    await h.delete()
    await h.set_state(BotStates.from_location)
    await h.send(
        "location_request",
        reply_markup=location_btn(lang)
    )

async def ask_location_post(call, state):
    h = UltraHandler(call, state)
    lang = await h.lang()
    await h.delete()
    await h.set_state(BotPostStates.from_location)
    await h.send(
        "location_request",
        reply_markup=location_btn(lang)
    )

@state(state=BotStates.from_location)
async def from_location_state_handler(call: CallbackQuery, state: StateContext):
    from .callbacks import order_callback
    h = UltraHandler(call, state)
    lang = await h.lang()

    city_api = CityServiceAPI()

    if isinstance(call, Message):
        if call.location:
            result = await city_api.check_location_in_allowed_city(call.location.latitude, call.location.longitude,
                                                                   max_distance_km=45.0)
            if result["success"]:
                city_name = result['city_name']
            else:
                if result["error"] in ["city_not_allowed", "no_city_found"]:
                    await h.delete()
                    await h.clear_state()
                    return h.send(
                        "errors.service_not_available",
                        reply_markup=order_inl(lang)
                    )
                else:
                    city_name = result["nearest_city"]
        else:
            await h.delete()
            await h.clear_state()
            await h.set_state(BotStates.from_location)
            return await h.send(
                "errors.send_exact_location",
                reply_markup=await start_inl(lang)
            )

        from_location = {"city": city_name,
                         "location": {"latitude": call.location.latitude, "longitude": call.location.longitude}}

    else:
        if call.data.endswith("back"):
            await h.clear_state()
            return await order_callback(call, state)

        if call.data.endswith("location"):
            return await ask_location(call, state)

        city = call.data.split("_")[-1]
        from_location = {"city": city, "location": None}

    await h.set_state(BotStates.to_location, {"from_location": from_location})
    await h.delete(count=2)
    return await h.send("travel_end.text", reply_markup=await start_inl(lang, from_location.get("city"), location=False))


@state(state=BotStates.to_location)
async def to_location_state_handler(call: [CallbackQuery, Message], state: StateContext):
    from .callbacks import now_callback
    h = UltraHandler(call, state)
    lang = await h.lang()
    city_api = CityServiceAPI()

    async with state.data() as data:
        loc_begin = data.get("from_location", {})

    if call.data.endswith("back"):
        return await now_callback(call, state)

    city = call.data.split("_")[-1]
    to_location = {"city": city, "location": None}

    await h.set_state(BotStates.details, {
        "to_location": to_location,
        "travel_class": "standard",
        "passenger": 1,
        "has_woman": False})

    await h.delete()
    await h.send("trip_details.text",
                 reply_markup=details_inl(lang, 1, False, "standard"),
                 loc_begin=await city_api.get_translate(loc_begin.get("city"), lang),
                 loc_end=await city_api.get_translate(to_location.get("city"), lang),
                 passenger=1,
                 travel_class=t("btn.standard", lang),
                 price=calculate_distance(loc_begin.get("city"), to_location.get("city"), tur="standard"),
                 has_woman="❌ ")


def calculate_distance(shahar1, shahar2, tur="economy"):
    CITY_PRICES = {
        "qoqon": {"distance": 230, "economy": 130000, "standard": 200000, "comfort": 230000},
        "fargona": {"distance": 305, "economy": 180000, "standard": 250000, "comfort": 270000},
        "namangan": {"distance": 281, "economy": 170000, "standard": 240000, "comfort": 260000},
        "andijon": {"distance": 345, "economy": 200000, "standard": 270000, "comfort": 290000}
    }
    # Toshkentdan boshqa shaharga
    if shahar1 == "tashkent" and shahar2 in CITY_PRICES:
        return CITY_PRICES[shahar2][tur]

    # Boshqa shahardan Toshkentga
    elif shahar2 == "tashkent" and shahar1 in CITY_PRICES:
        return CITY_PRICES[shahar1][tur]

    # Ikki shahar o'rtasida
    elif shahar1 in CITY_PRICES and shahar2 in CITY_PRICES:
        narx1 = CITY_PRICES[shahar1][tur]
        narx2 = CITY_PRICES[shahar2][tur]
        return (narx1 + narx2) // 2
    else:
        return 150_000


@state(state=BotStates.details)
async def details_state_handler(call: CallbackQuery, state: StateContext):
    h = UltraHandler(call, state)
    lang = await h.lang()

    city_api = CityServiceAPI()

    async with state.data() as data:
        from_location = data.get("from_location", {})
        to_location = data.get("to_location", {})
        travel_class = data.get("travel_class", "standard")
        passenger = data.get("passenger", 1)
        has_woman = data.get("has_woman", False)

    action = call.data.split(":")

    if action[0] == "back_details":
        await h.clear_state()
        from .callbacks import now_callback
        return await now_callback(call, state)
    elif action[0] == "details_start":
        base_price = calculate_distance(from_location.get("city"), to_location.get("city"), travel_class)
        total_price = base_price * passenger
        data.update({"price": total_price})
        return await confirm_order(call, state, data)
    elif action[0] == "passenger":
        passenger = int(action[1])
    elif action[0] == "has_woman":
        has_woman = action[1].lower() == "true"
    elif action[0] == "travel_class":
        travel_class = action[1]

    # Calculate price
    base_price = calculate_distance(from_location.get("city"), to_location.get("city"), travel_class)
    total_price = base_price * passenger

    # Update state with new data
    await h.set_state(BotStates.details, {
        "from_location": from_location,
        "to_location": to_location,
        "travel_class": travel_class,
        "passenger": passenger,
        "has_woman": has_woman,
        "price": total_price,
    })

    await h.edit(
        "trip_details.text",
        reply_markup=details_inl(lang, passenger, has_woman, travel_class),
        loc_begin=await city_api.get_translate(from_location.get("city"), lang),
        loc_end=await city_api.get_translate(to_location.get("city"), lang),
        passenger=passenger,
        travel_class=t(f"btn.{travel_class}", lang),
        price=total_price,
        has_woman="✅" if has_woman else "❌"
    )


async def confirm_order(call: CallbackQuery, state: StateContext, data: dict):
    h = UltraHandler(call, state)
    lang = await h.lang()
    data.update({"user": call.from_user.id})
    result = await RideService().create_travel(data)

    await h.clear_state()
    await h.edit(
        "travel_searching_drivers.text",
        reply_markup=cancel_inl(lang, result.get("order_id")),
    )
    logger.info(f"Created new travel {result}")


@state(state=BotPostStates.from_location)
async def post_from_location_state_handler(call: CallbackQuery, state: StateContext):
    from . import order_callback
    h = UltraHandler(call, state)
    lang = await h.lang()

    city_api = CityServiceAPI()

    if isinstance(call, Message):
        if call.location:
            result = await city_api.check_location_in_allowed_city(call.location.latitude, call.location.longitude,
                                                                   max_distance_km=45.0)
            if result["success"]:
                city_name = result['city_name']
            else:
                if result["error"] in ["city_not_allowed", "no_city_found"]:
                    await h.delete()
                    await h.clear_state()
                    return h.send(
                        "errors.service_not_available",
                        reply_markup=order_inl(lang)
                    )
                else:
                    city_name = result["nearest_city"]
        else:
            await h.delete()
            await h.clear_state()
            await h.set_state(BotPostStates.from_location)
            return await h.send(
                "errors.send_exact_location",
                reply_markup=await start_inl(lang)
            )

        from_location = {"city": city_name,
                         "location":
                             {
                                 "latitude": call.location.latitude,
                                 "longitude": call.location.longitude
                             }
                         }
    else:

        if call.data.endswith("back"):
            await h.clear_state()
            return await order_callback(call, state)

        if call.data.endswith("location"):
            return await ask_location_post(call, state)

        city = call.data.split("_")[-1]
        from_location = {"city": city, "location": None}

    await h.delete()
    await h.set_state(BotPostStates.to_location, {"from_location": from_location})
    return await h.send("parcel_pickup.text", reply_markup=await start_inl(lang, from_location.get("city"), location=False))


@state(state=BotPostStates.to_location)
async def post_to_location_state_handler(call: CallbackQuery, state: StateContext):
    h = UltraHandler(call, state)
    lang = await h.lang()

    to_loc = call.data.split("_")[-1]
    to_location = {"city": to_loc, "location": None}
    async with state.data() as data:
        from_location = data.get("from_location", {})

    price = int(calculate_distance(from_location.get("city"), to_loc, tur="economy") / 2)

    await h.set_state(BotPostStates.confirm, {
        "to_location": to_location,
        "price": price
    })

    return await h.edit(
        "delivery_price_confirm.text",
        reply_markup=start_post_inl(lang),
        price=price
    )


@cb(state=BotPostStates.confirm, pattern="post_")
async def confirm_callback_inline(call: CallbackQuery, state: StateContext):
    h = UltraHandler(call, state)
    lang = await h.lang()

    print(call.data)

    if call.data == "post_start":
        async with state.data() as data:
            from_location = data.get("from_location", {})
            to_location = data.get("to_location", {})
            price = data.get("price", 0)

            result = await PassengerPostService().create_post(
                {
                    'from_location': from_location,
                    'to_location': to_location,
                    'price': price,
                    'user': call.from_user.id,
                }
            )

            await h.clear_state()
            post_id = result.get("order_id")
            return await h.edit(
                "parcel_fast_pickup.text",
                reply_markup=cancel_inl(lang, post_id),
            )

    else:
        await h.clear_state()
        from . import order_callback
        return await order_callback(call, state)


__all__ = [
    "from_location_state_handler",
    "to_location_state_handler",
    "details_state_handler",
    "confirm_order"
]
