import json
from datetime import datetime
from typing import Dict

from application.core.log import logger
from application.database.cache import cache


async def track_activity(user_id: int, event_type: str, event_data: Dict) -> bool:
    """Track user activity for analytics"""
    try:
        activity_key = f"analytics:{datetime.now().strftime('%Y-%m-%d')}:{user_id}"

        activity = {
            'user_id': user_id,
            'event_type': event_type,
            'event_data': event_data,
            'timestamp': datetime.now().isoformat()
        }

        await cache.client.lpush(activity_key, json.dumps(activity))
        await cache.client.expire(activity_key, 86400 * 30)  # Keep for 30 days

        return True

    except Exception as e:
        logger.error(f"Error tracking activity: {e}")
        return False