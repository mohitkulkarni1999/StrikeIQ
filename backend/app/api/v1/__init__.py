"""
v1 API routers for StrikeIQ
"""

from .auth import router as auth_router
from .market import router as market_router
from .options import router as options_router
from .system import router as system_router
from .predictions import router as predictions_router
from .debug import router as debug_router

__all__ = [
    "auth_router",
    "market_router", 
    "options_router",
    "system_router",
    "predictions_router",
    "debug_router"
]
