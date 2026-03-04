#!/usr/bin/env python3
"""
Simple Runtime Audit of Upstox Protobuf Parser
Identifies exactly which protobuf parser is being used at runtime
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

def audit_protobuf_parser():
    """Simple audit of which protobuf parser is being used"""
    
    print("🔍 RUNTIME PROTOBUF PARSER AUDIT")
    print("=" * 60)
    
    try:
        # Check imports in websocket_market_feed.py
        try:
            with open('app/services/websocket_market_feed.py', 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Failed to read websocket_market_feed.py: {e}")
            return
        
        print("✅ IMPORT ANALYSIS:")
        
        # Check which parser is being imported
        if 'from app.services.upstox_protobuf_parser_v3 import' in content:
            print("   ✅ Using: upstox_protobuf_parser_v3.py (CORRECT)")
            print("   📝 Supports: ltpc mode + full mode")
            parser_file = 'upstox_protobuf_parser_v3.py'
        elif 'from app.services.upstox_protobuf_parser import' in content:
            print("   ❌ Using: upstox_protobuf_parser.py (OUTDATED)")
            print("   📝 Only supports: full mode structure")
            parser_file = 'upstox_protobuf_parser.py'
        else:
            print("   ❓ UNKNOWN: Could not identify parser import")
            parser_file = 'UNKNOWN'
        
        print(f"   📂 Active Parser: {parser_file}")
        print("")
        
        # Check the actual parser file content if we can identify it
        if parser_file != 'UNKNOWN':
            try:
                with open(f'app/services/{parser_file}', 'r') as f:
                    parser_content = f.read()
                    
                print("✅ PARSER CAPABILITIES:")
                
                # Check for ltpc mode support
                if 'feed.HasField("ltpc")' in parser_content:
                    print("   ✅ LTPC Mode: SUPPORTED")
                else:
                    print("   ❌ LTPC Mode: NOT SUPPORTED")
                
                # Check for full mode support
                if 'feed.HasField("ff")' in parser_content:
                    print("   ✅ Full Mode: SUPPORTED")
                else:
                    print("   ❌ Full Mode: NOT SUPPORTED")
                
                # Check for both modes
                ltpc_support = 'feed.HasField("ltpc")' in parser_content
                full_support = 'feed.HasField("ff")' in parser_content
                
                if ltpc_support and full_support:
                    print("   ✅ Dual Mode: SUPPORTED")
                else:
                    print("   ❌ Dual Mode: NOT SUPPORTED")
                
                # Check for debug logging
                if 'RAW PACKET SIZE = {len(message)}' in parser_content:
                    print("   ✅ Debug Logging: COMPREHENSIVE")
                else:
                    print("   ❌ Debug Logging: MISSING")
                
                print("")
                print("📋 SUBSCRIPTION COMPATIBILITY:")
                print("   - ltpc mode: Requires direct feed.ltpc.ltp access")
                print("   - full mode: Requires feed.ff.indexFF/marketFF.ltpc.ltp access")
                
            except Exception as e:
                print(f"❌ Parser analysis failed: {e}")
        
    except Exception as e:
        print(f"❌ Audit failed: {e}")

if __name__ == "__main__":
    print("🎯 UPSTOX PROTOBUF PARSER RUNTIME AUDIT")
    print("=" * 60)
    
    # Audit the current setup
    audit_protobuf_parser()
