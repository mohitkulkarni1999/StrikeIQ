"""
Fix token issue by clearing invalid credentials
"""

import json
import os
from datetime import datetime, timezone

def fix_token_issue():
    """Clear invalid credentials and provide auth URL"""
    
    print("🔧 Fixing Token Issue")
    print("=" * 40)
    
    # Check current credentials
    if os.path.exists('upstox_credentials.json'):
        with open('upstox_credentials.json', 'r') as f:
            creds = json.load(f)
        
        print(f"Current token expires at: {creds['expires_at']}")
        print(f"Current time: {datetime.now(timezone.utc)}")
        print(f"Refresh token available: {bool(creds.get('refresh_token'))}")
        
        # The token is being rejected by Upstox, so we need to clear it
        print("\n🗑️ Clearing invalid credentials...")
        os.remove('upstox_credentials.json')
        print("✅ Credentials cleared")
        
    else:
        print("ℹ️ No credentials file found")
    
    # Provide auth URL
    auth_url = "https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id=53c878a9-3f5d-44f9-aa2d-2528d34a24cd&redirect_uri=http://localhost:8000/api/v1/auth/upstox/callback"
    
    print(f"\n🔗 Please visit this URL to re-authenticate:")
    print(auth_url)
    
    print(f"\n📋 After authentication:")
    print("1. The callback will store new credentials")
    print("2. The frontend will be redirected to the dashboard")
    print("3. All API calls will work normally")
    
    return auth_url

if __name__ == "__main__":
    auth_url = fix_token_issue()
    print(f"\n🎯 Auth URL: {auth_url}")
