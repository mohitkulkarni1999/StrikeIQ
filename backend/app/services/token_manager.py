"""
Token Manager - Production-Safe Authentication State Management
Handles global authentication state and provides centralized auth validation
"""

from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class TokenManager:
    """
    Global token state manager for production-safe authentication handling
    """
    
    def __init__(self):
        self.is_valid = True
        self._invalidation_reason = None
    
    def invalidate(self, reason: str = "Authentication required"):
        """
        Mark token as invalid
        """
        self.is_valid = False
        self._invalidation_reason = reason
        logger.warning(f"Token invalidated: {reason}")
    
    def validate(self):
        """
        Mark token as valid (after successful authentication)
        """
        self.is_valid = True
        self._invalidation_reason = None
        logger.info("Token validated - authentication restored")
    
    def check(self):
        """
        Check if token is valid, raise exception if not
        """
        if not self.is_valid:
            raise HTTPException(
                status_code=401,
                detail=self._invalidation_reason or "Authentication required"
            )
    
    def check_auth_service(self, auth_service):
        """
        Check if auth service has valid credentials
        """
        if not auth_service.is_authenticated():
            self.invalidate("No valid credentials available")
            self.check()  # This will raise HTTPException
    
    def get_status(self) -> dict:
        """
        Get current authentication status
        """
        return {
            "is_valid": self.is_valid,
            "reason": self._invalidation_reason
        }

# Global instance
token_manager = TokenManager()

def get_token_manager() -> TokenManager:
    """Get the global token manager instance"""
    return token_manager
