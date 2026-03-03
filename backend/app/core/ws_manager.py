from fastapi import WebSocket
from typing import Dict, Set
import asyncio
import logging

logger = logging.getLogger(__name__)


class WSConnectionManager:

    def __init__(self):

        # channel → websocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

        # prevent race conditions
        self._lock = asyncio.Lock()

    # ================= CONNECT =================

    async def connect(self, key: str, websocket: WebSocket):

        async with self._lock:

            if key not in self.active_connections:
                self.active_connections[key] = set()

            self.active_connections[key].add(websocket)

            logger.info(
                f"🟢 WebSocket client connected → {key} → {len(self.active_connections[key])} clients"
            )

    # ================= DISCONNECT =================

    async def disconnect(self, key: str, websocket: WebSocket):

        async with self._lock:

            if key not in self.active_connections:
                return

            self.active_connections[key].discard(websocket)

            remaining = len(self.active_connections.get(key, []))
            if not self.active_connections[key]:
                del self.active_connections[key]

            logger.info(
                f"🔴 WebSocket client disconnected → {key} → remaining={remaining}"
            )

    # ================= BROADCAST =================

    async def broadcast_json(self, key: str, message: dict):

        logger.info(f"WS BROADCAST SENT - channel={key} message_type={message.get('type', 'unknown')}")

        async with self._lock:

            if key not in self.active_connections:
                logger.warning(f"⚠️ No active connections for channel: {key}")
                return

            connections = list(self.active_connections[key])

        dead = []
        
        for conn in connections:
            try:
                await conn.send_json(message)
            except Exception as e:
                dead.append(conn)
                logger.warning(f"❌ WS DEAD CLIENT REMOVED: {e}")

        # Remove dead connections
        if dead:
            async with self._lock:
                for d in dead:
                    if key in self.active_connections:
                        self.active_connections[key].discard(d)
                        if not self.active_connections[key]:
                            del self.active_connections[key]

        logger.info(
            f"WS BROADCAST COMPLETE - channel={key} sent={len(connections)-len(dead)} dead={len(dead)} total={len(connections)}"
        )

    async def _send_to_client(self, ws: WebSocket, message: dict):
        """Helper method to send message to a single client"""
        try:
            await ws.send_json(message)
            return True
        except Exception as e:
            # Handle WebSocket disconnect gracefully
            logger.debug(f"Failed to send to client (connection closed): {e}")
            return e
    
    async def send_heartbeat(self, key: str):
        """Send heartbeat ping to all clients in a channel"""
        # Disabled - do not send heartbeat messages to frontend
        # Frontend should only receive real market data
        logger.debug(f"Heartbeat disabled for channel {key}")
        pass
    
    async def start_heartbeat(self, key: str, interval: int = 10):
        """Start periodic heartbeat for a channel"""
        while True:
            try:
                await self.send_heartbeat(key)
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Heartbeat error for channel {key}: {e}")
                await asyncio.sleep(interval)


# singleton instance
manager = WSConnectionManager()