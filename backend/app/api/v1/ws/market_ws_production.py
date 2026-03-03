"""
Production WebSocket Market Endpoint
Uses the production-grade WebSocket manager
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.production_ws_manager import websocket_endpoint
from app.core.redis_client import redis_client
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/market")
async def market_websocket(websocket: WebSocket):
    """Production-grade market WebSocket endpoint"""
    
    async with websocket_endpoint(websocket, ["market_data"]) as connection_id:
        logger.info(f"🟢 MARKET WS CONNECTED: {connection_id}")
        
        try:
            # Keep connection alive with passive monitoring
            while True:
                try:
                    # Wait for client message or timeout
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                    
                    # Handle client messages if needed
                    try:
                        data = json.loads(message)
                        logger.debug(f"Received message from {connection_id}: {data}")
                        
                        # Handle pong responses
                        if data.get("type") == "pong":
                            from app.core.production_ws_manager import ws_manager
                            await ws_manager.handle_pong(connection_id)
                        
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON from {connection_id}: {message}")
                
                except asyncio.TimeoutError:
                    # Timeout is expected - just continue the loop
                    continue
                
        except WebSocketDisconnect:
            logger.info(f"🔌 MARKET WS DISCONNECTED: {connection_id}")
        except Exception as e:
            logger.error(f"❌ MARKET WS ERROR for {connection_id}: {e}")
            raise
