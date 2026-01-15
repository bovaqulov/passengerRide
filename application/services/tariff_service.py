from application.services.base import BaseService


class TariffServiceAPI(BaseService):
    async def get_tariff(self, tariff_id: int):
        return await self._request(
            "GET",
            f"/tariffs/{tariff_id}",
        )