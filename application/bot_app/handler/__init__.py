# application/bot_app/handler/__init__.py

"""
Handler module initialization
Import all handlers and register them
"""

from .decorator import (
    UltraHandler,
    HandlerMaster,
    cmd, cb, msg, state, err,
    throttle, error_handler, async_lru_cache
)

# Import all handler modules
from .commands import *
from .messages import *
from .callbacks import *
from .middlewares import *

# Register all handlers
async def setup_handlers():
    """Setup all bot handlers - call this once on startup"""

    await HandlerMaster.register_all()
    setup_my_middleware()
    logger.info("🎯 All handlers registered successfully!")

__all__ = [
    'UltraHandler',
    'HandlerMaster',
    'cmd', 'cb', 'msg', 'state', 'err',
    'setup_handlers',
    'throttle', 'error_handler', 'async_lru_cache'
]