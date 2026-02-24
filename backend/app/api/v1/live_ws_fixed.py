"""
Live WebSocket Endpoints - Live Option Chain Builder
Implements WS-scoped option chain building using Upstox V3 feed
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import WebSocket, WebSocketDisconnect, APIRouter, HTTPException
from app.services.live_option_chain_builder import get_live_chain_builder
from app.services.websocket_market_feed import ws_feed_manager
from app.services.upstox_auth_service import get_upstox_auth_service
from app.services.market_session_manager import get_market_session_manager

router = APIRouter(prefix="/ws", tags=["websocket"])
logger = logging.getLogger(__name__)

@router.websocket("/live-options/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str):
    """
    Live Option Chain Builder WebSocket endpoint
    Implements WS-scoped subscriptions and real-time chain building
    """
    
    # Handle expiry parameter from frontend
    expiry = websocket.query_params.get("expiry")
    if expiry in [None, "null", "None", "", "undefined"]:
        expiry = None
    
    logger.info(f"WebSocket connection - symbol: {symbol}, expiry: {expiry}")
    
    await websocket.accept()
    logger.info(f"WebSocket accepted for {symbol}")
    
    # Get services
    auth_service = get_upstox_auth_service()
    session_manager = get_market_session_manager()
    
    # Get shared WebSocket feed
    ws_feed_manager = WebSocketFeedManager()
    
    # Get shared feed instance
    ws_feed = await ws_feed_manager.get_feed()
    
    if not ws_feed:
        logger.error("Shared WebSocket feed not available")
        await websocket.send_json({
            "status": "error",
            "message": "WebSocket feed not initialized",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        return
    
    try:
        # Check authentication
        token = await auth_service.get_valid_access_token()
        if not token:
            logger.warning("Authentication required for WebSocket")
            await websocket.send_json({
                "status": "error",
                "message": "Authentication required",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            return
        
        # Send initial connection message
        await websocket.send_json({
            "status": "connected",
            "symbol": symbol,
            "message": "WebSocket connection successful",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Get market status
        market_status = str(session_manager.market_status)
        
        # Force LIVE mode when market is OPEN
        if market_status == "OPEN":
            current_engine_mode = session_manager.get_engine_mode()
            if current_engine_mode.value != "LIVE":
                logger.info(f"Market is OPEN, forcing LIVE mode (was {current_engine_mode.value})")
                await session_manager.update_market_status()
        
        # STEP 1: Initialize option chain structure
        try:
            builder = get_live_chain_builder()
            chain_state = await builder.initialize_chain(symbol, expiry)
            logger.info(f"Initialized option chain for {symbol}: {len(chain_state.strike_map)} strikes")
        except Exception as e:
            logger.error(f"Failed to initialize option chain for {symbol}: {e}")
            await websocket.send_json({
                "status": "error",
                "message": f"Failed to initialize option chain: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            return
        
        # STEP 2: Connect to WebSocket feed
        if not await ws_feed.connect():
            logger.error(f"Failed to connect WebSocket feed for {symbol}")
            await websocket.send_json({
                "status": "error",
                "message": "Failed to connect to market data feed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            return
        
        # STEP 3: Subscribe to specific instruments (ATM window)
        # Initial subscription will be empty until spot price is received
        builder = get_live_chain_builder()
        instrument_keys = await builder.subscribe_to_instruments(symbol)
        
        if instrument_keys:
            if not await ws_feed.subscribe_to_instruments(instrument_keys):
                logger.error(f"Failed to subscribe to instruments for {symbol}")
                await websocket.send_json({
                    "status": "error",
                    "message": "Failed to subscribe to market data",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                return
        else:
            logger.info(f"Waiting for spot price before subscribing to {symbol} instruments")
        
        # STEP 4: Start feed processing in background
        feed_task = asyncio.create_task(ws_feed.start_feed_loop())
        
        logger.info(f"Started live option chain builder for {symbol}")
        
        # STEP 5: Continuous broadcasting loop (main thread)
        try:
            while True:
                try:
                    # Build final option chain payload
                    builder = get_live_chain_builder()
                    payload = await builder.build_chain_payload(symbol)
                    
                    if payload:
                        # Add market status
                        payload["market_status"] = market_status
                        
                        # Send to client
                        await websocket.send_json({
                            "status": "market_data",
                            **payload
                        })
                    
                    # Wait 500ms before next update
                    await asyncio.sleep(0.5)
                    
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected during broadcast for {symbol}")
                    break
                except Exception as e:
                    logger.error(f"Error broadcasting chain update for {symbol}: {e}")
                    await asyncio.sleep(1)  # Wait longer on error
        
        finally:
            # Cleanup background feed task properly
            if feed_task:
                feed_task.cancel()
                try:
                    await feed_task
                except asyncio.CancelledError:
                    logger.debug(f"Background feed task cancelled for {symbol}")
                except Exception as e:
                    logger.error(f"Error cancelling feed task for {symbol}: {e}")
            
            # Note: Shared WebSocket feed is managed globally, no per-symbol cleanup needed
            logger.info(f"Cleaned up resources for {symbol} (shared feed preserved)")
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for {symbol}")
    except Exception as e:
        logger.error(f"WebSocket error for {symbol}: {e}")
        await websocket.send_json({
            "status": "error",
            "message": f"WebSocket error: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    finally:
        # Final cleanup in case of any error
        if feed_task:
            feed_task.cancel()
            try:
                await feed_task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass
