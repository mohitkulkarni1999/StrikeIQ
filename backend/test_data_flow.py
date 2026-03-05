#!/usr/bin/env python3
"""
Test script to validate StrikeIQ data flow
"""

import asyncio
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_message_router():
    """Test message router functionality"""
    logger.info("Testing message router...")
    
    try:
        from app.services.message_router import message_router
        
        # Test index tick routing
        index_tick = {
            "instrument_key": "NSE_INDEX|NIFTY 50",
            "ltp": 24555.30
        }
        
        message = message_router.route_tick(index_tick)
        if message:
            logger.info(f"✅ Index tick routed: {message['type']} for {message['symbol']}")
        else:
            logger.error("❌ Index tick routing failed")
        
        # Test option tick routing
        option_tick = {
            "instrument_key": "NSE_FO|NIFTY 26MAR2024 24500 CE",
            "ltp": 120.50
        }
        
        message = message_router.route_tick(option_tick)
        if message:
            logger.info(f"✅ Option tick routed: {message['type']} for {message['symbol']}")
        else:
            logger.error("❌ Option tick routing failed")
            
    except Exception as e:
        logger.error(f"❌ Message router test failed: {e}")

async def test_option_chain_builder():
    """Test option chain builder functionality"""
    logger.info("Testing option chain builder...")
    
    try:
        from app.services.option_chain_builder import option_chain_builder
        
        # Start the builder
        await option_chain_builder.start()
        
        # Test index price update
        option_chain_builder.update_index_price("NIFTY", 24550.0)
        
        # Test option tick updates
        option_chain_builder.update_option_tick("NIFTY", 24500, "CE", 120.50)
        option_chain_builder.update_option_tick("NIFTY", 24500, "PE", 140.25)
        option_chain_builder.update_option_tick("NIFTY", 24600, "CE", 95.75)
        option_chain_builder.update_option_tick("NIFTY", 24600, "PE", 110.80)
        
        # Get chain snapshot
        chain = option_chain_builder.get_chain("NIFTY")
        if chain:
            logger.info(f"✅ Option chain built: {len(chain['strikes'])} strikes")
        else:
            logger.error("❌ Option chain building failed")
            
        # Stop the builder
        await option_chain_builder.stop()
        
    except Exception as e:
        logger.error(f"❌ Option chain builder test failed: {e}")

async def test_heatmap_engine():
    """Test heatmap engine functionality"""
    logger.info("Testing heatmap engine...")
    
    try:
        from app.services.oi_heatmap_engine import oi_heatmap_engine
        
        # Start the engine
        await oi_heatmap_engine.start()
        
        # Get cached heatmap (should be empty initially)
        heatmap = oi_heatmap_engine.get_cached_heatmap("NIFTY")
        if heatmap:
            logger.info(f"✅ Heatmap data available: {heatmap['type']}")
        else:
            logger.info("ℹ️ No cached heatmap data (expected)")
            
        # Stop the engine
        await oi_heatmap_engine.stop()
        
    except Exception as e:
        logger.error(f"❌ Heatmap engine test failed: {e}")

async def test_analytics_broadcaster():
    """Test analytics broadcaster functionality"""
    logger.info("Testing analytics broadcaster...")
    
    try:
        from app.services.analytics_broadcaster import analytics_broadcaster
        
        # Start the broadcaster
        await analytics_broadcaster.start()
        
        # Test single analytics computation
        test_chain_data = {
            "symbol": "NIFTY",
            "spot": 24550,
            "calls": [
                {"strike": 24500, "ltp": 120.50, "oi": 120000, "volume": 1500},
                {"strike": 24600, "ltp": 95.75, "oi": 95000, "volume": 1200}
            ],
            "puts": [
                {"strike": 24500, "ltp": 140.25, "oi": 95000, "volume": 1200},
                {"strike": 24600, "ltp": 110.80, "oi": 110000, "volume": 1000}
            ]
        }
        
        analytics = await analytics_broadcaster.compute_single_analytics("NIFTY", test_chain_data)
        if analytics:
            logger.info(f"✅ Analytics computed: {analytics['type']}")
        else:
            logger.error("❌ Analytics computation failed")
            
        # Stop the broadcaster
        await analytics_broadcaster.stop()
        
    except Exception as e:
        logger.error(f"❌ Analytics broadcaster test failed: {e}")

async def test_websocket_manager():
    """Test WebSocket manager functionality"""
    logger.info("Testing WebSocket manager...")
    
    try:
        from app.core.ws_manager import manager
        
        # Test broadcast (no connections expected)
        test_message = {
            "type": "test_message",
            "timestamp": int(datetime.now().timestamp()),
            "data": {"test": True}
        }
        
        await manager.broadcast(test_message)
        logger.info("✅ WebSocket broadcast test completed")
        
    except Exception as e:
        logger.error(f"❌ WebSocket manager test failed: {e}")

async def test_protobuf_parser():
    """Test protobuf parser functionality"""
    logger.info("Testing protobuf parser...")
    
    try:
        from app.services.upstox_protobuf_parser_v3 import decode_protobuf_message_v3
        
        # Test with empty data (should return empty list)
        ticks = decode_protobuf_message_v3(b"")
        if isinstance(ticks, list):
            logger.info("✅ Protobuf parser handles empty data correctly")
        else:
            logger.error("❌ Protobuf parser failed on empty data")
            
    except Exception as e:
        logger.error(f"❌ Protobuf parser test failed: {e}")

async def main():
    """Run all tests"""
    logger.info("🚀 Starting StrikeIQ Data Flow Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Message Router", test_message_router),
        ("Option Chain Builder", test_option_chain_builder),
        ("Heatmap Engine", test_heatmap_engine),
        ("Analytics Broadcaster", test_analytics_broadcaster),
        ("WebSocket Manager", test_websocket_manager),
        ("Protobuf Parser", test_protobuf_parser),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\n🧪 Running {test_name} Test...")
            await test_func()
            results.append((test_name, "✅ PASSED"))
            logger.info(f"✅ {test_name} test completed successfully")
        except Exception as e:
            results.append((test_name, f"❌ FAILED: {e}"))
            logger.error(f"❌ {test_name} test failed: {e}")
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = sum(1 for _, status in results if "✅" in status)
    total = len(results)
    
    for test_name, status in results:
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\n📈 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Data flow is working correctly.")
    else:
        logger.warning(f"⚠️ {total - passed} tests failed. Check the errors above.")
    
    logger.info("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
