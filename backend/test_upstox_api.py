#!/usr/bin/env python3

import asyncio
import httpx
import urllib.parse

async def test_upstox_api():
    """Test the Upstox API with different instrument keys"""
    
    # Test token (expired, but will show us the structure)
    token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIxMjkwNjMiLCJqdGkiOiI2OTk5YTU0NTliZWNkZDViZDA5NGUyYzkiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc3MTY3Njk3NywiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzcxNzExMjAwfQ.qkzij7F8M3t6xu9ihozbjvHYDEAwZZwWDSMErMC_hg8"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        
        # Test 1: NIFTY with NSE_INDEX (user's working example)
        print("=== Test 1: NIFTY with NSE_INDEX ===")
        try:
            url1 = "https://api.upstox.com/v2/option/contract?instrument_key=NSE_INDEX%7CNifty%2050"
            response1 = await client.get(url1, headers={
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            })
            print(f"Status: {response1.status_code}")
            if response1.status_code == 200:
                data1 = response1.json()
                if isinstance(data1, dict) and 'data' in data1:
                    contracts1 = data1['data']
                    expiries1 = set()
                    for contract in contracts1[:5]:  # First 5 contracts
                        expiry = contract.get('expiry')
                        if expiry:
                            expiries1.add(expiry)
                    print(f"Found expiries: {sorted(list(expiries1))}")
                else:
                    print("No data field in response")
            else:
                print(f"Error: {response1.text[:200]}")
        except Exception as e:
            print(f"Exception: {e}")
        
        print("\n=== Test 2: NIFTY with NFO_FO ===")
        # Test 2: NIFTY with NFO_FO (our backend approach)
        try:
            url2 = "https://api.upstox.com/v2/option/contract?instrument_key=NFO_FO%7CNIFTY"
            response2 = await client.get(url2, headers={
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            })
            print(f"Status: {response2.status_code}")
            if response2.status_code == 200:
                data2 = response2.json()
                if isinstance(data2, dict) and 'data' in data2:
                    contracts2 = data2['data']
                    expiries2 = set()
                    for contract in contracts2[:5]:  # First 5 contracts
                        expiry = contract.get('expiry')
                        if expiry:
                            expiries2.add(expiry)
                    print(f"Found expiries: {sorted(list(expiries2))}")
                else:
                    print("No data field in response")
            else:
                print(f"Error: {response2.text[:200]}")
        except Exception as e:
            print(f"Exception: {e}")
        
        print("\n=== Test 3: BANKNIFTY with NFO_FO ===")
        # Test 3: BANKNIFTY with NFO_FO (what our backend should use)
        try:
            url3 = "https://api.upstox.com/v2/option/contract?instrument_key=NFO_FO%7CBANKNIFTY"
            response3 = await client.get(url3, headers={
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            })
            print(f"Status: {response3.status_code}")
            if response3.status_code == 200:
                data3 = response3.json()
                if isinstance(data3, dict) and 'data' in data3:
                    contracts3 = data3['data']
                    expiries3 = set()
                    for contract in contracts3[:5]:  # First 5 contracts
                        expiry = contract.get('expiry')
                        if expiry:
                            expiries3.add(expiry)
                    print(f"Found expiries: {sorted(list(expiries3))}")
                else:
                    print("No data field in response")
            else:
                print(f"Error: {response3.text[:200]}")
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_upstox_api())
