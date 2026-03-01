from fastapi import APIRouter
import logging

from app.services.websocket_market_feed import ws_feed_manager
from .market_ws import router as market_ws_router

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/ws/init")
async def ws_init():
    """
    Initialize shared Upstox WebSocket feed

    Frontend calls once:
    GET /api/ws/init
    """

    try:

        # already running
        if ws_feed_manager.is_connected:
            return {"status": "already_connected"}

        await ws_feed_manager.start_feed()

        logger.info("🟢 SHARED WS FEED INITIALIZED")

        return {"status": "success"}

    except Exception as e:

        logger.error(f"WS INIT FAILED: {e}")

        return {
            "status": "error",
            "message": str(e)
        }


# Register WebSocket endpoint
router.include_router(market_ws_router)