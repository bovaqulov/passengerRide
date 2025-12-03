import math
from abc import ABC, abstractmethod
from functools import wraps
from typing import Dict, List, Optional, Tuple, Union, Callable, Any
from dataclasses import dataclass

from telebot.states.asyncio import StateContext
from telebot.types import Message

from application.bot_app.handler import UltraHandler
from application.core.i18n import detect_slug
from application.core.log import logger


# ==================== VALIDATION RESULT ====================

@dataclass
class ValidationResult:
    """Validatsiya natijasi"""
    is_valid: bool
    data: Optional[Dict[str, Any]] = None
    error_key: Optional[str] = None

    @classmethod
    def success(cls, data: Dict[str, Any] = None):
        """Muvaffaqiyatli validatsiya"""
        return cls(is_valid=True, data=data or {})

    @classmethod
    def error(cls, error_key: str, data: Dict[str, Any] = None):
        """Xatoli validatsiya"""
        return cls(is_valid=False, data=data, error_key=error_key)

    @classmethod
    def action(cls, action_type: str):
        """Action (back, cancel, etc)"""
        return cls(is_valid=True, data={"action": action_type})

    def to_tuple(self) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Eski formatga o'tkazish (backward compatibility)"""
        return self.is_valid, self.data, self.error_key


# ==================== BASE VALIDATOR ====================

class BaseValidator(ABC):
    """
    Asosiy validator abstract class.
    Barcha validatorlar ushbu klassdan meros oladi.
    """

    def __init__(self, required: bool = True, allow_actions: bool = True):
        """
        Args:
            required: Maydon majburiy yoki yo'q
            allow_actions: Action tugmalarni qabul qilish (back, cancel)
        """
        self.required = required
        self.allow_actions = allow_actions

    @abstractmethod
    async def validate(
            self,
            message: Message,
            state: StateContext,
            lang: str,
            **kwargs
    ) -> ValidationResult:
        """
        Asosiy validatsiya metodi.

        Args:
            message: Telegram message
            state: Bot state
            lang: Til kodi (uz, ru, en)
            **kwargs: Qo'shimcha parametrlar

        Returns:
            ValidationResult: Validatsiya natijasi
        """
        pass

    async def __call__(
            self,
            message: Message,
            state: StateContext,
            lang: str,
            **kwargs
    ) -> ValidationResult:
        """Validator ni chaqirish"""
        # Action tekshirish
        if self.allow_actions:
            action = self.detect_action(message, lang)
            if action:
                return ValidationResult.action(action)

        # Bo'sh qiymat tekshirish
        if self.required and self._is_empty(message):
            return ValidationResult.error("errors.required_field")

        # Asosiy validatsiya
        try:
            return await self.validate(message, state, lang, **kwargs)
        except Exception as e:
            logger.exception(f"Validation error in {self.__class__.__name__}: {e}")
            return ValidationResult.error("errors.validation_error")

    @staticmethod
    def detect_action(
            message: Message,
            lang: str,
            action_keys: List[str] = None
    ) -> Optional[str]:
        """
        Actionlarni aniqlash (back, cancel, skip, etc)

        Args:
            message: Telegram message
            lang: Til kodi
            action_keys: Action key lari ro'yxati

        Returns:
            Action key yoki None
        """
        if not message.text:
            return None

        action_keys = action_keys or ["btn.back", "btn.cancel", "btn.skip"]
        detected_slug = detect_slug(message.text, lang)

        return detected_slug if detected_slug in action_keys else None

    @staticmethod
    def _is_empty(message: Message) -> bool:
        """Message bo'sh ekanligini tekshirish"""
        if not message:
            return True

        # Text, location, photo, contact, etc tekshirish
        return not any([
            message.text and message.text.strip(),
            message.location,
            message.photo,
            message.document,
            message.contact,
            message.voice,
            message.video
        ])


# ==================== LOCATION VALIDATOR ====================

