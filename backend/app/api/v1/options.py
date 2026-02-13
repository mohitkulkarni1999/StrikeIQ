from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from ...services.market_data.option_chain_service import OptionChainService
from ...services.market_data.smart_money_engine import SmartMoneyEngine
from ...services.market_data.smart_money_engine_v2 import SmartMoneyEngineV2
from ...services.market_data.performance_tracking_service import PerformanceTrackingService
from ...models.database import get_db
from ...core.config import settings
import logging
from datetime import datetime

router = APIRouter(prefix="/api/v1/options", tags=["options"])
logger = logging.getLogger(__name__)

def get_option_chain_service():
    """Dependency injection for OptionChainService"""
    return OptionChainService()

def get_smart_money_engine():
    """Dependency injection for SmartMoneyEngine"""
    return SmartMoneyEngine()

def get_smart_money_engine_v2():
    """Dependency injection for SmartMoneyEngineV2"""
    return SmartMoneyEngineV2()

def get_performance_tracking_service():
    """Dependency injection for PerformanceTrackingService"""
    return PerformanceTrackingService()

@router.get("/contract/{symbol}", response_model=Dict[str, Any])
async def get_option_contracts(
    symbol: str,
    service: OptionChainService = Depends(get_option_chain_service),
    db: Session = Depends(get_db)
):
    """Get available option contracts/expiries for a symbol"""
    try:
        logger.info(f"API request: Option contracts for {symbol}")
        
        # Validate symbol
        if symbol.upper() not in ["NIFTY", "BANKNIFTY"]:
            raise HTTPException(status_code=400, detail="Invalid symbol. Must be NIFTY or BANKNIFTY")
        
        # Get access token
        from ...services.upstox_auth_service import get_upstox_auth_service
        auth_service = get_upstox_auth_service()
        token = await auth_service.get_valid_access_token()
        
        if not token:
            raise HTTPException(status_code=401, detail="No access token available")
        
        # Get instrument key
        instrument_key = await service._get_instrument_key(symbol)
        
        # Fetch available expiry dates using the correct method
        try:
            # Get all expiries from Upstox
            nearest_expiry = await service._get_nearest_expiry(symbol, token)
            
            # Get all stored expiries for the dropdown
            all_expiries = service._all_expiries.get(symbol, [nearest_expiry])
            
            # DEBUG: Log what we're returning to frontend
            logger.info(f"Returning expiries to frontend for {symbol}: {all_expiries}")
            
            # If no expiries found, return a fallback
            if not all_expiries or len(all_expiries) == 0:
                logger.warning(f"No expiries found for {symbol}, using fallback")
                all_expiries = [nearest_expiry] if nearest_expiry else []
            
            return {
                "status": "success",
                "data": all_expiries,
                "symbol": symbol.upper(),
                "timestamp": datetime.now().isoformat(),
                "total_expiries": len(all_expiries)
            }
        except Exception as e:
            logger.error(f"Error fetching expiry dates: {e}")
            # Return a proper error response instead of 500
            return {
                "status": "error",
                "error": "Failed to fetch expiry dates",
                "detail": str(e),
                "data": [],
                "total_expiries": 0
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in option contracts API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chain/{symbol}", response_model=Dict[str, Any])
async def get_option_chain(
    symbol: str,
    expiry_date: Optional[str] = Query(None, description="Expiry date (YYYY-MM-DD)"),
    service: OptionChainService = Depends(get_option_chain_service),
    db: Session = Depends(get_db)
):
    """Get option chain for a symbol"""
    try:
        logger.info(f"API request: Option chain for {symbol}, expiry: {expiry_date}")
        
        # Validate symbol
        if symbol.upper() not in ["NIFTY", "BANKNIFTY"]:
            raise HTTPException(status_code=400, detail="Invalid symbol. Must be NIFTY or BANKNIFTY")
        
        # Validate expiry_date parameter
        if not expiry_date:
            raise HTTPException(status_code=400, detail="Expiry date is required")
        
        # Get option chain data
        chain_data = await service.get_option_chain(symbol, expiry_date)
        
        if "error" in chain_data:
            raise HTTPException(status_code=500, detail=chain_data["error"])
        
        # Add total_strikes and log final response
        chain_data["total_strikes"] = len(chain_data.get("calls", []))
        logger.info(f"Final option chain response: {chain_data}")
        
        return {
            "status": "success",
            "data": chain_data
        }
        
    except Exception as e:
        logger.error(f"Error in option chain API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/oi-analysis/{symbol}", response_model=Dict[str, Any])
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

@router.get("/greeks/{symbol}", response_model=Dict[str, Any])
async def get_greeks(
    symbol: str,
    strike: float = Query(..., description="Strike price"),
    option_type: str = Query(..., description="Option type: CE or PE"),
    expiry_date: Optional[str] = Query(None, description="Expiry date (YYYY-MM-DD)"),
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
        
        # Find specific option
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

@router.get("/smart-money/{symbol}", response_model=Dict[str, Any])
async def get_smart_money_signal(
    symbol: str,
    engine: SmartMoneyEngine = Depends(get_smart_money_engine),
    db: Session = Depends(get_db)
):
    """Get smart money directional bias signal for a symbol"""
    try:
        logger.info(f"API request: Smart money signal for {symbol}")
        
        # Validate symbol
        if symbol.upper() not in ["NIFTY", "BANKNIFTY"]:
            raise HTTPException(status_code=400, detail="Invalid symbol. Must be NIFTY or BANKNIFTY")
        
        # Generate smart money signal
        signal = await engine.generate_smart_money_signal(symbol, db)
        
        return {
            "status": "success",
            "data": signal,
            "timestamp": datetime.now().isoformat()
        }
        
    except ValueError as e:
        logger.error(f"Validation error in smart money API: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in smart money API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/smart-money-v2/{symbol}", response_model=Dict[str, Any])
async def get_smart_money_signal_v2(
    symbol: str,
    engine: SmartMoneyEngineV2 = Depends(get_smart_money_engine_v2),
    db: Session = Depends(get_db)
):
    """Get smart money directional bias signal v2 (statistically stable)"""
    try:
        logger.info(f"API request: Smart money v2 signal for {symbol}")
        
        # Validate symbol
        if symbol.upper() not in ["NIFTY", "BANKNIFTY"]:
            raise HTTPException(status_code=400, detail="Invalid symbol. Must be NIFTY or BANKNIFTY")
        
        # Generate smart money signal with v2 engine
        signal = await engine.generate_smart_money_signal(symbol, db)
        
        return {
            "status": "success",
            "data": signal,
            "timestamp": datetime.now().isoformat()
        }
        
    except ValueError as e:
        logger.error(f"Validation error in smart money v2 API: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in smart money v2 API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/smart-money/performance/{symbol}", response_model=Dict[str, Any])
async def get_smart_money_performance(
    symbol: str,
    days: int = Query(30, ge=1, le=365, description="Number of days for performance analysis"),
    service: PerformanceTrackingService = Depends(get_performance_tracking_service),
    db: Session = Depends(get_db)
):
    """Get smart money performance metrics for a symbol"""
    try:
        logger.info(f"API request: Smart money performance for {symbol}, days: {days}")
        
        # Validate symbol
        if symbol.upper() not in ["NIFTY", "BANKNIFTY"]:
            raise HTTPException(status_code=400, detail="Invalid symbol. Must be NIFTY or BANKNIFTY")
        
        # Get performance metrics
        performance = await service.get_performance_metrics(symbol, db, days)
        
        return {
            "status": "success",
            "data": performance,
            "timestamp": datetime.now().isoformat()
        }
        
    except ValueError as e:
        logger.error(f"Validation error in performance API: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in performance API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/smart-money/update-results/{symbol}", response_model=Dict[str, Any])
async def update_smart_money_results(
    symbol: str,
    lookback_minutes: int = Query(30, ge=5, le=120, description="Lookback period in minutes"),
    service: PerformanceTrackingService = Depends(get_performance_tracking_service),
    db: Session = Depends(get_db)
):
    """Update smart money prediction results based on actual market moves"""
    try:
        logger.info(f"API request: Update smart money results for {symbol}, lookback: {lookback_minutes}")
        
        # Validate symbol
        if symbol.upper() not in ["NIFTY", "BANKNIFTY"]:
            raise HTTPException(status_code=400, detail="Invalid symbol. Must be NIFTY or BANKNIFTY")
        
        # Update prediction results
        result = await service.update_prediction_results(symbol, db, lookback_minutes)
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except ValueError as e:
        logger.error(f"Validation error in update results API: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in update results API: {e}")
        raise HTTPException(status_code=500, detail=str(e))
