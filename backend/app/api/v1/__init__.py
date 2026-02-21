"""
v1 API routers for StrikeIQ
"""

from .auth import router as auth_router
from .market import router as market_router
from .options import router as options_router
from .system import router as system_router
from .predictions import router as predictions_router
from .debug import router as debug_router
from .intelligence import router as intelligence_router
from .market_session import router as market_session_router  # Add market session router
# RESTORED: WebSocket router for real-time options chain
from .live_ws import router as live_ws_router

__all__ = [
    "auth_router",
    "market_router", 
    "options_router",
    "system_router",
    "predictions_router",
    "debug_router",
    "intelligence_router",
    "market_session_router",  # Add to exports
    "live_ws_router"
]
