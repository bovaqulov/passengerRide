from application.services.base import BaseService


class RouteServiceAPI(BaseService):

    async def get_to_city(self, to_city_id):
        return await self._request(
            "GET",
            f'/routes/from-city/{to_city_id}',
        )
    async def get_route(self, route_id):
        return await self._request(
            "GET",
            f'/routes/{route_id}',
        )

    async def get_routes(self):
        return await self._request(
            "GET",
            '/routes',
        )

