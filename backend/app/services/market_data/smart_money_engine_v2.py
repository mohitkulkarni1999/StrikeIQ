import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from ...models.market_data import OptionChainSnapshot, MarketSnapshot, SmartMoneyPrediction
import numpy as np
from collections import defaultdict
import math

logger = logging.getLogger(__name__)

class SmartMoneyEngineV2:
    """Smart Money Engine v2 - Statistically stable with proper normalization"""
    
    def __init__(self, snapshot_count: int = 30, min_snapshots: int = 10):
        self.snapshot_count = snapshot_count
        self.min_snapshots = min_snapshots
        self._cache: Dict[str, Tuple[Dict[str, Any], datetime]] = {}
        self._cache_ttl = timedelta(seconds=30)
        
        # Configuration thresholds
        self.min_oi_change_threshold = 5000  # Minimum total OI change
        self.min_volume_ratio = 0.8  # Minimum volume ratio
        self.max_data_age_minutes = 2  # Maximum data age
    
    async def generate_smart_money_signal(
        self, 
        symbol: str, 
        db: Session,
        save_prediction: bool = True
    ) -> Dict[str, Any]:
        """Generate smart money signal with statistical stability"""
        try:
            # Check cache first
            cache_key = f"smart_money_v2_{symbol}"
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                logger.info(f"Returning cached smart money signal for {symbol}")
                return cached_result
            
            # Validate symbol
            if symbol.upper() not in ["NIFTY", "BANKNIFTY"]:
                raise ValueError(f"Invalid symbol: {symbol}. Must be NIFTY or BANKNIFTY")
            
            # Get latest snapshots
            snapshots = self._get_latest_snapshots(symbol, db)
            
            # Apply minimum activation thresholds
            activation_result = self._check_activation_thresholds(snapshots, symbol)
            if activation_result:
                if save_prediction:
                    await self._save_prediction(db, symbol, activation_result)
                return activation_result
            
            # Validate data quality
            validation_result = self._validate_data_quality(snapshots)
            if validation_result:
                if save_prediction:
                    await self._save_prediction(db, symbol, validation_result)
                return validation_result
            
            # Calculate normalized features
            features = await self._calculate_normalized_features(snapshots, db)
            
            # Generate bias and confidence
            bias, confidence, reasoning = self._generate_normalized_bias(features)
            
            # Create response
            result = {
                "symbol": symbol.upper(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "bias": bias,
                "confidence": confidence,
                "metrics": {
                    "pcr": features["pcr"],
                    "pcr_shift_z": features["pcr_shift_z"],
                    "atm_straddle": features["atm_straddle"],
                    "straddle_change_normalized": features["straddle_change_normalized"],
                    "oi_acceleration_ratio": features["oi_acceleration_ratio"],
                    "volume_ratio": features["volume_ratio"],
                    "iv_regime": features["iv_regime"]
                },
                "reasoning": reasoning,
                "data_quality": {
                    "snapshot_count": len(snapshots),
                    "data_freshness_minutes": features["data_freshness_minutes"],
                    "total_oi": features["total_oi"],
                    "expiry_date": features["expiry_date"]
                }
            }
            
            # Save prediction for tracking
            if save_prediction:
                await self._save_prediction(db, symbol, result, features)
            
            # Cache result
            self._cache_result(cache_key, result)
            
            logger.info(f"Generated smart money signal for {symbol}: {bias} (confidence: {confidence:.1f})")
            return result
            
        except Exception as e:
            logger.error(f"Error generating smart money signal for {symbol}: {e}")
            raise
    
    def _check_activation_thresholds(self, snapshots: List[OptionChainSnapshot], symbol: str) -> Optional[Dict[str, Any]]:
        """Check minimum activation thresholds"""
        if not snapshots:
            return self._create_insufficient_data_response(symbol, "No data available")
        
        # Check minimum snapshot count
        unique_timestamps = len(set(s.timestamp for s in snapshots))
        if unique_timestamps < self.min_snapshots:
            return self._create_insufficient_data_response(
                symbol, 
                f"Insufficient snapshots: {unique_timestamps} < {self.min_snapshots}"
            )
        
        # Check data freshness
        latest_timestamp = max(s.timestamp for s in snapshots)
        data_age = datetime.now(timezone.utc) - latest_timestamp
        if data_age > timedelta(minutes=self.max_data_age_minutes):
            return self._create_insufficient_data_response(
                symbol,
                f"Data too old: {data_age.total_seconds()/60:.1f} minutes"
            )
        
        # Calculate total OI change
        total_oi_change = sum(abs(s.oi_change or 0) for s in snapshots)
        if total_oi_change < self.min_oi_change_threshold:
            return self._create_insufficient_data_response(
                symbol,
                f"Insufficient OI change: {total_oi_change} < {self.min_oi_change_threshold}"
            )
        
        # Calculate volume ratio
        current_volume = sum(s.volume or 0 for s in snapshots if s.timestamp == latest_timestamp)
        avg_volume_15min = self._calculate_average_volume(snapshots, minutes=15)
        volume_ratio = current_volume / avg_volume_15min if avg_volume_15min > 0 else 0
        
        if volume_ratio < self.min_volume_ratio:
            return self._create_insufficient_data_response(
                symbol,
                f"Low volume ratio: {volume_ratio:.2f} < {self.min_volume_ratio}"
            )
        
        return None  # All thresholds passed
    
    def _validate_data_quality(self, snapshots: List[OptionChainSnapshot]) -> Optional[Dict[str, Any]]:
        """Validate data quality before processing"""
        for snapshot in snapshots:
            # Check for null values in critical fields
            if snapshot.oi is None or snapshot.oi < 0:
                return self._create_invalid_data_response("Invalid OI value detected")
            
            if snapshot.ltp is None or snapshot.ltp <= 0:
                return self._create_invalid_data_response("Invalid LTP value detected")
            
            if snapshot.strike is None or snapshot.strike <= 0:
                return self._create_invalid_data_response("Invalid strike value detected")
        
        # Check timestamp ordering
        timestamps = [s.timestamp for s in snapshots]
        if timestamps != sorted(timestamps, reverse=True):
            return self._create_invalid_data_response("Timestamp ordering inconsistency")
        
        return None  # Data quality passed
    
    def _calculate_average_volume(self, snapshots: List[OptionChainSnapshot], minutes: int) -> float:
        """Calculate average volume over specified minutes"""
        if not snapshots:
            return 0
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        recent_snapshots = [s for s in snapshots if s.timestamp >= cutoff_time]
        
        if not recent_snapshots:
            return 0
        
        # Group by timestamp and sum volume
        volume_by_time = defaultdict(int)
        for s in recent_snapshots:
            volume_by_time[s.timestamp] += s.volume or 0
        
        return sum(volume_by_time.values()) / len(volume_by_time) if volume_by_time else 0
    
    async def _calculate_normalized_features(
        self, 
        snapshots: List[OptionChainSnapshot], 
        db: Session
    ) -> Dict[str, Any]:
        """Calculate all normalized features from snapshots"""
        
        # Group snapshots by timestamp
        snapshots_by_time = defaultdict(list)
        for snapshot in snapshots:
            snapshots_by_time[snapshot.timestamp].append(snapshot)
        
        sorted_timestamps = sorted(snapshots_by_time.keys(), reverse=True)
        
        if len(sorted_timestamps) < 2:
            # Not enough data for delta calculations
            return self._calculate_basic_normalized_features(
                snapshots_by_time[sorted_timestamps[0]] if sorted_timestamps else []
            )
        
        # Current snapshot (latest)
        current_data = snapshots_by_time[sorted_timestamps[0]]
        previous_data = snapshots_by_time[sorted_timestamps[1]] if len(sorted_timestamps) > 1 else []
        
        # Calculate basic features
        current_features = self._calculate_basic_normalized_features(current_data)
        previous_features = self._calculate_basic_normalized_features(previous_data) if previous_data else current_features
        
        # Calculate normalized time-based features
        features = current_features.copy()
        
        # PCR Z-score over last N snapshots
        features["pcr_shift_z"] = self._calculate_pcr_zscore(snapshots_by_time, sorted_timestamps)
        
        # Normalized straddle change (0-1 range)
        features["straddle_change_normalized"] = self._normalize_straddle_change(
            current_features["atm_straddle"],
            previous_features["atm_straddle"]
        )
        
        # Normalized OI acceleration (ratio of total OI)
        features["oi_acceleration_ratio"] = self._normalize_oi_acceleration(
            current_data, previous_data, current_features["total_oi"]
        )
        
        # Volume ratio
        current_volume = sum(s.volume or 0 for s in current_data)
        avg_volume_15min = self._calculate_average_volume(snapshots, minutes=15)
        features["volume_ratio"] = current_volume / avg_volume_15min if avg_volume_15min > 0 else 0
        
        # IV regime with proper historical data
        features["iv_regime"] = self._calculate_iv_regime_robust(snapshots_by_time, sorted_timestamps)
        
        # Data freshness
        latest_timestamp = sorted_timestamps[0]
        features["data_freshness_minutes"] = (datetime.now(timezone.utc) - latest_timestamp).total_seconds() / 60
        
        # Expiry date (nearest weekly)
        features["expiry_date"] = self._get_nearest_weekly_expiry(current_data)
        
        return features
    
    def _calculate_basic_normalized_features(self, snapshots: List[OptionChainSnapshot]) -> Dict[str, Any]:
        """Calculate basic features from a single snapshot"""
        if not snapshots:
            return {
                "total_call_oi": 0,
                "total_put_oi": 0,
                "pcr": 0,
                "atm_straddle": 0,
                "spot_price": 0,
                "total_oi": 0
            }
        
        # Separate calls and puts
        calls = [s for s in snapshots if s.option_type == "CE"]
        puts = [s for s in snapshots if s.option_type == "PE"]
        
        # Total OI
        total_call_oi = sum(s.oi for s in calls)
        total_put_oi = sum(s.oi for s in puts)
        total_oi = total_call_oi + total_put_oi
        
        # PCR
        pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0
        
        # Get spot price from market snapshot or estimate from ATM strike
        spot_price = self._get_spot_price(snapshots)
        
        # ATM strike and straddle
        atm_strike, atm_straddle = self._calculate_atm_straddle(calls, puts, spot_price)
        
        return {
            "total_call_oi": total_call_oi,
            "total_put_oi": total_put_oi,
            "total_oi": total_oi,
            "pcr": pcr,
            "atm_strike": atm_strike,
            "atm_straddle": atm_straddle,
            "spot_price": spot_price
        }
    
    def _calculate_pcr_zscore(
        self, 
        snapshots_by_time: Dict[datetime, List[OptionChainSnapshot]],
        sorted_timestamps: List[datetime]
    ) -> float:
        """Calculate PCR z-score over last N snapshots"""
        if len(sorted_timestamps) < 5:
            return 0.0
        
        # Calculate PCR for each timestamp
        pcr_values = []
        for timestamp in sorted_timestamps[:self.snapshot_count]:
            data = snapshots_by_time[timestamp]
            features = self._calculate_basic_normalized_features(data)
            pcr_values.append(features["pcr"])
        
        if len(pcr_values) < 3:
            return 0.0
        
        # Calculate z-score
        current_pcr = pcr_values[0]
        mean_pcr = np.mean(pcr_values[1:])  # Exclude current
        std_pcr = np.std(pcr_values[1:])
        
        if std_pcr == 0:
            return 0.0
        
        return (current_pcr - mean_pcr) / std_pcr
    
    def _normalize_straddle_change(
        self, 
        current_straddle: float, 
        previous_straddle: float
    ) -> float:
        """Normalize straddle change to 0-1 range"""
        if previous_straddle == 0:
            return 0.0
        
        # Calculate percentage change
        pct_change = abs((current_straddle - previous_straddle) / previous_straddle)
        
        # Normalize to 0-1 range (cap at 50% change)
        return min(pct_change / 0.5, 1.0)
    
    def _normalize_oi_acceleration(
        self, 
        current_data: List[OptionChainSnapshot],
        previous_data: List[OptionChainSnapshot],
        total_oi: float
    ) -> float:
        """Normalize OI acceleration by total OI"""
        if total_oi == 0:
            return 0.0
        
        # Current OI delta
        current_oi_delta = self._calculate_oi_delta(current_data)
        previous_oi_delta = self._calculate_oi_delta(previous_data)
        
        acceleration = current_oi_delta - previous_oi_delta
        
        # Normalize by total OI
        return acceleration / total_oi if total_oi > 0 else 0.0
    
    def _calculate_oi_delta(self, snapshots: List[OptionChainSnapshot]) -> float:
        """Calculate OI delta (PE OI delta - CE OI delta)"""
        calls = [s for s in snapshots if s.option_type == "CE"]
        puts = [s for s in snapshots if s.option_type == "PE"]
        
        # Use oi_delta field if available, otherwise fall back to oi_change
        call_oi_delta = sum(s.oi_delta or s.oi_change or 0 for s in calls)
        put_oi_delta = sum(s.oi_delta or s.oi_change or 0 for s in puts)
        
        return put_oi_delta - call_oi_delta
    
    def _calculate_iv_regime_robust(
        self, 
        snapshots_by_time: Dict[datetime, List[OptionChainSnapshot]],
        sorted_timestamps: List[datetime]
    ) -> str:
        """Classify IV regime using at least 1 full trading day of data"""
        # Need at least 75 snapshots for 1 trading day (5-minute intervals over 6.25 hours)
        min_historical_snapshots = 75
        
        if len(sorted_timestamps) < min_historical_snapshots:
            return "NORMAL"  # Insufficient historical data
        
        # Calculate average IV for each timestamp
        iv_values = []
        for timestamp in sorted_timestamps[:min_historical_snapshots]:
            data = snapshots_by_time[timestamp]
            valid_iv = [s.iv for s in data if s.iv and s.iv > 0]
            if valid_iv:
                iv_values.append(sum(valid_iv) / len(valid_iv))
        
        if len(iv_values) < 20:
            return "NORMAL"  # Still insufficient data
        
        # Classify based on percentiles
        current_iv = iv_values[0]
        iv_sorted = sorted(iv_values)
        
        p30 = np.percentile(iv_sorted, 30)
        p70 = np.percentile(iv_sorted, 70)
        
        if current_iv <= p30:
            return "LOW"
        elif current_iv >= p70:
            return "HIGH"
        else:
            return "NORMAL"
    
    def _get_nearest_weekly_expiry(self, snapshots: List[OptionChainSnapshot]) -> str:
        """Get nearest weekly expiry from snapshots"""
        if not snapshots:
            return ""
        
        # Get unique expiry dates
        expiries = set(s.expiry for s in snapshots if s.expiry)
        
        if not expiries:
            return ""
        
        # For now, return the most common expiry
        # In production, this should calculate actual weekly expiry
        return max(expiries, key=lambda x: sum(1 for s in snapshots if s.expiry == x))
    
    def _generate_normalized_bias(self, features: Dict[str, Any]) -> Tuple[str, float, List[str]]:
        """Generate bias using normalized features and sigmoid confidence"""
        reasoning = []
        
        # Extract normalized features
        pcr_z = features.get("pcr_shift_z", 0)
        straddle_norm = features.get("straddle_change_normalized", 0)
        oi_accel_ratio = features.get("oi_acceleration_ratio", 0)
        volume_ratio = features.get("volume_ratio", 0)
        pcr = features.get("pcr", 0)
        
        # Calculate weighted sum for bias
        bullish_weight = 0
        bearish_weight = 0
        
        # PCR Z-score contribution
        if pcr_z > 0.5:  # PCR increasing significantly
            bullish_weight += pcr_z
            reasoning.append(f"PCR Z-score bullish: {pcr_z:.2f}")
        elif pcr_z < -0.5:  # PCR decreasing significantly
            bearish_weight += abs(pcr_z)
            reasoning.append(f"PCR Z-score bearish: {pcr_z:.2f}")
        
        # OI acceleration contribution
        if oi_accel_ratio > 0.001:  # Positive OI acceleration
            bullish_weight += oi_accel_ratio * 100
            reasoning.append(f"Positive OI acceleration: {oi_accel_ratio:.4f}")
        elif oi_accel_ratio < -0.001:  # Negative OI acceleration
            bearish_weight += abs(oi_accel_ratio) * 100
            reasoning.append(f"Negative OI acceleration: {oi_accel_ratio:.4f}")
        
        # Straddle change contribution
        if straddle_norm > 0.3:  # Significant straddle change
            # Check direction from raw data
            if features.get("straddle_change_percent", 0) > 0:
                bullish_weight += straddle_norm * 2
                reasoning.append(f"Upward straddle expansion: {straddle_norm:.2f}")
            else:
                bearish_weight += straddle_norm * 2
                reasoning.append(f"Downward straddle expansion: {straddle_norm:.2f}")
        
        # Volume ratio contribution
        if volume_ratio > 1.2:  # High volume
            bullish_weight += (volume_ratio - 1) * 2
            reasoning.append(f"High volume ratio: {volume_ratio:.2f}")
        
        # PCR level contribution
        if pcr > 1.3:  # High PCR
            bullish_weight += 1
            reasoning.append(f"High PCR level: {pcr:.2f}")
        elif pcr < 0.7:  # Low PCR
            bearish_weight += 1
            reasoning.append(f"Low PCR level: {pcr:.2f}")
        
        # Determine bias
        weight_diff = bullish_weight - bearish_weight
        if weight_diff > 0.5:
            bias = "BULLISH"
        elif weight_diff < -0.5:
            bias = "BEARISH"
        else:
            bias = "NEUTRAL"
        
        # Calculate confidence using sigmoid
        weighted_sum = weight_diff
        confidence = self._sigmoid_confidence(weighted_sum) * 100
        
        # Add reasoning for neutral bias
        if bias == "NEUTRAL":
            reasoning.append("Conflicting signals - neutral bias")
        
        return bias, round(confidence, 1), reasoning
    
    def _sigmoid_confidence(self, weighted_sum: float) -> float:
        """Calculate confidence using sigmoid function"""
        # Sigmoid function: 1 / (1 + e^(-x))
        # Scale the input to make the curve more appropriate
        scaled_input = weighted_sum * 2
        sigmoid_value = 1 / (1 + math.exp(-scaled_input))
        
        # Ensure confidence is between 0 and 1
        return max(0, min(1, sigmoid_value))
    
    def _get_spot_price(self, snapshots: List[OptionChainSnapshot]) -> float:
        """Get spot price from snapshots or estimate"""
        # Try to get from market snapshot first
        # For now, estimate from ATM strike range
        strikes = [s.strike for s in snapshots if s.strike]
        if strikes:
            return sum(strikes) / len(strikes)
        return 0
    
    def _calculate_atm_straddle(
        self, 
        calls: List[OptionChainSnapshot], 
        puts: List[OptionChainSnapshot],
        spot_price: float
    ) -> Tuple[float, float]:
        """Calculate ATM strike and straddle price"""
        if not calls or not puts or spot_price == 0:
            return 0, 0
        
        # Find ATM strike (closest to spot price)
        all_strikes = set(s.strike for s in calls) | set(s.strike for s in puts)
        if not all_strikes:
            return 0, 0
        
        atm_strike = min(all_strikes, key=lambda x: abs(x - spot_price))
        
        # Find corresponding CE and PE at ATM strike
        atm_ce = next((s for s in calls if s.strike == atm_strike), None)
        atm_pe = next((s for s in puts if s.strike == atm_strike), None)
        
        # Calculate straddle price
        straddle_price = 0
        if atm_ce and atm_pe:
            straddle_price = atm_ce.ltp + atm_pe.ltp
        
        return atm_strike, straddle_price
    
    def _get_latest_snapshots(self, symbol: str, db: Session) -> List[OptionChainSnapshot]:
        """Get latest option chain snapshots for symbol with optimized queries"""
        try:
            # Use indexed query to get latest N timestamps efficiently
            latest_timestamps = (
                db.query(OptionChainSnapshot.timestamp)
                .filter(OptionChainSnapshot.symbol == symbol.upper())
                .distinct()
                .order_by(desc(OptionChainSnapshot.timestamp))
                .limit(self.snapshot_count)
                .all()
            )
            
            if not latest_timestamps:
                return []
            
            timestamps = [t[0] for t in latest_timestamps]
            
            # Batch fetch all snapshots for these timestamps with optimized query
            snapshots = (
                db.query(OptionChainSnapshot)
                .filter(
                    and_(
                        OptionChainSnapshot.symbol == symbol.upper(),
                        OptionChainSnapshot.timestamp.in_(timestamps)
                    )
                )
                .order_by(desc(OptionChainSnapshot.timestamp))
                .all()
            )
            
            # Apply additional filtering in memory for better performance
            filtered_snapshots = []
            seen_strikes = set()
            
            for snapshot in snapshots:
                strike_key = (snapshot.timestamp, snapshot.strike, snapshot.option_type)
                if strike_key not in seen_strikes:
                    seen_strikes.add(strike_key)
                    filtered_snapshots.append(snapshot)
            
            return filtered_snapshots
            
        except Exception as e:
            logger.error(f"Error fetching snapshots for {symbol}: {e}")
            return []
    
    def _create_insufficient_data_response(self, symbol: str, reason: str) -> Dict[str, Any]:
        """Create response for insufficient data"""
        return {
            "symbol": symbol.upper(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "bias": "NEUTRAL",
            "confidence": 0.0,
            "metrics": {
                "pcr": 0.0,
                "pcr_shift_z": 0.0,
                "atm_straddle": 0.0,
                "straddle_change_normalized": 0.0,
                "oi_acceleration_ratio": 0.0,
                "volume_ratio": 0.0,
                "iv_regime": "NORMAL"
            },
            "reasoning": [f"Insufficient data for directional signal: {reason}"],
            "data_quality": {
                "status": "insufficient_data",
                "reason": reason
            }
        }
    
    def _create_invalid_data_response(self, reason: str) -> Dict[str, Any]:
        """Create response for invalid data"""
        return {
            "symbol": "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "bias": "NEUTRAL",
            "confidence": 0.0,
            "metrics": {
                "pcr": 0.0,
                "pcr_shift_z": 0.0,
                "atm_straddle": 0.0,
                "straddle_change_normalized": 0.0,
                "oi_acceleration_ratio": 0.0,
                "volume_ratio": 0.0,
                "iv_regime": "NORMAL"
            },
            "reasoning": [f"Data validation failed: {reason}"],
            "data_quality": {
                "status": "invalid_data",
                "reason": reason
            }
        }
    
    async def _save_prediction(
        self, 
        db: Session, 
        symbol: str, 
        result: Dict[str, Any],
        features: Optional[Dict[str, Any]] = None
    ):
        """Save prediction for performance tracking"""
        try:
            prediction = SmartMoneyPrediction(
                symbol=symbol.upper(),
                bias=result["bias"],
                confidence=result["confidence"],
                pcr=result["metrics"]["pcr"],
                pcr_shift_z=result["metrics"]["pcr_shift_z"],
                atm_straddle=result["metrics"]["atm_straddle"],
                straddle_change_normalized=result["metrics"]["straddle_change_normalized"],
                oi_acceleration_ratio=result["metrics"]["oi_acceleration_ratio"],
                iv_regime=result["metrics"]["iv_regime"],
                expiry_date=features.get("expiry_date", "") if features else ""
            )
            
            db.add(prediction)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error saving prediction: {e}")
            db.rollback()
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached result if valid"""
        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if datetime.now(timezone.utc) - timestamp < self._cache_ttl:
                return result
            else:
                del self._cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache result with timestamp"""
        self._cache[cache_key] = (result, datetime.now(timezone.utc))
    
    def clear_cache(self):
        """Clear all cached results"""
        self._cache.clear()
        logger.info("Smart money engine v2 cache cleared")
