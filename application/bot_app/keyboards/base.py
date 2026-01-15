from typing import Optional, List, Union
from dataclasses import dataclass
from telebot.types import (
    InlineKeyboardMarkup, ReplyKeyboardMarkup,
    InlineKeyboardButton, KeyboardButton, ReplyKeyboardRemove, WebAppInfo
)
from application.core.i18n import t as _


@dataclass
class InlineButton:
    """Inline tugma konfiguratsiyasi"""
    text: str
    callback_data: Optional[str] = None
    url: Optional[str] = None
    web_app: WebAppInfo = None
    pay: bool = False



@dataclass
class ReplyButton:
    """Reply tugma konfiguratsiyasi"""
    text: str
    request_contact: bool = False
    request_location: bool = False


class SimpleKeyboard:
    """Soddalashtirilgan keyboard builder"""

    def __init__(self, lang: str = "uz"):
        self.lang = lang
        self._inline_rows: List[List[InlineButton]] = []
        self._reply_rows: List[List[Union[ReplyButton, str]]] = []
        self._current_inline_row: List[InlineButton] = []
        self._current_reply_row: List[Union[ReplyButton, str]] = []

    # ============ INLINE TUGMALAR ============

    def ib(self, text: str, data = None, url: str = None) -> 'SimpleKeyboard':
        """Inline tugma qo'shish"""
        self._current_inline_row.append(InlineButton(text, callback_data=data, url=url))
        return self

    def url(self, text: str, url: str) -> 'SimpleKeyboard':
        """URL tugma"""
        return self.ib(text, url=url)

    def data(self, text: str, data: str) -> 'SimpleKeyboard':
        """Callback data tugma"""
        return self.ib(text, data=data)

    def web_app(self, text: str, web_app_url: str) -> 'SimpleKeyboard':
        """Web app tugma"""
        self._current_inline_row.append(InlineButton(text, web_app=WebAppInfo(web_app_url)))
        return self

    # ============ REPLY TUGMALAR ============

    def rb(self, text: str, contact: bool = False, location: bool = False) -> 'SimpleKeyboard':
        """Reply tugma qo'shish"""
        if contact or location:
            self._current_reply_row.append(ReplyButton(text, request_contact=contact, request_location=location))
        else:
            self._current_reply_row.append(text)
        return self

    def contact(self, text: str = "send.contact") -> 'SimpleKeyboard':
        """Contact tugma"""
        return self.rb(_(text, self.lang), contact=True)

    def location(self, text: str = "send.location") -> 'SimpleKeyboard':
        """Location tugma"""
        return self.rb(_(text, self.lang), location=True)

    def text(self, text: str) -> 'SimpleKeyboard':
        """Oddiy text tugma"""
        return self.rb(_(text, self.lang))

    # ============ QATOR OPERATSIYALARI ============

    def row(self) -> 'SimpleKeyboard':
        """Yangi qator"""
        if self._current_inline_row:
            self._inline_rows.append(self._current_inline_row)
            self._current_inline_row = []
        if self._current_reply_row:
            self._reply_rows.append(self._current_reply_row)
            self._current_reply_row = []
        return self

    def add_rows(self, *rows: List[str]) -> 'SimpleKeyboard':
        """Bir nechta qatorlarni bir vaqtda qo'shish"""
        for row in rows:
            for text in row:
                self.rb(text)
            self.row()
        return self

    # ============ YASASH METODLARI ============

    def inline(self, row_width: int = 2) -> InlineKeyboardMarkup:
        """Inline keyboard yasash"""
        self._finalize_rows()
        markup = InlineKeyboardMarkup(row_width=row_width)
        for row in self._inline_rows:
            buttons = []
            for btn in row:
                text = _(btn.text, self.lang) if not btn.url else btn.text

                if btn.callback_data:
                    buttons.append(InlineKeyboardButton(text, callback_data=btn.callback_data))
                elif btn.url:
                    buttons.append(InlineKeyboardButton(text, url=btn.url))
                elif btn.web_app:
                    buttons.append(InlineKeyboardButton(text, web_app=btn.web_app))
                elif btn.pay:
                    buttons.append(InlineKeyboardButton(text, pay=True))

            if buttons:
                markup.add(*buttons)

        return markup

    def reply(self, resize: bool = True, one_time: bool = False,
              selective: bool = False) -> ReplyKeyboardMarkup:
        """Reply keyboard yasash"""
        self._finalize_rows()

        markup = ReplyKeyboardMarkup(
            resize_keyboard=resize,
            one_time_keyboard=one_time,
            selective=selective
        )

        for row in self._reply_rows:
            buttons = []
            for btn in row:
                if isinstance(btn, ReplyButton):
                    text = _(btn.text, self.lang)
                    if btn.request_contact:
                        buttons.append(KeyboardButton(text, request_contact=True))
                    elif btn.request_location:
                        buttons.append(KeyboardButton(text, request_location=True))
                    else:
                        buttons.append(KeyboardButton(text))
                else:
                    buttons.append(KeyboardButton(_(btn, self.lang)))

            if buttons:
                markup.row(*buttons)

        return markup

    def _finalize_rows(self) -> None:
        """Qatorlarni yakunlash"""
        if self._current_inline_row:
            self._inline_rows.append(self._current_inline_row)
            self._current_inline_row = []
        if self._current_reply_row:
            self._reply_rows.append(self._current_reply_row)
            self._current_reply_row = []

    def clear(self) -> 'SimpleKeyboard':
        """Keyboardlarni tozalash"""
        self._inline_rows.clear()
        self._reply_rows.clear()
        self._current_inline_row.clear()
        self._current_reply_row.clear()
        return self

    def copy(self) -> 'SimpleKeyboard':
        """Nusxa olish"""
        new_kb = SimpleKeyboard(self.lang)
        new_kb._inline_rows = self._inline_rows.copy()
        new_kb._reply_rows = self._reply_rows.copy()
        new_kb._current_inline_row = self._current_inline_row.copy()
        new_kb._current_reply_row = self._current_reply_row.copy()
        return new_kb


# ==================== TEZKOR FUNKSIYALAR ====================

def kb(lang: str = "uz") -> SimpleKeyboard:
    """Asosiy keyboard builder"""
    return SimpleKeyboard(lang)


def remove_keyboard(selective: bool = False) -> ReplyKeyboardRemove:
    """Keyboardni olib tashlash"""
    return ReplyKeyboardRemove(selective=selective)


def quick_reply(*buttons: List[str], lang: str = "uz",
                resize: bool = True, one_time: bool = False) -> ReplyKeyboardMarkup:
    """Tezkor reply keyboard"""
    keyboard = kb(lang)
    keyboard.add_rows(*buttons)
    return keyboard.reply(resize=resize, one_time=one_time)


def quick_inline(buttons: List[List[tuple]], lang: str = "uz",
                 row_width: int = 2) -> InlineKeyboardMarkup:
    """Tezkor inline keyboard"""
    keyboard = kb(lang)
    for row in buttons:
        for text, data in row:
            if data.startswith('http'):
                keyboard.url(text, data)
            else:
                keyboard.data(text, data)
        keyboard.row()
    return keyboard.inline(row_width=row_width)