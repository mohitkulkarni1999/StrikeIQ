"""
Production-Grade Auth Status API
Provides server-side authentication status checking with proper token validation
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from ...services.token_manager import token_manager
from ...services.upstox_auth_service import get_upstox_auth_service

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
logger = logging.getLogger(__name__)

@router.get("/status", response_model=Dict[str, Any])
async def get_auth_status() -> Dict[str, Any]:
    """
    Production-grade authentication status check
    Validates actual token by calling get_valid_token()
    """
    try:
        # Attempt to get a valid token - this validates authentication
        await token_manager.get_valid_token()
        
        # If we get here, token is valid
        return {
            "authenticated": True,
            "login_url": None
        }
            
    except HTTPException as e:
        if e.status_code == 401:
            # Authentication failed - return login URL
            auth_service = get_upstox_auth_service()
            login_url = auth_service.get_authorization_url()
            
            return {
                "authenticated": False,
                "login_url": login_url
            }
        else:
            # Re-raise non-auth HTTP exceptions
            raise
            
    except Exception as e:
        logger.error(f"Auth status check failed: {str(e)}")
        
        # Treat any unexpected error as authentication failure
        auth_service = get_upstox_auth_service()
        login_url = auth_service.get_authorization_url()
        
        return {
            "authenticated": False,
            "login_url": login_url
        }
