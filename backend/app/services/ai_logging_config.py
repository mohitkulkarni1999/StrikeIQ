"""
Centralized AI Logging Configuration for StrikeIQ

Provides consistent logging across all AI components with structured formatting
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps

class AILogger:
    """Enhanced logger for AI components with structured logging"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(f"ai.{name}")
        self.component = name
        
        # Ensure logger has the right level and handlers
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _log_structured(self, level: str, message: str, **kwargs):
        """Log with structured data"""
        log_data = {
            'component': self.component,
            'timestamp': datetime.now().isoformat(),
            'message': message,
            **kwargs
        }
        
        formatted_message = f"{message} | {json.dumps(kwargs)}"
        
        if level == 'info':
            self.logger.info(formatted_message)
        elif level == 'warning':
            self.logger.warning(formatted_message)
        elif level == 'error':
            self.logger.error(formatted_message)
        elif level == 'debug':
            self.logger.debug(formatted_message)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional structured data"""
        self._log_structured('info', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional structured data"""
        self._log_structured('warning', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional structured data"""
        self._log_structured('error', message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional structured data"""
        self._log_structured('debug', message, **kwargs)
    
    def signal_generated(self, formula_id: str, signal: str, confidence: float, spot: float):
        """Log signal generation event"""
        self.info(
            "AI signal generated",
            event_type="SIGNAL_GENERATED",
            formula_id=formula_id,
            signal=signal,
            confidence=confidence,
            spot_price=spot
        )
    
    def prediction_stored(self, prediction_id: int, formula_id: str, signal: str):
        """Log prediction storage event"""
        self.info(
            "Prediction stored",
            event_type="PREDICTION_STORED",
            prediction_id=prediction_id,
            formula_id=formula_id,
            signal=signal
        )
    
    def paper_trade_opened(self, trade_id: int, prediction_id: int, option_type: str, strike: float, entry_price: float):
        """Log paper trade opening event"""
        self.info(
            "Paper trade opened",
            event_type="PAPER_TRADE_OPENED",
            trade_id=trade_id,
            prediction_id=prediction_id,
            option_type=option_type,
            strike_price=strike,
            entry_price=entry_price
        )
    
    def paper_trade_closed(self, trade_id: int, pnl: float, exit_price: float):
        """Log paper trade closing event"""
        self.info(
            "Paper trade closed",
            event_type="PAPER_TRADE_CLOSED",
            trade_id=trade_id,
            pnl=pnl,
            exit_price=exit_price
        )
    
    def outcome_evaluated(self, prediction_id: int, outcome: str, method: str, confidence: float):
        """Log outcome evaluation event"""
        self.info(
            "Outcome evaluated",
            event_type="OUTCOME_EVALUATED",
            prediction_id=prediction_id,
            outcome=outcome,
            evaluation_method=method,
            confidence=confidence
        )
    
    def learning_updated(self, formula_id: str, success_rate: float, adjusted_confidence: float):
        """Log learning update event"""
        self.info(
            "Formula learning updated",
            event_type="LEARNING_UPDATED",
            formula_id=formula_id,
            success_rate=success_rate,
            adjusted_confidence=adjusted_confidence
        )
    
    def job_started(self, job_name: str):
        """Log scheduled job start"""
        self.info(
            f"AI job started: {job_name}",
            event_type="JOB_STARTED",
            job_name=job_name
        )
    
    def job_completed(self, job_name: str, results: Dict[str, Any]):
        """Log scheduled job completion"""
        self.info(
            f"AI job completed: {job_name}",
            event_type="JOB_COMPLETED",
            job_name=job_name,
            results=results
        )
    
    def job_failed(self, job_name: str, error: str):
        """Log scheduled job failure"""
        self.error(
            f"AI job failed: {job_name}",
            event_type="JOB_FAILED",
            job_name=job_name,
            error=error
        )

def log_ai_event(event_type: str, description: str, component: str = "unknown", **kwargs):
    """Utility function to log AI events to database and console"""
    try:
        from ai.ai_db import ai_db
        
        # Log to database
        query = """
            INSERT INTO ai_event_log (event_type, description)
            VALUES (%s, %s)
        """
        
        params = (event_type, description)
        ai_db.execute_query(query, params)
        
        # Log to console
        logger = AILogger(component)
        logger.info(description, event_type=event_type, **kwargs)
        
    except Exception as e:
        # Fallback logging if database fails
        print(f"AI Event Log Error: {e}")
        print(f"Event: {event_type} - {description}")

def log_performance_metrics(component: str, operation: str, duration_ms: float, **kwargs):
    """Log performance metrics for AI operations"""
    logger = AILogger(component)
    logger.info(
        f"Performance: {operation} completed in {duration_ms}ms",
        event_type="PERFORMANCE_METRIC",
        operation=operation,
        duration_ms=duration_ms,
        **kwargs
    )

def ai_error_handler(func):
    """Decorator for consistent error handling in AI components"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            component = func.__module__.split('.')[-1]
            logger = AILogger(component)
            logger.error(
                f"Error in {func.__name__}: {str(e)}",
                event_type="COMPONENT_ERROR",
                function=func.__name__,
                error=str(e),
                args_count=len(args),
                kwargs_count=len(kwargs)
            )
            raise
    return wrapper

# Global logger instances for each component
signal_engine_logger = AILogger("signal_engine")
paper_trade_logger = AILogger("paper_trade_engine")
outcome_engine_logger = AILogger("outcome_engine")
learning_engine_logger = AILogger("learning_engine")
scheduler_logger = AILogger("scheduler")
