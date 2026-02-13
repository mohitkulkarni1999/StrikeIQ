from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from ...services.market_data.market_dashboard_service import MarketDashboardService
from ...models.database import get_db
from ...core.config import settings
import logging
from datetime import datetime

router = APIRouter(prefix="/api/v1/market", tags=["market"])
logger = logging.getLogger(__name__)

def get_market_service():
    """Dependency injection for MarketDashboardService"""
    return MarketDashboardService(get_db())

@router.get("/ltp/{symbol}", response_model=Dict[str, Any])
async def get_ltp(
    symbol: str,
    service: MarketDashboardService = Depends(get_market_service),
    db: Session = Depends(get_db)
):
    """Get LTP for a symbol"""
    try:
        logger.info(f"API request: LTP for {symbol}")
        
        # Validate symbol
        if symbol.upper() not in ["NIFTY", "BANKNIFTY"]:
            raise HTTPException(status_code=400, detail="Invalid symbol. Must be NIFTY or BANKNIFTY")
        
        # Get market data
        data = await service.get_dashboard_data(symbol.upper())
        
        return {
            "status": "success",
            "data": {
                "symbol": symbol.upper(),
                "spot_price": data.spot_price,
                "market_status": data.market_status.value if data.market_status else None,
                "timestamp": data.timestamp.isoformat() if data.timestamp else None,
                "session_type": data.session_type.value if data.session_type else None
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in LTP API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=Dict[str, Any])
async def get_market_status(
    service: MarketDashboardService = Depends(get_market_service),
    db: Session = Depends(get_db)
):
    """Get overall market status"""
    try:
        logger.info("API request: Market status")
        
        # Get market status using the service's internal method
        from ...services.market_data.market_dashboard_service import MarketStatus
        
        # Check current market status
        status = service._get_market_status()
        
        return {
            "status": "success",
            "data": {
                "market_status": status.value,
                "timestamp": datetime.now().isoformat(),
                "description": "Market is currently " + status.value.lower()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in market status API: {e}")
        raise HTTPException(status_code=500, detail=str(e))
