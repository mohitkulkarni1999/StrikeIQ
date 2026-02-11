import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import json
import os
import httpx
import urllib.parse
from ..core.config import settings

class TokenExpiredError(Exception):
    """Token has expired"""
    pass

class UpstoxCredentials:
    def __init__(self, access_token: str, refresh_token: str, expires_in: int):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = datetime.now() + timedelta(seconds=expires_in or 3600)

class UpstoxAuthService:
    def __init__(self, credentials_file: str = "upstox_credentials.json"):
        self._credentials_file = credentials_file
        self._credentials = self._load_credentials()

    def exchange_code_for_token(self, code: str) -> dict:
        try:
            url = "https://api.upstox.com/v2/login/authorization/token"
            headers = {
                "accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {
                "code": code,
                "client_id": settings.UPSTOX_API_KEY,
                "client_secret": settings.UPSTOX_API_SECRET,
                "redirect_uri": settings.REDIRECT_URI,
                "grant_type": "authorization_code"
            }
            
            response = httpx.post(url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            print(f"DEBUG: Token response from Upstox: {token_data}")  # Debug logging
            credentials = UpstoxCredentials(
                token_data.get("access_token"),
                token_data.get("refresh_token"),
                token_data.get("expires_in") or 3600
            )
            self._store_credentials(credentials)
            return {
                "access_token": credentials.access_token,
                "refresh_token": credentials.refresh_token,
                "expires_at": credentials.expires_at.isoformat()
            }
        except Exception as e:
            raise Exception(f"Token exchange failed: {str(e)}")

    def _store_credentials(self, credentials: UpstoxCredentials):
        with open(self._credentials_file, 'w') as f:
            json.dump({
                "access_token": credentials.access_token,
                "refresh_token": credentials.refresh_token,
                "expires_at": credentials.expires_at.isoformat()
            }, f)

    def _load_credentials(self) -> Optional[UpstoxCredentials]:
        if os.path.exists(self._credentials_file):
            with open(self._credentials_file, 'r') as f:
                data = json.load(f)
                expires_at = datetime.fromisoformat(data["expires_at"])
                # Recreate credentials with expires_at
                creds = UpstoxCredentials(data["access_token"], data["refresh_token"], 0)
                creds.expires_at = expires_at
                return creds
        return None

    async def refresh_access_token(self):
        """Refresh access token using refresh token"""
        try:
            if not self._credentials or not self._credentials.refresh_token:
                raise ValueError("No refresh token available")

            url = "https://api.upstox.com/v2/login/authorization/token"
            headers = {
                "accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {
                "refresh_token": self._credentials.refresh_token,
                "client_id": settings.UPSTOX_API_KEY,
                "client_secret": settings.UPSTOX_API_SECRET,
                "redirect_uri": settings.REDIRECT_URI,
                "grant_type": "refresh_token"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, data=data)
                response.raise_for_status()
                
                token_data = response.json()
                credentials = UpstoxCredentials(
                    token_data.get("access_token"),
                    token_data.get("refresh_token"),
                    token_data.get("expires_in") or 3600
                )
                
                # Debug logging to see what Upstox returns
                logger.info(f"Upstox token response: expires_in={token_data.get('expires_in')}, access_token_length={len(token_data.get('access_token', ''))}")
                
                self._store_credentials(credentials)
                self._credentials = credentials
                return credentials.access_token
        except Exception as e:
            # logging.error(f"Token refresh failed: {str(e)}")
            raise Exception(f"Token refresh failed: {str(e)}")

    async def get_valid_access_token(self) -> Optional[str]:
        if self._credentials and self._credentials.expires_at > datetime.now():
            return self._credentials.access_token
        elif self._credentials and self._credentials.refresh_token:
            try:
                return await self.refresh_access_token()
            except Exception as e:
                # If refresh fails, raise TokenExpiredError
                raise TokenExpiredError(f"Token refresh failed: {str(e)}")
        raise TokenExpiredError("No valid credentials available")

    def is_authenticated(self) -> bool:
        """Check if we have valid credentials or can refresh them"""
        if not self._credentials:
            return False
            
        # If token is valid (with 60s buffer), we are good
        if self._credentials.expires_at > datetime.now() + timedelta(seconds=60):
            return True
            
        # If token is expired but we have refresh token, we can refresh
        if self._credentials.refresh_token:
            return True
            
        return False

    def logout(self):
        if os.path.exists(self._credentials_file):
            os.remove(self._credentials_file)
        self._credentials = None

    def get_authorization_url(self) -> str:
        client_id = settings.UPSTOX_API_KEY
        redirect_uri = urllib.parse.quote(settings.REDIRECT_URI)
        
        # Generate authorization URL
        auth_url = f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"
        
        return auth_url

def get_upstox_auth_service():
    """Factory function to get UpstoxAuthService instance"""
    return UpstoxAuthService()
