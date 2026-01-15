
from application.bot_app.keyboards.base import kb


def main_menu_inl(lang: str):
    return (kb(lang)
            .web_app(f"order", "https://goz-ride-easy.vercel.app/")
            .row()
            .data(f"my_trip", "my_trip")
            .row()
            .data(f"help", "help")
            .inline())


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


def back_inl(lang: str):
    keyboard = kb(lang)
    keyboard.data("btn.back", f"back").row()
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