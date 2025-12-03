# services/passenger_post_service.py
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
from application.services.base import BaseService


@dataclass
class PassengerPost:
    user: int
    from_location: str
    to_location: str
    price: int
    status: str = "CREATED"
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


class PassengerPostService(BaseService):

    async def create_post(self, post_data: PassengerPost | Dict[str, Any]) -> Dict[str, Any]:

        if isinstance(post_data, PassengerPost):
            data = post_data.to_dict()
        else:
            data = post_data

        return await self._request("POST", "/posts/", json=data)

    async def get_post(self, post_id: int) -> Dict[str, Any]:
        """
        Get a specific post by ID

        Args:
            post_id: ID of the post record

        Returns:
            Post data
        """
        return await self._request("GET", f"/posts/{post_id}/")

    async def update_post(self, post_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a post record

        Args:
            post_id: ID of the post record
            update_data: Dictionary with fields to update

        Returns:
            Updated post data
        """
        return await self._request("PATCH", f"/posts/{post_id}/", json=update_data)

    async def delete_post(self, post_id: int) -> bool:
        """
        Delete a post record

        Args:
            post_id: ID of the post record

        Returns:
            True if successful
        """
        await self._request("DELETE", f"/posts/{post_id}/")
        return True

    async def list_posts(
            self,
            user_id: Optional[int] = None,
            from_location: Optional[str] = None,
            to_location: Optional[str] = None,
            status: Optional[str] = None,
            min_price: Optional[int] = None,
            max_price: Optional[int] = None,
            page: int = 1,
            page_size: int = 20
    ) -> Dict[str, Any]:
        """
        List posts with filtering and pagination

        Args:
            user_id: Filter by user ID
            from_location: Filter by origin location
            to_location: Filter by destination location
            status: Filter by status
            min_price: Minimum price filter
            max_price: Maximum price filter
            page: Page number for pagination
            page_size: Number of items per page

        Returns:
            Paginated list of posts
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
        if status:
            params["status"] = status
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price

        return await self._request("GET", "/posts/", params=params)

    async def search_posts(
            self,
            from_location: str = "",
            to_location: str = "",
            user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search posts by from and to locations

        Args:
            from_location: Origin location (partial match)
            to_location: Destination location (partial match)
            user_id: Optional user ID filter

        Returns:
            List of matching posts
        """
        params = {}
        if from_location:
            params["from"] = from_location
        if to_location:
            params["to"] = to_location
        if user_id:
            params["user_id"] = user_id

        return await self._request("GET", "/posts/search_routes/", params=params)

    async def get_user_posts(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all posts for a specific user

        Args:
            user_id: User ID to filter by

        Returns:
            List of user's posts
        """
        return await self._request("GET", "/posts/by_user/", params={"user_id": user_id})

    async def get_active_posts(self) -> List[Dict[str, Any]]:
        """
        Get all active posts (CREATED status)

        Returns:
            List of active posts
        """
        return await self._request("GET", "/posts/active_posts/")

    async def get_posts_by_price_range(self, min_price: int, max_price: int) -> List[Dict[str, Any]]:
        """
        Get posts within price range

        Args:
            min_price: Minimum price
            max_price: Maximum price

        Returns:
            List of posts in price range
        """
        return await self._request("GET", "/posts/price_range/", params={
            "min_price": min_price,
            "max_price": max_price
        })

    async def update_post_status(self, post_id: int, status: str) -> Dict[str, Any]:
        """
        Update post status using the custom action

        Args:
            post_id: ID of the post record
            status: New status value

        Returns:
            Updated post data
        """
        return await self._request(
            "POST",
            f"/posts/{post_id}/update_status/",
            json={"status": status}
        )

    # Helper methods for common status updates
    async def confirm_post(self, post_id: int) -> Dict[str, Any]:
        """Confirm a post"""
        return await self.update_post_status(post_id, "CONFIRMED")

    async def cancel_post(self, post_id: int) -> Dict[str, Any]:
        """Cancel a post"""
        return await self.update_post_status(post_id, "CANCELLED")

    async def complete_post(self, post_id: int) -> Dict[str, Any]:
        """Mark post as completed"""
        return await self.update_post_status(post_id, "COMPLETED")

    async def expire_post(self, post_id: int) -> Dict[str, Any]:
        """Mark post as expired"""
        return await self.update_post_status(post_id, "EXPIRED")