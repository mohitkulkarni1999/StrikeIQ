from fastapi import FastAPI, HTTPException, Depends, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import logging
from datetime import datetime
from contextlib import asynccontextmanager
import asyncio
import uvicorn
import os
import sys

from app.core.config import settings
from app.models.database import get_db
from app.services.market_dashboard_service import MarketDashboardService
from app.market_data.market_data_service import get_latest_option_chain
from app.api.v1 import (
    auth_router,
    market_router,
    options_router,
    system_router,
    predictions_router,
    debug_router,
    intelligence_router,
    market_session_router,  # Add market session router
    # RE-ENABLED: WebSocket router for live streaming
    live_ws_router,
)

# Configure logging with file output
import logging
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
import os
os.makedirs("logs", exist_ok=True)

# DEBUG: Log process ID for debugging
logger = logging.getLogger(__name__)
logger.info(f"Process ID: {os.getpid()}")

# Setup file logging
file_handler = RotatingFileHandler(
    "logs/server.log", 
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)

# Setup console logging
console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)

# Configure root logger
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    handlers=[file_handler, console_handler]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting StrikeIQ API...")
    
    # Start market session monitoring
    asyncio.create_task(start_market_session_manager(app))
    
    # RE-ENABLED: Start WebSocket streaming for live market data
    asyncio.create_task(start_market_feed(app))
    
    yield
    
    # Shutdown
    logger.info("Shutting down StrikeIQ API...")
    await stop_market_session_manager(app)
    await stop_data_scheduler(app)


async def start_market_session_manager(app: FastAPI):
    """Start market session monitoring"""
    try:
        from app.services.market_session_manager import get_market_session_manager
        
        logger.info("Starting market session manager...")
        session_manager = await get_market_session_manager()
        
        # Start status monitoring
        await session_manager.start_status_monitoring()
        
        # Store in app state for global access
        app.state.market_session_manager = session_manager
        
        logger.info("✅ Market session manager started")
        
    except Exception as e:
        logger.error(f"❌ Failed to start market session manager: {e}")


async def stop_market_session_manager(app: FastAPI):
    """Stop market session monitoring"""
    try:
        if hasattr(app.state, 'market_session_manager'):
            await app.state.market_session_manager.stop_status_monitoring()
            await app.state.market_session_manager.cleanup()
            logger.info("Market session manager stopped")
        
    except Exception as e:
        logger.error(f"Error stopping market session manager: {e}")


async def start_market_feed(app: FastAPI):
    """Start Upstox V3 WebSocket market feed for live streaming"""
    try:
        from app.services.upstox_market_feed import UpstoxMarketFeed, FeedConfig
        from app.core.live_market_state import MarketStateManager
        
        logger.info("Initializing Upstox V3 WebSocket market feed...")
        
        # Global market state manager
        market_state_manager = MarketStateManager()
        
        # Store market state manager in app state for global access
        app.state.market_state = market_state_manager
        
        # Initialize symbol states before starting feeds to prevent None returns
        symbols = ["NIFTY", "BANKNIFTY"]
        for symbol in symbols:
            await market_state_manager.initialize_symbol(symbol)
        
        # Start feeds for NIFTY and BANKNIFTY
        instrument_keys = {
            "NIFTY": "NSE_INDEX|Nifty 50",
            "BANKNIFTY": "NSE_INDEX|Nifty Bank"
        }
        
        for symbol in symbols:
            try:
                config = FeedConfig(
                    symbol=symbol,
                    spot_instrument_key=instrument_keys[symbol],
                    strike_range=10,
                    mode="full"
                )
                
                feed = UpstoxMarketFeed(config, market_state_manager)
                logger.info(f"Starting Upstox feed for {symbol}...")
                await feed.start()
                
                # Store feed globally for WebSocket access
                if not hasattr(app.state, 'upstox_feeds'):
                    app.state.upstox_feeds = {}
                app.state.upstox_feeds[symbol] = feed
                
                logger.info(f"✅ Upstox feed started for {symbol}")
                
            except Exception as e:
                logger.error(f"❌ Failed to start feed for {symbol}: {e}")
                continue
        
        logger.info("🚀 Upstox V3 WebSocket market feed initialization complete")
        
    except Exception as e:
        logger.error(f"❌ Failed to start market feed: {e}")


