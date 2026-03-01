"""
Trap Extension Layer - Coordinates Options Trap Detection
Lightweight, optimized for Intel i5 CPU, 8GB RAM
"""

import logging
from typing import Dict, Any
import time

from .options_trap_engine import OptionsTrapEngine

logger = logging.getLogger(__name__)

class TrapExtensionLayer:
    """
    Extension layer for options trap detection
    Provides simple interface for trap analysis
    """
    
    def __init__(self):
        self.trap_engine = OptionsTrapEngine()
        
        # Performance tracking
        self.execution_times = []
        self.total_executions = 0
        
        logger.info("TrapExtensionLayer initialized")
    
    def analyze_traps(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze options market traps
        
        Args:
            metrics: Dictionary with live market data
            
        Returns:
            Dictionary with trap analysis and performance metrics
        """
        start_time = time.time()
        
        try:
            # FIX 1: Metrics validation
            if not metrics:
                logger.debug("Empty metrics received")
                return self._safe_default()
            
            # Run trap detection
            trap_result = self.trap_engine.detect_trap(metrics)
            
            # Add performance metrics
            execution_time = time.time() - start_time
            execution_time_ms = execution_time * 1000
            
            trap_result["execution_time_ms"] = execution_time_ms
            
            # Track performance
            self.execution_times.append(execution_time_ms)
            self.total_executions += 1
            
            logger.info(f"Trap analysis completed in {execution_time_ms:.2f}ms")
            
            return trap_result
            
        except Exception as e:
            logger.error(f"TrapExtensionLayer error: {e}")
            return self._safe_default()
    
    def _safe_default(self) -> Dict[str, Any]:
        """Return safe default values"""
        return {
            "trap_signal": "NONE",
            "confidence": 0.0,
            "trap_strength": 0.0,
            "direction": "NONE",
            "reason": "invalid_metrics",
            "execution_time_ms": 0.0
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for trap detection
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
_trap_extension_layer = None

def get_trap_extension_layer() -> TrapExtensionLayer:
    """
    Get or create global Trap Extension Layer instance
    """
    global _trap_extension_layer
    if _trap_extension_layer is None:
        _trap_extension_layer = TrapExtensionLayer()
    return _trap_extension_layer

def analyze_options_traps(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to analyze options market traps
    
    Args:
        metrics: Dictionary with live market data
        
    Returns:
        Dictionary with trap detection results
    """
    extension_layer = get_trap_extension_layer()
    return extension_layer.analyze_traps(metrics)

def get_trap_performance() -> Dict[str, Any]:
    """
    Convenience function to get trap detection performance
    """
    extension_layer = get_trap_extension_layer()
    return extension_layer.get_performance_metrics()
