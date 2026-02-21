#!/usr/bin/env python3
"""
Test OAuth flow manually to debug the issue
"""

import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_token_exchange():
    """Test token exchange with the current code"""
    
    # Use a test authorization code (you need to get this from actual OAuth flow)
    test_code = "YCFnzN"  # This is from your callback URL
    
    url = "https://api.upstox.com/v2/login/authorization/token"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "code": test_code,
        "client_id": os.getenv('UPSTOX_API_KEY'),
        "client_secret": os.getenv('UPSTOX_API_SECRET'),
        "redirect_uri": os.getenv('UPSTOX_REDIRECT_URI'),
        "grant_type": "authorization_code"
    }
    
    print(f"Testing token exchange...")
    print(f"URL: {url}")
    print(f"Client ID: {os.getenv('UPSTOX_API_KEY')}")
    print(f"Redirect URI: {os.getenv('UPSTOX_REDIRECT_URI')}")
    print(f"Code: {test_code}")
    
    try:
        response = httpx.post(url, headers=headers, data=data)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            print("SUCCESS: Token exchange worked!")
            print(f"Access token: {token_data.get('access_token', 'N/A')[:20]}...")
            print(f"Refresh token: {token_data.get('refresh_token', 'N/A')[:20]}...")
            print(f"Expires in: {token_data.get('expires_in', 'N/A')}")
        else:
            print("FAILED: Token exchange failed")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_token_exchange()