class LocationValidator(BaseValidator):
    """
    Location validator - geografik joylashuvni tekshiradi.

    Features:
    - GPS location qabul qiladi
    - Shahar nomini qabul qiladi
    - Bir xil shaharni tekshiradi
    - Distance calculation
    """

    # Qo'llab-quvvatlanadigan shaharlar
    SUPPORTED_CITIES = {
        "uz": {
            "travel_locations.tashkent": "Toshkent",
            "travel_locations.andijan": "Andijon",
            "travel_locations.namangan": "Namangan",
            "travel_locations.fargona": "Farg'ona",
            "travel_locations.qoqon": "Qo'qon",
            "travel_locations.samarkand": "Samarqand",
            "travel_locations.bukhara": "Buxoro",
        },
        "ru": {
            "travel_locations.tashkent": "Ташкент",
            "travel_locations.andijan": "Андижан",
            "travel_locations.namangan": "Наманган",
            "travel_locations.fargona": "Фергана",
            "travel_locations.qoqon": "Коканд",
            "travel_locations.samarkand": "Самарканд",
            "travel_locations.bukhara": "Бухара",
        },
        "en": {
            "travel_locations.tashkent": "Tashkent",
            "travel_locations.andijan": "Andijan",
            "travel_locations.namangan": "Namangan",
            "travel_locations.fargona": "Fergana",
            "travel_locations.qoqon": "Kokand",
            "travel_locations.samarkand": "Samarkand",
            "travel_locations.bukhara": "Bukhara",
        }
    }

    def __init__(
            self,
            check_duplicate: bool = True,
            max_distance_km: float = 50,
            **kwargs
    ):
        """
        Args:
            check_duplicate: Bir xil shaharni tekshirish
            max_distance_km: Maksimal masofa (km) - bir xil deb hisoblanishi uchun
        """
        super().__init__(**kwargs)
        self.check_duplicate = check_duplicate
        self.max_distance_km = max_distance_km

    async def validate(
            self,
            message: Message,
            state: StateContext,
            lang: str,
            **kwargs
    ) -> ValidationResult:
        """Location validatsiyasi"""

        # GPS location tekshirish
        if message.location:
            return await self._validate_gps_location(message, state, lang)

        # Matn (shahar nomi) tekshirish
        if message.text:
            return await self._validate_text_location(message, state, lang)

        return ValidationResult.error("errors.invalid_input")

    async def _validate_gps_location(
            self,
            message: Message,
            state: StateContext,
            lang: str
    ) -> ValidationResult:
        """GPS location validatsiyasi"""
        from .utills import aget_place_from_coords

        try:
            # Koordinatalardan manzilni olish
            address = await aget_place_from_coords(
                message.location.latitude,
                message.location.longitude
            )

            address_data = {
                "address": address.get("full_address", "Unknown location"),
                "lat": message.location.latitude,
                "lng": message.location.longitude,
                "source": "gps_location",
                "details": {
                    "mahalla": address.get("mahalla"),
                    "shahar_tuman": address.get("shahar_tuman"),
                    "viloyat": address.get("viloyat")
                }
            }

            # Dublikat tekshirish
            if self.check_duplicate:
                is_duplicate, error_key = await self._check_duplicate(state, address_data)
                if is_duplicate:
                    return ValidationResult.error(error_key)

            logger.info(f"✅ GPS location validated: {address_data['address']}")
            return ValidationResult.success(address_data)

        except Exception as e:
            logger.error(f"❌ GPS location error: {e}")
            return ValidationResult.error("errors.location_service_error")

    async def _validate_text_location(
            self,
            message: Message,
            state: StateContext,
            lang: str
    ) -> ValidationResult:
        """Matn (shahar nomi) validatsiyasi"""
        from .utills import aget_coords_from_place

        # Shahar nomini aniqlash
        detected_slug = detect_slug(message.text, lang)
        cities = self.SUPPORTED_CITIES.get(lang, {})

        if detected_slug not in cities:
            return ValidationResult.error("errors.unknown_city")

        city_name = cities[detected_slug]

        try:
            # Shahar koordinatalarini olish
            locations = await aget_coords_from_place(city_name, accept_language=lang)

            if not locations or not locations[0].get('lat') or not locations[0].get('lon'):
                return ValidationResult.error("errors.city_not_found")

            location = locations[0]
            address_data = {
                "address": location.get('full_address', city_name),
                "lat": location['lat'],
                "lng": location['lon'],
                "source": "city_name",
                "city_key": detected_slug,
                "city_name": city_name
            }

            # Dublikat tekshirish
            if self.check_duplicate:
                is_duplicate, error_key = await self._check_duplicate(state, address_data)
                if is_duplicate:
                    return ValidationResult.error(error_key)

            logger.info(f"✅ City location validated: {city_name}")
            return ValidationResult.success(address_data)

        except Exception as e:
            logger.error(f"❌ City location error: {e}")
            return ValidationResult.error("errors.city_not_found")

    async def _check_duplicate(
            self,
            state: StateContext,
            current_location: Dict
    ) -> Tuple[bool, Optional[str]]:
        """
        Bir xil shahar ekanligini tekshirish

        Returns:
            Tuple[is_duplicate, error_key]
        """
        async with state.data() as data:
            from_location = data.get("from_location")

            if not from_location:
                return False, None

            # Masofani hisoblash
            distance = self._calculate_distance(from_location, current_location)

            if distance <= self.max_distance_km:
                logger.warning(f"⚠️ Duplicate location detected: {distance:.2f}km")
                return True, "errors.same_city"

            return False, None

    @staticmethod
    def _calculate_distance(loc1: Dict, loc2: Dict) -> float:
        """
        Ikki nuqta orasidagi masofani hisoblash (Haversine formula)

        Args:
            loc1: Birinchi location {lat, lng}
            loc2: Ikkinchi location {lat, lng}

        Returns:
            Masofa kilometrda
        """
        lat1, lon1 = loc1.get("lat"), loc1.get("lng")
        lat2, lon2 = loc2.get("lat"), loc2.get("lng")

        if None in (lat1, lon1, lat2, lon2):
            return float('inf')

        R = 6371  # Yer radiusi (km)

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c

        return round(distance, 2)


