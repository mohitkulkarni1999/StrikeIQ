#!/usr/bin/env python3
"""
Fresh Token Generator with Proper Parameters
"""

import requests
import webbrowser
import urllib.parse

# Your Upstox credentials
CLIENT_ID = "53c878a9-3f5d-44f9-aa2d-2528d34a24cd"
CLIENT_SECRET = "ng2tdrlo1k"
REDIRECT_URI = "http://localhost:8000/api/v1/auth/upstox/callback"

def exchange_code_for_token(code):
    """Exchange authorization code for access token"""
    token_url = "https://api.upstox.com/v2/login/authorization/token"
    
    data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(token_url, data=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            
            if access_token:
                print(f"\n✅ SUCCESS! New Access Token:")
                print(f"Token: {access_token[:50]}...")
                print(f"Expires: {token_data.get('expires_in', 'Unknown')}")
                
                # Save to credentials file
                import json
                from datetime import datetime, timezone
                
                credentials = {
                    "access_token": access_token,
                    "refresh_token": token_data.get("refresh_token"),
                    "expires_at": datetime.now(timezone.utc).isoformat()
                }
                
                with open("upstox_credentials.json", "w") as f:
                    json.dump(credentials, f, indent=2)
                
                print("✅ Saved to upstox_credentials.json")
                return access_token
        else:
            print(f"❌ ERROR: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return None

def get_auth_url():
    """Generate authorization URL"""
    auth_params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "read"  # Required scope
    }
    
    return f"https://api.upstox.com/v2/login/authorization/dialog?{urllib.parse.urlencode(auth_params)}"

if __name__ == "__main__":
    print("🔗 Upstox Token Generator v2")
    print("=" * 40)
    
    auth_url = get_auth_url()
    print(f"\n🌐 Authorization URL:\n{auth_url}")
    
    print("\n📋 Instructions:")
    print("1. Opening browser...")
    print("2. Login to Upstox")
    print("3. Authorize the app")
    print("4. Copy the 'code' from redirect URL")
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Get code from user
    code = input("\n🔑 Enter authorization code: ").strip()
    
    if code:
        print(f"\n🔄 Exchanging code for token...")
        token = exchange_code_for_token(code)
        
        if token:
            print(f"\n🎉 Token generation complete!")
        else:
            print(f"\n❌ Token generation failed!")
    else:
        print("\n❌ No code provided!")
