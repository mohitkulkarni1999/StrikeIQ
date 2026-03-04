#!/usr/bin/env python3
"""
Test the instrument key fix for Upstox WebSocket
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

async def test_instrument_key_fix():
    """Test the corrected instrument keys"""
    
    try:
        from app.services.websocket_market_feed import WebSocketMarketFeed
        
        print("🔧 Testing Instrument Key Fix...")
        print("=" * 60)
        print("✅ FIXED INSTRUMENT KEYS:")
        print("   NSE_INDEX|NIFTY 50 (was: NSE_INDEX|Nifty 50)")
        print("   NSE_INDEX|NIFTY BANK (was: NSE_INDEX|Nifty Bank)")
        print("=" * 60)
        
        # Create feed instance
        feed = WebSocketMarketFeed()
        
        # Start the feed
        await feed.start()
        
        print("✅ WebSocket feed started with corrected keys")
        print("📊 Waiting for market data...")
        print("🔍 EXPECTED LOGS:")
        print("   FINAL INSTRUMENT KEYS:")
        print("   NSE_INDEX|NIFTY 50")
        print("   NSE_INDEX|NIFTY BANK")
        print("   RAW PACKET SIZE = 600+ (not 154)")
        print("   PROTOBUF FEEDS RECEIVED = 2")
        print("   TICKS EXTRACTED = 2")
        print("   📡 BROADCAST → spot_tick")
        print("=" * 60)
        
        # Let it run for 30 seconds to capture market data
        await asyncio.sleep(30)
        
        print("\n🛑 Test completed. Check logs above for market data.")
        
        # Cleanup
        await feed.disconnect()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_instrument_key_fix())
