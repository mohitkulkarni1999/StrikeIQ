"""
Live WebSocket Endpoints - Live Option Chain Builder
WS SAFE VERSION (No HTTPException leakage)
Updated to forward option chain payloads directly without market_data wrapper
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect, APIRouter

from app.services.websocket_market_feed import ws_feed_manager
from app.services.upstox_auth_service import get_upstox_auth_service
from app.services.market_session_manager import get_market_session_manager
from app.services.live_option_chain_builder import get_live_chain_builder
from app.core.ws_manager import manager
from app.core.instrument_runtime import registry

router = APIRouter(prefix="/ws", tags=["websocket"])
logger = logging.getLogger(__name__)


async def safe_cancel_task(task: Optional[asyncio.Task]) -> None:
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


async def stream_market_status(symbol: str, websocket: WebSocket):
    """
    Stream market session status separately (not overriding option chain data)
    """
    session_manager = get_market_session_manager()

    try:
        while True:
            # Send market status separately
            await websocket.send_json({
                "status": "market_data",
                "data": {
                    "market_status": str(session_manager.market_status),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            })

            await asyncio.sleep(30)  # Send market status every 30 seconds

    except asyncio.CancelledError:
        logger.info(f"Market status stream cancelled for {symbol}")

    except Exception as e:
        logger.error(f"Market status broadcast error: {e}")


@router.websocket("/live-options/{symbol}")
async def websocket_endpoint(
    websocket: WebSocket,
    symbol: str,
    expiry: Optional[str] = None,
    expiry_date: Optional[str] = None
):

    # ✅ MUST be first line - accept immediately
    await websocket.accept()

    final_expiry = expiry or expiry_date

    if not final_expiry:
        await websocket.close(code=1008)
        return

    logger.info(f"WebSocket connection - symbol: {symbol}, expiry: {final_expiry}")

    # 🔐 AUTH CHECK
    try:
        auth_service = get_upstox_auth_service()
        token = await auth_service.get_valid_access_token()

        if not token:
            await websocket.send_json({
                "status": "error",
                "msg": "Upstox token missing"
            })
            await websocket.close(code=1011)
            return

    except Exception as e:
        logger.error(f"Auth failed: {e}")
        await websocket.send_json({
            "status": "error",
            "msg": "Auth failed"
        })
        await websocket.close(code=1011)
        return

    # 🚀 START SHARED WS FEED
    try:
        ws_feed = ws_feed_manager.feed

        if not ws_feed or not ws_feed.is_connected:
            logger.info("🚀 AUTO STARTING WS FEED...")
            ws_feed = await ws_feed_manager.start_feed()

        if not ws_feed:
            await websocket.send_json({
                "status": "error",
                "msg": "WS Feed failed"
            })
            await websocket.close(code=1011)
            return

        logger.info("🟢 USING SHARED WS FEED")

    except Exception as e:
        logger.error(f"Feed start failed: {e}")
        await websocket.close(code=1011)
        return

    builder = get_live_chain_builder()

    # 🟡 SAFE BUILDER INIT (NO HTTPException)
    try:
        logger.info(f"🚀 INITIALIZING OPTION CHAIN FOR {symbol}")
        await builder.initialize_chain(symbol, final_expiry, registry)
        await builder.subscribe_to_instruments(symbol)

    except Exception as e:
        logger.error(f"Builder init failed: {e}")
        await websocket.send_json({
            "status": "error",
            "msg": "Option chain init failed"
        })
        await websocket.close(code=1011)
        return

    # 🔥 CONNECT TO WS MANAGER TO RECEIVE BROADCASTS
    # This allows LiveOptionChainBuilder._broadcast() to send directly to this client
    await manager.connect(websocket, symbol)
    logger.info(f"📡 Connected to WS manager for {symbol}")

    # 📊 START MARKET STATUS STREAM (separate from option chain data)
    market_status_task = asyncio.create_task(
        stream_market_status(symbol, websocket)
    )

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        logger.info(f"Disconnected {symbol}")
        await builder.stop_tasks(symbol, final_expiry)

    finally:
        await safe_cancel_task(market_status_task)
        manager.disconnect(websocket, symbol)