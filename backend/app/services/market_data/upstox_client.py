import asyncio
import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from ...core.config import settings
from .types import InstrumentInfo, APIResponseError, AuthenticationError, TokenExpiredError

logger = logging.getLogger(__name__)

class UpstoxClient:
    """Pure API client for Upstox API"""
    
    def __init__(self):
        self.base_url = "https://api.upstox.com/v3"
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self, access_token: str) -> httpx.AsyncClient:
        """Get authenticated HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=30.0
            )
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def get_instruments(self, access_token: str) -> List[Dict[str, Any]]:
        """Fetch all instruments from Upstox"""
        try:
            client = await self._get_client(access_token)
            response = await client.get("/instruments")
            
            if response.status_code == 401:
                raise TokenExpiredError("Access token expired")
            elif response.status_code != 200:
                raise APIResponseError(f"HTTP {response.status_code}: {response.text}")
            
            data = response.json()
            if not isinstance(data, list):
                raise APIResponseError(f"Expected list, got {type(data)}")
            
            return data
            
        except httpx.RequestError as e:
            logger.error(f"Network error fetching instruments: {e}")
            raise APIResponseError(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching instruments: {e}")
            raise APIResponseError(f"Unexpected error: {e}")
    
    async def get_market_quote(self, access_token: str, instrument_key: str) -> Dict[str, Any]:
        """Get market quote for specific instrument"""
        try:
            client = await self._get_client(access_token)
            response = await client.get("/market-quote/ltp", params={"instrument_key": instrument_key})
            
            if response.status_code == 401:
                raise TokenExpiredError("Access token expired")
            elif response.status_code != 200:
                raise APIResponseError(f"HTTP {response.status_code}: {response.text}")
            
            data = response.json()
            
            # Validate response structure according to Upstox schema
            if not isinstance(data, dict):
                raise APIResponseError(f"Expected dict, got {type(data)}")
            
            if "status" not in data:
                raise APIResponseError("Missing 'status' field in response")
            
            if data["status"] != "success":
                raise APIResponseError(f"API returned status: {data['status']}")
            
            # Check for data field
            if "data" not in data:
                raise APIResponseError("Missing 'data' field in response")
            
            return data
            
        except httpx.RequestError as e:
            logger.error(f"Network error fetching quote for {instrument_key}: {e}")
            raise APIResponseError(f"Network error: {e}")
        except TokenExpiredError as e:
            logger.error(f"Token expired fetching quote for {instrument_key}: {e}")
            raise  # Re-raise TokenExpiredError without changing it
        except APIResponseError as e:
            logger.error(f"API error fetching quote for {instrument_key}: {e}")
            raise  # Re-raise APIResponseError without changing it
        except Exception as e:
            logger.error(f"Unexpected error fetching quote for {instrument_key}: {e}")
            raise APIResponseError(f"Unexpected error: {e}")
