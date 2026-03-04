#!/usr/bin/env python3
"""
Debug script to test Upstox WebSocket connection and protobuf parsing
Run this to see the detailed debug output
"""

import asyncio
import logging
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

async def test_websocket_feed():
    """Test the WebSocket market feed with debug logging"""
    
    try:
        # Import after path setup
        from app.services.websocket_market_feed import WebSocketMarketFeed
        
        print("🚀 Starting WebSocket Feed Debug Test...")
        print("=" * 60)
        
        # Create feed instance
        feed = WebSocketMarketFeed()
        
        # Start the feed (this will connect and subscribe)
        await feed.start()
        
        print("✅ WebSocket feed started")
        print("📊 Waiting for market data...")
        print("🔍 Watch for these debug messages:")
        print("   - RAW PACKET SIZE = <number>")
        print("   - SUBSCRIPTION PAYLOAD:")
        print("   - PROTOBUF V2 FEEDS COUNT = <number>")
        print("   - V2 FEED KEY = <instrument>")
        print("   - INDEX/OPTION/LTPC FEED DETECTED")
        print("   - V2 TICKS EXTRACTED = <number>")
        print("=" * 60)
        
        # Let it run for 30 seconds to capture debug output
        await asyncio.sleep(30)
        
        print("\n🛑 Test completed. Check logs above for debug info.")
        
        # Cleanup
        await feed.disconnect()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_websocket_feed())
