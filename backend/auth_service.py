"""
Authentication Service with Full Debug Logging
Handles token validation and expiration with trace tracking
"""

import jwt
import datetime
from typing import Optional, Dict, Any
from core.logger import auth_logger, get_trace_id

class AuthService:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.validation_count = 0
        self.expiration_count = 0
        self.missing_token_count = 0
        
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token with comprehensive logging"""
        try:
            auth_logger.info(f"AUTH TOKEN VALIDATION START trace={get_trace_id()}")
            
            if not token:
                self.missing_token_count += 1
                auth_logger.warning(f"AUTH TOKEN MISSING trace={get_trace_id()} total_missing={self.missing_token_count}")
                return None
            
            # Remove "Bearer " prefix if present
            if token.startswith("Bearer "):
                token = token[7:]
            
            # Decode JWT token
            try:
                payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
                self.validation_count += 1
                
                # Check token expiration
                exp_timestamp = payload.get('exp')
                if exp_timestamp:
                    exp_datetime = datetime.datetime.fromtimestamp(exp_timestamp)
                    now = datetime.datetime.now()
                    
                    if now > exp_datetime:
                        self.expiration_count += 1
                        auth_logger.warning(f"AUTH TOKEN EXPIRED trace={get_trace_id()} exp={exp_datetime.isoformat()} now={now.isoformat()} total_expired={self.expiration_count}")
                        return None
                    else:
                        auth_logger.info(f"AUTH TOKEN VALID trace={get_trace_id()} expires={exp_datetime.isoformat()} total_valid={self.validation_count}")
                else:
                    auth_logger.info(f"AUTH TOKEN VALID trace={get_trace_id()} no_expiry total_valid={self.validation_count}")
                
                return payload
                
            except jwt.ExpiredSignatureError:
                self.expiration_count += 1
                auth_logger.warning(f"AUTH TOKEN EXPIRED trace={get_trace_id()} total_expired={self.expiration_count}")
                return None
                
            except jwt.InvalidTokenError as e:
                auth_logger.error(f"AUTH TOKEN INVALID trace={get_trace_id()} error={str(e)}")
                return None
                
        except Exception as e:
            auth_logger.error(f"AUTH VALIDATION ERROR trace={get_trace_id()} error={str(e)}")
            return None
    
    async def check_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Check user session status with logging"""
        try:
            auth_logger.info(f"AUTH SESSION CHECK trace={get_trace_id()} user_id={user_id}")
            
            # Mock session check - replace with actual session validation
            session_data = {
                "user_id": user_id,
                "active": True,
                "last_activity": datetime.datetime.now().isoformat(),
                "permissions": ["market_data", "trading"]
            }
            
            auth_logger.info(f"AUTH SESSION VALID trace={get_trace_id()} user_id={user_id}")
            return session_data
            
        except Exception as e:
            auth_logger.error(f"AUTH SESSION ERROR trace={get_trace_id()} user_id={user_id} error={str(e)}")
            return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[str]:
        """Refresh access token with logging"""
        try:
            auth_logger.info(f"AUTH TOKEN REFRESH START trace={get_trace_id()}")
            
            # Mock token refresh - replace with actual refresh logic
            new_token = jwt.encode({
                "user_id": "mock_user",
                "exp": datetime.datetime.now() + datetime.timedelta(hours=1),
                "iat": datetime.datetime.now()
            }, self.secret_key, algorithm="HS256")
            
            auth_logger.info(f"AUTH TOKEN REFRESH SUCCESS trace={get_trace_id()}")
            return new_token
            
        except Exception as e:
            auth_logger.error(f"AUTH TOKEN REFRESH ERROR trace={get_trace_id()} error={str(e)}")
            return None
    
    def get_stats(self) -> Dict[str, int]:
        """Get authentication service statistics"""
        return {
            "validation_count": self.validation_count,
            "expiration_count": self.expiration_count,
            "missing_token_count": self.missing_token_count
        }

# Global auth service instance
auth_service: Optional[AuthService] = None

def init_auth_service(secret_key: str):
    """Initialize authentication service"""
    global auth_service
    auth_service = AuthService(secret_key)
    auth_logger.info("AUTH SERVICE INITIALIZED")

async def validate_token(token: str) -> Optional[Dict[str, Any]]:
    """Global function to validate token"""
    if not auth_service:
        auth_logger.error("AUTH SERVICE NOT INITIALIZED")
        return None
    return await auth_service.validate_token(token)

async def check_user_session(user_id: str) -> Optional[Dict[str, Any]]:
    """Global function to check user session"""
    if not auth_service:
        auth_logger.error("AUTH SERVICE NOT INITIALIZED")
        return None
    return await auth_service.check_user_session(user_id)

def get_auth_stats() -> Dict[str, int]:
    """Get authentication statistics"""
    if not auth_service:
        return {}
    return auth_service.get_stats()
