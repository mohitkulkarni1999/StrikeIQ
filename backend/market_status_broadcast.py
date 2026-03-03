"""
Market Status Broadcast - Backend WebSocket Integration
Broadcasts market status via WebSocket to prevent polling
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any
from websocket_manager import manager

class MarketStatusBroadcaster:
    def __init__(self):
        self.current_status = None
        self.last_broadcast = None
        self.broadcast_interval = 30  # seconds
        
    async def start_broadcasting(self):
        """Start broadcasting market status every 30 seconds"""
        while True:
            try:
                # Get current market status from your market session API
                market_status = await self.get_market_status()
                
                if market_status != self.current_status:
                    self.current_status = market_status
                    await manager.send_market_status(market_status)
                    print(f"📢 Market status broadcast: {market_status}")
                
                await asyncio.sleep(self.broadcast_interval)
                
            except Exception as e:
                print(f"❌ Market status broadcast error: {e}")
                await asyncio.sleep(5)  # retry after 5 seconds
    
    async def get_market_status(self) -> bool:
        """Get current market status - replace with your actual logic"""
        try:
            # This should integrate with your existing market session check
            # For now, return mock data - replace with actual API call
            import requests
            response = requests.get("http://localhost:8000/api/v1/market/session")
            data = response.json()
            
            # Backend returns { "market_status": "OPEN" }
            return data.get("market_status") == "OPEN"
            
        except Exception as e:
            print(f"Failed to get market status: {e}")
            return False
    
    async def broadcast_immediate(self, market_open: bool):
        """Broadcast market status immediately"""
        self.current_status = market_open
        await manager.send_market_status(market_open)
        print(f"🚀 Immediate market status broadcast: {market_open}")

# Global broadcaster instance
broadcaster = MarketStatusBroadcaster()

async def start_market_status_service():
    """Start the market status broadcasting service"""
    print("🚀 Starting Market Status Broadcasting Service")
    asyncio.create_task(broadcaster.start_broadcasting())
