"""
WebSocket endpoint for live options data streaming.
Implements single source of truth architecture.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.routing import APIRouter

from app.services.market_data.option_chain_service import OptionChainService
from app.services.upstox_auth_service import get_upstox_auth_service, UpstoxAuthService
from app.services.live_analytics_engine import LiveAnalyticsEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])

# Global live analytics engine
live_engine = LiveAnalyticsEngine()

class WebSocketManager:
    """Manages WebSocket connections for live data streaming"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.symbol_subscriptions: Dict[str, set] = {}
    
    async def connect(self, websocket: WebSocket, symbol: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[symbol] = websocket
        if symbol not in self.symbol_subscriptions:
            self.symbol_subscriptions[symbol] = set()
        self.symbol_subscriptions[symbol].add(websocket)
        
        logger.info(f"WebSocket connected for {symbol}. Total connections: {len(self.active_connections)}")
        
        # Send initial snapshot immediately
        await self.send_snapshot(websocket, symbol)
    
    async def disconnect(self, websocket: WebSocket, symbol: str):
        """Handle WebSocket disconnection"""
        if symbol in self.active_connections:
            del self.active_connections[symbol]
        if symbol in self.symbol_subscriptions:
            self.symbol_subscriptions[symbol].discard(websocket)
            if not self.symbol_subscriptions[symbol]:
                del self.symbol_subscriptions[symbol]
        
        logger.info(f"WebSocket disconnected for {symbol}. Active connections: {len(self.active_connections)}")
    
    async def send_snapshot(self, websocket: WebSocket, symbol: str):
        """Send initial snapshot to WebSocket client"""
        try:
            # Get existing snapshot data using current REST service
            auth_service = get_upstox_auth_service()
            option_service = OptionChainService(auth_service)
            
            # Use nearest expiry for snapshot
            snapshot_data = await option_service.get_option_chain(symbol)
            
            if snapshot_data and "status" not in snapshot_data:
                # Convert to WebSocket format
                ws_message = {
                    "status": "success",
                    "mode": "snapshot",
                    "data": {
                        "symbol": snapshot_data.get("symbol"),
                        "spot": snapshot_data.get("spot"),
                        "expiry": snapshot_data.get("expiry"),
                        "calls": snapshot_data.get("calls", []),
                        "puts": snapshot_data.get("puts", []),
                        "analytics": snapshot_data.get("analytics", {}),
                        "intelligence": snapshot_data.get("intelligence", {}),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                }
                
                await websocket.send_text(json.dumps(ws_message))
                logger.info(f"Sent snapshot for {symbol} via WebSocket")
            else:
                # Send error snapshot
                error_message = {
                    "status": "error",
                    "mode": "snapshot",
                    "error": "Failed to fetch initial data",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await websocket.send_text(json.dumps(error_message))
                
        except Exception as e:
            logger.error(f"Error sending snapshot for {symbol}: {e}")
            error_message = {
                "status": "error",
                "mode": "snapshot",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await websocket.send_text(json.dumps(error_message))
    
    async def broadcast_live_update(self, symbol: str, live_data: Dict[str, Any]):
        """Broadcast live update to all subscribers of a symbol"""
        if symbol not in self.symbol_subscriptions:
            return
        
        ws_message = {
            "status": "success",
            "mode": "live",
            "data": {
                "symbol": symbol,
                **live_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Send to all connected clients for this symbol
        disconnected = set()
        for websocket in self.symbol_subscriptions[symbol]:
            try:
                await websocket.send_text(json.dumps(ws_message))
            except Exception as e:
                logger.warning(f"Failed to send live update to client: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected:
            self.symbol_subscriptions[symbol].discard(websocket)
        
        logger.info(f"Broadcasted live update for {symbol} to {len(self.symbol_subscriptions[symbol])} clients")

# Global WebSocket manager
manager = WebSocketManager()

"""
Live WebSocket Endpoints
Provides real-time market data and analytics to frontend
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import WebSocket, WebSocketDisconnect, HTTPException, APIRouter
from app.services.upstox_market_feed import UpstoxMarketFeed, FeedConfig
from app.services.live_structural_engine import LiveStructuralEngine
from app.core.live_market_state import MarketStateManager

router = APIRouter(prefix="/ws", tags=["websocket"])
logger = logging.getLogger(__name__)

# Global instances
market_state_manager = MarketStateManager()
live_analytics_engine = LiveStructuralEngine(market_state_manager)
upstox_feeds: Dict[str, UpstoxMarketFeed] = {}

@router.websocket("/live-options/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str):
    """
    Enhanced WebSocket endpoint for live options data streaming.
    Sends real-time analytics instead of simple heartbeats.
    """
    print(f"🔌 WebSocket connection attempt - symbol: {symbol}")
    logger.info(f"WebSocket connection attempt - symbol: {symbol}")
    
    try:
        await websocket.accept()
        print(f"✅ WebSocket accepted for {symbol}")
        logger.info(f"WebSocket accepted for {symbol}")
        
        # Initialize Upstox feed if not already running
        if symbol not in upstox_feeds:
            config = FeedConfig(
                symbol=symbol,
                spot_instrument_key=get_spot_instrument_key(symbol),
                strike_range=10,
                mode="full"
            )
            
            feed = UpstoxMarketFeed(config)
            upstox_feeds[symbol] = feed
            
            # Start the feed in background
            await feed.start()
            
            # Start analytics engine if not already running
            asyncio.create_task(live_analytics_engine.start_analytics_loop(interval_seconds=2))
        
        # Send initial connection message
        await websocket.send_json({
            "status": "connected", 
            "symbol": symbol,
            "message": "WebSocket connection successful - Live analytics enabled",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        print(f"📡 Connection message sent to {symbol}")
        
        # Main message loop - send live analytics every second
        while True:
            try:
                # Get latest analytics for the symbol
                analytics_data = await live_analytics_engine.get_metrics_for_frontend(symbol)
                
                if analytics_data:
                    # Add metadata
                    analytics_data.update({
                        "status": "live_update",
                        "symbol": symbol,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
                    # Send to frontend
                    await websocket.send_json(analytics_data)
                    print(f"📊 Analytics sent to {symbol}: Expected Move={analytics_data.get('expected_move', 'N/A')}, Intent={analytics_data.get('intent_score', 'N/A')}")
                else:
                    # Send heartbeat if no analytics available yet
                    await websocket.send_json({
                        "status": "heartbeat",
                        "symbol": symbol,
                        "message": "Analytics computing...",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                
                # Wait before next update
                await asyncio.sleep(1)
                
            except WebSocketDisconnect:
                print(f"🔌 WebSocket disconnected for {symbol}")
                break
            except Exception as e:
                print(f"❌ Error sending analytics to {symbol}: {e}")
                await asyncio.sleep(1)
                
    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected for {symbol}")
    except Exception as e:
        print(f"❌ WebSocket error for {symbol}: {e}")
        try:
            await websocket.close()
        except:
            pass

def get_spot_instrument_key(symbol: str) -> str:
    """
    Get spot instrument key for symbol
    """
    symbol_mapping = {
        "NIFTY": "NSE_INDEX|Nifty 50",
        "BANKNIFTY": "NSE_INDEX|Nifty Bank",
        "FINNIFTY": "NSE_INDEX|Nifty Fin Service"
    }
    return symbol_mapping.get(symbol.upper(), f"NSE_INDEX|{symbol}")

@router.websocket("/test")
async def test_ws(websocket: WebSocket):
    """Simple test WebSocket endpoint"""
    print("🔌 Test WebSocket connection attempt")
    try:
        await websocket.accept()
        print("✅ Test WebSocket accepted")
        
        while True:
            await websocket.send_text("ping")
            print("📡 Sent ping")
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"❌ Test WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass

# Cleanup endpoint for graceful shutdown
@router.post("/cleanup/{symbol}")
async def cleanup_feed(symbol: str):
    """Cleanup Upstox feed for a symbol"""
    if symbol in upstox_feeds:
        await upstox_feeds[symbol].stop()
        del upstox_feeds[symbol]
        return {"status": "cleaned_up", "symbol": symbol}
    return {"status": "not_found", "symbol": symbol}
