"""
Auth Status API
Provides server-side authentication status checking
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from ...services.upstox_auth_service import get_upstox_auth_service

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
logger = logging.getLogger(__name__)

@router.get("/status", response_model=Dict[str, Any])
async def get_auth_status() -> Dict[str, Any]:
    """
    Check authentication status server-side
    """
    try:
        auth_service = get_upstox_auth_service()
        
        # Check if we have valid credentials
        is_authenticated = auth_service.is_authenticated()
        
        return {
            "authenticated": is_authenticated
        }
        
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
        return {
            "authenticated": False
        }
