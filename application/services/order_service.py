from application.services.base import BaseService

class OrderServiceAPI(BaseService):
    async def update_status(self, order_id, status):
        return await self._request(
            "PATCH",
            f"/orders/{order_id}/",
            json={'status': status},
        )
    async def get_by_id(self, telegram_id):
        return await self._request(
            "GET",
            f"/orders/user/{telegram_id}/",
        )

    async def update_rate(self, order_id, rate):
        return await self._request(
            "PATCH",
            f"/orders/{order_id}/",
            json={'rate': rate},
        )

