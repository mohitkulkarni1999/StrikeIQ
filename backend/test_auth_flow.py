#!/usr/bin/env python3
"""
Test OAuth Authentication Flow and Pipeline
"""

import asyncio
import logging
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_complete_flow():
    """Test complete authentication and pipeline flow"""
    
    print("\n" + "="*80)
    print("🔐 TESTING COMPLETE AUTH FLOW")
    print("="*80)
    
    # Step 1: Check if we can get auth URL
    print("\n🔹 STEP 1: GENERATE AUTH URL")
    print("-" * 40)
    
    try:
        from app.services.upstox_auth_service import get_upstox_auth_service
        
        auth_service = get_upstox_auth_service()
        auth_url = auth_service.get_authorization_url()
        
        print(f"✅ Auth URL generated:")
        print(f"   {auth_url}")
        print("\n📝 INSTRUCTIONS:")
        print("   1. Open this URL in browser")
        print("   2. Login to Upstox")
        print("   3. After redirect, copy the 'code' parameter")
        print("   4. Run: python exchange_code.py YOUR_CODE_HERE")
        
    except Exception as e:
        print(f"❌ ERROR generating auth URL: {e}")
        return False
    
    # Step 2: Check current credentials
    print("\n🔹 STEP 2: CHECK CURRENT CREDENTIALS")
    print("-" * 40)
    
    try:
        creds = auth_service._load_credentials()
        if creds:
            print(f"✅ Credentials found:")
            print(f"   Access Token: {creds.access_token[:20]}...")
            print(f"   Expires At: {creds.expires_at}")
            print(f"   Is Expired: {creds.is_expired()}")
        else:
            print("❌ No stored credentials found")
            
    except Exception as e:
        print(f"❌ ERROR checking credentials: {e}")
    
    # Step 3: Test token refresh if possible
    print("\n🔹 STEP 3: TEST TOKEN REFRESH")
    print("-" * 40)
    
    try:
        if creds and not creds.is_expired():
            print("✅ Valid credentials exist, testing refresh...")
            
            token_data = await auth_service.refresh_access_token()
            if token_data:
                print(f"✅ Token refresh successful:")
                print(f"   New Token: {token_data.get('access_token', '')[:20]}...")
            else:
                print("❌ Token refresh returned empty data")
        else:
            print("⚠️  No valid credentials to refresh")
            
    except Exception as e:
        print(f"❌ Token refresh failed: {e}")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_complete_flow())
