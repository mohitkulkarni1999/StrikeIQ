"""
Backend WebSocket Market Status Broadcasting
Sends market status updates via WebSocket to eliminate polling
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List
from fastapi import WebSocket

class MarketStatusBroadcaster:
    def __init__(self):
        self.connections: List[WebSocket] = []
        self.current_status = None
        self.last_broadcast_time = None
        self.broadcast_interval = 30  # seconds
        
    async def add_connection(self, websocket: WebSocket):
        """Add new WebSocket connection"""
        self.connections.append(websocket)
        print(f"📡 Market status broadcaster: connection added | total={len(self.connections)}")
        
        # Send current status immediately to new connection
        if self.current_status is not None:
            await self.send_to_connection(websocket, {
                "type": "market_status",
                "market_open": self.current_status,
                "timestamp": datetime.now().isoformat()
            })
    
    async def remove_connection(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.connections:
            self.connections.remove(websocket)
            print(f"📡 Market status broadcaster: connection removed | total={len(self.connections)}")
    
    async def update_market_status(self, market_open: bool):
        """Update and broadcast market status"""
        if market_open != self.current_status:
            self.current_status = market_open
            self.last_broadcast_time = datetime.now()
            
            message = {
                "type": "market_status",
                "market_open": market_open,
                "timestamp": self.last_broadcast_time.isoformat()
            }
            
            await self.broadcast_to_all(message)
            print(f"📢 Market status broadcast: {market_open} | connections={len(self.connections)}")
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients with dead client cleanup"""
        if not self.connections:
            return
            
        dead_connections = []
        
        for connection in self.connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"❌ Dead client detected in market status broadcast: {e}")
                dead_connections.append(connection)
        
        # Clean up dead connections
        for dead_connection in dead_connections:
            await self.remove_connection(dead_connection)
            print(f"🗑️ Removed dead connection from market status broadcaster")
    
    async def send_to_connection(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"❌ Failed to send market status to connection: {e}")
            await self.remove_connection(websocket)
    
    async def start_status_monitoring(self):
        """Start monitoring market status and broadcasting changes"""
        print("🚀 Starting Market Status Monitoring Service")
        
        while True:
            try:
                # Get current market status from your existing API
                market_open = await self.get_market_status_from_api()
                
                if market_open != self.current_status:
                    await self.update_market_status(market_open)
                
                await asyncio.sleep(self.broadcast_interval)
                
            except Exception as e:
                print(f"❌ Market status monitoring error: {e}")
                await asyncio.sleep(5)  # retry after 5 seconds
    
    async def get_market_status_from_api(self) -> bool:
        """Get market status from existing API endpoint"""
        try:
            import requests
            response = requests.get("http://localhost:8000/api/v1/market/session", timeout=5)
            data = response.json()
            
            # Backend returns { "market_status": "OPEN" }
            return data.get("market_status") == "OPEN"
            
        except Exception as e:
            print(f"❌ Failed to get market status from API: {e}")
            return self.current_status or False

# Global broadcaster instance
market_status_broadcaster = MarketStatusBroadcaster()

async def start_market_status_service():
    """Start market status broadcasting service"""
    print("🚀 Starting Market Status Broadcasting Service")
    asyncio.create_task(market_status_broadcaster.start_status_monitoring())
