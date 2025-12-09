from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
from application.services.base import BaseService


@dataclass
class Travel:
    user: int
    from_location: str
    to_location: str
    travel_class: str
    passenger: int = 1
    price: float | int = 0
    has_woman: bool = False
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.id is None:
            data.pop('id', None)
        data.pop('created_at', None)
        data.pop('updated_at', None)
        return data




class RideService(BaseService):

    async def create_travel(self, travel_data: Travel | Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new travel record

        Args:
            travel_data: Travel object or dictionary with travel data

        Returns:
            API response data
        """

        if isinstance(travel_data, Travel):
            data = travel_data.to_dict()
        else:
            data = travel_data

        return await self._request("POST", "/travels/", json=data)

    async def get_travel(self, travel_id: int) -> Dict[str, Any]:
        """
        Get a specific travel by ID

        Args:
            travel_id: ID of the travel record

        Returns:
            Travel data
        """
        return await self._request("GET", f"/travels/{travel_id}/")

    async def update_travel(self, travel_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a travel record

        Args:
            travel_id: ID of the travel record
            update_data: Dictionary with fields to update

        Returns:
            Updated travel data
        """
        return await self._request("PATCH", f"/travels/{travel_id}/", json=update_data)

    async def delete_travel(self, travel_id: int) -> bool:
        """
        Delete a travel record

        Args:
            travel_id: ID of the travel record

        Returns:
            True if successful
        """
        await self._request("DELETE", f"/travels/{travel_id}/")
        return True

    async def list_travels(
            self,
            user_id: Optional[int] = None,
            from_location: Optional[str] = None,
            to_location: Optional[str] = None,
            travel_class: Optional[str] = None,
            status: Optional[str] = None,
            has_woman: Optional[bool] = None,
            min_price: Optional[int] = None,
            max_price: Optional[int] = None,
            page: int = 1,
            page_size: int = 20
    ) -> Dict[str, Any]:
        """
        List travels with filtering and pagination

        Args:
            user_id: Filter by user ID
            from_location: Filter by origin location
            to_location: Filter by destination location
            travel_class: Filter by travel class
            status: Filter by status
            has_woman: Filter by has_woman flag
            min_price: Minimum price filter
            max_price: Maximum price filter
            page: Page number for pagination
            page_size: Number of items per page

        Returns:
            Paginated list of travels
        """
        params = {
            "page": page,
            "page_size": page_size,
        }

        # Add filters if provided
        if user_id:
            params["user"] = user_id
        if from_location:
            params["from_location"] = from_location
        if to_location:
            params["to_location"] = to_location
        if travel_class:
            params["travel_class"] = travel_class
        if has_woman is not None:
            params["has_woman"] = str(has_woman).lower()
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price

        return await self._request("GET", "/travels/", params=params)

    async def search_travels(
            self,
            from_location: str = "",
            to_location: str = "",
            user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search travels by from and to locations

        Args:
            from_location: Origin location (partial match)
            to_location: Destination location (partial match)
            user_id: Optional user ID filter

        Returns:
            List of matching travels
        """
        params = {}
        if from_location:
            params["from"] = from_location
        if to_location:
            params["to"] = to_location
        if user_id:
            params["user_id"] = user_id

        return await self._request("GET", "/travels/search_routes/", params=params)

    async def get_user_travels(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all travels for a specific user

        Args:
            user_id: User ID to filter by

        Returns:
            List of user's travels
        """
        return await self._request("GET", f"/travels/by-telegram-id/{user_id}/")

    async def bulk_create_travels(self, travels: List[Travel]) -> List[Dict[str, Any]]:
        """
        Create multiple travel records (if bulk create endpoint exists)

        Args:
            travels: List of Travel objects

        Returns:
            List of created travels
        """
        results = []
        for travel in travels:
            result = await self.create_travel(travel)
            results.append(result)
        return results

