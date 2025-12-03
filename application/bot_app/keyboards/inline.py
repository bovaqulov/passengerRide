from application.bot_app.keyboards.base import kb
from application.core.i18n import t
from application.services.city_service import CityServiceAPI


def main_menu_inl(lang: str):
    slug = "main_menu.btn"
    return (kb(lang)
            .data(f"{slug}.order", "order")
            .row()
            .data(f"{slug}.my_trip", "my_trip")
            .row()
            .data(f"{slug}.help", "help")
            .inline())


def order_inl(lang: str):
    slug = "travel_type.btn"
    return (kb(lang)

            .data(f"{slug}.now", "now")
            .row()
            .data(f"{slug}.post", "post")
            .row()
            .data("btn.back", "back")
            .inline())


async def start_inl(lang: str, no_city: str = None, location = True):
    """Shahar tanlash klaviaturasi"""
    city_api = CityServiceAPI()
    cities = await city_api.get_title_category(lang)

    keyboard = kb(lang)
    keyboard.data("btn.back", "back_city")
    keyboard.row()
    if location:
        keyboard.data("send_location", "city_location")
        keyboard.row()

    for title, name in cities:
        if title != no_city:
            keyboard.data(name, f'city_{title}')

    return keyboard.inline(row_width=2)


def details_inl(
        lang: str,
        passenger_count: int = 1,
        has_woman: bool = False,
        travel_class: str = "standard"
):
    """
    Sayohat tafsilotlari klaviaturasi

    MUHIM: Callback data nomlari handler bilan mos bo'lishi kerak:
    - passenger:{count}
    - has_woman:{value}
    - travel_class:{class_name}
    """
    check = "✅"
    keyboard = kb(lang)
    for count in [1, 2, 3, 4]:
        text_key = f"👤 {count}"
        checked = check if passenger_count == count else ""
        text = f"{text_key} {checked}"
        keyboard.data(text, f"passenger:{count}")

    keyboard.row()

    text = f'{t("female_passenger", lang)} {t("yes", lang)}' \
        if has_woman else \
        f'{t("female_passenger", lang)} {t("no", lang)}'

    keyboard.data(text, f"has_woman:{not has_woman}").row()
    keyboard.row()

    for car_class in ["economy", "standard", "business"]:
        checked = check if travel_class == car_class else ""
        text = f"{t(f'btn.{car_class}', lang)} {checked}"
        keyboard.data(text, f"travel_class:{car_class}")


    keyboard.row()

    # Navigatsiya
    keyboard.data("btn.back", "back_details")
    keyboard.data("btn.start", "details_start")

    return keyboard.inline(row_width=2)


def cancel_inl(lang: str, travel_id):
    keyboard = kb(lang)
    keyboard.data("btn.action_cancel", f"cancel_{travel_id}")
    return keyboard.inline()


def cancel_post_inl(lang: str, post_id):
    keyboard = kb(lang)
    keyboard.data("btn.action_cancel", f"can_post_{post_id}")
    return keyboard.inline()


def language_inl(lang: str):
    keyboard = kb(lang)
    keyboard.data("languages.uz", "lang_uz").row()
    keyboard.data("languages.ru", "lang_ru").row()
    keyboard.data("languages.en", "lang_en").row()
    return keyboard.inline()


def phone_number_rb(lang: str):
    keyboard = kb(lang)
    keyboard.contact("ask_phone_number.btn")
    return keyboard.reply()


def recreate_inl(lang: str):
    keyboard = kb(lang)
    keyboard.data("btn.restart", f"restart").row()
    keyboard.data("btn.back", f"back").row()
    return keyboard.inline()


def recreate_post_inl(lang: str):
    keyboard = kb(lang)
    keyboard.data("btn.restart", f"re_post_start").row()
    keyboard.data("btn.back", f"back").row()
    return keyboard.inline()


def start_post_inl(lang: str):
    keyboard = kb(lang)
    keyboard.data("btn.back", "post_back")
    keyboard.data("btn.start", "post_start")
    return keyboard.inline()


def back_inl(lang: str):
    keyboard = kb(lang)
    keyboard.data("btn.back", f"back").row()
    return keyboard.inline()

def location_btn(lang: str):
    keyboard = kb(lang)
    keyboard.rb("send_location", location=True).row()
    keyboard.rb("btn.back").row()
    return keyboard.reply()

def driver_connect_inl(lang: str):
    keyboard = kb(lang)
    keyboard.data("btn.back", f"back").row()
    keyboard.ib("contact_driver", "contact_driver").row()
    return keyboard.inline()

def in_car_inl(lang: str, order_id):
    keyboard = kb(lang)
    keyboard.data("in_car", f"in_car_{order_id}").row()
    return keyboard.inline()


def rate_trip_inl(lang: str, order_id):
    keyboard = kb(lang)
    for i in range(5, 0, -1):
        keyboard.data(str(i), f"rate_{i}_{order_id}")

    return keyboard.inline()
