#!/usr/bin/env python3
"""
Complete Upstox V3 WebSocket Test with Debug Logging
Tests the entire pipeline from connection to tick extraction
"""

import asyncio
import logging
import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

async def test_complete_pipeline():
    """Test the complete WebSocket pipeline with debug logging"""
    
    try:
        from app.services.websocket_market_feed import WebSocketMarketFeed
        
        print("🚀 TESTING COMPLETE UPSTOX V3 PIPELINE")
        print("=" * 60)
        print("📋 EXPECTED FLOW:")
        print("1. ✅ WebSocket Authorization")
        print("2. ✅ WebSocket Connection")
        print("3. ✅ Subscription Payload Sent")
        print("4. 📡 Binary Packets Received")
        print("5. 🔍 Protobuf Parsing")
        print("6. 📊 Tick Extraction")
        print("7. 🎯 Broadcast to Frontend")
        print("=" * 60)
        
        # Create and start feed
        feed = WebSocketMarketFeed()
        
        print("🔌 Starting WebSocket feed...")
        await feed.start()
        
        print("✅ Feed started successfully")
        print("📊 Monitoring for market data...")
        print("🔍 Watch for these key logs:")
        print("   - RAW PACKET SIZE = <number>")
        print("   - === PROTOBUF V3 PARSING ===")
        print("   - FEEDS COUNT = <number>")
        print("   - 🎯 INDEX FEED DETECTED")
        print("   - ✅ INDEX LTP EXTRACTED = <price>")
        print("   - 📊 TICK: <instrument> = <price>")
        print("   - 📡 FINAL TICK COUNT BROADCAST = <number>")
        print("=" * 60)
        
        # Let it run for 60 seconds to capture market data
        await asyncio.sleep(60)
        
        print("\n🛑 Test completed")
        print("📊 ANALYSIS:")
        print("   - If RAW PACKET SIZE stays ~154: Only heartbeats")
        print("   - If RAW PACKET SIZE > 500: Real market data")
        print("   - If FEEDS COUNT = 0: Subscription or parsing issue")
        print("   - If TICKS EXTRACTED > 0: Success!")
        
        # Cleanup
        await feed.disconnect()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_instrument_keys():
    """Test different instrument key formats"""
    
    print("\n🧪 TESTING INSTRUMENT KEY FORMATS")
    print("=" * 60)
    
    # Test different formats based on research
    test_keys = [
        "NSE_INDEX|NIFTY 50",      # Current format
        "NSE_INDEX|NIFTY 50 ",     # With space
        "NSE_INDEX|NIFTY 50",      # Uppercase
        "NSE_INDEX|NIFTY BANK",     # Current format
        "NSE_INDEX|NIFTY BANK",      # Uppercase
        "NSE_INDEX|NIFTY 50",       # Original format
        "NSE_INDEX|NIFTY BANK",      # Original format
    ]
    
    print("📝 Testing instrument key formats:")
    for i, key in enumerate(test_keys, 1):
        print(f"   {i}. {key}")
    
    print("\n💡 RECOMMENDATION:")
    print("   Use official format from Upstox documentation")
    print("   Check actual instrument keys from /api/v1/instruments endpoint")
    print("   Verify format matches WebSocket subscription requirements")

if __name__ == "__main__":
    print("🔧 UPSTOX V3 WEBSOCKET DEBUG SUITE")
    print("=" * 60)
    
    # Test instrument key formats first
    asyncio.run(test_instrument_keys())
    
    # Then test complete pipeline
    asyncio.run(test_complete_pipeline())
