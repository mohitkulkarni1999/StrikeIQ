from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.ws_manager import manager
from app.services.live_chain_manager import chain_manager
from app.services.instrument_registry import get_instrument_registry
from app.services.websocket_market_feed import ws_feed_manager

router = APIRouter()

@router.websocket("/ws/live-options/{symbol}")
async def live_options_ws(websocket: WebSocket, symbol: str):

    expiry = websocket.query_params.get("expiry")

    if expiry in [None, "null", "None", "", "undefined"]:
        await websocket.close()
        return

    key = f"{symbol}:{expiry}"

    await websocket.accept()
    await manager.connect(key, websocket)

    print(f"🟢 WS CONNECTED → {key}")

    builder = None

    try:

        # ✅ GET REGISTRY SINGLETON
        registry = get_instrument_registry()
        await registry.wait_until_ready()

        # ✅ GET BUILDER (PER EXPIRY)
        builder = await chain_manager.get_builder(symbol, expiry)

        # ✅ START BUILDER ONLY ONCE
        await builder.start()

        # 🔁 KEEP ALIVE
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:

        print(f"🔴 WS DISCONNECTED → {key}")
        await manager.disconnect(key, websocket)

        if builder:
            await builder.stop_tasks()