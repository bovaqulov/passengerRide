from application.services.base import BaseService


class SmsService(BaseService):
    async def send_sms(self, telegram_id, phone):
        return await self._request(
    "POST",
    "/sms/",
            json={
                "telegram_id": telegram_id,
                "phone": phone,
                "is_driver": False,
            }
        )
