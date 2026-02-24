from __future__ import annotations
import functools
import logging
from typing import Optional, Dict, Any, Union, Callable, TypeVar, cast
from app.services.token_manager import token_manager

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])

def retry_on_upstox_401(func: F) -> F:
    """
    Decorator to wrap any Upstox request and retry once on 401 Unauthorized
    after refreshing the token.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        # First attempt
        response = await func(*args, **kwargs)
        
        # Check if response is 401
        # This handles httpx.Response, or any object with status_code
        status_code = getattr(response, "status_code", None)
        
        if status_code == 401:
            logger.warning(f"Upstox 401 detected in {func.__name__}. Attempting token refresh...")
            
            # Refresh token via TokenManager (which uses UpstoxAuthService)
            new_token = await token_manager.refresh_access_token()
            
            if new_token:
                logger.info(f"Token refreshed successfully. Retrying {func.__name__}...")
                
                # If the function uses a token from headers, we might need to update headers
                # We try to inject the new token into headers if they exist in kwargs
                if 'headers' in kwargs and isinstance(kwargs['headers'], dict):
                    if 'Authorization' in kwargs['headers']:
                        kwargs['headers']['Authorization'] = f"Bearer {new_token}"
                
                # If the function takes access_token or token as a keyword argument
                if 'access_token' in kwargs:
                    kwargs['access_token'] = new_token
                if 'token' in kwargs:
                    kwargs['token'] = new_token
                
                # Retry
                return await func(*args, **kwargs)
            else:
                logger.error(f"Token refresh failed after 401 in {func.__name__}")
                token_manager.invalidate("Upstox 401 - Refresh failed")
        
        return response
    
    return cast(F, wrapper)
