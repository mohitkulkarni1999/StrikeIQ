
import json
import urllib.request
import urllib.error
import sys
import os

# Load credentials
CREDENTIALS_FILE = 'backend/upstox_credentials.json'

def load_credentials():
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None

def test_api():
    creds = load_credentials()
    if not creds:
        return

    access_token = creds.get('access_token')
    if not access_token:
        print("No access token found in credentials.")
        return

    print(f"Using Access Token: {access_token[:10]}...") 

    url = "https://api.upstox.com/v2/market-quote/ltp?instrument_key=NSE_INDEX|NIFTY%2050"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            print(f"Status Code: {response.status}")
            print(f"Response: {response.read().decode('utf-8')}")
            
    except urllib.error.HTTPError as e:
        print(f"API Request failed with HTTP Error: {e.code} - {e.reason}")
        print(e.read().decode('utf-8'))
    except Exception as e:
        print(f"API Request failed: {e}")

if __name__ == "__main__":
    test_api()
