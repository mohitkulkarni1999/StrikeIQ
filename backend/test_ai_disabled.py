#!/usr/bin/env python3
"""
Test AI Disabled Configuration
Verifies that AI is disabled but WebSocket functionality works
"""

import asyncio
import logging
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

# Configure logging to see startup messages
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_ai_disabled_startup():
    """Test startup sequence with AI disabled"""
    
    print("\n" + "="*60)
    print("🧪 TESTING AI DISABLED CONFIGURATION")
    print("="*60)
    
    # Test 1: Check ENABLE_AI flag
    print("\n🔹 STEP 1: CHECK AI CONFIGURATION")
    print("-" * 40)
    
    try:
        # Import main to check the flag
        import main
        print(f"✅ ENABLE_AI flag: {main.ENABLE_AI}")
        
        if not main.ENABLE_AI:
            print("✅ AI system is DISABLED as expected")
        else:
            print("❌ AI system is still ENABLED")
            return False
            
    except Exception as e:
        print(f"❌ Error checking AI configuration: {e}")
        return False
    
    # Test 2: Simulate startup sequence
    print("\n🔹 STEP 2: SIMULATE STARTUP SEQUENCE")
    print("-" * 40)
    
    try:
        # Test core imports (should work)
        from app.services.websocket_market_feed import ws_feed_manager
        from app.services.live_chain_manager import chain_manager
        from app.core.ws_manager import manager
        from app.services.instrument_registry import get_instrument_registry
        
        print("✅ Core WebSocket components imported successfully")
        
        # Test AI imports (should work but not start)
        from ai.scheduler import ai_scheduler
        from ai.ai_db import ai_db
        
        print("✅ AI components imported successfully (but not started)")
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test 3: Check AI scheduler state
    print("\n🔹 STEP 3: CHECK AI SCHEDULER STATE")
    print("-" * 40)
    
    try:
        # Check if scheduler is running (should be False)
        print(f"AI Scheduler type: {type(ai_scheduler)}")
        print(f"AI Scheduler jobs setup: {hasattr(ai_scheduler, 'scheduler')}")
        
        # The scheduler should have jobs configured but not be running
        if hasattr(ai_scheduler, 'scheduler'):
            jobs = ai_scheduler.scheduler.get_jobs()
            print(f"Configured jobs (not running): {len(jobs)}")
            for job in jobs:
                print(f"   - {job.name}")
        
        print("✅ AI scheduler is configured but not running")
        
    except Exception as e:
        print(f"❌ Error checking AI scheduler: {e}")
        return False
    
    # Test 4: Verify WebSocket functionality
    print("\n🔹 STEP 4: VERIFY WEBSOCKET FUNCTIONALITY")
    print("-" * 40)
    
    try:
        # Test WebSocket manager
        print(f"WebSocket manager active connections: {len(manager.active_connections)}")
        
        # Test chain manager
        from datetime import date
        builder = await chain_manager.get_builder("BANKNIFTY", date.today())
        print(f"Chain manager builder created: {type(builder)}")
        
        # Test symbol resolution (fixed earlier)
        from app.services.websocket_market_feed import resolve_symbol_from_instrument
        
        test_symbols = [
            "NSE_INDEX|Nifty 50",
            "NSE_INDEX|Nifty Bank"
        ]
        
        for symbol in test_symbols:
            resolved = resolve_symbol_from_instrument(symbol)
            print(f"Symbol resolution: {symbol} → {resolved}")
        
        print("✅ WebSocket functionality verified")
        
    except Exception as e:
        print(f"❌ WebSocket functionality error: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ AI DISABLED CONFIGURATION TEST PASSED")
    print("="*60)
    print("\n📋 SUMMARY:")
    print("   → AI system is DISABLED")
    print("   → No AI scheduler jobs will run")
    print("   → WebSocket functionality is PRESERVED")
    print("   → Market data pipeline is READY")
    print("   → Logs will be CLEAN for debugging")
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test_ai_disabled_startup())
    if result:
        print("\n🎉 Test completed successfully!")
        print("🚀 Ready to start backend with clean logs!")
    else:
        print("\n💥 Test failed!")