# ==================== TEXT VALIDATOR ====================

class TextValidator(BaseValidator):
    """Tekst validator"""

    def __init__(
            self,
            min_length: int = None,
            max_length: int = None,
            pattern: str = None,
            strip: bool = True,
            **kwargs
    ):
        super().__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self.strip = strip

    async def validate(
            self,
            message: Message,
            state: StateContext,
            lang: str,
            **kwargs
    ) -> ValidationResult:
        """Tekst validatsiyasi"""
        if not message.text:
            return ValidationResult.error("errors.text_required")

        text = message.text.strip() if self.strip else message.text

        # Uzunlik tekshirish
        if self.min_length and len(text) < self.min_length:
            return ValidationResult.error(
                "errors.text_too_short",
                {"min_length": self.min_length}
            )

        if self.max_length and len(text) > self.max_length:
            return ValidationResult.error(
                "errors.text_too_long",
                {"max_length": self.max_length}
            )

        # Pattern tekshirish
        if self.pattern:
            import re
            if not re.match(self.pattern, text):
                return ValidationResult.error("errors.invalid_format")

        return ValidationResult.success({"text": text})


# ==================== PHONE VALIDATOR ====================

class PhoneValidator(BaseValidator):
    """Telefon raqam validator"""

    PHONE_PATTERNS = [
        r'^\+998[0-9]{9}$',  # +998901234567
        r'^998[0-9]{9}$',  # 998901234567
        r'^[0-9]{9}$',  # 901234567
    ]

    def __init__(self, normalize: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.normalize = normalize

    async def validate(
            self,
            message: Message,
            state: StateContext,
            lang: str,
            **kwargs
    ) -> ValidationResult:
        """Telefon validatsiyasi"""
        # Contact orqali
        if message.contact:
            phone = message.contact.phone_number
        # Text orqali
        elif message.text:
            phone = message.text
        else:
            return ValidationResult.error("errors.phone_required")

        # Tozalash
        import re
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)

        # Pattern tekshirish
        valid = any(re.match(pattern, cleaned) for pattern in self.PHONE_PATTERNS)

        if not valid:
            return ValidationResult.error("errors.invalid_phone")

        # Normallash
        if self.normalize:
            if cleaned.startswith('+998'):
                normalized = cleaned
            elif cleaned.startswith('998'):
                normalized = '+' + cleaned
            else:
                normalized = '+998' + cleaned
        else:
            normalized = cleaned

        return ValidationResult.success({"phone": normalized})


# ==================== NUMBER VALIDATOR ====================

