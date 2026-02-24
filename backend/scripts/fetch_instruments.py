#!/usr/bin/env python3
"""
Startup script to fetch and cache Upstox instruments
Run this once at server startup to cache instruments locally
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

from app.services.upstox_auth_service import get_upstox_auth_service
from app.services.market_data.upstox_client import UpstoxClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_and_cache_instruments():
    """
    Fetch instruments from Upstox API and cache locally
    """
    try:
        logger.info("Starting instruments fetch and cache...")
        
        # Initialize services
        auth_service = get_upstox_auth_service()
        client = UpstoxClient()
        
        # Get access token
        token = await auth_service.get_valid_access_token()
        if not token:
            logger.error("Failed to get access token")
            return False
        
        # Fetch instruments
        logger.info("Fetching instruments from Upstox API...")
        instruments = await client.get_instruments(token)
        
        if not instruments:
            logger.error("No instruments received")
            return False
        
        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Save to file
        instruments_file = data_dir / "instruments.json"
        
        cache_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "count": len(instruments),
            "instruments": instruments
        }
        
        with open(instruments_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        logger.info(f"Successfully cached {len(instruments)} instruments to {instruments_file}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to fetch and cache instruments: {e}")
        return False
    finally:
        await client.close()

async def load_cached_instruments():
    """
    Load cached instruments from local file
    """
    try:
        instruments_file = Path("data/instruments.json")
        
        if not instruments_file.exists():
            logger.error("Cached instruments file not found")
            return None
        
        with open(instruments_file, 'r') as f:
            cache_data = json.load(f)
        
        instruments = cache_data.get("instruments", [])
        timestamp = cache_data.get("timestamp")
        count = cache_data.get("count", 0)
        
        logger.info(f"Loaded {count} instruments from cache (timestamp: {timestamp})")
        return instruments
        
    except Exception as e:
        logger.error(f"Failed to load cached instruments: {e}")
        return None

if __name__ == "__main__":
    # Run fetch and cache
    success = asyncio.run(fetch_and_cache_instruments())
    
    if success:
        # Test loading
        instruments = asyncio.run(load_cached_instruments())
        if instruments:
            print(f"✅ Instruments cache ready with {len(instruments)} instruments")
        else:
            print("❌ Failed to load cached instruments")
    else:
        print("❌ Failed to fetch and cache instruments")
