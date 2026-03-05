from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect
import asyncio
import logging

logger = logging.getLogger(__name__)

# Global broadcast lock
broadcast_lock = asyncio.Lock()

class WSManager:

    def __init__(self):

        # Use set to prevent duplicates and allow O(1) operations
        self.connections: set[WebSocket] = set()

        # Lock prevents race conditions during connect/disconnect
        self._lock = asyncio.Lock()
        
        # Instance broadcast lock
        self.broadcast_lock = asyncio.Lock()


    async def connect(self, websocket: WebSocket):

        async with self._lock:

            # Prevent duplicate connection BEFORE accepting
            if websocket in self.connections:

                logger.warning(
                    "⚠️ Duplicate websocket connection ignored"
                )
                return

            await websocket.accept()

            self.connections.add(websocket)

            logger.info(f"🟢 WebSocket client connected | clients={len(self.connections)}")


    async def disconnect(self, websocket: WebSocket):

        async with self._lock:

            if websocket in self.connections:

                self.connections.remove(websocket)

                logger.info(
                    f"🔴 WebSocket client disconnected | clients={len(self.connections)}"
                )


    async def broadcast(self, message):
        """Broadcast message to all connected clients concurrently"""
        async with self.broadcast_lock:
            if not self.connections:
                return  # No connections to broadcast to

            # Create list of send tasks
            send_tasks = []
            dead_connections = []

            for connection in self.connections:
                send_tasks.append(
                    self._send_with_error_handling(connection, message, dead_connections)
                )

            # Execute all sends concurrently
            if send_tasks:
                await asyncio.gather(*send_tasks, return_exceptions=True)

            # Remove dead connections
            for conn in dead_connections:
                if conn in self.connections:
                    self.connections.remove(conn)

            if dead_connections:
                logger.info(f"Removed {len(dead_connections)} dead connections")

    async def _send_with_error_handling(self, connection, message, dead_connections):
        """Send message to a single connection with error handling"""
        try:
            await connection.send_json(message)
        except Exception as e:
            dead_connections.append(connection)
            logger.debug(f"Failed to send to connection: {e}")


# singleton instance
manager = WSManager()
