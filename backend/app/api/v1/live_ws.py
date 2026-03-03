import asyncio
import logging
from datetime import datetime, timezone

from fastapi import WebSocket, WebSocketDisconnect, APIRouter, HTTPException

from app.services.websocket_market_feed import ws_feed_manager
from app.services.upstox_auth_service import get_upstox_auth_service
from app.services.instrument_registry import get_instrument_registry
from app.services.live_chain_manager import chain_manager
from app.core.ws_manager import manager

router = APIRouter(prefix="/ws", tags=["websocket"])
logger = logging.getLogger(__name__)

# Global dict for market status checks
upstox_feeds = {}


@router.websocket("/live-options/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str):

    expiry = websocket.query_params.get("expiry")

    if expiry in [None, "null", "None", "", "undefined"]:
        await websocket.close(code=1008)
        return

    key = f"{symbol}:{expiry}"

    await websocket.accept()
    logger.info(f"WS CONNECTED → {key}")

    auth_service = get_upstox_auth_service()

    # START GLOBAL FEED
    ws_feed = await ws_feed_manager.get_feed()
    if not ws_feed:
        try:
            ws_feed = await ws_feed_manager.start_feed()
        except HTTPException as e:
            logger.error(f" WS AUTH FAILED → {e.detail}")
            try:
                await websocket.send_json({
                    "status": "error",
                    "message": "Authentication required",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            except Exception:
                logger.warning("Client disconnected during auth error")
            await websocket.close(code=4401)
            return
        except Exception as e:
            logger.error(f" WS INTERNAL ERROR → {str(e)}")
            try:
                await websocket.send_json({
                    "status": "error", 
                    "message": "Internal server error",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            except Exception:
                logger.warning("Client disconnected during internal error")
            await websocket.close(code=1011)
            return

    if not ws_feed:
        try:
            await websocket.send_json({
                "status": "error",
                "message": "Market feed unavailable",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception:
            logger.warning("Client disconnected during market feed error")
        return

    builder = None

    try:

        token = await auth_service.get_valid_access_token()

        if not token:
            try:
                await websocket.send_json({
                    "status": "error",
                    "message": "Authentication required"
                })
            except Exception:
                logger.warning("Client disconnected during token error")
            return

        # GET SINGLETON REGISTRY
        registry = get_instrument_registry()

        # WAIT UNTIL READY
        await registry.wait_until_ready()

        symbol_upper = symbol.upper()
        
        # VALIDATE EXPIRY
        valid_expiries = registry.options.get(symbol_upper, {}).keys()
        
        if expiry not in valid_expiries:
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid expiry"
                })
            except Exception:
                logger.warning("Client disconnected")
            await websocket.close(code=1008)
            return
        
        logger.info(f"✅ Expiry validated: {symbol_upper}:{expiry}")
        
        # PER EXPIRY BUILDER - OFFLOAD TO BACKGROUND TASK
        expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
        
        # Start builder in background task
        builder_task = asyncio.create_task(
            chain_manager.get_builder(symbol, expiry_date)
        )
        
        builder = None

        # REGISTER CLIENT
        await manager.connect(key, websocket)

        logger.info(f"WS REGISTERED → {key}")

        # Handle builder in background
        async def handle_builder_ready():
            try:
                builder = await builder_task
                if builder:
                    await builder.start()
                    
                    # Send initial chain state
                    chain_state = builder.get_latest_option_chain()
                    if chain_state:
                        chain_data = chain_state.build_final_chain()
                        logger.info(f"🔍 [INITIAL CHAIN] {symbol_upper}: spot={chain_data.get('spot')}")
                        await websocket.send_json({
                            "type": "chain_update",
                            "data": chain_data
                        })
                        logger.info(f"📤 SENT INITIAL CHAIN: {len(chain_data.get('calls', []))} calls, {len(chain_data.get('puts', []))} puts")
                    else:
                        await websocket.send_json({
                            "type": "waiting",
                            "message": "Waiting for market data...",
                            "symbol": symbol_upper,
                            "expiry": expiry
                        })
                        logger.info(f"📤 SENT WAITING MESSAGE for {key}")
            except Exception as e:
                logger.error(f"Failed to handle builder: {e}")
        
        # Start background task for builder handling
        asyncio.create_task(handle_builder_ready())

        # CRITICAL FIX: Passive keepalive loop.
        # Do NOT use receive_text() — frontend does not send messages.
        # Server broadcasts chain_update via manager.broadcast_json().
        try:
            while True:
                await asyncio.sleep(60)

        except WebSocketDisconnect:
            logger.info(f"WS DISCONNECTED → {key}")

            await manager.disconnect(key, websocket)
        
        # Stop builder tasks if builder was created
        if 'builder_task' in locals() and builder_task and not builder_task.done():
            try:
                builder = await builder_task
                if builder:
                    await builder.stop_tasks()
            except Exception:
                pass

    except Exception as e:

        logger.error(f"WS ERROR → {key}: {e}")

        # Stop builder tasks if builder was created
        if 'builder_task' in locals() and builder_task and not builder_task.done():
            try:
                builder = await builder_task
                if builder:
                    await builder.stop_tasks()
            except Exception:
                pass

        await manager.disconnect(key, websocket)