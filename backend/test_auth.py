#!/usr/bin/env python3
"""
Test Authentication Flow
"""

import asyncio
import sys
import os
sys.path.append('.')

async def test_dashboard():
    """Test dashboard API directly"""
    import httpx
    
    try:
        print("Testing dashboard API...")
        response = httpx.get("http://localhost:8000/api/dashboard/NIFTY", timeout=5)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Session Type: {data.get('session_type')}")
            print(f"Market Status: {data.get('market_status')}")
            
            if data.get('session_type') == 'AUTH_REQUIRED':
                print("✅ AUTHENTICATION REDIRECT WORKING!")
            else:
                print("❌ No authentication redirect")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_dashboard())
