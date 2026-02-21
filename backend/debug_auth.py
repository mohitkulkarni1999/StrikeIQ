#!/usr/bin/env python3

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
import httpx

def debug_token_exchange():
    """Debug token exchange process"""
    print("=== Token Exchange Debug ===")
    print(f"API Key: {settings.UPSTOX_API_KEY}")
    print(f"API Secret: {settings.UPSTOX_API_SECRET}")
    print(f"Redirect URI: {settings.REDIRECT_URI}")
    print(f"Environment: {settings.ENVIRONMENT}")
    
    # Test with the NEW code you provided
    code = "TAwYh3"
    
    url = "https://api.upstox.com/v2/login/authorization/token"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "code": code,
        "client_id": settings.UPSTOX_API_KEY,
        "client_secret": settings.UPSTOX_API_SECRET,
        "redirect_uri": settings.REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    print(f"\nMaking request to: {url}")
    print(f"Data: {data}")
    
    try:
        response = httpx.post(url, headers=headers, data=data)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"\nSuccess! Token data keys: {list(token_data.keys())}")
        else:
            print(f"\nError: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"\nException: {e}")

if __name__ == "__main__":
    debug_token_exchange()
