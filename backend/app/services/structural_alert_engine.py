"""
Structural Alert Engine
Transforms analytics into actionable trading alerts and events
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    GAMMA_FLIP_BREAK = "gamma_flip_break"
    FLOW_IMBALANCE_SPIKE = "flow_imbalance_spike"
    REGIME_CHANGE = "regime_change"
    PIN_RISK_ALERT = "pin_risk_alert"
    GAMMA_PRESSURE_SHIFT = "gamma_pressure_shift"
    EXPIRY_MAGNET_ALERT = "expiry_magnet_alert"

@dataclass
class StructuralAlert:
    """Structural trading alert"""
    alert_type: AlertType
    severity: AlertSeverity
    symbol: str
    message: str
    current_value: float
    threshold: float
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class GammaMagnet:
    """Strike-level gamma analysis"""
    strike: float
    gex_value: float
    magnet_strength: float  # How strongly it attracts price
    distance_from_spot: float
    classification: str  # "magnet" or "cliff"

@dataclass
class StructuralInteraction:
    """Gamma + Flow interaction state"""
    gamma_state: str  # positive/negative
    flow_state: str   # call_writing/put_buying/etc.
    interaction_type: str  # range_compression/downside_acceleration/etc.
    confidence: float
    description: str

@dataclass
class RegimeDynamics:
    """Enhanced regime analysis"""
    regime: str
    confidence: float
    stability_score: float  # How long regime persisted (0-100)
    acceleration_index: float  # Is regime strengthening? (-100 to +100)
    transition_probability: float  # Probability of regime change

@dataclass
class ExpiryMagnetModel:
    """Expiry-specific pin and magnet analysis"""
    max_oi_strike: float
    max_gamma_strike: float
    distance_to_max_oi: float
    distance_to_max_gamma: float
    pin_probability: float
    magnet_strength: float
    days_to_expiry: int

class StructuralAlertEngine:
    """
    Transforms analytics into actionable trading intelligence
    """
    
    def __init__(self):
        self.alert_history: Dict[str, List[StructuralAlert]] = {}
        self.previous_regime: Dict[str, str] = {}
        self.regime_start_time: Dict[str, datetime] = {}
        self.regime_stability: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        
        # Alert thresholds
        self.FLOW_IMBALANCE_THRESHOLD = 0.6
        self.GAMMA_FLIP_DISTANCE_THRESHOLD = 50  # Points
        self.PIN_RISK_THRESHOLD = 0.8
        self.REGIME_CHANGE_MIN_DURATION = 300  # 5 minutes
    
    async def analyze_and_generate_alerts(self, symbol: str, metrics: Dict[str, Any]) -> List[StructuralAlert]:
        """
        Analyze metrics and generate structural alerts
        """
        alerts = []
        
        try:
            # 1️⃣ Gamma Flip Break Alert
            gamma_flip_alert = self._check_gamma_flip_break(symbol, metrics)
            if gamma_flip_alert:
                alerts.append(gamma_flip_alert)
            
            # 2️⃣ Flow Imbalance Spike Alert
            flow_alert = self._check_flow_imbalance_spike(symbol, metrics)
            if flow_alert:
                alerts.append(flow_alert)
            
            # 3️⃣ Regime Change Alert
            regime_alert = self._check_regime_change(symbol, metrics)
            if regime_alert:
                alerts.append(regime_alert)
            
            # 4️⃣ Pin Risk Alert
            pin_alert = self._check_pin_risk(symbol, metrics)
            if pin_alert:
                alerts.append(pin_alert)
            
            # 5️⃣ Gamma Pressure Shift Alert
            pressure_alert = self._check_gamma_pressure_shift(symbol, metrics)
            if pressure_alert:
                alerts.append(pressure_alert)
            
            # 6️⃣ Expiry Magnet Alert (if near expiry)
            expiry_alert = self._check_expiry_magnet(symbol, metrics)
            if expiry_alert:
                alerts.append(expiry_alert)
            
            # Store alerts
            await self._store_alerts(symbol, alerts)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating alerts for {symbol}: {e}")
            return []
    
    def _check_gamma_flip_break(self, symbol: str, metrics: Dict[str, Any]) -> Optional[StructuralAlert]:
        """Check if spot crossed gamma flip level"""
        try:
            spot = metrics.get("spot", 0)
            gamma_flip = metrics.get("gamma_flip_level", 0)
            distance_from_flip = metrics.get("distance_from_flip", 0)
            
            if not spot or not gamma_flip:
                return None
            
            # Check if spot crossed flip level
            if abs(distance_from_flip) < self.GAMMA_FLIP_DISTANCE_THRESHOLD:
                severity = AlertSeverity.HIGH if abs(distance_from_flip) < 25 else AlertSeverity.MEDIUM
                
                direction = "below" if spot < gamma_flip else "above"
                risk_type = "trend acceleration" if spot < gamma_flip else "mean reversion"
                
                return StructuralAlert(
                    alert_type=AlertType.GAMMA_FLIP_BREAK,
                    severity=severity,
                    symbol=symbol,
                    message=f"Spot moved {direction} gamma flip ({gamma_flip:.0f}). {risk_type.title()} risk elevated.",
                    current_value=spot,
                    threshold=gamma_flip,
                    timestamp=datetime.now(timezone.utc),
                    metadata={
                        "distance_from_flip": distance_from_flip,
                        "gamma_flip_level": gamma_flip,
                        "risk_type": risk_type
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking gamma flip break: {e}")
            return None
    
    def _check_flow_imbalance_spike(self, symbol: str, metrics: Dict[str, Any]) -> Optional[StructuralAlert]:
        """Check for unusual flow imbalance"""
        try:
            flow_imbalance = metrics.get("flow_imbalance", 0)
            flow_direction = metrics.get("flow_direction", "neutral")
            
            if abs(flow_imbalance) > self.FLOW_IMBALANCE_THRESHOLD:
                severity = AlertSeverity.HIGH if abs(flow_imbalance) > 0.8 else AlertSeverity.MEDIUM
                
                action = "writing" if "writing" in flow_direction else "buying"
                instrument = "calls" if flow_imbalance > 0 else "puts"
                
                return StructuralAlert(
                    alert_type=AlertType.FLOW_IMBALANCE_SPIKE,
                    severity=severity,
                    symbol=symbol,
                    message=f"Unusual {instrument} {action} detected. Flow imbalance: {flow_imbalance:.2f}",
                    current_value=flow_imbalance,
                    threshold=self.FLOW_IMBALANCE_THRESHOLD,
                    timestamp=datetime.now(timezone.utc),
                    metadata={
                        "flow_direction": flow_direction,
                        "imbalance_level": abs(flow_imbalance)
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking flow imbalance: {e}")
            return None
    
    def _check_regime_change(self, symbol: str, metrics: Dict[str, Any]) -> Optional[StructuralAlert]:
        """Check for regime changes"""
        try:
            current_regime = metrics.get("structural_regime", "unknown")
            confidence = metrics.get("regime_confidence", 0)
            
            if current_regime == "unknown":
                return None
            
            # Get previous regime
            previous_regime = self.previous_regime.get(symbol, current_regime)
            
            # Check for regime change
            if previous_regime != current_regime:
                # Check if enough time has passed since last change
                if symbol in self.regime_start_time:
                    time_since_change = (datetime.now(timezone.utc) - self.regime_start_time[symbol]).seconds
                    if time_since_change < self.REGIME_CHANGE_MIN_DURATION:
                        return None
                
                severity = AlertSeverity.HIGH if confidence > 70 else AlertSeverity.MEDIUM
                
                # Update regime tracking
                self.previous_regime[symbol] = current_regime
                self.regime_start_time[symbol] = datetime.now(timezone.utc)
                
                return StructuralAlert(
                    alert_type=AlertType.REGIME_CHANGE,
                    severity=severity,
                    symbol=symbol,
                    message=f"Regime changed from {previous_regime} to {current_regime}. Confidence: {confidence:.0f}%",
                    current_value=confidence,
                    threshold=50,
                    timestamp=datetime.now(timezone.utc),
                    metadata={
                        "previous_regime": previous_regime,
                        "new_regime": current_regime,
                        "confidence": confidence
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking regime change: {e}")
            return None
    
    def _check_pin_risk(self, symbol: str, metrics: Dict[str, Any]) -> Optional[StructuralAlert]:
        """Check for pin risk conditions"""
        try:
            flow_imbalance = metrics.get("flow_imbalance", 0)
            structural_regime = metrics.get("structural_regime", "unknown")
            distance_from_flip = metrics.get("distance_from_flip", 999999)
            
            # High pin risk conditions
            pin_risk_score = 0
            
            if abs(flow_imbalance) > self.PIN_RISK_THRESHOLD:
                pin_risk_score += 40
            
            if structural_regime == "range":
                pin_risk_score += 30
            
            if distance_from_flip < 25:
                pin_risk_score += 30
            
            if pin_risk_score > 60:
                severity = AlertSeverity.CRITICAL if pin_risk_score > 80 else AlertSeverity.HIGH
                
                return StructuralAlert(
                    alert_type=AlertType.PIN_RISK_ALERT,
                    severity=severity,
                    symbol=symbol,
                    message=f"High pin risk detected. Score: {pin_risk_score}/100. Price may get pinned.",
                    current_value=pin_risk_score,
                    threshold=60,
                    timestamp=datetime.now(timezone.utc),
                    metadata={
                        "pin_risk_score": pin_risk_score,
                        "flow_imbalance": flow_imbalance,
                        "regime": structural_regime,
                        "distance_from_flip": distance_from_flip
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking pin risk: {e}")
            return None
    
    def _check_gamma_pressure_shift(self, symbol: str, metrics: Dict[str, Any]) -> Optional[StructuralAlert]:
        """Check for significant gamma pressure changes"""
        try:
            net_gamma = metrics.get("net_gamma", 0)
            previous_gamma = getattr(self, f'_previous_gamma_{symbol}', 0)
            
            # Calculate gamma change
            gamma_change = net_gamma - previous_gamma
            gamma_change_pct = (gamma_change / abs(previous_gamma)) * 100 if previous_gamma != 0 else 0
            
            # Update previous gamma
            setattr(self, f'_previous_gamma_{symbol}', net_gamma)
            
            # Check for significant change
            if abs(gamma_change_pct) > 20:  # 20% change threshold
                severity = AlertSeverity.HIGH if abs(gamma_change_pct) > 50 else AlertSeverity.MEDIUM
                
                direction = "increasing" if gamma_change > 0 else "decreasing"
                pressure_type = "mean reversion" if net_gamma > 0 else "trend acceleration"
                
                return StructuralAlert(
                    alert_type=AlertType.GAMMA_PRESSURE_SHIFT,
                    severity=severity,
                    symbol=symbol,
                    message=f"Gamma pressure {direction} by {abs(gamma_change_pct):.1f}%. {pressure_type.title()} risk.",
                    current_value=net_gamma,
                    threshold=previous_gamma,
                    timestamp=datetime.now(timezone.utc),
                    metadata={
                        "gamma_change": gamma_change,
                        "gamma_change_pct": gamma_change_pct,
                        "pressure_type": pressure_type
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking gamma pressure shift: {e}")
            return None
    
    def _check_expiry_magnet(self, symbol: str, metrics: Dict[str, Any]) -> Optional[StructuralAlert]:
        """Check for expiry-specific conditions"""
        try:
            # This would need expiry date information
            # For now, implement basic logic
            days_to_expiry = 7  # Placeholder - should come from data
            
            if days_to_expiry <= 3:  # Within 3 days of expiry
                distance_from_flip = metrics.get("distance_from_flip", 999999)
                flow_imbalance = metrics.get("flow_imbalance", 0)
                
                # High expiry magnet conditions
                if distance_from_flip < 50 and abs(flow_imbalance) > 0.5:
                    severity = AlertSeverity.CRITICAL if days_to_expiry <= 1 else AlertSeverity.HIGH
                    
                    return StructuralAlert(
                        alert_type=AlertType.EXPIRY_MAGNET_ALERT,
                        severity=severity,
                        symbol=symbol,
                            message=f"Expiry magnet alert! {days_to_expiry} days to expiry. High pin risk.",
                        current_value=distance_from_flip,
                        threshold=50,
                        timestamp=datetime.now(timezone.utc),
                        metadata={
                            "days_to_expiry": days_to_expiry,
                            "distance_from_flip": distance_from_flip,
                            "flow_imbalance": flow_imbalance
                        }
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking expiry magnet: {e}")
            return None
    
    async def _store_alerts(self, symbol: str, alerts: List[StructuralAlert]) -> None:
        """Store alerts in history"""
        async with self._lock:
            if symbol not in self.alert_history:
                self.alert_history[symbol] = []
            
            self.alert_history[symbol].extend(alerts)
            
            # Keep only last 100 alerts per symbol
            if len(self.alert_history[symbol]) > 100:
                self.alert_history[symbol] = self.alert_history[symbol][-100:]
    
    async def get_recent_alerts(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts for a symbol"""
        async with self._lock:
            alerts = self.alert_history.get(symbol, [])
            
            # Sort by timestamp (most recent first)
            alerts.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Convert to dict format
            recent_alerts = []
            for alert in alerts[:limit]:
                recent_alerts.append({
                    "alert_type": alert.alert_type.value,
                    "severity": alert.severity.value,
                    "symbol": alert.symbol,
                    "message": alert.message,
                    "current_value": alert.current_value,
                    "threshold": alert.threshold,
                    "timestamp": alert.timestamp.isoformat(),
                    "metadata": alert.metadata
                })
            
            return recent_alerts
