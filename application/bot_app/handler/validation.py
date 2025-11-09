import re
from abc import ABC, abstractmethod
from functools import wraps
from typing import Dict, List, Optional, Tuple, Union, Callable

from telebot.states.asyncio import StateContext
from telebot.types import Message

from application.bot_app.handler import UltraHandler
from application.core.i18n import detect_slug


class BaseValidator(ABC):
    """Asosiy validator abstract class"""

    @abstractmethod
    async def validate(self, message: Message, lang: str, **kwargs) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Asosiy validatsiya metodi

        Returns:
            Tuple[is_valid, validated_data, error_key]
        """
        pass

    @staticmethod
    def detect_action(message: Message, lang: str, action_keys: List[str] = None) -> Optional[str]:
        """Actionlarni aniqlash (back, cancel, etc)"""
        if not message.text:
            return None

        detected_slug = detect_slug(message.text, lang)
        action_keys = action_keys or ["btn.back", "btn.cancel"]
        print(detected_slug)
        return detected_slug if detected_slug in action_keys else None


class LocationValidator(BaseValidator):
    """Location validator"""

    SUPPORTED_CITIES = {
        "uz": {
            "travel_locations.tashkent": "Toshkent",
            "travel_locations.andijan": "Andijon",
            "travel_locations.namangan": "Namangan",
            "travel_locations.fargona": "Farg'ona",
            "travel_locations.qoqon": "Qo'qon"},
        "ru": {
            "travel_locations.tashkent": "Ташкент",
            "travel_locations.andijan": "Андижан",
            "travel_locations.namangan": "Наманган",
            "travel_locations.fargona": "Фергана",
            "travel_locations.qoqon": "Коканд",
        },
        "en": {
            "travel_locations.tashkent": "Tashkent",
            "travel_locations.andijan": "Andijan",
            "travel_locations.namangan": "Namangan",
            "travel_locations.fargona": "Fergana",
            "travel_locations.qoqon": "Kokand"
        }
    }

    async def validate(self, message: Message, lang: str, **kwargs) -> Tuple[bool, Optional[Dict], Optional[str]]:
        # Action ni tekshirish
        action = self.detect_action(message, lang, ["btn.back", "btn.cancel"])
        if action:
            return True, {"action": action}, None

        # Location tekshirish
        if message.location:
            from .utills import aget_place_from_coords
            address = await aget_place_from_coords(message.location.latitude, message.location.longitude)
            return True, {
                "address": address.get("full_address"),
                "lat": message.location.latitude,
                "lng": message.location.longitude,
                "source": "location"
            }, None

        # Matn tekshirish (shahar nomi)
        if message.text:
            detected_slug = detect_slug(message.text, lang)

            if detected_slug in self.SUPPORTED_CITIES.get(lang).keys():

                from .utills import aget_coords_from_place
                city_name = self.SUPPORTED_CITIES[lang][detected_slug]
                locations = await aget_coords_from_place(city_name)

                if locations and locations[0].get('lat') and locations[0].get('lon'):
                    return True, {
                        "address": locations[0].get('full_address', city_name),
                        "lat": locations[0]['lat'],
                        "lng": locations[0]['lon'],
                        "source": "city_name"
                    }, None
                return False, None, "errors.city_not_found"

            return False, None, "errors.unknown_city"

        return False, None, "errors.invalid_input"


class TextValidator(BaseValidator):
    """Matn validatori"""

    def __init__(self, min_length: int = 1, max_length: int = 1000, allowed_pattern: str = None):
        self.min_length = min_length
        self.max_length = max_length
        self.allowed_pattern = allowed_pattern

    async def validate(self, message: Message, lang: str, **kwargs) -> Tuple[bool, Optional[Dict], Optional[str]]:
        action = self.detect_action(message, lang)
        if action:
            return True, {"action": action}, None

        if not message.text:
            return False, None, "errors.text_required"

        text = message.text.strip()

        if len(text) < self.min_length:
            return False, None, "errors.text_too_short"

        if len(text) > self.max_length:
            return False, None, "errors.text_too_long"

        if self.allowed_pattern and not re.match(self.allowed_pattern, text):
            return False, None, "errors.invalid_format"

        return True, {"text": text, "cleaned_text": text.strip()}, None


class PhoneValidator(BaseValidator):
    """Telefon raqam validatori"""

    async def validate(self, message: Message, lang: str, **kwargs) -> Tuple[bool, Optional[Dict], Optional[str]]:
        action = self.detect_action(message, lang)
        if action:
            return True, {"action": action}, None

        if message.contact:
            phone = message.contact.phone_number
        elif message.text:
            phone = message.text.strip()
        else:
            return False, None, "errors.phone_required"

        # Telefon raqamini tozalash va validatsiya
        cleaned_phone = self.clean_phone(phone)
        if not self.is_valid_phone(cleaned_phone):
            return False, None, "errors.invalid_phone"

        return True, {"phone": cleaned_phone, "source": "contact" if message.contact else "text"}, None

    @staticmethod
    def clean_phone(phone: str) -> str:
        """Telefon raqamini tozalash"""
        return ''.join(filter(str.isdigit, phone))

    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """Telefon raqamini tekshirish"""
        return len(phone) >= 9 and phone.startswith(
            ('+', '998', '9', '33', '88', '90', '91', '93', '94', '95', '97', '98', '99'))


class NumberValidator(BaseValidator):
    """Raqam validatori"""

    def __init__(self, min_value: float = None, max_value: float = None):
        self.min_value = min_value
        self.max_value = max_value

    async def validate(self, message: Message, lang: str, **kwargs) -> Tuple[bool, Optional[Dict], Optional[str]]:
        action = self.detect_action(message, lang)
        if action:
            return True, {"action": action}, None

        if not message.text:
            return False, None, "errors.number_required"

        try:
            number = float(message.text)
        except ValueError:
            return False, None, "errors.invalid_number"

        if self.min_value is not None and number < self.min_value:
            return False, None, "errors.number_too_small"

        if self.max_value is not None and number > self.max_value:
            return False, None, "errors.number_too_large"

        return True, {"number": number, "int_number": int(number) if number.is_integer() else number}, None


# Validator registry
VALIDATOR_REGISTRY = {
    "location": LocationValidator,
    "text": TextValidator,
    "phone": PhoneValidator,
    "number": NumberValidator,
}


def validate_with(validator: Union[str, BaseValidator], **validator_kwargs):
    """
    Validator decorator

    Args:
        validator: Validator nomi yoki instance
        validator_kwargs: Validator parametrlari
    """

    def decorator(handler_func: Callable):
        @wraps(handler_func)
        async def wrapper(message: Message, state: StateContext, *args, **kwargs):
            h = UltraHandler(message, state)
            lang = await h.lang()

            # Validator ni yaratish
            if isinstance(validator, str):
                validator_class = VALIDATOR_REGISTRY.get(validator)
                if not validator_class:
                    raise ValueError(f"Unknown validator: {validator}")
                validator_instance = validator_class(**validator_kwargs)
            else:
                validator_instance = validator

            # Validatsiya qilish
            is_valid, validated_data, error_key = await validator_instance.validate(message, lang, **validator_kwargs)

            if not is_valid:
                await h.send(error_key or "errors.validation_error")
                return

            # Validated data ni handler ga uzatish
            kwargs['validated_data'] = validated_data
            return await handler_func(message, state, *args, **kwargs)

        return wrapper

    return decorator


# Qisqa variantlar
def validate_location(handler_func: Callable):
    """Location validator decorator"""
    return validate_with("location")(handler_func)


def validate_text(min_length: int = 1, max_length: int = 1000, pattern: str = None):
    """Text validator decorator"""
    return validate_with("text", min_length=min_length, max_length=max_length, allowed_pattern=pattern)


def validate_phone(handler_func: Callable):
    """Phone validator decorator"""
    return validate_with("phone")(handler_func)


def validate_number(min_value: float = None, max_value: float = None):
    """Number validator decorator"""
    return validate_with("number", min_value=min_value, max_value=max_value)
