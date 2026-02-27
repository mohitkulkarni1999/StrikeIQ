#!/usr/bin/env python3
"""
Trace Data Flow Through WebSocket Pipeline
Adds temporary debug logging to track exact data movement
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Patch the WebSocket feed to add debug logging
original_process_loop = None

async def debug_process_loop(self):
    """Debug version of _process_loop with detailed logging"""
    print("🔍 [DEBUG] Starting enhanced process loop...")
    
    while self.running:
        try:
            raw = await self._message_queue.get()
            print(f"🔍 [DEBUG] Raw message received: {len(raw)} bytes")
            print(f"🔍 [DEBUG] Raw message preview: {raw[:100]}...")
            
            parsed = await asyncio.to_thread(parse_upstox_feed, raw)
            print(f"🔍 [DEBUG] Parsed result: {type(parsed)}")
            
            feeds = getattr(parsed, "feeds", None)
            if not feeds:
                print("🔍 [DEBUG] No feeds in parsed message")
                continue
            
            print(f"🔍 [DEBUG] Found {len(feeds)} feeds")
            
            for instrument_key, feed in feeds.items():
                print(f"🔍 [DEBUG] Processing feed: {instrument_key}")
                
                if not hasattr(feed, "ltpc"):
                    print("🔍 [DEBUG] No ltpc in feed")
                    continue
                
                ltp = getattr(feed.ltpc, "ltp", None)
                if not ltp:
                    print("🔍 [DEBUG] No ltp in feed.ltpc")
                    continue
                
                print(f"🔍 [DEBUG] LTP: {ltp}")
                
                symbol = resolve_symbol_from_instrument(instrument_key)
                if not symbol:
                    print("🔍 [DEBUG] Could not resolve symbol")
                    continue
                
                print(f"🔍 [DEBUG] Resolved symbol: {symbol}")
                
                tick_data = {
                    "instrument_key": instrument_key,
                    "ltp": ltp,
                    "timestamp": int(datetime.now().timestamp() * 1000),
                }
                
                print(f"🔍 [DEBUG] Tick data: {tick_data}")
                
                await self._route_tick_to_builders(symbol, instrument_key, tick_data)
                print(f"🔍 [DEBUG] Tick routed to builders")
                
        except Exception as e:
            print(f"🔍 [DEBUG] Process loop error: {e}")
            import traceback
            traceback.print_exc()

async def trace_data_flow():
    """Trace data flow through the pipeline"""
    
    print("\n" + "="*80)
    print("🔍 TRACING WEBSOCKET DATA FLOW")
    print("="*80)
    
    # Patch the process loop for debugging
    from app.services.websocket_market_feed import WebSocketMarketFeed
    from app.services.upstox_protobuf_parser import parse_upstox_feed
    from app.services.websocket_market_feed import resolve_symbol_from_instrument
    
    global original_process_loop
    original_process_loop = WebSocketMarketFeed._process_loop
    WebSocketMarketFeed._process_loop = debug_process_loop
    
    try:
        # Test with valid token if available
        from app.services.token_manager import token_manager
        
        auth_state = token_manager.get_auth_state()
        if auth_state['state'] != 'authenticated':
            print("❌ No valid authentication - cannot trace data flow")
            print("   Please run: python test_auth_flow.py")
            return False
        
        print("✅ Authentication found - starting data flow trace")
        
        # Start WebSocket feed
        from app.services.websocket_market_feed import ws_feed_manager
        
        print("🔄 Starting WebSocket feed...")
        await ws_feed_manager.start_feed()
        
        # Wait for some data
        print("⏳ Waiting for market data (30 seconds)...")
        await asyncio.sleep(30)
        
        print("✅ Data flow trace completed")
        return True
        
    except Exception as e:
        print(f"❌ Error in data flow trace: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Restore original process loop
        if original_process_loop:
            WebSocketMarketFeed._process_loop = original_process_loop

if __name__ == "__main__":
    result = asyncio.run(trace_data_flow())
    if result:
        print("\n🎉 Data flow trace successful!")
    else:
        print("\n💥 Data flow trace failed!")
