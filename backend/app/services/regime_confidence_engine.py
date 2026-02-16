"""
Regime Confidence Engine Upgrade
Enhanced regime analysis with stability, acceleration, and transition probability
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

class RegimeType(Enum):
    RANGE = "range"
    TREND = "trend"
    BREAKOUT = "breakout"
    PIN_RISK = "pin_risk"
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    UNKNOWN = "unknown"

@dataclass
class RegimeHistory:
    """Historical regime data point"""
    regime: RegimeType
    timestamp: datetime
    confidence: float
    metrics: Dict[str, Any]

@dataclass
class RegimeDynamics:
    """Enhanced regime analysis"""
    regime: RegimeType
    confidence: float
    stability_score: float  # How long regime persisted (0-100)
    acceleration_index: float  # Is regime strengthening? (-100 to +100)
    transition_probability: float  # Probability of regime change
    regime_duration: float  # Duration in minutes
    historical_consistency: float  # How consistent has this regime been
    momentum_score: float  # Current momentum of regime characteristics

class RegimeConfidenceEngine:
    """
    Enhanced regime confidence analysis with dynamics and prediction
    """
    
    def __init__(self):
        self.regime_history: Dict[str, List[RegimeHistory]] = {}
        self.regime_start_times: Dict[str, datetime] = {}
        self.previous_metrics: Dict[str, Dict[str, Any]] = {}
        self._lock = None  # Will be set in async context
        
        # Analysis parameters
        self.MIN_HISTORY_POINTS = 5
        self.MAX_HISTORY_POINTS = 100
        self.STABILITY_TIME_WEIGHT = 0.6  # Weight for time-based stability
        self.CONSISTENCY_WEIGHT = 0.4  # Weight for consistency-based stability
        
    async def analyze_regime_dynamics(self, symbol: str, current_metrics: Dict[str, Any]) -> RegimeDynamics:
        """
        Analyze regime dynamics with enhanced confidence metrics
        """
        try:
            # Extract current regime
            current_regime_str = current_metrics.get("structural_regime", "unknown")
            current_regime = RegimeType(current_regime_str)
            current_confidence = current_metrics.get("regime_confidence", 50)
            
            # Get previous metrics for acceleration calculation
            previous_metrics = self.previous_metrics.get(symbol, {})
            
            # Update history
            await self._update_regime_history(symbol, current_regime, current_confidence, current_metrics)
            
            # Calculate dynamics
            stability_score = self._calculate_stability_score(symbol)
            acceleration_index = self._calculate_acceleration_index(symbol, current_metrics, previous_metrics)
            transition_probability = self._calculate_transition_probability(symbol)
            regime_duration = self._calculate_regime_duration(symbol)
            historical_consistency = self._calculate_historical_consistency(symbol)
            momentum_score = self._calculate_momentum_score(symbol, current_metrics, previous_metrics)
            
            # Store current metrics for next iteration
            self.previous_metrics[symbol] = current_metrics.copy()
            
            return RegimeDynamics(
                regime=current_regime,
                confidence=current_confidence,
                stability_score=stability_score,
                acceleration_index=acceleration_index,
                transition_probability=transition_probability,
                regime_duration=regime_duration,
                historical_consistency=historical_consistency,
                momentum_score=momentum_score
            )
            
        except Exception as e:
            logger.error(f"Error analyzing regime dynamics for {symbol}: {e}")
            return self._create_default_dynamics(symbol)
    
    async def _update_regime_history(self, symbol: str, regime: RegimeType, confidence: float, metrics: Dict[str, Any]) -> None:
        """Update regime history for analysis"""
        if symbol not in self.regime_history:
            self.regime_history[symbol] = []
        
        # Add new history point
        history_point = RegimeHistory(
            regime=regime,
            timestamp=datetime.now(timezone.utc),
            confidence=confidence,
            metrics=metrics.copy()
        )
        
        self.regime_history[symbol].append(history_point)
        
        # Limit history size
        if len(self.regime_history[symbol]) > self.MAX_HISTORY_POINTS:
            self.regime_history[symbol] = self.regime_history[symbol][-self.MAX_HISTORY_POINTS:]
        
        # Update regime start time if changed
        if len(self.regime_history[symbol]) >= 2:
            previous_regime = self.regime_history[symbol][-2].regime
            if previous_regime != regime:
                self.regime_start_times[symbol] = datetime.now(timezone.utc)
        elif symbol not in self.regime_start_times:
            self.regime_start_times[symbol] = datetime.now(timezone.utc)
    
    def _calculate_stability_score(self, symbol: str) -> float:
        """
        Calculate regime stability score (0-100)
        Based on duration and consistency
        """
        try:
            if symbol not in self.regime_start_times:
                return 50  # No history
            
            # Time-based stability
            start_time = self.regime_start_times[symbol]
            duration_minutes = (datetime.now(timezone.utc) - start_time).total_seconds() / 60
            
            # More time = more stable (up to a point)
            time_stability = min(100, duration_minutes / 2)  # 2 hours = 100% time stability
            
            # Consistency-based stability
            consistency_stability = self._calculate_historical_consistency(symbol)
            
            # Weighted combination
            stability_score = (time_stability * self.STABILITY_TIME_WEIGHT + 
                            consistency_stability * self.CONSISTENCY_WEIGHT)
            
            return min(100, max(0, stability_score))
            
        except Exception as e:
            logger.error(f"Error calculating stability score: {e}")
            return 50
    
    def _calculate_acceleration_index(self, symbol: str, current_metrics: Dict[str, Any], previous_metrics: Dict[str, Any]) -> float:
        """
        Calculate acceleration index (-100 to +100)
        Positive = regime strengthening, Negative = regime weakening
        """
        try:
            if not previous_metrics:
                return 0
            
            acceleration_factors = []
            
            # Confidence acceleration
            current_confidence = current_metrics.get("regime_confidence", 50)
            previous_confidence = previous_metrics.get("regime_confidence", 50)
            confidence_change = current_confidence - previous_confidence
            acceleration_factors.append(confidence_change)
            
            # Net gamma acceleration
            current_gamma = current_metrics.get("net_gamma", 0)
            previous_gamma = previous_metrics.get("net_gamma", 0)
            
            if previous_gamma != 0:
                gamma_change_pct = ((current_gamma - previous_gamma) / abs(previous_gamma)) * 100
                # Scale to -100 to +100 range
                gamma_acceleration = np.clip(gamma_change_pct / 2, -100, 100)
                acceleration_factors.append(gamma_acceleration)
            
            # Flow imbalance acceleration
            current_flow = current_metrics.get("flow_imbalance", 0)
            previous_flow = previous_metrics.get("flow_imbalance", 0)
            flow_change = abs(current_flow) - abs(previous_flow)
            flow_acceleration = np.clip(flow_change * 100, -100, 100)
            acceleration_factors.append(flow_acceleration)
            
            # Expected move acceleration (volatility indicator)
            current_expected = current_metrics.get("expected_move", 0)
            previous_expected = previous_metrics.get("expected_move", 0)
            
            if previous_expected > 0:
                expected_change_pct = ((current_expected - previous_expected) / previous_expected) * 100
                expected_acceleration = np.clip(expected_change_pct, -100, 100)
                acceleration_factors.append(expected_acceleration)
            
            # Calculate weighted average
            if acceleration_factors:
                acceleration_index = np.mean(acceleration_factors)
                return np.clip(acceleration_index, -100, 100)
            
            return 0
            
        except Exception as e:
            logger.error(f"Error calculating acceleration index: {e}")
            return 0
    
    def _calculate_transition_probability(self, symbol: str) -> float:
        """
        Calculate probability of regime change (0-100)
        Based on historical patterns and current stability
        """
        try:
            if symbol not in self.regime_history or len(self.regime_history[symbol]) < self.MIN_HISTORY_POINTS:
                return 50  # Insufficient data
            
            history = self.regime_history[symbol]
            
            # Historical transition frequency
            transitions = 0
            for i in range(1, len(history)):
                if history[i].regime != history[i-1].regime:
                    transitions += 1
            
            total_periods = len(history) - 1
            if total_periods > 0:
                historical_transition_rate = transitions / total_periods
            else:
                historical_transition_rate = 0.1  # Default 10%
            
            # Current stability factor (more stable = less likely to transition)
            stability_score = self._calculate_stability_score(symbol)
            stability_factor = (100 - stability_score) / 100
            
            # Acceleration factor (high acceleration = more likely to transition)
            current_metrics = history[-1].metrics if history else {}
            acceleration_index = current_metrics.get("acceleration_index", 0)
            acceleration_factor = abs(acceleration_index) / 100
            
            # Combine factors
            transition_probability = (
                historical_transition_rate * 40 +  # 40% weight to history
                stability_factor * 30 +           # 30% weight to stability
                acceleration_factor * 30           # 30% weight to acceleration
            )
            
            return min(100, max(0, transition_probability * 100))
            
        except Exception as e:
            logger.error(f"Error calculating transition probability: {e}")
            return 50
    
    def _calculate_regime_duration(self, symbol: str) -> float:
        """Calculate current regime duration in minutes"""
        try:
            if symbol not in self.regime_start_times:
                return 0
            
            start_time = self.regime_start_times[symbol]
            duration_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
            return duration_seconds / 60  # Convert to minutes
            
        except Exception as e:
            logger.error(f"Error calculating regime duration: {e}")
            return 0
    
    def _calculate_historical_consistency(self, symbol: str) -> float:
        """
        Calculate how consistent the current regime has been historically
        """
        try:
            if symbol not in self.regime_history or len(self.regime_history[symbol]) < self.MIN_HISTORY_POINTS:
                return 50
            
            history = self.regime_history[symbol]
            current_regime = history[-1].regime
            
            # Count occurrences of current regime in recent history
            recent_history = history[-20:]  # Last 20 points
            regime_count = sum(1 for h in recent_history if h.regime == current_regime)
            
            consistency = (regime_count / len(recent_history)) * 100
            return min(100, max(0, consistency))
            
        except Exception as e:
            logger.error(f"Error calculating historical consistency: {e}")
            return 50
    
    def _calculate_momentum_score(self, symbol: str, current_metrics: Dict[str, Any], previous_metrics: Dict[str, Any]) -> float:
        """
        Calculate momentum score for current regime characteristics (0-100)
        """
        try:
            momentum_factors = []
            
            # Confidence momentum
            current_confidence = current_metrics.get("regime_confidence", 50)
            if current_confidence > 70:
                momentum_factors.append(current_confidence - 50)  # High confidence adds momentum
            
            # Flow momentum
            flow_imbalance = abs(current_metrics.get("flow_imbalance", 0))
            if flow_imbalance > 0.3:
                momentum_factors.append(flow_imbalance * 50)  # Strong flow adds momentum
            
            # Gamma momentum
            net_gamma = abs(current_metrics.get("net_gamma", 0))
            if net_gamma > 1000000:
                gamma_momentum = min(50, net_gamma / 1000000 * 10)
                momentum_factors.append(gamma_momentum)
            
            # Expected move momentum (volatility)
            expected_move = current_metrics.get("expected_move", 0)
            spot = current_metrics.get("spot", 1)
            if spot > 0:
                expected_move_pct = (expected_move / spot) * 100
                if expected_move_pct > 1:  # More than 1% expected move
                    momentum_factors.append(min(50, expected_move_pct * 10))
            
            if momentum_factors:
                momentum_score = np.mean(momentum_factors)
                return min(100, max(0, momentum_score))
            
            return 25  # Low momentum default
            
        except Exception as e:
            logger.error(f"Error calculating momentum score: {e}")
            return 25
    
    def _create_default_dynamics(self, symbol: str) -> RegimeDynamics:
        """Create default regime dynamics for error cases"""
        return RegimeDynamics(
            regime=RegimeType.UNKNOWN,
            confidence=50,
            stability_score=50,
            acceleration_index=0,
            transition_probability=50,
            regime_duration=0,
            historical_consistency=50,
            momentum_score=25
        )
    
    def format_for_frontend(self, dynamics: RegimeDynamics) -> Dict[str, Any]:
        """Format regime dynamics for frontend consumption"""
        return {
            "regime": dynamics.regime.value,
            "confidence": dynamics.confidence,
            "stability_score": dynamics.stability_score,
            "acceleration_index": dynamics.acceleration_index,
            "transition_probability": dynamics.transition_probability,
            "regime_duration_minutes": dynamics.regime_duration,
            "historical_consistency": dynamics.historical_consistency,
            "momentum_score": dynamics.momentum_score,
            "interpretation": {
                "stability_level": self._interpret_stability(dynamics.stability_score),
                "acceleration_trend": self._interpret_acceleration(dynamics.acceleration_index),
                "transition_risk": self._interpret_transition_risk(dynamics.transition_probability),
                "momentum_strength": self._interpret_momentum(dynamics.momentum_score)
            },
            "alerts": self._generate_regime_alerts(dynamics)
        }
    
    def _interpret_stability(self, stability_score: float) -> str:
        """Interpret stability score"""
        if stability_score >= 80:
            return "very_stable"
        elif stability_score >= 60:
            return "stable"
        elif stability_score >= 40:
            return "moderately_stable"
        else:
            return "unstable"
    
    def _interpret_acceleration(self, acceleration_index: float) -> str:
        """Interpret acceleration index"""
        if acceleration_index > 30:
            return "strengthening_rapidly"
        elif acceleration_index > 10:
            return "strengthening"
        elif acceleration_index > -10:
            return "stable"
        elif acceleration_index > -30:
            return "weakening"
        else:
            return "weakening_rapidly"
    
    def _interpret_transition_risk(self, transition_probability: float) -> str:
        """Interpret transition probability"""
        if transition_probability >= 70:
            return "high_risk"
        elif transition_probability >= 40:
            return "moderate_risk"
        else:
            return "low_risk"
    
    def _interpret_momentum(self, momentum_score: float) -> str:
        """Interpret momentum score"""
        if momentum_score >= 70:
            return "strong_momentum"
        elif momentum_score >= 40:
            return "moderate_momentum"
        else:
            return "weak_momentum"
    
    def _generate_regime_alerts(self, dynamics: RegimeDynamics) -> List[Dict[str, Any]]:
        """Generate alerts based on regime dynamics"""
        alerts = []
        
        # High transition risk alert
        if dynamics.transition_probability >= 70:
            alerts.append({
                "type": "transition_risk",
                "severity": "high",
                "message": f"High regime change risk ({dynamics.transition_probability:.0f}% probability)"
            })
        
        # Regime weakening alert
        if dynamics.acceleration_index < -30:
            alerts.append({
                "type": "regime_weakening",
                "severity": "medium",
                "message": f"Current regime weakening rapidly (acceleration: {dynamics.acceleration_index:.0f})"
            })
        
        # Low stability alert
        if dynamics.stability_score < 30:
            alerts.append({
                "type": "low_stability",
                "severity": "medium",
                "message": f"Regime stability low ({dynamics.stability_score:.0f}/100)"
            })
        
        # High momentum alert
        if dynamics.momentum_score >= 80:
            alerts.append({
                "type": "high_momentum",
                "severity": "low",
                "message": f"Strong regime momentum detected ({dynamics.momentum_score:.0f}/100)"
            })
        
        return alerts
