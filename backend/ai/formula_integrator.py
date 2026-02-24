import logging
from typing import Optional
from .prediction_service import prediction_service
from .experience_service import experience_service

logger = logging.getLogger(__name__)

class FormulaSignalIntegrator:
    """
    Integration point for all formula signals (F01-F24) to store predictions
    in AI learning system with experience-based confidence adjustment.
    
    This should be called whenever any formula generates a BUY/SELL signal.
    """
    
    def __init__(self):
        self.prediction_service = prediction_service
        self.experience_service = experience_service
        
    def store_formula_signal(
        self, 
        formula_id: str, 
        signal: str, 
        confidence: float, 
        current_price: float
    ) -> bool:
        """
        Store a formula signal in AI learning system with experience-based confidence adjustment
        
        Args:
            formula_id: Formula identifier (e.g., 'F01', 'F02', ..., 'F24')
            signal: Trading signal ('BUY' or 'SELL')
            confidence: Original confidence level (0.0 to 1.0)
            current_price: Current market price (NIFTY spot)
            
        Returns:
            bool: True if successfully stored, False if ignored due to low confidence
        """
        try:
            # Validate inputs
            if not formula_id or not signal or confidence is None or current_price is None:
                logger.error(f"Invalid parameters for formula signal: {formula_id}, {signal}, {confidence}, {current_price}")
                return False
                
            # Only store BUY/SELL signals
            if signal.upper() not in ['BUY', 'SELL']:
                logger.info(f"Ignoring non-trading signal: {signal} from {formula_id}")
                return True  # Not an error, just ignore
                
            # Validate formula_id format (F01-F24)
            if not formula_id.upper().startswith('F') or len(formula_id) != 3:
                logger.error(f"Invalid formula_id format: {formula_id}. Expected F01-F24")
                return False
                
            # Validate confidence range
            if not (0.0 <= confidence <= 1.0):
                logger.error(f"Invalid confidence value: {confidence}. Must be between 0.0 and 1.0")
                return False
                
            # STEP 1: Fetch experience score
            exp_score = self.experience_service.get_experience_score(formula_id)
            logger.info(f"Formula {formula_id}: original confidence={confidence:.2f}, experience_score={exp_score:.3f}")
            
            # STEP 2: Calculate adjusted confidence
            adjusted_confidence = confidence * exp_score
            logger.info(f"Formula {formula_id}: adjusted confidence={adjusted_confidence:.3f} (confidence * experience_score)")
            
            # STEP 3: Decision filter - ignore weak signals
            if adjusted_confidence < 0.40:
                logger.warning(f"{formula_id} {signal} ignored due to low adjusted confidence {adjusted_confidence:.2f}")
                return False  # Signal ignored, not an error
                
            # STEP 4: Store prediction with adjusted confidence
            success = self.prediction_service.store_prediction(
                formula_id=formula_id.upper(),
                signal=signal.upper(),
                confidence=adjusted_confidence,  # Use adjusted confidence
                spot=current_price
            )
            
            if success:
                logger.info(f"Formula signal stored: {formula_id} {signal} @ {current_price} (adjusted_confidence: {adjusted_confidence:.3f})")
            else:
                logger.error(f"Failed to store formula signal: {formula_id} {signal}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error storing formula signal from {formula_id}: {e}")
            return False
            
    def get_formula_performance(self, formula_id: str) -> Optional[dict]:
        """
        Get performance statistics for a specific formula
        
        Args:
            formula_id: Formula identifier (e.g., 'F01', 'F02', ..., 'F24')
            
        Returns:
            dict: Performance statistics or None if error
        """
        try:
            from .experience_updater import experience_updater
            return experience_updater.get_formula_experience(formula_id)
        except Exception as e:
            logger.error(f"Error getting formula performance for {formula_id}: {e}")
            return None
            
    def get_all_formula_scores(self) -> dict:
        """
        Get experience scores for all formulas
        
        Returns:
            dict: Mapping of formula_id -> success_rate
        """
        try:
            return self.experience_service.get_all_experience_scores()
        except Exception as e:
            logger.error(f"Error getting all formula scores: {e}")
            return {}
            
    def get_top_performers(self, limit: int = 5) -> list:
        """
        Get top performing formulas
        
        Args:
            limit: Maximum number of formulas to return
            
        Returns:
            list: Top performing formulas with their statistics
        """
        try:
            return self.experience_service.get_top_performers(limit)
        except Exception as e:
            logger.error(f"Error getting top performers: {e}")
            return []

# Global instance for easy access
formula_integrator = FormulaSignalIntegrator()

# Convenience function for easy integration
def store_formula_signal(formula_id: str, signal: str, confidence: float, current_price: float) -> bool:
    """
    Convenience function to store formula signals with experience-based confidence adjustment
    
    Usage in any formula:
    from ai.formula_integrator import store_formula_signal
    
    # When formula generates signal:
    success = store_formula_signal('F01', 'BUY', 0.85, 19500.50)
    
    The function will:
    1. Get experience score for F01
    2. Adjust confidence: 0.85 * experience_score
    3. Filter out if adjusted_confidence < 0.40
    4. Store with adjusted confidence if passes filter
    """
    return formula_integrator.store_formula_signal(formula_id, signal, confidence, current_price)
