# application/services/user_service.py

import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from application.database.cache import cache
from application.core.log import logger


@dataclass
class TelegramUser:
    """Telegram user model"""
    telegram_id: int
    username: Optional[str] = None
    full_name: str = ""
    phone: Optional[str] = None
    language: str = "en"
    is_active: bool = True
    is_banned: bool = False
    total_rides: int = 0
    rating: float = 5.0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @property
    def is_new(self) -> bool:
        """Check if user is new (no phone)"""
        return not self.phone

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TelegramUser':
        """Create from dictionary"""
        return cls(**data)

    @classmethod
    async def from_user_id(cls, telegram_id: int) -> Optional['TelegramUser']:
        """
        Get user from database by telegram_id
        Creates new user if it doesn't exist
        """
        try:
            # Get from Redis
            user_key = f"user:{telegram_id}"
            user_data = await cache.client.get(user_key)

            if user_data:
                return cls.from_dict(json.loads(user_data))

            # Create new user
            from telebot.types import User as TeleUser
            # Note: This is a simplified version
            # In production, you'd get User object from message
            new_user = cls(
                telegram_id=telegram_id,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )

            await new_user.save()
            return new_user

        except Exception as e:
            logger.error(f"Error fetching user {telegram_id}: {e}")
            return None

    async def save(self) -> bool:
        """Save user to database"""
        try:
            self.updated_at = datetime.now().isoformat()

            user_key = f"user:{self.telegram_id}"
            user_data = json.dumps(self.to_dict())

            await cache.client.set(user_key, user_data)

            # Add to users set
            await cache.client.sadd("users:all", str(self.telegram_id))

            logger.debug(f"User saved: {self.telegram_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving user {self.telegram_id}: {e}")
            return False

    async def update(self, **kwargs) -> bool:
        """Update user fields"""
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)

            return await self.save()

        except Exception as e:
            logger.error(f"Error updating user {self.telegram_id}: {e}")
            return False

    async def delete(self) -> bool:
        """Delete user from database"""
        try:
            user_key = f"user:{self.telegram_id}"
            await cache.client.delete(user_key)
            await cache.client.srem("users:all", str(self.telegram_id))

            logger.info(f"User deleted: {self.telegram_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting user {self.telegram_id}: {e}")
            return False

    @classmethod
    async def is_user_banned(cls, user_id):
        return False

    async def get_rides(self, limit: int = 10, page: int = 1) -> List[Any]:
        """Get user rides"""
        try:
            # This is a placeholder - implement based on your ride storage
            rides_key = f"user:{self.telegram_id}:rides"

            start = (page - 1) * limit
            end = start + limit - 1

            ride_ids = await cache.client.lrange(rides_key, start, end)

            # Fetch ride details
            rides = []
            for ride_id in ride_ids:
                ride_data = await cache.client.get(f"ride:{ride_id}")
                if ride_data:
                    rides.append(json.loads(ride_data))

            return rides

        except Exception as e:
            logger.error(f"Error fetching rides for user {self.telegram_id}: {e}")
            return []


# ==================== HELPER FUNCTIONS ====================

async def get_user_by_id(telegram_id: int) -> Optional[TelegramUser]:
    """Get user by telegram ID"""
    return await TelegramUser.from_user_id(telegram_id)


async def get_all_users(limit: int = 100, offset: int = 0) -> List[TelegramUser]:
    """Get all users with pagination"""
    try:
        user_ids = await cache.client.smembers("users:all")

        users = []
        for user_id in list(user_ids)[offset:offset + limit]:
            user = await get_user_by_id(int(user_id))
            if user:
                users.append(user)

        return users

    except Exception as e:
        logger.error(f"Error fetching all users: {e}")
        return []


async def is_user_banned(telegram_id: int) -> bool:
    """Check if user is banned"""
    try:
        user = await get_user_by_id(telegram_id)
        return user.is_banned if user else False
    except Exception as e:
        logger.error(f"Error checking ban status: {e}")
        return False


async def ban_user(telegram_id: int, reason: str = "") -> bool:
    """Ban user"""
    try:
        user = await get_user_by_id(telegram_id)
        if user:
            await user.update(is_banned=True, is_active=False)
            logger.info(f"User banned: {telegram_id}, reason: {reason}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        return False


async def unban_user(telegram_id: int) -> bool:
    """Unban user"""
    try:
        user = await get_user_by_id(telegram_id)
        if user:
            await user.update(is_banned=False, is_active=True)
            logger.info(f"User unbanned: {telegram_id}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error unbanning user: {e}")
        return False


async def get_user_count() -> int:
    """Get total user count"""
    try:
        return await cache.client.scard("users:all")
    except Exception as e:
        logger.error(f"Error getting user count: {e}")
        return 0