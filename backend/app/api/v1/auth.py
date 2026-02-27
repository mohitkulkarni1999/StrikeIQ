from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from app.services.token_manager import token_manager
from app.services.upstox_auth_service import get_upstox_auth_service
import logging

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
logger = logging.getLogger(__name__)


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