# application/services/admin_service.py

from typing import Dict
from application.services.user_service import get_user_count
from application.core.log import logger


async def get_stats() -> Dict:
    """Get application statistics"""
    try:
        total_users = await get_user_count()

        # Add more stats as needed
        stats = {
            'total_users': total_users,
            'total_rides': 0,  # Implement based on your ride storage
            'revenue': 0.0,  # Implement based on your payment system
            'active_today': 0  # Implement based on activity tracking
        }

        return stats

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            'total_users': 0,
            'total_rides': 0,
            'revenue': 0.0,
            'active_today': 0
        }


