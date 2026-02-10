"""
Production-Ready API Router
Enhanced main application with all routes integrated
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from contextlib import asynccontextmanager

from .core.config import settings
from .models.database import get_db
from .services.market_dashboard_service import MarketDashboardService
from .api.auth_routes import auth_router
from .api.market_routes import market_router
from .market_data.market_data_manager import get_market_data_manager

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting StrikeIQ API...")
    
    # Initialize market data manager (but don't start it yet)
    try:
        market_data_manager = await get_market_data_manager()
        logger.info("Market data manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize market data manager: {str(e)}")
    
    logger.info("StrikeIQ API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down StrikeIQ API...")
    
    # Stop market data manager
    try:
        market_data_manager = await get_market_data_manager()
        if market_data_manager.is_running:
            await market_data_manager.stop()
            logger.info("Market data manager stopped")
    except Exception as e:
        logger.error(f"Error stopping market data manager: {str(e)}")
    
    logger.info("StrikeIQ API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="StrikeIQ API",
    description="Production-ready options market intelligence platform",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(market_router)

# Legacy endpoints for backward compatibility
@app.get("/api/v1/dashboard/{symbol}")
async def get_dashboard_data(symbol: str, db=Depends(get_db)):
    """Get real-time dashboard data for a symbol (legacy endpoint)"""
    try:
        service = MarketDashboardService(db)
        data = await service.get_dashboard_data(symbol.upper())
        return data
    except Exception as e:
        logger.error(f"Error in dashboard endpoint for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/market-data/{symbol}")
async def get_latest_option_chain(symbol: str, db=Depends(get_db)):
    """Get latest option chain data (legacy endpoint)"""
    try:
        from .market_data import get_latest_option_chain as get_chain
        data = await get_chain(symbol.upper(), db)
        return data
    except Exception as e:
        logger.error(f"Error in market data endpoint for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        market_data_manager = await get_market_data_manager()
        status = market_data_manager.get_status()
        
        return {
            "status": "healthy",
            "market_data": {
                "is_running": status["is_running"],
                "mode": status["mode"],
                "websocket_connected": status["websocket_connected"]
            }
        }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "StrikeIQ API v2.0.0",
        "docs": "/docs",
        "health": "/health",
        "auth": "/api/v1/auth/status",
        "market_data": "/api/v1/market-data/status"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
