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
from app.services.market_session_manager import get_market_session_manager, MarketSession, EngineMode, is_live_market
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
        self.is_connected = False  # Add connection flag to prevent multiple connections
        self.session_manager = None  # Will be set in start method
        
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
        # Prevent multiple connections
        if self.is_connected:
            logger.warning(f"Already connected to {self.config.symbol}, skipping connection attempt")
            return True
        
        try:
            # Get authorized URL
            self.authorized_url = await self.get_authorized_websocket_url()
            if not self.authorized_url:
                return False
            
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
                    self.is_connected = True  # Set connection flag
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
        Get cached ATM ± strike range instruments to subscribe to
        NO REST CALLS - Use cached data from market state to prevent re-authorization loops
        FALLBACK TO BOOTSTRAP IF REST CHAIN NOT AVAILABLE
        """
        try:
            # Get current market state from our market state manager
            symbol_state = await self.market_state.get_symbol_state(self.config.symbol)
            if not symbol_state:
                logger.error(f"No market state available for {self.config.symbol}")
                return []
            
            # Use cached spot price from market state (WS preferred, REST fallback)
            current_spot = symbol_state.ws_tick_price if symbol_state.ws_tick_price is not None else symbol_state.rest_spot_price
            if not current_spot:
                logger.error(f"No spot price available for {self.config.symbol}")
                return []
            
            # Use cached option chain from market state
            cached_strikes = list(symbol_state.rest_option_chain.keys()) if symbol_state.rest_option_chain else []
            
            # BOOTSTRAP LOGIC: If no REST chain available, derive ATM from spot price
            if not cached_strikes:
                logger.warning(f"No REST option chain available for {self.config.symbol}, using bootstrap ATM calculation")
                
                # Calculate bootstrap ATM using spot price and standard strike gaps
                strike_gap = 50  # Standard NIFTY/BANKNIFTY strike gap
                bootstrap_atm = round(current_spot / strike_gap) * strike_gap
                
                # Generate bootstrap strike range around bootstrap ATM
                bootstrap_strikes = []
                for i in range(-self.config.strike_range, self.config.strike_range + 1):
                    strike = bootstrap_atm + (i * strike_gap)
                    if strike > 0:  # Only positive strikes
                        bootstrap_strikes.append(strike)
                
                # Convert to instrument keys
                instrument_keys = [self.config.spot_instrument_key]  # Add spot
                
                # Add bootstrap option strikes
                for strike in bootstrap_strikes:
                    instrument_keys.append(f"NFO_FO|{strike}-CE")
                    instrument_keys.append(f"NFO_FO|{strike}-PE")
                
                logger.info(f"Using {len(instrument_keys)} bootstrap instruments for {self.config.symbol} (ATM: {bootstrap_atm})")
                return instrument_keys
            
            # NORMAL PATH: REST chain available, use cached data
            # Find ATM from cached strikes
            atm_strike = min(cached_strikes, key=lambda x: abs(x - current_spot))
            logger.info(f"Using cached ATM strike: {atm_strike} (spot: {current_spot})")
            
            # Get strike range around ATM (ATM ± configured range)
            strike_range = []
            for strike in cached_strikes:
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
                instrument_keys.append(f"NFO_FO|{strike}-CE")
                instrument_keys.append(f"NFO_FO|{strike}-PE")
            
            logger.info(f"Using {len(instrument_keys)} cached instruments for {self.config.symbol} (ATM: {atm_strike})")
            return instrument_keys
            
        except HTTPException:
            # Re-raise HTTPException (401) without modification
            raise
        except Exception as e:
            logger.error(f"Error getting cached active strikes: {e}")
            return []
    
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
                
                # Update market state using WebSocket-specific method
                self.market_state.update_ws_tick_price(self.config.symbol, instrument_key, processed_data)
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
        Start the market feed service with market status integration
        """
        self.session_manager = await get_market_session_manager()
        
        # Register for market status changes
        await self.session_manager.register_status_callback(self._on_market_status_change)
        
        # Check current market status
        current_status = self.session_manager.get_market_status().value
        
        if not is_live_market(current_status):
            logger.info(f"NSE not live ({current_status}), switching to REST snapshot mode")
            self.is_running = False
            return
        
        self.is_running = True
        logger.info(f"Starting Upstox market feed for {self.config.symbol} (Market: {current_status})")
        
        # Run feed loop in background
        asyncio.create_task(self.run_feed_loop())
    
    async def _on_market_status_change(self, status: MarketSession, mode: EngineMode):
        """Handle market status changes"""
        logger.info(f"Market status changed: {status.value} ({mode.value})")
        
        if is_live_market(status.value) and mode == EngineMode.LIVE:
            # Market opened - start WebSocket feed
            if not self.is_running:
                logger.info("Market opened - starting WebSocket feed")
                self.is_running = True
                asyncio.create_task(self.run_feed_loop())
        else:
            # Market closed/halted - stop WebSocket feed
            if self.is_running:
                logger.info(f"Market {status.value} - stopping WebSocket feed")
                await self.stop()
    
    async def can_start_websocket(self) -> bool:
        """Check if WebSocket feed can be started based on market status"""
        if not self.session_manager:
            self.session_manager = await get_market_session_manager()
        
        current_status = self.session_manager.get_market_status().value
        return is_live_market(current_status) and self.session_manager.get_engine_mode() == EngineMode.LIVE
    
    async def resync_subscriptions(self) -> None:
        """
        Resync WebSocket subscriptions when REST option chain becomes available
        """
        try:
            logger.info(f"Resyncing subscriptions for {self.config.symbol}")
            
            # Get new instrument list with updated REST chain
            new_instrument_keys = await self.get_active_strikes()
            
            if new_instrument_keys and self.websocket:
                # Send new subscription message
                subscription_message = {
                    "guid": f"strikeiq_resync_{int(datetime.now().timestamp())}",
                    "method": "sub",
                    "data": {
                        "mode": self.config.mode,
                        "instrumentKeys": new_instrument_keys
                    }
                }
                
                message_bytes = json.dumps(subscription_message).encode('utf-8')
                await self.websocket.send(message_bytes)
                logger.info(f"Resubscribed to {len(new_instrument_keys)} instruments for {self.config.symbol}")
            
        except Exception as e:
            logger.error(f"Error resyncing subscriptions: {e}")

    async def stop(self) -> None:
        """
        Stop the market feed service
        """
        self.is_running = False
        self.is_connected = False  # Reset connection flag
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass
        logger.info(f"Stopped Upstox market feed for {self.config.symbol}")
