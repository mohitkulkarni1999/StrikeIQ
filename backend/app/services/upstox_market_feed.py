"""
Upstox Market Data Feed V3 Service
Handles connection to Upstox WebSocket feed, decoding, and normalization
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
# import protobuf  # Will need to install protobuf - making optional for now
from app.services.upstox_auth_service import UpstoxAuthService
from app.core.live_market_state import MarketStateManager
import httpx

logger = logging.getLogger(__name__)

@dataclass
class FeedConfig:
    """Configuration for market data feed"""
    symbol: str
    spot_instrument_key: str
    strike_range: int = 10  # ATM ± 10 strikes
    mode: str = "full"  # full, ltpc, option_greeks, full_d30
    reconnect_delay: int = 5
    heartbeat_interval: int = 30

class UpstoxMarketFeed:
    """
    Handles Upstox Market Data Feed V3 connection and data processing
    """
    
    def __init__(self, config: FeedConfig):
        self.config = config
        self.auth_service = UpstoxAuthService()
        self.market_state = MarketStateManager()
        self.websocket = None
        self.authorized_url = None
        self.is_running = False
        self.last_heartbeat = None
        
    async def get_authorized_websocket_url(self) -> Optional[str]:
        """
        Get authorized WebSocket URL from Upstox API
        """
        try:
            # Get valid access token with automatic refresh
            access_token = await self.auth_service.get_valid_access_token()
            if not access_token:
                logger.error("No valid access token available")
                return None
                
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.upstox.com/v3/feed/market-data-feed/authorize",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", {}).get("authorized_redirect_uri")
                else:
                    logger.error(f"Failed to get authorized URL: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting authorized WebSocket URL: {e}")
            return None
    
    async def connect_to_feed(self) -> bool:
        """
        Connect to Upstox WebSocket feed
        """
        try:
            # Get authorized URL
            self.authorized_url = await self.get_authorized_websocket_url()
            if not self.authorized_url:
                return False
            
            logger.info(f"Connecting to Upstox feed: {self.config.symbol}")
            
            # Connect to WebSocket
            self.websocket = await websockets.connect(
                self.authorized_url,
                ping_interval=20,
                ping_timeout=10
            )
            
            logger.info(f"Connected to Upstox feed for {self.config.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Upstox feed: {e}")
            return False
    
    async def subscribe_to_instruments(self, instrument_keys: List[str]) -> bool:
        """
        Subscribe to specific instruments
        """
        try:
            subscription_message = {
                "guid": f"strikeiq_{int(datetime.now().timestamp())}",
                "method": "sub",
                "data": {
                    "mode": self.config.mode,
                    "instrumentKeys": instrument_keys
                }
            }
            
            # Send subscription request in binary format
            message_bytes = json.dumps(subscription_message).encode('utf-8')
            await self.websocket.send(message_bytes)
            
            logger.info(f"Subscribed to {len(instrument_keys)} instruments for {self.config.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to instruments: {e}")
            return False
    
    async def get_active_strikes(self) -> List[str]:
        """
        Get ATM ± strike range instruments to subscribe to
        """
        try:
            # Get current option chain to find ATM and active strikes
            # Get valid access token with automatic refresh
            access_token = await self.auth_service.get_valid_access_token()
            if not access_token:
                logger.error("No valid access token available for option chain")
                return None
                
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            # Get spot price first
            spot_url = f"https://api.upstox.com/v3/market-quote/ltp?instrument_key={self.config.spot_instrument_key}"
            async with httpx.AsyncClient() as client:
                spot_response = await client.get(spot_url, headers=headers)
                if spot_response.status_code != 200:
                    logger.error("Failed to get spot price")
                    return []
                
                spot_data = spot_response.json()
                spot_price = float(spot_data["data"]["ltp"])
            
            # Get option chain to find active strikes
            chain_url = f"https://api.upstox.com/v2/option/chain?instrument_key={self.config.spot_instrument_key}"
            chain_response = await client.get(chain_url, headers=headers)
            
            if chain_response.status_code != 200:
                logger.error("Failed to get option chain")
                return []
            
            chain_data = chain_response.json()
            
            # Find ATM strike and get range
            all_strikes = []
            for option_data in chain_data.get("data", []):
                strike = option_data.get("strike_price", 0)
                if strike > 0:
                    all_strikes.append(strike)
            
            if not all_strikes:
                logger.error("No strikes found in option chain")
                return []
            
            # Find ATM strike
            atm_strike = min(all_strikes, key=lambda x: abs(x - spot_price))
            
            # Get strike range (ATM ± configured range)
            strike_range = []
            for strike in all_strikes:
                if abs(strike - atm_strike) <= (self.config.strike_range * 50):  # 50 point intervals
                    strike_range.append(strike)
            
            # Sort and limit strikes
            strike_range.sort()
            if len(strike_range) > (self.config.strike_range * 2 + 1):
                center_idx = strike_range.index(atm_strike)
                start_idx = max(0, center_idx - self.config.strike_range)
                end_idx = min(len(strike_range), center_idx + self.config.strike_range + 1)
                strike_range = strike_range[start_idx:end_idx]
            
            # Convert to instrument keys
            instrument_keys = [self.config.spot_instrument_key]  # Add spot
            
            # Add option strikes
            for strike in strike_range:
                # NFO options format
                instrument_keys.append(f"NFO_FO|{strike}-CE")
                instrument_keys.append(f"NFO_FO|{strike}-PE")
            
            logger.info(f"Selected {len(instrument_keys)} instruments for {self.config.symbol} (ATM: {atm_strike})")
            return instrument_keys
            
        except Exception as e:
            logger.error(f"Error getting active strikes: {e}")
            return []
    
    async def process_message(self, message: bytes) -> None:
        """
        Process incoming WebSocket message from Upstox
        """
        try:
            # Decode protobuf message (placeholder - need actual proto implementation)
            # For now, handle JSON messages during development
            if isinstance(message, bytes):
                try:
                    decoded_message = message.decode('utf-8')
                    data = json.loads(decoded_message)
                except:
                    # This would be protobuf decoding in production
                    logger.debug("Received binary protobuf message")
                    return
            else:
                data = message
            
            message_type = data.get("type")
            
            if message_type == "market_info":
                logger.info("Received market status info")
                self.last_heartbeat = datetime.now(timezone.utc)
                
            elif message_type == "live_feed":
                await self.process_live_feed(data)
                
            else:
                logger.debug(f"Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def process_live_feed(self, data: Dict[str, Any]) -> None:
        """
        Process live market data feed
        """
        try:
            feeds = data.get("feeds", {})
            timestamp = data.get("currentTs")
            
            for instrument_key, feed_data in feeds.items():
                # Extract relevant data based on mode
                processed_data = {
                    "instrument_key": instrument_key,
                    "timestamp": timestamp,
                    "ltp": feed_data.get("ltpc", {}).get("ltp"),
                    "ltt": feed_data.get("ltpc", {}).get("ltt"),
                    "ltq": feed_data.get("ltpc", {}).get("ltq"),
                    "cp": feed_data.get("ltpc", {}).get("cp"),
                }
                
                # Add option greeks if available
                if "option_greeks" in feed_data:
                    greeks = feed_data["option_greeks"]
                    processed_data.update({
                        "delta": greeks.get("delta"),
                        "gamma": greeks.get("gamma"),
                        "theta": greeks.get("theta"),
                        "vega": greeks.get("vega"),
                        "iv": greeks.get("iv")
                    })
                
                # Update market state
                self.market_state.update_instrument_data(self.config.symbol, instrument_key, processed_data)
                
        except Exception as e:
            logger.error(f"Error processing live feed: {e}")
    
    async def run_feed_loop(self) -> None:
        """
        Main feed loop - connect, subscribe, and process messages
        """
        while self.is_running:
            try:
                # Connect to feed
                if not await self.connect_to_feed():
                    await asyncio.sleep(self.config.reconnect_delay)
                    continue
                
                # Get instruments to subscribe to
                instrument_keys = await self.get_active_strikes()
                if not instrument_keys:
                    await asyncio.sleep(self.config.reconnect_delay)
                    continue
                
                # Subscribe to instruments
                if not await self.subscribe_to_instruments(instrument_keys):
                    await asyncio.sleep(self.config.reconnect_delay)
                    continue
                
                # Process messages
                async for message in self.websocket:
                    await self.process_message(message)
                    
                    # Check heartbeat
                    if (self.last_heartbeat and 
                        (datetime.now(timezone.utc) - self.last_heartbeat).seconds > self.config.heartbeat_interval * 2):
                        logger.warning("Heartbeat timeout, reconnecting...")
                        break
                
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed, reconnecting...")
            except Exception as e:
                logger.error(f"Feed loop error: {e}")
            
            # Cleanup and reconnect delay
            if self.websocket:
                try:
                    await self.websocket.close()
                except:
                    pass
            
            await asyncio.sleep(self.config.reconnect_delay)
    
    async def start(self) -> None:
        """
        Start the market feed service
        """
        self.is_running = True
        logger.info(f"Starting Upstox market feed for {self.config.symbol}")
        
        # Run feed loop in background
        asyncio.create_task(self.run_feed_loop())
    
    async def stop(self) -> None:
        """
        Stop the market feed service
        """
        self.is_running = False
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass
        logger.info(f"Stopped Upstox market feed for {self.config.symbol}")
