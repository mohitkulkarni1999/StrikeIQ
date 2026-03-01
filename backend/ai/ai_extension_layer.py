"""
AI Extension Layer - Coordinates advanced AI intelligence modules
Lightweight, optimized for Intel i5 CPU, 8GB RAM
"""

import logging
from typing import Dict, Any
import time

# Import the four new engines
from .liquidity_engine import LiquidityEngine
from .stoploss_hunt_engine import StoplossHuntEngine
from .smart_money_engine import SmartMoneyEngine
from .gamma_squeeze_engine import GammaSqueezeEngine

logger = logging.getLogger(__name__)

class AIExtensionLayer:
    """
    Coordinates advanced AI intelligence modules
    Runs all engines sequentially and combines their outputs
    """
    
    def __init__(self):
        # Initialize all engines
        self.liquidity_engine = LiquidityEngine()
        self.stoploss_hunt_engine = StoplossHuntEngine()
        self.smart_money_engine = SmartMoneyEngine()
        self.gamma_squeeze_engine = GammaSqueezeEngine()
        
        # Performance tracking
        self.execution_times = []
        self.total_executions = 0
        
        logger.info("AI Extension Layer initialized with all engines")
    
    def analyze_advanced_signals(self, live_metrics) -> Dict[str, Any]:
        """
        Run all advanced AI engines and return combined signals
        """
        start_time = time.time()
        
        try:
            # FIX 1: Metrics validation
            if not live_metrics:
                logger.debug("Empty metrics received")
                return self._safe_default()
            
            # Initialize default values
            advanced_ai_signals = {
                "liquidity_signal": "NONE",
                "liquidity_confidence": 0.0,
                "liquidity_direction": "NONE",
                "liquidity_strength": 0.0,
                "stoploss_hunt_signal": "NONE",
                "stoploss_hunt_confidence": 0.0,
                "stoploss_hunt_direction": "NONE",
                "stoploss_hunt_strength": 0.0,
                "smart_money_signal": "NEUTRAL",
                "smart_money_confidence": 0.0,
                "smart_money_direction": "NONE",
                "smart_money_strength": 0.0,
                "gamma_squeeze_signal": "NONE",
                "gamma_squeeze_confidence": 0.0,
                "gamma_squeeze_direction": "NONE",
                "gamma_squeeze_strength": 0.0,
                "execution_time_ms": 0.0
            }
            
            # Run engines sequentially with error handling
            
            # 1. Liquidity Engine
            try:
                liquidity_result = self.liquidity_engine.analyze(live_metrics)
                advanced_ai_signals["liquidity_signal"] = liquidity_result.get("signal", "NONE")
                advanced_ai_signals["liquidity_confidence"] = liquidity_result.get("confidence", 0.0)
                advanced_ai_signals["liquidity_direction"] = liquidity_result.get("direction", "NONE")
                advanced_ai_signals["liquidity_strength"] = liquidity_result.get("strength", 0.0)
                
                if liquidity_result.get("signal") != "NONE":
                    logger.info(f"Liquidity sweep detected: {liquidity_result.get('signal')}")
                    
            except Exception as e:
                logger.error(f"Liquidity engine error: {e}")
                advanced_ai_signals["liquidity_signal"] = "NONE"
                advanced_ai_signals["liquidity_confidence"] = 0.0
                advanced_ai_signals["liquidity_direction"] = "NONE"
                advanced_ai_signals["liquidity_strength"] = 0.0
            
            # 2. Stoploss Hunt Engine
            try:
                hunt_result = self.stoploss_hunt_engine.analyze(live_metrics)
                advanced_ai_signals["stoploss_hunt_signal"] = hunt_result.get("signal", "NONE")
                advanced_ai_signals["stoploss_hunt_confidence"] = hunt_result.get("confidence", 0.0)
                advanced_ai_signals["stoploss_hunt_direction"] = hunt_result.get("direction", "NONE")
                advanced_ai_signals["stoploss_hunt_strength"] = hunt_result.get("strength", 0.0)
                
                if hunt_result.get("signal") != "NONE":
                    logger.info(f"Stoploss hunt detected: {hunt_result.get('signal')}")
                    
            except Exception as e:
                logger.error(f"Stoploss hunt engine error: {e}")
                advanced_ai_signals["stoploss_hunt_signal"] = "NONE"
                advanced_ai_signals["stoploss_hunt_confidence"] = 0.0
                advanced_ai_signals["stoploss_hunt_direction"] = "NONE"
                advanced_ai_signals["stoploss_hunt_strength"] = 0.0
            
            # 3. Smart Money Engine
            try:
                smart_money_result = self.smart_money_engine.analyze(live_metrics)
                advanced_ai_signals["smart_money_signal"] = smart_money_result.get("signal", "NEUTRAL")
                advanced_ai_signals["smart_money_confidence"] = smart_money_result.get("confidence", 0.0)
                advanced_ai_signals["smart_money_direction"] = smart_money_result.get("direction", "NONE")
                advanced_ai_signals["smart_money_strength"] = smart_money_result.get("strength", 0.0)
                
                if smart_money_result.get("signal") != "NEUTRAL":
                    logger.info(f"Smart money bias detected: {smart_money_result.get('signal')}")
                    
            except Exception as e:
                logger.error(f"Smart money engine error: {e}")
                advanced_ai_signals["smart_money_signal"] = "NEUTRAL"
                advanced_ai_signals["smart_money_confidence"] = 0.0
                advanced_ai_signals["smart_money_direction"] = "NONE"
                advanced_ai_signals["smart_money_strength"] = 0.0
            
            # 4. Gamma Squeeze Engine
            try:
                squeeze_result = self.gamma_squeeze_engine.analyze(live_metrics)
                advanced_ai_signals["gamma_squeeze_signal"] = squeeze_result.get("signal", "NONE")
                advanced_ai_signals["gamma_squeeze_confidence"] = squeeze_result.get("confidence", 0.0)
                advanced_ai_signals["gamma_squeeze_direction"] = squeeze_result.get("direction", "NONE")
                advanced_ai_signals["gamma_squeeze_strength"] = squeeze_result.get("strength", 0.0)
                
                if squeeze_result.get("signal") != "NONE":
                    logger.info(f"Gamma squeeze detected: {squeeze_result.get('signal')}")
                    
            except Exception as e:
                logger.error(f"Gamma squeeze engine error: {e}")
                advanced_ai_signals["gamma_squeeze_signal"] = "NONE"
                advanced_ai_signals["gamma_squeeze_confidence"] = 0.0
                advanced_ai_signals["gamma_squeeze_direction"] = "NONE"
                advanced_ai_signals["gamma_squeeze_strength"] = 0.0
            
            # Track performance
            execution_time = time.time() - start_time
            execution_time_ms = execution_time * 1000
            advanced_ai_signals["execution_time_ms"] = execution_time_ms
            
            self.execution_times.append(execution_time_ms)
            self.total_executions += 1
            
            logger.info(f"AI Extension Layer completed in {execution_time_ms:.2f}ms")
            
            return advanced_ai_signals
            
        except Exception as e:
            logger.error(f"AI Extension Layer error: {e}")
            return self._safe_default()
    
    def _safe_default(self) -> Dict[str, Any]:
        """Return safe default values"""
        return {
            "liquidity_signal": "NONE",
            "liquidity_confidence": 0.0,
            "liquidity_direction": "NONE",
            "liquidity_strength": 0.0,
            "stoploss_hunt_signal": "NONE",
            "stoploss_hunt_confidence": 0.0,
            "stoploss_hunt_direction": "NONE",
            "stoploss_hunt_strength": 0.0,
            "smart_money_signal": "NEUTRAL",
            "smart_money_confidence": 0.0,
            "smart_money_direction": "NONE",
            "smart_money_strength": 0.0,
            "gamma_squeeze_signal": "NONE",
            "gamma_squeeze_confidence": 0.0,
            "gamma_squeeze_direction": "NONE",
            "gamma_squeeze_strength": 0.0,
            "execution_time_ms": 0.0
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for extension layer
        """
        try:
            if not self.execution_times:
                return {
                    'total_executions': 0,
                    'avg_execution_time_ms': 0,
                    'max_execution_time_ms': 0,
                    'min_execution_time_ms': 0
                }
            
            avg_time = sum(self.execution_times) / len(self.execution_times)
            max_time = max(self.execution_times)
            min_time = min(self.execution_times)
            
            return {
                'total_executions': self.total_executions,
                'avg_execution_time_ms': avg_time,
                'max_execution_time_ms': max_time,
                'min_execution_time_ms': min_time
            }
            
        except Exception as e:
            logger.error(f"Performance metrics error: {e}")
            return {'error': str(e)}

# Global instance
_ai_extension_layer = None

def get_ai_extension_layer() -> AIExtensionLayer:
    """
    Get or create global AI Extension Layer instance
    """
    global _ai_extension_layer
    if _ai_extension_layer is None:
        _ai_extension_layer = AIExtensionLayer()
    return _ai_extension_layer

def analyze_advanced_ai_signals(live_metrics) -> Dict[str, Any]:
    """
    Convenience function to analyze advanced AI signals
    """
    extension_layer = get_ai_extension_layer()
    return extension_layer.analyze_advanced_signals(live_metrics)

def get_extension_performance() -> Dict[str, Any]:
    """
    Convenience function to get extension layer performance
    """
    extension_layer = get_ai_extension_layer()
    return extension_layer.get_performance_metrics()
