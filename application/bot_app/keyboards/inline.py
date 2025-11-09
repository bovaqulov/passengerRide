from application.bot_app.keyboards.base import kb


def main_menu_inl(lang: str):
    return (kb(lang)
            .data("main_menu.btn.order", "order")
            .row()
            .data("main_menu.btn.my_trip", "my_trip")
            .row()
            .data("main_menu.btn.help", "help")
            .inline()
            )


def order_inl(lang: str):
    return (kb(lang)
            .data("travel_type.btn.now", "now")
            .row()
            .data("travel_type.btn.post", "post")
            .row()
            .data("btn.back", "back")
            .inline()
            )


def start_inl(lang: str):
    return (kb(lang)
            .rb("btn.back")
            .rb("travel_locations.send_location", location=True)
            .row()
            .rb("travel_locations.tashkent")
            .rb("travel_locations.qoqon")
            .row()
            .rb("travel_locations.andijan")
            .rb("travel_locations.namangan")
            .row()
            .rb("travel_locations.fargona")
            .reply())
