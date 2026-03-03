from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.ws_manager import manager
from app.core.redis_client import redis_client
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/market")
async def market_websocket(websocket: WebSocket):

    await websocket.accept()

    await manager.connect("market_data", websocket)

    logger.info(
        f"🟢 MARKET WS CONNECTED | clients={len(manager.active_connections.get('market_data', set()))}"
    )

    try:

        from app.services.market_session_manager import get_market_session_manager

        market_manager = get_market_session_manager()

        market_open = await market_manager.is_market_open()

        await websocket.send_json({
            "type": "market_status",
            "market_open": market_open
        })

        logger.info(f"📊 Initial market status sent: market_open={market_open}")

        # Send last tick if available
        last_tick = await redis_client.get("market:last_tick")

        if last_tick:

            await websocket.send_json({
                "type": "market_tick",
                "data": last_tick
            })

    except Exception as e:

        logger.error(f"Failed initial WS state: {e}")

    try:

        while True:
            # Passive connection keep-alive - no receive_text() needed
            # Frontend does not send messages, just keep connection open
            await asyncio.sleep(60)

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