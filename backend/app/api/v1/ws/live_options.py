from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.ws_manager import manager

router = APIRouter()

@router.websocket("/ws/live-options/{symbol}")
async def live_options_ws(websocket: WebSocket, symbol: str):
    await manager.connect(websocket, symbol)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, symbol)