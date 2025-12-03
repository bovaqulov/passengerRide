# services.py
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
from application.services.base import BaseService


@dataclass
class PassengerCreateService:
    telegram_id: int
    full_name: str
    phone: str


@dataclass
class PassengerGetService:
    id: int
    telegram_id: int
    full_name: str
    language: str
    phone: str
    total_rides: int
    rating: int


@dataclass
class PassengerUpdateService:
    full_name: Optional[str] = None
    phone: Optional[str] = None
    rating: Optional[int] = None
    total_rides: Optional[int] = None


@dataclass
class PassengerService:
    id: int
    telegram_id: int
    full_name: str
    phone: str
    total_rides: int
    rating: int
    created_at: datetime
    updated_at: datetime


class PassengerServiceAPI(BaseService):

    async def create(self, passenger: PassengerCreateService) -> Optional[PassengerService]:
        try:
            result = await self._request(
                "POST",
                "/passengers/",
                json=asdict(passenger)
            )
            return PassengerService(**result)
        except Exception as e:
            print(f"Create error: {e}")
            return None

    async def get_by_user(self, user_id: int) -> Optional[PassengerGetService]:
        try:
            result = await self._request(
                "GET",
                f"/passengers/user/{user_id}/",
            )

            if not result or result.get("telegram_id") != user_id:
                return None

            return PassengerGetService(**result)
        except Exception as e:
            print(f"Get by user error: {e}")
            return None

    async def update_user(self, passenger_id: int, data: PassengerUpdateService) -> Optional[PassengerService]:
        try:
            # Faqat None emas fieldlarni yuborish
            update_data = {k: v for k, v in asdict(data).items() if v is not None}

            result = await self._request(
                "PATCH",
                f"/passengers/{passenger_id}/",
                json=update_data
            )
            return PassengerService(**result)
        except Exception as e:
            print(f"Update error: {e}")
            return None

    async def get_by_id(self, passenger_id: int) -> Optional[PassengerService]:
        try:
            result = await self._request(
                "GET",
                f"/passengers/{passenger_id}/",
            )
            return PassengerService(**result)
        except Exception as e:
            print(f"Get by ID error: {e}")
            return None