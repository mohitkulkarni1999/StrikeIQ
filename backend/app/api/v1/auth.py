from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from app.services.token_manager import token_manager
from app.services.upstox_auth_service import get_upstox_auth_service
import logging

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
logger = logging.getLogger(__name__)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.get("/status")
async def auth_status():
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


@router.get("/upstox")
def login():

    auth_service = get_upstox_auth_service()
    auth_url = auth_service.get_authorization_url()

    return RedirectResponse(auth_url)


@router.get("/upstox/callback")
async def callback(code: str = Query(None)):
    auth_service = get_upstox_auth_service()

    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing")

    try:
        logger.info("Exchanging authorization code...")
        token_data = await auth_service.exchange_code_for_token(code)
        
        # Use TokenManager's public login method
        await token_manager.login(
            access_token=token_data["access_token"],
            expires_in=token_data.get("expires_in", 3600)
        )
        
        logger.info("Upstox connected successfully")
    except Exception as e:
        logger.error(f"Token exchange failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    return RedirectResponse(
        url="http://localhost:3000/auth/success?upstox=connected",
        status_code=302
    )


@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    Returns new access token with expiration time
    """
    try:
        # For now, we'll use the token manager's refresh capability
        # In a full implementation, we'd validate the refresh_token parameter
        logger.info("Token refresh request received")
        
        # Force refresh the token using token manager
        new_access_token = await token_manager.force_refresh()
        
        # Calculate expires_in (default to 1 hour from now)
        expires_in = 3600
        
        logger.info("Token refreshed successfully")
        
        return {
            "access_token": new_access_token,
            "expires_in": expires_in
        }
        
    except HTTPException as e:
        if e.status_code == 401:
            logger.warning("Token refresh failed: Invalid authentication")
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired refresh token"
            )
        else:
            raise
            
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Token refresh failed"
        )