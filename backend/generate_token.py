#!/usr/bin/env python3
"""
Upstox Token Generator
"""

import webbrowser
import urllib.parse

# Your Upstox credentials
CLIENT_ID = "53c878a9-3f5d-44f9-aa2d-2528d34a24cd"
REDIRECT_URI = "http://localhost:8000/api/v1/auth/upstox/callback"

# Build authorization URL
auth_params = {
    "response_type": "code",
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "scope": "read"  # Add required scopes
}

auth_url = f"https://api.upstox.com/v2/login/authorization/dialog?{urllib.parse.urlencode(auth_params)}"

print("🔗 Upstox Authorization URL:")
print(auth_url)
print("\n📋 Instructions:")
print("1. Copy and paste the URL above in your browser")
print("2. Login to Upstox and authorize the app")
print("3. After authorization, you'll be redirected to your callback URL")
print("4. Copy the 'code' parameter from the redirect URL")
print("\n🌐 Opening browser automatically...")

# Open browser
webbrowser.open(auth_url)

# Wait for user to provide code
code = input("\n🔑 Enter the authorization code from redirect URL: ")

print(f"\n✅ Received code: {code[:20]}...")
print("\n📤 Now use this code to get access token with:")
print(f"curl -X POST 'https://api.upstox.com/v2/login/authorization/token' \\")
print(f"  -H 'Content-Type: application/x-www-form-urlencoded' \\")
print(f"  -d 'code={code}&client_id={CLIENT_ID}&client_secret=ng2tdrlo1k&redirect_uri={REDIRECT_URI}&grant_type=authorization_code'")
