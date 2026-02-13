from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from ..services.market_data.option_chain_service import OptionChainService
from ..models.database import get_db
from ..core.config import settings
import logging
from datetime import datetime

router = APIRouter(tags=["option-chain"])
logger = logging.getLogger(__name__)

def get_option_chain_service():
    """Dependency injection for OptionChainService"""
    return OptionChainService()

@router.get("/{symbol}", response_model=Dict[str, Any])
async def get_option_chain(
    symbol: str,
    expiry_date: str = None,
    service: OptionChainService = Depends(get_option_chain_service),
    db: Session = Depends(get_db)
):
    """Get option chain for a symbol"""
    try:
        logger.info(f"API request: Option chain for {symbol}, expiry: {expiry_date}")
        
        # Validate symbol
        if symbol.upper() not in ["NIFTY", "BANKNIFTY"]:
            raise HTTPException(status_code=400, detail="Invalid symbol. Must be NIFTY or BANKNIFTY")
        
        # Get option chain data
        chain_data = await service.get_option_chain(symbol, expiry_date)
        
        if "error" in chain_data:
            raise HTTPException(status_code=500, detail=chain_data["error"])
        
        return {
            "status": "success",
            "data": chain_data,
            "symbol": symbol.upper(),
            "expiry_date": expiry_date,
            "timestamp": chain_data[0]["timestamp"] if chain_data else None,
            "total_strikes": len(chain_data)
        }
        
    except Exception as e:
        logger.error(f"Error in option chain API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}/oi-analysis", response_model=Dict[str, Any])
async def get_oi_analysis(
    symbol: str,
    service: OptionChainService = Depends(get_option_chain_service),
    db: Session = Depends(get_db)
):
    """Get OI analysis for a symbol"""
    try:
        logger.info(f"API request: OI analysis for {symbol}")
        
        # Validate symbol
        if symbol.upper() not in ["NIFTY", "BANKNIFTY"]:
            raise HTTPException(status_code=400, detail="Invalid symbol. Must be NIFTY or BANKNIFTY")
        
        # Get OI analysis
        analysis = await service.get_oi_analysis(symbol)
        
        if "error" in analysis:
            raise HTTPException(status_code=500, detail=analysis["error"])
        
        return {
            "status": "success",
            "data": analysis,
            "symbol": symbol.upper(),
            "timestamp": analysis.get("timestamp"),
            "total_strikes": analysis.get("total_strikes", 0)
        }
        
    except Exception as e:
        logger.error(f"Error in OI analysis API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}/greeks", response_model=Dict[str, Any])
async def get_greeks(
    symbol: str,
    strike: float,
    option_type: str,
    expiry_date: str = None,
    service: OptionChainService = Depends(get_option_chain_service),
    db: Session = Depends(get_db)
):
    """Get Greeks for specific option"""
    try:
        logger.info(f"API request: Greeks for {symbol} {strike} {option_type}")
        
        # Validate symbol
        if symbol.upper() not in ["NIFTY", "BANKNIFTY"]:
            raise HTTPException(status_code=400, detail="Invalid symbol. Must be NIFTY or BANKNIFTY")
        
        # Validate option type
        if option_type.upper() not in ["CE", "PE"]:
            raise HTTPException(status_code=400, detail="Invalid option type. Must be CE or PE")
        
        # Get option chain to find specific strike
        chain_data = await service.get_option_chain(symbol, expiry_date)
        
        if "error" in chain_data:
            raise HTTPException(status_code=500, detail=chain_data["error"])
        
        # Find the specific option
        target_option = None
        for item in chain_data:
            if (item.get("strike_price") == strike and 
                item.get("option_type") == option_type.upper()):
                target_option = item
                break
        
        if not target_option:
            raise HTTPException(status_code=404, detail=f"Option not found: {strike} {option_type}")
        
        # Extract Greeks if available
        greeks = {
            "delta": target_option.get("delta"),
            "gamma": target_option.get("gamma"),
            "theta": target_option.get("theta"),
            "vega": target_option.get("vega"),
            "implied_volatility": target_option.get("iv")
        }
        
        return {
            "status": "success",
            "data": {
                "strike": strike,
                "option_type": option_type,
                "greeks": greeks,
                "ltp": target_option.get("ltp"),
                "oi": target_option.get("oi"),
                "volume": target_option.get("volume")
            },
            "symbol": symbol.upper(),
            "expiry_date": expiry_date,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in Greeks API: {e}")
        raise HTTPException(status_code=500, detail=str(e))
