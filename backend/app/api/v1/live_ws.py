"""
Live WebSocket Endpoints - Live Option Chain Builder
Implements WS-scoped option chain building using Upstox V3 feed
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import WebSocket, WebSocketDisconnect, APIRouter, HTTPException
from app.services.websocket_market_feed import WebSocketFeedManager, ws_feed_manager
from app.services.upstox_auth_service import get_upstox_auth_service
from app.services.market_session_manager import get_market_session_manager
from app.services.live_option_chain_builder import get_live_chain_builder, LiveOptionChainBuilder

router = APIRouter(prefix="/ws", tags=["websocket"])
logger = logging.getLogger(__name__)

async def safe_cancel_task(task: Optional[asyncio.Task]) -> None:
    """
    Safely cancel a background task without double cancellation
    """
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass  # Expected cancellation
        except Exception as e:
            logger.error(f"Error cancelling task: {e}")

async def stream_live_chain(symbol: str, websocket: WebSocket, builder: LiveOptionChainBuilder):
    """
    STEP 2: Background broadcast loop for live option chain updates
    """
    logger.info(f"Starting broadcast stream for {symbol}")
    try:
        from app.services.market_session_manager import get_market_session_manager
        session_manager = get_market_session_manager()
        
        while True:
            try:
                # Build final option chain payload from global builder
                payload = await builder.build_chain_payload(symbol)
                
                if payload:
                    # Add market status structure if needed, but user didn't specify it in Step 2.
                    # However, they said "Expected: client receives market_data every second."
                    # Structure: {"status": "market_data", "data": payload}
                    await websocket.send_json({
                        "status": "market_data",
                        "data": payload,
                        "market_status": str(session_manager.market_status),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                
                # STEP 2: Wait 1 second before next update
                await asyncio.sleep(1)
                
            except (WebSocketDisconnect, RuntimeError):
                # Connection closed
                logger.info(f"Broadcast loop detected disconnect for {symbol}, stopping.")
                break
            except Exception as e:
                logger.error(f"Error in broadcast loop for {symbol}: {e}")
                await asyncio.sleep(2)
                
    except asyncio.CancelledError:
        logger.info(f"Broadcast stream cancelled for {symbol}")
    except Exception as e:
        logger.error(f"Broadcast stream error for {symbol}: {e}")

@router.websocket("/live-options/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str, expiry: Optional[str] = None, expiry_date: Optional[str] = None):
    """
    Live Option Chain Builder WebSocket endpoint
    Implements WS-scoped subscriptions and real-time chain building
    """
    
    # Handle expiry parameter from frontend - support both formats
    final_expiry = expiry or expiry_date
    
    if not final_expiry or final_expiry in [None, "null", "None", "", "undefined"]:
        raise ValueError("Expiry is required for option chain")
    
    logger.info(f"WebSocket connection - symbol: {symbol}, expiry: {final_expiry}")
    
    await websocket.accept()
    logger.info(f"WebSocket accepted for {symbol}")
    
    # Get services
    auth_service = get_upstox_auth_service()
    session_manager = get_market_session_manager()
    
    # Get shared WebSocket feed (reuse existing)
    ws_feed = ws_feed_manager.feed

    if not ws_feed or not ws_feed.is_connected:
        await websocket.close(code=1011)
        print("🔴 WS FEED NOT RUNNING")
        return
    feed_task: Optional[asyncio.Task] = None
    
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
        
        # GET SHARED FEED FROM APP STATE
        upstox_feeds = getattr(websocket.app.state, 'upstox_feeds', {})
        ws_feed = upstox_feeds.get('shared')
        
        if not ws_feed:
            logger.error("Shared WebSocket feed not available")
            await websocket.send_json({
                "status": "error",
                "message": "WebSocket feed not initialized",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            return

        # Use factory function to get builder instance
        builder = get_live_chain_builder()
        
        # Initialize chain if not already done
        try:
            await builder.initialize_option_chain(symbol, final_expiry)
            logger.info("Initialized builder for %s", symbol)
        except Exception as e:
            logger.warning(f"Builder already initialized for {symbol} or initialization failed: {e}")

        logger.info(f"Using shared feed for {symbol}")
        
        # STEP 1: Start background broadcast task using the shared builder
        broadcast_task = asyncio.create_task(stream_live_chain(symbol, websocket, builder))
        
        try:
            # Keep connection open and listen for messages or disconnect
            while True:
                data = await websocket.receive_text()
                # Handle incoming messages if any...
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for {symbol}")
        finally:
            # Clean up background task
            await safe_cancel_task(broadcast_task)
            logger.info(f"Client stream for {symbol} disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error for {symbol}: {e}")
        try:
            await websocket.send_json({
                "status": "error",
                "message": f"WebSocket error: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except:
            pass
