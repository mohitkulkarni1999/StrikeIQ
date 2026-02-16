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
from app.services.upstox_auth_service import get_upstox_auth_service
from app.services.token_manager import get_token_manager
from app.core.live_market_state import MarketStateManager
from fastapi import HTTPException
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
    
    def __init__(self, config: FeedConfig, market_state: Optional[MarketStateManager] = None):
        self.config = config
        self.auth_service = get_upstox_auth_service()  # Use shared instance
        self.market_state = market_state or MarketStateManager()
        self.token_manager = get_token_manager()
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
                self.token_manager.invalidate("No valid access token")
                raise HTTPException(
                    status_code=401,
                    detail="Upstox authentication required"
                )
                
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            # Use V2 endpoint for WebSocket authorization
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.upstox.com/v2/feed/market-data-feed/authorize",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Upstox authorize response: {data}")
                    redirect_uri = data.get("data", {}).get("authorized_redirect_uri")
                    if redirect_uri:
                        logger.info(f"Got WebSocket redirect URI: {redirect_uri}")
                        return redirect_uri
                    else:
                        logger.error("No redirect URI in authorize response")
                        return None
                elif response.status_code == 401:
                    logger.error("Upstox token revoked or expired")
                    self.token_manager.invalidate("Upstox token revoked or expired")
                    raise HTTPException(
                        status_code=401,
                        detail="Upstox authentication required"
                    )
                elif response.status_code == 410:
                    # V2 endpoint is deprecated, fallback to V3
                    logger.warning("V2 endpoint deprecated (410 Gone), falling back to V3")
                    v3_response = await client.get(
                        "https://api.upstox.com/v3/feed/market-data-feed/authorize",
                        headers=headers
                    )
                    
                    if v3_response.status_code == 200:
                        v3_data = v3_response.json()
                        logger.info(f"Upstox V3 authorize response: {v3_data}")
                        v3_redirect_uri = v3_data.get("data", {}).get("authorized_redirect_uri")
                        if v3_redirect_uri:
                            logger.info(f"Got WebSocket redirect URI from V3: {v3_redirect_uri}")
                            # STEP 5: VERIFY WE ARE NOT REUSING OLD REDIRECT URI
                            import re
                            request_id_match = re.search(r'requestId=([^&]+)', v3_redirect_uri)
                            if request_id_match:
                                request_id = request_id_match.group(1)
                                logger.warning(f"Authorize requestId: {request_id}")
                            # STEP 4: LOG TIME BETWEEN AUTHORIZE AND CONNECT
                            import time
                            self.authorize_time = time.time()
                            return v3_redirect_uri
                        else:
                            logger.error("No redirect URI in V3 authorize response")
                            return None
                    elif v3_response.status_code == 401:
                        logger.error("Upstox token revoked or expired (V3)")
                        self.token_manager.invalidate("Upstox token revoked or expired")
                        raise HTTPException(
                            status_code=401,
                            detail="Upstox authentication required"
                        )
                    else:
                        logger.error(f"Failed to get V3 authorized URL: {v3_response.status_code}")
                        return None
                elif response.status_code >= 500:
                    # Retry only for server errors (5xx)
                    logger.error(f"Upstox server error: {response.status_code}")
                    return None
                else:
                    logger.error(f"Failed to get authorized URL: {response.status_code}")
                    return None
                    
        except HTTPException:
            # Re-raise HTTPException (401) without modification
            raise
        except Exception as e:
            logger.error(f"Error getting authorized WebSocket URL: {e}")
            return None
    
    async def connect_to_feed(self) -> bool:
        """
        Connect to Upstox WebSocket feed
        """
        try:
            # STEP 6: VERIFY WEBSOCKETS VERSION
            import websockets
            logger.warning(f"Websockets version: {websockets.__version__}")
            
            # Get authorized URL
            self.authorized_url = await self.get_authorized_websocket_url()
            if not self.authorized_url:
                return None
            
            logger.info(f"Connecting to Upstox feed: {self.config.symbol}")
            
            # Connection state tracking
            self.connection_attempts = 0
            self.max_connection_attempts = 5
            self.connection_backoff = 2  # seconds
            
            # Check connection attempts
            if self.connection_attempts >= self.max_connection_attempts:
                logger.warning(f"Max connection attempts ({self.max_connection_attempts}) reached for {self.config.symbol}, backing off")
                return False
            
            self.connection_attempts += 1
            
            # Add delay to prevent rapid reconnections
            await asyncio.sleep(self.connection_backoff)
            
            try:
                # STEP 1: LOG EXACT REDIRECT URI USED
                logger.warning("=== WS DEBUG START ===")
                logger.warning(f"Redirect URI Used: {self.authorized_url}")
                logger.warning(f"URI Length: {len(self.authorized_url)}")
                logger.warning(f"Contains code param: {'code=' in self.authorized_url}")
                logger.warning("=== WS DEBUG END ===")
                
                # STEP 4: LOG TIME BETWEEN AUTHORIZE AND CONNECT
                import time
                connect_time = time.time()
                if hasattr(self, 'authorize_time'):
                    time_diff = connect_time - self.authorize_time
                    logger.warning(f"Time between authorize and connect: {time_diff} seconds")
                
                # STEP 3: FORCE SUBPROTOCOL DEBUG
                async with websockets.connect(
                            self.authorized_url,
                            subprotocols=["json"],
                            ping_interval=20,
                            ping_timeout=10
                        ) as websocket:
                    logger.warning(f"WebSocket subprotocol selected: {websocket.subprotocol}")
                    self.websocket = websocket
                    logger.info(f"WebSocket connected successfully for {self.config.symbol}")
                    # Reset connection attempts on success
                    self.connection_attempts = 0
                    return True
            except Exception as ws_error:
                self.connection_attempts += 1
                logger.error(f"WebSocket connection failed: {ws_error} (attempt {self.connection_attempts})")
                
                # STEP 10: OUTPUT FULL HANDSHAKE ERROR DETAILS
                logger.exception("Full WebSocket failure stacktrace")
                    
                # Check if it's an authentication error
                if "403" in str(ws_error) or "401" in str(ws_error):
                    logger.error("WebSocket authentication failed - token may be invalid for WebSocket feed")
                    # Don't return False here, let the error propagate
                    raise HTTPException(
                        status_code=401,
                        detail="WebSocket authentication failed"
                    )
                elif "connection refused" in str(ws_error).lower() or "connection reset" in str(ws_error).lower():
                    logger.warning("WebSocket connection refused - possible network issue")
                    if self.connection_attempts < self.max_connection_attempts:
                        # Retry with exponential backoff
                        backoff_time = min(self.connection_backoff * (2 ** self.connection_attempts), 30)
                        logger.info(f"Retrying WebSocket connection in {backoff_time} seconds")
                        await asyncio.sleep(backoff_time)
                        return await self.connect_to_feed()
                    else:
                        logger.error("Max connection attempts reached")
                        return False
                else:
                    logger.error(f"Unexpected WebSocket error: {ws_error}")
                    if self.connection_attempts < self.max_connection_attempts:
                        # Retry with exponential backoff
                        backoff_time = min(self.connection_backoff * (2 ** self.connection_attempts), 30)
                        logger.info(f"Retrying WebSocket connection in {backoff_time} seconds")
                        await asyncio.sleep(backoff_time)
                        return await self.connect_to_feed()
                    else:
                        logger.error("Max connection attempts reached")
                        return False
            
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
            # Check token validity first
            self.token_manager.check()
            
            # Get current option chain to find ATM and active strikes
            # Get valid access token with automatic refresh
            access_token = await self.auth_service.get_valid_access_token()
            if not access_token:
                logger.error("No valid access token available for option chain")
                self.token_manager.invalidate("No valid access token")
                raise HTTPException(
                    status_code=401,
                    detail="Upstox authentication required"
                )
                
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            # Get spot price first
            if self.config.symbol.upper() == "BANKNIFTY":
                # Use BankNifty instrument key for spot price
                spot_url = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key=NSE_INDEX|Bank Nifty"
                spot_instrument_key = "NSE_INDEX|Bank Nifty"
            else:
                # Use Nifty instrument key for spot price
                spot_url = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={self.config.spot_instrument_key}"
            
            async with httpx.AsyncClient() as client:
                spot_response = await client.get(spot_url, headers=headers)
                if spot_response.status_code == 401:
                    logger.error("Upstox token revoked or expired (spot price)")
                    self.token_manager.invalidate("Upstox token revoked or expired")
                    raise HTTPException(
                        status_code=401,
                        detail="Upstox authentication required"
                    )
                elif spot_response.status_code != 200:
                    logger.error(f"Failed to get spot price: {spot_response.status_code} - {spot_response.text}")
                    return []
                
                try:
                    spot_data = spot_response.json()
                    # Handle different response formats
                    if "data" in spot_data:
                        data = spot_data["data"]
                        # Check for empty data (BankNifty case)
                        if not data:
                            logger.error(f"Empty spot data received for {self.config.symbol}")
                            return []
                        # Handle nested instrument key format (Nifty case)
                        elif isinstance(data, dict) and len(data) == 1:
                            # Extract the instrument data
                            instrument_key = list(data.keys())[0]
                            instrument_data = data[instrument_key]
                            logger.warning(f"Found instrument data: {instrument_key} -> {instrument_data}")
                            if "last_price" in instrument_data:
                                spot_price = float(instrument_data["last_price"])
                                logger.info(f"Successfully extracted spot price: {spot_price}")
                            elif "ltp" in instrument_data:
                                spot_price = float(instrument_data["ltp"])
                                logger.info(f"Successfully extracted spot price (ltp): {spot_price}")
                            else:
                                logger.error(f"No last_price or ltp in instrument data: {instrument_data}")
                                return []
                        # Handle direct ltp format
                        elif "ltp" in data:
                            spot_price = float(data["ltp"])
                            logger.info(f"Successfully extracted spot price (direct): {spot_price}")
                        else:
                            logger.error(f"Unexpected spot data format: {spot_data}")
                            return []
                    else:
                        logger.error(f"Invalid spot data response: {spot_data}")
                        return []
                except Exception as json_error:
                    logger.error(f"Failed to parse spot price JSON: {json_error}")
                    return []
            
            # Get option chain to find active strikes
            if self.config.symbol.upper() == "BANKNIFTY":
                # Use BankNifty instrument key for option chain
                chain_url = f"https://api.upstox.com/v2/option/chain?instrument_key=NSE_INDEX|Bank Nifty"
            else:
                # Use Nifty instrument key for option chain
                chain_url = f"https://api.upstox.com/v2/option/chain?instrument_key={self.config.spot_instrument_key}"
                spot_instrument_key = self.config.spot_instrument_key
            async with httpx.AsyncClient() as client:
                spot_response = await client.get(spot_url, headers=headers)
                if spot_response.status_code == 401:
                    logger.error("Upstox token revoked or expired (spot price)")
                    self.token_manager.invalidate("Upstox token revoked or expired")
                    raise HTTPException(
                        status_code=401,
                        detail="Upstox authentication required"
                    )
                elif spot_response.status_code != 200:
                    logger.error(f"Failed to get spot price: {spot_response.status_code} - {spot_response.text}")
                    return []
                
                try:
                    spot_data = spot_response.json()
                    # Handle different response formats
                    if "data" in spot_data:
                        if "ltp" in spot_data["data"]:
                            spot_price = float(spot_data["data"]["ltp"])
                        else:
                            logger.error(f"Unexpected spot data format: {spot_data}")
                            return []
                    else:
                        logger.error(f"Invalid spot data response: {spot_data}")
                        return []
                except Exception as json_error:
                    logger.error(f"Failed to parse spot price JSON: {json_error}")
                    return []
            
            # Get option chain to find active strikes
            if self.config.symbol.upper() == "BANKNIFTY":
                # Use BankNifty instrument key for option chain
                chain_url = f"https://api.upstox.com/v2/option/chain?instrument_key=NSE_INDEX|Bank Nifty"
            else:
                # Use Nifty instrument key for option chain
                chain_url = f"https://api.upstox.com/v2/option/chain?instrument_key=NSE_INDEX|Nifty 50"
            
            chain_response = await client.get(chain_url, headers=headers)
            
            if chain_response.status_code == 401:
                logger.error("Upstox token revoked or expired (option chain)")
                self.token_manager.invalidate("Upstox token revoked or expired")
                raise HTTPException(
                    status_code=401,
                    detail="Upstox authentication required"
                )
            elif chain_response.status_code != 200:
                logger.error(f"Failed to get option chain: {chain_response.status_code} - {chain_response.text}")
                return []
            
            try:
                chain_data = chain_response.json()
            except Exception as json_error:
                logger.error(f"Failed to parse option chain JSON: {json_error}")
                return []
            
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
            if self.config.symbol.upper() == "BANKNIFTY":
                # For BankNifty, we need to get BankNifty spot price
                banknifty_url = f"https://api.upstox.com/v3/market-quote/ltp?instrument_key=NSE_INDEX|Bank Nifty"
                async with httpx.AsyncClient() as client:
                    banknifty_response = await client.get(banknifty_url, headers=headers)
                    if banknifty_response.status_code == 401:
                        logger.error("Upstox token revoked or expired (BankNifty spot price)")
                        self.token_manager.invalidate("Upstox token revoked or expired")
                        raise HTTPException(
                            status_code=401,
                            detail="Upstox authentication required"
                        )
                    elif banknifty_response.status_code != 200:
                        logger.error(f"Failed to get BankNifty spot price: {banknifty_response.status_code} - {banknifty_response.text}")
                        return []
                    
                    try:
                        banknifty_data = banknifty_response.json()
                        if "data" in banknifty_data and "ltp" in banknifty_data["data"]:
                            banknifty_spot_price = float(banknifty_data["data"]["ltp"])
                        else:
                            logger.error(f"Unexpected BankNifty spot data format: {banknifty_data}")
                            return []
                    except Exception as json_error:
                        logger.error(f"Failed to parse BankNifty spot price JSON: {json_error}")
                        return []
                
                # Use BankNifty spot price for ATM calculation
                spot_price = banknifty_spot_price if 'banknifty_spot_price' in locals() else spot_price
            else:
                # Use Nifty spot price for ATM calculation
                spot_price = spot_price
            
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
            
        except HTTPException:
            # Re-raise HTTPException (401) without modification
            raise
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
                logger.debug(f"Updated market state for {self.config.symbol} - {instrument_key}: LTP={processed_data.get('ltp')}")
                
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
