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
                f"🟢 WS CONNECTED → {key} → {len(self.active_connections[key])} clients"
            )

    # ================= DISCONNECT =================

    async def disconnect(self, key: str, websocket: WebSocket):

        async with self._lock:

            if key not in self.active_connections:
                return

            self.active_connections[key].discard(websocket)

            if not self.active_connections[key]:
                del self.active_connections[key]

            logger.info(
                f" WS DISCONNECTED → {key} → remaining={len(self.active_connections.get(key, []))}"
            )

    # ================= BROADCAST =================

    async def broadcast_json(self, key: str, message: dict):

        async with self._lock:

            if key not in self.active_connections:
                logger.warning(f"⚠️ No active connections for channel: {key}")
                return

            connections = list(self.active_connections[key])

        dead_connections = []
        
        # Parallel broadcast using asyncio.gather for 1000+ concurrent connections
        send_tasks = []
        for ws in connections:
            send_tasks.append(self._send_to_client(ws, message))
        
        results = await asyncio.gather(*send_tasks, return_exceptions=True)
        
        sent_count = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                dead_connections.append(connections[i])
                logger.warning(f"❌ Failed to send to client: {result}")
            else:
                sent_count += 1

        # cleanup dead sockets
        if dead_connections:

            async with self._lock:

                for ws in dead_connections:

                    if key in self.active_connections:
                        self.active_connections[key].discard(ws)

                if key in self.active_connections and not self.active_connections[key]:
                    del self.active_connections[key]

        logger.info(
            f" BROADCAST → {key} → sent={sent_count} dead={len(dead_connections)} total={len(connections)}"
        )
        
        # Log the actual message being broadcasted
        logger.debug(f" Message broadcasted: {message}")

    async def _send_to_client(self, ws: WebSocket, message: dict):
        """Helper method to send message to a single client"""
        try:
            await ws.send_json(message)
            return True
        except Exception as e:
            return e


# singleton instance
manager = WSConnectionManager()