async def stop_data_scheduler(app: FastAPI):
    """Stop data scheduler and WebSocket feeds"""
    try:
        # Stop WebSocket feeds if they exist
        if hasattr(app.state, 'upstox_feeds'):
            for symbol, feed in app.state.upstox_feeds.items():
                try:
                    await feed.stop()
                    logger.info(f"Stopped Upstox feed for {symbol}")
                except Exception as e:
                    logger.error(f"Error stopping feed for {symbol}: {e}")
        
        logger.info("Data scheduler and feeds stopped")
        
    except Exception as e:
        logger.error(f"Error stopping data scheduler: {e}")


app = FastAPI(
    title="StrikeIQ API",
    description="Options Market Intelligence SaaS for Indian Markets",
    version="2.0.0",
    lifespan=lifespan
)

# Include all v1 routers
app.include_router(auth_router)
app.include_router(market_router)
app.include_router(options_router)
app.include_router(system_router)
app.include_router(predictions_router)
app.include_router(debug_router)
app.include_router(intelligence_router)
app.include_router(market_session_router)  # Add market session router
# RE-ENABLED: WebSocket router for live streaming
app.include_router(live_ws_router)

# CORS middleware - Fixed for WebSocket support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "ws://localhost:3000", "http://localhost:8000", "ws://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔍 GLOBAL HTTP REQUEST LOGGER FOR AUDIT
@app.middleware("http")
async def log_all_http_requests(request, call_next):
    print(f"🌐 REST HIT: {request.url.path}")
    print(f"🌐 REST METHOD: {request.method}")
    print(f"🌐 REST TIMESTAMP: {datetime.now().isoformat()}")
    
    response = await call_next(request)
    
    print(f"🌐 REST STATUS: {response.status_code}")
    print(f"🌐 REST COMPLETED: {request.url.path}")
    
    return response
logger.info("=== REGISTERED ROUTES ===")
for route in app.routes:
    if hasattr(route, 'path'):
        route_type = getattr(route, 'methods', 'N/A')
        logger.info(f"Route: {route.path} | Methods: {route_type} | Type: {type(route).__name__}")
        
logger.info("=== END ROUTES ===")


@app.get("/")
async def root():
    return {"message": "StrikeIQ API is running", "version": "2.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/dashboard/{symbol}")
async def get_dashboard_data(symbol: str, db: Depends = Depends(get_db)):
    """Get real-time dashboard data for a symbol"""
    try:
        service = MarketDashboardService(db)
        data = await service.get_dashboard_data(symbol.upper())
        return data
    except Exception as e:
        logger.error(f"Error in dashboard endpoint for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/market-data/{symbol}")
async def get_market_data(symbol: str):
    """Get latest option chain data for symbol"""
    try:
        data = await get_latest_option_chain(symbol.upper())
        return {
            "status": "success",
            "data": data
        }
    except ValueError as e:
        logger.error(f"Invalid symbol {symbol}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching market data for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch market data")


@app.get("/api/v1/auth/upstox")
async def get_upstox_auth_url():
    """Get Upstox OAuth authorization URL"""
    try:
        from app.services.upstox_auth_service import get_upstox_auth_service
        auth_service = get_upstox_auth_service()
        auth_url = auth_service.get_authorization_url()
        return {"authorization_url": auth_url}
    except Exception as e:
        logger.error(f"Error generating auth URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate authorization URL")


@app.get("/api/v1/auth/upstox/callback")
async def upstox_auth_callback(code: str = Query(None)):
    """Handle Upstox OAuth callback"""
    try:
        from app.services.upstox_auth_service import get_upstox_auth_service
        auth_service = get_upstox_auth_service()
        
        # Debug logging
        logger.info(f"Received callback with code: {code}")
        
        if not code:
            logger.error("No authorization code received")
            raise ValueError("Authorization code is required")
        
        token_data = auth_service.exchange_code_for_token(code)
        
        # Redirect to frontend success page
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="http://localhost:3000/auth/success?status=success")
    except ValueError as e:
        logger.error(f"Invalid callback parameters: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in auth callback: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication failed")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,  # Changed port from 8000 to 8001
        reload=True
    )
