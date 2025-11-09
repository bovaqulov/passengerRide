
import json
from datetime import datetime
from typing import Dict, Optional
from application.database.cache import cache
from application.core.log import logger


async def create_ride(user_id: int, ride_data: Dict) -> Optional[Dict]:
    """Create a new ride"""
    try:
        ride_id = await cache.client.incr("ride:id:counter")

        ride = {
            'id': ride_id,
            'user_id': user_id,
            'from_city': ride_data.get('from_city'),
            'to_city': ride_data.get('to_city'),
            'date': ride_data.get('date'),
            'time': ride_data.get('time'),
            'seats': ride_data.get('seats', 1),
            'price': ride_data.get('price', 0.0),
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }

        # Save ride
        ride_key = f"ride:{ride_id}"
        await cache.client.set(ride_key, json.dumps(ride))

        # Add to user's rides
        user_rides_key = f"user:{user_id}:rides"
        await cache.client.lpush(user_rides_key, str(ride_id))

        logger.info(f"Ride created: {ride_id} by user {user_id}")
        return ride

    except Exception as e:
        logger.error(f"Error creating ride: {e}")
        return None


async def get_ride_by_id(ride_id: int) -> Optional[Dict]:
    """Get ride by ID"""
    try:
        ride_key = f"ride:{ride_id}"
        ride_data = await cache.client.get(ride_key)

        if ride_data:
            return json.loads(ride_data)
        return None

    except Exception as e:
        logger.error(f"Error getting ride {ride_id}: {e}")
        return None

