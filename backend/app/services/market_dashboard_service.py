import logging
from typing import Dict, Any
import httpx
from ..services.upstox_auth_service import UpstoxAuthService
from ..core.config import settings

class MarketDashboardService:
    def __init__(self, db):
        self.db = db
        self.auth_service = UpstoxAuthService()
        self.client = None
        try:
            access_token = self.auth_service.get_valid_access_token()
            if access_token:
                self.client = httpx.Client(
                    base_url="https://api.upstox.com/v2",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
        except Exception as e:
            logging.error(f"Error initializing Upstox client: {e}")

    async def get_dashboard_data(self, symbol: str) -> Dict[str, Any]:
        try:
            if not self.client:
                return self._get_fallback_data(symbol)

            # Try different instrument key formats
            instrument_keys = [
                f"NSE_INDEX|{symbol}",
                f"NSE:{symbol}",
                symbol
            ]
            
            for instrument_key in instrument_keys:
                try:
                    response = self.client.get(f"/market-quote/ltp", params={"instrument_key": instrument_key})
                    if response.status_code == 200:
                        data = response.json()
                        logging.info(f"Market quote response for {instrument_key}: {data}")
                        
                        if 'data' in data and data['data']:
                            ltp_data = data['data']
                            logging.info(f"LTP data: {ltp_data}")
                            
                            # Extract LTP from different possible structures
                            ltp = 0
                            if isinstance(ltp_data, dict):
                                ltp = ltp_data.get('last_price', 0) or ltp_data.get('ltp', 0)
                            elif isinstance(ltp_data, list) and ltp_data:
                                ltp = ltp_data[0].get('last_price', 0) or ltp_data[0].get('ltp', 0)
                            
                            return {
                                "current_market": {
                                    "spot_price": ltp,
                                    "change": 0,
                                    "change_percent": 0
                                }
                            }
                        else:
                            logging.warning(f"No data in market quote for {instrument_key}")
                except Exception as e:
                    logging.error(f"Error fetching market quote for {instrument_key}: {e}")
                    continue
            
            # If all failed, return fallback
            return self._get_fallback_data(symbol)
        except Exception as e:
            logging.error(f"Error in get_dashboard_data: {e}")
            return self._get_fallback_data(symbol)

    def _get_fallback_data(self, symbol: str) -> Dict[str, Any]:
        # Check market hours
        from datetime import datetime
        now = datetime.now()
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        is_market_open = market_open <= now <= market_close and now.weekday() < 5
        if is_market_open:
            message = "Data Unavailable"
            market_status = "error"
        else:
            message = "Market Closed"
            market_status = "closed"
        return {
            "current_market": {
                "spot_price": None,
                "change": None,
                "change_percent": None,
                "volume": None,
                "vwap": None
            },
            "market_status": market_status,
            "message": message,
            "signals": {
                "bias_signal": {
                    "confidence": 0,
                    "action": "NEUTRAL",
                    "strength": "WEAK"
                }
            }
        }
