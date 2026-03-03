"""
WebSocket Manager with Full Debug Logging
Handles client connections, broadcasting, and dead client cleanup with trace tracking
"""

from typing import List, Set
from fastapi import WebSocket
import json
import asyncio
from core.logger import ws_logger, get_trace_id

class WebSocketManager:
    def __init__(self):
        # Store active connections
        self.active_connections: List[WebSocket] = []
        self.dead_clients: Set[WebSocket] = set()
        self.broadcast_count = 0
        self.client_connect_count = 0
        self.client_disconnect_count = 0

    async def connect(self, websocket: WebSocket):
        """Accept and store new WebSocket connection with logging"""
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            self.client_connect_count += 1
            
            ws_logger.info(f"WS CLIENT CONNECTED trace={get_trace_id()} client_id={id(websocket)} total_clients={len(self.active_connections)} total_connects={self.client_connect_count}")
            
        except Exception as e:
            ws_logger.error(f"WS CONNECT ERROR trace={get_trace_id()} error={str(e)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection with logging"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.client_disconnect_count += 1
            
            ws_logger.info(f"WS CLIENT DISCONNECTED trace={get_trace_id()} client_id={id(websocket)} total_clients={len(self.active_connections)} total_disconnects={self.client_disconnect_count}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients with dead client cleanup and logging"""
        if not self.active_connections:
            ws_logger.debug(f"WS BROADCAST SKIPPED trace={get_trace_id()} reason=no_clients")
            return

        # Log broadcast start
        message_type = message.get('type', 'unknown')
        ws_logger.info(f"WS BROADCAST START trace={get_trace_id()} type={message_type} clients={len(self.active_connections)}")

        dead_clients = []
        successful_sends = 0
        
        # Send message to all connected clients
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
                successful_sends += 1
                ws_logger.debug(f"WS SEND SUCCESS trace={get_trace_id()} client_id={id(connection)} type={message_type}")
                
            except Exception as e:
                ws_logger.warning(f"WS CLIENT DEAD trace={get_trace_id()} client_id={id(connection)} error={str(e)}")
                dead_clients.append(connection)
        
        # Clean up dead clients
        for dead_client in dead_clients:
            self.disconnect(dead_client)
            ws_logger.info(f"WS CLIENT REMOVED trace={get_trace_id()} client_id={id(dead_client)}")
        
        self.broadcast_count += 1
        
        ws_logger.info(f"WS BROADCAST COMPLETE trace={get_trace_id()} type={message_type} successful={successful_sends} dead={len(dead_clients)} active={len(self.active_connections)} total_broadcasts={self.broadcast_count}")

    async def send_market_data(self, market_data: dict):
        """Send market data with specific logging"""
        await self.broadcast({
            "type": "market_data",
            "data": market_data,
            "timestamp": market_data.get('timestamp'),
            "trace_id": get_trace_id()
        })

    async def send_heatmap(self, heatmap_data: dict):
        """Send heatmap data with specific logging"""
        await self.broadcast({
            "type": "heatmap",
            "data": heatmap_data,
            "timestamp": heatmap_data.get('timestamp'),
            "trace_id": get_trace_id()
        })

    async def send_market_status(self, market_open: bool):
        """Send market status with specific logging"""
        await self.broadcast({
            "type": "market_status",
            "market_open": market_open,
            "timestamp": asyncio.get_event_loop().time(),
            "trace_id": get_trace_id()
        })

    def get_stats(self) -> dict:
        """Get WebSocket manager statistics"""
        return {
            "active_connections": len(self.active_connections),
            "broadcast_count": self.broadcast_count,
            "client_connect_count": self.client_connect_count,
            "client_disconnect_count": self.client_disconnect_count,
            "dead_clients": len(self.dead_clients)
        }

    async def send_chain_update(self, data: dict):
        """Send options chain update"""
        message = {
            "type": "chain_update",
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast(message)

    async def send_market_tick(self, data: dict):
        """Send market tick update"""
        message = {
            "type": "market_tick",
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast(message)

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)

# Global WebSocket manager instance
manager = WebSocketManager()
