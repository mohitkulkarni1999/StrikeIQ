from fastapi import APIRouter
from typing import Dict, Any
import logging
from datetime import datetime

router = APIRouter(prefix="/api/v1", tags=["system"])
logger = logging.getLogger(__name__)

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "service": "StrikeIQ API"
    }

@router.get("/debug/routes", response_model=Dict[str, Any])
async def debug_routes():
    """Debug endpoint to show all registered routes"""
    try:
        from ...main import app
        
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append({
                    "path": route.path,
                    "methods": getattr(route, 'methods', ['N/A']),
                    "name": getattr(route, 'name', 'N/A')
                })
        
        return {
            "status": "success",
            "data": {
                "total_routes": len(routes),
                "routes": routes
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in debug routes: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
