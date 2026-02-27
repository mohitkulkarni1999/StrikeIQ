#!/usr/bin/env python3
"""
WebSocket Market Data Pipeline Debugger
Traces exact failure points in the data pipeline
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def debug_pipeline():
    """Debug the complete WebSocket market data pipeline"""
    
    print("\n" + "="*80)
    print("🔍 WEBSOCKET MARKET DATA PIPELINE DEBUG")
    print("="*80)
    
    # Step 1: Check Authentication State
    print("\n🔹 STEP 1: AUTHENTICATION STATE")
    print("-" * 40)
    
    try:
        from app.services.token_manager import token_manager
        
        auth_state = token_manager.get_auth_state()
        print(f"Auth State: {auth_state['state']}")
        print(f"Failure Reason: {auth_state.get('failure_reason', 'None')}")
        
        if auth_state['state'] == 'AUTH_REQUIRED':
            print("❌ FAILURE POINT 1: NO VALID AUTHENTICATION")
            print("   → Token manager has no valid credentials")
            print("   → Need to authenticate via OAuth flow first")
            return False
            
    except Exception as e:
        print(f"❌ ERROR checking auth state: {e}")
        return False
    
    # Step 2: Test Token Retrieval
    print("\n🔹 STEP 2: TOKEN RETRIEVAL")
    print("-" * 40)
    
    try:
        token = await token_manager.get_valid_token()
        print(f"✅ Token retrieved successfully: {token[:20]}...")
    except Exception as e:
        print(f"❌ FAILURE POINT 2: TOKEN RETRIEVAL FAILED")
        print(f"   Error: {e}")
        return False
    
    # Step 3: Test WebSocket Authorization
    print("\n🔹 STEP 3: WEBSOCKET AUTHORIZATION")
    print("-" * 40)
    
    try:
        from app.services.websocket_market_feed import WebSocketMarketFeed
        
        ws_feed = WebSocketMarketFeed()
        ws_url = await ws_feed._authorize_feed(token)
        
        if ws_url:
            print(f"✅ WebSocket URL authorized: {ws_url[:50]}...")
        else:
            print("❌ FAILURE POINT 3: WEBSOCKET AUTHORIZATION FAILED")
            print("   → Could not get WebSocket URL from Upstox")
            return False
            
    except Exception as e:
        print(f"❌ FAILURE POINT 3: WEBSOCKET AUTHORIZATION ERROR")
        print(f"   Error: {e}")
        return False
    
    # Step 4: Test WebSocket Connection
    print("\n🔹 STEP 4: WEBSOCKET CONNECTION")
    print("-" * 40)
    
    try:
        import websockets
        
        print("Attempting to connect to WebSocket...")
        async with websockets.connect(
            ws_url,
            subprotocols=["json"],
            ping_interval=None,
            ping_timeout=None,
            close_timeout=5,
            max_queue=None
        ) as websocket:
            print("✅ WebSocket connection established")
            
            # Test subscription
            payload = {
                "guid": "debug-feed",
                "method": "sub",
                "data": {
                    "mode": "full",
                    "instrumentKeys": ["NSE_INDEX|Nifty 50"]
                }
            }
            
            await websocket.send(str(payload))
            print("✅ Subscription sent successfully")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"✅ Received response: {response[:100]}...")
            except asyncio.TimeoutError:
                print("⚠️  No response received within 5 seconds")
            
    except Exception as e:
        print(f"❌ FAILURE POINT 4: WEBSOCKET CONNECTION FAILED")
        print(f"   Error: {e}")
        return False
    
    # Step 5: Test Protobuf Parser
    print("\n🔹 STEP 5: PROTOBUF PARSER")
    print("-" * 40)
    
    try:
        from app.services.upstox_protobuf_parser import parse_upstox_feed
        
        # Test with dummy data
        test_data = b'\x0a\x00'  # Empty protobuf message
        result = parse_upstox_feed(test_data)
        print(f"✅ Protobuf parser works: {type(result)}")
        
    except Exception as e:
        print(f"❌ FAILURE POINT 5: PROTOBUF PARSER ERROR")
        print(f"   Error: {e}")
        return False
    
    # Step 6: Test Chain Manager
    print("\n🔹 STEP 6: CHAIN MANAGER")
    print("-" * 40)
    
    try:
        from app.services.live_chain_manager import chain_manager
        from datetime import date
        
        # Test getting a builder
        builder = await chain_manager.get_builder("BANKNIFTY", date.today())
        print(f"✅ Chain manager works: {type(builder)}")
        
    except Exception as e:
        print(f"❌ FAILURE POINT 6: CHAIN MANAGER ERROR")
        print(f"   Error: {e}")
        return False
    
    # Step 7: Test WebSocket Manager
    print("\n🔹 STEP 7: WEBSOCKET MANAGER")
    print("-" * 40)
    
    try:
        from app.core.ws_manager import manager
        
        print(f"✅ WebSocket manager works: {type(manager)}")
        print(f"   Active connections: {len(manager.active_connections)}")
        
    except Exception as e:
        print(f"❌ FAILURE POINT 7: WEBSOCKET MANAGER ERROR")
        print(f"   Error: {e}")
        return False
    
    print("\n" + "="*80)
    print("✅ ALL PIPELINE COMPONENTS WORKING")
    print("="*80)
    return True

if __name__ == "__main__":
    result = asyncio.run(debug_pipeline())
    if result:
        print("\n🎉 Pipeline is healthy!")
        sys.exit(0)
    else:
        print("\n💥 Pipeline has failures!")
        sys.exit(1)
