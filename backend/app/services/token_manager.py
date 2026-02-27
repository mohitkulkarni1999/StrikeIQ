from __future__ import annotations
"""
Production-Grade Async Safe Token Manager
Handles single source of truth for Upstox access token
"""

import asyncio
import time
import logging
import os
from typing import Optional, Dict, Any
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class AuthState:
    AUTHENTICATED = "authenticated"
    AUTH_REQUIRED = "auth_required"


class TokenManager:
    """
    Production-grade async-safe global token manager
    Prevents concurrent refresh and handles permanent invalidation
    """

    def __init__(self):
        self._access_token: Optional[str] = None
        self._expiry_ts: float = 0
        self._auth_state = AuthState.AUTH_REQUIRED
        self._auth_failure_reason: Optional[str] = None
        
        self._lock = asyncio.Lock()

    # ======================================================
    # PUBLIC METHODS ONLY
    # ======================================================

    async def get_valid_token(self) -> str:
        """
        Returns valid access token or raises HTTPException
        Safe for concurrent usage with double-check locking
        """
        # First check outside lock
        if self._auth_state == AuthState.AUTH_REQUIRED:
            raise HTTPException(
                status_code=401,
                detail=self._auth_failure_reason or "Authentication required"
            )

        if self._is_token_valid():
            return self._access_token

        # Acquire lock for refresh
        async with self._lock:
            # Double check after lock acquisition
            if self._auth_state == AuthState.AUTH_REQUIRED:
                raise HTTPException(
                    status_code=401,
                    detail=self._auth_failure_reason or "Authentication required"
                )

            if self._is_token_valid():
                return self._access_token

            # Perform refresh
            return await self._refresh_token_locked()

    async def force_refresh(self) -> str:
        """
        Force token refresh when 401 detected
        """
        async with self._lock:
            if self._auth_state == AuthState.AUTH_REQUIRED:
                raise HTTPException(
                    status_code=401,
                    detail=self._auth_failure_reason or "Authentication required"
                )
            return await self._refresh_token_locked()

    def invalidate_permanently(self, reason: str = "Authentication required"):
        """
        Permanently invalidate authentication state
        Clear all credentials and force manual re-login
        """
        logger.warning(f"Authentication permanently invalidated: {reason}")
        
        self._auth_state = AuthState.AUTH_REQUIRED
        self._auth_failure_reason = reason
        self._access_token = None
        self._expiry_ts = 0
        
        # Clear stored credentials file
        self._clear_stored_credentials()

    def get_auth_state(self) -> Dict[str, Any]:
        """
        Returns current authentication state
        """
        return {
            "state": self._auth_state,
            "failure_reason": self._auth_failure_reason
        }

    async def login(self, access_token: str, expires_in: int):
        """
        Set authenticated state after successful login
        """
        async with self._lock:
            self._set_authenticated_state(access_token, expires_in)

    # ======================================================
    # INTERNAL METHODS ONLY
    # ======================================================

    def _is_token_valid(self) -> bool:
        return (
            self._access_token is not None
            and time.time() < self._expiry_ts - 60  # 60 sec safety buffer
            and self._auth_state == AuthState.AUTHENTICATED
        )

    async def _refresh_token_locked(self) -> str:
        """
        Internal token refresh - must be called within lock
        """
        try:
            logger.info("Refreshing Upstox access token...")

            from .upstox_auth_service import get_upstox_auth_service
            auth_service = get_upstox_auth_service()
            
            token_data = await auth_service.refresh_access_token()

            if not token_data or "access_token" not in token_data:
                raise Exception("Invalid token response from auth service")

            self._set_authenticated_state(token_data["access_token"], token_data.get("expires_in", 3600))

            logger.info("Token refreshed successfully")
            return self._access_token

        except HTTPException as e:
            if e.status_code == 401:
                self.invalidate_permanently("Token refresh failed: Invalid credentials")
            raise
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            self.invalidate_permanently(f"Token refresh failed: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Authentication refresh failed"
            )

    def _clear_stored_credentials(self):
        """
        Clear stored credentials file
        """
        try:
            credentials_file = "upstox_credentials.json"
            if os.path.exists(credentials_file):
                os.remove(credentials_file)
                logger.info("Stored credentials cleared")
        except Exception as e:
            logger.error(f"Failed to clear stored credentials: {e}")

    def _set_authenticated_state(self, access_token: str, expires_in: int):
        """
        Internal method to set authenticated state after successful login
        """
        self._access_token = access_token
        self._expiry_ts = time.time() + expires_in
        self._auth_state = AuthState.AUTHENTICATED
        self._auth_failure_reason = None


# Global singleton instance
token_manager = TokenManager()

def get_token_manager() -> TokenManager:
    return token_manager