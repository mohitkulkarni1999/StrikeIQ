"""
NSE Market Session Manager
Handles market status polling and engine mode switching
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum
import httpx
from .upstox_auth_service import get_upstox_auth_service
from .token_manager import get_token_manager
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class MarketSession(Enum):
    """NSE market session states"""
    OPEN = "OPEN"
    PRE_OPEN = "PRE_OPEN"
    OPENING_END = "OPENING_END"
    CLOSING = "CLOSING"
    CLOSING_END = "CLOSING_END"
    CLOSED = "CLOSED"
    HALTED = "HALTED"
    UNKNOWN = "UNKNOWN"

class EngineMode(Enum):
    """Engine operation modes"""
    LIVE = "LIVE"
    SNAPSHOT = "SNAPSHOT"
    HALTED = "HALTED"
    OFFLINE = "OFFLINE"

class MarketSessionManager:
    """
    Manages market session status and coordinates engine behavior
    """
    
    _instance: Optional['MarketSessionManager'] = None
    _instance_lock = asyncio.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        
        self.auth_service = get_upstox_auth_service()
        self.token_manager = get_token_manager()
        self.client = httpx.AsyncClient(timeout=10.0)
        
        # Market status state
        self.current_status = MarketSession.UNKNOWN
        self.current_engine_mode = EngineMode.OFFLINE
        self.last_status_check = None
        self.status_poll_interval = 60  # seconds
        
        # Polling control
        self._polling_task = None
        self._is_polling = False
        
        # Status change callbacks
        self._status_callbacks = []
        
        self._initialized = True
        logger.info("MarketSessionManager initialized")
    
    async def start_status_monitoring(self):
        """Start continuous market status monitoring"""
        if self._is_polling:
            logger.warning("Status monitoring already running")
            return
        
        self._is_polling = True
        self._polling_task = asyncio.create_task(self._poll_market_status())
        logger.info("Market status monitoring started")
    
    async def stop_status_monitoring(self):
        """Stop market status monitoring"""
        self._is_polling = False
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
        logger.info("Market status monitoring stopped")
    
    async def _poll_market_status(self):
        """Continuous market status polling"""
        while self._is_polling:
            try:
                await self.update_market_status()
                await asyncio.sleep(self.status_poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in market status polling: {e}")
                await asyncio.sleep(10)  # Short retry on error
    
    async def update_market_status(self) -> MarketSession:
        """Fetch and update market status from Upstox API"""
        try:
            # Get valid access token
            token = await self.auth_service.get_valid_access_token()
            if not token:
                logger.error("No access token available for market status")
                await self._set_status(MarketSession.UNKNOWN, EngineMode.OFFLINE)
                return MarketSession.UNKNOWN
            
            # Call Upstox market status API
            response = await self.client.get(
                "https://api.upstox.com/v2/market/status/NSE",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 401:
                logger.error("Token expired fetching market status")
                self.token_manager.invalidate("Market status token expired")
                await self._set_status(MarketSession.UNKNOWN, EngineMode.OFFLINE)
                return MarketSession.UNKNOWN
            elif response.status_code != 200:
                logger.error(f"Market status API error: {response.status_code}")
                await self._set_status(MarketSession.UNKNOWN, EngineMode.OFFLINE)
                return MarketSession.UNKNOWN
            
            data = response.json()
            status_str = data.get("status", "UNKNOWN").upper()
            
            # Map Upstox status to our enum
            if status_str == "OPEN":
                new_status = MarketSession.OPEN
                new_mode = EngineMode.LIVE
            elif status_str == "PRE_OPEN":
                new_status = MarketSession.PRE_OPEN
                new_mode = EngineMode.SNAPSHOT
            elif status_str == "OPENING_END":
                new_status = MarketSession.OPENING_END
                new_mode = EngineMode.SNAPSHOT
            elif status_str == "CLOSING":
                new_status = MarketSession.CLOSING
                new_mode = EngineMode.SNAPSHOT
            elif status_str == "CLOSING_END":
                new_status = MarketSession.CLOSING_END
                new_mode = EngineMode.SNAPSHOT
            elif status_str == "CLOSED":
                new_status = MarketSession.CLOSED
                new_mode = EngineMode.SNAPSHOT
            elif status_str == "HALTED":
                new_status = MarketSession.HALTED
                new_mode = EngineMode.HALTED
            else:
                new_status = MarketSession.UNKNOWN
                new_mode = EngineMode.OFFLINE
            
            await self._set_status(new_status, new_mode)
            logger.info(f"Market status updated: {new_status.value} ({new_mode.value})")
            return new_status
            
        except Exception as e:
            logger.error(f"Error fetching market status: {e}")
            await self._set_status(MarketSession.UNKNOWN, EngineMode.OFFLINE)
            return MarketSession.UNKNOWN
    
    async def _set_status(self, status: MarketSession, mode: EngineMode):
        """Set market status and trigger callbacks if changed"""
        status_changed = (self.current_status != status)
        mode_changed = (self.current_engine_mode != mode)
        
        self.current_status = status
        self.current_engine_mode = mode
        self.last_status_check = datetime.now(timezone.utc)
        
        if status_changed or mode_changed:
            logger.info(f"Market status changed: {status.value} ({mode.value})")
            await self._notify_status_change(status, mode)
    
    async def _notify_status_change(self, status: MarketSession, mode: EngineMode):
        """Notify all registered callbacks of status change"""
        for callback in self._status_callbacks:
            try:
                await callback(status, mode)
            except Exception as e:
                logger.error(f"Error in status callback: {e}")
    
    def register_status_callback(self, callback):
        """Register a callback for status changes"""
        self._status_callbacks.append(callback)
    
    def unregister_status_callback(self, callback):
        """Unregister a status change callback"""
        if callback in self._status_callbacks:
            self._status_callbacks.remove(callback)
    
    def get_market_status(self) -> MarketSession:
        """Get current market status"""
        return self.current_status
    
    def get_engine_mode(self) -> EngineMode:
        """Get current engine mode"""
        return self.current_engine_mode
    
    def is_market_open(self) -> bool:
        """Check if market is open for live trading"""
        return self.current_status == MarketSession.OPEN
    
    def is_live_mode(self) -> bool:
        """Check if engines should run in live mode"""
        return self.current_engine_mode == EngineMode.LIVE
    
    def is_snapshot_mode(self) -> bool:
        """Check if engines should run in snapshot mode"""
        return self.current_engine_mode == EngineMode.SNAPSHOT
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get comprehensive status information"""
        return {
            "market_status": self.current_status.value,
            "engine_mode": self.current_engine_mode.value,
            "last_check": self.last_status_check.isoformat() if self.last_status_check else None,
            "is_polling": self._is_polling
        }
    
    async def force_status_check(self) -> MarketSession:
        """Force an immediate status check"""
        return await self.update_market_status()
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.stop_status_monitoring()
        await self.client.aclose()
        logger.info("MarketSessionManager cleaned up")

# Global instance
market_session_manager = MarketSessionManager()

# Convenience functions
async def get_market_session_manager() -> MarketSessionManager:
    """Get the global market session manager instance"""
    return market_session_manager

def get_market_status() -> MarketSession:
    """Get current market status (sync version for quick checks)"""
    return market_session_manager.get_market_status()

def get_engine_mode() -> EngineMode:
    """Get current engine mode (sync version for quick checks)"""
    return market_session_manager.get_engine_mode()

def is_market_open() -> bool:
    """Check if market is open for live trading"""
    return market_session_manager.is_market_open()

def is_live_market(status: str) -> bool:
    """Check if market is in live trading phase (only OPEN)"""
    return status == "OPEN"

def is_snapshot_mode() -> bool:
    """Check if snapshot mode is active (sync version)"""
    return market_session_manager.is_snapshot_mode()

def is_live_mode() -> bool:
    """Check if live mode is active (sync version)"""
    return market_session_manager.is_live_mode()

def get_nse_trading_phase() -> str:
    """Get current NSE trading phase"""
    return market_session_manager.get_market_status().value
