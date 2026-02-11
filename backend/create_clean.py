import sys
import os

# Read the file
with open('app/services/market_dashboard_service.py', 'r') as f:
    content = f.read()

# Create a completely new, clean version
clean_content = '''import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
import httpx
from ..services.upstox_auth_service import UpstoxAuthService
from ..core.config import settings

class MarketDashboardService:
    def __init__(self, db):
        self.db = db
        self.auth_service = UpstoxAuthService()
        self.client = None
        self.access_token = None
        self.token_expires_at = None

    async def _get_access_token(self):
        """Get valid access token"""
        try:
            # Check if we have a valid token
            if self.access_token and self.token_expires_at:
                if datetime.now() < self.token_expires_at:
                    return self.access_token
            
            # Get new token
            token_data = await self.auth_service.get_access_token()
            if 'access_token' in token_data:
                self.access_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # Buffer of 60 seconds
                
                # Initialize HTTP client with token
                self.client = httpx.AsyncClient(
                    base_url="https://api.upstox.com/v3",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                return self.access_token
        except Exception as e:
            logging.error(f"Error getting access token: {e}")
            return None

    async def get_dashboard_data(self, symbol: str) -> Dict[str, Any]:
        try:
            # Get access token
            token = await self._get_access_token()
            if not token:
                return self._get_fallback_data(symbol)

            # Try common NIFTY instrument keys first - UPDATED WITH CORRECT FORMAT
            common_keys = [
                "NSE_INDEX|NIFTY50",  # Main NIFTY 50 index
                "NSE_INDEX|NIFTY 50",  # Alternative format
                "NSE_INDEX|NIFTY",     # Alternative format
                "NSE_INDEX|NIFTY100",    # NIFTY 100 index
                "NSE_INDEX|NIFTY 200",    # NIFTY 200 index
                "NSE_INDEX|NIFTY 500",    # NIFTY 500 index
                "NSE_INDEX|NIFTY NEXT 50", # NIFTY Next 50
                "NSE_INDEX|NIFTY50 EQL Wgt", # NIFTY50 Equal Weight
                "NSE_INDEX|NIFTY50 PR 1x Inv", # NIFTY50 PR 1x Inv
                "NSE_INDEX|NIFTY50 PR 2x Lev", # NIFTY50 PR 2x Lev
                "NSE_INDEX|NIFTY50 USD",      # NIFTY50 USD
                "NSE_INDEX|NIFTY100",       # NIFTY100
                "NSE_INDEX|NIFTY200",       # NIFTY200
                "NSE_INDEX|NIFTY500",       # NIFTY500
                "NSE_INDEX|NIFTY TOTAL MKT"  # NIFTY Total Market
            ]
            
            # Try both LTP and index quote endpoints
            endpoints_to_try = ["/market-quote/ltp", "/market-quote/quote"]
            
            for endpoint in endpoints_to_try:
                for instrument_key in common_keys:
                    try:
                        # Add delay to avoid rate limiting
                        await asyncio.sleep(1)  # 1 second delay between requests
                        response = await self.client.get(endpoint, params={"instrument_key": instrument_key})
                        logging.info(f"Trying {endpoint} with key: {instrument_key}")
                        logging.info(f"Response Status: {response.status_code}")
                        
                        if response.status_code == 200:
                            data = response.json()
                            logging.info(f"Success with key {instrument_key}: {data}")
                            
                            if 'data' in data and data['data'] and data['data'] != {}:
                                ltp_data = data['data']
                                logging.info(f"LTP data: {ltp_data}")
                                
                                # Extract LTP from different possible structures
                                ltp = 0
                                if isinstance(ltp_data, dict):
                                    ltp = ltp_data.get('last_price', 0) or ltp_data.get('ltp', 0) or ltp_data.get('price', 0)
                                elif isinstance(ltp_data, list) and ltp_data:
                                    ltp = ltp_data[0].get('last_price', 0) or ltp_data[0].get('ltp', 0) or ltp_data[0].get('price', 0)
                                
                                if ltp > 0:
                                    logging.info(f"Found valid LTP: {ltp}")
                                    return {
                                        "current_market": {
                                            "spot_price": ltp,
                                            "change": 0,
                                            "change_percent": 0
                                        }
                                    }
                                else:
                                    logging.warning(f"LTP is 0, data structure: {ltp_data}")
                            else:
                                logging.warning(f"Empty data field for {instrument_key}, full response: {data}")
                                # Check if data is in a different format
                                if 'status' in data and data.get('status') == 'success':
                                    logging.info(f"API success but no data, checking alternative fields")
                                    # Try to find data in other possible locations
                                    for key in data:
                                        if key != 'status' and data[key]:
                                            logging.info(f"Found alternative data field: {key} = {data[key]}")
                                            # Check if alternative field contains the required data
                                            if isinstance(data[key], dict) and 'last_price' in data[key]:
                                                ltp = data[key]['last_price']
                                                if ltp > 0:
                                                    logging.info(f"Found valid LTP in alternative field: {ltp}")
                                                    return {
                                                        "current_market": {
                                                            "spot_price": ltp,
                                                            "change": 0,
                                                            "change_percent": 0
                                                        }
                                                    }
                        else:
                            logging.warning(f"HTTP {response.status_code} for {instrument_key}")
                    except Exception as e:
                        logging.error(f"Error with key {instrument_key}: {e}")
                        continue

            # Add delay before starting instruments discovery
            logging.info("Waiting 2 seconds before instruments discovery...")
            await asyncio.sleep(2)  # 2 second delay before instruments discovery
            
            # If common keys fail, try to get instruments from different endpoints
            instrument_endpoints = ["/instrument/master", "/instruments/master", "/instruments"]
            for endpoint in instrument_endpoints:
                try:
                    # Add delay to avoid rate limiting
                    await asyncio.sleep(1)  # 1 second delay between requests
                    instruments_response = await self.client.get(endpoint)
                    logging.info(f"Trying instruments endpoint: {endpoint}")
                    logging.info(f"Response Status: {instruments_response.status_code}")
                    
                    if instruments_response.status_code == 200:
                        instruments_data = instruments_response.json()
                        logging.info(f"Instruments endpoint {endpoint} worked")
                        
                        # Look for NIFTY in the response
                        instruments_list = instruments_data.get('data', []) if isinstance(instruments_data, dict) else instruments_data
                        for instrument in instruments_list:
                            if isinstance(instrument, dict):
                                name = instrument.get('name', '').upper()
                                tradingsymbol = instrument.get('tradingsymbol', '').upper()
                                if 'NIFTY' in name or 'NIFTY' in tradingsymbol:
                                    instrument_key = instrument.get('instrument_key') or instrument.get('instrument_token')
                                    if instrument_key:
                                        logging.info(f"Found NIFTY instrument: {name}, key: {instrument_key}")
                                        
                                        # Try to get quote with this key
                                        response = await self.client.get("/market-quote/ltp", params={"instrument_key": instrument_key})
                                        if response.status_code == 200:
                                            data = response.json()
                                            if 'data' in data and data['data'] and data['data'] != {}:
                                                ltp_data = data['data']
                                                ltp = 0
                                                if isinstance(ltp_data, dict):
                                                    ltp = ltp_data.get('last_price', 0) or ltp_data.get('ltp', 0) or ltp_data.get('price', 0)
                                                elif isinstance(ltp_data, list) and ltp_data:
                                                    ltp = ltp_data[0].get('last_price', 0) or ltp_data[0].get('ltp', 0) or ltp_data[0].get('price', 0)
                                                
                                                if ltp > 0:
                                                    return {
                                                        "current_market": {
                                                            "spot_price": ltp,
                                                            "change": 0,
                                                            "change_percent": 0
                                                        }
                                                    }
                        break
                except Exception as e:
                    logging.error(f"Error with instruments endpoint {endpoint}: {e}")
                    continue
            
            # If all failed, return fallback
            fallback_data = self._get_fallback_data(symbol)
            logging.info(f"Returning fallback data: {fallback_data}")
            return fallback_data
        except Exception as e:
            logging.error(f"Error in get_dashboard_data: {e}")
            return self._get_fallback_data(symbol)

    def _get_fallback_data(self, symbol):
        """Get fallback data when API fails"""
        import datetime
        
        # Determine market status based on time
        now = datetime.datetime.now()
        market_hours = (9 <= now.hour < 16 and now.weekday() < 5)  # 9:15 AM to 3:30 PM, Mon-Fri
        
        if market_hours:
            market_status = "error"
            message = "Data Unavailable"
        else:
            market_status = "closed"
            message = "Market Closed"
        
        return {
            "current_market": {
                "symbol": symbol,
                "spot_price": None,
                "vwap": None,
                "change": None,
                "change_percent": None,
                "volume": None,
                "timestamp": datetime.datetime.now().isoformat(),
                "market_status": market_status.upper(),
                "message": message
            },
            "real_time_signals": {
                "timestamp": datetime.datetime.now().isoformat(),
                "bias_signal": {
                    "action": "NEUTRAL",
                    "strength": "WEAK",
                    "confidence": 0
                },
                "expected_move_signal": {
                    "signal": "NEUTRAL",
                    "action": "HOLD",
                    "distance": 0
                },
                "smart_money_signal": {
                    "signal": "NEUTRAL",
                    "action": "HOLD"
                },
                "overall_signal": {
                    "action": "HOLD",
                    "strength": "WEAK",
                    "confidence": 0,
                    "reasoning": message
                }
            },
            "historical_analysis": [],
            "market_status": market_status,
            "message": message
        }
'''

# Write the clean version
with open('app/services/market_dashboard_service.py', 'w') as f:
    f.write(clean_content)

print("✅ Created clean, fixed version!")
