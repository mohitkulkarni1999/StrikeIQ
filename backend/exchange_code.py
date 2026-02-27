#!/usr/bin/env python3
"""
Exchange authorization code for access token
Usage: python exchange_code.py YOUR_AUTH_CODE_HERE
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

async def exchange_code(code):
    """Exchange authorization code for access token"""
    
    try:
        from app.services.upstox_auth_service import get_upstox_auth_service
        from app.services.token_manager import token_manager
        
        print(f"🔄 Exchanging code: {code[:20]}...")
        
        auth_service = get_upstox_auth_service()
        token_data = await auth_service.exchange_code_for_token(code)
        
        if token_data and "access_token" in token_data:
            access_token = token_data["access_token"]
            refresh_token = token_data.get("refresh_token", "")
            expires_in = token_data.get("expires_in", 3600)
            
            print(f"✅ Token exchange successful!")
            print(f"   Access Token: {access_token[:20]}...")
            print(f"   Refresh Token: {refresh_token[:20]}...")
            print(f"   Expires In: {expires_in} seconds")
            
            # Store in token manager
            await token_manager.login(access_token, expires_in)
            print("✅ Token stored in manager")
            
            # Test the pipeline now
            print("\n🔍 Testing pipeline with new token...")
            from debug_pipeline import debug_pipeline
            result = await debug_pipeline()
            
            return result
            
        else:
            print("❌ Token exchange failed - no token in response")
            print(f"Response: {token_data}")
            return False
            
    except Exception as e:
        print(f"❌ Error exchanging code: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python exchange_code.py YOUR_AUTH_CODE_HERE")
        sys.exit(1)
    
    code = sys.argv[1]
    result = asyncio.run(exchange_code(code))
    
    if result:
        print("\n🎉 Authentication and pipeline successful!")
    else:
        print("\n💥 Authentication or pipeline failed!")
