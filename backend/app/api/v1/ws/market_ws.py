from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.ws_manager import manager
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/market")
async def market_websocket(websocket: WebSocket):
    """
    Live Market WebSocket

    Frontend connects here:
    ws://localhost:8000/ws/market

    Backend broadcasts using:
    manager.broadcast_json("market_data", payload)
    """

    await websocket.accept()

    await manager.connect("market_data", websocket)

    logger.info(
        f"🟢 MARKET WS CONNECTED | clients={len(manager.active_connections.get('market_data', set()))}"
    )
    
    # Log all active channels for debugging
    logger.info(f"📊 Active channels: {list(manager.active_connections.keys())}")

    try:

        while True:

            # keep connection alive without blocking
            await asyncio.sleep(30)

            try:
                await websocket.send_json({"type": "ping"})
                logger.debug("💓 Sent ping to client")
            except Exception:
                # connection probably closed
                logger.warning("⚠️ Failed to send ping - connection closed")
                break

    except WebSocketDisconnect:

        logger.info("🔴 MARKET WS CLIENT DISCONNECTED")

    except Exception as e:

        logger.error(f"❌ MARKET WS ERROR: {e}")

    finally:

        try:
            await manager.disconnect("market_data", websocket)
        except Exception:
            pass

        logger.info(
            f"🔴 MARKET WS CLEANUP | remaining_clients={len(manager.active_connections.get('market_data', set()))}"
        )