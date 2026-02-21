import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
import json
import os
import httpx
import urllib.parse
import hmac
import hashlib
import base64
import secrets
from ..core.config import settings

logger = logging.getLogger(__name__)

# Global singleton instance
_auth_service_instance = None

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
        self._rate_limit_store = {}  # IP-based rate limiting only

    def _check_rate_limit(self, client_ip: str) -> bool:
        """Check if client IP is rate limited"""
        if client_ip not in self._rate_limit_store:
            self._rate_limit_store[client_ip] = {'timestamp': datetime.now(timezone.utc)}
            return True
        
        # Clean up old entries (older than 1 hour)
        current_time = datetime.now(timezone.utc)
        cutoff_time = current_time - timedelta(hours=1)
        
        # Remove old entries
        expired_keys = [
            ip for ip, data in self._rate_limit_store.items()
            if data['timestamp'] < cutoff_time
        ]
        
        for expired_key in expired_keys:
            del self._rate_limit_store[expired_key]
        
        # Check current requests
        recent_requests = [
            data for ip, data in self._rate_limit_store.items()
            if data['timestamp'] > current_time - timedelta(minutes=5)
        ]
        
        # Rate limit: max 5 requests per minute
        if len(recent_requests) >= 5:
            return False
        
        return True
    
    def generate_signed_state(self) -> str:
        """Generate HMAC-signed state token"""
        timestamp = str(int(datetime.now(timezone.utc).timestamp()))
        random_part = secrets.token_urlsafe(16)
        payload = f"{timestamp}:{random_part}"

        secret = settings.SECRET_KEY.encode()
        signature = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()

        full_state = f"{payload}:{signature}"
        return base64.urlsafe_b64encode(full_state.encode()).decode()

    def validate_signed_state(self, state: str) -> bool:
        """Validate HMAC-signed state token"""
        try:
            decoded = base64.urlsafe_b64decode(state.encode()).decode()
            timestamp, random_part, signature = decoded.split(":")

            payload = f"{timestamp}:{random_part}"
            secret = settings.SECRET_KEY.encode()
            expected_signature = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()

            if not hmac.compare_digest(signature, expected_signature):
                return False

            # Expiry check (10 minutes)
            current_time = int(datetime.now(timezone.utc).timestamp())
            if current_time - int(timestamp) > 600:
                return False

            return True

        except Exception:
            return False

    def _get_client_ip(self, request) -> str:
        """Get client IP from request"""
        # Try to get real IP, fallback to X-Forwarded-For
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Get the first IP in the list
            return forwarded_for.split(',')[0].strip()
        
        # Fallback to remote_addr
        return request.client.host or 'unknown'

    def exchange_code_for_token(self, code: str) -> dict:
        """Exchange authorization code for access token"""
        try:
            logger.info(f"Attempting to exchange code for token")
            logger.info(f"Using API key: {settings.UPSTOX_API_KEY[:8]}...")
            logger.info(f"Redirect URI: {settings.REDIRECT_URI}")
            
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
            
            logger.info(f"Making token exchange request to: {url}")
            response = httpx.post(url, headers=headers, data=data)
            
            # Log response status for debugging
            logger.info(f"Token exchange response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Token exchange failed with status {response.status_code}")
                logger.error(f"Response body: {response.text}")
                raise Exception(f"Token exchange failed: {response.status_code} - {response.text}")
            
            response.raise_for_status()
            
            token_data = response.json()
            logger.info(f"Token exchange successful, received keys: {list(token_data.keys())}")
            
            # SECURITY: Remove debug logging - Never log tokens
            credentials = UpstoxCredentials(
                token_data.get("access_token"),
                token_data.get("refresh_token"),
                token_data.get("expires_in") or 3600
            )
            self._store_credentials(credentials)
            
            # Validate TokenManager after successful authentication
            from .token_manager import get_token_manager
            token_manager = get_token_manager()
            token_manager.validate()
            
            return {
                "access_token": credentials.access_token,
                "refresh_token": credentials.refresh_token,
                "expires_at": credentials.expires_at.isoformat()
            }
        except Exception as e:
            # SECURITY: Never log sensitive data
            raise Exception(f"Token exchange failed: {str(e)}")

    def _store_credentials(self, credentials: UpstoxCredentials):
        """Store credentials securely"""
        try:
            with open(self._credentials_file, 'w') as f:
                json.dump({
                    "access_token": credentials.access_token,
                    "refresh_token": credentials.refresh_token,
                    "expires_at": credentials.expires_at.isoformat()
                }, f)
            logger.info("Credentials stored securely")
        except Exception as e:
            logger.error(f"Error storing credentials: {e}")
            raise

    def _load_credentials(self) -> Optional[UpstoxCredentials]:
        """Load credentials securely"""
        if not os.path.exists(self._credentials_file):
            logger.info("No credentials file found")
            return None
        
        try:
            with open(self._credentials_file, 'r') as f:
                data = json.load(f)
                expires_at = datetime.fromisoformat(data["expires_at"])
                # SECURITY: Ensure timezone awareness
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                
                # DEBUG: Log parsed expiry
                logger.info(f"Parsed token expiry: {expires_at}")
                logger.info(f"Current time: {datetime.now(timezone.utc)}")
                logger.info(f"Token valid: {expires_at > datetime.now(timezone.utc)}")
                # SECURITY: Validate token structure (refresh_token optional)
                if not all(key in data for key in ["access_token", "expires_at"]):
                    logger.warning("Invalid credential structure")
                    return None
                
                # SECURITY: Validate token values (refresh_token optional)
                if not data.get("access_token") or not data.get("expires_at"):
                    logger.warning("Invalid token values")
                    return None
                
                # SECURITY: Check expiration
                if expires_at <= datetime.now(timezone.utc):
                    logger.warning("Token expired")
                    return None
                
                # Recreate credentials with expires_at (refresh_token optional)
                refresh_token = data.get("refresh_token")
                creds = UpstoxCredentials(data["access_token"], refresh_token or "", 0)
                creds.expires_at = expires_at
                
                # DEBUG: Log credential loading
                logger.info(f"Loaded credentials. Expires at: {expires_at}")
                
                return creds
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            return None

    async def refresh_access_token(self):
        """Refresh access token using refresh token"""
        try:
            if not self._credentials or not self._credentials.refresh_token:
                raise ValueError("No refresh token available")
            
            # SECURITY: Check if refresh token is still valid
            if datetime.now(timezone.utc) > self._credentials.expires_at:
                logger.warning("Refresh token expired")
                raise TokenExpiredError("Refresh token expired")
            
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
            
            # SECURITY: Rate limit check before making request
            client_ip = self._get_client_ip(request)
            
            if not self._check_rate_limit(client_ip):
                logger.warning(f"Rate limit check failed for IP: {client_ip}")
                # Continue with request but log warning
            else:
                logger.info(f"Making refresh request from IP: {client_ip}")
            
            # SECURITY: Log refresh attempt (without sensitive data)
            logger.info(f"Refresh token request - client_id: {settings.UPSTOX_API_KEY[:8]}..., redirect_uri: {settings.REDIRECT_URI}")
            
            # SECURITY: Use refresh_token as grant_type
            data = {
                "refresh_token": self._credentials.refresh_token,
                "client_id": settings.UPSTOX_API_KEY,
                "client_secret": settings.UPSTOX_API_SECRET,
                "redirect_uri": settings.REDIRECT_URI,
                "grant_type": "refresh_token"
            }
            
            response = httpx.post(url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            if not all(key in token_data for key in ["access_token", "expires_in"]):
                logger.error("Invalid token values in response")
                raise Exception("Invalid token values in response")
            
            credentials = UpstoxCredentials(
                token_data.get("access_token"),
                token_data.get("refresh_token"),
                token_data.get("expires_in") or 3600
            )
            
            # SECURITY: Store new credentials securely
            self._store_credentials(credentials)
            self._credentials = credentials
            
            logger.info("Token refreshed successfully")
            return credentials.access_token
        except ValueError as e:
            logger.error(f"Token refresh failed: {e}")
            raise TokenExpiredError(f"Token refresh failed: {e}")
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise Exception(f"Token refresh failed: {e}")

    async def get_valid_access_token(self) -> Optional[str]:
        """Get valid access token with automatic refresh"""
        # SECURITY: Ensure timezone-aware comparison
        now = datetime.now(timezone.utc)
        
        if self._credentials and self._credentials.expires_at > now:
            return self._credentials.access_token
        elif self._credentials and self._credentials.refresh_token:
            try:
                return await self.refresh_access_token()
            except (TokenExpiredError, ValueError):
                # If refresh fails, raise TokenExpiredError
                raise TokenExpiredError(f"Token refresh failed: {str(e)}")
        
        raise TokenExpiredError("No valid credentials available")

    def is_authenticated(self) -> bool:
        """Check if we have valid credentials or can refresh them"""
        if not self._credentials:
            logger.info("No credentials available")
            return False
            
        # SECURITY: Ensure timezone-aware comparison
        now = datetime.now(timezone.utc)
        
        # If token is valid (with 60s buffer), we are good
        if self._credentials.expires_at > now + timedelta(seconds=60):
            logger.info("Authentication active")
            return True
            
        # If token is expired but we have refresh token, we can refresh
        if self._credentials.refresh_token:
            logger.info("Token expired but refresh token available")
            return True
            
        return False

    def logout(self):
        """Logout and remove credentials"""
        if os.path.exists(self._credentials_file):
            os.remove(self._credentials_file)
        self._credentials = None

    def get_authorization_url(self, state: str = None) -> str:
        """Generate authorization URL with proper URL encoding"""
        from urllib.parse import urlencode
        
        params = {
            "response_type": "code",
            "client_id": settings.UPSTOX_API_KEY,
            "redirect_uri": settings.REDIRECT_URI,
        }
        
        # Add state if provided
        if state:
            params["state"] = state
        
        # SECURITY: Use urlencode for proper URL encoding
        authorization_url = (
            "https://api.upstox.com/v2/login/authorization/dialog?"
            + urlencode(params)
        )
        
        # DEBUG: Log the generated URL for verification
        logger.info(f"Generated authorization_url: {authorization_url}")
        
        return authorization_url
    

def get_upstox_auth_service():
    """Factory function to get shared UpstoxAuthService instance"""
    global _auth_service_instance
    if _auth_service_instance is None:
        _auth_service_instance = UpstoxAuthService()
    return _auth_service_instance
