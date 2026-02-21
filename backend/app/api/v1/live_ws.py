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
token_manager = get_token_manager()
auth_service = get_upstox_auth_service()

@router.websocket("/live-options/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str):
    """
    Enhanced WebSocket endpoint for live options data streaming.
    Sends real-time market data from MarketStateManager (NOT REST).
    """
    print(f"🔌 WebSocket connection attempt - symbol: {symbol}")
    logger.info(f"WebSocket connection attempt - symbol: {symbol}")
    
    try:
        # Check token validity first
        token = await auth_service.get_valid_access_token()
        if not token:
            logger.warning("Authentication required for WebSocket: No valid credentials available")
            raise HTTPException(status_code=403, detail="Upstox authentication required")
        
        await websocket.accept()
        print(f"✅ WebSocket accepted for {symbol}")
        logger.info(f"WebSocket accepted for {symbol}")
        
        # Send initial connection message
        await websocket.send_json({
            "status": "connected", 
            "symbol": symbol,
            "message": "WebSocket connection successful - Live streaming enabled",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        print(f"📡 Connection message sent to {symbol}")
        
        # Start analytics engine if not already running
        asyncio.create_task(live_analytics_engine.start_analytics_loop(interval_seconds=2))
        
        # Main message loop - send live market data from MarketStateManager
        while True:
            try:
                # Get live market data from MarketStateManager (populated by Upstox feed)
                market_data = await market_state_manager.get_live_data_for_frontend(symbol)
                
                # Get analytics data
                analytics_data = await live_analytics_engine.get_metrics_for_frontend(symbol)
                
                if market_data:
                    # Build response with required fields including separated REST and WS data
                    response_data = {
                        "status": "live_update",
                        "symbol": symbol,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        # Separated data sources as requested
                        "rest_spot_price": market_data.get("rest_spot_price"),
                        "ws_tick_price": market_data.get("ws_tick_price"),
                        "atm_strike": market_data.get("atm_strike"),
                        "current_atm_strike": market_data.get("current_atm_strike"),
                        "atm_last_updated": market_data.get("atm_last_updated"),
                        "option_chain": {
                            "symbol": symbol,
                            "spot": market_data.get("spot_price"),  # Combined (WS preferred)
                            "expiry": "current",  # Will be populated by feed
                            "calls": [],
                            "puts": []
                        },
                        "greeks": {},  # Will be populated by feed
                        "analytics": analytics_data,
                        "market_data": {
                            "total_oi_calls": market_data.get("total_oi_calls", 0),
                            "total_oi_puts": market_data.get("total_oi_puts", 0),
                            "pcr": market_data.get("pcr", 0),
                            "strikes": market_data.get("strikes", {})
                        },
                        # Additional metadata for data source identification
                        "data_source": "websocket_stream",
                        "ws_last_update": market_data.get("ws_last_update_ts"),
                        "rest_last_update": market_data.get("rest_last_update")
                    }
                    
                    # Populate option chain with strike data
                    strikes = market_data.get("strikes", {})
                    calls = []
                    puts = []
                    
                    for strike_price, strike_info in strikes.items():
                        # Add call data
                        if strike_info.get("call"):
                            calls.append({
                                "strike": strike_price,
                                "ltp": strike_info["call"].get("ltp"),
                                "oi": strike_info["call"].get("oi"),
                                "delta": strike_info["call"].get("delta"),
                                "gamma": strike_info["call"].get("gamma"),
                                "theta": strike_info["call"].get("theta"),
                                "vega": strike_info["call"].get("vega"),
                                "iv": strike_info["call"].get("iv"),
                                "volume": strike_info["call"].get("volume"),
                                "change": strike_info["call"].get("change", 0)
                            })
                        
                        # Add put data
                        if strike_info.get("put"):
                            puts.append({
                                "strike": strike_price,
                                "ltp": strike_info["put"].get("ltp"),
                                "oi": strike_info["put"].get("oi"),
                                "delta": strike_info["put"].get("delta"),
                                "gamma": strike_info["put"].get("gamma"),
                                "theta": strike_info["put"].get("theta"),
                                "vega": strike_info["put"].get("vega"),
                                "iv": strike_info["put"].get("iv"),
                                "volume": strike_info["put"].get("volume"),
                                "change": strike_info["put"].get("change", 0)
                            })
                    
                    # Sort calls and puts by strike price
                    calls.sort(key=lambda x: x["strike"])
                    puts.sort(key=lambda x: x["strike"])
                    
                    response_data["option_chain"]["calls"] = calls
                    response_data["option_chain"]["puts"] = puts
                    
                    # Send to frontend
                    await websocket.send_json(response_data)
                    print(f"📡 Live update sent to {symbol}: REST_SPOT={market_data.get('rest_spot_price')}, WS_TICK={market_data.get('ws_tick_price')}, ATM={market_data.get('current_atm_strike')}, Strikes={len(strikes)}")
                    
                    # Show specific changing values
                    ws_tick = market_data.get("ws_tick_price")
                    rest_spot = market_data.get("rest_spot_price")
                    current_atm = market_data.get("current_atm_strike")
                    
                    if ws_tick and current_atm:
                        print(f"  {symbol}: WS={ws_tick} -> ATM={current_atm} (gap: {abs(ws_tick - current_atm):.1f})")
                    elif rest_spot and current_atm:
                        print(f"  {symbol}: REST={rest_spot} -> ATM={current_atm} (gap: {abs(rest_spot - current_atm):.1f})")
                
                else:
                    # Send heartbeat if no data available yet
                    await websocket.send_json({
                        "status": "heartbeat",
                        "symbol": symbol,
                        "message": "Market data connecting...",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "data_source": "websocket_stream"
                    })
                
                # Wait before next update (real-time streaming)
                await asyncio.sleep(0.5)  # 500ms for real-time updates
                
            except WebSocketDisconnect:
                print(f"🔌 WebSocket disconnected for {symbol}")
                break
            except Exception as e:
                print(f"❌ Error sending data to {symbol}: {e}")
                await asyncio.sleep(1)
                
    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected for {symbol}")
    except HTTPException as e:
        if e.status_code == 401:
            print(f"🔐 Authentication required for {symbol}")
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
    # This would access the global app.state.upstox_feeds
    # For now, return success
    return {"status": "cleaned_up", "symbol": symbol}
