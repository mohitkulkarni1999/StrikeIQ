"""
Shared spot price utility for StrikeIQ backend.

Centralizes spot price extraction logic to avoid duplication
and ensure consistent handling across all endpoints.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Instrument key mapping for Upstox API v2/v3
INSTRUMENT_MAP = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank"
}

async def get_spot_price(symbol: str) -> Optional[float]:
    """
    Get spot price for a symbol using centralized logic.
    
    Args:
        symbol: Trading symbol (e.g., "NIFTY", "BANKNIFTY")
        
    Returns:
        Spot price as float, or None if unavailable
        
    Raises:
        No exceptions - handles errors internally and returns None
    """
    try:
        logger.info(f"[SPOT] Fetching spot price for {symbol}")
        
        # Validate symbol
        symbol_upper = symbol.upper()
        if symbol_upper not in INSTRUMENT_MAP:
            logger.error(f"[SPOT] Unknown symbol: {symbol}")
            return None
        
        instrument_key = INSTRUMENT_MAP[symbol_upper]
        logger.info(f"[SPOT] Mapped {symbol} to instrument key: {instrument_key}")
        
        # Import auth service and client locally to avoid circular imports
        from ..services.upstox_auth_service import get_upstox_auth_service
        from ..services.market_data.upstox_client import UpstoxClient
        
        # Get authentication service and token
        auth_service = get_upstox_auth_service()
        token = await auth_service.get_valid_access_token()
        
        if not token:
            logger.error(f"[SPOT] No valid token available for {symbol}")
            return None
        
        logger.info(f"[SPOT] Using token: {token[:20]}...")
        
        # Create client and fetch quote
        client = UpstoxClient()
        try:
            api_response = await client.get_market_quote(token, instrument_key)
            logger.info(f"[SPOT] Raw API response: {api_response}")
        finally:
            await client.close()
        
        # Parse response using the working logic from dashboard service
        spot_price = _parse_spot_price_response(symbol, api_response)
        
        if spot_price is not None:
            logger.info(f"[SPOT] Successfully extracted spot price for {symbol}: {spot_price}")
        else:
            logger.warning(f"[SPOT] Failed to extract spot price for {symbol}")
        
        return spot_price
        
    except Exception as e:
        logger.error(f"[SPOT] Unexpected error for {symbol}: {type(e).__name__}: {e}")
        return None

def _parse_spot_price_response(symbol: str, api_response: Dict[str, Any]) -> Optional[float]:
    """
    Parse spot price from Upstox API response.
    
    Uses the same logic as the working dashboard service.
    """
    try:
        # Validate Upstox response
        if api_response.get("status") != "success":
            logger.error(f"[SPOT] Upstox API error: {api_response}")
            return None
        
        data = api_response.get("data", {})
        
        if not data:
            logger.error(f"[SPOT] Empty LTP response: {api_response}")
            return None
        
        # Extract nested instrument data - this handles the actual response structure
        instrument_data = next(iter(data.values()), None)
        
        if not instrument_data:
            logger.error(f"[SPOT] No instrument data in response: {api_response}")
            return None
        
        ltp = instrument_data.get("last_price")
        
        if ltp is None:
            logger.error(f"[SPOT] No last_price in instrument data: {instrument_data}")
            return None
        
        # Validate that LTP is a positive number
        try:
            spot_price = float(ltp)
            if spot_price <= 0:
                logger.error(f"[SPOT] Invalid spot price (<= 0): {spot_price}")
                return None
            return spot_price
        except (ValueError, TypeError) as e:
            logger.error(f"[SPOT] Could not convert LTP to float: {ltp} - {e}")
            return None
            
    except Exception as e:
        logger.error(f"[SPOT] Error parsing spot price response for {symbol}: {e}")
        return None

def get_instrument_key(symbol: str) -> Optional[str]:
    """
    Get instrument key for a symbol.
    
    Args:
        symbol: Trading symbol
        
    Returns:
        Instrument key string or None if unknown symbol
    """
    symbol_upper = symbol.upper()
    return INSTRUMENT_MAP.get(symbol_upper)
