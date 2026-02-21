"""
Live WebSocket Endpoints - Enhanced with Real Upstox Feed Integration
Provides real-time market data and analytics to frontend
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import WebSocket, WebSocketDisconnect, APIRouter, HTTPException
from app.services.upstox_market_feed import UpstoxMarketFeed, FeedConfig
from app.services.live_structural_engine import LiveStructuralEngine
from app.services.token_manager import get_token_manager
from app.services.upstox_auth_service import get_upstox_auth_service
from app.core.live_market_state import MarketStateManager

router = APIRouter(prefix="/ws", tags=["websocket"])
logger = logging.getLogger(__name__)

# Global instances
market_state_manager = MarketStateManager()
live_analytics_engine = LiveStructuralEngine(market_state_manager)
upstox_feeds: Dict[str, UpstoxMarketFeed] = {}
token_manager = get_token_manager()
auth_service = get_upstox_auth_service()

@router.websocket("/live-options/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str):
    """
    Enhanced WebSocket endpoint for live options data streaming.
    Sends real-time analytics instead of simple heartbeats.
    """
    print(f"WebSocket connection attempt - symbol: {symbol}")
    logger.info(f"WebSocket connection attempt - symbol: {symbol}")
    
    try:
        # Check token validity first
        token = await auth_service.get_valid_access_token()
        if not token:
            logger.warning("Authentication required for WebSocket: No valid credentials available")
            raise HTTPException(status_code=403, detail="Upstox authentication required")
        
        await websocket.accept()
        print(f"WebSocket accepted for {symbol}")
        logger.info(f"WebSocket accepted for {symbol}")
        
        # Initialize Upstox feed if not already running
        if symbol not in upstox_feeds:
            config = FeedConfig(
                symbol=symbol,
                spot_instrument_key=get_spot_instrument_key(symbol),
                strike_range=10,
                mode="full"
            )
            
            feed = UpstoxMarketFeed(config, market_state_manager)
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
        print(f"Connection message sent to {symbol}")
        
        # Main message loop - send live analytics and market data every second
        while True:
            try:
                # Get latest analytics for symbol
                analytics_data = await live_analytics_engine.get_metrics_for_frontend(symbol)
                
                # Get live market data from Upstox feed
                market_data = {}
                if symbol in upstox_feeds:
                    feed = upstox_feeds[symbol]
                    market_snapshot = await feed.market_state.get_market_snapshot(symbol)
                    if market_snapshot:
                        market_data = {
                            "current_spot": market_snapshot.get("spot"),
                            "spot_change": market_snapshot.get("spot_change", 0),
                            "spot_change_percent": market_snapshot.get("spot_change_percent", 0),
                            "market_status": "active",
                            "last_update": market_snapshot.get("last_update")
                        }
                
                if analytics_data or market_data:
                    # Combine analytics and market data
                    combined_data = {
                        "status": "live_update",
                        "symbol": symbol,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "analytics": analytics_data,
                        "market_data": market_data
                    }
                    
                    # Send to frontend
                    await websocket.send_json(combined_data)
                    print(f"Live update sent to {symbol}: Analytics={bool(analytics_data)}, Market Data={bool(market_data)}")
                    
                    # Show specific changing values
                    if market_data:
                        spot = market_data.get("current_spot")
                        change = market_data.get("spot_change", 0)
                        change_pct = market_data.get("spot_change_percent", 0)
                        if spot and change != 0:
                            print(f" {symbol}: {spot} ({change:+.2f}, {change_pct:+.2f}%)")
                        elif change_pct != 0:
                            print(f" {symbol}: {spot} ({change_pct:+.2f}%)")
                        else:
                            print(f" {symbol}: {spot} (no change)")
                
                else:
                    # Send heartbeat if no data available yet
                    await websocket.send_json({
                        "status": "heartbeat",
                        "symbol": symbol,
                        "message": "Market data connecting...",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                
                # Wait before next update
                await asyncio.sleep(1)
                
            except WebSocketDisconnect:
                print(f"WebSocket disconnected for {symbol}")
                break
            except Exception as e:
                print(f"Error sending analytics to {symbol}: {e}")
                await asyncio.sleep(1)
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for {symbol}")
    except HTTPException as e:
        if e.status_code == 401:
            print(f"Authentication required for {symbol}")
            logger.warning(f"Authentication required for WebSocket: {e.detail}")
            
            # Send auth_required message before closing
            try:
                await websocket.send_json({
                    "status": "auth_required",
                    "message": "Authentication required",
                    "detail": e.detail,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                await asyncio.sleep(0.1)  # Brief delay to ensure message is sent
            except:
                pass
            finally:
                try:
                    await websocket.close()
                except:
                    pass
        else:
            print(f"❌ HTTP error for {symbol}: {e}")
            try:
                await websocket.close()
            except:
                pass
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
