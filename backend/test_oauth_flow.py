#!/usr/bin/env python3
"""
Automated OAuth Flow Testing Script
For development testing without manual URL copying
"""

import webbrowser
import requests
import json
import time

def test_oauth_flow():
    """Test complete OAuth flow automatically"""
    print("🚀 Starting OAuth Flow Test...")
    
    # 1. Get auth URL with state
    print("📡 Step 1: Getting auth URL...")
    response = requests.get("http://localhost:8000/api/v1/auth/upstox", 
                           headers={"accept": "application/json"})
    
    if response.status_code != 200:
        print(f"❌ Failed to get auth URL: {response.status_code}")
        return False
    
    auth_data = response.json()
    auth_url = auth_data["data"]["authorization_url"]
    state = auth_data["data"]["state"]
    
    print(f"✅ Auth URL generated: {auth_url[:50]}...")
    print(f"✅ State generated: {state}")
    
    # 2. Open browser automatically
    print("📡 Step 2: Opening browser...")
    browser = webbrowser.Chrome()
    
    try:
        # 3. Navigate to Upstox
        print("📡 Step 3: Navigating to Upstox...")
        browser.get(auth_url)
        
        # 4. Wait for user to complete authentication
        print("⏳ Step 4: Waiting for authentication...")
        print("   Please complete authentication on Upstox")
        print("   The browser will automatically redirect back to your app")
        
        # Wait for redirect to our app
        max_wait_time = 120  # 2 minutes max
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            if "localhost:3000/auth/success" in browser.current_url:
                print("✅ Step 5: Authentication successful!")
                print("✅ Redirect detected - closing browser...")
                time.sleep(2)
                browser.quit()
                return True
            time.sleep(1)
        
        print("⏰ Timeout - authentication not completed")
        browser.quit()
        return False
        
    except Exception as e:
        print(f"❌ Error during OAuth flow: {e}")
        browser.quit()
        return False

def verify_authentication():
    """Verify authentication status"""
    print("🔍 Step 6: Verifying authentication...")
    
    # Check debug endpoint
    response = requests.get("http://localhost:8000/api/v1/debug/auth-session",
                           headers={"accept": "application/json"})
    
    if response.status_code == 200:
        debug_data = response.json()
        if debug_data.get("authenticated"):
            print("✅ Authentication verified!")
            print(f"✅ Token expires: {debug_data.get('token_expiry')}")
            print(f"✅ State validation enabled: {debug_data.get('state_validation_enabled')}")
            return True
        else:
            print("❌ Authentication not verified")
            return False
    else:
        print("❌ Failed to verify authentication")
        return False

if __name__ == "__main__":
    print("🎯 OAuth Flow Automation Tool")
    print("=" * 50)
    
    # Test OAuth flow
    success = test_oauth_flow()
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 OAuth FLOW TEST COMPLETED SUCCESSFULLY!")
        print("✅ You should now be authenticated in your app")
        print("✅ Check your dashboard at: http://localhost:3000")
        
        # Verify authentication
        verify_authentication()
    else:
        print("\n" + "=" * 50)
        print("❌ OAuth FLOW TEST FAILED")
        print("❌ Please check:")
        print("   1. Backend server is running on port 8000")
        print("   2. Frontend app is running on port 3000")
        print("   3. Upstox credentials are configured")
        print("   4. No firewall blocking the ports")
