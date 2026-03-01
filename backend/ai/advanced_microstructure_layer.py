"""
Advanced Microstructure Layer - Coordinates dealer gamma and liquidity vacuum analysis
Lightweight, optimized for Intel i5 CPU, 8GB RAM
Execution time: < 1ms
"""

import logging
from typing import Dict, Any
import time

# Import the two new engines
from .dealer_gamma_engine import DealerGammaEngine
from .liquidity_vacuum_engine import LiquidityVacuumEngine

logger = logging.getLogger(__name__)

class AdvancedMicrostructureLayer:
    """
    Coordinates advanced microstructure analysis
    Runs dealer gamma and liquidity vacuum engines sequentially
    """
    
    def __init__(self):
        # Initialize engines
        self.dealer_gamma_engine = DealerGammaEngine()
        self.liquidity_vacuum_engine = LiquidityVacuumEngine()
        
        # Performance tracking
        self.execution_times = []
        self.total_executions = 0
        
        logger.info("AdvancedMicrostructureLayer initialized with dealer gamma and liquidity vacuum engines")
    
    def analyze_microstructure(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run all microstructure engines and return combined signals
        
        Args:
            metrics: Dictionary with live market data
            
        Returns:
            Dictionary with combined microstructure analysis
        """
        start_time = time.time()
        
        try:
            # Metrics validation
            if not metrics:
                logger.debug("Empty metrics received")
                return self._safe_default()
            
            # Initialize default values
            microstructure_signals = {
                "dealer_gamma_signal": "GAMMA_NEUTRAL",
                "dealer_gamma_confidence": 0.0,
                "dealer_gamma_direction": "NONE",
                "dealer_gamma_strength": 0.0,
                "liquidity_vacuum_signal": "NONE",
                "liquidity_vacuum_confidence": 0.0,
                "liquidity_vacuum_direction": "NONE",
                "liquidity_vacuum_strength": 0.0,
                "execution_time_ms": 0.0
            }
            
            # Run engines sequentially with error handling
            
            # 1. Dealer Gamma Engine
            try:
                gamma_result = self.dealer_gamma_engine.analyze(metrics)
                microstructure_signals["dealer_gamma_signal"] = gamma_result.get("signal", "GAMMA_NEUTRAL")
                microstructure_signals["dealer_gamma_confidence"] = gamma_result.get("confidence", 0.0)
                microstructure_signals["dealer_gamma_direction"] = gamma_result.get("direction", "NONE")
                microstructure_signals["dealer_gamma_strength"] = gamma_result.get("strength", 0.0)
                
                if gamma_result.get("signal") != "GAMMA_NEUTRAL":
                    logger.info(f"Dealer gamma regime detected: {gamma_result.get('signal')}")
                    
            except Exception as e:
                logger.error(f"Dealer gamma engine error: {e}")
                microstructure_signals["dealer_gamma_signal"] = "GAMMA_NEUTRAL"
                microstructure_signals["dealer_gamma_confidence"] = 0.0
                microstructure_signals["dealer_gamma_direction"] = "NONE"
                microstructure_signals["dealer_gamma_strength"] = 0.0
            
            # 2. Liquidity Vacuum Engine
            try:
                vacuum_result = self.liquidity_vacuum_engine.analyze(metrics)
                microstructure_signals["liquidity_vacuum_signal"] = vacuum_result.get("signal", "NONE")
                microstructure_signals["liquidity_vacuum_confidence"] = vacuum_result.get("confidence", 0.0)
                microstructure_signals["liquidity_vacuum_direction"] = vacuum_result.get("direction", "NONE")
                microstructure_signals["liquidity_vacuum_strength"] = vacuum_result.get("strength", 0.0)
                
                if vacuum_result.get("signal") != "NONE":
                    logger.info(f"Liquidity vacuum detected: {vacuum_result.get('signal')}")
                    
            except Exception as e:
                logger.error(f"Liquidity vacuum engine error: {e}")
                microstructure_signals["liquidity_vacuum_signal"] = "NONE"
                microstructure_signals["liquidity_vacuum_confidence"] = 0.0
                microstructure_signals["liquidity_vacuum_direction"] = "NONE"
                microstructure_signals["liquidity_vacuum_strength"] = 0.0
            
            # Add performance metrics
            execution_time = time.time() - start_time
            execution_time_ms = execution_time * 1000
            
            microstructure_signals["execution_time_ms"] = execution_time_ms
            
            # Track performance
            self.execution_times.append(execution_time_ms)
            self.total_executions += 1
            
            logger.info(f"Advanced microstructure analysis completed in {execution_time_ms:.2f}ms")
            
            return microstructure_signals
            
        except Exception as e:
            logger.error(f"AdvancedMicrostructureLayer error: {e}")
            return self._safe_default()
    
    def _safe_default(self) -> Dict[str, Any]:
        """Return safe default values"""
        return {
            "dealer_gamma_signal": "GAMMA_NEUTRAL",
            "dealer_gamma_confidence": 0.0,
            "dealer_gamma_direction": "NONE",
            "dealer_gamma_strength": 0.0,
            "liquidity_vacuum_signal": "NONE",
            "liquidity_vacuum_confidence": 0.0,
            "liquidity_vacuum_direction": "NONE",
            "liquidity_vacuum_strength": 0.0,
            "execution_time_ms": 0.0
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for microstructure analysis
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
_advanced_microstructure_layer = None

def get_advanced_microstructure_layer() -> AdvancedMicrostructureLayer:
    """
    Get or create global AdvancedMicrostructureLayer instance
    """
    global _advanced_microstructure_layer
    if _advanced_microstructure_layer is None:
        _advanced_microstructure_layer = AdvancedMicrostructureLayer()
    return _advanced_microstructure_layer

def analyze_advanced_microstructure(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to analyze advanced microstructure
    
    Args:
        metrics: Dictionary with live market data
        
    Returns:
        Dictionary with advanced microstructure analysis
    """
    extension_layer = get_advanced_microstructure_layer()
    return extension_layer.analyze_microstructure(metrics)

def get_microstructure_performance() -> Dict[str, Any]:
    """
    Convenience function to get microstructure performance
    """
    extension_layer = get_advanced_microstructure_layer()
    return extension_layer.get_performance_metrics()
