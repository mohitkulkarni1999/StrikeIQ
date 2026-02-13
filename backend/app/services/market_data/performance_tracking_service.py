import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from ...models.market_data import SmartMoneyPrediction, MarketSnapshot

logger = logging.getLogger(__name__)

class PerformanceTrackingService:
    """Service for tracking and analyzing SmartMoneyEngine performance"""
    
    def __init__(self):
        pass
    
    async def get_performance_metrics(
        self, 
        symbol: str, 
        db: Session,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get performance metrics for a symbol over specified days"""
        try:
            # Validate symbol
            if symbol.upper() not in ["NIFTY", "BANKNIFTY"]:
                raise ValueError(f"Invalid symbol: {symbol}. Must be NIFTY or BANKNIFTY")
            
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Get all predictions in the period
            predictions = (
                db.query(SmartMoneyPrediction)
                .filter(
                    and_(
                        SmartMoneyPrediction.symbol == symbol.upper(),
                        SmartMoneyPrediction.timestamp >= cutoff_date
                    )
                )
                .order_by(desc(SmartMoneyPrediction.timestamp))
                .all()
            )
            
            if not predictions:
                return self._create_empty_performance_response(symbol)
            
            # Calculate basic metrics
            total_signals = len(predictions)
            directional_signals = [p for p in predictions if p.bias != "NEUTRAL"]
            
            # Calculate win rate for completed signals
            completed_signals = [p for p in directional_signals if p.result in ["CORRECT", "WRONG"]]
            correct_signals = [p for p in completed_signals if p.result == "CORRECT"]
            
            win_rate = len(correct_signals) / len(completed_signals) if completed_signals else 0
            
            # Calculate last 7 day accuracy
            last_7_days = datetime.now(timezone.utc) - timedelta(days=7)
            recent_predictions = [p for p in predictions if p.timestamp >= last_7_days]
            recent_completed = [p for p in recent_predictions if p.result in ["CORRECT", "WRONG"]]
            recent_correct = [p for p in recent_completed if p.result == "CORRECT"]
            
            last_7_day_accuracy = len(recent_correct) / len(recent_completed) if recent_completed else 0
            
            # Calculate bias distribution
            bias_counts = {"BULLISH": 0, "BEARISH": 0, "NEUTRAL": 0}
            for prediction in predictions:
                bias_counts[prediction.bias] = bias_counts.get(prediction.bias, 0) + 1
            
            # Calculate average confidence by bias
            confidence_by_bias = {}
            for bias in ["BULLISH", "BEARISH", "NEUTRAL"]:
                bias_predictions = [p for p in predictions if p.bias == bias]
                if bias_predictions:
                    avg_confidence = sum(p.confidence for p in bias_predictions) / len(bias_predictions)
                    confidence_by_bias[bias] = round(avg_confidence, 1)
            
            # Calculate performance by IV regime
            iv_regime_performance = self._calculate_iv_regime_performance(predictions)
            
            # Get recent predictions (last 10)
            recent_predictions_data = []
            for prediction in predictions[:10]:
                recent_predictions_data.append({
                    "timestamp": prediction.timestamp.isoformat(),
                    "bias": prediction.bias,
                    "confidence": prediction.confidence,
                    "result": prediction.result or "PENDING",
                    "pcr": prediction.pcr,
                    "iv_regime": prediction.iv_regime,
                    "atm_straddle": prediction.atm_straddle,
                    "straddle_change_normalized": prediction.straddle_change_normalized,
                    "oi_acceleration_ratio": prediction.oi_acceleration_ratio,
                    "expiry_date": prediction.expiry_date
                })
            
            return {
                "symbol": symbol.upper(),
                "period_days": days,
                "total_signals": total_signals,
                "directional_signals": len(directional_signals),
                "completed_signals": len(completed_signals),
                "win_rate": round(win_rate * 100, 1),
                "last_7_day_accuracy": round(last_7_day_accuracy * 100, 1),
                "bias_distribution": bias_counts,
                "average_confidence_by_bias": confidence_by_bias,
                "iv_regime_performance": iv_regime_performance,
                "recent_predictions": recent_predictions_data,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics for {symbol}: {e}")
            raise
    
    def _calculate_iv_regime_performance(
        self, 
        predictions: List[SmartMoneyPrediction]
    ) -> Dict[str, Any]:
        """Calculate performance metrics by IV regime"""
        regimes = ["LOW", "NORMAL", "HIGH"]
        performance = {}
        
        for regime in regimes:
            regime_predictions = [p for p in predictions if p.iv_regime == regime]
            completed = [p for p in regime_predictions if p.result in ["CORRECT", "WRONG"]]
            correct = [p for p in completed if p.result == "CORRECT"]
            
            performance[regime] = {
                "total_signals": len(regime_predictions),
                "completed_signals": len(completed),
                "win_rate": round(len(correct) / len(completed) * 100, 1) if completed else 0,
                "average_confidence": round(sum(p.confidence for p in regime_predictions) / len(regime_predictions), 1) if regime_predictions else 0
            }
        
        return performance
    
    def _create_empty_performance_response(self, symbol: str) -> Dict[str, Any]:
        """Create response for no performance data"""
        return {
            "symbol": symbol.upper(),
            "period_days": 30,
            "total_signals": 0,
            "directional_signals": 0,
            "completed_signals": 0,
            "win_rate": 0.0,
            "last_7_day_accuracy": 0.0,
            "bias_distribution": {"BULLISH": 0, "BEARISH": 0, "NEUTRAL": 0},
            "average_confidence_by_bias": {},
            "iv_regime_performance": {
                "LOW": {"total_signals": 0, "completed_signals": 0, "win_rate": 0, "average_confidence": 0},
                "NORMAL": {"total_signals": 0, "completed_signals": 0, "win_rate": 0, "average_confidence": 0},
                "HIGH": {"total_signals": 0, "completed_signals": 0, "win_rate": 0, "average_confidence": 0}
            },
            "recent_predictions": [],
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "message": "No performance data available"
        }
    
    async def update_prediction_results(
        self, 
        symbol: str, 
        db: Session,
        lookback_minutes: int = 30
    ) -> Dict[str, Any]:
        """Update prediction results based on actual market moves"""
        try:
            # Get pending predictions older than lookback period
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=lookback_minutes)
            
            pending_predictions = (
                db.query(SmartMoneyPrediction)
                .filter(
                    and_(
                        SmartMoneyPrediction.symbol == symbol.upper(),
                        SmartMoneyPrediction.timestamp <= cutoff_time,
                        SmartMoneyPrediction.result.is_(None)
                    )
                )
                .all()
            )
            
            updated_count = 0
            for prediction in pending_predictions:
                # Calculate actual move
                actual_move = await self._calculate_actual_move(
                    prediction.timestamp, 
                    symbol, 
                    db,
                    lookback_minutes
                )
                
                # Determine result
                result = self._determine_prediction_result(prediction, actual_move)
                
                # Update prediction
                prediction.actual_move = actual_move
                prediction.result = result
                updated_count += 1
            
            db.commit()
            
            return {
                "symbol": symbol.upper(),
                "updated_predictions": updated_count,
                "lookback_minutes": lookback_minutes,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating prediction results for {symbol}: {e}")
            db.rollback()
            raise
    
    async def _calculate_actual_move(
        self, 
        prediction_time: datetime, 
        symbol: str, 
        db: Session,
        lookback_minutes: int
    ) -> float:
        """Calculate actual price move from prediction time to now"""
        try:
            # Get market snapshots around prediction time
            start_time = prediction_time
            end_time = prediction_time + timedelta(minutes=lookback_minutes)
            
            # Get spot price at prediction time
            start_snapshot = (
                db.query(MarketSnapshot)
                .filter(
                    and_(
                        MarketSnapshot.symbol == symbol,
                        MarketSnapshot.timestamp >= start_time,
                        MarketSnapshot.timestamp <= start_time + timedelta(minutes=5)
                    )
                )
                .order_by(MarketSnapshot.timestamp)
                .first()
            )
            
            # Get spot price at end time
            end_snapshot = (
                db.query(MarketSnapshot)
                .filter(
                    and_(
                        MarketSnapshot.symbol == symbol,
                        MarketSnapshot.timestamp >= end_time - timedelta(minutes=5),
                        MarketSnapshot.timestamp <= end_time + timedelta(minutes=5)
                    )
                )
                .order_by(desc(MarketSnapshot.timestamp))
                .first()
            )
            
            if not start_snapshot or not end_snapshot:
                return 0.0
            
            # Calculate percentage change
            start_price = start_snapshot.spot_price
            end_price = end_snapshot.spot_price
            
            if start_price == 0:
                return 0.0
            
            return ((end_price - start_price) / start_price) * 100
            
        except Exception as e:
            logger.error(f"Error calculating actual move: {e}")
            return 0.0
    
    def _determine_prediction_result(
        self, 
        prediction: SmartMoneyPrediction, 
        actual_move: float
    ) -> str:
        """Determine if prediction was correct"""
        if prediction.bias == "NEUTRAL":
            return "NEUTRAL"
        
        # Define minimum move threshold
        min_move_threshold = 0.1  # 0.1% minimum move
        
        if abs(actual_move) < min_move_threshold:
            return "NEUTRAL"
        
        if prediction.bias == "BULLISH" and actual_move > min_move_threshold:
            return "CORRECT"
        elif prediction.bias == "BEARISH" and actual_move < -min_move_threshold:
            return "CORRECT"
        else:
            return "WRONG"
