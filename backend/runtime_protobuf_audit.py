#!/usr/bin/env python3
"""
Runtime Audit of Upstox Protobuf Parser
Identifies exactly which parser file is being used at runtime
"""

import asyncio
import logging
import sys
import os
import inspect

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

def audit_protobuf_parser_usage():
    """Audit which protobuf parser is actually being used at runtime"""
    
    print("🔍 RUNTIME PROTOBUF PARSER AUDIT")
    print("=" * 60)
    
    try:
        # Import the websocket feed to check its imports
        from app.services.websocket_market_feed import WebSocketMarketFeed
        
        print("✅ IMPORT AUDIT:")
        print("   Checking websocket_market_feed.py imports...")
        
        # Get the source code of the websocket feed
        feed_source = inspect.getsource(WebSocketMarketFeed)
        
        # Check which parser is being imported
        if 'upstox_protobuf_parser_v3' in feed_source:
            print("   ✅ Using: upstox_protobuf_parser_v3.py (CORRECT)")
            print("   📝 Supports: ltpc mode + full mode")
            parser_file = 'upstox_protobuf_parser_v3.py'
        elif 'upstox_protobuf_parser' in feed_source:
            print("   ❌ Using: upstox_protobuf_parser.py (OUTDATED)")
            print("   📝 Only supports: full mode structure")
            parser_file = 'upstox_protobuf_parser.py'
        else:
            print("   ❓ UNKNOWN: Could not identify parser import")
            parser_file = 'UNKNOWN'
        
        print(f"   📂 Active Parser: {parser_file}")
        print("")
        
        # Check the actual parser file content
        if parser_file != 'UNKNOWN':
            try:
                with open(f'app/services/{parser_file}', 'r') as f:
                    parser_content = f.read()
                    
                print("✅ PARSER FILE ANALYSIS:")
                print("   Checking for dual mode support...")
                
                # Check for ltpc mode support
                if 'feed.HasField("ltpc")' in parser_content:
                    print("   ✅ LTPC Mode: SUPPORTED")
                else:
                    print("   ❌ LTPC Mode: NOT SUPPORTED")
                
                # Check for full mode support
                if 'feed.HasField("ff")' in parser_content and 'ff.HasField("indexFF")' in parser_content:
                    print("   ✅ Full Mode: SUPPORTED")
                else:
                    print("   ❌ Full Mode: NOT SUPPORTED")
                
                # Check for both modes
                ltpc_count = parser_content.count('feed.HasField("ltpc")')
                full_count = parser_content.count('feed.HasField("ff")')
                
                if ltpc_count > 0 and full_count > 0:
                    print("   ✅ Dual Mode: SUPPORTED")
                else:
                    print("   ❌ Dual Mode: NOT SUPPORTED")
                
                # Check for debug logging
                if 'RAW PACKET SIZE = {len(message)}' in parser_content:
                    print("   ✅ Debug Logging: COMPREHENSIVE")
                else:
                    print("   ❌ Debug Logging: MISSING")
                
                print("")
                print("📋 EXPECTED PARSER CAPABILITIES:")
                print("   - LTPC mode support: feed.HasField('ltpc') + feed.ltpc.ltp")
                print("   - Full mode support: feed.HasField('ff') + feed.ff.indexFF/marketFF.ltpc.ltp")
                print("   - Debug logging: Packet size, feed count, LTP values")
                print("   - Structure detection: Proper field checking")
                print("")
                
                # Check subscription mode compatibility
                print("📋 SUBSCRIPTION COMPATIBILITY:")
                print("   - ltpc mode: Requires direct feed.ltpc.ltp access")
                print("   - full mode: Requires feed.ff.indexFF/marketFF.ltpc.ltp access")
                
            except Exception as e:
                print(f"❌ Parser analysis failed: {e}")
        
    except Exception as e:
        print(f"❌ Audit failed: {e}")
        import traceback
        traceback.print_exc()

async def test_runtime_parser():
    """Test runtime parser behavior"""
    
    print("\n🚀 TESTING RUNTIME PARSER BEHAVIOR")
    print("=" * 60)
    
    try:
        from app.services.websocket_market_feed import WebSocketMarketFeed
        
        print("📡 Creating WebSocket feed to test parser...")
        feed = WebSocketMarketFeed()
        
        print("📋 EXPECTED RUNTIME BEHAVIOR:")
        print("   - Should use upstox_protobuf_parser_v3.py")
        print("   - Should support both ltpc and full mode")
        print("   - Should show dual mode detection logs")
        print("   - Should extract LTP values correctly")
        print("")
        
        print("⚠️  NOTE: This will show which parser is ACTUALLY being used")
        print("⚠️  If the wrong parser is active, market data will fail")
        print("")
        
        # Don't actually start the feed to avoid connection issues
        print("🔍 INSPECTION RESULTS:")
        print(f"   Active Parser: {inspect.getfile(WebSocketMarketFeed._connect.__code__.co_filename)}")
        
        # Get the actual function being called
        process_func = WebSocketMarketFeed._process_loop
        print(f"   Process Function: {process_func}")
        
        # Check the source of the process function
        process_source = inspect.getsource(process_func)
        print(f"   Process Function Source: Uses {process_func.__code__.co_name}")
        
        # Check imports in the process function
        if 'upstox_protobuf_parser_v3' in process_source:
            print("   ✅ Process Function: Uses CORRECT parser")
        elif 'upstox_protobuf_parser' in process_source:
            print("   ❌ Process Function: Uses OUTDATED parser")
        else:
            print("   ❓ Process Function: UNKNOWN parser")
        
    except Exception as e:
        print(f"❌ Runtime test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🎯 UPSTOX PROTOBUF PARSER RUNTIME AUDIT")
    print("=" * 60)
    
    # First audit the current setup
    audit_protobuf_parser_usage()
    
    print("\n" + "=" * 60)
    
    # Then test runtime behavior
    asyncio.run(test_runtime_parser())