class NumberValidator(BaseValidator):
    """Raqam validator"""

    def __init__(
            self,
            min_value: Union[int, float] = None,
            max_value: Union[int, float] = None,
            integer_only: bool = False,
            **kwargs
    ):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
        self.integer_only = integer_only

    async def validate(
            self,
            message: Message,
            state: StateContext,
            lang: str,
            **kwargs
    ) -> ValidationResult:
        """Raqam validatsiyasi"""
        if not message.text:
            return ValidationResult.error("errors.number_required")

        try:
            if self.integer_only:
                number = int(message.text)
            else:
                number = float(message.text)
        except ValueError:
            return ValidationResult.error("errors.invalid_number")

        # Min/max tekshirish
        if self.min_value is not None and number < self.min_value:
            return ValidationResult.error(
                "errors.number_too_small",
                {"min_value": self.min_value}
            )

        if self.max_value is not None and number > self.max_value:
            return ValidationResult.error(
                "errors.number_too_large",
                {"max_value": self.max_value}
            )

        return ValidationResult.success({"number": number})


# ==================== VALIDATOR REGISTRY ====================

VALIDATOR_REGISTRY = {
    "location": LocationValidator,
    "text": TextValidator,
    "phone": PhoneValidator,
    "number": NumberValidator,
}


# ==================== DECORATOR ====================

def validate_with(validator: Union[str, BaseValidator], **validator_kwargs):
    """
    Universal validator decorator.

    Usage:
        @validate_with("location", check_duplicate=True)
        async def handler(message, state, validated_data):
            ...

    Args:
        validator: Validator nomi yoki instance
        validator_kwargs: Validator parametrlari
    """

    def decorator(handler_func: Callable):
        @wraps(handler_func)
        async def wrapper(message: Message, state: StateContext, *args, **kwargs):
            h = UltraHandler(message, state)
            lang = await h.lang()

            # Validator yaratish
            if isinstance(validator, str):
                validator_class = VALIDATOR_REGISTRY.get(validator)
                if not validator_class:
                    raise ValueError(f"Unknown validator: {validator}")
                validator_instance = validator_class(**validator_kwargs)
            else:
                validator_instance = validator

            # Validatsiya
            result = await validator_instance(message, state, lang, **validator_kwargs)

            if not result.is_valid:
                await h.send(result.error_key or "errors.validation_error", **result.data or {})
                return

            # Handler ga uzatish
            kwargs['validated_data'] = result.data
            return await handler_func(message, state, *args, **kwargs)

        return wrapper

    return decorator


# ==================== QISQA VARIANTLAR ====================

def validate_location(**kwargs):
    """Location validator decorator"""
    return validate_with("location", **kwargs)


def validate_text(**kwargs):
    """Text validator decorator"""
    return validate_with("text", **kwargs)


def validate_phone(**kwargs):
    """Phone validator decorator"""
    return validate_with("phone", **kwargs)


def validate_number(**kwargs):
    """Number validator decorator"""
    return validate_with("number", **kwargs)


# ==================== USAGE EXAMPLES ====================

"""
# 1. Location validator
@validate_location(check_duplicate=True, max_distance_km=50)
async def handle_from_location(message: Message, state: StateContext, validated_data: Dict):
    async with state.data() as data:
        data['from_location'] = validated_data
    await h.send("location_saved")

# 2. Text validator
@validate_text(min_length=3, max_length=50)
async def handle_name(message: Message, state: StateContext, validated_data: Dict):
    name = validated_data['text']
    await save_name(name)

# 3. Phone validator
@validate_phone(normalize=True)
async def handle_phone(message: Message, state: StateContext, validated_data: Dict):
    phone = validated_data['phone']
    await save_phone(phone)

# 4. Number validator
@validate_number(min_value=1, max_value=4, integer_only=True)
async def handle_seats(message: Message, state: StateContext, validated_data: Dict):
    seats = validated_data['number']
    await save_seats(seats)

# 5. Custom validator
class DateValidator(BaseValidator):
    async def validate(self, message, state, lang, **kwargs):
        # Custom logic
        return ValidationResult.success({"date": parsed_date})

@validate_with(DateValidator())
async def handle_date(message, state, validated_data):
    date = validated_data['date']
"""