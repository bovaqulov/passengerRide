import json

from application.bot_app.keyboards.inline import in_car_inl, rate_trip_inl
from application.core import bot, t


async def driver_response(request):
    notify = await request.body()
    data = json.loads(notify)
    print(data)
    driver = data.get('driver_details', {})
    car = driver.get('cars', [])[0]
    content_object = data.get('content_object', {})
    lang = data.get("creator", {}).get("language", "uz")

    if data.get("status") == "assigned":
        text = t("find_driver", lang,
                 order_id=data.get("id", 0),
                 full_name=driver.get('full_name', None),
                 car_model=car.get('car_model', None),
                 car_number=car.get('car_number', None),
                 phone=driver.get('phone', None),
                 rating=driver.get('rating', None),
                 from_city=driver.get('from_location', "").title(),
                 to_city=driver.get('to_location', "").title(),
                 passenger=content_object.get('passenger', None),
                 price=content_object.get('price', None))

        try:
            await bot.send_message(
                chat_id=data["user"],
                text=text)
        except Exception as e:
            print(e)

    if data.get("status") == "arrived":
        text_arrived = t("driver_arrived", lang)
        try:
            await bot.send_message(
                data["user"],
                text_arrived,
                reply_markup=in_car_inl(lang, order_id=data["id"])
            )
        except Exception as e:
            print(e)

    if data.get("status") == "ended":
        text_ended = t("rate_trip", lang)
        try:
            await bot.send_message(
                data["user"],
                text_ended,
                reply_markup=rate_trip_inl(lang, order_id=data["content_object"]['id'])
            )
        except Exception as e:
            print(e)


